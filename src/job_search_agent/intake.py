"""Add a single vacancy from a link or from pasted text.

The original response or text is kept as a snapshot artifact and the vacancy goes
through the normal observation merge, so a repeated add updates the same record and
never replaces a more complete text. Nothing is applied to or sent on the user's behalf.

Supported inputs:

* an hh.ru vacancy link, read through the public HH API;
* any public page that publishes a JSON-LD JobPosting;
* any other public page: its visible text is kept with `content_scope = page_text`
  and the title comes from the page;
* pasted text, optionally starting with `Title:`, `Company:`, `Location:`, `Salary:`,
  `URL:` header lines.

A company that cannot be matched by name is created with `needs_review: true`.
"""

from __future__ import annotations

import html
import json
import re
import unicodedata

import httpx

from . import availability, descriptions, sources, vacancy_fields
from .core import TRACKS, Store, canonical_url, digest, now, safe_id

MAX_TEXT = 200_000
HH_VACANCY = re.compile(r"^https://(?:[\w-]+\.)?hh\.(?:ru|kz)/vacancy/(\d+)")


def _visible_text(markup: str) -> str:
    markup = re.sub(
        r"(?is)<(script|style|noscript|template|svg|nav|footer|header)[^>]*>.*?</\1>", " ", markup
    )
    markup = re.sub(r"(?i)<br\s*/?>|</(p|li|h[1-6]|div|tr)>", "\n", markup)
    text = html.unescape(re.sub(r"<[^>]+>", " ", markup))
    lines = [re.sub(r"[ \t ]+", " ", line).strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line)[:MAX_TEXT]


def _page_title(markup: str) -> str | None:
    for pattern in (
        r'(?is)<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)',
        r"(?is)<h1[^>]*>(.*?)</h1>",
        r"(?is)<title[^>]*>(.*?)</title>",
    ):
        match = re.search(pattern, markup)
        if match:
            title = sources.plain(match.group(1))
            if title:
                return title[:200]
    return None


def _norm(value: object) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", str(value or "")).casefold()).strip()


def find_company(store: Store, name: str | None, company_id: str | None = None) -> dict | None:
    if company_id:
        company = store.get("companies", company_id)
        if not company:
            raise ValueError("Company not found")
        return company
    wanted = _norm(name)
    if not wanted:
        return None
    for company in store.all("companies"):
        names = [company.get("name"), *(company.get("aliases") or [])]
        if any(_norm(item) == wanted for item in names if item):
            return company
    return None


def ensure_company(
    store: Store, name: str | None, company_id: str | None = None
) -> tuple[dict, bool]:
    company = find_company(store, name, company_id)
    if company:
        return company, False
    if not name or not name.strip():
        raise ValueError("Company is unknown; pass --company-id or a company name")
    transliterated = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "-", transliterated.lower()).strip("-")[:48] or "company"
    company = {
        "id": safe_id(f"{slug}-{digest(_norm(name))[:8]}"),
        "name": name.strip(),
        "about": "unknown",
        "business_areas": [],
        "needs_review": True,
        "size": {
            "metric": "employees",
            "value": None,
            "as_of": None,
            "scope": "unknown",
            "source_url": None,
            "reliability": "not_disclosed",
        },
    }
    store.put("companies", company)
    store.event("company_created_from_intake", [company["id"]], {"name": company["name"]})
    return company, True


def _finish(store: Store, value: dict, snapshot: str, company_created: bool, method: str) -> dict:
    observed = store.observe_vacancy_detailed(value, "intake", snapshot)
    duplicates = sources.possible_duplicates(store, [observed["id"]])
    store.event(
        "vacancy_added",
        [observed["id"], value["company_id"]],
        {"method": method, "status": observed["status"], "possible_duplicates": len(duplicates)},
    )
    vacancy = store.get("vacancies", observed["id"])
    return {
        "vacancy_id": observed["id"],
        "status": observed["status"],
        "changed_fields": observed["fields"],
        "company_id": value["company_id"],
        "company_created": company_created,
        "content_scope": vacancy.get("content_scope"),
        "possible_duplicates": duplicates,
        "conditions": vacancy.get("conditions"),
        "snapshot": snapshot,
    }


def _base(company_id: str, market: str | None, track: str | None) -> dict:
    if market not in (None, "ru", "intl", "unknown"):
        raise ValueError("market must be ru, intl or unknown")
    if track not in (None, *TRACKS):
        raise ValueError("Unknown career track")
    value = {
        "company_id": company_id,
        "market": market or "unknown",
        "requirements": [],
        "availability": "unknown",
    }
    if track:
        value["target_track"] = track
    return value


