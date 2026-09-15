"""Preparation module on synthetic data: briefs, track plans and the text practice cycle."""

import pytest

from job_search_agent import activity, inbox, preparation, workflow
from job_search_agent.cli import seed_demo
from job_search_agent.core import Store, atomic_write, digest, encode, init_home

VACANCY = "demo-platform-lead"
SOURCE = {"url": "https://example.invalid/careers/process", "date": "2026-09-01"}


@pytest.fixture
def store(tmp_path):
    with Store(init_home(tmp_path / "workspace", demo=True)) as value:
        seed_demo(value)
        yield value


def json_file(tmp_path, name, value):
    path = tmp_path / name
    atomic_write(path, encode(value))
    return path


def run_activity(store, tmp_path, skill, record):
    started = activity.start(
        store,
        json_file(
            tmp_path,
            "request.json",
            {
                "schema_version": 1,
                "skill": skill,
                "operation": "Synthetic preparation work",
                "actor": {
                    "environment": "claude",
                    "model": "claude-opus-5",
                    "session": "synthetic",
                },
                "expected_result": {"types": [record["type"]]},
            },
        ),
    )
    return activity.finish(
        store,
        started["id"],
        json_file(
            tmp_path,
            "result.json",
            {
                "schema_version": 1,
                "status": "completed",
                "next_action": "Practice",
                "records": [record],
            },
        ),
    )


def brief(**updates):
    return {
        "type": "preparation_brief",
        "data": {
            "vacancy_id": VACANCY,
            "track": "product",
            "company": {
                "claims": [
                    {
                        "text": "Builds fictional platforms",
                        "kind": "confirmed",
                        "sources": [SOURCE],
                    },
                    {"text": "Teams are probably small", "kind": "assumption"},
                ]
            },
            "role": {"tasks": ["Own platform adoption"], "requirement_ids": ["req-platform"]},
            "interview": {
                "stages": [
                    {
                        "name": "Case interview",
                        "format": "60 minutes",
                        "kind": "participant_report",
                        "sources": [SOURCE],
                    }
                ]
            },
            "coding": {
                "status": "not_required",
                "basis": "Process page lists no coding stage",
                "source": SOURCE["url"],
                "date": "2026-09-01",
            },
            "questions": [
                {
                    "text": "How would you grow adoption?",
                    "type": "product_case",
                    "tests": "Metrics and prioritisation",
                    "provenance": "generated",
                },
                {
                    "text": "Tell us about a platform launch",
                    "type": "behavioral",
                    "tests": "Ownership",
                    "provenance": "published",
                    "source": SOURCE,
                },
            ],
            "stories": [
                {
                    "title": "Platform team",
                    "situation": "s",
                    "task": "t",
                    "action": "a",
                    "result": "r",
                    "fact_ids": ["sample-job"],
                }
            ],
            "story_gaps": ["No example of a failed launch yet"],
            "plan": [{"when": "Day 1", "hours": 2, "focus": "Company and role"}],
            "brief": "Synthetic brief.",
            "employer_questions": ["How is platform adoption measured?"],
            **updates,
        },
    }


def test_brief_marks_provenance_and_refuses_unsupported_claims(store, tmp_path):
    bad_cases = [
        ({"company": {"claims": [{"text": "x", "kind": "confirmed"}]}}, "dated source"),
        (
            {
                "questions": [
                    {
                        "text": "Reverse a list",
                        "type": "coding",
                        "tests": "Algorithms",
                        "provenance": "generated",
                    }
                ]
            },
            "Coding questions",
        ),
        (
            {
                "stories": [
                    {
                        "title": "x",
                        "situation": "s",
                        "task": "t",
                        "action": "a",
                        "result": "r",
                        "fact_ids": [],
                    }
                ]
            },
            "verified facts",
        ),
        (
            {
                "questions": [
                    {"text": "q", "type": "behavioral", "tests": "t", "provenance": "published"}
                ]
            },
            "dated source",
        ),
        ({"coding": {"status": "required"}}, "coding.basis"),
    ]
    for updates, message in bad_cases:
        record = brief()
        record["data"].update(updates)
        with pytest.raises(ValueError, match=message):
            run_activity(store, tmp_path, "career-interview-prep", record)
    run_activity(store, tmp_path, "career-interview-prep", brief())
    [stored] = store.all("preparation_briefs")
    assert stored["company"]["claims"][1]["kind"] == "assumption"
    coding = store.get("vacancies", VACANCY)["coding_requirement"]
    assert coding["status"] == "not_required" and coding["recorded_by"].startswith("brief:")


