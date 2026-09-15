"""CV module: version states, edit proposals and decisions, draft assembly and CV import.

Two scenarios share one model:

* fix a master CV (exactly one per track: `master-product`, `master-technical-leadership`);
* tailor a version for a vacancy. A vacancy version records `based_on` (the master
  version it started from); tailoring never writes to the master package.

An agent proposes edits (`cv_edit_proposal` activity result → `cv_edits`): each edit is
before → after → reason → facts. The user accepts, rejects or edits each one
(`cv_edit_decision` requests → `cv_edit_decisions`, full history). `ajh cv apply-edits`
assembles a draft from accepted edits; a new version still goes through `prepare` with
flagship authorship and independent content and visual reviews. Accepting an edit
never replaces a review, and nothing adds a skill without a verified fact.
"""

from __future__ import annotations

import re
from pathlib import Path
from uuid import uuid4

from .core import FLAGSHIPS, TRACKS, Store, atomic_write, digest, encode, now, read_json, safe_id

EDIT_KINDS = frozenset({"wording", "emphasis", "reorder", "add_evidence", "remove"})
DECISIONS = frozenset({"accept", "reject", "edit"})
STATES = (
    "invalid",
    "draft",
    "awaiting_facts",
    "written",
    "awaiting_content_review",
    "awaiting_visual_review",
    "ready",
)
COVERAGE_STATUSES = frozenset({"covered", "not_evidenced", "not_applicable"})
MAX_IMPORT_CHARS = 60_000


def version_state(
    version: dict, integrity_errors: list[str], reviews: list[dict], coverage: list | None
) -> dict:
    """Derive the state of one exact version; reasons explain the next step."""
    if integrity_errors:
        return {"state": "invalid", "reasons": integrity_errors}
    if not version.get("author_model"):
        return {"state": "draft", "reasons": ["mechanical_source"]}
    if isinstance(coverage, list) and any(
        isinstance(row, dict) and row.get("included") is None for row in coverage
    ):
        return {"state": "awaiting_facts", "reasons": ["coverage_unreconciled"]}
    latest = {}
    for review in reviews:
        if isinstance(review, dict) and review.get("kind") in {"content", "visual"}:
            latest[review["kind"]] = review
    if not latest:
        return {"state": "written", "reasons": ["no_reviews"]}
    if latest.get("content", {}).get("passed") is not True:
        return {"state": "awaiting_content_review", "reasons": ["content_review_missing_or_failed"]}
    if latest.get("visual", {}).get("passed") is not True:
        return {"state": "awaiting_visual_review", "reasons": ["visual_review_missing_or_failed"]}
    if version.get("review_status") != "passed":
        return {"state": "awaiting_content_review", "reasons": ["review_status_pending"]}
    return {"state": "ready", "reasons": []}


def state_for(store: Store, package: dict, version: dict) -> dict:
    from .workflow import version_checks

    reviews = []
    for path in version.get("reviews", []):
        try:
            reviews.append(read_json(store.path(path)))
        except (OSError, ValueError):
            continue
    coverage = None
    if version.get("files", {}).get("coverage"):
        try:
            coverage = read_json(store.path(version["files"]["coverage"]))
        except (OSError, ValueError):
            coverage = None
    return version_state(version, version_checks(store, version), reviews, coverage)


def cv_source(store: Store, version: dict) -> str:
    return store.path(version["files"]["cv_source"]).read_text(encoding="utf-8")


# --------------------------------------------------------------------------- proposals


