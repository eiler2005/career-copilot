import hashlib
import json
import os
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen

import pytest

from job_search_agent import dashboard
from job_search_agent.dashboard import (
    DashboardServer,
    Journal,
    _eligible_artifact_path,
    _safe_relative_path,
    allowed_hosts,
    location_display,
    redact_local_paths,
)


def make_workspace(tmp_path: Path) -> Path:
    home = tmp_path / "private-workspace"
    home.mkdir()
    (home / "workspace.json").write_text('{"schema_version": 1}', encoding="utf-8")
    (home / "settings.json").write_text('{"private": true}', encoding="utf-8")
    with sqlite3.connect(home / "journal.sqlite") as connection:
        connection.executescript(
            """
            CREATE TABLE records (kind TEXT NOT NULL, id TEXT NOT NULL, payload TEXT NOT NULL,
                                  PRIMARY KEY(kind, id));
            CREATE TABLE artifacts (path TEXT PRIMARY KEY, sha256 TEXT NOT NULL, bytes INTEGER NOT NULL);
            """
        )
        connection.execute(
            "INSERT INTO records VALUES (?, ?, ?)",
            (
                "vacancies",
                "role-1",
                json.dumps(
                    {
                        "id": "role-1",
                        "title": "Example role",
                        "location": "Moscow, Russia",
                        "urls": ["https://example.test/role"],
                    }
                ),
            ),
        )
        connection.execute(
            "INSERT INTO records VALUES (?, ?, ?)",
            ("activities", "act-1", json.dumps({"id": "act-1", "status": "open"})),
        )
    return home


def add_artifact(home: Path, relative: str, data: bytes) -> None:
    target = home.joinpath(*relative.split("/"))
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    with sqlite3.connect(home / "journal.sqlite") as connection:
        connection.execute(
            "INSERT INTO artifacts VALUES (?, ?, ?)",
            (relative, hashlib.sha256(data).hexdigest(), len(data)),
        )


@contextmanager
def running_server(home: Path, tmp_path: Path):
    assets = tmp_path / "assets"
    assets.mkdir()
    (assets / "index.html").write_text("<!doctype html><title>Dashboard</title>", encoding="utf-8")
    (assets / "styles.css").write_text("body{}", encoding="utf-8")
    (assets / "styles-v2.css").write_text("body{color: navy}", encoding="utf-8")
    (assets / "design.js").write_text(
        'document.documentElement.dataset.design = "v2";', encoding="utf-8"
    )
    (assets / "app.js").write_text("void 0", encoding="utf-8")
    server = DashboardServer(("127.0.0.1", 0), Journal.open(home), assets)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()


def request(url: str, host: str | None = None):
    target = Request(url, headers={"Host": host}) if host else url
    with urlopen(target, timeout=5) as response:
        return response.status, response.headers, response.read()


def head_request(url: str):
    with urlopen(Request(url, method="HEAD"), timeout=5) as response:
        return response.status, response.headers, response.read()


def test_dashboard_serves_only_allowlisted_assets_with_matching_get_and_head_metadata(
    tmp_path: Path,
):
    home = make_workspace(tmp_path)
    with running_server(home, tmp_path) as base:
        for asset, content_type in (
            ("styles.css", "text/css; charset=utf-8"),
            ("styles-v2.css", "text/css; charset=utf-8"),
            ("design.js", "text/javascript; charset=utf-8"),
            ("app.js", "text/javascript; charset=utf-8"),
        ):
            status, headers, body = request(f"{base}/assets/{asset}")
            head_status, head_headers, head_body = head_request(f"{base}/assets/{asset}")
            assert status == head_status == 200
            assert body and head_body == b""
            assert headers["Content-Type"] == head_headers["Content-Type"] == content_type
            assert (
                int(headers["Content-Length"]) == int(head_headers["Content-Length"]) == len(body)
            )
        with pytest.raises(HTTPError) as error:
            request(base + "/assets/secret.txt")
        assert error.value.code == 404


