"""Read-only public ATS and JSON-LD adapters. No application or bypass methods."""

from __future__ import annotations

import html
import ipaddress
import json
import math
import os
import re
import time
import unicodedata
from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from urllib.parse import quote, urlsplit

import httpx

from . import relevance, source_adapters, vacancy_fields
from .core import Store, canonical_url, digest, now, safe_id


def plain(text: str) -> str:
    text = html.unescape(html.unescape(text or ""))
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text)).strip()


class JobLD(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reading = False
        self.buffer = ""
        self.objects = []

    def handle_starttag(self, tag, attrs):
        if tag == "script" and dict(attrs).get("type") == "application/ld+json":
            self.reading, self.buffer = True, ""

    def handle_data(self, data):
        if self.reading:
            self.buffer += data

    def handle_endtag(self, tag):
        if tag == "script" and self.reading:
            self.reading = False
            self.objects.append(json.loads(self.buffer))


def source_company_id(name: str) -> str:
    """Create a stable local employer ID when an aggregate source has no employer key."""
    identity = re.sub(r"\s+", " ", unicodedata.normalize("NFKC", name).strip())
    transliterated = unicodedata.normalize("NFKD", identity).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "-", transliterated.lower()).strip("-")
    readable = (slug or "company")[:48]
    return safe_id(f"linkedinsalaries-{readable}-{digest(identity.casefold())[:16]}")


def linkedinsalaries_jobs(data: dict, source: dict) -> list[dict]:
    """Normalize the provider's documented public dataset without requesting LinkedIn."""
    items = data.get("jobs") if isinstance(data, dict) else None
    if not isinstance(items, list):
        raise TypeError("Expected LinkedIn Salaries jobs list")
    result = []
    for item in items:
        if not isinstance(item, dict):
            raise TypeError("Expected LinkedIn Salaries job object")
        external_value = item.get("id")
        title_value = item.get("title")
        company_value = item.get("company")
        if (
            external_value is None
            or isinstance(external_value, bool)
            or not isinstance(title_value, str)
            or not isinstance(company_value, str)
        ):
            raise ValueError("LinkedIn Salaries job is missing identity fields")
        external = str(external_value).strip()
        title = title_value.strip()
        company_name = company_value.strip()
        url = str(item.get("url", ""))
        if not external or not title or not company_name:
            raise ValueError("LinkedIn Salaries job is missing identity fields")
        if urlsplit(url).hostname not in {"linkedin.com", "www.linkedin.com"}:
            raise ValueError("LinkedIn Salaries job URL is not a LinkedIn vacancy")
        salary = item.get("salaryUsdMo")
        if (
            isinstance(salary, bool)
            or not isinstance(salary, (int, float))
            or not math.isfinite(salary)
            or salary < 0
        ):
            salary = None
        result.append(
            {
                "id": f"linkedinsalaries-{safe_id(external)}",
                "company_id": source_company_id(company_name),
                "company_name": company_name,
                "external_id": external,
                "provider": "linkedinsalaries",
                "title": plain(title),
                # This is the provider's company-location label, not a verified job location.
                "location": str(item.get("companyLocation") or "unknown"),
                "market": source.get("market", "unknown"),
                "urls": [canonical_url(url)],
                "text": "",
                "requirements": [],
                "availability": "unknown",
                # An aggregated index card does not verify that the posting is still open.
                "content_scope": "salary_index_card",
                "conditions": vacancy_fields.from_aggregate(item),
                "compensation": {
                    "source": "linkedinsalaries.com",
                    "raw": item.get("salaryCite"),
                    "normalized_monthly_usd": salary,
                    "currency": "USD",
                    "period": "month",
                    "reliability": "aggregated",
                },
                "source_labels": {
                    "job_type": item.get("jobType"),
                    "seniority": item.get("jobLevel"),
                    "work_mode": item.get("jobMode"),
                    "payment_type": item.get("jobPayments"),
                    "employment_type": item.get("jobTime"),
                    "region": item.get("region"),
                    "easy_apply": item.get("easyApply"),
                    "published_on": item.get("dayKey"),
                    "dataset_date": data.get("todayKey"),
                },
            }
        )
    return result


