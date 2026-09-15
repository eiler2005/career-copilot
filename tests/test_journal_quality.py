"""Duplicate-free results, readable artifact names and stored translations."""

import json
import re

import pytest

from job_search_agent import maintenance, translations, workflow
from job_search_agent.cli import seed_demo, verify
from job_search_agent.core import Store, atomic_write, digest, encode, init_home, now
from job_search_agent.naming import MAX_COMPONENT_BYTES, readable_name, shorten_component, slug


@pytest.fixture
def store(tmp_path):
    home = init_home(tmp_path / "private", demo=True)
    with Store(home) as db:
        seed_demo(db)
        yield db


def test_readable_names_are_dated_contextual_bounded_and_hash_suffixed():
    sha = "ab" * 32
    assert readable_name(["Product", "demo-platform-lead"], sha, ".json", "2026-09-14") == (
        "2026-09-14-product-demo-platform-lead-abababab.json"
    )
    assert readable_name(["2026-09-14 shared learning plan"], sha, ".md", "2026-09-14") == (
        "2026-09-14-shared-learning-plan-abababab.md"
    )
    assert slug("Руководитель продукта / CPO") == "руководитель-продукта-cpo"
    long = "Министерство цифрового развития " * 12 + ".txt"
    short = shorten_component(long, sha)
    assert len(short.encode()) <= MAX_COMPONENT_BYTES
    assert short.startswith("Министерство цифрового развития") and short.endswith("-abababab.txt")
    assert shorten_component("short name.txt", sha) == "short name.txt"
    assert len(readable_name(["x" * 400], sha, ".md").encode()) <= MAX_COMPONENT_BYTES


def test_readable_artifact_reuses_identical_content_in_the_same_directory(store):
    first = store.readable_artifact("evidence", ["Career notes"], "same body", ".md")
    second = store.readable_artifact("evidence", ["Other name"], "same body", ".md")
    assert first == second
    assert re.fullmatch(r"evidence/\d{4}-\d{2}-\d{2}-career-notes-[0-9a-f]{8}\.md", first)
    other = store.readable_artifact("reviews", ["Career notes"], "same body", ".md")
    assert other.startswith("reviews/")


def test_re_evaluation_supersedes_instead_of_duplicating(store):
    first = workflow.evaluate(store, "demo-platform-lead", "product")[0]
    # Same conclusion from changed inputs keeps a single record.
    facts = store.facts
    facts["facts"][0]["text"] += " Updated wording."
    atomic_write(store.home / "facts.json", encode(facts))
    again = workflow.evaluate(store, "demo-platform-lead", "product")[0]
    assert again["id"] == first["id"]
    assert [a["id"] for a in store.all("assessments")] == [first["id"]]
    # A different conclusion replaces the current one and archives the previous result.
    vacancy = store.get("vacancies", "demo-platform-lead")
    vacancy["requirements"].append(
        {"id": "req-2", "text": "Lead platform pricing", "mandatory": False}
    )
    store.put("vacancies", vacancy)
    changed = workflow.evaluate(store, "demo-platform-lead", "product")[0]
    assert changed["id"] != first["id"]
    assert [a["id"] for a in store.all("assessments")] == [changed["id"]]
    archived = store.get("superseded_records", f"assessments--{first['id']}")
    assert archived["superseded_by"] == changed["id"] and archived["payload"]["id"] == first["id"]
    assert (
        store.get("current_assessments", "demo-platform-lead:product")["assessment_id"]
        == changed["id"]
    )


def test_learning_plans_keep_one_current_version(store):
    first = workflow.learning_plan(store, "demo-platform-lead", "product")
    assert workflow.learning_plan(store, "demo-platform-lead", "product")["id"] == first["id"]
    vacancy = store.get("vacancies", "demo-platform-lead")
    vacancy["requirements"].append(
        {"id": "req-2", "text": "Lead platform pricing", "mandatory": True}
    )
    store.put("vacancies", vacancy)
    second = workflow.learning_plan(store, "demo-platform-lead", "product")
    assert [plan["id"] for plan in store.all("learning")] == [second["id"]]
    assert (
        store.get("superseded_records", f"learning--{first['id']}")["superseded_by"] == second["id"]
    )
    pointer = store.get("current_learning", "demo-platform-lead:product")
    assert pointer["learning_id"] == second["id"]
    files = [
        row[0]
        for row in store.db.execute("SELECT path FROM artifacts WHERE path LIKE 'learning/%'")
    ]
    assert all(
        re.search(r"learning/\d{4}-\d{2}-\d{2}-product-demo-platform-lead-[0-9a-f]{8}\.json$", f)
        for f in files
    )


