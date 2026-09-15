"""CV module on synthetic data: states, based-on versions, edit proposals, decisions, import."""

import json

import pytest

from job_search_agent import activity, cv, inbox, workflow
from job_search_agent.cli import seed_demo
from job_search_agent.core import Store, atomic_write, digest, encode, init_home

VACANCY = "demo-platform-lead"
FLAGSHIP = {"environment": "claude", "model": "claude-opus-5", "session": "synthetic-author"}


@pytest.fixture
def store(tmp_path):
    with Store(init_home(tmp_path / "workspace", demo=True)) as value:
        seed_demo(value)
        yield value


def json_file(tmp_path, name, value):
    path = tmp_path / name
    atomic_write(path, encode(value))
    return path


def authored_master(store, tmp_path):
    text, coverage = workflow.markdown_draft(store.facts, "product")
    source = tmp_path / "cv.md"
    atomic_write(source, text)
    package = workflow.prepare(
        store,
        "master",
        "product",
        cv=source,
        author_model="claude-opus-5",
        author_session="synthetic-author",
        coverage_file=json_file(tmp_path, "coverage.json", coverage),
    )
    return package, package["versions"][-1], text


def propose(store, tmp_path, package, version, edits):
    request = json_file(
        tmp_path,
        "request.json",
        {
            "schema_version": 1,
            "skill": "career-cv-tailor",
            "operation": "Propose CV edits",
            "actor": FLAGSHIP,
            "expected_result": {"types": ["cv_edit_proposal"]},
        },
    )
    started = activity.start(store, request)
    result = json_file(
        tmp_path,
        "result.json",
        {
            "schema_version": 1,
            "status": "completed",
            "next_action": "User decides each edit",
            "records": [
                {
                    "type": "cv_edit_proposal",
                    "data": {
                        "id": "proposal-1",
                        "package_id": package["id"],
                        "version_id": version["id"],
                        "edits": edits,
                    },
                }
            ],
        },
    )
    return activity.finish(store, started["id"], result)


def test_version_states_follow_authorship_coverage_and_reviews():
    version = {"author_model": "claude-opus-5", "review_status": "pending"}
    assert cv.version_state({}, [], [], None)["state"] == "draft"
    assert cv.version_state(version, ["missing_or_changed:cv_pdf"], [], None)["state"] == "invalid"
    assert cv.version_state(version, [], [], [{"included": None}])["state"] == "awaiting_facts"
    assert cv.version_state(version, [], [], [])["state"] == "written"
    content = {"kind": "content", "passed": True}
    assert (
        cv.version_state(version, [], [{"kind": "content", "passed": False}], [])["state"]
        == "awaiting_content_review"
    )
    assert cv.version_state(version, [], [content], [])["state"] == "awaiting_visual_review"
    ready = {**version, "review_status": "passed"}
    assert (
        cv.version_state(ready, [], [content, {"kind": "visual", "passed": True}], [])["state"]
        == "ready"
    )


def test_vacancy_version_is_based_on_master_without_changing_it(store, tmp_path):
    master, master_version, text = authored_master(store, tmp_path)
    before = store.get("packages", master["id"])
    source = tmp_path / "tailored.md"
    atomic_write(source, text + "\nTailored emphasis for platform adoption.\n")
    package = workflow.prepare(
        store,
        VACANCY,
        "product",
        cv=source,
        author_model="claude-opus-5",
        author_session="synthetic-author",
        based_on=f"{master['id']}:{master_version['id']}",
    )
    assert package["versions"][-1]["based_on"]["version_id"] == master_version["id"]
    assert store.get("packages", master["id"]) == before
    with pytest.raises(ValueError, match="based-on"):
        workflow.prepare(
            store,
            VACANCY,
            "technical-leadership",
            cv=source,
            author_model="claude-opus-5",
            author_session="synthetic-author",
            based_on=f"{master['id']}:{master_version['id']}",
        )
    assert cv.overview(store)["masters"]["product"]["state"] == "written"


