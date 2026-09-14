"""Synthetic host-runtime contracts, immutable handoffs and truthful statistics."""

import pytest

from job_search_agent import activity, report, stats, workflow
from job_search_agent.cli import parser, run, seed_demo, verify
from job_search_agent.core import Store, atomic_write, digest, encode, init_home, read_json


@pytest.fixture
def store(tmp_path):
    with Store(init_home(tmp_path / "workspace", demo=True)) as value:
        seed_demo(value)
        yield value


def json_file(tmp_path, name, value):
    path = tmp_path / name
    atomic_write(path, encode(value))
    return path


def request(tmp_path, **updates):
    return json_file(
        tmp_path,
        "request.json",
        {
            "schema_version": 1,
            "skill": "career-copilot",
            "operation": "synthetic action",
            "expected_result": {"types": []},
            **updates,
        },
    )


def result(tmp_path, **updates):
    return json_file(
        tmp_path,
        "result.json",
        {
            "schema_version": 1,
            "status": "completed",
            "next_action": "Inspect next task",
            **updates,
        },
    )


def file_ref(tmp_path, name="evidence", body="Synthetic evidence"):
    path = tmp_path / (name + ".md")
    atomic_write(path, body)
    return {"name": name, "path": str(path), "sha256": digest(path.read_bytes())}


def test_distinct_starts_resume_and_idempotent_finish(store, tmp_path):
    first = activity.start(store, request(tmp_path))
    second = activity.start(store, request(tmp_path))
    assert first["id"] != second["id"]
    with Store(store.home) as reopened:
        assert activity.show(reopened, first["id"])["resumable"]
        activity.bind(reopened, first["id"])
        reopened.event("continued", [], {"synthetic": True})
    completed = activity.finish(store, first["id"], result(tmp_path))
    assert completed == activity.finish(store, first["id"], result(tmp_path))
    assert any(e["type"] == "continued" for e in completed["events"])
    with pytest.raises(ValueError, match="Conflicting"):
        activity.finish(store, first["id"], result(tmp_path, next_action="Different"))
    assert len(store.all("activities")) == 2


def test_link_events_does_not_rewrite_legacy_id_or_timestamp(store, tmp_path):
    event_id = store.event("existing_action", [], {"same": True})
    old = store.get("events", event_id)
    for _ in range(2):
        started = activity.start(store, request(tmp_path))
        activity.bind(store, started["id"])
        assert store.event("existing_action", [], {"same": True}) == event_id
    assert store.get("events", event_id) == old
    assert len([r for r in store.all("activity_events") if r["event_id"] == event_id]) == 2


def test_stale_inputs_fail_completed_but_can_record_blocker(store, tmp_path):
    ref = file_ref(tmp_path)
    started = activity.start(store, request(tmp_path, inputs=[ref]))
    atomic_write(tmp_path / "evidence.md", "Changed")
    assert not activity.show(store, started["id"])["resumable"]
    with pytest.raises(ValueError, match="inputs changed"):
        activity.finish(store, started["id"], result(tmp_path))
    assert (
        activity.finish(store, started["id"], result(tmp_path, status="blocked"))["status"]
        == "blocked"
    )
    with pytest.raises(ValueError, match="stale"):
        activity.start(store, request(tmp_path, inputs=[ref]))


def test_missing_model_is_blocked_never_relabelled(store, tmp_path):
    started = activity.start(store, request(tmp_path, required_model="gpt-6-astra"))
    assert started["status"] == "blocked" and started["actor"]["model"] is None
    with pytest.raises(ValueError):
        activity.finish(store, started["id"], result(tmp_path))
    finished = activity.finish(store, started["id"], result(tmp_path, status="blocked"))
    assert finished["actor"]["model"] is None
    child = activity.start(store, request(tmp_path, parent_activity_id=started["id"]))
    assert child["parent_activity_id"] == started["id"]


