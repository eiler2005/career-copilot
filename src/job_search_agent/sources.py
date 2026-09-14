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
                "status_checked_on": now(),
                "content_scope": "salary_index_card",
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
            value = {
                "id": f"{provider}-{safe_id(source['company_id'])}-{safe_id(external)}",
                "company_id": source["company_id"],
                "external_id": external,
                "provider": provider,
                "title": plain(title),
                "location": str(location),
                "market": source.get("market", "unknown"),
                "urls": [canonical_url(url)],
                "text": plain(content),
                "requirements": [],
                "availability": availability,
                "status_checked_on": now(),
                "content_scope": "excerpt"
                if not item.get("description") and provider == "hh"
                else "full",
            }
        result.append(value)
    return result


def endpoint(source: dict, page: int = 0) -> str:
    board = quote(source.get("board", ""), safe="")
    provider = source["provider"]
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
    remaining = int(settings.get("max_requests_per_run", 20))
    for source in sources:
        sid = safe_id(source["id"])
        old_health = store.get("source_health", sid) or {}
        health = {**old_health, "id": sid, "last_attempt": now(), "count": 0}
        health.pop("failure_status", None)
        if not replay and old_health.get("next_attempt", "") > now():
            results.append(
                {"id": sid, "status": "cooldown", "next_attempt": old_health["next_attempt"]}
            )
            continue
        company = store.get("companies", source["company_id"])
        if not company and source["provider"] != "linkedinsalaries":
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
                url = endpoint(source, page)
                allowed = set(source.get("allowed_hosts", [])) | {
                    urlsplit(endpoint(source)).hostname
                }
                checked_url(url, allowed)
                if source.get("proxy_env") and not source.get("proxy_allowed", False):
                    raise ValueError("Proxy requires explicit per-source permission")
                if source.get("proxy_env") and "linkedin" in urlsplit(url).hostname:
                    raise ValueError("LinkedIn proxy route is forbidden")
                proxy = os.environ.get(source.get("proxy_env", ""))
                own_client = client is None
                transport = client or httpx.Client(
                    timeout=25, follow_redirects=False, trust_env=False, proxy=proxy
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
                try:
                    response = transport.get(
                        url,
                        headers={
                            "User-Agent": source.get(
                                "user_agent", "job-search-agent/0.1 (read-only job research)"
                            )
                        },
                    )
                    raw = response.content
                    if len(raw) > 5_000_000:
                        status = "response_too_large"
                        break
                    snapshot = store.artifact(f"snapshots/{sid}/{digest(raw)}.txt", raw)
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
                for value in selected_jobs:
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
                    store.observe_vacancy(value, sid, snapshot, replay=bool(replay))
                health["count"] += len(selected_jobs)
                status = "success_nonempty" if health["count"] else "success_empty"
            except (ValueError, KeyError, TypeError, AttributeError):
                status = "parse_changed"
                break
            if replay or source["provider"] not in {"lever", "hh"} or len(jobs) < 100:
                break
            # Avoid rapid pagination. A paginated board can be manually continued after cooldown.
            if page == pages - 1:
                status = "partial"
        if health["count"] and not status.startswith("success"):
            health["failure_status"], status = status, "partial"
        health["status"] = status
        if status.startswith("success"):
            health.update(last_success=now(), rate_limit_attempts=0)
        if status != "rate_limited" and health.get("failure_status") != "rate_limited":
            interval = max(4, int(source.get("interval_seconds", 3600)))
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
    return results
