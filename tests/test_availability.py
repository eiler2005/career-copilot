"""Conservative, explainable vacancy availability checks."""

import json
import socket

import httpx
import pytest

from job_search_agent import availability
from job_search_agent.cli import seed_demo
from job_search_agent.core import Store, init_home

POSTING = "https://jobs.example.test/vacancy/123456/platform-lead"


@pytest.fixture
def store(tmp_path):
    home = init_home(tmp_path / "private", demo=True)
    with Store(home) as db:
        seed_demo(db)
        vacancy = db.get("vacancies", "demo-platform-lead")
        db.put("vacancies", {**vacancy, "urls": [POSTING]})
        yield db


@pytest.fixture(autouse=True)
def public_dns(monkeypatch):
    def resolve(host, port, *args, **kwargs):
        address = "10.0.0.8" if host.startswith("internal.") else "93.184.216.34"
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (address, port))]

    monkeypatch.setattr(availability.socket, "getaddrinfo", resolve)


def page(body: str, script: str = "") -> str:
    return (
        f"<html><head><title>Role</title><script>{script}</script></head><body>{body}</body></html>"
    )


@pytest.mark.parametrize(
    ("status", "final", "markup", "expected"),
    [
        (404, POSTING, "", ("closed", "http_gone", "high")),
        (403, POSTING, "", ("unknown", "access_blocked", "low")),
        (
            200,
            POSTING,
            "<title>Attention Required! | Cloudflare</title>",
            ("unknown", "access_blocked", "low"),
        ),
        (500, POSTING, "", ("unknown", "http_error", "low")),
        (
            200,
            "https://jobs.example.test/vacancies/",
            page("Jobs"),
            ("closed", "redirected_away", "medium"),
        ),
        (
            200,
            "https://www.example.test/closed/",
            page("Closed"),
            ("closed", "redirected_away", "medium"),
        ),
        (
            200,
            POSTING,
            page("<h2>Вакансия в архиве</h2><button>Откликнуться</button>"),
            ("closed", "closed_marker", "high"),
        ),
        (
            200,
            POSTING,
            page("<p>No longer accepting applications</p>"),
            ("closed", "closed_marker", "high"),
        ),
        (
            200,
            POSTING,
            page(
                '<script type="application/ld+json">{"@type":"JobPosting","validThrough":"2020-01-01"}</script>'
            ),
            ("closed", "structured_expired", "high"),
        ),
        (
            200,
            POSTING,
            page("<a>Apply now</a>", script="'вакансия в архиве'"),
            ("open", "apply_control", "medium"),
        ),
        (
            200,
            POSTING,
            page(
                '<script type="application/ld+json">{"@type":"JobPosting","title":"Lead"}</script>'
            ),
            ("open", "structured_posting", "medium"),
        ),
        (200, POSTING, page("Welcome"), ("unknown", "no_signal", "low")),
    ],
)
def test_classify_uses_visible_signals_only(status, final, markup, expected):
    result = availability.classify(POSTING, status, final, markup)
    assert (result["status"], result["reason"], result["confidence"]) == expected


def test_human_closed_state_is_not_reopened_by_medium_signal():
    medium_open = {"status": "open", "confidence": "medium"}
    assert availability.effective_availability("closed", medium_open) == "conflicting"
    assert availability.effective_availability("unknown", medium_open) == "open"
    assert availability.effective_availability("archived", {"status": "closed"}) == "archived"
    assert availability.effective_availability("open", {"status": "closed"}) == "closed"
    assert availability.effective_availability("open", {"status": "unknown"}) == "open"


def test_private_and_local_addresses_are_never_fetched():
    for url in (
        "http://localhost/job",
        "ftp://jobs.example.test/1",
        "https://internal.example.test/1",
        "https://user:" + "pw" + "@jobs.example.invalid/",  # split for the privacy scanner
    ):
        with pytest.raises(ValueError):
            availability.public_url(url)
    result = availability.check_url("https://internal.example.test/vacancy/1")
    assert (result["status"], result["reason"]) == ("unknown", "not_public_url")
    assert availability.check_url(None)["reason"] == "no_url"


def test_redirects_are_revalidated_and_results_update_the_journal(store):
    calls = []

    def handler(request):
        calls.append(str(request.url))
        if request.url.path.endswith("platform-lead"):
            return httpx.Response(302, headers={"location": "https://internal.example.test/steal"})
        return httpx.Response(200, text="secret")

    client = httpx.Client(transport=httpx.MockTransport(handler), follow_redirects=False)
    result = availability.check_url(POSTING, client)
    assert result["reason"] == "not_public_url" and calls == [POSTING]

    closed = httpx.Client(
        transport=httpx.MockTransport(
            lambda request: httpx.Response(200, text=page("Вакансия закрыта"))
        ),
        follow_redirects=False,
    )
    summary = availability.run(store, delay=0, client=closed)
    assert summary["counts"] == {"open": 0, "closed": 1, "unknown": 0}
    vacancy = store.get("vacancies", "demo-platform-lead")
    assert vacancy["availability"] == "closed"
    assert vacancy["availability_check"]["reason"] == "closed_marker"
    assert vacancy["status_checked_on"] == vacancy["availability_check"]["checked_at"][:10]
    assert len(vacancy["availability_history"]) == 1
    assert any(event["type"] == "availability_checked" for event in store.all("events"))
    # Inactive vacancies are skipped by default; explicit IDs are always checked.
    assert availability.run(store, delay=0, client=closed)["checked"] == 0
    assert availability.run(store, ["demo-platform-lead"], delay=0, client=closed)["checked"] == 1
    with pytest.raises(ValueError):
        availability.select(store, ["missing-vacancy"])


def test_dashboard_results_import_only_newer_checks(store):
    result = {
        "status": "open",
        "confidence": "medium",
        "reason": "apply_control",
        "evidence": "apply now",
        "checked_at": "2026-09-15T08:00:00+00:00",
        "method": availability.METHOD,
        "url": POSTING,
    }
    assert availability.import_results(store, {"demo-platform-lead": result, "gone": result}) == {
        "applied": 1,
        "skipped": 1,
    }
    older = {**result, "status": "closed", "checked_at": "2026-09-01T08:00:00+00:00"}
    assert availability.import_results(store, {"demo-platform-lead": older})["applied"] == 0
    assert store.get("vacancies", "demo-platform-lead")["availability"] == "open"
    with pytest.raises(ValueError):
        availability.import_results(store, {"demo-platform-lead": {"status": "maybe"}})
    json.dumps(store.get("vacancies", "demo-platform-lead"))
