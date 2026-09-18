"""Profile relevance on synthetic vacancies: tiers, reasons, queries and collection."""

import json

import httpx
import pytest

from job_search_agent import activity, relevance, sources
from job_search_agent.cli import parser, run, seed_demo
from job_search_agent.core import Store, atomic_write, encode, init_home

SETTINGS = {
    "policy": {
        "tracks": ["product", "technical-leadership"],
        "interests": ["AI/GenAI agents", "payments", "enterprise platforms"],
        "exclude": ["gambling"],
        "russia_director_only": True,
        "bigtech_company_ids": ["example-bigtech"],
    }
}
FACTS = {
    "facts": [
        {"id": "f1", "tags": ["ai", "platforms"], "verification": "verified"},
        {"id": "f2", "tags": ["payments"], "verification": "self_reported"},
        {"id": "f3", "tags": ["industrial"], "verification": "conflicting"},
    ]
}
LONG = " Responsibilities include roadmap, discovery, stakeholder work and delivery." * 4


def screen(title, text="", settings=SETTINGS, **vacancy):
    resolved = relevance.profile(settings, FACTS)
    return relevance.screen({"title": title, "text": text, **vacancy}, resolved)


def test_titles_outside_the_profile_are_off_profile_with_the_deciding_words():
    office = screen("Руководитель офиса", market="ru")
    assert office["tier"] == "off_profile"
    assert office["reasons"][0] == {"code": "excluded_function", "terms": ["офис"]}
    sales = screen("VP of Sales, AI Platform")
    assert sales["tier"] == "off_profile" and sales["reasons"][0]["terms"] == ["sales"]
    assert screen("Директор магазина", market="ru")["reasons"][0]["code"] == "no_track_function"
    gambling = screen("Head of Product", "A gambling operator." + LONG)
    assert gambling["reasons"][0] == {"code": "policy_exclusion", "terms": ["gambling"]}


def test_target_level_and_candidate_domains_make_a_strong_match():
    result = screen("Director of Product, Agentic AI", "Payments platform for banks." + LONG)
    assert result["tier"] == "strong" and result["relevant"]
    # "AI" in a title is also a technical-leadership function, so both tracks are named.
    assert result["tracks"] == ["product", "technical-leadership"] and result["level"] == "top"
    assert [item["id"] for item in result["domains"]] == ["ai", "payments", "platforms"]
    assert result["domains"][0]["in_title"] == ["ai", "agent", "agentic"]
    assert result["score"] > screen("Head of Product")["score"]


def test_levels_below_the_target_and_individual_contributors_are_weak():
    assert screen("Senior Product Manager, AI", LONG)["tier"] == "weak"
    engineer = screen("Staff AI Engineer", "LLM agents." + LONG)
    assert engineer["tier"] == "weak" and engineer["level"] == "below"
    assert screen("Director of Engineering, AI Platform")["tier"] == "strong"
    project = screen("Руководитель проектов по развитию ИИ", market="intl")
    assert project["level"] == "below"


def test_big_tech_levels_are_mapped_per_employer_not_by_title_words():
    result = screen("Senior Product Manager, AI Agents", LONG, company_id="example-bigtech")
    assert result["level"] == "company_specific" and result["relevant"]
    assert screen("Senior Product Manager, AI Agents", LONG)["tier"] == "weak"


def test_russian_roles_follow_the_director_only_policy():
    # "Руководитель разработки" heads the whole function: head level, not a team lead.
    head = screen(
        "Руководитель разработки AI, ML", "Платформа машинного обучения." + LONG, market="ru"
    )
    assert head["level"] == "top" and head["tier"] == "strong"
    lead = screen(
        "Руководитель группы разработки ИИ", "Платформа машинного обучения." + LONG, market="ru"
    )
    assert lead["tier"] == "weak" and lead["score"] <= relevance.BELOW_TARGET_CAP
    assert lead["reasons"][1]["code"] == "level_below_market_rule"
    director = screen("Директор по искусственному интеллекту", market="ru")
    assert director["tier"] == "strong"