def from_url(
    store: Store,
    url: str,
    *,
    company_id: str | None = None,
    market: str | None = None,
    track: str | None = None,
    client: httpx.Client | None = None,
) -> dict:
    url = canonical_url(url.strip())
    own = client is None
    client = client or httpx.Client(timeout=25, follow_redirects=False, trust_env=False)
    try:
        hh = HH_VACANCY.match(url)
        target = f"https://api.hh.ru/vacancies/{hh.group(1)}" if hh else url
        try:
            status, final, body = availability.fetch_page(target, client)
        except ValueError as error:
            raise ValueError(f"Could not read the page: {error}") from None
        except httpx.HTTPError:
            raise ValueError("Could not read the page: network_error") from None
    finally:
        if own:
            client.close()
    if status in {404, 410}:
        raise ValueError(f"The posting is not available (HTTP {status})")
    if status in availability.BLOCKED_STATUSES:
        raise ValueError(
            f"The site restricted automated access (HTTP {status}); paste the text instead"
        )
    if not 200 <= status < 300:
        raise ValueError(f"The site returned HTTP {status}")
    if hh:
        item = json.loads(body)
        employer = item.get("employer") or {}
        company, created = ensure_company(store, employer.get("name"), company_id)
        snapshot = store.readable_artifact(
            "snapshots/intake", [company["name"], item.get("name")], body, ".json"
        )
        [parsed] = sources.parse_jobs(
            "hh", body, {"company_id": company["id"], "url": url, "market": market or "ru"}
        )
        value = {**_base(company["id"], market or "ru", track), **parsed, "urls": [url]}
        value["content_scope"] = "full" if item.get("description") else "excerpt"
        # The HH API reports the vacancy itself, so its archive flag is a dated signal.
        value["availability"] = "archived" if item.get("archived") else "open"
        value["status_checked_on"] = now()
        value["availability_basis"] = "hh api"
        return _finish(store, value, snapshot, created, "hh_api")
    postings = availability._job_postings(body)
    if postings:
        posting = postings[0]
        organization = posting.get("hiringOrganization") or {}
        name = organization.get("name") if isinstance(organization, dict) else None
        company, created = ensure_company(store, name, company_id)
        snapshot = store.readable_artifact(
            "snapshots/intake", [company["name"], posting.get("title")], body, ".html"
        )
        [parsed] = sources.parse_jobs(
            "corporate",
            f'<script type="application/ld+json">{json.dumps(posting)}</script>',
            {"company_id": company["id"], "url": final, "market": market or "unknown"},
        )
        value = {
            **_base(company["id"], market, track),
            **parsed,
            "id": f"intake-{digest(url)[:20]}",
            "provider": "intake",
            "urls": sorted({url, canonical_url(final)}),
        }
        value.pop("status_checked_on", None)
        return _finish(store, value, snapshot, created, "jsonld")
    title = _page_title(body)
    text = _visible_text(body)
    if not title or len(text) < 200:
        raise ValueError("The page has no readable vacancy text; paste the text instead")
    company = find_company(store, None, company_id) if company_id else None
    if not company:
        raise ValueError(
            "The page does not name the employer in a structured way; pass --company-id"
        )
    snapshot = store.readable_artifact("snapshots/intake", [company["name"], title], body, ".html")
    value = {
        **_base(company["id"], market, track),
        "id": f"intake-{digest(url)[:20]}",
        "provider": "intake",
        "title": title,
        "location": "unknown",
        "urls": sorted({url, canonical_url(final)}),
        "text": text,
        "content_scope": "page_text",
        "conditions": vacancy_fields.from_posting(text, None, "", "page_text"),
    }
    return _finish(store, value, snapshot, False, "page_text")


def from_text(
    store: Store,
    text: str,
    *,
    title: str | None = None,
    company_name: str | None = None,
    company_id: str | None = None,
    url: str | None = None,
    location: str | None = None,
    market: str | None = None,
    track: str | None = None,
) -> dict:
    if not isinstance(text, str) or len(text.strip()) < 40 or len(text) > MAX_TEXT:
        raise ValueError("Paste the vacancy text (40 to 200000 characters)")
    meta, body = descriptions.parse_posting(text)
    title = (title or meta.get("title") or "").strip()
    if not title:
        raise ValueError("Vacancy title is required (pass it or start the text with 'Title:')")
    company, created = ensure_company(store, company_name or meta.get("company"), company_id)
    link = url or meta.get("url")
    urls = [canonical_url(link.strip())] if link else []
    location = (location or meta.get("location") or "unknown").strip()
    snapshot = store.readable_artifact("snapshots/intake", [company["name"], title], text, ".md")
    value = {
        **_base(company["id"], market, track),
        "id": f"intake-{digest(urls[0] if urls else [company['id'], title, body[:2000]])[:20]}",
        "provider": "intake",
        "title": sources.plain(title),
        "location": location,
        "urls": urls,
        "text": body,
        "content_scope": "full",
        "conditions": vacancy_fields.from_posting(body, meta, location, "pasted_text"),
    }
    return _finish(store, value, snapshot, created, "text")
