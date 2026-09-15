"""Readable, collision-safe artifact file names.

Every generated name follows one pattern inside its directory:

    <YYYY-MM-DD>-<context>-<short-sha256><suffix>

The date says when the material entered the journal, the context says what it is
(track, vacancy, original file name, review kind...) and the eight-character
content hash keeps names unique and ties them to the registered checksum. Each
path component stays well below the 255-byte limit of common file systems.
"""

from __future__ import annotations

import re
import unicodedata

MAX_COMPONENT_BYTES = 200
HASH_CHARS = 8


def slug(text: object, max_bytes: int = 60) -> str:
    """Lowercase words joined by hyphens; Cyrillic and other letters are kept."""
    value = unicodedata.normalize("NFKC", str(text or "")).casefold()
    value = re.sub(r"[^\w]+", "-", value, flags=re.UNICODE).replace("_", "-")
    value = re.sub(r"-{2,}", "-", value).strip("-")
    return truncate_bytes(value, max_bytes).strip("-")


def truncate_bytes(value: str, max_bytes: int) -> str:
    encoded = value.encode("utf-8")
    if len(encoded) <= max_bytes:
        return value
    cut = encoded[:max_bytes].decode("utf-8", errors="ignore")
    boundary = max(cut.rfind("-"), cut.rfind(" "))
    return cut[:boundary] if boundary > max_bytes // 3 else cut


def readable_name(parts: list[object], sha256: str, suffix: str, date: str | None = None) -> str:
    """Build `<date>-<parts>-<hash><suffix>` with a bounded byte length."""
    suffix = re.sub(r"[^A-Za-z0-9.]", "", suffix or "")[:10]
    tail = f"-{sha256[:HASH_CHARS]}{suffix}"
    words = [slug(part, 64) for part in parts]
    if date:
        # A context that already starts with the same date would repeat it.
        words = [
            word.removeprefix(date).lstrip("-") if word.startswith(date) else word for word in words
        ]
    stem = "-".join(item for item in [date or "", *words] if item)
    budget = MAX_COMPONENT_BYTES - len(tail.encode("utf-8"))
    stem = truncate_bytes(stem, budget).strip("-") or "file"
    return f"{stem}{tail}"


def shorten_component(name: str, sha256: str) -> str:
    """Keep a readable original file name but fit it into the component budget."""
    if len(name.encode("utf-8")) <= MAX_COMPONENT_BYTES:
        return name
    match = re.match(r"^(.*?)(\.[A-Za-z0-9]{1,10})?$", name)
    stem, suffix = (match.group(1), match.group(2) or "") if match else (name, "")
    tail = f"-{sha256[:HASH_CHARS]}{suffix}"
    budget = MAX_COMPONENT_BYTES - len(tail.encode("utf-8"))
    return f"{truncate_bytes(stem, budget).rstrip(' -,.')}{tail}"


def day(timestamp: object) -> str | None:
    match = re.match(r"^(\d{4}-\d{2}-\d{2})", str(timestamp or ""))
    return match.group(1) if match else None