def parse_jobs(provider: str, body: str, source: dict) -> list[dict]:
    data = None if provider == "corporate" else json.loads(body)
    if provider in source_adapters.ADAPTERS:
        return source_adapters.ADAPTERS[provider].parse(data, source)
    if provider == "hh" and source.get("query") and not source.get("employer_id"):
        return hh_search_jobs(data, source)
    if provider == "greenhouse":
        items = data["jobs"]
    elif provider == "lever":
        if not isinstance(data, list):
            raise ValueError("Expected Lever list")
        items = data
    elif provider == "ashby":
        items = data["jobs"]
    elif provider == "hh":
        items = data.get("items", [data] if "id" in data else None)
    elif provider == "linkedinsalaries":
        return linkedinsalaries_jobs(data, source)
    elif provider == "manual":
        items = data["vacancies"]
    elif provider == "corporate":
        parser = JobLD()
        parser.feed(body)
        items = []

        def descend(value):
            if isinstance(value, dict):
                kind = value.get("@type", [])
                if kind == "JobPosting" or isinstance(kind, list) and "JobPosting" in kind:
                    items.append(value)
                else:
                    for child in value.values():
                        descend(child)
            elif isinstance(value, list):
                for child in value:
                    descend(child)

        descend(parser.objects)
        if not items:
            raise ValueError("No JobPosting data; manual/browser import required")
    else:
        raise ValueError("Unknown provider")
    if not isinstance(items, list):
        raise TypeError("Unexpected response schema")
    result = []
    for item in items:
        if provider == "manual":
            value = dict(item)
            value.setdefault("availability", "unknown")
            if "conditions" not in value:
                value["conditions"] = vacancy_fields.from_posting(
                    value.get("text", ""), None, str(value.get("location", "")), "manual"
                )
        else:
            external = str(
                item.get("id")
                or item.get("identifier", {}).get("value")
                or digest([item.get("title"), item.get("url")])[:20]
            )
            url = (
                item.get("absolute_url")
                or item.get("hostedUrl")
                or item.get("jobUrl")
                or item.get("alternate_url")
                or item.get("url")
                or source["url"]
            )
            title = item.get("title") or item.get("text") or item.get("name")
            if not title:
                raise ValueError("Missing job title")
            content = (
                item.get("content")
                or item.get("descriptionPlain")
                or item.get("descriptionHtml")
                or item.get("description")
                or ""
            )
            if provider == "lever":
                content += " " + " ".join(x.get("content", "") for x in item.get("lists", []))
            if provider == "hh" and not content:
                content = " ".join(str(x or "") for x in item.get("snippet", {}).values())
            location = (
                item.get("location")
                or item.get("categories", {}).get("location")
                or item.get("area", {}).get("name")
                or item.get("jobLocation")
                or "unknown"
            )
            if isinstance(location, dict):
                location = location.get("name") or json.dumps(location, ensure_ascii=False)
            availability = (
                "open" if provider in {"greenhouse", "lever", "ashby", "hh"} else "unknown"
            )
            if item.get("archived") is True:
                availability = "archived"
            valid = item.get("validThrough")
            if valid and str(valid)[:10] < now()[:10]:
                availability = "expired_copy"
            text = plain(content)
            value = {
                "id": f"{provider}-{safe_id(source['company_id'])}-{safe_id(external)}",
                "company_id": source["company_id"],
                "external_id": external,
                "provider": provider,
                "title": plain(title),
                "location": str(location),
                "market": source.get("market", "unknown"),
                "urls": [canonical_url(url)],
                "text": text,
                "requirements": [],
                "availability": availability,
                "content_scope": "excerpt"
                if not item.get("description") and provider == "hh"
                else "full",
                "conditions": vacancy_fields.from_provider(provider, item, text, str(location)),
            }
            if provider in {"greenhouse", "lever", "ashby", "hh"}:
                # Being listed on the employer's own board is a dated availability signal.
                value["status_checked_on"] = now()
                value["availability_basis"] = f"{provider} board listing"
        result.append(value)
    return result