def test_user_coding_flag_is_not_overwritten_by_a_brief(store, tmp_path):
    store.patch(
        "vacancies",
        VACANCY,
        {
            "coding_requirement": {
                "status": "required",
                "basis": "Recruiter said so",
                "recorded_by": "dashboard-request",
            }
        },
        None,
        "test",
    )
    run_activity(store, tmp_path, "career-interview-prep", brief())
    assert store.get("vacancies", VACANCY)["coding_requirement"]["status"] == "required"


def test_track_plan_is_baseline_without_vacancy_gaps(store):
    plan = preparation.track_plan(store, "product", "Senior product role", 6)
    assert plan["basis"]["kind"] == "baseline" and plan["basis"]["vacancy_ids"] == []
    assert all("Baseline" in topic["why"] for topic in plan["topics"])
    assert preparation.track_plan(store, "product", "Senior product role", 6)["id"] == plan["id"]
    with pytest.raises(ValueError):
        preparation.track_plan(store, "product", "", 6)


def test_duplicate_vacancies_do_not_add_weight_to_a_merged_gap(store):
    vacancy = store.get("vacancies", VACANCY)
    gap = {
        "id": "req-metrics",
        "text": "Design pricing experiments",
        "mandatory": True,
        "evidence_checked": True,
    }
    store.put("vacancies", {**vacancy, "target_track": "product", "requirements": [gap]})
    store.put(
        "vacancies",
        {
            **vacancy,
            "id": "demo-copy",
            "urls": ["https://example.invalid/copy"],
            "target_track": "product",
            "requirements": [gap],
        },
    )
    store.put(
        "vacancies",
        {
            **vacancy,
            "id": "demo-other",
            "title": "Growth Lead",
            "urls": ["https://example.invalid/other"],
            "target_track": "product",
            "requirements": [gap],
        },
    )
    for key in (VACANCY, "demo-copy", "demo-other"):
        workflow.evaluate(store, key, "product")
    plan = preparation.track_plan(store, "product", "Platform roles", 5)
    [topic] = [item for item in plan["topics"] if item["title"] == "Design pricing experiments"]
    assert plan["basis"]["kind"] == "vacancies"
    assert sorted(topic["where_found"]) == ["demo-copy", "demo-other", VACANCY]
    assert topic["weight"] == 2
    learning = workflow.learning_plan(store, None, "product")
    assert all(len(g["vacancy_ids"]) == len(set(g["vacancy_ids"])) for g in learning["gaps"])