def test_typed_dossier_revision_and_atomic_invalid_registration(store, tmp_path):
    started = activity.start(
        store,
        request(
            tmp_path,
            expected_result={"types": ["company_dossier", "text_revision"]},
            actor={"model": "gpt-6-astra", "session": "synthetic-editor"},
        ),
    )
    artifacts = [
        file_ref(tmp_path, "before"),
        file_ref(tmp_path, "after", "Revised fictional text"),
    ]
    records = [
        {
            "type": "company_dossier",
            "data": {
                "id": "dossier",
                "company_id": "example-systems",
                "dossier_artifact": "after",
                "profile": {"research_note": "Synthetic"},
            },
        },
        {
            "type": "text_revision",
            "data": {
                "id": "revision",
                "before_artifact": "before",
                "after_artifact": "after",
                "change_notes": ["Simplified words"],
            },
        },
    ]
    old = store.get("companies", "example-systems")
    activity.finish(store, started["id"], result(tmp_path, artifacts=artifacts, records=records))
    company = store.get("companies", "example-systems")
    assert all(company[key] == value for key, value in old.items())
    assert company["dossier_refs"] == ["dossier"]
    assert store.get("text_revisions", "revision")["before"]["sha256"] == artifacts[0]["sha256"]
    other = activity.start(store, request(tmp_path))
    records[0]["data"]["id"] = "not-committed"
    records[1]["data"]["after_artifact"] = "missing"
    with pytest.raises(ValueError):
        activity.finish(store, other["id"], result(tmp_path, artifacts=artifacts, records=records))
    assert store.get("company_dossiers", "not-committed") is None


def test_interview_progress_needs_artifact_and_review(store, tmp_path):
    started = activity.start(store, request(tmp_path))
    artifact = file_ref(tmp_path)
    records = [
        {
            "type": "interview_plan",
            "data": {
                "id": "plan",
                "track": "product",
                "objectives": ["Explain metrics"],
                "plan_artifact": "evidence",
            },
        },
        {
            "type": "interview_practice",
            "data": {
                "id": "practice",
                "plan_id": "plan",
                "exercise": "Metrics answer",
                "evidence_artifact": "evidence",
            },
        },
        {
            "type": "interview_feedback",
            "data": {
                "id": "feedback",
                "practice_id": "practice",
                "findings": ["Clear causal reasoning"],
                "feedback_artifact": "evidence",
            },
        },
        {
            "type": "interview_progress",
            "data": {
                "practice_id": "practice",
                "feedback_id": "feedback",
                "decision": "demonstrated",
                "rationale": "Answer demonstrates example",
                "reviewer": {"session": "synthetic-coach"},
            },
        },
    ]
    with pytest.raises(ValueError, match="evidence_artifact"):
        activity.finish(
            store, started["id"], result(tmp_path, artifacts=[artifact], records=records)
        )
    assert not store.all("interview_plans")
    records[-1]["data"]["evidence_artifact"] = "evidence"
    activity.finish(store, started["id"], result(tmp_path, artifacts=[artifact], records=records))
    assert stats.compute(store)["interviews"]["evidence_backed_progress"] == {"demonstrated": 1}


def prepare_cv(store, tmp_path, **kwargs):
    text, coverage = workflow.markdown_draft(store.facts, "product")
    cv = tmp_path / "cv.md"
    atomic_write(cv, text)
    matrix = json_file(tmp_path, "coverage.json", coverage)
    package = workflow.prepare(
        store,
        "master",
        "product",
        cv=cv,
        author_model="gpt-6-astra",
        author_session="synthetic-author",
        coverage_file=matrix,
        **kwargs,
    )
    return package, cv, matrix


def test_stats_separates_packages_versions_hiring_and_sends(store, tmp_path):
    package, _, _ = prepare_cv(store, tmp_path)
    package["application_status"] = "submitted"
    store.put("packages", package)
    started = activity.start(store, request(tmp_path))
    activity.finish(store, started["id"], result(tmp_path))
    summary = stats.compute(store)
    assert summary["submissions"]["evidence_backed"] == 0
    assert summary["documents"]["packages"] == summary["documents"]["versions"] == 1
    assert summary["vacancies"]["hiring_availability"] == {"unknown": 1}
    assert summary["activities"]["actual_models"] == {"unknown": 1}
    assert summary["activities"]["telemetry"]["cost"]["total"] is None
    assert summary["activities"]["durations"][0]["seconds"] >= 0
    html = report.render(store).read_text()
    assert "Overview" in html and "Activities" in html and "Interviews" in html
    assert html.count('class="card"') == 6
    assert 'name="viewport"' in html and 'class="table-scroll"' in html
    assert "prefers-color-scheme:dark" in html
    assert "<summary>Activity details</summary>" in html
    assert "<details open" not in html


