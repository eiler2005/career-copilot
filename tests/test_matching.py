"""Explainable fit on synthetic vacancies: outcomes, routing, staleness and preferences."""

import pytest

from job_search_agent import matching, workflow
from job_search_agent.cli import parser, run, seed_demo
from job_search_agent.core import Store, atomic_write, encode, init_home

VACANCY = "demo-platform-lead"


@pytest.fixture
def store(tmp_path):
    with Store(init_home(tmp_path / "workspace", demo=True)) as value:
        seed_demo(value)
        vacancy = value.get("vacancies", VACANCY)
        value.put(
            "vacancies",
            {**vacancy, "target_track": "product", "level": {"raw": "Lead", "source": "synthetic"}},
        )
        yield value


def set_requirements(store, *requirements):
    vacancy = store.get("vacancies", VACANCY)
    store.put("vacancies", {**vacancy, "requirements": list(requirements)})


def evaluate(store, **kwargs):
    [result] = workflow.evaluate(store, VACANCY, "product", **kwargs)
    return result


def requirement(**updates):
    return {
        "id": "req-platform",
        "text": "Explain platform adoption metrics",
        "mandatory": True,
        **updates,
    }


def pass_gates(store):
    vacancy = store.get("vacancies", VACANCY)
    store.put(
        "vacancies",
        {**vacancy, "language_gate": "pass", "eligibility_gate": "pass", "content_scope": "full"},
    )


def test_reviewed_verified_evidence_fits_and_never_scores(store):
    pass_gates(store)
    set_requirements(store, requirement(evidence_fact_ids=["sample-book"], evidence_reviewed=True))
    result = evaluate(store)
    assert result["outcome"] == "fits_verified"
    assert result["requirements"][0]["status"] == "match"
    assert result["requirements"][0]["evidence"][0]["fact_id"] == "sample-book"
    assert not any("score" in key or "probability" in key for key in result)


@pytest.mark.parametrize("scope", ["excerpt", "card", "salary_index_card", "unknown"])
def test_matching_excerpt_requirements_cannot_claim_complete_fit(store, scope):
    pass_gates(store)
    set_requirements(store, requirement(evidence_fact_ids=["sample-book"], evidence_reviewed=True))
    vacancy = store.get("vacancies", VACANCY)
    store.put("vacancies", {**vacancy, "content_scope": scope, "requirements_complete": True})
    result = evaluate(store)
    assert result["requirements"][0]["status"] == "match"
    assert result["outcome"] == "insufficient_data"


def test_explicit_incomplete_annotation_blocks_fit_but_preserves_decision_gates(store):
    pass_gates(store)
    set_requirements(store, requirement(evidence_fact_ids=["sample-book"], evidence_reviewed=True))
    vacancy = store.get("vacancies", VACANCY)
    vacancy.update(content_scope="full", requirements_complete=False)
    store.put("vacancies", vacancy)
    assert evaluate(store)["outcome"] == "insufficient_data"
    store.put("vacancies", {**vacancy, "eligibility_gate": "fail"})
    assert evaluate(store)["outcome"] == "not_fit_mandatory"
    store.put("vacancies", {**vacancy, "eligibility_gate": "unknown"})
    assert evaluate(store)["outcome"] == "has_questions"


def test_a_missing_cv_word_is_not_a_missing_experience(store):
    pass_gates(store)
    set_requirements(store, requirement(tag="platforms"))
    row = evaluate(store)["requirements"][0]
    assert row["status"] == "unknown" and row["action"]["type"] == "cv_edit"
    assert row["suggested_facts"] == ["sample-book"]
    set_requirements(store, requirement(tag="unrelated-skill"))
    row = evaluate(store)["requirements"][0]
    assert row["status"] == "unknown" and row["action"]["type"] == "clarify"
    set_requirements(store, requirement(tag="unrelated-skill", evidence_checked=True))
    row = evaluate(store)["requirements"][0]
    assert row["status"] == "gap" and row["action"]["type"] == "preparation"
    set_requirements(store, requirement())
    row = evaluate(store)["requirements"][0]
    assert row["status"] == "unknown" and "not linked" in row["basis"]


def test_unknown_mandatory_condition_raises_a_question_not_a_rejection(store):
    pass_gates(store)
    set_requirements(store, requirement(minimum_years=8))
    result = evaluate(store)
    assert result["outcome"] == "has_questions"
    assert result["requirements"][0]["action"]["type"] == "clarify"
    assert result["requirements"][0]["category"] == "constraint"


