"""Read-only vacancy availability checks with explainable, conservative rules.

A check fetches the posting URL already stored for a vacancy, follows at most a few
redirects to public addresses, and classifies the response:

* closed  — HTTP 404/410, a redirect away from the posting, an explicit visible
            "closed/archived" message or an expired structured posting;
* open    — a visible apply control or a published structured job posting;
* unknown — access blocked (never bypassed), network errors or no reliable signal.

Results carry the reason, confidence and evidence. A human-recorded closed state is
never silently reopened by a medium-confidence signal; it becomes `conflicting`.
"""

from __future__ import annotations

import html
import ipaddress
import json
import re
import socket
import time
from collections.abc import Iterable
from datetime import UTC, datetime
from urllib.parse import urljoin, urlsplit

import httpx

from .core import Store, now

METHOD = "availability-rules-v1"
USER_AGENT = "Mozilla/5.0 (compatible; CareerCopilot/0.1; read-only availability check)"
MAX_BYTES = 3_000_000
MAX_REDIRECTS = 5
HISTORY_LIMIT = 20
INACTIVE = frozenset({"closed", "archived", "expired", "expired_copy"})
CLOSED_MARKERS = (
    "no longer accepting applications",
    "this job is no longer available",
    "job is no longer available",
    "this position has been filled",
    "position has been filled",
    "this job has expired",
    "this position is no longer open",
    "вакансия в архиве",
    "вакансия закрыта",
    "вакансия больше не актуальна",
    "приём откликов завершён",
    "прием откликов завершен",
    "больше не принимает отклики",
)
OPEN_MARKERS = (
    "apply now",
    "apply for this job",
    "easy apply",
    "submit application",
    "submit your application",
    "откликнуться",
    "подать заявку",
    "отправить резюме",
)
BLOCKED_STATUSES = frozenset({401, 403, 407, 429, 451, 503})


def _visible_text(markup: str) -> str:
    markup = re.sub(r"(?is)<(script|style|noscript|template|svg)[^>]*>.*?</\1>", " ", markup)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", markup))).casefold()


def _job_postings(markup: str) -> list[dict]:
    postings = []
    for match in re.finditer(r"(?is)<script[^>]+application/ld\+json[^>]*>(.*?)</script>", markup):
        try:
            data = json.loads(match.group(1))
        except ValueError:
            continue
        items = (
            data
            if isinstance(data, list)
            else data.get("@graph", [data])
            if isinstance(data, dict)
            else []
        )
        postings += [
            item
            for item in items
            if isinstance(item, dict) and "JobPosting" in str(item.get("@type"))
        ]
    return postings


def _expired(posting: dict) -> bool:
    value = posting.get("validThrough")
    if not isinstance(value, str) or not value:
        return False
    try:
        moment = datetime.fromisoformat(value)
    except ValueError:
        return False
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=UTC)
    return moment < datetime.now(UTC)


def _identifiers(url: str) -> list[str]:
    """Stable tokens a redirect must keep to still point at the same posting."""
    path = urlsplit(url).path
    numbers = re.findall(r"\d{4,}", path)
    if numbers:
        return numbers
    segments = [segment for segment in path.split("/") if len(segment) >= 6]
    return segments[-1:]


def redirected_away(original: str, final: str) -> bool:
    if urlsplit(final).path.rstrip("/").lower().endswith(("/closed", "/expired", "/archive")):
        return True
    tokens = _identifiers(original)
    return bool(tokens) and not any(token.lower() in final.lower() for token in tokens)


def public_url(url: str) -> str:
    """Allow only HTTP(S) URLs whose host resolves exclusively to public addresses."""
    parts = urlsplit(url)
    if parts.scheme not in {"http", "https"} or not parts.hostname or parts.username:
        raise ValueError("not_public_url")
    host = parts.hostname
    if host in {"localhost"} or host.endswith((".local", ".internal", ".localhost")):
        raise ValueError("not_public_url")
    try:
        addresses = {info[4][0] for info in socket.getaddrinfo(host, parts.port or 443)}
    except OSError as error:
        raise ValueError("network_error") from error
    if not addresses or not all(
        ipaddress.ip_address(address.split("%")[0]).is_global for address in addresses
    ):
        raise ValueError("not_public_url")
    return url