def test_actual_submission_requires_evidence(store, tmp_path):
    package, _, _ = prepare_cv(store, tmp_path)
    started = activity.start(store, request(tmp_path))
    record = {
        "type": "submission",
        "data": {
            "package_id": package["id"],
            "version_id": package["current_version"],
            "channel": "manual",
            "sent_at": "2026-01-01T10:00:00+00:00",
            "user_confirmed": True,
        },
    }
    with pytest.raises(ValueError, match="evidence_artifact"):
        activity.finish(store, started["id"], result(tmp_path, records=[record]))
    record["data"]["evidence_artifact"] = "evidence"
    activity.finish(
        store, started["id"], result(tmp_path, records=[record], artifacts=[file_ref(tmp_path)])
    )
    assert stats.compute(store)["submissions"]["evidence_backed"] == 1
    evidence = store.all("submissions")[0]["evidence"]
    atomic_write(store.path(evidence["path"]), "tampered")
    assert stats.compute(store)["submissions"]["evidence_backed"] == 0


def test_contributors_final_reviewer_independent_from_all(store, tmp_path):
    package, cv, matrix = prepare_cv(store, tmp_path)
    first_task = store.path(package["versions"][0]["files"]["task"]).read_bytes()
    contributor = {
        "role": "author",
        "model": "gpt-6-astra",
        "session": "synthetic-author",
        "outputs": [{"document": "cv", "path": str(cv), "sha256": digest(cv.read_bytes())}],
    }
    editor = {**contributor, "role": "editor", "session": "synthetic-editor"}
    path = json_file(
        tmp_path, "contributors.json", {"schema_version": 1, "contributors": [contributor, editor]}
    )
    package = workflow.prepare(
        store, "master", "product", cv=cv, coverage_file=matrix, contributors_file=path
    )
    assert len(package["versions"]) == 2
    assert store.path(package["versions"][0]["files"]["task"]).read_bytes() == first_task
    version = package["versions"][-1]
    task = read_json(store.path(version["files"]["task"]))
    assert task["schema_version"] == workflow.HANDOFF_SCHEMA_VERSION
    assert "task" not in task["inputs"]
    review = {
        "kind": "content",
        "version_id": version["id"],
        "sha256": version["sha256"],
        "model": "gpt-6-astra",
        "session": "synthetic-editor",
        "passed": True,
        "coverage_complete": True,
        "findings": ["Synthetic evidence checked"],
    }
    with pytest.raises(ValueError, match="Independent"):
        workflow.record_review(store, package["id"], json_file(tmp_path, "review.json", review))
    review["session"] = "synthetic-independent"
    workflow.record_review(store, package["id"], json_file(tmp_path, "review.json", review))
    assert verify(store)["passed"]
    contributor["outputs"][0]["sha256"] = "0" * 64
    json_file(tmp_path, "contributors.json", {"schema_version": 1, "contributors": [contributor]})
    with pytest.raises(ValueError, match="stale"):
        workflow.prepare(store, "master", "product", cv=cv, contributors_file=path)