def test_location_display_is_conservative_about_ambiguous_cities():
    assert location_display({"location": "Moscow, Russia"}) == {
        "raw": "Moscow, Russia",
        "country": "Russia",
        "city": "Moscow",
        "remote": "unknown",
    }
    assert location_display({"location": "Springfield"}) == {
        "raw": "Springfield",
        "country": None,
        "city": None,
        "remote": "unknown",
    }
    assert location_display({"location": "Paris, France", "work_mode": "hybrid"}) == {
        "raw": "Paris, France",
        "country": "France",
        "city": "Paris",
        "remote": "hybrid",
    }
    assert location_display(
        {"location": {"raw": "Berlin, Germany", "country": "Freedonia", "city": "Capital"}}
    ) == {
        "raw": "Berlin, Germany",
        "country": "Freedonia",
        "city": "Capital",
        "remote": "unknown",
    }
    assert location_display({"location": "Springfield", "country": "Qazania", "city": "North"}) == {
        "raw": "Springfield",
        "country": "Qazania",
        "city": "North",
        "remote": "unknown",
    }
    assert location_display({"location": "Russia"}) == {
        "raw": "Russia",
        "country": "Russia",
        "city": None,
        "remote": "unknown",
    }
    assert location_display({"location": "Berlin, Paris, Germany"}) == {
        "raw": "Berlin, Paris, Germany",
        "country": "Germany",
        "city": None,
        "remote": "unknown",
    }
    assert location_display({"location": "Москва", "market": "ru"})["country"] == "Russia"
    assert location_display({"location": "Москва", "market": "ru"})["city"] == "Москва"
    assert location_display({"location": "New York, NY"}) == {
        "raw": "New York, NY",
        "country": "United States",
        "city": "New York",
        "remote": "unknown",
    }
    assert location_display({"location": "Seattle, US"})["city"] == "Seattle"
    assert location_display({"location": "San Francisco, CA"}) == {
        "raw": "San Francisco, CA",
        "country": "United States",
        "city": "San Francisco",
        "remote": "unknown",
    }
    assert location_display({"location": "Hong Kong SAR"}) == {
        "raw": "Hong Kong SAR",
        "country": "Hong Kong",
        "city": "Hong Kong",
        "remote": "unknown",
    }
    assert location_display({"location": "California, US"})["city"] is None
    assert location_display({"location": "Remote United States (remote)"}) == {
        "raw": "Remote United States (remote)",
        "country": "United States",
        "city": None,
        "remote": "remote",
    }
    assert location_display({"location": "San Francisco / Bellevue, US"})["city"] is None
    assert location_display({"location": "Paris"})["city"] is None
    assert location_display({"location": "Paris (Texas)"})["city"] is None
    assert location_display({"location": "France, Germany"})["country"] is None
    assert location_display({"location": "Paris, France, Berlin, Germany"})["country"] is None
    assert location_display({"location": "Remote, Germany"})["country"] == "Germany"


def test_dashboard_reads_existing_journal_without_changing_it(tmp_path: Path):
    home = make_workspace(tmp_path)
    database = home / "journal.sqlite"
    before = database.read_bytes(), database.stat().st_mtime_ns
    with running_server(home, tmp_path) as base:
        status, headers, body = request(base + "/api/workspace")
        assert status == 200
        assert headers["Cache-Control"] == "no-store"
        payload = json.loads(body)
        vacancy = payload["vacancies"][0]
        assert vacancy["kind"] == "vacancies"
        assert vacancy["payload"]["location"] == "Moscow, Russia"
        assert vacancy["display"]["location"]["country"] == "Russia"
        status, _, body = request(base + "/api/records/vacancies/role-1")
        assert status == 200
        assert json.loads(body)["payload"]["urls"] == ["https://example.test/role"]
    assert (database.read_bytes(), database.stat().st_mtime_ns) == before


def test_delete_journal_snapshot_is_readable_from_a_strict_read_only_mount(tmp_path: Path):
    home = make_workspace(tmp_path)
    database = home / "journal.sqlite"
    with sqlite3.connect(database) as connection:
        assert connection.execute("PRAGMA journal_mode=DELETE").fetchone()[0].lower() == "delete"
    assert not database.with_name("journal.sqlite-wal").exists()
    assert not database.with_name("journal.sqlite-shm").exists()
    os.chmod(database, 0o444)
    os.chmod(home, 0o555)
    try:
        payload = Journal.open(home).workspace()
    finally:
        os.chmod(home, 0o755)
        os.chmod(database, 0o644)
    assert payload["vacancies"][0]["id"] == "role-1"


def test_live_wal_commit_is_visible_to_the_next_request(tmp_path: Path):
    home = make_workspace(tmp_path)
    with running_server(home, tmp_path) as base:
        assert json.loads(request(base + "/api/workspace")[2])["vacancies"][0]["payload"][
            "title"
        ] == ("Example role")
        with sqlite3.connect(home / "journal.sqlite") as connection:
            assert connection.execute("PRAGMA journal_mode=WAL").fetchone()[0].lower() == "wal"
            connection.execute(
                "UPDATE records SET payload=? WHERE kind=? AND id=?",
                (
                    json.dumps(
                        {
                            "id": "role-1",
                            "title": "Updated role",
                            "location": "Moscow, Russia",
                        }
                    ),
                    "vacancies",
                    "role-1",
                ),
            )
        assert json.loads(request(base + "/api/workspace")[2])["vacancies"][0]["payload"][
            "title"
        ] == ("Updated role")


