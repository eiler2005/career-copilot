"""Additional read-only job sources: public ATS boards, remote-job boards and open data.

Every adapter reads a documented public endpoint, never logs in, never bypasses a
challenge page and keeps the provider's terms visible in `NOTICES`. A normalised card
records the original link, the provider and conditions with their origin; unknown
values stay unknown.

| Provider          | Kind                      | Endpoint (documented)                                            |
| ----------------- | ------------------------- | ---------------------------------------------------------------- |
| smartrecruiters   | ATS board per company     | api.smartrecruiters.com/v1/companies/{board}/postings            |
| workable          | ATS board per company     | apply.workable.com/api/v1/widget/accounts/{board}                |
| recruitee         | ATS board per company     | {board}.recruitee.com/api/offers/                                |
| remotive          | remote-job board          | remotive.com/api/remote-jobs                                     |
| remoteok          | remote-job board          | remoteok.com/api                                                 |
| jobicy            | remote-job board          | jobicy.com/api/v2/remote-jobs                                    |
| arbeitnow         | job board (Europe)        | www.arbeitnow.com/api/job-board-api                              |
| getonbrd          | job board (Latin America) | www.getonbrd.com/api/v0/search/jobs                              |
| trudvsem          | Russian open data         | opendata.trudvsem.ru/api/v1/vacancies                            |
"""

from __future__ import annotations

import html
import re
import unicodedata
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from urllib.parse import quote, urlencode

from . import vacancy_fields as fields
from .core import canonical_url, digest, safe_id

NOTICES = {
    "remotive": "Remotive asks API users to link back to the job URL and credit Remotive; keep requests to a few per day.",
    "remoteok": "Remote OK requires a link back to the original job URL and a mention of Remote OK as the source.",
    "jobicy": "Jobicy asks to credit Jobicy with a link and to send applicants to the original job URL.",
    "arbeitnow": "Arbeitnow data comes from employers' applicant tracking systems; link to the original job URL.",
    "getonbrd": "Get on Board public search API; link to the public job page.",
    "trudvsem": "Open data of the Russian federal job portal (Работа России); employer contact fields are not copied into cards.",
}


def plain(text: object) -> str:
    value = html.unescape(html.unescape(str(text or "")))
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", value)).strip()


def company_id(provider: str, name: str) -> str:
    identity = re.sub(r"\s+", " ", unicodedata.normalize("NFKC", name).strip())
    ascii_name = unicodedata.normalize("NFKD", identity).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_name.lower()).strip("-")[:48] or "company"
    return safe_id(f"{provider}-{slug}-{digest(identity.casefold())[:12]}")


def _date(value: object) -> str | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool) and value > 10**9:
        seconds = value / 1000 if value > 10**11 else value
        return datetime.fromtimestamp(seconds, UTC).date().isoformat()
    if isinstance(value, str) and re.match(r"\d{4}-\d{2}-\d{2}", value.strip()):
        return value.strip()[:10]
    return None


def _number(value: object) -> float | int | None:
    if isinstance(value, bool) or value in (None, "", 0, "0"):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return int(number) if number.is_integer() else number


def salary(low: object, high: object, currency: object, period: str, source: str) -> dict | None:
    low, high = _number(low), _number(high)
    if low is None and high is None or not isinstance(currency, str) or not currency.strip():
        return None
    return {
        "min": low,
        "max": high,
        "currency": currency.strip().upper(),
        "period": period,
        "gross_net": "unknown",
        "raw": {"min": low, "max": high, "currency": currency, "period": period},
        "source": source,
    }


def geography(value: object, source: str) -> dict:
    items = value if isinstance(value, list) else re.split(r"[,;/|]", str(value or ""))
    names = []
    for item in items:
        name = plain(item)
        if not name:
            continue
        if name.casefold() in {
            "anywhere",
            "worldwide",
            "global",
            "remote",
            "anywhere in the world",
        }:
            name = "Worldwide"
        if name not in names:
            names.append(name)
    if not names:
        return {"status": "unknown", "countries": [], "basis": None, "source": None}
    return {
        "status": "listed",
        "countries": names,
        "basis": ", ".join(names)[:200],
        "source": source,
    }


