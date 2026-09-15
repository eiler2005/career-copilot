"""Additional job sources on synthetic payloads shaped like the providers' public responses."""

import json
from datetime import UTC, datetime, timedelta

import httpx
import pytest

from job_search_agent import source_adapters, sources
from job_search_agent.cli import seed_demo
from job_search_agent.core import Store, atomic_write, encode, init_home

BOARD = {"company_id": "example-systems", "board": "example", "market": "intl"}
AGGREGATE = {"market": "intl"}

PAYLOADS = {
    "smartrecruiters": {
        "offset": 0,
        "limit": 100,
        "totalFound": 1,
        "content": [
            {
                "id": "744000001",
                "name": "Director, Platform Product",
                "releasedDate": "2026-09-01T10:00:00.000Z",
                "location": {"city": "London", "country": "gb", "remote": False, "hybrid": True},
                "typeOfEmployment": {"label": "Full-time"},
                "experienceLevel": {"label": "Director"},
            }
        ],
    },
    "workable": {
        "name": "Example",
        "jobs": [
            {
                "title": "Head of Product",
                "shortcode": "AB12CD34",
                "employment_type": "Full-time",
                "telecommuting": True,
                "url": "https://apply.workable.com/j/AB12CD34",
                "published_on": "2026-08-30",
                "country": "Germany",
                "city": "Berlin",
                "experience": "Director",
            }
        ],
    },
    "recruitee": {
        "offers": [
            {
                "id": 1001,
                "title": "Product Director",
                "status": "published",
                "careers_url": "https://example.recruitee.com/o/product-director",
                "description": "<p>Lead the synthetic platform.</p>",
                "requirements": "<p>Fluent English is required.</p>",
                "city": "Amsterdam",
                "country": "Netherlands",
                "remote": False,
                "hybrid": True,
                "employment_type_code": "fulltime_permanent",
                "published_at": "2026-09-10 08:00:00 UTC",
                "salary": {"min": "90000", "max": "120000", "period": "year", "currency": "EUR"},
            }
        ]
    },
    "remotive": {
        "jobs": [
            {
                "id": 2001,
                "url": "https://remotive.com/remote-jobs/product/lead-2001",
                "title": "Lead Product Manager",
                "company_name": "Fictional Remote Co",
                "job_type": "full_time",
                "publication_date": "2026-09-12T09:00:00",
                "candidate_required_location": "Europe, UK",
                "salary": "$150k - $180k",
                "description": "<p>Synthetic remote product role.</p>",
            }
        ]
    },
    "remoteok": [
        {"legal": "Synthetic legal notice; link back to Remote OK."},
        {
            "id": "3001",
            "position": "VP Product",
            "company": "Fictional Remote Co",
            "location": "Worldwide",
            "salary_min": 140000,
            "salary_max": 0,
            "date": "2026-09-11T00:00:00+00:00",
            "url": "https://remoteok.com/remote-jobs/3001",
            "description": "Synthetic VP role.",
        },
    ],
    "jobicy": {
        "jobs": [
            {
                "id": 4001,
                "url": "https://jobicy.com/jobs/4001-principal-product",
                "jobTitle": "Principal Product Manager",
                "companyName": "Fictional Jobs Inc",
                "jobType": ["Full-Time"],
                "jobGeo": "USA",
                "jobLevel": "Director",
                "jobExcerpt": "Synthetic excerpt.",
                "pubDate": "2026-09-13 10:00:00",
                "annualSalaryMin": "160000",
                "annualSalaryMax": "200000",
                "salaryCurrency": "USD",
            }
        ]
    },
    "arbeitnow": {
        "data": [
            {
                "slug": "product-lead-berlin-5001",
                "company_name": "Fictional GmbH",
                "title": "Product Lead",
                "description": "<p>Synthetic Berlin role.</p>",
                "remote": True,
                "url": "https://www.arbeitnow.com/jobs/companies/fictional/product-lead-berlin-5001",
                "job_types": ["full time"],
                "location": "Berlin",
                "created_at": 1789000000,
            }
        ]
    },
    "getonbrd": {
        "data": [
            {
                "id": "product-manager-fictional-santiago",
                "attributes": {
                    "title": "Digital Product Manager",
                    "description": "<div>Synthetic description.</div>",
                    "remote_modality": "fully_remote",
                    "countries": ["Chile", "Peru"],
                    "min_salary": 2300,
                    "max_salary": 3200,
                    "published_at": 1789418306,
                    "company": {
                        "data": {"id": "fictional", "attributes": {"name": "Fictional SpA"}}
                    },
                },
                "links": {
                    "public_url": "https://www.getonbrd.com/jobs/product-manager-fictional-santiago"
                },
            }
        ],
        "meta": {"page": 1, "per_page": 100, "total_pages": 1},
    },
    "trudvsem": {
        "status": "200",
        "meta": {"total": 1, "limit": 100},
        "results": {
            "vacancies": [
                {
                    "vacancy": {
                        "id": "00000000-aaaa-bbbb-cccc-000000000001",
                        "job-name": "Директор по цифровым продуктам",
                        "company": {
                            "name": "ООО Вымышленная Компания",
                            "inn": "0000000000",
                            "email": "hr@example.invalid",
                        },
                        "region": {"name": "Москва"},
                        "salary_min": 300000,
                        "salary_max": 400000,
                        "employment": "Полная занятость",
                        "schedule": "Удалённая работа",
                        "duty": "Развитие цифровых продуктов",
                        "requirements": "Опыт управления продуктами",
                        "vac_url": "https://trudvsem.ru/vacancy/card/0000000000/00000000-aaaa-bbbb-cccc-000000000001",
                        "creation-date": "2026-09-14",
                        "contact_list": [
                            {"contact_type": "Телефон", "contact_value": "+7 000 000-00-00"}
                        ],
                    }
                }
            ]
        },
    },
}