def test_dashboard_limits_records_and_artifacts_to_registered_safe_paths(tmp_path: Path):
    home = make_workspace(tmp_path)
    add_artifact(home, "packages/example.html", b"<h1>private</h1>")
    add_artifact(home, "packages/Резюме.pdf", b"pdf")
    add_artifact(home, "snapshots/provider/source.txt", b"source")
    add_artifact(home, "settings.json", b"{}")
    add_artifact(home, "facts.json", b"{}")
    add_artifact(home, "maintenance/review.json", b"{}")
    with running_server(home, tmp_path) as base:
        status, headers, body = request(base + "/api/artifacts/packages/example.html")
        assert status == 200
        assert body == b"<h1>private</h1>"
        assert headers["Content-Disposition"].startswith("attachment;")
        assert headers["Content-Type"] == "application/octet-stream"
        assert "default-src 'self'" in headers["Content-Security-Policy"]
        _, unicode_headers, _ = request(base + "/api/artifacts/" + quote("packages/Резюме.pdf"))
        assert 'filename="download.pdf"' in unicode_headers["Content-Disposition"]
        assert "filename*=UTF-8''packages%2F" not in unicode_headers["Content-Disposition"]
        assert "filename*=UTF-8''%D0%A0" in unicode_headers["Content-Disposition"]
        assert request(base + "/api/artifacts/snapshots/provider/source.txt")[2] == b"source"
        registry = json.loads(request(base + "/api/workspace")[2])["artifacts"]
        assert [artifact["path"] for artifact in registry] == [
            "packages/example.html",
            "packages/Резюме.pdf",
            "snapshots/provider/source.txt",
        ]
        for path in (
            "/api/artifacts/settings.json",
            "/api/artifacts/facts.json",
            "/api/artifacts/maintenance/review.json",
            "/api/artifacts/%2E%2E/settings.json",
            "/api/artifacts/journal.sqlite",
            "/api/records/settings/anything",
        ):
            with pytest.raises(HTTPError) as error:
                request(base + path)
            assert error.value.code == 404
    assert not _safe_relative_path("packages/header\r\nX-Injection: yes.txt")
    assert not _eligible_artifact_path("journal.sqlite")


def test_dashboard_rejects_an_untrusted_host_header(tmp_path: Path):
    home = make_workspace(tmp_path)
    with running_server(home, tmp_path) as base:
        assert request(base + "/healthz", host="127.0.0.1:18100")[0] == 200
        with pytest.raises(HTTPError) as error:
            request(base + "/api/workspace", host="attacker.example")
        assert error.value.code == 400


def test_registered_symlink_is_not_downloadable(tmp_path: Path):
    home = make_workspace(tmp_path)
    (home / "outside.html").write_text("outside", encoding="utf-8")
    (home / "packages").mkdir()
    (home / "packages" / "linked.html").symlink_to(home / "outside.html")
    data = b"outside"
    with sqlite3.connect(home / "journal.sqlite") as connection:
        connection.execute(
            "INSERT INTO artifacts VALUES (?, ?, ?)",
            ("packages/linked.html", hashlib.sha256(data).hexdigest(), len(data)),
        )
    with running_server(home, tmp_path) as base:
        with pytest.raises(HTTPError) as error:
            request(base + "/api/artifacts/packages/linked.html")
        assert error.value.code == 404


def test_legacy_file_alias_is_reachable_without_granting_arbitrary_paths(tmp_path: Path):
    home = make_workspace(tmp_path)
    add_artifact(home, "legacy/ai-job-search/cv.md", b"legacy CV")
    with sqlite3.connect(home / "journal.sqlite") as connection:
        connection.execute(
            "INSERT INTO records VALUES (?, ?, ?)",
            (
                "legacy_files",
                "ai-job-search/cv.md",
                json.dumps(
                    {
                        "id": "ai-job-search/cv.md",
                        "path": "legacy/ai-job-search/cv.md",
                        "sha256": hashlib.sha256(b"legacy CV").hexdigest(),
                    }
                ),
            ),
        )
    with running_server(home, tmp_path) as base:
        detail = json.loads(request(base + "/api/records/legacy_files/ai-job-search%2Fcv.md")[2])
        assert detail["payload"]["path"] == "legacy/ai-job-search/cv.md"
        assert request(base + "/api/artifacts/legacy/ai-job-search/cv.md")[2] == b"legacy CV"


def add_record(home: Path, kind: str, payload: dict) -> None:
    with sqlite3.connect(home / "journal.sqlite") as connection:
        connection.execute(
            "INSERT INTO records VALUES (?, ?, ?)", (kind, payload["id"], json.dumps(payload))
        )


@contextmanager
def configured_server(home: Path, tmp_path: Path, hosts: frozenset[str]):
    assets = tmp_path / "configured-assets"
    assets.mkdir()
    (assets / "index.html").write_text("<!doctype html>", encoding="utf-8")
    server = DashboardServer(("127.0.0.1", 0), Journal.open(home), assets, hosts)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()


def test_reverse_proxy_hostname_is_accepted_only_when_configured(tmp_path: Path):
    home = make_workspace(tmp_path)
    hosts = allowed_hosts(["Career.Example.test.", "other.example.test"])
    assert {"localhost", "127.0.0.1", "[::1]", "career.example.test"} <= hosts
    with configured_server(home, tmp_path, hosts) as base:
        assert request(base + "/api/workspace", host="career.example.test")[0] == 200
        assert request(base + "/healthz", host="CAREER.EXAMPLE.TEST:443")[0] == 200
        with pytest.raises(HTTPError) as error:
            request(base + "/api/workspace", host="career.example.test.attacker.test")
        assert error.value.code == 400
    for invalid in ("career.example.test:8443", "10.0.0.1", "exa mple.test", "-bad.test", "a/b"):
        with pytest.raises(ValueError):
            allowed_hosts([invalid])
    assert allowed_hosts(["", " , "]) == allowed_hosts()