def conditions(
    text: str,
    location: str,
    source: str,
    *,
    salary_value: dict | None = None,
    work_mode: str | None = None,
    employment: object = None,
    allowed: dict | None = None,
    published: object = None,
    level: str | None = None,
) -> dict:
    result = fields.from_posting(text, None, location, source)
    if salary_value:
        result["salary"] = salary_value
    if work_mode and work_mode != "unknown":
        result["work_mode"] = fields.field(work_mode, source, work_mode)
    if employment:
        value = fields._employment(employment)
        if value != "unknown":
            result["employment"] = fields.field(
                value,
                source,
                employment if isinstance(employment, str) else ", ".join(map(str, employment)),
            )
    if allowed and allowed.get("status") != "unknown":
        result["allowed_geography"] = allowed
    date = _date(published)
    if date:
        result["published_on"] = date
    if level:
        result["level_label"] = {"value": level, "source": source}
    return result


def card(
    provider: str,
    source: dict,
    *,
    external: object,
    title: object,
    url: object,
    text: str = "",
    location: object = "unknown",
    company_name: str | None = None,
    scope: str = "full",
    conditions_value: dict | None = None,
) -> dict:
    external = str(external or "").strip()
    title = plain(title)
    link = str(url or "").strip()
    if not external or not title or not link.startswith("https://"):
        raise ValueError(f"{provider} job is missing identity fields")
    aggregate = company_name is not None
    if aggregate and not company_name.strip():
        raise ValueError(f"{provider} job is missing the employer name")
    value = {
        "id": f"{provider}-{safe_id(external)}"
        if aggregate
        else f"{provider}-{safe_id(source['company_id'])}-{safe_id(external)}",
        "company_id": company_id(provider, company_name) if aggregate else source["company_id"],
        "external_id": external,
        "provider": provider,
        "title": title,
        "location": plain(location) or "unknown",
        "market": source.get("market", "unknown"),
        "urls": [canonical_url(link)],
        "text": text,
        "requirements": [],
        "availability": "unknown",
        "content_scope": scope,
        "conditions": conditions_value
        or fields.from_posting(text, None, plain(location), provider),
    }
    label = value["conditions"].pop("level_label", None)
    if label:
        value["level"] = {"raw": label["value"], "source": label["source"]}
    if aggregate:
        value["company_name"] = company_name.strip()
    return value


def _list(data: object, *path: str) -> list:
    for key in path:
        if not isinstance(data, dict):
            raise TypeError("Unexpected response schema")
        data = data.get(key)
    if not isinstance(data, list):
        raise TypeError("Unexpected response schema")
    return data


# --------------------------------------------------------------------------- ATS boards


def smartrecruiters(data: object, source: dict) -> list[dict]:
    board = source["board"]
    result = []
    for item in _list(data, "content"):
        location = item.get("location") or {}
        place = ", ".join(part for part in (location.get("city"), location.get("country")) if part)
        mode = (
            "remote"
            if location.get("remote")
            else "hybrid"
            if location.get("hybrid")
            else "unknown"
        )
        result.append(
            card(
                "smartrecruiters",
                source,
                external=item.get("id"),
                title=item.get("name"),
                url=f"https://jobs.smartrecruiters.com/{quote(board, safe='')}/{quote(str(item.get('id') or ''), safe='')}",
                location=place or "unknown",
                scope="card",
                conditions_value=conditions(
                    "",
                    place,
                    "smartrecruiters",
                    work_mode=mode,
                    employment=(item.get("typeOfEmployment") or {}).get("label"),
                    published=item.get("releasedDate"),
                    level=(item.get("experienceLevel") or {}).get("label"),
                ),
            )
        )
    return result


