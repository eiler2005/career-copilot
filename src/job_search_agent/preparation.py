"""Preparation module: vacancy briefs, track plans for general gaps and a text practice cycle.

Two independent entries, neither requires a finished CV or an interview:

* Mode A — a vacancy brief (`preparation_brief` activity result → `preparation_briefs`):
  company claims marked confirmed / participant report / assumption with dated sources,
  role tasks, interview stages, a coding requirement with basis, questions with provenance
  and what they test, STAR stories tied to verified facts, a time plan, a short brief and
  questions for the employer.
* Mode B — a track plan (`ajh prep plan` → `track_plans`): topics merged from preparation
  gaps across vacancies (a duplicate vacancy never adds weight), or an explicit baseline
  for the direction when no vacancy gaps exist.

Practice is a text cycle: question → answer → follow-up → review → retry
(`practice_sessions`, `practice_attempts`, `practice_review` results). A review quotes
fragments of the answer. Practice progress never creates experience or changes a CV;
confirmed progress still needs an `interview_progress` decision by an independent reviewer.
"""

from __future__ import annotations

import re
import unicodedata
from uuid import uuid4

from .core import TRACKS, Store, digest, now, safe_id

CLAIM_KINDS = frozenset({"confirmed", "participant_report", "assumption"})
QUESTION_TYPES = frozenset(
    {"behavioral", "leadership", "product_case", "system_design", "self_presentation", "coding"}
)
PROVENANCE = frozenset({"published", "generated"})
CODING = frozenset({"required", "not_required", "unknown"})
TOPIC_STATUSES = ("open", "attempted", "reviewed")
# Plans a practice session can belong to: general-gap plans, vacancy learning plans, interview plans.
PLAN_KINDS = frozenset({"track_plans", "learning", "interview_plans", "preparation_overviews"})
BASELINE = {
    "product": [
        (
            "Product sense and discovery",
            "product_case",
            "Frame a problem, segments and success criteria",
        ),
        (
            "Strategy and prioritization",
            "product_case",
            "Choose between alternatives and explain trade-offs",
        ),
        (
            "Metrics and experiments",
            "product_case",
            "Design a testable experiment with a guardrail metric",
        ),
        (
            "Pricing, GTM and unit economics",
            "product_case",
            "Ground a pricing decision in inputs and constraints",
        ),
        (
            "Stakeholder leadership",
            "leadership",
            "Describe influencing without authority with a real story",
        ),
        (
            "Self-presentation",
            "self_presentation",
            "Two-minute story of the career path and motivation",
        ),
    ],
    "technical-leadership": [
        (
            "Architecture and system design",
            "system_design",
            "Design a service with explicit trade-offs",
        ),
        (
            "Distributed systems and trade-offs",
            "system_design",
            "Explain consistency and failure handling",
        ),
        (
            "Reliability and incident analysis",
            "system_design",
            "Analyse an incident and propose SLOs",
        ),
        (
            "Engineering organization and delivery",
            "leadership",
            "Explain how delivery and quality were improved",
        ),
        (
            "Hiring, feedback and team growth",
            "leadership",
            "A real story about developing an engineer",
        ),
        (
            "Self-presentation",
            "self_presentation",
            "Two-minute story of the career path and motivation",
        ),
    ],
}


def _text(value: object, name: str, limit: int = 4000, required: bool = True) -> str | None:
    if value is None and not required:
        return None
    if not isinstance(value, str) or (required and not value.strip()) or len(value) > limit:
        raise ValueError(f"{name} must be text up to {limit} characters")
    return value.strip()


def _sources(value: object, name: str, required: bool) -> list[dict]:
    items = value or []
    if not isinstance(items, list):
        raise ValueError(f"{name}: sources must be a list")  # noqa: TRY004
    result = []
    for item in items:
        if not isinstance(item, dict) or not re.match(r"^https?://", str(item.get("url") or "")):
            raise ValueError(f"{name}: each source needs an http(s) url")
        if not re.match(r"^\d{4}-\d{2}-\d{2}", str(item.get("date") or "")):
            raise ValueError(f"{name}: each source needs the date it was read (YYYY-MM-DD)")
        result.append(
            {"url": item["url"], "date": str(item["date"])[:10], "title": item.get("title")}
        )
    if required and not result:
        raise ValueError(f"{name}: a confirmed or reported claim needs a dated source")
    return result