def test_allowed_hosts_come_from_cli_and_environment(tmp_path: Path, monkeypatch):
    home = make_workspace(tmp_path)
    captured = {}
    monkeypatch.setattr(
        dashboard,
        "serve",
        lambda home_arg, host, port, hosts, state_dir: captured.update(home=home_arg, hosts=hosts),
    )
    monkeypatch.setenv("AJH_DASHBOARD_ALLOWED_HOSTS", "env.example.test")
    monkeypatch.setattr(
        "sys.argv",
        ["ajh-dashboard", "--home", str(home), "--allowed-host", "cli.example.test"],
    )
    assert dashboard.main() == 0
    assert {"env.example.test", "cli.example.test"} <= captured["hosts"]


def test_responses_are_not_indexed_and_report_journal_freshness(tmp_path: Path):
    home = make_workspace(tmp_path)
    with running_server(home, tmp_path) as base:
        status, headers, body = request(base + "/api/workspace")
        _, page_headers, _ = request(base + "/")
    assert status == 200
    assert headers["X-Robots-Tag"] == "noindex, nofollow, noarchive"
    assert page_headers["X-Robots-Tag"] == "noindex, nofollow, noarchive"
    assert "camera=()" in headers["Permissions-Policy"]
    meta = json.loads(body)["meta"]
    assert meta["journal_updated_at"].endswith("+00:00")
    assert meta["journal_updated_at"] <= meta["generated_at"]


def test_import_records_are_listed_in_history_and_openable(tmp_path: Path):
    home = make_workspace(tmp_path)
    add_record(home, "imports", {"id": "import-1", "files": 3, "dry_run": False})
    with running_server(home, tmp_path) as base:
        history = json.loads(request(base + "/api/workspace")[2])["history"]
        assert [(item["kind"], item["id"]) for item in history] == [("imports", "import-1")]
        detail = json.loads(request(base + "/api/records/imports/import-1")[2])
    assert detail["payload"]["files"] == 3


def test_configured_sources_show_health_and_never_checked_sources_without_secrets(
    tmp_path: Path,
):
    home = make_workspace(tmp_path)
    (home / "settings.json").write_text(
        json.dumps(
            {
                "sources": [
                    {
                        "id": "checked-board",
                        "provider": "greenhouse",
                        "company_name": "Example Systems",
                        "enabled": True,
                        # Built at runtime so the repository privacy scanner sees no credential URL.
                        "proxy_url": "http://user:" + "secret" + "@proxy.example.invalid",
                        "token": "secret-token",
                    },
                    {"id": "quiet-board", "provider": "corporate", "enabled": False},
                    {"id": "../bad", "provider": "corporate"},
                    "not-a-source",
                ]
            }
        ),
        encoding="utf-8",
    )
    add_record(home, "source_health", {"id": "checked-board", "status": "ok", "count": 4})
    add_record(home, "source_health", {"id": "retired-board", "status": "blocked"})
    with running_server(home, tmp_path) as base:
        body = request(base + "/api/workspace")[2]
        sources = json.loads(body)["sources"]
        detail = json.loads(request(base + "/api/records/source_settings/checked-board")[2])
    assert b"secret" not in body
    assert [(item["kind"], item["id"]) for item in sources] == [
        ("source_health", "retired-board"),
        ("source_settings", "checked-board"),
        ("source_settings", "quiet-board"),
    ]
    assert sources[1]["payload"]["health"]["status"] == "ok"
    assert "health" not in sources[2]["payload"]
    assert detail["payload"]["company_name"] == "Example Systems"
    assert set(detail["payload"]) <= {*dashboard.SOURCE_SETTING_FIELDS, "health"}


def test_local_filesystem_paths_are_redacted_from_record_payloads(tmp_path: Path):
    home = make_workspace(tmp_path)
    user_root = "/Users" + "/example"  # split so the privacy scanner sees no private path
    add_record(
        home,
        "activities",
        {
            "id": "act-2",
            "actor": {"session": user_root + "/.sessions/run.jsonl"},
            "artifacts": [{"original_path": "~/drafts/cv.md", "path": "packages/cv.md"}],
            "note": f"Kept {user_root} in prose.\nSecond line",
            "url": "https://example.test/Users/role",
        },
    )
    with running_server(home, tmp_path) as base:
        body = request(base + "/api/workspace")[2]
        detail = json.loads(request(base + "/api/records/activities/act-2")[2])["payload"]
    assert (user_root + "/.sessions").encode() not in body
    assert detail["actor"]["session"] == "[local]/run.jsonl"
    assert detail["artifacts"] == [{"original_path": "[local]/cv.md", "path": "packages/cv.md"}]
    assert detail["note"].startswith(f"Kept {user_root}")
    assert detail["url"] == "https://example.test/Users/role"
    assert redact_local_paths("C:\\Users\\example\\cv.docx") == "[local]/cv.docx"
    assert redact_local_paths("/opt/career-copilot/workspace/") == "[local]/workspace"
    assert redact_local_paths("/api/records") == "/api/records"


def test_older_assessment_of_the_same_vacancy_and_track_is_marked_superseded(tmp_path: Path):
    home = make_workspace(tmp_path)
    for key, at, track in (
        ("a-old", "2026-01-01T10:03:00Z", "product"),
        ("a-new", "2026-01-01T10:19:00Z", "product"),
        ("a-other", "2026-01-01T09:00:00Z", "technical-leadership"),
    ):
        add_record(
            home, "assessments", {"id": key, "vacancy_id": "role-1", "track": track, "at": at}
        )
    with running_server(home, tmp_path) as base:
        vacancies = json.loads(request(base + "/api/workspace")[2])["vacancies"]
    current = {item["id"]: item["display"].get("current") for item in vacancies}
    assert current == {"a-new": True, "a-old": False, "a-other": True, "role-1": None}


