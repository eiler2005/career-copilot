"""Deterministic host-agent handoffs; no model calls or external sends."""

from __future__ import annotations

from datetime import UTC, datetime
from functools import wraps
from math import isfinite
from pathlib import Path
from uuid import uuid4

from . import inbox
from .core import FLAGSHIPS, TRACKS, Store, digest, encode, now, read_json, safe_id

SCHEMA_VERSION = 1
SKILLS = (
    "career-copilot",
    "career-job-search",
    "career-company-research",
    "career-cv-tailor",
    "career-natural-writing",
    "career-cover-letter",
    "career-interview-prep",
    "career-journal-stats",
)
RESULT_KINDS = {
    "company_dossier": "company_dossiers",
    "text_revision": "text_revisions",
    "cover_letter": "cover_letters",
    "interview_plan": "interview_plans",
    "interview_practice": "interview_practices",
    "interview_feedback": "interview_feedback",
    "interview_progress": "interview_progress",
    "submission": "submissions",
    "employer_response": "employer_responses",
    "cv_edit_proposal": "cv_edits",
}


def transaction(function):
    """Keep registration atomic, including artifact rows staged during validation."""

    @wraps(function)
    def wrapped(store, *args, **kwargs):
        store.db.execute("BEGIN IMMEDIATE")
        try:
            result = function(store, *args, **kwargs)
            store.db.execute("COMMIT")
            return result
        except Exception:
            store.db.execute("ROLLBACK")
            raise

    return wrapped


def actor_metadata(value: dict | None) -> dict:
    value = value or {}
    if not isinstance(value, dict):
        raise ValueError("Actor must be an object with actual identities or nulls")  # noqa: TRY004
    result = {key: value.get(key) for key in ("environment", "model", "session")}
    if any(v is not None and (not isinstance(v, str) or not v.strip()) for v in result.values()):
        raise ValueError("Actor identities must be nonempty strings or null")
    environment = result["environment"]
    if (
        environment in FLAGSHIPS
        and result["model"] in FLAGSHIPS.values()
        and FLAGSHIPS[environment] != result["model"]
    ):
        raise ValueError("Actor model conflicts with environment")
    return result


def observed_time(value: str) -> datetime:
    timestamp = datetime.fromisoformat(value)
    if timestamp.tzinfo is None or timestamp > datetime.now(UTC):
        raise ValueError("Observed timestamp requires timezone and cannot be in the future")
    return timestamp


def snapshot_ref(store: Store, ref: dict, base: Path) -> dict:
    if not isinstance(ref, dict) or not ref.get("path") or not ref.get("sha256"):
        raise ValueError("File reference requires path and sha256")
    path = Path(ref["path"]).expanduser()
    path = (base / path).resolve() if not path.is_absolute() else path.resolve()
    if not path.is_file():
        raise ValueError("File reference missing or stale")
    body = path.read_bytes()
    if digest(body) != ref["sha256"]:
        raise ValueError("File reference missing or stale")
    relative = store.readable_artifact("activity-artifacts", [path.stem], body, path.suffix)
    return {"path": relative, "sha256": digest(body), "original_path": str(path)}


def refs_valid(store: Store, refs: list[dict], *, originals: bool = False) -> bool:
    for ref in refs:
        path = store.path(ref["path"])
        if not path.is_file() or digest(path.read_bytes()) != ref["sha256"]:
            return False
        if originals:
            original = Path(ref["original_path"])
            if not original.is_file() or digest(original.read_bytes()) != ref["sha256"]:
                return False
    return True