def test_maintenance_dedupe_archives_existing_duplicates_idempotently(store):
    base = {"vacancy_id": "demo-platform-lead", "track": "product", "decision": "watch"}
    store.put("assessments", {"id": "assessment-old", "at": "2026-01-01T10:03:00+00:00", **base})
    store.put("assessments", {"id": "assessment-new", "at": "2026-01-01T10:19:00+00:00", **base})
    plan = maintenance.dedupe(store)
    assert plan["applied"] is False and plan["superseded"] == 1
    assert store.get("assessments", "assessment-old")
    result = maintenance.dedupe(store, apply=True)
    assert result["applied"] is True and result["superseded"] == 1
    assert store.get("assessments", "assessment-old") is None
    assert (
        store.get("superseded_records", "assessments--assessment-old")["superseded_by"]
        == "assessment-new"
    )
    assert (
        store.get("current_assessments", "demo-platform-lead:product")["assessment_id"]
        == "assessment-new"
    )
    assert maintenance.dedupe(store, apply=True)["superseded"] == 0
    assert any(event["type"] == "records_deduplicated" for event in store.all("events"))


def test_rename_artifacts_updates_files_references_and_facts(store):
    body = b"# Evidence\n"
    sha = digest(body)
    evidence = f"evidence/{sha}.md"
    store.artifact(evidence, body)
    plan_body = b"plan"
    plan_path = f"activity-artifacts/{digest(plan_body)}.md"
    store.artifact(plan_path, plan_body)
    long_name = "legacy/postings/" + "Очень длинное название вакансии " * 4 + ".txt"
    store.artifact(long_name, b"posting")
    store.put(
        "interview_plans",
        {
            "id": "plan-1",
            "created_at": "2026-09-14T10:00:00+00:00",
            "plan": {"path": plan_path, "original_path": "/srv/plans/2026-09-14-shared-plan.md"},
        },
    )
    store.put("legacy_files", {"id": long_name.removeprefix("legacy/"), "path": long_name})
    facts = store.facts
    facts["facts"][0]["sources"] = [evidence]
    facts["facts"][0]["original_sources"] = ["../cv/verified distinctions.md"]
    atomic_write(store.home / "facts.json", encode(facts))
    store.event("facts_imported", [], {"sha256": "x", "fact_count": 2, "at": now()})

    dry = maintenance.rename_artifacts(store)
    assert dry["applied"] is False and dry["renamed"] == 3
    assert store.path(evidence).exists()
    result = maintenance.rename_artifacts(store, apply=True)
    mapping = result["mapping"]
    assert re.fullmatch(
        r"evidence/\d{4}-\d{2}-\d{2}-verified-distinctions-[0-9a-f]{8}\.md", mapping[evidence]
    )
    assert (
        mapping[plan_path]
        == f"activity-artifacts/2026-09-14-shared-plan-{digest(plan_body)[:8]}.md"
    )
    assert len(mapping[long_name].rsplit("/", 1)[1].encode()) <= MAX_COMPONENT_BYTES
    for old, new in mapping.items():
        assert not store.path(old).exists() and store.artifact_intact(new)
    assert store.get("interview_plans", "plan-1")["plan"]["path"] == mapping[plan_path]
    assert (
        store.get("legacy_files", long_name.removeprefix("legacy/"))["path"] == mapping[long_name]
    )
    assert store.facts["facts"][0]["sources"] == [mapping[evidence]]
    assert (store.home / result["manifest"]).is_file()
    assert verify(store)["passed"] is True
    assert maintenance.rename_artifacts(store, apply=True)["renamed"] == 0


def test_translations_round_trip_without_rewriting_originals(store):
    workflow.learning_plan(store, "demo-platform-lead", "product")
    exported = translations.export(store)
    item = next(entry for entry in exported["items"] if entry["text"] == "Company brief")
    assert item["source_lang"] == "en" and item["translations"] == {"en": "Company brief", "ru": ""}
    item["translations"]["ru"] = "Справка о компании"
    with pytest.raises(ValueError):
        translations.import_translations(store, exported)  # translator identity is mandatory
    exported["actor"] = {"environment": "claude", "model": "claude-opus-5", "session": "test"}
    assert translations.import_translations(store, exported)["imported"] == 1
    stored = store.get("text_translations", translations.text_id("Company brief"))
    assert stored["translations"] == {"en": "Company brief", "ru": "Справка о компании"}
    assert stored["translator"]["model"] == "claude-opus-5"
    assert "Company brief" in json.dumps(store.all("learning"))
    assert not any(
        entry["text"] == "Company brief" for entry in translations.export(store)["items"]
    )
    tampered = {**exported, "items": [{**item, "text": "Company brief!"}]}
    with pytest.raises(ValueError):
        translations.import_translations(store, tampered)
    assert translations.language("Российская компания") == "ru"