def classify(original: str, status: int, final: str, markup: str) -> dict:
    """Pure decision function over a fetched response."""
    if status in {404, 410}:
        return {
            "status": "closed",
            "confidence": "high",
            "reason": "http_gone",
            "evidence": str(status),
        }
    title = re.search(r"(?is)<title[^>]*>(.*?)</title>", markup or "")
    if status in BLOCKED_STATUSES or (title and "attention required" in title.group(1).casefold()):
        return {
            "status": "unknown",
            "confidence": "low",
            "reason": "access_blocked",
            "evidence": str(status),
        }
    if not 200 <= status < 300:
        return {
            "status": "unknown",
            "confidence": "low",
            "reason": "http_error",
            "evidence": str(status),
        }
    if redirected_away(original, final):
        return {
            "status": "closed",
            "confidence": "medium",
            "reason": "redirected_away",
            "evidence": final[:200],
        }
    text = _visible_text(markup)
    closed = next((marker for marker in CLOSED_MARKERS if marker in text), None)
    if closed:
        return {
            "status": "closed",
            "confidence": "high",
            "reason": "closed_marker",
            "evidence": closed,
        }
    postings = _job_postings(markup)
    if any(_expired(posting) for posting in postings):
        return {
            "status": "closed",
            "confidence": "high",
            "reason": "structured_expired",
            "evidence": "validThrough",
        }
    opened = next((marker for marker in OPEN_MARKERS if marker in text), None)
    if (
        opened is None
        and "linkedin.com" in (urlsplit(final).hostname or "")
        and "top-card-layout__cta" in markup
    ):
        opened = "linkedin apply control"
    if opened:
        return {
            "status": "open",
            "confidence": "medium",
            "reason": "apply_control",
            "evidence": opened,
        }
    if postings:
        return {
            "status": "open",
            "confidence": "medium",
            "reason": "structured_posting",
            "evidence": "JobPosting",
        }
    return {"status": "unknown", "confidence": "low", "reason": "no_signal", "evidence": None}


def check_url(url: str | None, client: httpx.Client | None = None) -> dict:
    """Fetch one posting URL and classify it; never raises for remote failures."""
    started = now()
    base = {
        "url": url,
        "checked_at": started,
        "method": METHOD,
        "http_status": None,
        "final_url": None,
    }
    if not url:
        return {
            **base,
            "status": "unknown",
            "confidence": "low",
            "reason": "no_url",
            "evidence": None,
        }
    own = client is None
    client = client or httpx.Client(timeout=20, follow_redirects=False, trust_env=False)
    try:
        current = public_url(url)
        for _ in range(MAX_REDIRECTS + 1):
            with client.stream(
                "GET",
                current,
                headers={"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9,ru;q=0.7"},
            ) as response:
                if response.is_redirect and response.headers.get("location"):
                    current = public_url(urljoin(current, response.headers["location"]))
                    continue
                body = bytearray()
                for chunk in response.iter_bytes():
                    body += chunk
                    if len(body) > MAX_BYTES:
                        break
                markup = body.decode(response.encoding or "utf-8", errors="replace")
                verdict = classify(url, response.status_code, str(response.url), markup)
                return {
                    **base,
                    **verdict,
                    "http_status": response.status_code,
                    "final_url": str(response.url),
                }
        return {
            **base,
            "status": "unknown",
            "confidence": "low",
            "reason": "too_many_redirects",
            "evidence": None,
        }
    except ValueError as error:
        reason = (
            str(error) if str(error) in {"not_public_url", "network_error"} else "network_error"
        )
        return {
            **base,
            "status": "unknown",
            "confidence": "low",
            "reason": reason,
            "evidence": None,
        }
    except httpx.HTTPError:
        return {
            **base,
            "status": "unknown",
            "confidence": "low",
            "reason": "network_error",
            "evidence": None,
        }
    finally:
        if own:
            client.close()


def posting_url(vacancy: dict) -> str | None:
    for value in vacancy.get("urls") or []:
        if isinstance(value, str) and value.startswith(("http://", "https://")):
            return value
    return None


def effective_availability(current: object, result: dict) -> str:
    """Merge a check into the recorded availability without overriding human judgment."""
    current = current if isinstance(current, str) else "unknown"
    status = result.get("status")
    if status == "closed":
        return "archived" if current == "archived" else "closed"
    if status == "open":
        if current in INACTIVE and result.get("confidence") != "high":
            return "conflicting"
        return "open"
    return current