@transaction
def start(store: Store, request_path: Path) -> dict:
    request = read_json(request_path)
    if request.get("schema_version") != SCHEMA_VERSION or request.get("skill") not in SKILLS:
        raise ValueError("Supported activity schema_version and skill required")
    if not isinstance(request.get("operation"), str) or not request["operation"].strip():
        raise ValueError("Activity operation required")
    expected = request.get("expected_result")
    if not isinstance(expected, dict) or not isinstance(expected.get("types"), list):
        raise ValueError("expected_result.types array required (may be empty for CLI operations)")  # noqa: TRY004
    if not set(expected["types"]).issubset(RESULT_KINDS):
        raise ValueError("Unsupported expected result type")
    parent = request.get("parent_activity_id")
    if parent and not store.get("activities", parent):
        raise ValueError("Parent activity not found")
    related = request.get("related", {})
    if not isinstance(related, dict) or related.get("track", TRACKS[0]) not in TRACKS:
        raise ValueError("Invalid related entities or track")
    for field, kind in (("company_id", "companies"), ("vacancy_id", "vacancies")):
        if related.get(field) and not store.get(kind, related[field]):
            raise ValueError("Related entity not found")
    task = store.get("tasks", related["task_id"]) if related.get("task_id") else None
    if related.get("task_id") and (
        not task or task["status"] not in {"queued", "blocked", "failed"}
    ):
        raise ValueError("Related task not found or not waiting for an agent")
    actor = actor_metadata(request.get("actor"))
    required = request.get("required_model")
    if required is not None and (not isinstance(required, str) or not required):
        raise ValueError("required_model must be a model identity or null")
    inputs = request.get("inputs", [])
    if not isinstance(inputs, list):
        raise ValueError("inputs must be an array")  # noqa: TRY004
    refs = [snapshot_ref(store, ref, request_path.resolve().parent) for ref in inputs]
    key = "act-" + uuid4().hex
    request_ref = store.artifact(f"activities/{key}/request.json", encode(request))
    requires_flagship = request["skill"] in {
        "career-cv-tailor",
        "career-natural-writing",
        "career-cover-letter",
    }
    blocked = bool(required and (actor["model"] != required or not actor["session"])) or (
        requires_flagship and (actor["model"] not in FLAGSHIPS.values() or not actor["session"])
    )
    value = {
        "id": key,
        "schema_version": SCHEMA_VERSION,
        "skill": request["skill"],
        "operation": request["operation"],
        "parent_activity_id": parent,
        "related": related,
        "inputs": refs,
        "actor": actor,
        "required_model": required,
        "requires_flagship": requires_flagship,
        "expected_result": expected,
        "request": {"path": request_ref, "sha256": digest(request)},
        "status": "blocked" if blocked else "running",
        "started_at": now(),
        "finished_at": None,
        "result": None,
        "next_action": "Required model and actual session unavailable; start a new linked activity"
        if blocked
        else "Perform the operation, then activity finish with the result file",
    }
    store.put("activities", value, immutable=True)
    if task:
        inbox.bind_task_to_activity(store, task["id"], key, blocked=blocked)
    previous = store.activity_id
    store.activity_id = key
    try:
        store.event(
            "activity_started", [key], {"skill": value["skill"], "operation": value["operation"]}
        )
    finally:
        store.activity_id = previous
    return show(store, key)


def show(store: Store, activity_id: str) -> dict:
    value = store.get("activities", activity_id)
    if not value:
        raise ValueError("Activity not found")
    links = [r for r in store.all("activity_events") if r["activity_id"] == activity_id]
    valid = refs_valid(store, value["inputs"], originals=True)
    return {
        **value,
        "input_integrity": valid,
        "request_integrity": refs_valid(store, [value["request"]]),
        "result_integrity": refs_valid(
            store, [value["result"], *value.get("artifacts", {}).values()]
        )
        if value.get("result")
        else None,
        "resumable": value["status"] == "running" and valid,
        "events": [store.get("events", r["event_id"]) for r in links],
    }


def bind(store: Store, activity_id: str) -> None:
    value = show(store, activity_id)
    if not value["resumable"]:
        raise ValueError("Activity is not running or has stale inputs")
    store.activity_id = activity_id


def package_version(store: Store, package_id: str, version_id: str) -> tuple[dict, dict]:
    from .workflow import version_checks

    package = store.get("packages", package_id)
    version = next((v for v in (package or {}).get("versions", []) if v["id"] == version_id), None)
    if not version or version_checks(store, version):
        raise ValueError("Referenced package version missing or stale")
    return package, version