def workable(data: object, source: dict) -> list[dict]:
    result = []
    for item in _list(data, "jobs"):
        place = ", ".join(
            part for part in (item.get("city"), item.get("state"), item.get("country")) if part
        )
        result.append(
            card(
                "workable",
                source,
                external=item.get("shortcode"),
                title=item.get("title"),
                url=item.get("url") or item.get("shortlink"),
                location=place or "unknown",
                scope="card",
                conditions_value=conditions(
                    "",
                    place,
                    "workable",
                    work_mode="remote" if item.get("telecommuting") else None,
                    employment=item.get("employment_type"),
                    published=item.get("published_on") or item.get("created_at"),
                    level=item.get("experience"),
                ),
            )
        )
    return result


def recruitee(data: object, source: dict) -> list[dict]:
    result = []
    for item in _list(data, "offers"):
        if item.get("status") not in (None, "published"):
            continue
        text = plain(f"{item.get('description') or ''} {item.get('requirements') or ''}")
        place = ", ".join(part for part in (item.get("city"), item.get("country")) if part)
        pay = item.get("salary") or {}
        period = {
            "year": "year",
            "month": "month",
            "hour": "hour",
            "yearly": "year",
            "monthly": "month",
            "hourly": "hour",
        }.get(str(pay.get("period") or "").lower(), "unknown")
        mode = (
            "remote"
            if item.get("remote")
            else "hybrid"
            if item.get("hybrid")
            else "office"
            if item.get("on_site")
            else None
        )
        result.append(
            card(
                "recruitee",
                source,
                external=item.get("id"),
                title=item.get("title"),
                url=item.get("careers_url"),
                text=text,
                location=place or "unknown",
                conditions_value=conditions(
                    text,
                    place,
                    "recruitee",
                    salary_value=salary(
                        pay.get("min"),
                        pay.get("max"),
                        pay.get("currency"),
                        period,
                        "recruitee.salary",
                    ),
                    work_mode=mode,
                    employment=item.get("employment_type_code"),
                    published=item.get("published_at"),
                    level=item.get("experience_code"),
                ),
            )
        )
    return result


# --------------------------------------------------------------------------- job boards


def remotive(data: object, source: dict) -> list[dict]:
    result = []
    for item in _list(data, "jobs"):
        text = plain(item.get("description"))
        allowed = item.get("candidate_required_location")
        pay_text = str(item.get("salary") or "")
        result.append(
            card(
                "remotive",
                source,
                external=item.get("id"),
                title=item.get("title"),
                url=item.get("url"),
                text=text,
                location=allowed or "Remote",
                company_name=str(item.get("company_name") or ""),
                conditions_value=conditions(
                    text,
                    "Remote",
                    "remotive",
                    salary_value=fields.salary_from_text(pay_text, "remotive.salary")
                    if pay_text
                    else None,
                    work_mode="remote",
                    employment=item.get("job_type"),
                    allowed=geography(allowed, "remotive.candidate_required_location"),
                    published=item.get("publication_date"),
                ),
            )
        )
    return result


def remoteok(data: object, source: dict) -> list[dict]:
    if not isinstance(data, list):
        raise TypeError("Unexpected response schema")
    result = []
    for item in data:
        # The first element is Remote OK's legal notice, not a job.
        if not isinstance(item, dict) or not item.get("id") or not item.get("position"):
            continue
        text = plain(item.get("description"))
        result.append(
            card(
                "remoteok",
                source,
                external=item.get("id"),
                title=item.get("position"),
                url=item.get("url") or item.get("apply_url"),
                text=text,
                location=item.get("location") or "Remote",
                company_name=str(item.get("company") or ""),
                conditions_value=conditions(
                    text,
                    "Remote",
                    "remoteok",
                    salary_value=salary(
                        item.get("salary_min"),
                        item.get("salary_max"),
                        "USD",
                        "year",
                        "remoteok.salary",
                    ),
                    work_mode="remote",
                    allowed=geography(item.get("location"), "remoteok.location"),
                    published=item.get("date") or item.get("epoch"),
                ),
            )
        )
    return result