@pytest.mark.parametrize("provider", sorted(PAYLOADS))
def test_each_adapter_normalises_identity_link_and_conditions(provider):
    source = BOARD if not source_adapters.ADAPTERS[provider].aggregate else AGGREGATE
    [job] = sources.parse_jobs(provider, json.dumps(PAYLOADS[provider]), source)
    assert job["provider"] == provider and job["title"] and job["urls"][0].startswith("https://")
    assert job["availability"] == "unknown"
    assert job["conditions"]["method"] == "conditions-v1"
    if source_adapters.ADAPTERS[provider].aggregate:
        assert job["company_name"] and job["id"].startswith(f"{provider}-")
    else:
        assert job["company_id"] == "example-systems"
    assert "contact" not in json.dumps(job, ensure_ascii=False)
    assert "hr@example.invalid" not in json.dumps(job, ensure_ascii=False)


def test_structured_conditions_keep_their_origin():
    [recruitee] = sources.parse_jobs("recruitee", json.dumps(PAYLOADS["recruitee"]), BOARD)
    assert recruitee["conditions"]["salary"] == {
        "min": 90000,
        "max": 120000,
        "currency": "EUR",
        "period": "year",
        "gross_net": "unknown",
        "raw": {"min": 90000, "max": 120000, "currency": "EUR", "period": "year"},
        "source": "recruitee.salary",
    }
    assert recruitee["conditions"]["work_mode"]["value"] == "hybrid"
    [remotive] = sources.parse_jobs("remotive", json.dumps(PAYLOADS["remotive"]), AGGREGATE)
    assert remotive["conditions"]["allowed_geography"]["countries"] == ["Europe", "UK"]
    [remoteok] = sources.parse_jobs("remoteok", json.dumps(PAYLOADS["remoteok"]), AGGREGATE)
    garbled = dict(PAYLOADS["remoteok"][1], position="Director de InvestigaciÃ³n")
    [repaired] = sources.parse_jobs("remoteok", json.dumps([garbled]), AGGREGATE)
    assert repaired["title"] == "Director de Investigación"
    assert source_adapters.repair_mojibake("Zürich Ã") == "Zürich Ã"
    assert remoteok["conditions"]["allowed_geography"]["countries"] == ["Worldwide"]
    assert (
        remoteok["conditions"]["salary"]["min"] == 140000
        and remoteok["conditions"]["salary"]["max"] is None
    )
    [jobicy] = sources.parse_jobs("jobicy", json.dumps(PAYLOADS["jobicy"]), AGGREGATE)
    assert jobicy["level"] == {"raw": "Director", "source": "jobicy"}
    assert jobicy["content_scope"] == "excerpt"
    [trudvsem] = sources.parse_jobs("trudvsem", json.dumps(PAYLOADS["trudvsem"]), {})
    assert trudvsem["market"] == "ru" and trudvsem["company_id"] == "trudvsem-inn-0000000000"
    assert trudvsem["conditions"]["salary"]["currency"] == "RUB"
    assert trudvsem["conditions"]["work_mode"]["value"] == "remote"


