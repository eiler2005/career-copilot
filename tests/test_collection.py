"""Collection, normalised conditions, campaigns and adding a vacancy (synthetic data only)."""

import json
import socket

import httpx
import pytest

from job_search_agent import availability, campaigns, inbox, intake, maintenance, sources
from job_search_agent import vacancy_fields as fields
from job_search_agent.cli import seed_demo
from job_search_agent.core import Store, atomic_write, encode, init_home

VACANCY = "demo-platform-lead"


@pytest.fixture
def store(tmp_path, monkeypatch):
    monkeypatch.setattr(sources.time, "sleep", lambda _seconds: None)

    def resolve(host, port, *args, **kwargs):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", port))]

    monkeypatch.setattr(availability.socket, "getaddrinfo", resolve)
    with Store(init_home(tmp_path / "workspace", demo=True)) as value:
        seed_demo(value)
        yield value


# --------------------------------------------------------------------------- conditions


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("от 250 000 до 350 000 ₽ на руки", (250000, 350000, "RUB", "unknown", "net")),
        ("Salary: $150,000 - $200,000 per year", (150000, 200000, "USD", "year", "unknown")),
        ("€90k–110k gross annually", (90000, 110000, "EUR", "year", "gross")),
        ("до 400 000 руб. в месяц", (None, 400000, "RUB", "month", "unknown")),
        (
            "Pay range: 180,000 USD to 220,000 USD a year",
            (180000, 220000, "USD", "year", "unknown"),
        ),
    ],
)
def test_salary_keeps_the_original_range_currency_and_period(text, expected):
    salary = fields.salary_from_text(text, "posting_text")
    assert (
        salary["min"],
        salary["max"],
        salary["currency"],
        salary["period"],
        salary["gross_net"],
    ) == expected
    assert salary["raw"] == text


def test_salary_without_currency_or_amount_is_not_invented():
    assert fields.salary_from_text("Competitive salary and equity", "posting_text") is None
    assert fields.salary_from_text("Team of 150 people", "posting_text") is None


def test_hh_item_conditions_come_from_structured_fields():
    item = {
        "salary": {"from": 300000, "to": None, "currency": "RUR", "gross": False},
        "work_format": [{"id": "HYBRID"}],
        "employment": {"id": "full"},
        "published_at": "2026-09-01T10:00:00+0300",
        "area": {"name": "Example City"},
        "languages": [{"id": "eng", "name": "English", "level": {"name": "B2"}}],
    }
    result = fields.from_provider("hh", item, "Описание роли", "Example City")
    assert result["salary"]["min"] == 300000 and result["salary"]["max"] is None
    assert result["salary"]["currency"] == "RUB" and result["salary"]["gross_net"] == "net"
    assert result["salary"]["period"] == "unknown"
    assert result["work_mode"] == {"value": "hybrid", "source": "hh.work_format", "raw": "HYBRID"}
    assert result["employment"]["value"] == "full_time"
    assert result["language"]["value"] == ["en"]
    assert result["published_on"] == "2026-09-01"


def test_remote_without_a_country_list_does_not_allow_any_country():
    ashby = fields.from_provider("ashby", {"isRemote": True, "employmentType": "FullTime"}, "")
    assert ashby["work_mode"]["value"] == "remote"
    assert ashby["allowed_geography"]["status"] == "unknown"
    listed = fields.from_provider(
        "corporate",
        {
            "jobLocationType": "TELECOMMUTE",
            "applicantLocationRequirements": [{"@type": "Country", "name": "Canada"}],
            "baseSalary": {
                "currency": "CAD",
                "value": {"minValue": 120000, "maxValue": 150000, "unitText": "YEAR"},
            },
            "datePosted": "2026-08-30",
        },
        "",
    )
    assert listed["allowed_geography"]["countries"] == ["Canada"]
    assert listed["salary"]["period"] == "year" and listed["published_on"] == "2026-08-30"
    stated = fields.from_posting("We hire remotely. Remote (US only).", None, "Remote")
    assert stated["allowed_geography"]["countries"] == ["United States"]
    assert "US only" in stated["allowed_geography"]["basis"]


def test_aggregator_conversion_stays_separate_from_employer_salary():
    result = fields.from_aggregate({"salaryUsdMo": 9000, "salaryCite": None, "jobMode": "Remote"})
    assert result["salary"] is None
    assert result["provider_conversion"]["amount"] == 9000
    assert "not an employer offer" in result["provider_conversion"]["note"]


def test_known_values_survive_a_less_informative_update():
    old = fields.from_posting("Salary: 100000 EUR per year. Hybrid.", None, "Example City, hybrid")
    new = fields.empty()
    merged = fields.merge(old, new)
    assert merged["salary"]["min"] == 100000 and merged["work_mode"]["value"] == "hybrid"


# --------------------------------------------------------------------------- observation merge