def test_standalone_letter_exact_cv_binding_and_stale_rejection(store, tmp_path):
    package, cv, matrix = prepare_cv(store, tmp_path)
    actor = {"model": "gpt-6-astra", "session": "synthetic-letter-author"}
    started = activity.start(store, request(tmp_path, actor=actor))
    letter = file_ref(tmp_path, "letter", "Synthetic cover letter")
    activity.finish(
        store,
        started["id"],
        result(
            tmp_path,
            artifacts=[letter],
            records=[
                {
                    "type": "cover_letter",
                    "data": {
                        "id": "letter-one",
                        "cv_package_id": package["id"],
                        "cv_version_id": package["current_version"],
                        "draft_artifact": "letter",
                    },
                }
            ],
        ),
    )
    composed = workflow.prepare(
        store,
        "master",
        "product",
        cv=cv,
        coverage_file=matrix,
        author_model="gpt-6-astra",
        author_session="synthetic-author",
        letter_record="letter-one",
    )
    assert composed["versions"][-1]["cv_version_id"] == package["current_version"]
    assert len(composed["versions"][-1]["contributors"]) == 2
    same = workflow.prepare(
        store,
        "master",
        "product",
        cv=cv,
        coverage_file=matrix,
        author_model="gpt-6-astra",
        author_session="synthetic-author",
        letter_record="letter-one",
    )
    assert same == composed
    atomic_write(cv, cv.read_text() + "\nNew synthetic context\n")
    with pytest.raises(ValueError, match="stale CV"):
        workflow.prepare(
            store,
            "master",
            "product",
            cv=cv,
            author_model="gpt-6-astra",
            author_session="synthetic-author",
            letter_record="letter-one",
        )


def test_cli_activity_stats_and_linked_existing_command(store, tmp_path):
    args = parser().parse_args(
        ["--home", str(store.home), "activity", "start", "--request", str(request(tmp_path))]
    )
    started = run(args)
    assert run(parser().parse_args(["--home", str(store.home), "activity", "show", started["id"]]))[
        "resumable"
    ]
    run(
        parser().parse_args(
            [
                "--home",
                str(store.home),
                "--activity-id",
                started["id"],
                "evaluate",
                "--track",
                "product",
            ]
        )
    )
    shown = activity.show(store, started["id"])
    assert any(e["type"] == "vacancy_evaluated" for e in shown["events"])
    assert (
        run(parser().parse_args(["--home", str(store.home), "stats"]))["activities"]["total"] == 1
    )


def test_external_writing_cannot_bypass_flagship_gate(store, tmp_path):
    for skill in ("career-natural-writing", "career-cover-letter", "career-cv-tailor"):
        started = activity.start(store, request(tmp_path, skill=skill))
        assert started["status"] == "blocked"
    started = activity.start(store, request(tmp_path))
    artifacts = [file_ref(tmp_path, "before"), file_ref(tmp_path, "after")]
    with pytest.raises(ValueError, match="flagship"):
        activity.finish(
            store,
            started["id"],
            result(
                tmp_path,
                artifacts=artifacts,
                records=[
                    {
                        "type": "text_revision",
                        "data": {
                            "before_artifact": "before",
                            "after_artifact": "after",
                            "change_notes": "Edited",
                        },
                    }
                ],
            ),
        )


def test_review_tampering_cannot_promote_readiness(store, tmp_path):
    package, _, _ = prepare_cv(store, tmp_path)
    version = package["versions"][0]
    review = {
        "kind": "content",
        "version_id": version["id"],
        "sha256": version["sha256"],
        "model": "gpt-6-astra",
        "session": "synthetic-reviewer",
        "passed": False,
        "coverage_complete": True,
        "findings": ["Needs clarification"],
    }
    workflow.record_review(store, package["id"], json_file(tmp_path, "review.json", review))
    version = store.get("packages", package["id"])["versions"][0]
    review["passed"] = True
    atomic_write(store.path(version["reviews"][0]), encode(review))
    review.update(kind="visual", checked_pages=[1], extracted_text_checked=True)
    with pytest.raises(ValueError, match="hashes"):
        workflow.record_review(store, package["id"], json_file(tmp_path, "review.json", review))
    assert stats.compute(store)["documents"]["current_review_readiness"] == {"invalid": 1}


