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

from job_search_agent.dashboard import (
    DashboardServer,
    Journal,
    _eligible_artifact_path,
    _safe_relative_path,
    location_display,
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