def test_text_practice_cycle_reviews_quoted_fragments_and_changes_no_facts(store, tmp_path):
    facts_before = digest(store.facts)
    plan = preparation.track_plan(store, "product", "Senior product role", 6)
    topic = plan["topics"][0]
    state = tmp_path / "state"
    inbox.write_request(
        state,
        {
            "type": "prep_create",
            "payload": {
                "track": "product",
                "plan_id": plan["id"],
                "topic_id": topic["id"],
                "question": topic["diagnostic_question"],
                "type": topic["type"],
                "tests": topic["criterion"],
                "provenance": "generated",
            },
        },
    )
    inbox.import_requests(store, state / inbox.REQUEST_DIR)
    inbox.apply_requests(store)
    [session] = store.all("practice_sessions")
    answer = "I would start with segments. Then I would pick one metric and run an experiment."
    inbox.write_request(
        state,
        {"type": "practice_answer", "payload": {"session_id": session["id"], "answer": answer}},
    )
    inbox.import_requests(store, state / inbox.REQUEST_DIR)
    [applied] = [item for item in inbox.apply_requests(store)["requests"]]
    assert applied["status"] == "queued_for_agent"
    [attempt] = store.all("practice_attempts")
    assert store.get("tasks", attempt["task_id"])["type"] == "review_practice"
    assert preparation.topic_statuses(store, plan)[topic["id"]] == "attempted"
    review = {
        "type": "practice_review",
        "data": {
            "attempt_id": attempt["id"],
            "items": [
                {
                    "fragment": "pick one metric",
                    "criterion": "Metric choice",
                    "problem": "No guardrail metric",
                    "improvement": "Name a guardrail",
                }
            ],
            "follow_up": "Which guardrail would you use?",
            "next_action": "Retry with a guardrail",
            "retry": {"question": "Redo the case with a guardrail metric"},
        },
    }
    bad = {
        **review,
        "data": {
            **review["data"],
            "items": [{**review["data"]["items"][0], "fragment": "not in the answer"}],
        },
    }
    with pytest.raises(ValueError, match="quote"):
        run_activity(store, tmp_path, "career-interview-prep", bad)
    run_activity(store, tmp_path, "career-interview-prep", review)
    assert preparation.topic_statuses(store, plan)[topic["id"]] == "reviewed"
    retry = preparation.submit_answer(
        store,
        {
            "session_id": session["id"],
            "answer": answer + " Guardrail: churn.",
            "previous_attempt_id": attempt["id"],
        },
    )
    follow = preparation.submit_answer(
        store, {"session_id": session["id"], "answer": "Churn rate.", "follow_up_to": attempt["id"]}
    )
    assert (retry["kind"], retry["number"], follow["kind"]) == ("retry", 2, "follow_up")
    assert digest(store.facts) == facts_before
    assert not store.all("interview_progress")
    with pytest.raises(ValueError, match="coding"):
        preparation.create_session(
            store,
            {
                "vacancy_id": VACANCY,
                "question": "q",
                "type": "coding",
                "tests": "t",
                "provenance": "generated",
            },
        )


def test_practice_can_follow_a_vacancy_learning_plan_week_or_gap(store):
    from job_search_agent.dashboard import Journal

    vacancy = store.get("vacancies", VACANCY)
    gap = {
        "id": "req-x",
        "text": "Design pricing experiments",
        "mandatory": True,
        "evidence_checked": True,
    }
    store.put("vacancies", {**vacancy, "target_track": "product", "requirements": [gap]})
    plan = workflow.learning_plan(store, VACANCY, "product")
    with pytest.raises(ValueError, match="plan_kind"):
        preparation.create_session(
            store,
            {
                "plan_id": plan["id"],
                "plan_kind": "unknown",
                "question": "q",
                "type": "product_case",
                "tests": "t",
                "provenance": "generated",
            },
        )
    with pytest.raises(ValueError, match="Plan not found"):
        preparation.create_session(
            store,
            {
                "plan_id": "missing",
                "plan_kind": "learning",
                "question": "q",
                "type": "product_case",
                "tests": "t",
                "provenance": "generated",
            },
        )
    session = preparation.create_session(
        store,
        {
            "track": "product",
            "vacancy_id": VACANCY,
            "plan_id": plan["id"],
            "plan_kind": "learning",
            "topic_id": "week-1",
            "question": "Frame a problem",
            "type": "product_case",
            "tests": "Discovery",
            "provenance": "generated",
        },
    )
    preparation.submit_answer(
        store, {"session_id": session["id"], "answer": "Segments first, then success criteria."}
    )
    data = Journal.open(store.home).workspace()
    record = next(
        item
        for item in data["preparations"]
        if item["kind"] == "learning" and item["id"] == plan["id"]
    )
    assert record["display"]["topic_status"]["week-1"] == "attempted"
    assert record["display"]["topic_status"]["week-2"] == "open"
    assert all(
        status == "open"
        for key, status in record["display"]["topic_status"].items()
        if key != "week-1"
    )