def test_proposals_quote_the_cv_and_never_add_unverified_evidence(store, tmp_path):
    package, version, text = authored_master(store, tmp_path)
    quote = text.splitlines()[0]
    facts = store.facts
    facts["facts"].append(
        {**facts["facts"][0], "id": "unverified", "verification": "self_reported"}
    )
    atomic_write(store.home / "facts.json", encode(facts))
    for bad, message in (
        (
            {"id": "e1", "kind": "wording", "before": "Not in the CV", "after": "x", "reason": "r"},
            "quote",
        ),
        (
            {
                "id": "e1",
                "kind": "add_evidence",
                "before": "",
                "section": "Experience",
                "after": "Led X",
                "reason": "r",
                "fact_ids": ["unverified"],
            },
            "verified",
        ),
        (
            {"id": "e1", "kind": "remove", "before": quote, "after": "something", "reason": "r"},
            "removal",
        ),
        (
            {
                "id": "e1",
                "kind": "wording",
                "before": quote,
                "after": "x",
                "reason": "r",
                "requirement_ids": ["missing"],
            },
            "requirement",
        ),
    ):
        with pytest.raises(ValueError, match=message):
            propose(store, tmp_path, package, version, [bad])
    finished = propose(
        store,
        tmp_path,
        package,
        version,
        [
            {
                "id": "e1",
                "kind": "wording",
                "before": quote,
                "after": quote + " (clarified)",
                "reason": "Clearer title",
            },
            {
                "id": "e2",
                "kind": "emphasis",
                "before": quote,
                "after": quote.upper(),
                "reason": "Emphasis",
                "needs_candidate_input": True,
                "question": "Is the upper-case title acceptable?",
            },
        ],
    )
    [proposal] = store.all("cv_edits")
    assert finished["status"] == "completed" and proposal["scope"] == "master"
    assert proposal["cv_source_sha256"] == version["sha256"]["cv_source"]


def test_decisions_are_history_and_the_draft_uses_only_accepted_edits(store, tmp_path):
    package, version, text = authored_master(store, tmp_path)
    lines = [line for line in text.splitlines() if line.strip()]
    propose(
        store,
        tmp_path,
        package,
        version,
        [
            {
                "id": "keep",
                "kind": "wording",
                "before": lines[0],
                "after": lines[0] + " — accepted",
                "reason": "r",
            },
            {
                "id": "drop",
                "kind": "wording",
                "before": lines[1],
                "after": "rejected text",
                "reason": "r",
            },
            {
                "id": "own",
                "kind": "wording",
                "before": lines[2],
                "after": "agent text",
                "reason": "r",
            },
            {
                "id": "later",
                "kind": "wording",
                "before": lines[3],
                "after": "undecided",
                "reason": "r",
            },
        ],
    )
    state = tmp_path / "state"
    for edit_id, decision, extra in (
        ("keep", "accept", {}),
        ("drop", "accept", {}),
        ("own", "edit", {"text": "user text"}),
    ):
        inbox.write_request(
            state,
            {
                "type": "cv_edit_decision",
                "base": {"kind": "cv_edits", "id": "proposal-1"},
                "payload": {
                    "proposal_id": "proposal-1",
                    "edit_id": edit_id,
                    "decision": decision,
                    **extra,
                },
            },
        )
    inbox.import_requests(store, state / inbox.REQUEST_DIR)
    assert {item["status"] for item in inbox.apply_requests(store)["requests"]} == {"applied"}
    cv.record_decision(
        store, {"proposal_id": "proposal-1", "edit_id": "drop", "decision": "reject"}
    )
    assert len(store.all("cv_edit_decisions")) == 4
    output = tmp_path / "draft.md"
    summary = cv.apply_edits(store, "proposal-1", output)
    draft = output.read_text(encoding="utf-8")
    assert summary["applied"] == ["keep", "own"] and summary["rejected"] == ["drop"]
    assert summary["undecided"] == ["later"]
    assert (
        lines[0] + " — accepted" in draft and "user text" in draft and "rejected text" not in draft
    )
    # The master package itself is unchanged; a new version needs prepare and reviews.
    assert store.get("packages", package["id"])["current_version"] == version["id"]
    with pytest.raises(ValueError):
        cv.record_decision(
            store, {"proposal_id": "proposal-1", "edit_id": "own", "decision": "edit", "text": ""}
        )


