"""Synthetic channel exports: identity, evidence preservation and bounded collection."""

import asyncio
import json
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from job_search_agent import sources, telegram, telegram_export
from job_search_agent.core import Store, init_home


@pytest.fixture
def store(tmp_path):
    with Store(init_home(tmp_path / "private", demo=True)) as value:
        yield value


def payload(messages, channel="1001"):
    return json.dumps(
        {
            "schema_version": 1,
            "channel": {"id": channel, "username": "fictional_jobs", "title": "Example board"},
            "messages": messages,
        }
    ).encode()


def message(number=1, **extra):
    return {
        "id": number,
        "date": "2026-01-01T12:00:00+00:00",
        "edit_date": None,
        "text": "Title: Platform Engineer\nCompany: Fictional Example Labs\nBuild useful systems.",
        **extra,
    }


def test_replay_and_edit_preserve_raw_evidence(store):
    raw = payload([message()])
    first = telegram.import_export(store, raw)
    vacancy_id = first["new"][0]
    before = store.get("vacancies", vacancy_id)
    assert before["availability"] == "unknown"
    assert before["telegram"]["text"] == message()["text"]
    assert telegram.import_export(store, raw)["replayed"]
    assert store.get("vacancies", vacancy_id) == before
    edited = message(text=message()["text"] + " Remote.", edit_date="2026-01-02T12:00:00+00:00")
    assert telegram.import_export(store, payload([edited]))["changed"] == [vacancy_id]
    # Different bytes containing an older post must not roll an edit back.
    assert telegram.import_export(store, raw + b" ")["unchanged"] == [vacancy_id]
    assert store.get("vacancies", vacancy_id)["text"].endswith("Remote.")
    assert len(store.all("vacancies")) == 1
    assert len(store.all("observations")) == 3


def test_outbound_homepages_do_not_merge_posts_and_channel_is_not_employer(store):
    item = message(
        text="Title: Platform Engineer\nBuild systems.", outbound_links=["https://example.org/"]
    )
    result = telegram.import_export(store, payload([item, {**item, "id": 2}]))
    assert len(result["new"]) == 2
    assert len(store.all("companies")) == 2
    assert all(c["name"] == "Unknown employer" for c in store.all("companies"))
    assert all("https://example.org" not in v["urls"] for v in store.all("vacancies"))


def test_reviewed_exact_job_link_merges_reposts_but_not_different_employers(store):
    link = "https://example.org/jobs/platform?utm_source=telegram"
    first = telegram.import_export(store, payload([message(job_url=link)]))
    second = telegram.import_export(store, payload([message(2, job_url=link)]))
    assert not second["new"]
    assert len(store.all("vacancies")) == 1
    assert len(store.all("telegram_posts")) == 2
    other = message(3, job_url=link, company_name="Other Fictional Labs")
    assert len(telegram.import_export(store, payload([other]))["new"]) == 1
    assert store.get("vacancies", first["new"][0])["availability"] == "unknown"


def test_duplicate_message_dedup_and_nonjobs_remain_in_snapshot(store):
    item = message()
    result = telegram.import_export(
        store, payload([item, item, message(2, text="Weekly news roundup")])
    )
    assert result["observed_total"] == 2
    assert len(result["skipped"]) == 1
    assert result["skipped"][0]["reason"] == "title_unresolved"
    assert len(store.all("vacancies")) == 1


@pytest.mark.parametrize(
    "items",
    [
        [message(date="yesterday")],
        [message(), message(text="conflict")],
        [message(job_url="https://example.org")],
    ],
)
def test_invalid_export_does_not_mutate_journal(store, items):
    with pytest.raises(ValueError):
        telegram.import_export(store, payload(items))
    assert not store.all("vacancies")
    assert not store.all("companies")


def test_collector_respects_limit_and_date_without_write_calls():
    date = datetime(2026, 1, 2, tzinfo=UTC)

    class ReadOnlyClient:
        async def get_entity(self, channel):
            return SimpleNamespace(
                id=1001, username="fictional_jobs", title="Example", broadcast=True
            )

        async def iter_messages(self, entity, limit):
            assert limit == 2
            for number, at in [(2, date), (1, datetime(2026, 1, 1, tzinfo=UTC))]:
                yield SimpleNamespace(
                    id=number,
                    date=at,
                    edit_date=None,
                    message="Engineer",
                    entities=[SimpleNamespace(url="https://example.org/jobs/1")],
                )

    result = asyncio.run(telegram_export.collect(ReadOnlyClient(), "fictional_jobs", 2, date))
    assert len(result["messages"]) == 1
    assert result["coverage"]["reached_since"]
    assert result["messages"][0]["outbound_links"] == ["https://example.org/jobs/1"]