def hh_search_jobs(data: dict, source: dict) -> list[dict]:
    """HH text search: employers come from each item, not from the source."""
    items = data.get("items") if isinstance(data, dict) else None
    if not isinstance(items, list):
        raise TypeError("Unexpected response schema")
    result = []
    for item in items:
        employer = item.get("employer") or {}
        name = str(employer.get("name") or "").strip()
        if not name:
            raise ValueError("HH search item is missing the employer")
        company = (
            safe_id(f"hh-employer-{employer['id']}")
            if employer.get("id")
            else source_adapters.company_id("hh", name)
        )
        [value] = parse_jobs(
            "hh", json.dumps(item), {**source, "company_id": company, "employer_id": "item"}
        )
        value["id"] = f"hh-{safe_id(str(item.get('id')))}"
        value["company_name"] = name
        result.append(value)
    return result


def page_size(provider: str) -> int | None:
    if provider in source_adapters.ADAPTERS:
        return source_adapters.ADAPTERS[provider].page_size
    return 100 if provider in {"lever", "hh"} else None


def endpoint(source: dict, page: int = 0) -> str:
    board = quote(source.get("board", ""), safe="")
    provider = source["provider"]
    if provider in source_adapters.ADAPTERS:
        return source_adapters.ADAPTERS[provider].endpoint(source, page)
    if provider == "hh" and not source.get("employer_id"):
        if not source.get("query"):
            raise ValueError("HH source needs employer_id or query")
        params = {
            "text": source["query"],
            "per_page": 100,
            "page": page,
            "order_by": "publication_time",
        }
        for key in ("area", "period", "professional_role", "experience", "schedule"):
            if source.get(key):
                params[key] = source[key]
        return "https://api.hh.ru/vacancies?" + "&".join(
            f"{key}={quote(str(value), safe='')}" for key, value in params.items()
        )
    if provider == "greenhouse":
        return f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs?content=true"
    if provider == "lever":
        return f"https://api.lever.co/v0/postings/{board}?mode=json&limit=100&skip={page * 100}"
    if provider == "ashby":
        return f"https://api.ashbyhq.com/posting-api/job-board/{board}?includeCompensation=true"
    if provider == "hh":
        return f"https://api.hh.ru/vacancies?employer_id={quote(str(source['employer_id']))}&per_page=100&page={page}"
    if provider == "linkedinsalaries":
        dataset = "https://linkedinsalaries.com/jobs.json"
        if canonical_url(source.get("url", dataset)) != dataset:
            raise ValueError("LinkedIn Salaries supports only its public jobs.json dataset")
        return dataset
    return canonical_url(source["url"])


def proxy_client(proxy: str) -> httpx.Client:
    """Client for the reserve proxy channel; the proxy URL is never logged or stored."""
    return httpx.Client(timeout=40, follow_redirects=False, trust_env=False, proxy=proxy)


def retry_delay(header: str | None) -> int:
    try:
        if header and header.isdigit():
            return max(1, int(header))
        if header:
            return max(1, int((parsedate_to_datetime(header) - datetime.now(UTC)).total_seconds()))
    except (ValueError, TypeError):
        pass
    return 30


def checked_url(url: str, allowed: set[str]) -> str:
    canonical_url(url)
    parts = urlsplit(url)
    if parts.scheme != "https" or parts.hostname not in allowed:
        raise ValueError("Source URL outside HTTPS host allowlist")
    try:
        if not ipaddress.ip_address(parts.hostname).is_global:
            raise ValueError("Private source address is forbidden")
    except ValueError as error:
        if "forbidden" in str(error):
            raise
    if parts.hostname in {"localhost", "localhost.localdomain"} or parts.hostname.endswith(
        ".local"
    ):
        raise ValueError("Local source host is forbidden")
    return url