def test_a_banking_product_is_not_product_management():
    pricing = screen("Исполнительный директор по ценообразованию продуктов банка", market="ru")
    assert pricing["tier"] == "off_profile"
    assert screen("Head of Lending Products")["tier"] == "off_profile"
    assert screen("Директор по продукту (кредитные продукты)", market="ru")["tracks"] == ["product"]


def test_the_thermometer_adds_four_parts_and_hard_rules_cap_it():
    result = screen("Director of Product, Agentic AI", "Payments platform for banks." + LONG)
    assert sum(result["parts"].values()) == result["score"] and result["method"] == "rules"
    assert result["parts"]["role"] == 30 and result["parts"]["level"] == 25
    assert 0 < result["parts"]["evidence"] <= 20
    backed = next(reason for reason in result["reasons"] if reason["code"] == "cv_support")
    assert {"id": "ai", "facts": 1} in backed["domains"]
    office = screen("Office manager")
    assert office["score"] <= relevance.OFF_PROFILE_CAP
    assert screen("Senior Product Manager, AI", LONG)["score"] <= relevance.BELOW_TARGET_CAP


def test_missing_text_is_not_treated_as_a_missing_domain():
    no_text = screen("Head of Product")
    assert no_text["tier"] == "possible" and no_text["text_checked"] is False
    assert {"code": "no_text", "terms": []} in no_text["reasons"]
    full_text = screen("Head of Product", "Consumer grocery delivery." + LONG)
    assert full_text["tier"] == "weak"
    assert {"code": "no_domain_overlap", "terms": []} in full_text["reasons"]


def test_domain_in_a_leadership_title_rescues_a_title_without_a_track_word():
    result = screen("Head of Payments Operations")
    assert result["tier"] == "possible"
    assert result["reasons"][0]["code"] == "domain_title_only"


def test_domains_come_from_fact_tags_and_interests_but_not_conflicting_facts():
    resolved = relevance.profile(SETTINGS, FACTS)
    assert set(resolved["domains"]) == {"ai", "payments", "platforms"}
    explicit = relevance.profile({**SETTINGS, "relevance": {"domains": ["industrial"]}}, FACTS)
    assert list(explicit["domains"]) == ["industrial"]


def test_query_grammar_with_title_scope_and_exclusions():
    parsed = relevance.parse_query("title:(engineer | инженер) + (ai | ии) - crypto")
    assert parsed == {
        "all_of": [
            {"field": "title", "terms": ["engineer", "инженер"]},
            {"field": "any", "terms": ["ai", "ии"]},
        ],
        "none_of": [{"field": "any", "terms": ["crypto"]}],
    }
    norm = relevance.norm

    def fields(title, text=""):
        return {"title": norm(title), "text": norm(text)}

    hit = relevance.match_query(parsed, fields("Staff AI Engineer", "LLM work"))
    assert hit == {"matched": True, "terms": ["engineer", "ai"], "excluded_by": []}
    text_only = relevance.match_query(parsed, fields("Head of Product", "engineer and AI"))
    assert text_only["matched"] is False
    blocked = relevance.match_query(parsed, fields("AI Engineer", "crypto exchange"))
    assert blocked["matched"] is False and blocked["excluded_by"] == ["crypto"]
    # Short terms are whole words; longer ones allow endings.
    assert relevance.found(norm("aid for airlines"), ["ai"]) == []
    assert relevance.found(norm("инженера платежей"), ["инженер", "платеж"]) == [
        "инженер",
        "платеж",
    ]
    for broken in ("", "   ", "-crypto", "x" * 301):
        with pytest.raises(ValueError):
            relevance.parse_query(broken)


def test_include_queries_replace_the_function_check_but_never_the_level():
    settings = {
        **SETTINGS,
        "relevance": {"queries": [{"name": "Robotics", "query": "robot", "include": True}]},
    }
    head = screen("Head of Robotics", settings=settings)
    # A query match without CV support is a lead worth reading, not a strong match.
    assert head["tier"] == "possible" and head["parts"]["role"] == 24
    assert any(reason["code"] == "query_included" for reason in head["reasons"])
    junior = screen("Robotics Specialist", settings=settings)
    assert junior["tier"] == "weak"
    plain = screen("Head of Robotics")
    assert plain["tier"] == "off_profile"