def test_explicit_contributors_cannot_omit_bound_letter_author(store, tmp_path):
    package, cv, matrix = prepare_cv(store, tmp_path)
    actor = {"model": "gpt-6-astra", "session": "synthetic-letter-author"}
    started = activity.start(store, request(tmp_path, actor=actor))
    letter = file_ref(tmp_path, "letter", "Synthetic letter")
    activity.finish(
        store,
        started["id"],
        result(
            tmp_path,
            artifacts=[letter],
            records=[
                {
                    "type": "cover_letter",
                    "data": {
                        "id": "letter-two",
                        "cv_package_id": package["id"],
                        "cv_version_id": package["current_version"],
                        "draft_artifact": "letter",
                    },
                }
            ],
        ),
    )
    contributors = json_file(
        tmp_path,
        "contributors.json",
        {
            "schema_version": 1,
            "contributors": [
                {
                    "role": "editor",
                    "model": "gpt-6-astra",
                    "session": "synthetic-composer",
                    "outputs": [
                        {"document": "cv", "path": str(cv), "sha256": digest(cv.read_bytes())},
                        {"document": "letter", "path": letter["path"], "sha256": letter["sha256"]},
                    ],
                }
            ],
        },
    )
    composed = workflow.prepare(
        store,
        "master",
        "product",
        cv=cv,
        coverage_file=matrix,
        contributors_file=contributors,
        letter_record="letter-two",
    )
    version = composed["versions"][-1]
    assert {c["session"] for c in version["contributors"]} == {
        "synthetic-composer",
        "synthetic-author",
        "synthetic-letter-author",
    }
    review = {
        "kind": "content",
        "version_id": version["id"],
        "sha256": version["sha256"],
        "model": "gpt-6-astra",
        "session": "synthetic-letter-author",
        "passed": True,
        "coverage_complete": True,
        "findings": ["Inspected synthetic letter"],
    }
    with pytest.raises(ValueError, match="Independent"):
        workflow.record_review(store, composed["id"], json_file(tmp_path, "review.json", review))


def test_response_evidence_and_source_health_stats(store, tmp_path):
    package, _, _ = prepare_cv(store, tmp_path)
    started = activity.start(store, request(tmp_path))
    records = [
        {
            "type": "submission",
            "data": {
                "id": "send",
                "package_id": package["id"],
                "version_id": package["current_version"],
                "channel": "manual",
                "sent_at": "2026-01-01T10:00:00+00:00",
                "user_confirmed": True,
                "evidence_artifact": "evidence",
            },
        },
        {
            "type": "employer_response",
            "data": {
                "submission_id": "send",
                "status": "interview",
                "received_at": "2026-01-02T10:00:00+00:00",
                "summary": "Fictional interview invitation",
                "evidence_artifact": "evidence",
            },
        },
    ]
    activity.finish(
        store, started["id"], result(tmp_path, artifacts=[file_ref(tmp_path)], records=records)
    )
    store.put(
        "source_health",
        {"id": "synthetic-source", "status": "success_nonempty", "last_success": "2026-01-01"},
    )
    workflow.learning_plan(store, None, "product")
    summary = stats.compute(store)
    assert summary["responses"]["statuses"] == {"interview": 1}
    assert summary["sources"]["errors"] == 0
    assert summary["interviews"]["baseline_learning_plans"] == 1


def test_repeated_evaluation_links_original_event(store, tmp_path):
    workflow.evaluate(store, track="product")
    original = next(e for e in store.all("events") if e["type"] == "vacancy_evaluated")
    started = activity.start(store, request(tmp_path))
    activity.bind(store, started["id"])
    workflow.evaluate(store, track="product")
    assert original in activity.show(store, started["id"])["events"]


def test_result_validation_rolls_back_artifact_registration(store, tmp_path):
    started = activity.start(store, request(tmp_path))
    count = store.db.execute("SELECT count(*) FROM artifacts").fetchone()[0]
    with pytest.raises(ValueError):
        activity.finish(
            store,
            started["id"],
            result(
                tmp_path,
                artifacts=[file_ref(tmp_path)],
                records=[{"type": "company_dossier", "data": {}}],
            ),
        )
    assert store.db.execute("SELECT count(*) FROM artifacts").fetchone()[0] == count
    assert activity.show(store, started["id"])["status"] == "running"