def test_excerpt_never_replaces_full_text_and_status_is_reported(store):
    base = {
        "id": "board-role",
        "company_id": "example-systems",
        "title": "Platform Lead",
        "location": "Example City",
        "urls": ["https://example.invalid/jobs/role"],
        "text": "Full synthetic description " * 20,
        "content_scope": "full",
        "availability": "closed",
    }
    first = store.observe_vacancy_detailed(base, "synthetic", "snapshot-1")
    assert first["status"] == "new"
    again = store.observe_vacancy_detailed(base, "synthetic", "snapshot-2")
    assert again["status"] == "unchanged"
    excerpt = {**base, "text": "Short card", "content_scope": "excerpt", "availability": "unknown"}
    changed = store.observe_vacancy_detailed(excerpt, "synthetic", "snapshot-3")
    vacancy = store.get("vacancies", "board-role")
    assert vacancy["content_scope"] == "full" and vacancy["text"] == base["text"]
    assert vacancy["availability"] == "closed"
    assert changed["status"] == "unchanged"


def test_collection_run_lists_new_changed_duplicates_and_errors(store):
    settings = store.settings
    settings["sources"] = [
        {
            "id": "board",
            "provider": "greenhouse",
            "board": "example",
            "company_id": "example-systems",
        },
        {
            "id": "broken",
            "provider": "greenhouse",
            "company_id": "example-systems",
            "proxy_env": "X",
        },
    ]
    atomic_write(store.home / "settings.json", encode(settings))
    jobs = {
        "jobs": [
            {
                "id": 11,
                "title": "Platform Product Lead",
                "absolute_url": "https://example.invalid/jobs/11",
                "location": {"name": "Example City"},
                "content": "<p>Synthetic role</p>",
                "updated_at": "2026-09-10T00:00:00Z",
            }
        ]
    }
    with httpx.Client(
        transport=httpx.MockTransport(lambda request: httpx.Response(200, json=jobs))
    ) as client:
        sources.discover(store, client=client)
    [run] = store.all("collection_runs")
    assert run["new"] == ["greenhouse-example-systems-11"]
    assert run["possible_duplicates"] == [
        {
            "vacancy_id": "greenhouse-example-systems-11",
            "other_id": VACANCY,
            "reason": "same_title_and_company",
        }
    ]
    assert [(error["source_id"], error["status"]) for error in run["errors"]] == [
        ("broken", "config_error")
    ]
    vacancy = store.get("vacancies", "greenhouse-example-systems-11")
    assert vacancy["conditions"]["updated_on"] == "2026-09-10"
    assert store.get("vacancies", VACANCY)["availability"] == "unknown"


# --------------------------------------------------------------------------- intake


POSTING_TEXT = """Title: Staff Platform Manager
Company: Fictional Robotics
Location: Example City, hybrid
Salary: от 400 000 до 500 000 ₽ в месяц

Responsibilities: lead a fictional platform group. Fluent English is required.
This synthetic text exists only for tests and describes no real employer.
"""


def test_add_from_text_creates_reviewable_company_and_keeps_original(store):
    result = intake.from_text(store, POSTING_TEXT, market="ru", track="product")
    assert result["status"] == "new" and result["company_created"] is True
    company = store.get("companies", result["company_id"])
    assert company["needs_review"] is True and company["name"] == "Fictional Robotics"
    conditions = result["conditions"]
    assert (conditions["salary"]["min"], conditions["salary"]["max"]) == (400000, 500000)
    assert conditions["work_mode"]["value"] == "hybrid"
    assert conditions["language"]["value"] == ["en"]
    assert store.path(result["snapshot"]).read_text(encoding="utf-8") == POSTING_TEXT
    repeat = intake.from_text(store, POSTING_TEXT, market="ru", track="product")
    assert repeat["vacancy_id"] == result["vacancy_id"] and repeat["status"] == "unchanged"
    with pytest.raises(ValueError, match="title"):
        intake.from_text(store, "No header, only a long enough body of synthetic text here.")


def test_add_from_url_reads_jsonld_and_refuses_blocked_or_unnamed_pages(store):
    posting = {
        "@context": "https://schema.org",
        "@type": "JobPosting",
        "title": "Head of Fictional Platform",
        "hiringOrganization": {"name": "Example Systems (fictional)"},
        "description": "<p>Synthetic posting. Salary: $150,000 - $180,000 per year.</p>",
        "jobLocation": {"name": "Example City"},
        "employmentType": "FULL_TIME",
    }
    pages = {
        "/jobs/1": httpx.Response(
            200,
            text=f'<html><script type="application/ld+json">{json.dumps(posting)}</script></html>',
        ),
        "/jobs/blocked": httpx.Response(403, text="denied"),
        "/jobs/plain": httpx.Response(200, text="<h1>Plain role</h1><p>" + "text " * 80 + "</p>"),
    }
    client = httpx.Client(transport=httpx.MockTransport(lambda request: pages[request.url.path]))
    result = intake.from_url(store, "https://jobs.example.invalid/jobs/1", client=client)
    assert result["company_id"] == "example-systems" and result["company_created"] is False
    assert result["conditions"]["employment"]["value"] == "full_time"
    assert result["conditions"]["salary"]["max"] == 180000
    with pytest.raises(ValueError, match="restricted"):
        intake.from_url(store, "https://jobs.example.invalid/jobs/blocked", client=client)
    with pytest.raises(ValueError, match="company"):
        intake.from_url(store, "https://jobs.example.invalid/jobs/plain", client=client)
    plain = intake.from_url(
        store,
        "https://jobs.example.invalid/jobs/plain",
        company_id="example-systems",
        client=client,
    )
    assert plain["content_scope"] == "page_text"