def validate_record(
    store: Store, record: dict, artifacts: dict, activity: dict, pending: dict
) -> dict:
    kind = record.get("type")
    if kind not in RESULT_KINDS or not isinstance(record.get("data"), dict):
        raise ValueError("Typed result requires supported type and data object")
    data = dict(record["data"])
    key = safe_id(data.get("id", kind + "-" + uuid4().hex))

    def required(*fields):
        if any(not data.get(field) for field in fields):
            raise ValueError(f"{kind} requires {', '.join(fields)}")

    def artifact(field):
        required(field)
        if data[field] not in artifacts:
            raise ValueError("Typed result references an unknown artifact name")
        return artifacts[data[field]]

    def reference(field, target):
        required(field)
        value = pending.get((target, data[field])) or store.get(target, data[field])
        if not value:
            raise ValueError("Typed result references a missing record")
        return value

    if kind == "cv_edit_proposal":
        from . import cv

        data = cv.validate_proposal(store, data, activity)
    elif kind == "company_dossier":
        data["profile_before"] = reference("company_id", "companies")
        data["dossier"] = artifact("dossier_artifact")
        if not isinstance(data.get("profile", {}), dict):
            raise ValueError("Company profile must be an object")
        if "id" in data.get("profile", {}):
            raise ValueError("Company profile cannot replace the company ID")
    elif kind == "text_revision":
        if activity["actor"]["model"] not in FLAGSHIPS.values() or not activity["actor"]["session"]:
            raise ValueError("Text revision requires actual flagship actor and session")
        data["before"] = artifact("before_artifact")
        data["after"] = artifact("after_artifact")
        required("change_notes")
    elif kind in {"cover_letter", "submission"}:
        prefix = "cv_" if kind == "cover_letter" else ""
        required(prefix + "package_id", prefix + "version_id")
        package, version = package_version(
            store, data[prefix + "package_id"], data[prefix + "version_id"]
        )
        if kind == "cover_letter":
            data["draft"] = artifact("draft_artifact")
            data["cv_source_sha256"] = version["sha256"]["cv_source"]
            if (
                activity["actor"]["model"] not in FLAGSHIPS.values()
                or not activity["actor"]["session"]
            ):
                raise ValueError("Cover letter requires actual flagship actor and session")
        else:
            required("channel", "sent_at")
            observed_time(data["sent_at"])
            if data.get("user_confirmed") is not True:
                raise ValueError("Submission requires explicit user confirmation")
            data["evidence"] = artifact("evidence_artifact")
            data["vacancy_id"] = package["vacancy_id"]
    elif kind == "employer_response":
        submission = reference("submission_id", "submissions")
        required("status", "received_at", "summary")
        if data["status"] not in {"acknowledged", "interview", "rejected", "offer", "other"}:
            raise ValueError("Unsupported employer response status")
        observed_time(data["received_at"])
        if not refs_valid(store, [submission["evidence"]]):
            raise ValueError("Submission evidence is stale")
        data["evidence"] = artifact("evidence_artifact")
        data["package_id"] = submission["package_id"]
        data["vacancy_id"] = submission["vacancy_id"]
    elif kind == "interview_plan":
        required("track", "objectives")
        if data["track"] not in TRACKS:
            raise ValueError("Unknown interview track")
        data["plan"] = artifact("plan_artifact")
    elif kind == "interview_practice":
        reference("plan_id", "interview_plans")
        required("exercise")
        data["evidence"] = artifact("evidence_artifact")
    elif kind == "interview_feedback":
        reference("practice_id", "interview_practices")
        required("findings")
        data["feedback"] = artifact("feedback_artifact")
    elif kind == "interview_progress":
        practice = reference("practice_id", "interview_practices")
        feedback = reference("feedback_id", "interview_feedback")
        required("decision", "rationale")
        if feedback["practice_id"] != practice["id"]:
            raise ValueError("Interview feedback must refer to this practice")
        if not refs_valid(store, [practice["evidence"], feedback["feedback"]]):
            raise ValueError("Interview practice or feedback evidence is stale")
        if data["decision"] not in {"demonstrated", "needs_practice", "blocked"}:
            raise ValueError("Invalid interview progress decision")
        data["evidence"] = artifact("evidence_artifact")
        reviewer = actor_metadata(data.get("reviewer"))
        if not reviewer["session"]:
            raise ValueError("Interview progress requires an actual reviewer session")
        data["reviewer"] = reviewer
    return {
        **data,
        "id": key,
        "activity_id": activity["id"],
        "actor": activity["actor"],
        "type": kind,
        "created_at": now(),
    }