def test_latest_assessment_uses_real_evaluation_order(store):
    vacancy = store.get("vacancies", "demo-platform-lead")
    initial = workflow.evaluate(store, vacancy["id"], "product")[0]
    vacancy["availability"] = "closed"
    store.put("vacancies", vacancy)
    workflow.evaluate(store, vacancy["id"], "product")
    assert stats.compute(store)["assessments"]["latest_by_track"]["product"] == {"watch": 1}
    vacancy["availability"] = "unknown"
    store.put("vacancies", vacancy)
    assert workflow.evaluate(store, vacancy["id"], "product")[0]["id"] == initial["id"]
    assert stats.compute(store)["assessments"]["latest_by_track"]["product"] == {
        initial["decision"]: 1
    }


def test_future_or_undated_submission_rejected(store, tmp_path):
    package, _, _ = prepare_cv(store, tmp_path)
    started = activity.start(store, request(tmp_path))
    for timestamp in ("2999-01-01T00:00:00+00:00", "2026-01-01"):
        with pytest.raises(ValueError, match="timestamp"):
            activity.finish(
                store,
                started["id"],
                result(
                    tmp_path,
                    artifacts=[file_ref(tmp_path)],
                    records=[
                        {
                            "type": "submission",
                            "data": {
                                "package_id": package["id"],
                                "version_id": package["current_version"],
                                "channel": "manual",
                                "sent_at": timestamp,
                                "user_confirmed": True,
                                "evidence_artifact": "evidence",
                            },
                        }
                    ],
                ),
            )


def test_contributors_reject_conflicting_explicit_author(store, tmp_path):
    _, cv, _ = prepare_cv(store, tmp_path)
    path = json_file(
        tmp_path,
        "contributors.json",
        {
            "schema_version": 1,
            "contributors": [
                {
                    "role": "author",
                    "model": "gpt-6-astra",
                    "session": "synthetic-author",
                    "outputs": [
                        {"document": "cv", "path": str(cv), "sha256": digest(cv.read_bytes())}
                    ],
                }
            ],
        },
    )
    for model, session in (
        ("not-a-model", "synthetic-author"),
        ("gpt-6-astra", "different-session"),
    ):
        with pytest.raises(ValueError, match="Explicit author"):
            workflow.prepare(
                store,
                "master",
                "product",
                cv=cv,
                contributors_file=path,
                author_model=model,
                author_session=session,
            )


def test_interview_stats_invalidates_tampered_practice_chain(store, tmp_path):
    refs = {
        name: file_ref(tmp_path, name, "Synthetic " + name)
        for name in ("plan", "practice", "feedback", "progress")
    }
    started = activity.start(store, request(tmp_path))
    records = [
        {
            "type": "interview_plan",
            "data": {
                "id": "plan",
                "track": "product",
                "objectives": ["Metrics"],
                "plan_artifact": "plan",
            },
        },
        {
            "type": "interview_practice",
            "data": {
                "id": "practice",
                "plan_id": "plan",
                "exercise": "Metrics",
                "evidence_artifact": "practice",
            },
        },
        {
            "type": "interview_feedback",
            "data": {
                "id": "feedback",
                "practice_id": "practice",
                "findings": ["Clear"],
                "feedback_artifact": "feedback",
            },
        },
        {
            "type": "interview_progress",
            "data": {
                "practice_id": "practice",
                "feedback_id": "feedback",
                "decision": "demonstrated",
                "rationale": "Clear explanation",
                "evidence_artifact": "progress",
                "reviewer": {"session": "synthetic-coach"},
            },
        },
    ]
    activity.finish(
        store, started["id"], result(tmp_path, artifacts=list(refs.values()), records=records)
    )
    assert stats.compute(store)["interviews"]["evidence_backed_progress"] == {"demonstrated": 1}
    practice = store.get("interview_practices", "practice")
    atomic_write(store.path(practice["evidence"]["path"]), "Changed practice")
    assert stats.compute(store)["interviews"]["evidence_backed_progress"] == {}