def discover(store: Store, *, source_id: str | None = None, client=None, replay: str | None = None):
    settings = store.settings
    sources = [
        s
        for s in settings["sources"]
        if s.get("enabled", True) and (source_id is None or s["id"] == source_id)
    ]
    if source_id and not sources:
        raise ValueError("Unknown or disabled source")
    results = []
    run = {
        "new": [],
        "changed": [],
        "unchanged": 0,
        "errors": [],
        "relevance": {},
        "screened_out": 0,
    }
    try:
        facts = store.facts
    except (OSError, ValueError):
        facts = None
    try:
        screen_profile = relevance.profile(settings, facts)
    except ValueError:
        # An invalid relevance section never stops collection; the dashboard shows the error.
        screen_profile = None
    started = now()
    remaining = int(settings.get("max_requests_per_run", 20))
    for source in sources:
        sid = safe_id(source["id"])
        old_health = store.get("source_health", sid) or {}
        health = {**old_health, "id": sid, "last_attempt": now(), "count": 0}
        health.pop("failure_status", None)
        health.pop("route", None)
        health.pop("screened_out", None)
        if not replay and old_health.get("next_attempt", "") > now():
            results.append(
                {"id": sid, "status": "cooldown", "next_attempt": old_health["next_attempt"]}
            )
            continue
        aggregate = (
            source["provider"] == "linkedinsalaries"
            or (
                source["provider"] in source_adapters.ADAPTERS
                and source_adapters.ADAPTERS[source["provider"]].aggregate
            )
            or (
                source["provider"] == "hh"
                and bool(source.get("query"))
                and not source.get("employer_id")
            )
        )
        company = store.get("companies", source.get("company_id", ""))
        if not company and not aggregate:
            store.put(
                "companies",
                {
                    "id": source["company_id"],
                    "name": source.get("company_name", source["company_id"]),
                    "about": "unknown",
                    "business_areas": [],
                    "size": {
                        "metric": "employees",
                        "value": None,
                        "as_of": None,
                        "scope": "unknown",
                        "source_url": None,
                        "reliability": "not_disclosed",
                    },
                },
            )
        status = "success_empty"
        pages = max(1, min(int(source.get("max_pages", 3)), 20))
        for page in range(pages):
            if page and not replay:
                time.sleep(max(4, min(30, int(source.get("request_gap_seconds", 4)))))
            body = ""
            snapshot = replay
            if replay:
                body = store.path(replay).read_text(encoding="utf-8")
            else:
                if remaining <= 0:
                    status = "partial" if health["count"] else "budget_exhausted"
                    break
                try:
                    url = endpoint(source, page)
                    allowed = set(source.get("allowed_hosts", [])) | {
                        urlsplit(endpoint(source)).hostname
                    }
                    checked_url(url, allowed)
                    if source.get("proxy_env") and not source.get("proxy_allowed", False):
                        raise ValueError("Proxy requires explicit per-source permission")
                    if source.get("proxy_env") and "linkedin" in urlsplit(url).hostname:
                        raise ValueError("LinkedIn proxy route is forbidden")
                    if source.get("proxy_mode", "always") not in {"always", "fallback"}:
                        raise ValueError("proxy_mode must be always or fallback")
                except (ValueError, KeyError) as error:
                    # A configuration problem is recorded for this source; others still run.
                    status = "config_error"
                    health["config_error"] = (
                        str(error) if isinstance(error, ValueError) else f"missing {error}"
                    )
                    break
                proxy = os.environ.get(source.get("proxy_env", "")) or None
                # In fallback mode the proxy is a reserve channel for network failures only.
                fallback = proxy if source.get("proxy_mode") == "fallback" else None
                own_client = client is None
                transport = client or httpx.Client(
                    timeout=25,
                    follow_redirects=False,
                    trust_env=False,
                    proxy=None if fallback else proxy,
                )
                remaining -= 1
                host_key = "host-request:" + urlsplit(url).hostname
                last_request = store.db.execute(
                    "SELECT value FROM meta WHERE key=?", (host_key,)
                ).fetchone()
                gap = max(4, min(30, int(source.get("request_gap_seconds", 4))))
                if last_request:
                    wait = gap - (time.time() - float(last_request[0]))
                    if wait > 0:
                        time.sleep(min(wait, gap))
                store.db.execute(
                    "INSERT OR REPLACE INTO meta VALUES(?,?)", (host_key, str(time.time()))
                )
                headers = {
                    "User-Agent": source.get(
                        "user_agent", "job-search-agent/0.1 (read-only job research)"
                    )
                }
                try:
                    try:
                        response = transport.get(url, headers=headers)
                        health["route"] = "proxy" if proxy and not fallback else "direct"
                    except (httpx.TimeoutException, httpx.TransportError):
                        if not fallback:
                            raise
                        # Only a failed connection is retried; HTTP answers such as 403 or
                        # 429 and challenge pages are never retried through another route.
                        with proxy_client(fallback) as reserve:
                            response = reserve.get(url, headers=headers)
                        health["route"] = "proxy_fallback"
                    raw = response.content
                    if len(raw) > 5_000_000:
                        status = "response_too_large"
                        break
                    snapshot = store.readable_artifact(
                        f"snapshots/{sid}", ["response"], raw, ".txt"
                    )
                    body = response.text
                    health["http_status"] = response.status_code
                    if response.status_code == 429:
                        status = "rate_limited"
                        retries = min(int(old_health.get("rate_limit_attempts", 0)) + 1, 3)
                        delay = max(
                            retry_delay(response.headers.get("retry-after")),
                            3600 if retries >= 3 else 30 * retries,
                        )
                        health["next_attempt"] = (
                            datetime.now(UTC) + timedelta(seconds=delay)
                        ).isoformat(timespec="seconds")
                        health["rate_limit_attempts"] = retries
                        break
                    if response.status_code in {401, 403, 407, 999}:
                        status = (
                            "auth_required" if response.status_code in {401, 407} else "blocked"
                        )
                        break
                    if response.status_code != 200:
                        status = (
                            "redirect_requires_review" if response.is_redirect else "http_error"
                        )
                        break
                    if re.search(
                        r"captcha|verify you are human|authwall|access denied",
                        body[:20000],
                        re.IGNORECASE,
                    ):
                        status = "blocked"
                        break
                except httpx.TimeoutException:
                    status = "timeout"
                    break
                except httpx.HTTPError:
                    status = "network_error"
                    break
                finally:
                    if own_client:
                        transport.close()
            try:
                jobs = parse_jobs(source["provider"], body, source)
                health["observed_total"] = health.get("observed_total", 0) + len(jobs)
                selected_jobs = [
                    job
                    for job in jobs
                    if not source.get("include_title")
                    or re.search(source["include_title"], job["title"], re.IGNORECASE)
                ]
                kept = []
                for value in selected_jobs:
                    tier = (
                        relevance.screen(value, screen_profile)["tier"] if screen_profile else None
                    )
                    if tier == "off_profile" and source.get("skip_off_profile"):
                        # The snapshot keeps the original; the card is only not added.
                        health["screened_out"] = health.get("screened_out", 0) + 1
                        run["screened_out"] += 1
                        continue
                    kept.append(value)
                    known = (
                        _company_by_name(store, value["company_name"])
                        if value.get("company_name")
                        and not store.get("companies", value["company_id"])
                        else None
                    )
                    if known:
                        # The same employer found by another source keeps one company record.
                        value["company_id"] = known["id"]
                    if value.get("company_name") and not store.get(
                        "companies", value["company_id"]
                    ):
                        store.put(
                            "companies",
                            {
                                "id": value["company_id"],
                                "name": value["company_name"],
                                "about": "unknown",
                                "business_areas": [],
                                "size": {
                                    "metric": "employees",
                                    "value": None,
                                    "as_of": None,
                                    "scope": "unknown",
                                    "source_url": None,
                                    "reliability": "not_disclosed",
                                },
                            },
                        )
                    if replay:
                        value.update(
                            availability="unknown", status_checked_on=None, historical_snapshot=True
                        )
                    observed = store.observe_vacancy_detailed(
                        value, sid, snapshot, replay=bool(replay)
                    )
                    if observed["status"] == "new":
                        run["new"].append(observed["id"])
                        if tier:
                            run["relevance"][tier] = run["relevance"].get(tier, 0) + 1
                    elif observed["status"] == "changed":
                        run["changed"].append({"id": observed["id"], "fields": observed["fields"]})
                    else:
                        run["unchanged"] += 1
                health["count"] += len(kept)
                status = "success_nonempty" if health["count"] else "success_empty"
            except (ValueError, KeyError, TypeError, AttributeError):
                status = "parse_changed"
                break
            size = page_size(source["provider"])
            if replay or size is None or len(jobs) < size:
                break
            # Avoid rapid pagination. A paginated board can be manually continued after cooldown.
            if page == pages - 1:
                status = "partial"
        if health["count"] and not status.startswith("success"):
            health["failure_status"], status = status, "partial"
        health["status"] = status
        if status != "config_error":
            health.pop("config_error", None)
        if not status.startswith("success"):
            run["errors"].append(
                {
                    "source_id": sid,
                    "status": health.get("failure_status", status),
                    "http_status": health.get("http_status"),
                    "reason": health.get("config_error"),
                    "last_success": health.get("last_success"),
                }
            )
        if status.startswith("success"):
            health.update(last_success=now(), rate_limit_attempts=0)
        if status != "rate_limited" and health.get("failure_status") != "rate_limited":
            minimum = (
                source_adapters.ADAPTERS[source["provider"]].min_interval_seconds
                if source["provider"] in source_adapters.ADAPTERS
                else 4
            )
            interval = max(minimum, int(source.get("interval_seconds", 3600)))
            health["next_attempt"] = (datetime.now(UTC) + timedelta(seconds=interval)).isoformat(
                timespec="seconds"
            )
        if replay:
            health.pop("last_success", None)
            health["replay_only"] = True
            store.event(
                "snapshot_replayed",
                [sid],
                {"snapshot": replay, "count": health["count"], "status": status},
            )
        else:
            store.put("source_health", health)
            store.event("source_checked", [sid], {"health": health})
        results.append(health)
    if not replay and sources:
        record_run(store, run, started, [safe_id(source["id"]) for source in sources])
    return results