def test_requirement_coverage_must_cover_every_requirement_with_verified_facts(store, tmp_path):
    vacancy = store.get("vacancies", VACANCY)
    facts = store.facts
    good = [
        {
            "requirement_id": "req-platform",
            "status": "covered",
            "cv_location": "Experience",
            "fact_ids": ["sample-job"],
        }
    ]
    assert cv.validate_requirement_coverage(good, vacancy, facts)[0]["status"] == "covered"
    for bad in (
        [],
        [{**good[0], "fact_ids": []}],
        [{**good[0], "cv_location": None}],
        [{**good[0], "status": "maybe"}],
    ):
        with pytest.raises(ValueError):
            cv.validate_requirement_coverage(bad, vacancy, facts)
    _, _, text = authored_master(store, tmp_path)
    source = tmp_path / "tailored.md"
    atomic_write(source, text)
    package = workflow.prepare(
        store,
        VACANCY,
        "product",
        cv=source,
        author_model="claude-opus-5",
        author_session="synthetic-author",
        requirement_coverage_file=json_file(tmp_path, "requirement-coverage.json", good),
    )
    files = package["versions"][-1]["files"]
    assert (
        json.loads(store.path(files["requirement_coverage"]).read_text())[0]["cv_location"]
        == "Experience"
    )


def test_import_extracts_structure_and_queues_fact_extraction_without_creating_facts(store):
    facts_before = digest(store.facts)
    text = (
        "# Experience\n2019–2024 Example Systems, Platform Lead. Grew adoption by 40%.\n\n# Education\nFictional University, 2010-2014\n"
        + "Synthetic filler line.\n" * 5
    )
    result = cv.import_cv(store, text, "product", "synthetic-cv.md")
    assert [section["title"] for section in result["sections"]] == ["Experience", "Education"]
    assert result["dates"][0]["start"] == "2019" and any(
        "40%" in line for line in result["claims_to_check"]
    )
    task = store.get("tasks", result["task_id"])
    assert task["type"] == "extract_cv_facts" and task["status"] == "queued"
    assert digest(store.facts) == facts_before
    assert cv.import_cv(store, text, "product", "synthetic-cv.md")["id"] == result["id"]
    with pytest.raises(ValueError):
        cv.import_cv(store, "too short", "product", "x.md")


def test_dashboard_previews_package_pdfs_inline_and_reports_version_states(store, tmp_path):
    import threading
    from urllib.error import HTTPError
    from urllib.request import urlopen

    from job_search_agent.dashboard import DashboardServer, Journal

    package, version, _ = authored_master(store, tmp_path)
    assets = tmp_path / "assets"
    assets.mkdir()
    (assets / "index.html").write_text("<!doctype html>", encoding="utf-8")
    server = DashboardServer(("127.0.0.1", 0), Journal.open(store.home), assets)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        with urlopen(f"{base}/api/preview/{version['files']['cv_pdf']}", timeout=5) as response:
            assert response.headers["Content-Type"] == "application/pdf"
            assert response.headers["Content-Disposition"].startswith("inline")
            assert response.headers["X-Frame-Options"] == "SAMEORIGIN"
            assert response.read(4) == b"%PDF"
        with pytest.raises(HTTPError) as error:
            urlopen(f"{base}/api/preview/{version['files']['cv_source']}", timeout=5)
        assert error.value.code == 404
        with urlopen(f"{base}/api/workspace", timeout=5) as response:
            data = json.loads(response.read())
        with urlopen(f"{base}/", timeout=5) as response:
            assert "frame-src 'self'" in response.headers["Content-Security-Policy"]
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()
    record = next(item for item in data["documents"] if item["id"] == package["id"])
    assert record["display"]["versions"][version["id"]]["state"] == "written"