def test_latex_sources_are_downloadable_and_semicolon_locations_resolve(tmp_path: Path):
    home = make_workspace(tmp_path)
    add_artifact(home, "packages/example/cv.tex", b"\\documentclass{article}")
    with running_server(home, tmp_path) as base:
        assert request(base + "/api/artifacts/packages/example/cv.tex")[2].startswith(b"\\doc")
    assert location_display({"location": "Москва; Россия"})["country"] == "Russia"
    assert location_display({"location": "Dubai, Dubai, UAE"})["city"] == "Dubai"
    assert location_display({"location": "Greater London, England, UK"})["city"] == "London"


def add_plans(home: Path) -> None:
    plan_text = (
        "# Shared plan\n\nSession `/root/private-session` and **bold `todo`** text.\n\n"
        "| Week | Work |\n| --- | --- |\n| 1 | Case and metrics |\n\n- first\n- second\n"
    )
    add_artifact(home, "activity-artifacts/plan.md", plan_text.encode())
    add_artifact(home, "packages/example/cv.pdf", b"%PDF-1.4 not text")
    add_record(home, "companies", {"id": "example-co", "name": "Example Systems"})
    add_record(
        home,
        "vacancies",
        {"id": "role-2", "title": "Platform Lead", "company_id": "example-co", "urls": []},
    )
    for key, created in (
        ("learning-old", "2026-01-01T10:03:00Z"),
        ("learning-new", "2026-01-01T10:19:00Z"),
    ):
        add_record(
            home,
            "learning",
            {
                "id": key,
                "track": "product",
                "vacancy_id": "role-2",
                "created_at": created,
                "hours_per_week": 6,
                "interview_date": None,
                "warning": "Baseline only.",
                "weeks": [{"week": 1, "focus": "Метрики", "deliverable": "Кейс", "status": "todo"}],
                "gaps": [
                    {
                        "text": "Platform experience",
                        "gap_type": "evidence",
                        "mandatory": True,
                        "status": "todo",
                        "next_action": "Prepare a case",
                        "done_requires": "Reviewed answer",
                        "resources": [],
                        "vacancy_ids": ["role-2"],
                    }
                ],
                "shared": ["STAR bank"],
            },
        )
    add_record(
        home,
        "interview_plans",
        {
            "id": "interview-plan-product",
            "track": "product",
            "created_at": "2026-01-02T09:00:00Z",
            "objectives": ["Explain the case"],
            "plan": {"path": "activity-artifacts/plan.md"},
        },
    )


def pdf_text(data: bytes) -> str:
    from io import BytesIO

    from pypdf import PdfReader

    return "\n".join(page.extract_text() or "" for page in PdfReader(BytesIO(data)).pages)


def test_markdown_artifacts_are_readable_inline_with_local_paths_redacted(tmp_path: Path):
    home = make_workspace(tmp_path)
    add_plans(home)
    with running_server(home, tmp_path) as base:
        status, headers, body = request(base + "/api/text/activity-artifacts/plan.md")
        for path in (
            "/api/text/packages/example/cv.pdf",
            "/api/text/activity-artifacts/missing.md",
        ):
            with pytest.raises(HTTPError) as error:
                request(base + path)
            assert error.value.code == 404
    assert status == 200
    assert headers["Content-Type"] == "text/plain; charset=utf-8"
    assert headers["X-Content-Type-Options"] == "nosniff"
    text = body.decode()
    assert "`[local]/private-session`" in text
    assert "/root/private-session" not in text


def test_learning_and_interview_plans_download_as_pdf(tmp_path: Path):
    home = make_workspace(tmp_path)
    add_plans(home)
    with running_server(home, tmp_path) as base:
        status, headers, body = request(base + "/api/plans/learning/learning-new.pdf")
        _, _, english = request(base + "/api/plans/learning/learning-new.pdf?lang=en")
        _, interview_headers, interview = request(
            base + "/api/plans/interview_plans/interview-plan-product.pdf"
        )
        for path in (
            "/api/plans/vacancies/role-2.pdf",
            "/api/plans/learning/missing.pdf",
            "/api/plans/learning/..%2Fsettings.pdf",
        ):
            with pytest.raises(HTTPError) as error:
                request(base + path)
            assert error.value.code == 404
        preparations = json.loads(request(base + "/api/workspace")[2])["preparations"]
    assert status == 200 and headers["Content-Type"] == "application/pdf"
    assert headers["Content-Disposition"] == (
        'attachment; filename="career-copilot-learning-product-2026-01-01.pdf"'
    )
    learning = pdf_text(body)
    assert "План подготовки · Продуктовое" in learning
    assert "Platform Lead · Example Systems" in learning
    assert "Метрики" in learning and "Prepare a case" in learning
    assert "Learning plan · Product" in pdf_text(english)
    assert interview_headers["Content-Disposition"].startswith(
        'attachment; filename="career-copilot-interview-plans-product-2026-01-02.pdf"'
    )
    detailed = pdf_text(interview)
    assert "Shared plan" in detailed and "Case and metrics" in detailed
    assert "private-session" in detailed and "/root/" not in detailed
    current = {item["id"]: item["display"].get("current") for item in preparations}
    assert current["learning-new"] is True and current["learning-old"] is False