def overview(**updates):
    exercise = {
        "id": "w1-pitch",
        "text": "Two-minute pitch",
        "type": "self_presentation",
        "track": "both",
        "tests": "Positioning",
    }
    track = {
        "positioning": "Synthetic positioning",
        "target_vacancy_ids": [VACANCY],
        "themes": [
            {
                "title": "Platforms",
                "strength": "verified",
                "fact_ids": ["sample-book"],
                "action": {"type": "preparation", "text": "Case"},
            }
        ],
    }
    return {
        "type": "preparation_overview",
        "data": {
            "title": "Synthetic overview",
            "as_of": "2026-09-15",
            "summary": "Synthetic summary.",
            "basis": {"vacancy_ids": [VACANCY]},
            "tracks": [{**track, "track": "product"}, {**track, "track": "technical-leadership"}],
            "common": [
                {"title": "Evidence", "strength": "unknown", "action": {"type": "verify_evidence"}}
            ],
            "evidence_to_verify": [{"fact_id": "sample-job", "why": "Title", "how": "Letter"}],
            "plan": {
                "hours_per_week": 6,
                "weeks": [
                    {
                        "theme": "Positioning",
                        "track": "both",
                        "exercises": [exercise],
                        "deliverable": "Pitch",
                    }
                ],
            },
            "questions": [
                {
                    "id": "q-platform",
                    "text": "Grow adoption",
                    "type": "product_case",
                    "track": "product",
                    "tests": "Metrics",
                }
            ],
            "stories": [{"title": "Team", "fact_ids": ["sample-job"], "use_for": "Leadership"}],
            **updates,
        },
    }


def test_overview_ties_strength_to_evidence_and_links_practice(store, tmp_path):
    from job_search_agent.dashboard import Journal

    facts = store.facts
    facts["facts"].append(
        {**facts["facts"][1], "id": "reported-only", "verification": "self_reported"}
    )
    atomic_write(store.home / "facts.json", encode(facts))
    base = overview()["data"]
    bad = [
        ({"tracks": base["tracks"][:1]}, "both tracks"),
        (
            {
                "tracks": [
                    {
                        **base["tracks"][0],
                        "themes": [
                            {"title": "x", "strength": "verified", "fact_ids": ["reported-only"]}
                        ],
                    },
                    base["tracks"][1],
                ]
            },
            "verified facts only",
        ),
        (
            {
                "questions": [
                    {
                        "id": "q",
                        "text": "Reverse a list",
                        "type": "coding",
                        "track": "technical-leadership",
                        "tests": "t",
                    }
                ]
            },
            "non-coding",
        ),
        ({"stories": [{"title": "x", "fact_ids": [], "use_for": "y"}]}, "tied to facts"),
        ({"basis": {"vacancy_ids": ["missing"]}}, "unknown IDs"),
    ]
    for updates, message in bad:
        with pytest.raises(ValueError, match=message):
            run_activity(store, tmp_path, "career-interview-prep", overview(**updates))
    run_activity(store, tmp_path, "career-interview-prep", overview())
    [record] = store.all("preparation_overviews")
    assert record["plan"]["weeks"][0]["week"] == 1
    session = preparation.create_session(
        store,
        {
            "track": "product",
            "plan_id": record["id"],
            "plan_kind": "preparation_overviews",
            "topic_id": "w1-pitch",
            "question": "Two-minute pitch",
            "type": "self_presentation",
            "tests": "Positioning",
            "provenance": "generated",
        },
    )
    preparation.submit_answer(store, {"session_id": session["id"], "answer": "My pitch."})
    data = Journal.open(store.home).workspace()
    shown = next(item for item in data["preparations"] if item["kind"] == "preparation_overviews")
    assert shown["display"]["topic_status"] == {"w1-pitch": "attempted", "q-platform": "open"}


def test_practice_requests_accept_only_known_plan_kinds(tmp_path):
    base = {
        "question": "q",
        "type": "product_case",
        "tests": "t",
        "provenance": "generated",
        "plan_id": "plan-1",
    }
    for kind in ("track_plans", "learning", "interview_plans", "preparation_overviews"):
        request = inbox.write_request(
            tmp_path / "state", {"type": "prep_create", "payload": {**base, "plan_kind": kind}}
        )
        assert request["payload"]["plan_kind"] == kind
    with pytest.raises(ValueError):
        inbox.write_request(
            tmp_path / "state",
            {"type": "prep_create", "payload": {**base, "plan_kind": "vacancies"}},
        )