def _claims(values: object, name: str) -> list[dict]:
    if not isinstance(values, list):
        raise ValueError(f"{name} must be a list")  # noqa: TRY004
    result = []
    for index, claim in enumerate(values):
        if not isinstance(claim, dict) or claim.get("kind") not in CLAIM_KINDS:
            raise ValueError(
                f"{name}[{index}]: kind must be confirmed, participant_report or assumption"
            )
        result.append(
            {
                "text": _text(claim.get("text"), f"{name}[{index}].text", 2000),
                "kind": claim["kind"],
                "sources": _sources(
                    claim.get("sources"), f"{name}[{index}]", claim["kind"] != "assumption"
                ),
            }
        )
    return result


def validate_brief(store: Store, data: dict) -> dict:
    """Validate a `preparation_brief` result; called from activity registration."""
    vacancy = store.get("vacancies", str(data.get("vacancy_id") or ""))
    if not vacancy:
        raise ValueError("preparation_brief requires an existing vacancy_id")
    track = data.get("track")
    if track not in TRACKS:
        raise ValueError("preparation_brief requires a track")
    requirement_ids = {item["id"] for item in vacancy.get("requirements", [])}
    facts = {fact["id"]: fact for fact in store.facts["facts"]}
    company = data.get("company") or {}
    role = data.get("role") or {}
    interview = data.get("interview") or {}
    coding = data.get("coding") or {"status": "unknown"}
    if coding.get("status") not in CODING:
        raise ValueError("coding.status must be required, not_required or unknown")
    if coding["status"] != "unknown":
        _text(coding.get("basis"), "coding.basis", 1000)
        if not coding.get("source"):
            raise ValueError("A coding requirement needs its source")
    unknown = set(role.get("requirement_ids") or []) - requirement_ids
    if unknown:
        raise ValueError(f"role.requirement_ids not in the vacancy: {sorted(unknown)}")
    stages = []
    for index, stage in enumerate(interview.get("stages") or []):
        if not isinstance(stage, dict) or stage.get("kind") not in CLAIM_KINDS:
            raise ValueError(f"interview.stages[{index}] needs name, format and a claim kind")
        stages.append(
            {
                "name": _text(stage.get("name"), f"interview.stages[{index}].name", 200),
                "format": _text(
                    stage.get("format"), f"interview.stages[{index}].format", 500, required=False
                ),
                "kind": stage["kind"],
                "sources": _sources(
                    stage.get("sources"),
                    f"interview.stages[{index}]",
                    stage["kind"] != "assumption",
                ),
            }
        )
    questions = []
    for index, question in enumerate(data.get("questions") or []):
        if not isinstance(question, dict) or question.get("type") not in QUESTION_TYPES:
            raise ValueError(f"questions[{index}].type must be one of {sorted(QUESTION_TYPES)}")
        if question.get("provenance") not in PROVENANCE:
            raise ValueError(f"questions[{index}].provenance must be published or generated")
        if question["type"] == "coding" and coding["status"] != "required":
            raise ValueError("Coding questions are added only when coding is required with a basis")
        source = question.get("source")
        if question["provenance"] == "published" and not (
            isinstance(source, dict) and source.get("url") and source.get("date")
        ):
            raise ValueError(f"questions[{index}]: a published question needs a dated source")
        questions.append(
            {
                "id": safe_id(str(question.get("id") or f"q{index + 1}")),
                "text": _text(question.get("text"), f"questions[{index}].text", 1000),
                "type": question["type"],
                "tests": _text(question.get("tests"), f"questions[{index}].tests", 500),
                "requirement_ids": [
                    item
                    for item in question.get("requirement_ids") or []
                    if item in requirement_ids
                ],
                "provenance": question["provenance"],
                "source": source,
            }
        )
    stories = []
    for index, story in enumerate(data.get("stories") or []):
        fact_ids = story.get("fact_ids") if isinstance(story, dict) else None
        if not fact_ids or any(
            facts.get(item, {}).get("verification") != "verified" for item in fact_ids
        ):
            raise ValueError(
                f"stories[{index}] must be tied to verified facts; record a story gap instead"
            )
        stories.append(
            {
                "title": _text(story.get("title"), f"stories[{index}].title", 200),
                **{
                    part: _text(story.get(part), f"stories[{index}].{part}", 2000)
                    for part in ("situation", "task", "action", "result")
                },
                "fact_ids": fact_ids,
                "tests": story.get("tests"),
            }
        )
    plan = []
    for index, step in enumerate(data.get("plan") or []):
        hours = step.get("hours") if isinstance(step, dict) else None
        if isinstance(hours, bool) or not isinstance(hours, (int, float)) or hours <= 0:
            raise ValueError(f"plan[{index}].hours must be a positive number")
        plan.append(
            {
                "when": _text(step.get("when"), f"plan[{index}].when", 100),
                "hours": hours,
                "focus": _text(step.get("focus"), f"plan[{index}].focus", 500),
            }
        )
    return {
        **data,
        "vacancy_id": vacancy["id"],
        "company_id": vacancy.get("company_id"),
        "track": track,
        "company": {"claims": _claims(company.get("claims") or [], "company.claims")},
        "role": {
            "tasks": [_text(item, "role.tasks", 500) for item in role.get("tasks") or []],
            "requirement_ids": list(role.get("requirement_ids") or []),
        },
        "interview": {"stages": stages},
        "coding": {
            "status": coding["status"],
            "basis": coding.get("basis"),
            "source": coding.get("source"),
            "date": coding.get("date"),
        },
        "questions": questions,
        "stories": stories,
        "story_gaps": [_text(item, "story_gaps", 500) for item in data.get("story_gaps") or []],
        "plan": plan,
        "brief": _text(data.get("brief"), "brief", 6000),
        "employer_questions": [
            _text(item, "employer_questions", 500) for item in data.get("employer_questions") or []
        ],
    }