def test_queries_look_in_company_title_location_and_text_fields():
    vacancy = {
        "title": "Head of AI Platform",
        "text": "Kubernetes and LLM serving." + LONG,
        "location": "Berlin, Germany",
        "company_name": "Fictional Bank",
        "conditions": {"work_mode": {"value": "hybrid"}, "allowed_geography": {"countries": []}},
    }
    fields = relevance.search_fields(vacancy, company="Fictional Bank FB Group")

    def matches(query):
        return relevance.match_query(relevance.parse_query(query), fields)["matched"]

    assert matches("company:(fictional bank) + title:head + location:(berlin | remote) + llm")
    assert matches("компания:fb + должность:(head | директор) + где:hybrid + стек:kubernetes")
    assert not matches("company:sber + ai")
    assert not matches("location:remote + ai")
    assert not matches("text:(head of ai)")
    # A plain group looks everywhere, including company and location.
    assert matches("germany + fictional")
    # A word that is not a known field keeps its colon as text.
    assert relevance.parse_query("c++: + ai")["all_of"][0]["field"] == "any"


def test_invalid_settings_are_reported_not_guessed():
    for config, message in (
        ([], "must be an object"),
        ({"levels": {"middle": []}}, "levels accepts"),
        ({"target_level": "senior"}, "target_level"),
        ({"queries": [{"query": ""}]}, "non-empty string"),
        ({"exclude_title": "sales"}, "must be a list"),
        ({"ignore_in_title": ["(unclosed"]}, "invalid pattern"),
    ):
        with pytest.raises(ValueError, match=message):
            relevance.validate(config)
        assert relevance.problem({"relevance": config})


@pytest.fixture
def store(tmp_path, monkeypatch):
    monkeypatch.setattr(sources.time, "sleep", lambda _seconds: None)
    with Store(init_home(tmp_path / "workspace", demo=True)) as value:
        seed_demo(value)
        yield value


def jobicy_payload(*titles):
    return {
        "jobs": [
            {
                "id": 5000 + index,
                "url": f"https://jobicy.com/jobs/{5000 + index}-role",
                "jobTitle": title,
                "companyName": f"Fictional Employer {index}",
                "jobGeo": "Anywhere",
                "jobDescription": "Synthetic description of an AI platform role." + LONG,
                "pubDate": "2026-09-15 10:00:00",
            }
            for index, title in enumerate(titles)
        ]
    }


def test_collection_counts_tiers_and_can_skip_off_profile_cards(store):
    settings = store.settings
    settings["sources"] = [
        {"id": "jobicy-all", "provider": "jobicy", "query": "director", "market": "intl"},
        {
            "id": "jobicy-screened",
            "provider": "jobicy",
            "query": "head",
            "market": "intl",
            "skip_off_profile": True,
        },
    ]
    atomic_write(store.home / "settings.json", encode(settings))
    payload = jobicy_payload("Director of Product, AI Platform", "Office Manager")
    with httpx.Client(
        transport=httpx.MockTransport(lambda request: httpx.Response(200, json=payload))
    ) as client:
        stored, screened = sources.discover(store, client=client)
    assert stored["count"] == 2 and "screened_out" not in stored
    assert screened["count"] == 1 and screened["screened_out"] == 1
    [run] = store.all("collection_runs")
    assert run["relevance"] == {"strong": 1, "off_profile": 1}
    assert run["screened_out"] == 1


def test_cli_lists_explains_and_searches(store):
    store.put(
        "vacancies",
        {
            "id": "synthetic-director",
            "title": "Director of Product, Agentic AI",
            "company_id": "example-systems",
            "text": "Payments platform." + LONG,
            "urls": ["https://example.invalid/director"],
        },
    )
    store.put(
        "vacancies",
        {
            "id": "synthetic-office",
            "title": "Office manager",
            "company_id": "example-systems",
            "urls": ["https://example.invalid/office"],
        },
    )
    home = str(store.home)

    def cli(*args):
        return json.loads(encode(run(parser().parse_args(["--home", home, "relevance", *args]))))

    relevant = cli("list", "--relevant")
    assert "synthetic-director" in [row["id"] for row in relevant]
    assert "synthetic-office" not in [row["id"] for row in relevant]
    explained = cli("explain", "synthetic-office")
    assert explained["tier"] == "off_profile" and "excluded function" in explained["summary"]
    found = cli("search", "title:product + (ai | agentic)")
    assert [row["id"] for row in found if row["id"].startswith("synthetic")] == [
        "synthetic-director"
    ]
    assert found[0]["query_terms"] == ["product", "ai"]