def validate_proposal(store: Store, data: dict, activity: dict) -> dict:
    """Validate a `cv_edit_proposal` result; called from activity registration."""
    from .activity import package_version

    if activity["actor"]["model"] not in FLAGSHIPS.values() or not activity["actor"]["session"]:
        raise ValueError("CV edit proposals require an actual flagship actor and session")
    package, version = package_version(
        store, data.get("package_id", ""), data.get("version_id", "")
    )
    text = cv_source(store, version)
    facts = {fact["id"]: fact for fact in store.facts["facts"]}
    vacancy = (
        store.get("vacancies", package["vacancy_id"]) if package["vacancy_id"] != "master" else None
    )
    requirement_ids = {item["id"] for item in (vacancy or {}).get("requirements", [])}
    edits = data.get("edits")
    if not isinstance(edits, list) or not edits:
        raise ValueError("cv_edit_proposal requires a non-empty edits list")
    seen, normalized = set(), []
    for edit in edits:
        if not isinstance(edit, dict):
            raise ValueError("Each edit must be an object")  # noqa: TRY004
        key = safe_id(str(edit.get("id") or ""))
        if key in seen:
            raise ValueError(f"Duplicate edit id {key}")
        seen.add(key)
        kind = edit.get("kind")
        if kind not in EDIT_KINDS:
            raise ValueError(f"Edit {key}: kind must be one of {sorted(EDIT_KINDS)}")
        before, after = edit.get("before", ""), edit.get("after", "")
        if not isinstance(before, str) or not isinstance(after, str):
            raise ValueError(f"Edit {key}: before and after must be text")  # noqa: TRY004
        if before and before not in text:
            raise ValueError(f"Edit {key}: 'before' must quote the current CV text exactly")
        if not before and kind != "add_evidence":
            raise ValueError(f"Edit {key}: only add_evidence may insert new text without 'before'")
        if kind == "remove" and after:
            raise ValueError(f"Edit {key}: a removal has an empty 'after'")
        if not isinstance(edit.get("reason"), str) or not edit["reason"].strip():
            raise ValueError(f"Edit {key}: a reason is required")
        fact_ids = edit.get("fact_ids") or []
        if not isinstance(fact_ids, list) or any(item not in facts for item in fact_ids):
            raise ValueError(f"Edit {key}: fact_ids must reference existing facts")
        if kind == "add_evidence" and (
            not fact_ids or any(facts[item].get("verification") != "verified" for item in fact_ids)
        ):
            raise ValueError(f"Edit {key}: new evidence needs verified facts")
        unknown = set(edit.get("requirement_ids") or []) - requirement_ids
        if unknown:
            raise ValueError(f"Edit {key}: unknown requirement IDs {sorted(unknown)}")
        needs_input = edit.get("needs_candidate_input") is True
        if needs_input and not (isinstance(edit.get("question"), str) and edit["question"].strip()):
            raise ValueError(f"Edit {key}: a question for the candidate is required")
        if kind == "add_evidence" and not before and not edit.get("section"):
            raise ValueError(f"Edit {key}: inserting new text needs the target section")
        normalized.append(
            {
                "id": key,
                "kind": kind,
                "section": str(edit.get("section") or ""),
                "before": before,
                "after": after,
                "reason": edit["reason"].strip(),
                "fact_ids": fact_ids,
                "requirement_ids": list(edit.get("requirement_ids") or []),
                "needs_candidate_input": needs_input,
                "question": edit.get("question") if needs_input else None,
            }
        )
    return {
        **data,
        "package_id": package["id"],
        "version_id": version["id"],
        "scope": "master" if package["vacancy_id"] == "master" else "vacancy",
        "vacancy_id": package["vacancy_id"],
        "track": package["track"],
        "cv_source_sha256": version["sha256"]["cv_source"],
        "edits": normalized,
    }


def decisions_for(store: Store, proposal_id: str) -> dict[str, dict]:
    """Latest decision per edit; decisions are immutable history in insertion order."""
    latest: dict[str, dict] = {}
    for item in store.insertion_order("cv_edit_decisions"):
        if item.get("proposal_id") == proposal_id:
            latest[item["edit_id"]] = item
    return latest


def record_decision(store: Store, payload: dict, request_id: str | None = None) -> dict:
    proposal = store.get("cv_edits", payload["proposal_id"])
    if not proposal:
        raise ValueError("CV edit proposal not found")
    edit = next((item for item in proposal["edits"] if item["id"] == payload["edit_id"]), None)
    if not edit:
        raise ValueError("Edit not found in the proposal")
    if payload["decision"] == "edit" and not (payload.get("text") or "").strip():
        raise ValueError("An edited decision needs the replacement text")
    if payload["decision"] == "edit" and edit["kind"] == "remove":
        raise ValueError("A removal can only be accepted or rejected")
    value = {
        "id": "cvd-" + uuid4().hex[:20],
        "proposal_id": proposal["id"],
        "edit_id": edit["id"],
        "decision": payload["decision"],
        "text": payload.get("text") if payload["decision"] == "edit" else None,
        "note": payload.get("note"),
        "decided_at": now(),
        # Position in this proposal's history, so readers without row order agree on "latest".
        "sequence": 1
        + sum(
            1
            for item in store.all("cv_edit_decisions")
            if item.get("proposal_id") == proposal["id"]
        ),
        "request_id": request_id,
        "decided_by": "user",
    }
    store.put("cv_edit_decisions", value, immutable=True)
    store.event("cv_edit_decided", [proposal["id"], edit["id"]], {"decision": value["decision"]})
    return value


