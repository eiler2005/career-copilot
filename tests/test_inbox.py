"""Browser requests reach the journal only through versioned, auditable operations."""

import json

import pytest

from job_search_agent import activity, inbox
from job_search_agent.cli import parser, run, seed_demo
from job_search_agent.core import Store, VersionConflict, atomic_write, encode, init_home

VACANCY = "demo-platform-lead"


@pytest.fixture
def store(tmp_path):
    with Store(init_home(tmp_path / "workspace", demo=True)) as value:
        seed_demo(value)
        yield value


def write(tmp_path, *requests):
    folder = tmp_path / "state"
    for item in requests:
        inbox.write_request(folder, item)
    return folder / inbox.REQUEST_DIR


def decision(store, status="not_interested", version=None, reason="Relocation is required"):
    return {
        "type": "vacancy_decision",
        "base": {
            "kind": "vacancies",
            "id": VACANCY,
            "version": version or store.version("vacancies", VACANCY),
        },
        "payload": {"status": status, "reason": reason},
    }


def test_patch_checks_version_and_records_before_after(store):
    version = store.version("vacancies", VACANCY)
    updated = store.patch("vacancies", VACANCY, {"note": "synthetic"}, version, "test")
    assert updated["note"] == "synthetic" and store.version("vacancies", VACANCY) != version
    with pytest.raises(VersionConflict):
        store.patch("vacancies", VACANCY, {"note": "lost update"}, version, "test")
    assert store.get("vacancies", VACANCY)["note"] == "synthetic"
    event = next(e for e in store.all("events") if e["type"] == "record_updated")
    assert event["details"]["before"] == {"note": None}
    assert event["details"]["after"] == {"note": "synthetic"}
    with pytest.raises(ValueError, match="id"):
        store.patch("vacancies", VACANCY, {"id": "other"}, None, "test")


def test_import_and_apply_is_idempotent_and_keeps_evidence(store, tmp_path):
    before = store.get("vacancies", VACANCY)
    folder = write(tmp_path, decision(store))
    assert inbox.import_requests(store, folder) == {
        "imported": 1,
        "already_imported": 0,
        "invalid": 0,
    }
    assert inbox.import_requests(store, folder)["already_imported"] == 1
    applied = inbox.apply_requests(store)
    assert [item["status"] for item in applied["requests"]] == ["applied"]
    assert inbox.apply_requests(store) == {"processed": 0, "requests": []}
    vacancy = store.get("vacancies", VACANCY)
    assert vacancy["personal_decision"]["status"] == "not_interested"
    assert vacancy["requirements"] == before["requirements"]
    assert vacancy["availability"] == before["availability"]


def test_stale_request_becomes_conflict_and_changes_nothing(store, tmp_path):
    stale = decision(store)
    store.patch("vacancies", VACANCY, {"note": "changed elsewhere"}, None, "test")
    inbox.import_requests(store, write(tmp_path, stale))
    result = inbox.apply_requests(store)["requests"][0]
    assert result["status"] == "conflict" and "changed" in result["error"]
    assert "personal_decision" not in store.get("vacancies", VACANCY)
    request = store.all("inbox_requests")[0]
    assert request["status"] == "conflict" and request["error"]


def test_invalid_requests_are_rejected_before_they_are_stored(store, tmp_path):
    for bad in (
        {"type": "unknown"},
        {"type": "vacancy_decision", "payload": {"status": "interested"}},
        {**decision(store), "base": {"kind": "companies", "id": "x"}},
        decision(store, status="not_interested", reason=""),
        {"type": "task", "payload": {"task_type": "send_email"}},
        {"type": "task", "payload": {"task_type": "collect", "related": {"path": "/etc"}}},
    ):
        with pytest.raises(ValueError):
            inbox.write_request(tmp_path / "state", bad)
    broken = tmp_path / "broken.json"
    broken.write_text("{not json", encoding="utf-8")
    assert inbox.import_requests(store, broken)["invalid"] == 1


def test_failed_apply_rolls_back_and_reject_keeps_reason(store, tmp_path):
    folder = write(
        tmp_path,
        {"type": "evaluate", "payload": {"vacancy_id": "missing", "track": "product"}},
        {"type": "evaluate", "payload": {"vacancy_id": VACANCY, "track": "product"}},
    )
    inbox.import_requests(store, folder)
    statuses = sorted(item["status"] for item in inbox.apply_requests(store)["requests"])
    assert statuses == ["applied", "failed"]
    assert store.all("current_assessments")
    inbox.write_request(tmp_path / "state", decision(store))
    inbox.import_requests(store, folder)
    pending = next(item for item in store.all("inbox_requests") if item["status"] == "pending")
    assert inbox.reject_request(store, pending["id"], "Not now")["status"] == "rejected"
    with pytest.raises(ValueError):
        inbox.reject_request(store, pending["id"], "again")


def test_task_is_done_only_when_its_activity_really_finishes(store, tmp_path):
    folder = write(
        tmp_path,
        {
            "type": "task",
            "payload": {
                "task_type": "annotate_requirements",
                "related": {"vacancy_id": VACANCY, "track": "product"},
                "note": "Split the long requirement list",
            },
        },
    )
    inbox.import_requests(store, folder)
    assert inbox.apply_requests(store)["requests"][0]["status"] == "queued_for_agent"
    task = inbox.next_task(store)
    assert task["status"] == "queued" and task["skill"] == "career-job-search"
    request_path = tmp_path / "activity.json"
    atomic_write(
        request_path,
        encode({**task["activity_request"], "operation": "Annotate requirements"}),
    )
    started = activity.start(store, request_path)
    assert store.get("tasks", task["id"])["status"] == "running"
    assert inbox.next_task(store) is None
    with pytest.raises(ValueError, match="task"):
        activity.start(store, request_path)
    result_path = tmp_path / "result.json"
    atomic_write(
        result_path,
        encode({"schema_version": 1, "status": "blocked", "next_action": "Need the full text"}),
    )
    activity.finish(store, started["id"], result_path)
    closed = store.get("tasks", task["id"])
    assert closed["status"] == "blocked" and closed["next_action"] == "Need the full text"


def test_cli_inbox_and_tasks_commands(store, tmp_path):
    folder = write(tmp_path, decision(store, status="interested", reason=None))
    home = str(store.home)
    cli = parser()
    assert run(cli.parse_args(["--home", home, "inbox", "import", str(folder)]))["imported"] == 1
    listed = run(cli.parse_args(["--home", home, "inbox", "list", "--status", "pending"]))
    assert len(listed) == 1
    assert run(cli.parse_args(["--home", home, "inbox", "apply"]))["processed"] == 1
    assert run(cli.parse_args(["--home", home, "tasks", "next"])) == {"task": None}
    assert json.loads(encode(run(cli.parse_args(["--home", home, "tasks", "list"])))) == []