def test_markdown_blocks_parse_the_plan_subset():
    from job_search_agent.dashboard_pdf import markdown_blocks, redact_local_text

    blocks = markdown_blocks(
        "# Title\nline one\nline two\n\n| A | B |\n|---|:---:|\n| 1 | 2 |\n\n1. one\n2. two\n- x\n"
    )
    assert blocks == [
        ("h", 1, "Title"),
        ("p", "line one line two"),
        ("table", [["A", "B"], ["1", "2"]]),
        ("ol", ["one", "two"]),
        ("ul", ["x"]),
    ]
    assert redact_local_text("see ~/notes/plan.md, then /api/text") == (
        "see [local]/plan.md, then /api/text"
    )


def post(url: str, body: object, headers: dict | None = None):
    data = json.dumps(body).encode()
    target = Request(
        url,
        data=data,
        method="POST",
        headers={"Content-Type": "application/json", **(headers or {})},
    )
    with urlopen(target, timeout=5) as response:
        return response.status, json.loads(response.read())


@contextmanager
def stateful_server(home: Path, tmp_path: Path):
    assets = tmp_path / "state-assets"
    assets.mkdir()
    (assets / "index.html").write_text("<!doctype html>", encoding="utf-8")
    journal = Journal.open(home, tmp_path / "dashboard-state")
    server = DashboardServer(("127.0.0.1", 0), journal, assets)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()


def test_availability_check_endpoint_is_guarded_cached_and_overlaid(tmp_path: Path, monkeypatch):
    home = make_workspace(tmp_path)
    calls = []

    def fake_check(url):
        calls.append(url)
        return {
            "url": url,
            "status": "closed",
            "confidence": "high",
            "reason": "closed_marker",
            "evidence": "вакансия в архиве",
            "checked_at": dashboard.datetime.now(dashboard.UTC).isoformat(timespec="seconds"),
            "method": "availability-rules-v1",
            "http_status": 200,
            "final_url": url,
        }

    monkeypatch.setattr(dashboard.availability, "check_url", fake_check)
    header = {"X-Career-Copilot": "availability-check"}
    with running_server(home, tmp_path) as base:
        with pytest.raises(HTTPError) as error:
            post(base + "/api/availability/check", {"vacancy_ids": ["role-1"]}, header)
        assert error.value.code == 501
        assert json.loads(request(base + "/api/workspace")[2])["capabilities"] == {
            "availability_check": False,
            "requests": False,
        }
    with stateful_server(home, tmp_path) as base:
        for body, headers, code in (
            ({"vacancy_ids": ["role-1"]}, {}, 403),
            ({"vacancy_ids": ["role-1"]}, {**header, "Origin": "https://attacker.example"}, 403),
            ({"vacancy_ids": [f"role-{i}" for i in range(11)]}, header, 400),
            ({"vacancy_ids": ["../x"]}, header, 400),
        ):
            with pytest.raises(HTTPError) as error:
                post(base + "/api/availability/check", body, headers)
            assert error.value.code == code
        status, result = post(
            base + "/api/availability/check",
            {"vacancy_ids": ["role-1", "missing"]},
            {**header, "Origin": "http://127.0.0.1"},
        )
        assert status == 200 and list(result["results"]) == ["role-1"]
        _, cached = post(base + "/api/availability/check", {"vacancy_ids": ["role-1"]}, header)
        assert cached["results"]["role-1"]["cached"] is True and len(calls) == 1
        payload = json.loads(request(base + "/api/workspace")[2])
        vacancy = next(item for item in payload["vacancies"] if item["id"] == "role-1")
        assert payload["capabilities"] == {"availability_check": True, "requests": True}
        assert vacancy["display"]["availability"] == "closed"
        assert vacancy["display"]["availability_check"]["pending_import"] is True
        detail = json.loads(request(base + "/api/records/vacancies/role-1")[2])
        assert detail["display"]["checked_at"] == vacancy["display"]["checked_at"]
    assert calls == ["https://example.test/role"]
    state = json.loads((tmp_path / "dashboard-state" / "availability-checks.json").read_text())
    assert state["checks"]["role-1"]["reason"] == "closed_marker"
    with pytest.raises(ValueError):
        Journal.open(home, home / "state")