def after_brief(store: Store, brief: dict) -> None:
    """A researched coding requirement fills the vacancy flag unless the user already set one."""
    vacancy = store.get("vacancies", brief["vacancy_id"])
    current = vacancy.get("coding_requirement") or {}
    if brief["coding"]["status"] != "unknown" and current.get("recorded_by") != "dashboard-request":
        store.patch(
            "vacancies",
            vacancy["id"],
            {
                "coding_requirement": {
                    **brief["coding"],
                    "recorded_at": now(),
                    "recorded_by": f"brief:{brief['id']}",
                }
            },
            None,
            "coding requirement from a preparation brief",
        )


# --------------------------------------------------------------------------- track plans


def _identity(vacancy: dict, companies: dict) -> str:
    company = companies.get(vacancy.get("company_id"), {}).get("name") or vacancy.get("company_id")
    value = unicodedata.normalize("NFKC", f"{vacancy.get('title')}|{company}").casefold()
    return re.sub(r"[^\w|]+", " ", value).strip()


def track_plan(
    store: Store,
    track: str,
    goal: str,
    hours: float,
    experience: str | None = None,
    vacancy_ids: list[str] | None = None,
) -> dict:
    """Merge preparation gaps across vacancies into topics, or state a baseline plan."""
    if track not in TRACKS:
        raise ValueError("Unknown career track")
    goal = _text(goal, "goal", 500)
    if isinstance(hours, bool) or not isinstance(hours, (int, float)) or not 0 < hours <= 80:
        raise ValueError("hours must be between 0 and 80 per week")
    companies = {item["id"]: item for item in store.all("companies")}
    pointers = [item for item in store.all("current_assessments") if item.get("track") == track]
    if vacancy_ids:
        missing = set(vacancy_ids) - {item["id"] for item in store.all("vacancies")}
        if missing:
            raise ValueError(f"Unknown vacancies {sorted(missing)}")
        pointers = [item for item in pointers if item["vacancy_id"] in vacancy_ids]
    topics: dict[str, dict] = {}
    seen_roles: dict[str, set] = {}
    for pointer in pointers:
        assessment = store.get("assessments", pointer["assessment_id"])
        vacancy = store.get("vacancies", pointer["vacancy_id"])
        if not assessment or not vacancy:
            continue
        role = _identity(vacancy, companies)
        for row in assessment.get("requirements", []):
            if row.get("action", {}).get("type") != "preparation":
                continue
            text = re.sub(r"\s+", " ", str(row["text"])).strip()
            key = "topic-" + digest([text.casefold(), row.get("gap_type")])[:12]
            topic = topics.setdefault(
                key,
                {
                    "id": key,
                    "title": text,
                    "type": row.get("gap_type", "knowledge"),
                    "why": "Preparation gap in vacancy requirements",
                    "where_found": [],
                    "weight": 0,
                    "criterion": "A reviewed answer or exercise that meets the requirement without new CV claims",
                    "exercise": f"Explain or solve a realistic case for: {text}",
                    "diagnostic_question": f"How would you demonstrate: {text}?",
                    "materials": [],
                    "status": "open",
                },
            )
            roles = seen_roles.setdefault(key, set())
            if vacancy["id"] not in topic["where_found"]:
                topic["where_found"].append(vacancy["id"])
            if role not in roles:
                # Duplicate postings of the same role and company do not add weight.
                roles.add(role)
                topic["weight"] += 1
    basis = "vacancies" if topics else "baseline"
    if not topics:
        for title, kind, exercise in BASELINE[track]:
            key = "topic-" + digest([track, title])[:12]
            topics[key] = {
                "id": key,
                "title": title,
                "type": kind,
                "why": "Baseline preparation for the direction; not derived from vacancy requirements",
                "where_found": [],
                "weight": 0,
                "criterion": "A reviewed answer that meets the rubric on a retry",
                "exercise": exercise,
                "diagnostic_question": exercise,
                "materials": [],
                "status": "open",
            }
    ordered = sorted(topics.values(), key=lambda item: (-item["weight"], item["title"]))
    plan = {
        "track": track,
        "goal": goal,
        "hours_per_week": hours,
        "experience": _text(experience, "experience", 2000, required=False),
        "basis": {
            "kind": basis,
            "vacancy_ids": sorted({v for t in ordered for v in t["where_found"]}),
        },
        "topics": ordered,
        "cycle": ["diagnostic", "topics", "plan", "materials", "practice", "review", "retry"],
        "note": "Reading materials does not close a gap; only a reviewed attempt changes a topic's status.",
    }
    key = "track-plan-" + digest(plan)[:20]
    existing = store.get("track_plans", key)
    if existing:
        return existing
    value = {"id": key, "created_at": now(), **plan}
    store.put("track_plans", value, immutable=True)
    store.event(
        "track_plan_created",
        [key, *plan["basis"]["vacancy_ids"]],
        {"basis": basis, "topics": len(ordered)},
    )
    return value


