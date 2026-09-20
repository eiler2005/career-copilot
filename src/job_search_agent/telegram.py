"""Offline, bounded Telegram exports. Channel posts are leads, never live job checks."""

from __future__ import annotations

import json
import re
from datetime import datetime
from urllib.parse import urlsplit

from . import intake, sources, vacancy_fields
from .core import CONTENT_RANK, Store, canonical_url, digest, now

MAX_BYTES = 10_000_000
MAX_MESSAGES = 1000
ROLE = re.compile(
    r"(?i)\b(engineer|ingenieur|ingénieur|developer|manager|director|lead|head|architect|scientist|chief|cto|cpo|ceo|cfo|vp|"
    r"инженер\w*|разработчик\w*|менеджер\w*|руководител\w*|директор\w*|архитектор\w*)\b"
)


def _timestamp(value: object, *, optional: bool = False) -> str | None:
    if optional and value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("Telegram message date must be an ISO timestamp")  # noqa: TRY004
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        raise ValueError("Telegram message date must be an ISO timestamp") from None
    if parsed.tzinfo is None:
        raise ValueError("Telegram message timestamp must include a timezone")
    return value


def parse_export(raw: bytes) -> tuple[dict, list[dict]]:
    """Validate all input before journal writes; preserve raw text and link evidence."""
    if len(raw) > MAX_BYTES:
        raise ValueError("Telegram export exceeds 10 MB")
    data = json.loads(raw)
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise ValueError("Expected Telegram export schema_version 1")
    channel = data.get("channel")
    if not isinstance(channel, dict) or not re.fullmatch(r"-?\d+", str(channel.get("id", ""))):
        raise ValueError("Telegram export requires a stable numeric channel id")
    username = channel.get("username")
    if not isinstance(username, str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{3,31}", username):
        raise ValueError("Only exports of public channels with a username are supported")
    messages = data.get("messages")
    if not isinstance(messages, list) or len(messages) > MAX_MESSAGES:
        raise ValueError("Telegram export must contain at most 1000 messages")
    result = {}
    for item in messages:
        if not isinstance(item, dict) or type(item.get("id")) is not int or item["id"] < 1:
            raise ValueError("Telegram message requires a positive integer id")
        text = item.get("text")
        if not isinstance(text, str) or len(text) > 200_000:
            raise ValueError("Telegram message text is invalid or too large")
        date = _timestamp(item.get("date"))
        edit_date = _timestamp(item.get("edit_date"), optional=True)
        links = item.get("outbound_links", [])
        if not isinstance(links, list) or any(not isinstance(link, str) for link in links):
            raise ValueError("Telegram outbound_links must be a string array")
        links = sorted(set(links + re.findall(r"https?://[^\s<>]+", text)))
        # Keep unrecognized schemes only in original bytes, never as clickable links.
        links = sorted(
            {
                canonical_url(link.rstrip(".,);]"))
                for link in links
                if link.startswith(("http://", "https://"))
            }
        )
        title = item.get("title")
        employer = item.get("company_name")
        for field in (title, employer):
            if field is not None and (not isinstance(field, str) or len(field) > 250):
                raise ValueError("Telegram title/company_name must be short strings")
        title = (title or "").strip()
        employer = (employer or "").strip()
        vacancy_evidence = bool(
            employer
            or re.search(
                r"(?im)^(?:company|employer|компания|работодатель)\s*:|#(?:vacancy|вакансия)\b",
                text,
            )
        )
        if not title:
            for line in text.splitlines()[:5]:
                line = line.strip().strip("#* ")
                match = re.match(r"(?i)^(?:title|role|позиция|вакансия)\s*:\s*(.+)$", line)
                if match:
                    title = match[1][:250]
                    break
                if (
                    vacancy_evidence
                    and len(line) <= 160
                    and ROLE.search(line)
                    and not re.search(r"https?://", line)
                ):
                    title = line
                    break
        if "company_name" not in item:
            match = re.search(
                r"(?im)^(?:company|employer|компания|работодатель)\s*:\s*([^\n]+)$", text
            )
            employer = match[1].strip()[:250] if match else ""
        job_url = item.get("job_url")
        if job_url:
            job_url = canonical_url(job_url)
            if urlsplit(job_url).hostname in {"t.me", "telegram.me"} or urlsplit(
                job_url
            ).path.lower() in {"", "/jobs", "/careers", "/vacancies"}:
                raise ValueError("job_url must identify an explicitly reviewed employer vacancy")
        skip_reason = item.get("skip_reason")
        if skip_reason is not None and (not isinstance(skip_reason, str) or len(skip_reason) > 250):
            raise ValueError("skip_reason must be a short review reason")
        value = {
            "message_id": item["id"],
            "date": date,
            "edit_date": edit_date,
            "text": text,
            "title": title,
            "company_name": employer,
            "permalink": f"https://t.me/{username}/{item['id']}",
            "outbound_links": links,
            "job_url": job_url,
            "skip_reason": skip_reason,
        }
        previous = result.get(item["id"])
        if previous and previous != value:
            raise ValueError("Conflicting versions of one message in Telegram export")
        result[item["id"]] = value
    return data, list(result.values())


def import_export(store: Store, raw: bytes) -> dict:
    data, messages = parse_export(raw)
    key = "telegram-import-" + digest(raw)[:24]
    previous = store.get("telegram_imports", key)
    if previous:
        return {**previous, "replayed": True}
    own = not store.db.in_transaction
    if own:
        store.db.execute("BEGIN IMMEDIATE")
    try:
        channel = data["channel"]
        source_id = "telegram-" + str(channel["id"])
        snapshot = store.readable_artifact("snapshots/telegram", [source_id], raw, ".json")
        result = {
            "id": key,
            "source_id": source_id,
            "snapshot": snapshot,
            "imported_at": now(),
            "coverage": data.get("coverage", {"complete": False}),
            "observed_total": len(messages),
            "new": [],
            "changed": [],
            "unchanged": [],
            "skipped": [],
            "replayed": False,
        }
        for message in messages:
            external = f"{channel['id']}-{message['message_id']}"
            post_id = "telegram-" + external
            if message["skip_reason"] or not message["title"]:
                result["skipped"].append(
                    {
                        "message_id": message["message_id"],
                        "reason": message["skip_reason"] or "title_unresolved",
                    }
                )
                continue
            # Bind later edits to the resolved posting, even when another source owned its ID.
            binding = store.get("telegram_posts", post_id)
            old = store.get("vacancies", binding["vacancy_id"]) if binding else None
            if old:
                company = store.get("companies", old["company_id"])
            elif message["company_name"]:
                company, _ = intake.ensure_company(store, message["company_name"])
            else:
                company = {
                    "id": "unknown-" + post_id,
                    "name": "Unknown employer",
                    "needs_review": True,
                    "about": "unknown",
                }
                store.put("companies", company)
            urls = [message["permalink"]]
            if message["job_url"] and message["company_name"]:
                urls.append(message["job_url"])
            conditions = vacancy_fields.from_posting(
                message["text"], None, "unknown", "telegram_post"
            )
            conditions["published_on"] = message["date"][:10]
            value = {
                "id": old["id"] if old else post_id,
                "external_id": external,
                "company_id": company["id"],
                "provider": "telegram",
                "title": message["title"],
                "text": message["text"],
                "urls": urls,
                "availability": "unknown",
                "location": "unknown",
                "market": "unknown",
                "content_scope": "excerpt",
                "requirements": [],
                "conditions": conditions,
                "telegram": {"channel": channel, **message},
                "needs_review": True,
            }
            canonical = old
            if canonical is None:
                matches = [
                    v
                    for v in store.all("vacancies")
                    if v["company_id"] == company["id"] and set(v.get("urls", [])) & set(urls)
                ]
                if len(matches) == 1:
                    canonical = matches[0]
            if canonical and CONTENT_RANK.get(canonical.get("content_scope", "full"), 3) > 1:
                # A channel excerpt cannot erase established official fields. Its original
                # claims remain inspectable in telegram and the immutable observation.
                for field in (
                    "title",
                    "market",
                    "location",
                    "provider",
                    "external_id",
                    "conditions",
                    "needs_review",
                ):
                    if field in canonical:
                        value[field] = canonical[field]
                    elif field in {"needs_review", "external_id"}:
                        value.pop(field, None)
            version_at = message["edit_date"] or message["date"]
            stale = bool(
                binding
                and binding.get("version_at")
                and datetime.fromisoformat(version_at)
                < datetime.fromisoformat(binding["version_at"])
            )
            observed = store.observe_vacancy_detailed(value, source_id, snapshot, replay=stale)
            if not stale:
                store.put(
                    "telegram_posts",
                    {"id": post_id, "vacancy_id": observed["id"], "version_at": version_at},
                )
            result[observed["status"]].append(observed["id"])
        collection = sources.record_run(
            store,
            {
                "new": result["new"],
                "changed": [{"id": key} for key in result["changed"]],
                "unchanged": len(result["unchanged"]),
                "errors": [],
                "screened_out": len(result["skipped"]),
            },
            result["imported_at"],
            [source_id],
        )
        result["collection_run_id"] = collection["id"]
        store.put(
            "source_health",
            {
                "id": source_id,
                "status": "imported",
                "route": "offline_export",
                "last_attempt": result["imported_at"],
                "count": len(messages) - len(result["skipped"]),
                "observed_total": len(messages),
                "coverage": result["coverage"],
                "snapshot": snapshot,
            },
        )
        store.put("telegram_imports", result, immutable=True)
        store.event(
            "telegram_export_imported", [key], {"source_id": source_id, "snapshot": snapshot}
        )
        if own:
            store.db.execute("COMMIT")
        return result
    except Exception:
        if own:
            store.db.execute("ROLLBACK")
        raise