def run_review(store, tmp_path, reviews, model="claude-opus-5"):
    request, result = tmp_path / "request.json", tmp_path / "result.json"
    atomic_write(
        request,
        encode(
            {
                "schema_version": 1,
                "skill": "career-job-search",
                "operation": "Semantic relevance review",
                "actor": {"environment": "claude", "model": model, "session": "synthetic"},
                "expected_result": {"types": ["relevance_review"]},
            }
        ),
    )
    started = activity.start(store, request)
    atomic_write(
        result,
        encode(
            {
                "schema_version": 1,
                "status": "completed",
                "next_action": "Read the strong matches",
                "records": [{"type": "relevance_review", "data": {"reviews": reviews}}],
            }
        ),
    )
    return activity.finish(store, started["id"], result)


def review(vacancy_id, verdict="strong", score=82):
    return {
        "vacancy_id": vacancy_id,
        "verdict": verdict,
        "score": score,
        "track": "technical-leadership",
        "summary": "Heads ML development: the candidate's platform and AI delivery match.",
        "reasons": [
            {"kind": "fit", "text": "Leads an engineering function"},
            {"kind": "gap", "text": "Hands-on ML research is not in the CV"},
        ],
    }


def test_a_semantic_review_decides_until_the_vacancy_or_facts_change(store, tmp_path):
    store.put(
        "vacancies",
        {
            "id": "synthetic-ml-lead",
            "title": "Руководитель группы разработки ML",
            "company_id": "example-systems",
            "market": "ru",
            "text": "Команда машинного обучения." + LONG,
            "urls": ["https://example.invalid/ml"],
        },
    )
    home = str(store.home)

    def cli(*args):
        return json.loads(encode(run(parser().parse_args(["--home", home, "relevance", *args]))))

    before = cli("explain", "synthetic-ml-lead")
    assert before["method"] == "rules" and before["tier"] == "weak"
    assert "synthetic-ml-lead" in [row["id"] for row in cli("pending", "--limit", "50")]
    run_review(store, tmp_path, [review("synthetic-ml-lead")])
    after = cli("explain", "synthetic-ml-lead")
    assert after["method"] == "agent" and after["tier"] == "strong" and after["score"] == 82
    assert after["rules"] == {"tier": "weak", "score": before["score"]}
    assert after["review"]["stale"] is False and after["review"]["model"] == "claude-opus-5"
    assert "synthetic-ml-lead" not in [row["id"] for row in cli("pending", "--limit", "50")]
    vacancy = store.get("vacancies", "synthetic-ml-lead")
    store.put("vacancies", {**vacancy, "text": "Новый текст вакансии." + LONG})
    changed = cli("explain", "synthetic-ml-lead")
    assert changed["method"] == "rules" and changed["review"]["stale"] is True


def test_semantic_reviews_are_validated(store, tmp_path):
    vacancy_id = store.all("vacancies")[0]["id"]
    for broken, message in (
        ([review("missing-vacancy")], "stored vacancy"),
        ([review(vacancy_id, "strong", 55)], "outside the strong band"),
        ([review(vacancy_id, "off_profile", 30)], "outside the off_profile band"),
        ([{**review(vacancy_id), "reasons": []}], "1–6 reasons"),
        ([{**review(vacancy_id), "track": "sales"}], "track"),
        ([review(vacancy_id), review(vacancy_id)], "reviewed twice"),
        ([{**review(vacancy_id), "fact_ids": ["no-such-fact"]}], "existing facts"),
    ):
        with pytest.raises(ValueError, match=message):
            run_review(store, tmp_path, broken)
    with pytest.raises(ValueError, match="flagship"):
        run_review(store, tmp_path, [review(vacancy_id)], model="small-model")