def test_schema_changes_and_missing_identity_are_rejected():
    for provider in ("jobicy", "trudvsem", "workable", "getonbrd"):
        with pytest.raises((TypeError, ValueError)):
            sources.parse_jobs(provider, json.dumps({"unexpected": []}), BOARD)
    broken = {"jobs": [{**PAYLOADS["jobicy"]["jobs"][0], "url": "http://insecure.example"}]}
    with pytest.raises(ValueError, match="identity"):
        sources.parse_jobs("jobicy", json.dumps(broken), AGGREGATE)


def test_endpoints_use_documented_public_routes():
    assert sources.endpoint({**BOARD, "provider": "smartrecruiters"}, 1).startswith(
        "https://api.smartrecruiters.com/v1/companies/example/postings?limit=100&offset=100"
    )
    assert (
        sources.endpoint({**BOARD, "provider": "recruitee"})
        == "https://example.recruitee.com/api/offers/"
    )
    assert sources.endpoint({"provider": "jobicy", "query": "product", "geo": "usa"}).startswith(
        "https://jobicy.com/api/v2/remote-jobs?count=50&geo=usa&tag=product"
    )
    assert sources.endpoint(
        {"provider": "trudvsem", "query": "директор", "region": "7700000000000"}, 2
    ).startswith("https://opendata.trudvsem.ru/api/v1/vacancies/region/7700000000000?text=")
    assert "offset=2&limit=100" in sources.endpoint({"provider": "trudvsem", "query": "x"}, 2)
    assert sources.endpoint(
        {"provider": "hh", "query": "product director", "area": "1"}
    ).startswith("https://api.hh.ru/vacancies?text=product%20director&per_page=100&page=0")
    with pytest.raises(ValueError, match="employer_id or query"):
        sources.endpoint({"provider": "hh"})
    assert sources.page_size("trudvsem") == 100 and sources.page_size("jobicy") is None


def test_hh_text_search_takes_employers_from_items():
    payload = {
        "items": [
            {
                "id": "9001",
                "name": "Product Director",
                "alternate_url": "https://hh.ru/vacancy/9001",
                "area": {"name": "Москва"},
                "employer": {"id": "77", "name": "Вымышленный Банк"},
                "snippet": {"requirement": "Опыт", "responsibility": "Продукт"},
                "salary": {"from": 400000, "to": None, "currency": "RUR", "gross": True},
            }
        ]
    }
    [job] = sources.parse_jobs(
        "hh", json.dumps(payload), {"query": "product director", "market": "ru"}
    )
    assert job["id"] == "hh-9001" and job["company_id"] == "hh-employer-77"
    assert job["company_name"] == "Вымышленный Банк"
    assert job["conditions"]["salary"]["gross_net"] == "gross"


@pytest.fixture
def store(tmp_path, monkeypatch):
    monkeypatch.setattr(sources.time, "sleep", lambda _seconds: None)
    with Store(init_home(tmp_path / "workspace", demo=True)) as value:
        seed_demo(value)
        yield value


def configure(store, *items):
    settings = store.settings
    settings["sources"] = list(items)
    atomic_write(store.home / "settings.json", encode(settings))


def test_discovery_reuses_a_known_employer_and_respects_provider_intervals(store):
    company = store.get("companies", "example-systems")
    payload = {"jobs": [{**PAYLOADS["jobicy"]["jobs"][0], "companyName": company["name"]}]}
    configure(
        store,
        {
            "id": "jobicy-product",
            "provider": "jobicy",
            "query": "product",
            "market": "intl",
            "interval_seconds": 60,
        },
    )
    with httpx.Client(
        transport=httpx.MockTransport(lambda request: httpx.Response(200, json=payload))
    ) as client:
        [health] = sources.discover(store, client=client)
    assert health["status"] == "success_nonempty"
    vacancy = store.get("vacancies", "jobicy-4001")
    assert vacancy["company_id"] == "example-systems"
    assert store.get("companies", "jobicy-product") is None
    next_attempt = datetime.fromisoformat(health["next_attempt"])
    assert next_attempt - datetime.now(UTC) > timedelta(minutes=55)