# --------------------------------------------------------------------------- practice


def create_session(store: Store, payload: dict) -> dict:
    if payload.get("type") not in QUESTION_TYPES:
        raise ValueError(f"type must be one of {sorted(QUESTION_TYPES)}")
    if payload.get("provenance") not in PROVENANCE:
        raise ValueError("provenance must be published or generated")
    vacancy_id = payload.get("vacancy_id")
    if vacancy_id and not store.get("vacancies", vacancy_id):
        raise ValueError("Vacancy not found")
    plan_id = payload.get("plan_id")
    plan_kind = payload.get("plan_kind") or ("track_plans" if plan_id else None)
    if plan_kind not in (None, *PLAN_KINDS):
        raise ValueError(f"plan_kind must be one of {sorted(PLAN_KINDS)}")
    if plan_id and not store.get(plan_kind, plan_id):
        raise ValueError("Plan not found")
    if payload["type"] == "coding" and vacancy_id:
        coding = (store.get("vacancies", vacancy_id).get("coding_requirement") or {}).get("status")
        if coding != "required":
            raise ValueError("Coding practice for a vacancy needs a recorded coding requirement")
    value = {
        "id": "ps-" + uuid4().hex[:20],
        "track": payload.get("track") if payload.get("track") in TRACKS else None,
        "vacancy_id": vacancy_id,
        "plan_id": plan_id,
        "plan_kind": plan_kind,
        "topic_id": payload.get("topic_id"),
        "question": _text(payload.get("question"), "question", 1000),
        "type": payload["type"],
        "tests": _text(payload.get("tests"), "tests", 500),
        "provenance": payload["provenance"],
        "source": payload.get("source"),
        "created_at": now(),
    }
    store.put("practice_sessions", value, immutable=True)
    store.event(
        "practice_session_created",
        [value["id"]] + ([vacancy_id] if vacancy_id else []),
        {"type": value["type"]},
    )
    return value