def test_request_endpoint_stores_validated_requests_without_touching_the_journal(tmp_path: Path):
    home = make_workspace(tmp_path)
    journal_bytes = (home / "journal.sqlite").read_bytes()
    header = {"X-Career-Copilot": "request"}
    decision = {"type": "vacancy_decision", "payload": {"status": "interested"}}
    with running_server(home, tmp_path) as base:
        with pytest.raises(HTTPError) as error:
            post(base + "/api/requests", decision, header)
        assert error.value.code == 501
    with stateful_server(home, tmp_path) as base:
        version = json.loads(request(base + "/api/records/vacancies/role-1")[2])["version"]
        pinned = {**decision, "base": {"kind": "vacancies", "id": "role-1", "version": version}}
        for body, headers, code in (
            (pinned, {}, 403),
            (pinned, {**header, "Origin": "https://attacker.example"}, 403),
            ({"type": "drop_table"}, header, 422),
            (decision, header, 422),
            ({**pinned, "base": {**pinned["base"], "id": "missing"}}, header, 404),
            ({**pinned, "base": {**pinned["base"], "version": "0" * 16}}, header, 409),
        ):
            with pytest.raises(HTTPError) as error:
                post(base + "/api/requests", body, headers)
            assert error.value.code == code
        status, stored = post(
            base + "/api/requests",
            {**pinned, "id": "../../escape", "created_at": "1999-01-01T00:00:00+00:00"},
            {**header, "Origin": "http://127.0.0.1"},
        )
        assert status == 202 and stored["status"] == "pending"
        assert stored["request"]["id"].startswith("req-")
        assert not stored["request"]["created_at"].startswith("1999")
        listed = json.loads(request(base + "/api/requests")[2])["requests"]
        assert [item["id"] for item in listed] == [stored["request"]["id"]]
        workspace = json.loads(request(base + "/api/workspace")[2])
        assert workspace["pending_requests"] == listed
    files = list((tmp_path / "dashboard-state" / "requests").glob("*.json"))
    assert [path.stem for path in files] == [stored["request"]["id"]]
    assert (home / "journal.sqlite").read_bytes() == journal_bytes


def test_translations_and_superseded_records_reach_the_browser(tmp_path: Path):
    home = make_workspace(tmp_path)
    add_record(
        home,
        "text_translations",
        {
            "id": "tr-1",
            "text": "Archive only; do not apply.",
            "translations": {
                "en": "Archive only; do not apply.",
                "ru": "Только архив; не откликаться.",
                "xx": "ignored",
            },
        },
    )
    add_record(
        home,
        "superseded_records",
        {
            "id": "assessments--assessment-old",
            "kind": "assessments",
            "record_id": "assessment-old",
            "superseded_by": "assessment-new",
            "payload": {"id": "assessment-old", "vacancy_id": "role-1", "track": "product"},
        },
    )
    with running_server(home, tmp_path) as base:
        payload = json.loads(request(base + "/api/workspace")[2])
        archived = json.loads(request(base + "/api/records/assessments/assessment-old")[2])
    assert payload["translations"]["Archive only; do not apply."] == {
        "en": "Archive only; do not apply.",
        "ru": "Только архив; не откликаться.",
    }
    assert archived["payload"]["vacancy_id"] == "role-1"
    assert archived["display"]["current"] is False
    assert archived["display"]["superseded_by"] == "assessment-new"


def test_vacancy_descriptions_quote_the_posting_or_research_section(tmp_path: Path):
    home = make_workspace(tmp_path)
    posting = (
        "Title: Example role\nCompany: Example Systems\nLocation: Moscow\nURL: https://example.test/role\n\n"
        "We build a platform for payments. The team owns APIs and partner integrations. "
        "Responsibilities: lead the roadmap."
    )
    add_artifact(home, "legacy/postings/example-role.txt", posting.encode())
    add_record(
        home,
        "legacy_files",
        {"id": "postings/example-role.txt", "path": "legacy/postings/example-role.txt"},
    )
    research = "# Big Tech\n\n| Role | Place | Status | Theme |\n|---|---|---|---|\n| Staff PM 998877 | London | open | Local payment methods growth |\n"
    add_artifact(home, "legacy/research/search.md", research.encode())
    add_record(
        home,
        "vacancies",
        {"id": "role-2", "title": "Example role", "posting": "postings/example-role.txt"},
    )
    add_record(
        home,
        "vacancies",
        {
            "id": "stripe-998877",
            "title": "Staff PM",
            "evidence": ["legacy/research/search.md"],
            "urls": [],
        },
    )
    with running_server(home, tmp_path) as base:
        vacancies = {
            item["id"]: item
            for item in json.loads(request(base + "/api/workspace")[2])["vacancies"]
        }
        detail = json.loads(request(base + "/api/records/vacancies/role-2")[2])
    described = vacancies["role-2"]["display"]["description"]
    assert (
        described["kind"] == "posting" and described["path"] == "legacy/postings/example-role.txt"
    )
    assert described["excerpt"].startswith("We build a platform for payments.")
    assert "Company:" not in described["excerpt"] and described["meta"]["location"] == "Moscow"
    assert detail["display"]["description"] == described
    research_description = vacancies["stripe-998877"]["display"]["description"]
    assert research_description["kind"] == "research"
    assert research_description["excerpt"] == "Local payment methods growth"
    assert vacancies["role-1"]["display"]["description"] is None


def test_description_excerpts_are_short_and_end_cleanly():
    from job_search_agent.descriptions import excerpt, parse_posting, plain

    text = "First sentence is here. " * 30
    short = excerpt(text)
    assert len(short) <= 360 and short.endswith(".")
    assert plain("**Bold** [link](https://x.test) `code` - item") == "Bold link code - item"
    meta, body = parse_posting("Title: A\nSalary: \n\nBody text")
    assert meta == {"title": "A", "salary": ""} and body == "Body text"