def test_blocked_board_is_recorded_without_retrying_another_route(store):
    configure(
        store, {"id": "remotive", "provider": "remotive", "category": "product", "market": "intl"}
    )
    calls = []

    def blocked(request):
        calls.append(str(request.url))
        return httpx.Response(403, text="<title>Just a moment...</title>")

    with httpx.Client(transport=httpx.MockTransport(blocked)) as client:
        [health] = sources.discover(store, client=client)
    assert health["status"] == "blocked" and len(calls) == 1
    assert calls[0].startswith("https://remotive.com/api/remote-jobs?category=product")
    next_attempt = datetime.fromisoformat(health["next_attempt"])
    assert next_attempt - datetime.now(UTC) > timedelta(hours=5)


def test_paginated_open_data_stops_on_a_short_page(store):
    first = {
        **PAYLOADS["trudvsem"],
        "results": {"vacancies": PAYLOADS["trudvsem"]["results"]["vacancies"] * 1},
    }
    configure(
        store,
        {
            "id": "trudvsem",
            "provider": "trudvsem",
            "query": "директор",
            "market": "ru",
            "max_pages": 3,
        },
    )
    calls = []

    def respond(request):
        calls.append(str(request.url))
        return httpx.Response(200, json=first)

    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        sources.discover(store, client=client)
    assert len(calls) == 1
    assert store.get("vacancies", "trudvsem-00000000-aaaa-bbbb-cccc-000000000001")["market"] == "ru"


SECRET_PROXY = "http://user:" + "synthetic-secret" + "@proxy.invalid:8080"


def fallback_source(**updates):
    return {
        "id": "jobicy-fallback",
        "provider": "jobicy",
        "query": "product",
        "market": "intl",
        "proxy_env": "CC_SYNTHETIC_PROXY",
        "proxy_allowed": True,
        "proxy_mode": "fallback",
        **updates,
    }


def test_proxy_fallback_only_retries_failed_connections(store, monkeypatch):
    monkeypatch.setenv("CC_SYNTHETIC_PROXY", SECRET_PROXY)
    used = []

    def reserve(proxy):
        used.append(proxy)
        return httpx.Client(
            transport=httpx.MockTransport(
                lambda request: httpx.Response(200, json=PAYLOADS["jobicy"])
            )
        )

    monkeypatch.setattr(sources, "proxy_client", reserve)
    configure(store, fallback_source())

    def unreachable(request):
        raise httpx.ConnectTimeout("synthetic timeout", request=request)

    with httpx.Client(transport=httpx.MockTransport(unreachable)) as client:
        [health] = sources.discover(store, client=client)
    assert health["status"] == "success_nonempty" and health["route"] == "proxy_fallback"
    assert used == [SECRET_PROXY]
    journal = json.dumps(
        [store.all(kind) for kind in ("source_health", "events", "collection_runs")]
    )
    assert "synthetic-secret" not in journal


def test_proxy_fallback_never_retries_http_refusals(store, monkeypatch):
    monkeypatch.setenv("CC_SYNTHETIC_PROXY", SECRET_PROXY)
    monkeypatch.setattr(
        sources, "proxy_client", lambda proxy: pytest.fail("a refusal must not use the proxy")
    )
    configure(store, fallback_source())
    with httpx.Client(
        transport=httpx.MockTransport(lambda request: httpx.Response(403, text="challenge"))
    ) as client:
        [health] = sources.discover(store, client=client)
    assert health["status"] == "blocked" and health["route"] == "direct"


def test_proxy_modes_need_permission_and_a_known_mode(store, monkeypatch):
    monkeypatch.setenv("CC_SYNTHETIC_PROXY", SECRET_PROXY)
    for updates, message in (
        ({"proxy_allowed": False}, "permission"),
        ({"proxy_mode": "evade"}, "proxy_mode"),
    ):
        configure(store, fallback_source(**updates))
        with httpx.Client(
            transport=httpx.MockTransport(lambda request: pytest.fail("no request"))
        ) as client:
            [health] = sources.discover(store, client=client, source_id="jobicy-fallback")
        assert health["status"] == "config_error" and message in health["config_error"]
        store.db.execute("DELETE FROM records WHERE kind='source_health'")