def submit_answer(store: Store, payload: dict, request_id: str | None = None) -> dict:
    from . import inbox

    session = store.get("practice_sessions", str(payload.get("session_id") or ""))
    if not session:
        raise ValueError("Practice session not found")
    answer = _text(payload.get("answer"), "answer", 12000)
    previous = payload.get("previous_attempt_id")
    follow_up_to = payload.get("follow_up_to")
    for ref in (previous, follow_up_to):
        attempt = store.get("practice_attempts", ref) if ref else None
        if ref and (not attempt or attempt["session_id"] != session["id"]):
            raise ValueError("Referenced attempt is not part of this session")
    number = 1 + sum(
        1 for item in store.all("practice_attempts") if item["session_id"] == session["id"]
    )
    artifact = store.readable_artifact(
        "evidence/practice", [session["id"], f"attempt-{number}"], answer, ".md"
    )
    value = {
        "id": "pa-" + uuid4().hex[:20],
        "session_id": session["id"],
        "number": number,
        "kind": "follow_up" if follow_up_to else "retry" if previous else "answer",
        "previous_attempt_id": previous,
        "follow_up_to": follow_up_to,
        "answer": {"path": artifact, "sha256": digest(answer.encode())},
        "submitted_at": now(),
        "request_id": request_id,
        "review_id": None,
    }
    task = inbox.create_task(
        store,
        "review_practice",
        {
            k: v
            for k, v in {
                "session_id": session["id"],
                "attempt_id": value["id"],
                "vacancy_id": session.get("vacancy_id"),
                "track": session.get("track"),
            }.items()
            if v
        },
        "Review the answer: quote fragments, criterion, problem, improvement; optional follow-up and retry question.",
        request_id,
    )
    value["task_id"] = task["id"]
    store.put("practice_attempts", value, immutable=True)
    store.event("practice_answer_submitted", [session["id"], value["id"]], {"kind": value["kind"]})
    return value


def validate_review(store: Store, data: dict) -> dict:
    """Validate a `practice_review` result: fragments must quote the answer exactly."""
    attempt = store.get("practice_attempts", str(data.get("attempt_id") or ""))
    if not attempt:
        raise ValueError("practice_review requires an existing attempt_id")
    answer = store.path(attempt["answer"]["path"]).read_text(encoding="utf-8")
    if digest(answer.encode()) != attempt["answer"]["sha256"]:
        raise ValueError("The stored answer changed; the review cannot be registered")
    items = data.get("items")
    if not isinstance(items, list) or not items:
        raise ValueError("practice_review requires review items")
    normalized = []
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise ValueError(f"items[{index}] must be an object")  # noqa: TRY004
        fragment = item.get("fragment")
        if not isinstance(fragment, str) or not fragment.strip() or fragment not in answer:
            raise ValueError(f"items[{index}].fragment must quote the answer exactly")
        normalized.append(
            {
                "fragment": fragment,
                "criterion": _text(item.get("criterion"), f"items[{index}].criterion", 300),
                "problem": _text(item.get("problem"), f"items[{index}].problem", 1000),
                "improvement": _text(item.get("improvement"), f"items[{index}].improvement", 1000),
            }
        )
    retry = data.get("retry") or {}
    return {
        **data,
        "attempt_id": attempt["id"],
        "session_id": attempt["session_id"],
        "items": normalized,
        "follow_up": _text(data.get("follow_up"), "follow_up", 1000, required=False),
        "next_action": _text(data.get("next_action"), "next_action", 500),
        "retry": {"question": _text(retry.get("question"), "retry.question", 1000, required=False)},
        "note": "A practice review is feedback, not demonstrated progress, experience or a CV change.",
    }


def topic_statuses(store: Store, plan: dict) -> dict[str, str]:
    """Derived status per topic: attempts and reviews only; materials never change it."""
    sessions = [
        s
        for s in store.all("practice_sessions")
        if s.get("plan_id") == plan["id"] and (s.get("plan_kind") or "track_plans") == "track_plans"
    ]
    attempts = store.all("practice_attempts")
    reviews = {r["attempt_id"] for r in store.all("practice_reviews")}
    result = {}
    for topic in plan["topics"]:
        own = [s["id"] for s in sessions if s.get("topic_id") == topic["id"]]
        tried = [a for a in attempts if a["session_id"] in own]
        result[topic["id"]] = (
            "reviewed"
            if any(a["id"] in reviews for a in tried)
            else "attempted"
            if tried
            else "open"
        )
    return result


# --------------------------------------------------------------------------- preparation overview

STRENGTHS = frozenset({"verified", "reported", "gap", "unknown"})
OVERVIEW_ACTIONS = frozenset({"verify_evidence", "cv_edit", "preparation", "clarify", "none"})
PLAN_TRACKS = frozenset({*TRACKS, "both"})