def jobicy(data: object, source: dict) -> list[dict]:
    result = []
    for item in _list(data, "jobs"):
        text = plain(item.get("jobDescription") or item.get("jobExcerpt"))
        result.append(
            card(
                "jobicy",
                source,
                external=item.get("id"),
                title=item.get("jobTitle"),
                url=item.get("url"),
                text=text,
                location=item.get("jobGeo") or "Remote",
                company_name=str(item.get("companyName") or ""),
                scope="full" if item.get("jobDescription") else "excerpt",
                conditions_value=conditions(
                    text,
                    "Remote",
                    "jobicy",
                    salary_value=salary(
                        item.get("annualSalaryMin"),
                        item.get("annualSalaryMax"),
                        item.get("salaryCurrency"),
                        "year",
                        "jobicy.annualSalary",
                    ),
                    work_mode="remote",
                    employment=item.get("jobType"),
                    allowed=geography(item.get("jobGeo"), "jobicy.jobGeo"),
                    published=item.get("pubDate"),
                    level=item.get("jobLevel"),
                ),
            )
        )
    return result


def arbeitnow(data: object, source: dict) -> list[dict]:
    result = []
    for item in _list(data, "data"):
        text = plain(item.get("description"))
        result.append(
            card(
                "arbeitnow",
                source,
                external=item.get("slug"),
                title=item.get("title"),
                url=item.get("url"),
                text=text,
                location=item.get("location") or "unknown",
                company_name=str(item.get("company_name") or ""),
                conditions_value=conditions(
                    text,
                    str(item.get("location") or ""),
                    "arbeitnow",
                    work_mode="remote" if item.get("remote") is True else None,
                    employment=item.get("job_types"),
                    published=item.get("created_at"),
                ),
            )
        )
    return result


def getonbrd(data: object, source: dict) -> list[dict]:
    result = []
    for item in _list(data, "data"):
        attributes = item.get("attributes") or {}
        company = ((attributes.get("company") or {}).get("data") or {}).get("attributes") or {}
        text = plain(
            " ".join(
                str(attributes.get(key) or "")
                for key in ("description", "projects", "functions", "desirable")
            )
        )
        countries = attributes.get("countries") or []
        mode = {
            "fully_remote": "remote",
            "remote_local": "remote",
            "hybrid": "hybrid",
            "no_remote": "office",
        }.get(
            str(attributes.get("remote_modality") or ""),
            "remote" if attributes.get("remote") else None,
        )
        result.append(
            card(
                "getonbrd",
                source,
                external=item.get("id"),
                title=attributes.get("title"),
                url=(item.get("links") or {}).get("public_url"),
                text=text,
                location=", ".join(countries) or "unknown",
                company_name=str(
                    company.get("name")
                    or ((attributes.get("company") or {}).get("data") or {}).get("id")
                    or ""
                ),
                conditions_value=conditions(
                    text,
                    ", ".join(countries),
                    "getonbrd",
                    salary_value=salary(
                        attributes.get("min_salary"),
                        attributes.get("max_salary"),
                        "USD",
                        "month",
                        "getonbrd.salary",
                    ),
                    work_mode=mode,
                    allowed=geography(countries, "getonbrd.countries")
                    if mode == "remote" and countries
                    else None,
                    published=attributes.get("published_at"),
                ),
            )
        )
    return result