def apply_result(store: Store, vacancy_id: str, result: dict) -> dict:
    vacancy = store.get("vacancies", vacancy_id)
    if not vacancy:
        raise ValueError("Vacancy not found")
    previous = vacancy.get("availability_check") or {}
    if previous.get("checked_at") and previous["checked_at"] >= result["checked_at"]:
        return vacancy
    history = [*(vacancy.get("availability_history") or []), result][-HISTORY_LIMIT:]
    updated = {**vacancy, "availability_check": result, "availability_history": history}
    if result["status"] != "unknown":
        updated["availability"] = effective_availability(vacancy.get("availability"), result)
        updated["status_checked_on"] = result["checked_at"][:10]
    store.put("vacancies", updated)
    store.event(
        "availability_checked",
        [vacancy_id],
        {
            "status": result["status"],
            "reason": result["reason"],
            "confidence": result["confidence"],
            "checked_at": result["checked_at"],
            "availability": updated.get("availability"),
        },
    )
    return updated


def select(
    store: Store, ids: Iterable[str] = (), unverified: bool = False, stale_days: int | None = None
) -> list[dict]:
    wanted = set(ids)
    today = datetime.now(UTC).date()
    chosen = []
    for vacancy in store.all("vacancies"):
        if wanted and vacancy["id"] not in wanted:
            continue
        if not wanted:
            if (
                vacancy.get("review_status") == "rejected"
                or vacancy.get("availability") in INACTIVE
            ):
                continue
            checked = (vacancy.get("availability_check") or {}).get("checked_at") or vacancy.get(
                "status_checked_on"
            )
            if unverified and vacancy.get("availability") not in {None, "unknown", "conflicting"}:
                continue
            if stale_days is not None and checked:
                try:
                    if (today - datetime.fromisoformat(checked[:10]).date()).days < stale_days:
                        continue
                except ValueError:
                    pass
        chosen.append(vacancy)
    missing = wanted - {vacancy["id"] for vacancy in chosen}
    if missing:
        raise ValueError("Vacancy not found")
    return chosen


def run(
    store: Store,
    ids: Iterable[str] = (),
    unverified: bool = False,
    stale_days: int | None = None,
    limit: int = 50,
    delay: float = 2.0,
    client: httpx.Client | None = None,
) -> dict:
    vacancies = select(store, ids, unverified, stale_days)[: max(0, limit)]
    results, last_host = [], {}
    for vacancy in vacancies:
        url = posting_url(vacancy)
        host = urlsplit(url).hostname if url else None
        if host and host in last_host and delay > 0:
            wait = delay - (time.monotonic() - last_host[host])
            if wait > 0:
                time.sleep(wait)
        result = check_url(url, client)
        if host:
            last_host[host] = time.monotonic()
        store.db.execute("BEGIN IMMEDIATE")
        try:
            updated = apply_result(store, vacancy["id"], result)
            store.db.execute("COMMIT")
        except Exception:
            store.db.execute("ROLLBACK")
            raise
        results.append(
            {"vacancy_id": vacancy["id"], "availability": updated.get("availability"), **result}
        )
    counts = {
        status: sum(1 for item in results if item["status"] == status)
        for status in ("open", "closed", "unknown")
    }
    return {"checked": len(results), "counts": counts, "results": results}


def import_results(store: Store, entries: dict) -> dict:
    """Apply checks recorded by a remote dashboard (vacancy_id -> result)."""
    if not isinstance(entries, dict):
        raise ValueError("Availability import expects an object keyed by vacancy ID")  # noqa: TRY004
    applied = skipped = 0
    store.db.execute("BEGIN IMMEDIATE")
    try:
        for vacancy_id, result in sorted(entries.items()):
            required = {"status", "confidence", "reason", "checked_at", "method"}
            if (
                not isinstance(result, dict)
                or not required <= set(result)
                or result["status"] not in {"open", "closed", "unknown"}
            ):
                raise ValueError("Invalid availability result")
            datetime.fromisoformat(result["checked_at"])
            if not store.get("vacancies", vacancy_id):
                skipped += 1
                continue
            before = (store.get("vacancies", vacancy_id).get("availability_check") or {}).get(
                "checked_at"
            )
            apply_result(store, vacancy_id, result)
            applied += 0 if before and before >= result["checked_at"] else 1
        store.db.execute("COMMIT")
    except Exception:
        store.db.execute("ROLLBACK")
        raise
    return {"applied": applied, "skipped": skipped}