def _ids(values: object, known: dict | set, name: str) -> list[str]:
    items = values or []
    if not isinstance(items, list) or any(not isinstance(item, str) for item in items):
        raise ValueError(f"{name} must be a list of IDs")
    unknown = [item for item in items if item not in known]
    if unknown:
        raise ValueError(f"{name}: unknown IDs {unknown[:5]}")
    return list(dict.fromkeys(items))


def validate_overview(store: Store, data: dict) -> dict:
    """Validate a `preparation_overview`: one unified preparation review across both tracks.

    Strength labels are tied to evidence: `verified` needs verified non-target facts,
    `reported` needs existing facts that are neither conflicting nor targets. Coding
    exercises are not accepted here: coding is set per vacancy with a basis.
    """
    facts = {fact["id"]: fact for fact in store.facts["facts"]}
    vacancies = {item["id"] for item in store.all("vacancies")}

    def evidence(item: dict, name: str) -> dict:
        strength = item.get("strength", "unknown")
        if strength not in STRENGTHS:
            raise ValueError(f"{name}.strength must be one of {sorted(STRENGTHS)}")
        fact_ids = _ids(item.get("fact_ids"), facts, f"{name}.fact_ids")
        if strength == "verified" and (
            not fact_ids
            or any(
                facts[key].get("verification") != "verified"
                or facts[key].get("claim_type") == "target"
                for key in fact_ids
            )
        ):
            raise ValueError(f"{name}: 'verified' needs verified facts only")
        if strength == "reported" and (
            not fact_ids
            or any(
                facts[key].get("verification") == "conflicting"
                or facts[key].get("claim_type") == "target"
                for key in fact_ids
            )
        ):
            raise ValueError(f"{name}: 'reported' needs existing non-conflicting, non-target facts")
        action = item.get("action") or {"type": "none"}
        if action.get("type") not in OVERVIEW_ACTIONS:
            raise ValueError(f"{name}.action.type must be one of {sorted(OVERVIEW_ACTIONS)}")
        return {
            "title": _text(item.get("title"), f"{name}.title", 300),
            "why": _text(item.get("why"), f"{name}.why", 1500, required=False),
            "strength": strength,
            "fact_ids": fact_ids,
            "vacancy_ids": _ids(item.get("vacancy_ids"), vacancies, f"{name}.vacancy_ids"),
            "action": {
                "type": action["type"],
                "text": _text(action.get("text"), f"{name}.action.text", 800, required=False),
            },
        }

    tracks = []
    for index, section in enumerate(data.get("tracks") or []):
        if section.get("track") not in TRACKS:
            raise ValueError(f"tracks[{index}].track must be one of {list(TRACKS)}")
        tracks.append(
            {
                "track": section["track"],
                "positioning": _text(
                    section.get("positioning"), f"tracks[{index}].positioning", 1500
                ),
                "target_vacancy_ids": _ids(
                    section.get("target_vacancy_ids"),
                    vacancies,
                    f"tracks[{index}].target_vacancy_ids",
                ),
                "market_notes": [
                    _text(item, f"tracks[{index}].market_notes", 800)
                    for item in section.get("market_notes") or []
                ],
                "themes": [
                    evidence(item, f"tracks[{index}].themes[{n}]")
                    for n, item in enumerate(section.get("themes") or [])
                ],
                "interview_focus": [
                    _text(item, f"tracks[{index}].interview_focus", 500)
                    for item in section.get("interview_focus") or []
                ],
            }
        )
    if {section["track"] for section in tracks} != set(TRACKS):
        raise ValueError("A preparation overview covers both tracks")
    seen: set[str] = set()

    def exercise(item: dict, name: str) -> dict:
        key = safe_id(str(item.get("id") or ""))
        if key in seen:
            raise ValueError(f"{name}: duplicate id {key}")
        seen.add(key)
        if item.get("type") not in QUESTION_TYPES - {"coding"}:
            raise ValueError(f"{name}.type must be a non-coding question type")
        if item.get("track") not in PLAN_TRACKS:
            raise ValueError(f"{name}.track must be product, technical-leadership or both")
        return {
            "id": key,
            "text": _text(item.get("text"), f"{name}.text", 1000),
            "type": item["type"],
            "track": item["track"],
            "tests": _text(item.get("tests"), f"{name}.tests", 500),
            "fact_ids": _ids(item.get("fact_ids"), facts, f"{name}.fact_ids"),
            "vacancy_ids": _ids(item.get("vacancy_ids"), vacancies, f"{name}.vacancy_ids"),
        }

    plan = data.get("plan") or {}
    hours = plan.get("hours_per_week")
    if isinstance(hours, bool) or not isinstance(hours, (int, float)) or not 0 < hours <= 80:
        raise ValueError("plan.hours_per_week must be between 0 and 80")
    weeks = []
    for index, week in enumerate(plan.get("weeks") or []):
        if week.get("track") not in PLAN_TRACKS:
            raise ValueError(
                f"plan.weeks[{index}].track must be product, technical-leadership or both"
            )
        weeks.append(
            {
                "week": index + 1,
                "theme": _text(week.get("theme"), f"plan.weeks[{index}].theme", 300),
                "track": week["track"],
                "goals": [
                    _text(item, f"plan.weeks[{index}].goals", 500)
                    for item in week.get("goals") or []
                ],
                "tasks": [
                    _text(item, f"plan.weeks[{index}].tasks", 500)
                    for item in week.get("tasks") or []
                ],
                "exercises": [
                    exercise(item, f"plan.weeks[{index}].exercises[{n}]")
                    for n, item in enumerate(week.get("exercises") or [])
                ],
                "deliverable": _text(
                    week.get("deliverable"), f"plan.weeks[{index}].deliverable", 500
                ),
            }
        )
    if not weeks:
        raise ValueError("plan.weeks is required")
    stories = []
    for index, story in enumerate(data.get("stories") or []):
        fact_ids = _ids(story.get("fact_ids"), facts, f"stories[{index}].fact_ids")
        if not fact_ids:
            raise ValueError(
                f"stories[{index}] must be tied to facts; list missing stories in story_gaps"
            )
        stories.append(
            {
                "title": _text(story.get("title"), f"stories[{index}].title", 300),
                "fact_ids": fact_ids,
                "tracks": [track for track in story.get("tracks") or [] if track in TRACKS]
                or list(TRACKS),
                "use_for": _text(story.get("use_for"), f"stories[{index}].use_for", 800),
                "caution": _text(
                    story.get("caution"), f"stories[{index}].caution", 800, required=False
                ),
            }
        )
    evidence_to_verify = []
    for index, item in enumerate(data.get("evidence_to_verify") or []):
        [fact_id] = _ids([item.get("fact_id")], facts, f"evidence_to_verify[{index}].fact_id")
        evidence_to_verify.append(
            {
                "fact_id": fact_id,
                "why": _text(item.get("why"), f"evidence_to_verify[{index}].why", 800),
                "how": _text(item.get("how"), f"evidence_to_verify[{index}].how", 800),
            }
        )
    return {
        **data,
        "title": _text(data.get("title"), "title", 300),
        "as_of": _text(data.get("as_of"), "as_of", 20),
        "summary": _text(data.get("summary"), "summary", 4000),
        "basis": {
            "vacancy_ids": _ids(
                (data.get("basis") or {}).get("vacancy_ids"), vacancies, "basis.vacancy_ids"
            ),
            "notes": _text(
                (data.get("basis") or {}).get("notes"), "basis.notes", 2000, required=False
            ),
        },
        "tracks": tracks,
        "common": [
            evidence(item, f"common[{n}]") for n, item in enumerate(data.get("common") or [])
        ],
        "evidence_to_verify": evidence_to_verify,
        "plan": {"hours_per_week": hours, "weeks": weeks},
        "questions": [
            exercise(item, f"questions[{n}]") for n, item in enumerate(data.get("questions") or [])
        ],
        "stories": stories,
        "story_gaps": [_text(item, "story_gaps", 500) for item in data.get("story_gaps") or []],
        "cv_advice": [
            {
                "track": item.get("track") if item.get("track") in PLAN_TRACKS else "both",
                "text": _text(item.get("text"), f"cv_advice[{n}].text", 1000),
                "fact_ids": _ids(item.get("fact_ids"), facts, f"cv_advice[{n}].fact_ids"),
            }
            for n, item in enumerate(data.get("cv_advice") or [])
        ],
        "do_not": [_text(item, "do_not", 500) for item in data.get("do_not") or []],
        "next_actions": [
            _text(item, "next_actions", 500) for item in data.get("next_actions") or []
        ],
        "note": "Agent-authored review from recorded facts and vacancies; strength labels follow fact verification. It changes no facts, CV or assessment.",
    }
