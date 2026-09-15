"""Explainable fit: requirement matrix, mandatory constraints, preferences and completeness.

The result answers "do we fit" without a score or a hiring probability:

* `insufficient_data`  — no annotated requirements or no verified facts for the track;
* `not_fit_mandatory`  — a confirmed mandatory mismatch with its basis;
* `has_questions`      — a mandatory requirement or constraint is unknown or needs preparation;
* `fits_verified`      — every mandatory requirement is backed by reviewed verified facts
                         and every mandatory constraint passes.

A missing word in the CV is never a missing experience: verified facts that look relevant
but are not yet reviewed make a requirement `unknown` with a CV action, never a `gap`.
Search campaigns are preferences and never change the outcome.
"""

from __future__ import annotations

import re

from .core import TRACKS, digest, safe_id

METHOD = "evidence-rules-v2"
OUTCOMES = (
    "not_assessed",
    "insufficient_data",
    "fits_verified",
    "has_questions",
    "not_fit_mandatory",
)
GAP_TYPES = frozenset({"knowledge", "practice", "experience_framing", "structural"})
ACTIONS = frozenset({"cv_edit", "preparation", "clarify", "decision_basis", "none"})
# Vacancy fields that describe where or when a record was seen, or a personal choice,
# rather than what the role requires. They do not make an assessment stale.
VOLATILE_VACANCY_FIELDS = frozenset(
    {
        "last_seen",
        "source_observation",
        "status_checked_on",
        "availability",
        "availability_basis",
        "availability_check",
        "availability_history",
        "personal_decision",
        "next_action",
        "decision",
        "review_status",
        "reviewed_on",
        "assessments",
        "coding_requirement",
    }
)


def validate_requirements(requirements: object, fact_ids: set[str] | None = None) -> list[dict]:
    """Check an annotated requirement list before it is stored on a vacancy."""
    if not isinstance(requirements, list):
        raise ValueError("requirements must be a list")  # noqa: TRY004
    seen, result = set(), []
    for item in requirements:
        if not isinstance(item, dict):
            raise ValueError("Each requirement must be an object")  # noqa: TRY004
        key = safe_id(str(item.get("id") or ""))
        if key in seen:
            raise ValueError(f"Duplicate requirement id {key}")
        seen.add(key)
        if not isinstance(item.get("text"), str) or not item["text"].strip():
            raise ValueError(f"Requirement {key} needs text")
        if not isinstance(item.get("mandatory", False), bool):
            raise ValueError(f"Requirement {key}: mandatory must be true or false")  # noqa: TRY004
        if item.get("gap_type", "knowledge") not in GAP_TYPES:
            raise ValueError(f"Requirement {key}: gap_type must be one of {sorted(GAP_TYPES)}")
        if item.get("category", "qualification") not in {"qualification", "constraint"}:
            raise ValueError(f"Requirement {key}: category must be qualification or constraint")
        evidence = item.get("evidence_fact_ids", [])
        if not isinstance(evidence, list) or not all(isinstance(value, str) for value in evidence):
            raise ValueError(f"Requirement {key}: evidence_fact_ids must be a list of fact IDs")
        if fact_ids is not None and set(evidence) - fact_ids:
            raise ValueError(
                f"Requirement {key}: unknown fact IDs {sorted(set(evidence) - fact_ids)}"
            )
        if not isinstance(item.get("evidence_checked", False), bool):
            raise ValueError(f"Requirement {key}: evidence_checked must be true or false")  # noqa: TRY004
        if not isinstance(item.get("evidence_reviewed", False), bool):
            raise ValueError(f"Requirement {key}: evidence_reviewed must be true or false")  # noqa: TRY004
        years = item.get("minimum_years")
        if years is not None and (
            isinstance(years, bool) or not isinstance(years, (int, float)) or years < 0
        ):
            raise ValueError(f"Requirement {key}: minimum_years must be a positive number")
        result.append({**item, "id": key, "text": item["text"].strip()})
    return result


def input_hashes(vacancy: dict, company: dict, facts: dict, settings: dict) -> dict:
    """Digests of everything an assessment depends on, per part, to explain staleness."""
    return {
        "vacancy": digest({k: v for k, v in vacancy.items() if k not in VOLATILE_VACANCY_FIELDS})[
            :16
        ],
        "company": digest(company or {})[:16],
        "facts": digest(facts.get("facts", []))[:16],
        "policy": digest(settings.get("policy", {}))[:16],
        "candidate": digest(settings.get("candidate", {}))[:16],
    }


def stale_parts(recorded: dict | None, current: dict) -> list[str] | None:
    """Changed input parts, [] when current, None when the assessment predates input tracking."""
    if not isinstance(recorded, dict) or not recorded:
        return None
    return sorted(part for part, value in current.items() if recorded.get(part) != value)


def _fact_source(fact: dict) -> str | None:
    sources = fact.get("sources") or []
    return str(sources[0]) if sources else None