def test_advice_is_skipped_and_explicit_review_exclusion_wins(store):
    result = telegram.import_export(
        store,
        payload(
            [
                message(1, text="Engineer career advice\nTake our course today."),
                message(2, title="Platform Engineer", skip_reason="course_advertisement"),
                message(3, text="CTO\nКомпания: Fictional Example Labs\nBuild platforms."),
            ]
        ),
    )
    assert len(result["new"]) == 1
    assert {item["reason"] for item in result["skipped"]} == {
        "title_unresolved",
        "course_advertisement",
    }
    assert store.get("collection_runs", result["collection_run_id"])["unchanged"] == 0
    assert store.get("source_health", result["source_id"])["status"] == "imported"


def test_generic_careers_link_is_not_job_identity(store):
    with pytest.raises(ValueError):
        telegram.import_export(store, payload([message(job_url="https://example.org/careers/")]))


@pytest.mark.parametrize("reviewed_employer", [None, ""])
def test_reviewed_unknown_employer_does_not_reextract_rejected_label(store, reviewed_employer):
    item = message(
        company_name=reviewed_employer,
        text="Title: Platform Engineer\nCompany: Generic unnamed business\nBuild systems.",
    )
    result = telegram.import_export(store, payload([item]))
    vacancy = store.get("vacancies", result["new"][0])
    assert store.get("companies", vacancy["company_id"])["name"] == "Unknown employer"
    assert vacancy["telegram"]["company_name"] == ""
    assert "Generic unnamed business" in vacancy["telegram"]["text"]


def test_channel_excerpt_preserves_official_card_fields(store):
    from job_search_agent import intake

    company, _ = intake.ensure_company(store, "Fictional Example Labs")
    official = {
        "id": "ats-example-1",
        "company_id": company["id"],
        "provider": "example_ats",
        "external_id": "123",
        "title": "Principal Platform Engineer",
        "market": "intl",
        "location": "Fictional City",
        "content_scope": "full",
        "text": "The complete official description.",
        "availability": "active",
        "urls": ["https://example.org/jobs/platform"],
        "requirements": [],
        "conditions": {"published_on": "2025-12-20"},
    }
    store.put("vacancies", official)
    result = telegram.import_export(store, payload([message(job_url=official["urls"][0])]))
    assert not result["new"]
    merged = store.get("vacancies", official["id"])
    for field in ("title", "market", "location", "provider", "external_id", "text", "availability"):
        assert merged[field] == official[field]
    assert merged["conditions"]["published_on"] == "2025-12-20"
    assert merged["telegram"]["text"] == message()["text"]


def configure_channel(store, **extra):
    settings = store.settings
    settings["sources"] = [
        {
            "id": "telegram-1001",
            "provider": "telegram",
            "board": "fictional_jobs",
            "name": "Example board",
            "collection_mode": "external_export",
            "enabled": True,
            **extra,
        }
    ]
    (store.home / "settings.json").write_text(json.dumps(settings))


def test_registered_channel_discover_never_requests_http_or_creates_employer(store):
    configure_channel(store)

    class NoHTTP:
        def get(self, *args, **kwargs):
            pytest.fail("Telegram discover must not request HTTP")

    result = sources.discover(store, client=NoHTTP())
    assert result[0]["status"] == "external_export_required"
    assert not store.all("companies")
    assert not store.all("vacancies")
    configure_channel(store, enabled=False, disabled_reason="User paused collection")
    assert sources.discover(store, client=NoHTTP()) == []
    with pytest.raises(ValueError, match="disabled"):
        sources.discover(store, source_id="telegram-1001", client=NoHTTP())


def test_discover_preserves_export_import_times_and_coverage(store):
    configure_channel(store)
    data = json.loads(payload([message()]))
    data.update(exported_at="2026-01-03T12:00:00+00:00", coverage={"complete": False, "limit": 1})
    imported = telegram.import_export(store, json.dumps(data).encode())
    health = sources.discover(store)[0]
    assert health["status"] == "external_export_required"
    for field in ("exported_at", "imported_at", "coverage"):
        assert health[field] == imported[field]
    assert health["count"] == 1
    assert "last_success" not in health


def test_invalid_channel_registration_is_explicit_configuration_error(store):
    configure_channel(store, collection_mode="http")
    assert sources.discover(store)[0]["status"] == "config_error"
    assert not store.all("companies")