def apply_edits(store: Store, proposal_id: str, output: Path) -> dict:
    """Assemble a draft from accepted edits; the draft is not a version and not reviewed."""
    from .activity import package_version

    proposal = store.get("cv_edits", proposal_id)
    if not proposal:
        raise ValueError("CV edit proposal not found")
    _, version = package_version(store, proposal["package_id"], proposal["version_id"])
    text = cv_source(store, version)
    if digest(text.encode()) != proposal["cv_source_sha256"]:
        raise ValueError("The CV source changed after the proposal; request a new proposal")
    decisions = decisions_for(store, proposal_id)
    applied, rejected, undecided, conflicts = [], [], [], []
    for edit in proposal["edits"]:
        decision = decisions.get(edit["id"])
        if not decision:
            undecided.append(edit["id"])
            continue
        if decision["decision"] == "reject":
            rejected.append(edit["id"])
            continue
        replacement = decision["text"] if decision["decision"] == "edit" else edit["after"]
        if edit["before"]:
            if text.count(edit["before"]) < 1:
                conflicts.append(edit["id"])
                continue
            text = text.replace(edit["before"], replacement, 1)
        else:
            lines = text.splitlines(keepends=True)
            index = next(
                (
                    i
                    for i, line in enumerate(lines)
                    if line.lstrip().startswith("#")
                    and edit["section"].casefold() in line.casefold()
                ),
                None,
            )
            if index is None:
                conflicts.append(edit["id"])
                continue
            lines.insert(index + 1, replacement.rstrip("\n") + "\n")
            text = "".join(lines)
        applied.append(edit["id"])
    atomic_write(output, text)
    summary = {
        "proposal_id": proposal_id,
        "output": str(output),
        "sha256": digest(text.encode()),
        "applied": applied,
        "rejected": rejected,
        "undecided": undecided,
        "conflicts": conflicts,
        "next_action": "Author the new version with prepare --based-on and run content and visual reviews",
    }
    store.event(
        "cv_edits_assembled", [proposal_id], {k: v for k, v in summary.items() if k != "output"}
    )
    return summary


# --------------------------------------------------------------------------- requirement coverage


def validate_requirement_coverage(rows: object, vacancy: dict, facts: dict) -> list[dict]:
    if not isinstance(rows, list):
        raise ValueError("Requirement coverage must be a list")  # noqa: TRY004
    requirements = {item["id"] for item in vacancy.get("requirements", [])}
    verified = {f["id"] for f in facts["facts"] if f.get("verification") == "verified"}
    seen, result = set(), []
    for row in rows:
        if not isinstance(row, dict) or row.get("requirement_id") not in requirements:
            raise ValueError("Coverage rows must reference the vacancy's requirements")
        if row["requirement_id"] in seen:
            raise ValueError("Each requirement appears once in the coverage")
        seen.add(row["requirement_id"])
        if row.get("status") not in COVERAGE_STATUSES:
            raise ValueError(f"Coverage status must be one of {sorted(COVERAGE_STATUSES)}")
        fact_ids = row.get("fact_ids") or []
        if row["status"] == "covered" and (not fact_ids or set(fact_ids) - verified):
            raise ValueError("A covered requirement needs verified fact IDs")
        if row["status"] == "covered" and not row.get("cv_location"):
            raise ValueError("A covered requirement names where the CV shows it")
        result.append(
            {
                "requirement_id": row["requirement_id"],
                "status": row["status"],
                "cv_location": row.get("cv_location"),
                "fact_ids": fact_ids,
                "note": row.get("note"),
            }
        )
    missing = requirements - seen
    if missing:
        raise ValueError(f"Coverage is missing requirements {sorted(missing)}")
    return result


# --------------------------------------------------------------------------- import


DATE_RANGE = re.compile(
    r"(?P<start>(?:19|20)\d{2}(?:[-./]\d{1,2})?)\s*(?:[-–—]|to|по|до)\s*(?P<end>(?:19|20)\d{2}(?:[-./]\d{1,2})?|present|now|current|н\.?\s?в\.?|настоящее время)",
    re.IGNORECASE,
)
CLAIM = re.compile(
    r"\d+(?:[.,]\d+)?\s*(?:%|x\b|×|млн|млрд|k\b|m\b|bn\b|\+)|\b(?:led|grew|increased|reduced|увелич|сократ|вырос|руководил)",
    re.IGNORECASE,
)


