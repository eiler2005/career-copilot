"""Requests from the browser and tasks for an agent session.

The dashboard never edits the journal. It writes *requests* into its state directory.
`ajh inbox import` copies them into the journal and `ajh inbox apply` executes them
against the local journal, the single source of truth:

* deterministic requests (a personal decision, a clarification, an evaluation, ...)
  are applied by a controlled Store operation with an optimistic version check;
* requests that need authored or researched work become `tasks`. An existing agent
  session picks a task up, runs it as an activity and the task is closed only when
  that activity really finishes.

Every request keeps its status (`pending`, `applied`, `queued_for_agent`, `conflict`,
`failed`, `rejected`) and the reason, so nothing silently disappears.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from .core import TRACKS, Store, VersionConflict, atomic_write, encode, now, safe_id

SCHEMA_VERSION = 1
MAX_REQUEST_BYTES = 40_000
MAX_TEXT = 20_000
REQUEST_DIR = "requests"
TASK_TYPES = frozenset(
    {
        "collect",
        "annotate_requirements",
        "tailor_cv",
        "fix_master_cv",
        "extract_cv_facts",
        "prepare_vacancy_brief",
        "track_plan_materials",
        "review_practice",
    }
)
TASK_SKILLS = {
    "collect": "career-job-search",
    "annotate_requirements": "career-job-search",
    "tailor_cv": "career-cv-tailor",
    "fix_master_cv": "career-cv-tailor",
    "extract_cv_facts": "career-cv-tailor",
    "prepare_vacancy_brief": "career-interview-prep",
    "track_plan_materials": "career-interview-prep",
    "review_practice": "career-interview-prep",
}
RELATED_KEYS = frozenset(
    {
        "vacancy_id",
        "company_id",
        "track",
        "package_id",
        "version_id",
        "plan_id",
        "session_id",
        "attempt_id",
        "proposal_id",
        "campaign_id",
        "requirement_id",
        "import_id",
    }
)


def _text(value: object, name: str, limit: int = MAX_TEXT, required: bool = True) -> str | None:
    if value is None and not required:
        return None
    if not isinstance(value, str) or (required and not value.strip()) or len(value) > limit:
        raise ValueError(f"{name} must be text up to {limit} characters")
    return value.strip()


def _choice(value: object, name: str, options: frozenset[str] | set[str] | tuple) -> str:
    if value not in options:
        raise ValueError(f"{name} must be one of {sorted(options)}")
    return str(value)


def _related(value: object) -> dict:
    if value is None:
        return {}
    if not isinstance(value, dict) or not set(value) <= RELATED_KEYS:
        raise ValueError("related contains unsupported keys")
    result = {}
    for key, item in value.items():
        if item is None:
            continue
        if key == "track":
            result[key] = _choice(item, "track", TRACKS)
        else:
            result[key] = safe_id(str(item))
    return result


# Payload validators run in the browser endpoint and again at import time.
Validator = Callable[[dict], dict]
VALIDATORS: dict[str, Validator] = {}
# Handlers run at apply time against the local journal.
Handler = Callable[[Store, dict], dict]
HANDLERS: dict[str, Handler] = {}
# Request types whose base record must exist and match a version.
BASE_KINDS: dict[str, str] = {}


def request_type(name: str, base_kind: str | None = None):
    """Register a validator/handler pair for one request type."""

    def register(pair: tuple[Validator, Handler]):
        VALIDATORS[name], HANDLERS[name] = pair
        if base_kind:
            BASE_KINDS[name] = base_kind
        return pair

    return register


def validate_request(data: object) -> dict:
    """Normalise and validate a request; raises ValueError with a safe message."""
    if not isinstance(data, dict):
        raise ValueError("Request must be a JSON object")  # noqa: TRY004
    kind = data.get("type")
    if kind not in VALIDATORS:
        raise ValueError("Unsupported request type")
    payload = data.get("payload") or {}
    if not isinstance(payload, dict):
        raise ValueError("payload must be an object")  # noqa: TRY004
    created = data.get("created_at") or now()
    try:
        datetime.fromisoformat(str(created))
    except ValueError:
        raise ValueError("created_at must be an ISO timestamp") from None
    request = {
        "schema_version": SCHEMA_VERSION,
        "id": safe_id(str(data.get("id") or "req-" + uuid4().hex)),
        "type": kind,
        "created_at": str(created),
        "base": None,
        "payload": VALIDATORS[kind](payload),
    }
    base = data.get("base")
    if kind in BASE_KINDS:
        if not isinstance(base, dict):
            raise ValueError("This request needs the record it changes")
        if base.get("kind") != BASE_KINDS[kind]:
            raise ValueError("Request base kind does not match its type")
        version = base.get("version")
        if version is not None and not re.fullmatch(r"[0-9a-f]{16}", str(version)):
            raise ValueError("Base version must be a 16-character hex digest")
        request["base"] = {
            "kind": base["kind"],
            "id": safe_id(str(base.get("id"))),
            "version": version,
        }
    if len(encode(request).encode()) > MAX_REQUEST_BYTES:
        raise ValueError("Request is too large")
    return request


def write_request(state_dir: Path, data: object) -> dict:
    request = validate_request(data)
    folder = state_dir / REQUEST_DIR
    folder.mkdir(parents=True, exist_ok=True, mode=0o700)
    atomic_write(folder / f"{request['id']}.json", encode(request))
    return request


def pending_files(state_dir: Path | None) -> list[dict]:
    """Requests stored by a dashboard, newest last; unreadable files are skipped."""
    if state_dir is None or not (state_dir / REQUEST_DIR).is_dir():
        return []
    requests = []
    for path in sorted((state_dir / REQUEST_DIR).glob("*.json")):
        try:
            requests.append(validate_request(json.loads(path.read_text(encoding="utf-8"))))
        except (OSError, ValueError):
            continue
    return sorted(requests, key=lambda item: (item["created_at"], item["id"]))


def import_requests(store: Store, source: Path) -> dict:
    """Copy request files (a directory or one JSON file/array) into the journal as pending."""
    paths = sorted(source.glob("*.json")) if source.is_dir() else [source]
    imported = skipped = invalid = 0
    store.db.execute("BEGIN IMMEDIATE")
    try:
        for path in paths:
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                invalid += 1
                continue
            for item in raw if isinstance(raw, list) else [raw]:
                try:
                    request = validate_request(item)
                except ValueError:
                    invalid += 1
                    continue
                if store.get("inbox_requests", request["id"]):
                    skipped += 1
                    continue
                store.put(
                    "inbox_requests",
                    {
                        **request,
                        "status": "pending",
                        "imported_at": now(),
                        "result": None,
                        "error": None,
                    },
                )
                imported += 1
        if imported:
            store.event("inbox_imported", [], {"imported": imported})
        store.db.execute("COMMIT")
    except Exception:
        store.db.execute("ROLLBACK")
        raise
    return {"imported": imported, "already_imported": skipped, "invalid": invalid}


def apply_requests(store: Store, request_id: str | None = None) -> dict:
    """Apply pending requests in creation order, each in its own transaction."""
    pending = [
        item
        for item in store.all("inbox_requests")
        if item["status"] == "pending" and (request_id is None or item["id"] == request_id)
    ]
    if request_id and not pending:
        raise ValueError("Pending request not found")
    outcome = []
    for request in sorted(pending, key=lambda item: (item["created_at"], item["id"])):
        store.db.execute("BEGIN IMMEDIATE")
        try:
            base = request.get("base")
            if base:
                current = store.version(base["kind"], base["id"])
                if current is None:
                    raise ValueError("The record this request changes no longer exists")
                if base.get("version") and current != base["version"]:
                    raise VersionConflict("The record changed after the request was made")
            result = HANDLERS[request["type"]](store, request)
            status = "queued_for_agent" if result.get("task_id") else "applied"
            store.put(
                "inbox_requests",
                {**request, "status": status, "result": result, "applied_at": now()},
            )
            store.event(
                "inbox_request_applied",
                [request["id"]],
                {"type": request["type"], "status": status},
            )
            store.db.execute("COMMIT")
        except VersionConflict as error:
            store.db.execute("ROLLBACK")
            status, result = "conflict", str(error)
        except ValueError as error:
            store.db.execute("ROLLBACK")
            status, result = "failed", str(error)
        except Exception:
            store.db.execute("ROLLBACK")
            raise
        else:
            outcome.append({"id": request["id"], "type": request["type"], "status": status})
            continue
        store.db.execute("BEGIN IMMEDIATE")
        store.put(
            "inbox_requests", {**request, "status": status, "error": result, "applied_at": now()}
        )
        store.event(
            "inbox_request_applied", [request["id"]], {"type": request["type"], "status": status}
        )
        store.db.execute("COMMIT")
        outcome.append(
            {"id": request["id"], "type": request["type"], "status": status, "error": result}
        )
    return {"processed": len(outcome), "requests": outcome}


def reject_request(store: Store, request_id: str, reason: str) -> dict:
    request = store.get("inbox_requests", request_id)
    if not request or request["status"] != "pending":
        raise ValueError("Pending request not found")
    updated = {
        **request,
        "status": "rejected",
        "error": _text(reason, "reason", 1000),
        "applied_at": now(),
    }
    store.put("inbox_requests", updated)
    store.event("inbox_request_rejected", [request_id], {"type": request["type"]})
    return {"id": request_id, "status": "rejected"}


# --------------------------------------------------------------------------- tasks


def create_task(
    store: Store, task_type: str, related: dict, note: str | None, request_id: str | None
) -> dict:
    task = {
        "id": "task-" + uuid4().hex[:20],
        "type": _choice(task_type, "task_type", TASK_TYPES),
        "skill": TASK_SKILLS[task_type],
        "status": "queued",
        "related": related,
        "note": note,
        "request_id": request_id,
        "activity_id": None,
        "result_refs": [],
        "created_at": now(),
        "updated_at": now(),
    }
    for key, kind in (
        ("vacancy_id", "vacancies"),
        ("company_id", "companies"),
        ("package_id", "packages"),
    ):
        if related.get(key) and not store.get(kind, related[key]):
            raise ValueError(f"Related {key} not found")
    store.put("tasks", task)
    store.event("task_queued", [task["id"], *related.values()], {"type": task_type})
    return task


def next_task(store: Store) -> dict | None:
    queued = [task for task in store.all("tasks") if task["status"] == "queued"]
    if not queued:
        return None
    task = min(queued, key=lambda item: (item["created_at"], item["id"]))
    return {
        **task,
        "activity_request": {
            "schema_version": 1,
            "skill": task["skill"],
            "operation": f"{task['type']} (task {task['id']})",
            "related": {**task["related"], "task_id": task["id"]},
            "actor": {"environment": None, "model": None, "session": None},
            "inputs": [],
            "expected_result": {"types": []},
        },
    }


def bind_task_to_activity(
    store: Store, task_id: str, activity_id: str, *, blocked: bool = False
) -> None:
    """Attach a started activity; a blocked activity (wrong model/session) blocks the task."""
    task = store.get("tasks", task_id)
    if not task:
        raise ValueError("Related task not found")
    if task["status"] not in {"queued", "blocked", "failed"}:
        raise ValueError("Task is not waiting for an agent")
    status = "blocked" if blocked else "running"
    store.put("tasks", {**task, "status": status, "activity_id": activity_id, "updated_at": now()})
    store.event("task_started", [task_id, activity_id], {"status": status})


def close_task_from_activity(store: Store, activity: dict) -> None:
    """Mirror the real activity outcome onto its task; never mark done without it."""
    task_id = (activity.get("related") or {}).get("task_id")
    task = store.get("tasks", task_id) if task_id else None
    if not task or task.get("activity_id") != activity["id"]:
        return
    status = {"completed": "done", "blocked": "blocked", "failed": "failed"}.get(activity["status"])
    if not status:
        return
    store.put(
        "tasks",
        {
            **task,
            "status": status,
            "result_refs": activity.get("records") or [],
            "next_action": activity.get("next_action"),
            "updated_at": now(),
        },
    )
    store.event("task_closed", [task_id, activity["id"]], {"status": status})


# --------------------------------------------------------------------------- stage 0 request types


def _validate_task(payload: dict) -> dict:
    return {
        "task_type": _choice(payload.get("task_type"), "task_type", TASK_TYPES),
        "related": _related(payload.get("related")),
        "note": _text(payload.get("note"), "note", 2000, required=False),
    }


def _apply_task(store: Store, request: dict) -> dict:
    payload = request["payload"]
    task = create_task(
        store, payload["task_type"], payload["related"], payload["note"], request["id"]
    )
    return {"task_id": task["id"]}


request_type("task")((_validate_task, _apply_task))


def _validate_decision(payload: dict) -> dict:
    return {
        "status": _choice(
            payload.get("status"), "status", {"not_interested", "interested", "cleared"}
        ),
        "reason": _text(
            payload.get("reason"),
            "reason",
            1000,
            required=payload.get("status") == "not_interested",
        ),
    }


def _apply_decision(store: Store, request: dict) -> dict:
    payload, key = request["payload"], request["base"]["id"]
    decision = None if payload["status"] == "cleared" else {**payload, "at": request["created_at"]}
    store.patch(
        "vacancies",
        key,
        {"personal_decision": decision},
        None,
        "personal decision from the dashboard",
    )
    return {"vacancy_id": key, "personal_decision": payload["status"]}


request_type("vacancy_decision", "vacancies")((_validate_decision, _apply_decision))


def _validate_clarification(payload: dict) -> dict:
    return {
        "question": _text(payload.get("question"), "question", 1000),
        "answer": _text(payload.get("answer"), "answer", 4000),
        "requirement_id": safe_id(str(payload["requirement_id"]))
        if payload.get("requirement_id")
        else None,
        "source": _text(payload.get("source"), "source", 500, required=False),
    }


def _apply_clarification(store: Store, request: dict) -> dict:
    key = request["base"]["id"]
    vacancy = store.get("vacancies", key)
    entry = {
        **request["payload"],
        "at": request["created_at"],
        "request_id": request["id"],
        "reviewed": False,
    }
    clarifications = [*(vacancy.get("clarifications") or []), entry]
    store.patch(
        "vacancies",
        key,
        {"clarifications": clarifications},
        None,
        "clarification answer from the dashboard",
    )
    return {"vacancy_id": key, "clarifications": len(clarifications)}


request_type("clarification_answer", "vacancies")((_validate_clarification, _apply_clarification))


def _validate_coding(payload: dict) -> dict:
    return {
        "status": _choice(payload.get("status"), "status", {"required", "not_required", "unknown"}),
        "basis": _text(payload.get("basis"), "basis", 1000),
        "source": _text(payload.get("source"), "source", 500, required=False),
        "date": _text(payload.get("date"), "date", 40, required=False),
    }


def _apply_coding(store: Store, request: dict) -> dict:
    key = request["base"]["id"]
    coding = {
        **request["payload"],
        "recorded_at": request["created_at"],
        "recorded_by": "dashboard-request",
    }
    store.patch(
        "vacancies",
        key,
        {"coding_requirement": coding},
        None,
        "coding requirement from the dashboard",
    )
    return {"vacancy_id": key, "coding_requirement": coding["status"]}


request_type("coding_requirement", "vacancies")((_validate_coding, _apply_coding))


def _validate_evaluate(payload: dict) -> dict:
    return {
        "vacancy_id": safe_id(str(payload.get("vacancy_id"))),
        "track": _choice(payload.get("track"), "track", TRACKS),
    }


def _apply_evaluate(store: Store, request: dict) -> dict:
    from . import workflow

    payload = request["payload"]
    result = workflow.evaluate(store, payload["vacancy_id"], payload["track"])
    return {"assessment_ids": [item["id"] for item in result]}


request_type("evaluate")((_validate_evaluate, _apply_evaluate))


# --------------------------------------------------------------------------- stage 1 request types


def _validate_vacancy_add(payload: dict) -> dict:
    url = _text(payload.get("url"), "url", 2000, required=False)
    text = _text(payload.get("text"), "text", 100_000, required=False)
    if bool(url) == bool(text):
        raise ValueError("Give either a link or the vacancy text")
    if url and not re.match(r"^https?://", url):
        raise ValueError("url must start with http:// or https://")
    market = payload.get("market") or None
    if market not in (None, "ru", "intl", "unknown"):
        raise ValueError("market must be ru, intl or unknown")
    return {
        "url": url,
        "text": text,
        "title": _text(payload.get("title"), "title", 200, required=False),
        "company_name": _text(payload.get("company_name"), "company_name", 200, required=False),
        "company_id": safe_id(str(payload["company_id"])) if payload.get("company_id") else None,
        "location": _text(payload.get("location"), "location", 200, required=False),
        "posting_url": _text(payload.get("posting_url"), "posting_url", 2000, required=False),
        "market": market,
        "track": _choice(payload["track"], "track", TRACKS) if payload.get("track") else None,
    }


def _apply_vacancy_add(store: Store, request: dict) -> dict:
    from . import intake

    payload = request["payload"]
    if payload["url"]:
        return intake.from_url(
            store,
            payload["url"],
            company_id=payload["company_id"],
            market=payload["market"],
            track=payload["track"],
        )
    return intake.from_text(
        store,
        payload["text"],
        title=payload["title"],
        company_name=payload["company_name"],
        company_id=payload["company_id"],
        url=payload["posting_url"],
        location=payload["location"],
        market=payload["market"],
        track=payload["track"],
    )


request_type("vacancy_add")((_validate_vacancy_add, _apply_vacancy_add))


def _validate_campaign(payload: dict) -> dict:
    from . import campaigns

    expected = payload.get("expected_version")
    if expected is not None and not re.fullmatch(r"[0-9a-f]{16}", str(expected)):
        raise ValueError("expected_version must be a 16-character hex digest")
    return {"campaign": campaigns.validate(payload.get("campaign")), "expected_version": expected}


def _apply_campaign(store: Store, request: dict) -> dict:
    from . import campaigns
    from .core import digest

    payload = request["payload"]
    settings = store.settings
    updated, previous = campaigns.upsert(settings, payload["campaign"])
    current = digest(previous)[:16] if previous else None
    if current != payload["expected_version"]:
        raise VersionConflict("The campaign changed after the request was made")
    store.event(
        "campaigns_updated",
        [payload["campaign"]["id"]],
        {"before": previous, "after": payload["campaign"], "request_id": request["id"]},
    )
    atomic_write(store.home / "settings.json", encode(updated))
    return {"campaign_id": payload["campaign"]["id"], "created": previous is None}


request_type("campaign_upsert")((_validate_campaign, _apply_campaign))


# --------------------------------------------------------------------------- stage 3 request types


def _validate_cv_decision(payload: dict) -> dict:
    decision = _choice(payload.get("decision"), "decision", {"accept", "reject", "edit"})
    return {
        "proposal_id": safe_id(str(payload.get("proposal_id"))),
        "edit_id": safe_id(str(payload.get("edit_id"))),
        "decision": decision,
        "text": _text(payload.get("text"), "text", 4000, required=decision == "edit"),
        "note": _text(payload.get("note"), "note", 1000, required=False),
    }


def _apply_cv_decision(store: Store, request: dict) -> dict:
    from . import cv

    value = cv.record_decision(store, request["payload"], request["id"])
    return {"decision_id": value["id"], "edit_id": value["edit_id"], "decision": value["decision"]}


request_type("cv_edit_decision", "cv_edits")((_validate_cv_decision, _apply_cv_decision))


def _validate_cv_import(payload: dict) -> dict:
    return {
        "track": _choice(payload.get("track"), "track", TRACKS),
        "text": _text(payload.get("text"), "text", 35_000),
        "filename": _text(payload.get("filename") or "pasted-cv.md", "filename", 120),
    }


def _apply_cv_import(store: Store, request: dict) -> dict:
    from . import cv

    payload = request["payload"]
    value = cv.import_cv(store, payload["text"], payload["track"], payload["filename"])
    return {"import_id": value["id"], "task_id": value["task_id"]}


request_type("cv_import")((_validate_cv_import, _apply_cv_import))


# --------------------------------------------------------------------------- stage 4 request types


def _validate_prep_plan(payload: dict) -> dict:
    hours = payload.get("hours")
    if isinstance(hours, bool) or not isinstance(hours, (int, float)):
        raise ValueError("hours must be a number")  # noqa: TRY004
    vacancies = payload.get("vacancy_ids") or []
    if not isinstance(vacancies, list):
        raise ValueError("vacancy_ids must be a list")  # noqa: TRY004
    return {
        "track": _choice(payload.get("track"), "track", TRACKS),
        "goal": _text(payload.get("goal"), "goal", 500),
        "hours": hours,
        "experience": _text(payload.get("experience"), "experience", 2000, required=False),
        "vacancy_ids": [safe_id(str(item)) for item in vacancies][:50],
    }


def _apply_prep_plan(store: Store, request: dict) -> dict:
    from . import preparation

    p = request["payload"]
    plan = preparation.track_plan(
        store, p["track"], p["goal"], p["hours"], p["experience"], p["vacancy_ids"] or None
    )
    return {"plan_id": plan["id"], "basis": plan["basis"]["kind"], "topics": len(plan["topics"])}


request_type("prep_plan")((_validate_prep_plan, _apply_prep_plan))


def _validate_prep_create(payload: dict) -> dict:
    from . import preparation

    def optional_id(key: str) -> str | None:
        return safe_id(str(payload[key])) if payload.get(key) else None

    return {
        "track": _choice(payload["track"], "track", TRACKS) if payload.get("track") else None,
        "vacancy_id": optional_id("vacancy_id"),
        "plan_id": optional_id("plan_id"),
        "topic_id": optional_id("topic_id"),
        "question": _text(payload.get("question"), "question", 1000),
        "type": _choice(payload.get("type"), "type", preparation.QUESTION_TYPES),
        "tests": _text(payload.get("tests"), "tests", 500),
        "provenance": _choice(payload.get("provenance"), "provenance", preparation.PROVENANCE),
        "source": payload.get("source") if isinstance(payload.get("source"), dict) else None,
    }


def _apply_prep_create(store: Store, request: dict) -> dict:
    from . import preparation

    session = preparation.create_session(store, request["payload"])
    return {"session_id": session["id"]}


request_type("prep_create")((_validate_prep_create, _apply_prep_create))


def _validate_practice_answer(payload: dict) -> dict:
    def optional_id(key: str) -> str | None:
        return safe_id(str(payload[key])) if payload.get(key) else None

    return {
        "session_id": safe_id(str(payload.get("session_id"))),
        "answer": _text(payload.get("answer"), "answer", 12_000),
        "previous_attempt_id": optional_id("previous_attempt_id"),
        "follow_up_to": optional_id("follow_up_to"),
    }


def _apply_practice_answer(store: Store, request: dict) -> dict:
    from . import preparation

    attempt = preparation.submit_answer(store, request["payload"], request["id"])
    return {"attempt_id": attempt["id"], "task_id": attempt["task_id"]}


request_type("practice_answer")((_validate_practice_answer, _apply_practice_answer))