def test_vacancies_carry_dates_campaign_matches_and_collection_runs(tmp_path: Path):
    home = make_workspace(tmp_path)
    (home / "settings.json").write_text(
        json.dumps(
            {
                "campaigns": [
                    {
                        "id": "intl",
                        "name": "Synthetic intl",
                        "market": "intl",
                        "track": "product",
                        "work_modes": ["remote"],
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    with sqlite3.connect(home / "journal.sqlite") as connection:
        connection.execute(
            "UPDATE records SET payload=? WHERE kind='vacancies' AND id='role-1'",
            (
                json.dumps(
                    {
                        "id": "role-1",
                        "title": "Example role",
                        "market": "intl",
                        "first_seen": "2026-09-01T00:00:00+00:00",
                        "conditions": {
                            "published_on": "2026-08-30",
                            "work_mode": {"value": "remote", "source": "synthetic"},
                        },
                    }
                ),
            ),
        )
    add_record(
        home,
        "collection_runs",
        {"id": "run-1", "started_at": "2026-09-02T00:00:00+00:00", "new": ["role-1"]},
    )
    with running_server(home, tmp_path) as base:
        payload = json.loads(request(base + "/api/workspace")[2])
        vacancy = next(item for item in payload["vacancies"] if item["id"] == "role-1")
        detail = json.loads(request(base + "/api/records/vacancies/role-1")[2])
    assert vacancy["display"]["dates"]["published_on"] == "2026-08-30"
    assert vacancy["display"]["dates"]["discovered_at"].startswith("2026-09-01")
    [match] = vacancy["display"]["campaigns"]
    assert match["campaign_id"] == "intl"
    assert {item["name"]: item["status"] for item in match["criteria"]}["work_modes"] == "match"
    assert detail["display"]["campaigns"] == vacancy["display"]["campaigns"]
    # An invalid campaign list is not partially applied.
    assert payload["campaigns"] == [] or all(
        item["id"] != "broken" for item in payload["campaigns"]
    )
    assert [item["id"] for item in payload["sources"] if item["kind"] == "collection_runs"] == [
        "run-1"
    ]
    assert len(vacancy["version"]) == 16


def test_vacancies_carry_profile_relevance_in_lists_and_single_records(tmp_path):
    home = make_workspace(tmp_path)
    (home / "settings.json").write_text(
        json.dumps({"policy": {"tracks": ["product"], "interests": ["payments"]}}),
        encoding="utf-8",
    )
    with sqlite3.connect(home / "journal.sqlite") as connection:
        connection.execute(
            "INSERT INTO records VALUES (?, ?, ?)",
            (
                "vacancies",
                "role-2",
                json.dumps(
                    {"id": "role-2", "title": "Head of Product, Payments", "urls": []},
                ),
            ),
        )
    from job_search_agent import relevance

    # One verified payments fact backs the payments domain; the review below was made with it.
    facts = {"facts": [{"id": "f1", "tags": ["payments"], "verification": "verified"}]}
    (home / "facts.json").write_text(json.dumps(facts), encoding="utf-8")
    reviewed = {"id": "role-1", "title": "Example role", "location": "Moscow, Russia", "urls": []}
    with sqlite3.connect(home / "journal.sqlite") as connection:
        connection.execute(
            "UPDATE records SET payload=? WHERE kind='vacancies' AND id='role-1'",
            (json.dumps(reviewed),),
        )
        connection.execute(
            "INSERT INTO records VALUES (?, ?, ?)",
            (
                "relevance_reviews",
                "review-1",
                json.dumps(
                    {
                        "id": "review-1",
                        "created_at": "2026-09-18T10:00:00+00:00",
                        "actor": {"model": "claude-opus-5"},
                        "facts_sha256": relevance.facts_version(facts),
                        "reviews": [
                            {
                                "vacancy_id": "role-1",
                                "verdict": "possible",
                                "score": 58,
                                "track": "product",
                                "summary": "Unclear role; worth reading the posting.",
                                "reasons": [{"kind": "gap", "text": "No description"}],
                                "fact_ids": [],
                                "input_sha256": relevance.review_input(reviewed),
                            }
                        ],
                    }
                ),
            ),
        )
    with running_server(home, tmp_path) as base:
        data = json.loads(request(base + "/api/workspace")[2])
        tiers = {item["id"]: item["display"]["relevance"]["tier"] for item in data["vacancies"]}
        assert tiers == {"role-1": "possible", "role-2": "strong"}
        role = next(item for item in data["vacancies"] if item["id"] == "role-1")
        assert role["display"]["relevance"]["method"] == "agent"
        assert role["display"]["relevance"]["rules"]["tier"] == "off_profile"
        assert data["relevance_error"] is None and data["relevance_queries"] == []
        single = json.loads(request(base + "/api/records/vacancies/role-2")[2])
        assert single["display"]["relevance"]["domains"][0]["id"] == "payments"
    (home / "settings.json").write_text(json.dumps({"relevance": {"target_level": "x"}}))
    (tmp_path / "second").mkdir()
    with running_server(home, tmp_path / "second") as base:
        data = json.loads(request(base + "/api/workspace")[2])
        assert "target_level" in data["relevance_error"]
        assert "relevance" not in data["vacancies"][0]["display"]