def _company_by_name(store: Store, name: str) -> dict | None:
    wanted = _identity(name)
    if not wanted:
        return None
    for company in store.all("companies"):
        if any(
            _identity(item) == wanted
            for item in [company.get("name"), *(company.get("aliases") or [])]
            if item
        ):
            return company
    return None


def _identity(text: object) -> str:
    value = unicodedata.normalize("NFKC", str(text or "")).casefold()
    value = re.sub(r"\((?:m|f|w|d|x)(?:/(?:m|f|w|d|x))*\)", " ", value)
    return re.sub(r"[^\w]+", " ", value).strip()


def possible_duplicates(store: Store, vacancy_ids: list[str]) -> list[dict]:
    """Different records that look like the same role; never merged automatically."""
    vacancies = store.all("vacancies")
    companies = {item["id"]: _identity(item.get("name")) for item in store.all("companies")}
    found, seen = [], set()
    for key in vacancy_ids:
        vacancy = next((item for item in vacancies if item["id"] == key), None)
        if not vacancy:
            continue
        title = _identity(vacancy.get("title"))
        company = companies.get(vacancy.get("company_id")) or _identity(vacancy.get("company_id"))
        place = _identity(vacancy.get("location"))
        for other in vacancies:
            if other["id"] == key or not title or _identity(other.get("title")) != title:
                continue
            other_company = companies.get(other.get("company_id")) or _identity(
                other.get("company_id")
            )
            reason = (
                "same_title_and_company"
                if company and company == other_company
                else "same_title_and_location"
                if place
                and place not in {"unknown", "remote"}
                and place == _identity(other.get("location"))
                else None
            )
            pair = tuple(sorted((key, other["id"])))
            if reason and pair not in seen:
                seen.add(pair)
                found.append({"vacancy_id": key, "other_id": other["id"], "reason": reason})
    return found


def record_run(store: Store, run: dict, started: str, source_ids: list[str]) -> dict:
    touched = run["new"] + [item["id"] for item in run["changed"]]
    value = {
        "id": "run-" + digest([started, source_ids, run])[:20],
        "started_at": started,
        "finished_at": now(),
        "source_ids": source_ids,
        "new": run["new"],
        "changed": run["changed"],
        "unchanged": run["unchanged"],
        "possible_duplicates": possible_duplicates(store, touched),
        "errors": run["errors"],
        "relevance": run.get("relevance") or {},
        "screened_out": run.get("screened_out", 0),
    }
    store.put("collection_runs", value, immutable=True)
    store.event(
        "collection_finished",
        source_ids,
        {key: len(value[key]) for key in ("new", "changed", "possible_duplicates", "errors")},
    )
    return value