def trudvsem(data: object, source: dict) -> list[dict]:
    result = []
    results = data.get("results") if isinstance(data, dict) else None
    items = (results or {}).get("vacancies", []) if isinstance(results, dict) else None
    if items is None or not isinstance(items, list):
        raise TypeError("Unexpected response schema")
    for entry in items:
        item = entry.get("vacancy") if isinstance(entry, dict) else None
        if not isinstance(item, dict):
            raise TypeError("Unexpected response schema")
        company = item.get("company") or {}
        name = str(company.get("name") or "")
        text = plain(
            " ".join(str(item.get(key) or "") for key in ("duty", "requirements", "qualification"))
        )
        region = (item.get("region") or {}).get("name") or "unknown"
        value = card(
            "trudvsem",
            {**source, "market": source.get("market", "ru")},
            external=item.get("id"),
            title=item.get("job-name"),
            url=item.get("vac_url"),
            text=text,
            location=f"{region}, Россия" if region != "unknown" else "Россия",
            company_name=name,
            scope="excerpt",
            conditions_value=conditions(
                text,
                str(region),
                "trudvsem",
                salary_value=salary(
                    item.get("salary_min"),
                    item.get("salary_max"),
                    "RUB",
                    "month",
                    "trudvsem.salary",
                ),
                work_mode=fields._mode(item.get("schedule")) if item.get("schedule") else None,
                employment=item.get("employment"),
                published=item.get("creation-date"),
            ),
        )
        if company.get("inn"):
            # The taxpayer number identifies the employer across postings.
            value["company_id"] = safe_id(f"trudvsem-inn-{company['inn']}")
        result.append(value)
    return result


# --------------------------------------------------------------------------- registry


@dataclass(frozen=True)
class Adapter:
    parse: Callable[[object, dict], list[dict]]
    endpoint: Callable[[dict, int], str]
    page_size: int | None = None
    aggregate: bool = False
    min_interval_seconds: int = 3600


def _query(source: dict, **extra: object) -> str:
    params = {key: value for key, value in extra.items() if value not in (None, "")}
    return urlencode(params)


ADAPTERS: dict[str, Adapter] = {
    "smartrecruiters": Adapter(
        smartrecruiters,
        lambda s, page: (
            f"https://api.smartrecruiters.com/v1/companies/{quote(s['board'], safe='')}/postings?{_query(s, limit=100, offset=page * 100)}"
        ),
        page_size=100,
    ),
    "workable": Adapter(
        workable,
        lambda s, page: (
            f"https://apply.workable.com/api/v1/widget/accounts/{quote(s['board'], safe='')}"
        ),
    ),
    "recruitee": Adapter(
        recruitee, lambda s, page: f"https://{quote(s['board'], safe='')}.recruitee.com/api/offers/"
    ),
    "remotive": Adapter(
        remotive,
        lambda s, page: (
            f"https://remotive.com/api/remote-jobs?{_query(s, category=s.get('category'), search=s.get('query'), limit=s.get('limit'))}".rstrip(
                "?"
            )
        ),
        aggregate=True,
        min_interval_seconds=6 * 3600,
    ),
    "remoteok": Adapter(
        remoteok,
        lambda s, page: f"https://remoteok.com/api?{_query(s, tag=s.get('tag'))}".rstrip("?"),
        aggregate=True,
    ),
    "jobicy": Adapter(
        jobicy,
        lambda s, page: (
            f"https://jobicy.com/api/v2/remote-jobs?{_query(s, count=min(int(s.get('limit') or 50), 100), geo=s.get('geo'), industry=s.get('category'), tag=s.get('query'))}"
        ),
        aggregate=True,
    ),
    "arbeitnow": Adapter(
        arbeitnow,
        lambda s, page: f"https://www.arbeitnow.com/api/job-board-api?{_query(s, page=page + 1)}",
        page_size=100,
        aggregate=True,
    ),
    "getonbrd": Adapter(
        getonbrd,
        lambda s, page: (
            f"https://www.getonbrd.com/api/v0/search/jobs?{_query(s, query=s.get('query'), per_page=100, page=page + 1, expand='["company"]')}"
        ),
        page_size=100,
        aggregate=True,
    ),
    "trudvsem": Adapter(
        trudvsem,
        lambda s, page: (
            f"https://opendata.trudvsem.ru/api/v1/vacancies{'/region/' + quote(str(s['region']), safe='') if s.get('region') else ''}?{_query(s, text=s.get('query'), offset=page, limit=100)}"
        ),
        page_size=100,
        aggregate=True,
    ),
}