def _norm(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip().casefold()


def requirement_row(requirement: dict, facts: list[dict], candidate: dict, track: str) -> dict:
    by_id = {fact["id"]: fact for fact in facts}
    usable = [
        by_id[key]
        for key in requirement.get("evidence_fact_ids", [])
        if key in by_id
        and by_id[key].get("verification") == "verified"
        and by_id[key].get("claim_type") != "target"
    ]
    suggestions = [
        fact["id"]
        for fact in facts
        if requirement.get("tag")
        and requirement["tag"] in fact.get("tags", [])
        and fact.get("verification") == "verified"
        and track in fact.get("tracks", TRACKS)
        and fact["id"] not in {item["id"] for item in usable}
    ]
    gap_type = requirement.get("gap_type", "knowledge")
    structural = bool(
        requirement.get("minimum_years")
        or requirement.get("authorization")
        or requirement.get("license")
        or gap_type == "structural"
    )
    category = requirement.get("category") or ("constraint" if structural else "qualification")
    row = {
        "requirement_id": requirement["id"],
        "text": requirement["text"],
        "source": requirement.get("source"),
        "category": category,
        "mandatory": requirement.get("mandatory", False) is True,
        "gap_type": "structural" if structural else gap_type,
        "evidence": [
            {
                "fact_id": fact["id"],
                "verification": fact.get("verification"),
                "source": _fact_source(fact),
            }
            for fact in usable
        ],
        "suggested_facts": suggestions,
        # Kept for evidence-rules-v1 readers.
        "covered": bool(usable and requirement.get("evidence_reviewed")),
    }
    authorization = requirement.get("authorization")
    stated = (
        (candidate.get("work_authorization") or {}).get(authorization) if authorization else None
    )
    if requirement.get("confirmed_unmet"):
        status, action, basis = "gap", "decision_basis", str(requirement["confirmed_unmet"])
    elif authorization and stated == "no":
        status, action, basis = (
            "gap",
            "decision_basis",
            f"Candidate settings: no work authorization for {authorization}",
        )
    elif authorization and stated == "yes":
        status, action, basis = (
            "match",
            "none",
            f"Candidate settings: authorized to work in {authorization}",
        )
    elif usable and requirement.get("evidence_reviewed"):
        status, action, basis = "match", "none", "Reviewed verified facts"
    elif usable:
        status, action, basis = (
            "unknown",
            "cv_edit",
            "Verified facts are linked but not reviewed against this requirement",
        )
    elif structural:
        status, action, basis = (
            "unknown",
            "clarify",
            "Needs dated evidence or confirmation; a course cannot close it",
        )
    elif suggestions or gap_type == "experience_framing":
        status, action, basis = (
            "unknown",
            "cv_edit",
            "Experience probably exists in verified facts; confirm it and describe it in the CV",
        )
    elif requirement.get("evidence_checked") is True:
        status, action, basis = (
            "gap",
            "preparation",
            "No verified evidence after comparison; build and demonstrate it",
        )
    else:
        # A tag without matching facts is a word match, not proof of absence: unknown, not a gap.
        status, action, basis = (
            "unknown",
            "clarify",
            "Evidence is not linked yet; annotate which verified facts cover it",
        )
    clarification = next(
        (
            item
            for item in reversed(requirement.get("clarifications") or [])
            if isinstance(item, dict)
        ),
        None,
    )
    row.update(
        status=status,
        basis=basis,
        basis_code=basis_code(basis, requirement),
        action={"type": action, "text": ACTION_TEXT[action]},
    )
    if clarification:
        row["clarification"] = clarification
    return row


# Stable codes for rule-generated bases, so an interface can show them in its language.
BASIS_CODES = {
    "Reviewed verified facts": "reviewed_evidence",
    "Verified facts are linked but not reviewed against this requirement": "unreviewed_evidence",
    "Needs dated evidence or confirmation; a course cannot close it": "structural_unknown",
    "Experience probably exists in verified facts; confirm it and describe it in the CV": "probable_experience",
    "No verified evidence after comparison; build and demonstrate it": "checked_no_evidence",
    "Evidence is not linked yet; annotate which verified facts cover it": "not_linked",
    "Vacancy track annotation": "track_annotated",
    "Vacancy track is not annotated": "track_missing",
    "Recorded gate": "gate_recorded",
    "Not recorded": "gate_not_recorded",
    "Where the work may be done is not stated": "geography_not_stated",
    "Candidate languages cover the requirement": "languages_covered",
    "Requirements are not annotated from a full description": "no_requirements",
    "Company-specific L5+ equivalence needs evidence": "level_mapping_needed",
    "Meets this employer's documented target band": "level_meets_band",
    "Below this employer's target band": "level_below_band",
    "Unmapped employer level": "level_unmapped",
    "Non-bigtech Russian director threshold": "level_director_threshold",
    "Confirm scope and seniority; no cross-company numeric conversion": "level_confirm_scope",
    "No verified candidate facts for this track": "no_verified_facts",
}


def basis_code(basis: str | None, requirement: dict | None = None) -> str | None:
    if requirement and requirement.get("confirmed_unmet"):
        return "confirmed_unmet"
    if basis and basis.startswith("Candidate settings: no work authorization"):
        return "authorization_no"
    if basis and basis.startswith("Candidate settings: authorized"):
        return "authorization_yes"
    if basis and basis.startswith("Allowed: "):
        return "geography_listed"
    if basis and basis.startswith("Not in candidate languages"):
        return "languages_missing"
    return BASIS_CODES.get(basis or "")


ACTION_TEXT = {
    "cv_edit": "Confirm the experience and describe it in the CV",
    "preparation": "Add to preparation: exercise, criterion and a demonstrated result",
    "clarify": "Ask the employer or confirm with the candidate",
    "decision_basis": "Use as the basis for a decision; re-check if the facts change",
    "none": "",
}


def constraints(vacancy: dict, gate: dict, track_verdict: str, candidate: dict) -> list[dict]:
    """Mandatory conditions that are not qualifications: track, level, language, eligibility, geography."""
    to_status = {"pass": "pass", "fail": "fail", "flag": "unknown", None: "unknown"}
    result = [
        {
            "name": "track",
            "status": to_status[track_verdict],
            "basis": "Vacancy track annotation"
            if track_verdict != "flag"
            else "Vacancy track is not annotated",
        },
        {
            "name": "seniority",
            "status": to_status.get(gate.get("verdict"), "unknown"),
            "basis": gate.get("reason"),
        },
    ]
    for name, field in (("language", "language_gate"), ("eligibility", "eligibility_gate")):
        value = vacancy.get(field)
        result.append(
            {
                "name": name,
                "status": to_status.get(value, "unknown"),
                "basis": vacancy.get(f"{field}_basis")
                or ("Recorded gate" if value else "Not recorded"),
            }
        )
    conditions = vacancy.get("conditions") or {}
    geography = conditions.get("allowed_geography") or {}
    countries = {_norm(item) for item in candidate.get("work_countries") or []}
    if countries:
        listed = {_norm(item) for item in geography.get("countries") or []}
        if geography.get("status") == "listed" and listed:
            status = "pass" if listed & countries else "fail"
            basis = f"Allowed: {', '.join(geography['countries'])} ({geography.get('basis')})"
        else:
            status, basis = "unknown", "Where the work may be done is not stated"
        result.append({"name": "geography", "status": status, "basis": basis})
    required_languages = (conditions.get("language") or {}).get("value") or []
    spoken = {_norm(item) for item in candidate.get("languages") or []}
    if required_languages and spoken:
        missing = [code for code in required_languages if _norm(code) not in spoken]
        result.append(
            {
                "name": "required_languages",
                "status": "unknown" if missing else "pass",
                "basis": f"Not in candidate languages: {', '.join(missing)}"
                if missing
                else "Candidate languages cover the requirement",
            }
        )
    for item in result:
        item["basis_code"] = basis_code(item["basis"])
    return result


def completeness(vacancy: dict, requirements: list, facts: list[dict], track: str) -> dict:
    return {
        "description": vacancy.get("content_scope")
        or ("full" if vacancy.get("text") else "unknown"),
        "requirements": len(requirements),
        "mandatory_requirements": sum(1 for item in requirements if item.get("mandatory")),
        "verified_facts_for_track": sum(
            1
            for fact in facts
            if fact.get("verification") == "verified" and track in fact.get("tracks", TRACKS)
        ),
    }


def outcome(matrix: list[dict], limits: list[dict], data: dict) -> tuple[str, str, dict]:
    """The five-way result, one short reason (the first blocking item) and what it refers to."""
    if not data["requirements"]:
        text = "Requirements are not annotated from a full description"
        return "insufficient_data", text, {"type": "data", "code": basis_code(text)}
    if not data["verified_facts_for_track"]:
        text = "No verified candidate facts for this track"
        return "insufficient_data", text, {"type": "data", "code": basis_code(text)}

    def about_row(row: dict) -> dict:
        return {"type": "requirement", "id": row["requirement_id"], "code": row.get("basis_code")}

    def about_limit(item: dict) -> dict:
        return {"type": "constraint", "name": item["name"], "code": item.get("basis_code")}

    for row in matrix:
        if row["mandatory"] and row["action"]["type"] == "decision_basis":
            return "not_fit_mandatory", f"{row['text']}: {row['basis']}", about_row(row)
    for item in limits:
        if item["status"] == "fail":
            return "not_fit_mandatory", f"{item['name']}: {item['basis']}", about_limit(item)
    for row in matrix:
        if row["mandatory"] and row["status"] != "match":
            return "has_questions", f"{row['text']}: {row['basis']}", about_row(row)
    for item in limits:
        if item["status"] == "unknown":
            return "has_questions", f"{item['name']}: {item['basis']}", about_limit(item)
    mandatory = sum(1 for row in matrix if row["mandatory"])
    return (
        "fits_verified",
        f"All {mandatory} mandatory requirements are backed by reviewed verified facts",
        {"type": "all_mandatory", "count": mandatory},
    )