def test_confirmed_mandatory_mismatch_is_explained(store):
    pass_gates(store)
    settings = store.settings
    settings["candidate"] = {"work_authorization": {"Example Country": "no"}}
    atomic_write(store.home / "settings.json", encode(settings))
    set_requirements(
        store, requirement(authorization="Example Country", text="Right to work in Example Country")
    )
    result = evaluate(store)
    assert result["outcome"] == "not_fit_mandatory"
    assert "Example Country" in result["reason"]
    assert result["requirements"][0]["action"]["type"] == "decision_basis"


def test_missing_requirements_or_facts_are_insufficient_data(store):
    set_requirements(store)
    assert evaluate(store)["outcome"] == "insufficient_data"
    set_requirements(store, requirement())
    facts = store.facts
    for fact in facts["facts"]:
        fact["verification"] = "self_reported"
    atomic_write(store.home / "facts.json", encode(facts))
    result = evaluate(store)
    assert result["outcome"] == "insufficient_data" and "verified" in result["reason"]


def test_preferences_never_change_the_outcome(store):
    pass_gates(store)
    set_requirements(store, requirement(evidence_fact_ids=["sample-book"], evidence_reviewed=True))
    before = evaluate(store)["outcome"]
    settings = store.settings
    settings["campaigns"] = [
        {"id": "ru", "name": "Russia only", "market": "ru", "track": "technical-leadership"}
    ]
    atomic_write(store.home / "settings.json", encode(settings))
    result = evaluate(store)
    assert result["outcome"] == before == "fits_verified"
    assert result["preferences"][0]["status"] == "mismatch"


def test_changed_facts_make_the_assessment_stale_and_refresh_the_pointer(store):
    pass_gates(store)
    set_requirements(store, requirement(evidence_fact_ids=["sample-book"], evidence_reviewed=True))
    evaluate(store)
    pointer = store.get("current_assessments", f"{VACANCY}:product")
    vacancy, company = store.get("vacancies", VACANCY), store.get("companies", "example-systems")
    current = matching.input_hashes(vacancy, company, store.facts, store.settings)
    assert matching.stale_parts(pointer["checked_inputs"], current) == []
    facts = store.facts
    facts["facts"][1]["text"] += " Updated."
    atomic_write(store.home / "facts.json", encode(facts))
    current = matching.input_hashes(vacancy, company, store.facts, store.settings)
    assert matching.stale_parts(pointer["checked_inputs"], current) == ["facts"]
    # Availability checks and personal decisions are not requirement inputs.
    store.put(
        "vacancies",
        {**vacancy, "availability": "closed", "personal_decision": {"status": "interested"}},
    )
    again = matching.input_hashes(
        store.get("vacancies", VACANCY), company, store.facts, store.settings
    )
    assert again["vacancy"] == current["vacancy"]
    assert workflow.evaluate(store, VACANCY, "product", stale_only=True)
    assert workflow.evaluate(store, VACANCY, "product", stale_only=True) == []
    refreshed = store.get("current_assessments", f"{VACANCY}:product")
    assert (
        matching.stale_parts(
            refreshed["checked_inputs"],
            matching.input_hashes(
                store.get("vacancies", VACANCY), company, store.facts, store.settings
            ),
        )
        == []
    )


def test_requirement_annotations_are_validated(store, tmp_path):
    for bad in (
        [{"id": "a", "text": ""}],
        [{"id": "a", "text": "x"}, {"id": "a", "text": "y"}],
        [{"id": "a", "text": "x", "gap_type": "vibes"}],
        [{"id": "a", "text": "x", "evidence_fact_ids": ["missing-fact"]}],
        [{"id": "a", "text": "x", "mandatory": "yes"}],
    ):
        with pytest.raises(ValueError):
            matching.validate_requirements(bad, {fact["id"] for fact in store.facts["facts"]})
    path = tmp_path / "requirements.json"
    atomic_write(path, encode([requirement(evidence_fact_ids=["sample-job"])]))
    args = parser().parse_args(
        ["--home", str(store.home), "vacancy", "requirements", VACANCY, str(path)]
    )
    assert run(args) == {"vacancy_id": VACANCY, "requirements": 1}
    assert any(e["type"] == "record_updated" for e in store.all("events"))


def test_dashboard_marks_assessments_stale_with_the_changed_part(store):
    from job_search_agent.dashboard import Journal

    pass_gates(store)
    set_requirements(store, requirement(evidence_fact_ids=["sample-book"], evidence_reviewed=True))
    evaluate(store)

    def current_assessment():
        data = Journal.open(store.home).workspace()
        return next(
            item
            for item in data["vacancies"]
            if item["kind"] == "assessments" and item["display"].get("current")
        )

    assert current_assessment()["display"]["stale"] == []
    vacancy = store.get("vacancies", VACANCY)
    store.put("vacancies", {**vacancy, "requirements": [requirement(text="Changed requirement")]})
    assert current_assessment()["display"]["stale"] == ["vacancy"]