def read_cv_file(path: Path) -> str:
    suffix = path.suffix.casefold()
    if suffix == ".pdf":
        from pypdf import PdfReader

        return "\n\n".join(page.extract_text() or "" for page in PdfReader(path).pages)
    if suffix in {".md", ".txt"}:
        return path.read_text(encoding="utf-8")
    raise ValueError("CV import supports .md, .txt and .pdf")


def extract_structure(text: str) -> dict:
    """Sections, date ranges and lines with claims to check; no fact is created here."""
    sections, current = [], {"title": "", "lines": []}
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        heading = re.match(r"^#{1,6}\s+(.*)$", line)
        upper = len(line) <= 60 and line.upper() == line and re.search(r"[A-ZА-ЯЁ]{3}", line)
        if heading or upper:
            if current["title"] or current["lines"]:
                sections.append(current)
            current = {"title": (heading.group(1) if heading else line).strip(), "lines": []}
        else:
            current["lines"].append(line)
    if current["title"] or current["lines"]:
        sections.append(current)
    dates = [
        {"text": match.group(0), "start": match.group("start"), "end": match.group("end")}
        for match in DATE_RANGE.finditer(text)
    ]
    claims = [line.strip() for line in text.splitlines() if line.strip() and CLAIM.search(line)]
    return {
        "sections": [{"title": s["title"], "lines": len(s["lines"])} for s in sections],
        "dates": dates[:100],
        "claims_to_check": claims[:200],
        "characters": len(text),
    }


def import_cv(
    store: Store, text: str, track: str, filename: str, original: bytes | None = None
) -> dict:
    from . import inbox

    if track not in TRACKS:
        raise ValueError("Unknown career track")
    if not isinstance(text, str) or len(text.strip()) < 100 or len(text) > MAX_IMPORT_CHARS:
        raise ValueError("CV text must be 100 to 60000 characters; check that extraction worked")
    stem = Path(filename or "cv").stem
    source_path = store.readable_artifact(
        "evidence/cv-imports",
        [track, stem],
        original if original is not None else text,
        Path(filename or "cv.md").suffix or ".md",
    )
    text_path = store.readable_artifact("evidence/cv-imports", [track, stem, "text"], text, ".txt")
    structure = extract_structure(text)
    key = "cvi-" + digest([track, text])[:20]
    existing = store.get("cv_imports", key)
    if existing:
        return existing
    task = inbox.create_task(
        store,
        "extract_cv_facts",
        {"track": track, "import_id": key},
        "Propose facts from the imported CV; import them only after verification (ajh facts import).",
        None,
    )
    value = {
        "id": key,
        "track": track,
        "filename": filename,
        "source": {
            "path": source_path,
            "sha256": digest(original if original is not None else text.encode()),
        },
        "text": {"path": text_path, "sha256": digest(text.encode())},
        **structure,
        "task_id": task["id"],
        "imported_at": now(),
        "note": "Extraction only. Facts are created solely through a verified facts import.",
    }
    store.put("cv_imports", value, immutable=True)
    store.event(
        "cv_imported", [key, task["id"]], {"track": track, "sections": len(structure["sections"])}
    )
    return value


def overview(store: Store) -> dict:
    """Masters per track and vacancy versions with their states (for CLI `cv status`)."""
    result = {"masters": {}, "vacancies": []}
    for package in store.all("packages"):
        versions = package.get("versions") or []
        current = next((v for v in versions if v["id"] == package.get("current_version")), None)
        if not current:
            continue
        entry = {
            "package_id": package["id"],
            "track": package["track"],
            "version_id": current["id"],
            "based_on": current.get("based_on"),
            **state_for(store, package, current),
            "pdf": current.get("files", {}).get("cv_pdf"),
        }
        if package["vacancy_id"] == "master":
            result["masters"][package["track"]] = entry
        else:
            result["vacancies"].append({**entry, "vacancy_id": package["vacancy_id"]})
    for track in TRACKS:
        result["masters"].setdefault(track, None)
    return result


def dump(value: dict) -> str:
    return encode(value)