def test_add_request_goes_through_the_inbox(store, tmp_path):
    inbox.write_request(
        tmp_path / "state", {"type": "vacancy_add", "payload": {"text": POSTING_TEXT}}
    )
    with pytest.raises(ValueError):
        inbox.write_request(tmp_path / "state", {"type": "vacancy_add", "payload": {}})
    inbox.import_requests(store, tmp_path / "state" / inbox.REQUEST_DIR)
    [outcome] = inbox.apply_requests(store)["requests"]
    assert outcome["status"] == "applied"
    [request] = store.all("inbox_requests")
    assert request["result"]["status"] == "new"


# --------------------------------------------------------------------------- campaigns


def campaign(**updates):
    return {
        "name": "Intl platform product",
        "market": "intl",
        "track": "product",
        "role_titles": ["Product Lead"],
        "work_countries": ["Canada"],
        "work_modes": ["remote", "hybrid"],
        "salary": {"min": 150000, "currency": "USD", "period": "year"},
        "exclusions": ["gambling"],
        **updates,
    }


def test_campaign_validation_rejects_unclear_settings():
    for bad in (
        campaign(track="sales"),
        campaign(market="moon"),
        campaign(work_modes=["sometimes"]),
        campaign(salary={"min": 1, "currency": "dollars", "period": "year"}),
        campaign(name=""),
    ):
        with pytest.raises(ValueError):
            campaigns.validate(bad)
    with pytest.raises(ValueError, match="unique"):
        campaigns.validate_all([campaign(), campaign()])


def test_campaign_match_keeps_unknown_and_never_converts_currency(store):
    vacancy = store.get("vacancies", VACANCY)
    vacancy["conditions"] = fields.from_posting(
        "Remote. Salary: 120 000 EUR per year.", None, "Remote"
    )
    result = campaigns.match(vacancy, campaigns.validate(campaign()))
    by_name = {item["name"]: item["status"] for item in result["criteria"]}
    assert by_name == {
        "market": "match",
        "track": "match",
        "role_titles": "match",
        "work_countries": "unknown",
        "work_modes": "match",
        "salary": "unknown",
        "exclusions": "match",
    }
    assert result["status"] == "unknown"
    excluded = campaigns.match(
        {**vacancy, "text": "A gambling platform"}, campaigns.validate(campaign())
    )
    assert excluded["status"] == "mismatch"
    director = campaigns.match(
        {**vacancy, "title": "Platform Director"}, campaigns.validate(campaign(role_titles=["CTO"]))
    )
    assert {item["name"]: item["status"] for item in director["criteria"]}[
        "role_titles"
    ] == "mismatch"


def test_campaign_upsert_request_checks_the_campaign_version(store, tmp_path):
    first = {
        "type": "campaign_upsert",
        "payload": {"campaign": campaign(id="intl"), "expected_version": None},
    }
    inbox.write_request(tmp_path / "state", first)
    inbox.import_requests(store, tmp_path / "state" / inbox.REQUEST_DIR)
    assert inbox.apply_requests(store)["requests"][0]["status"] == "applied"
    assert [item["id"] for item in campaigns.configured(store.settings)] == ["intl"]
    stale = {
        "type": "campaign_upsert",
        "payload": {"campaign": campaign(id="intl", name="Renamed"), "expected_version": None},
    }
    inbox.write_request(tmp_path / "state2", stale)
    inbox.import_requests(store, tmp_path / "state2" / inbox.REQUEST_DIR)
    assert inbox.apply_requests(store)["requests"][0]["status"] == "conflict"
    assert campaigns.configured(store.settings)[0]["name"] == "Intl platform product"


def test_reextract_conditions_is_a_dry_run_until_applied(store):
    vacancy = store.get("vacancies", VACANCY)
    store.put("vacancies", {**vacancy, "text": "Salary: 90 000 EUR per year. Hybrid role."})
    preview = maintenance.reextract_conditions(store)
    assert preview["applied"] is False and preview["changed"] == 1
    assert "conditions" not in store.get("vacancies", VACANCY)
    applied = maintenance.reextract_conditions(store, apply=True)
    assert applied["applied"] is True
    assert store.get("vacancies", VACANCY)["conditions"]["salary"]["min"] == 90000
    assert maintenance.reextract_conditions(store)["changed"] == 0
