"""Optional read-only Telegram collector using an existing external Telethon session.

Run with Python where Telethon and the existing session already live. No login,
session writes, joining, messages, read acknowledgements or media downloads.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sqlite3
from datetime import UTC, datetime
from pathlib import Path


async def collect(client, channel: str, limit: int, since: datetime | None) -> dict:
    if not 1 <= limit <= 1000:
        raise ValueError("limit must be between 1 and 1000")
    if since and since.tzinfo is None:
        raise ValueError("since must include a timezone")
    entity = await client.get_entity(channel)
    if not getattr(entity, "broadcast", False) or not getattr(entity, "username", None):
        raise ValueError("Only public broadcast channels are supported")
    messages = []
    scanned = 0
    reached_since = False
    async for message in client.iter_messages(entity, limit=limit):
        scanned += 1
        if since and message.date < since:
            reached_since = True
            break
        text = message.message or ""
        if not text:
            continue
        # Text URLs are also recovered by the importer. Hidden text links need entities.
        links = sorted(
            {
                item.url
                for item in (message.entities or [])
                if getattr(item, "url", None) and item.url.startswith(("https://", "http://"))
            }
        )
        messages.append(
            {
                "id": message.id,
                "date": message.date.isoformat(),
                "edit_date": message.edit_date.isoformat() if message.edit_date else None,
                "text": text,
                "outbound_links": links,
            }
        )
    return {
        "schema_version": 1,
        "exported_at": datetime.now(UTC).isoformat(),
        "channel": {"id": str(entity.id), "username": entity.username, "title": entity.title},
        "messages": messages,
        "coverage": {
            "limit": limit,
            "since": since.isoformat() if since else None,
            "scanned": scanned,
            "reached_since": reached_since,
            "complete": reached_since or scanned < limit,
        },
    }


def memory_session(path: Path):
    from telethon.crypto import AuthKey
    from telethon.sessions import MemorySession

    path = path.expanduser().resolve(strict=True)
    # SQLite's read-only URI prevents altering the source session or entity/cursor tables.
    connection = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)
    try:
        row = connection.execute(
            "SELECT dc_id, server_address, port, auth_key FROM sessions"
        ).fetchone()
    finally:
        connection.close()
    if not row or not row[3]:
        raise ValueError("Existing session has no authorization key")
    session = MemorySession()
    session.set_dc(row[0], row[1], row[2])
    session.auth_key = AuthKey(row[3])
    return session


async def run(args) -> dict:
    from telethon import TelegramClient

    client = TelegramClient(
        memory_session(args.session),
        int(os.environ["TELEGRAM_API_ID"]),
        os.environ["TELEGRAM_API_HASH"],
        receive_updates=False,
        flood_sleep_threshold=0,
        request_retries=0,
        connection_retries=0,
        auto_reconnect=False,
    )
    await client.connect()
    try:
        if not await client.is_user_authorized():
            raise ValueError("Existing session is unauthorized; no login attempted")
        return await collect(client, args.channel, args.limit, args.since)
    finally:
        await client.disconnect()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session", type=Path, required=True)
    parser.add_argument("--channel", required=True)
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--since", type=datetime.fromisoformat)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        # Validate limits before any connection. Output creation never overwrites evidence.
        if not 1 <= args.limit <= 1000 or (args.since and args.since.tzinfo is None):
            raise ValueError("Invalid bounded collection arguments")
        if args.output.exists():
            raise ValueError("Output already exists")
        result = asyncio.run(run(args))
        fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(result, handle, ensure_ascii=False, indent=2)
        return 0
    except Exception as error:  # noqa: BLE001 — redact optional provider exceptions
        # Provider exceptions can contain source/session details; never print their text.
        print(json.dumps({"error": type(error).__name__, "status": "collection_failed"}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