@transaction
def finish(store: Store, activity_id: str, result_path: Path) -> dict:
    activity = store.get("activities", activity_id)
    if not activity:
        raise ValueError("Activity not found")
    result = read_json(result_path)
    result_hash = digest(result)
    if activity.get("result"):
        if activity["result"]["sha256"] != result_hash:
            raise ValueError("Conflicting activity result; start a new activity")
        return show(store, activity_id)
    if result.get("schema_version") != SCHEMA_VERSION or result.get("status") not in {
        "completed",
        "blocked",
        "failed",
    }:
        raise ValueError("Supported result schema_version and terminal status required")
    if not isinstance(result.get("next_action"), str) or not result["next_action"].strip():
        raise ValueError("Result next_action required")
    if result["status"] == "completed" and not refs_valid(
        store, activity["inputs"], originals=True
    ):
        raise ValueError("Activity inputs changed; start a new activity with fresh hashes")
    actor = actor_metadata(result.get("actor", activity["actor"]))
    if activity["actor"]["model"] and actor != activity["actor"]:
        raise ValueError("Actor changed; use a new child activity for another actor")
    required = activity.get("required_model")
    if (
        result["status"] == "completed"
        and required
        and (actor["model"] != required or not actor["session"])
    ):
        raise ValueError("Required model unavailable; finish blocked without fabricating identity")
    if activity["status"] == "blocked" and result["status"] == "completed":
        raise ValueError("Start a new linked activity when the required model becomes available")
    activity["actor"] = actor
    telemetry = result.get("telemetry") or {}
    for name in ("input_tokens", "output_tokens", "cost"):
        value = telemetry.get(name)
        if value is not None and (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or value < 0
            or not isfinite(value)
        ):
            raise ValueError("Telemetry must be measured nonnegative numbers or null")
    artifacts = {}
    for ref in result.get("artifacts", []):
        name = safe_id(ref.get("name", ""))
        if name in artifacts:
            raise ValueError("Duplicate result artifact name")
        artifacts[name] = snapshot_ref(store, ref, result_path.resolve().parent)
    records = result.get("records", [])
    if result["status"] != "completed" and records:
        raise ValueError("Blocked/failed results cannot register completed typed outputs")
    if result["status"] == "completed" and not set(activity["expected_result"]["types"]).issubset(
        {r.get("type") for r in records}
    ):
        raise ValueError("Completed result is missing expected typed outputs")
    pending = {}
    for record in records:
        value = validate_record(store, record, artifacts, activity, pending)
        key = (RESULT_KINDS[value["type"]], value["id"])
        if key in pending or store.get(*key):
            raise ValueError("Typed record ID already exists; create a new ID")
        pending[key] = value
    previous = store.activity_id
    store.activity_id = activity_id
    try:
        for (kind, key), value in pending.items():
            store.put(kind, value, immutable=True)
            if kind == "company_dossiers":
                company = store.get("companies", value["company_id"])
                profile = {**company, **value.get("profile", {})}
                profile["dossier_refs"] = company.get("dossier_refs", []) + [key]
                store.put("companies", profile)
            store.event("activity_output_registered", [activity_id, key], {"kind": kind})
        path = store.artifact(f"activities/{activity_id}/result.json", encode(result))
        activity.update(
            status=result["status"],
            finished_at=now(),
            next_action=result["next_action"],
            result={"path": path, "sha256": result_hash},
            artifacts=artifacts,
            records=[{"kind": kind, "id": key} for kind, key in pending],
            telemetry={
                key: telemetry.get(key) for key in ("input_tokens", "output_tokens", "cost")
            },
        )
        store.put("activities", activity)
        inbox.close_task_from_activity(store, activity)
        store.event(
            "activity_finished",
            [activity_id],
            {"status": activity["status"], "result_sha256": result_hash},
        )
    finally:
        store.activity_id = previous
    return show(store, activity_id)
