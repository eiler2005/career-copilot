"""Short, quoted vacancy descriptions for the dashboard.

The excerpt is taken verbatim (whitespace and Markdown syntax normalised) from the
retained posting file, or from the research section that names the vacancy. It is
never paraphrased; the source file and section travel with it so the full text is
one click away.
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path, PurePosixPath

EXCERPT_CHARS = 360
TEXT_SUFFIXES = frozenset({".md", ".txt"})
HEADER = re.compile(
    r"^(title|company|location|url|source|salary|posted|date|employment|schedule):\s*(.*)$",
    re.IGNORECASE,
)
URL = re.compile(r"https?://\S+")


@lru_cache(maxsize=256)
def _read(path: str, mtime_ns: int, size: int) -> str:
    del mtime_ns, size  # cache key only
    return Path(path).read_text(encoding="utf-8", errors="replace")


def read_text(path: Path) -> str | None:
    try:
        stat = path.stat()
    except OSError:
        return None
    if path.suffix.casefold() not in TEXT_SUFFIXES or stat.st_size > 1_000_000:
        return None
    return _read(str(path), stat.st_mtime_ns, stat.st_size)


def plain(text: str) -> str:
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = URL.sub("", text)
    text = re.sub(r"[*_`#>|]+", " ", text)
    text = re.sub(r"^\s*[-•]\s+", "", text, flags=re.MULTILINE)
    return re.sub(r"\s+", " ", text).strip(" -–—:;,")


def excerpt(text: str, limit: int = EXCERPT_CHARS) -> str:
    text = plain(text)
    if len(text) <= limit:
        return text
    window = text[:limit]
    stop = max(window.rfind(". "), window.rfind("! "), window.rfind("? "), window.rfind("; "))
    if stop > limit * 0.55:
        return window[: stop + 1].strip()
    return window[: window.rfind(" ")].rstrip(" ,;:-") + "…"


def parse_posting(text: str) -> tuple[dict[str, str], str]:
    """Split a retained posting into header fields and body text."""
    meta: dict[str, str] = {}
    lines = text.splitlines()
    start = 0
    for index, line in enumerate(lines[:15]):
        match = HEADER.match(line.strip())
        if match:
            meta[match.group(1).casefold()] = match.group(2).strip(" ,")
            start = index + 1
        elif line.strip():
            break
    return meta, "\n".join(lines[start:]).strip()


def _tokens(payload: dict) -> list[str]:
    tokens = re.findall(r"\d{4,}", str(payload.get("id", "")))
    for url in payload.get("urls") or []:
        if isinstance(url, str):
            tokens.append(url.rstrip("/").split("?")[0])
            tokens += re.findall(r"\d{4,}", url)
    return [token for token in dict.fromkeys(tokens) if token]


def research_section(text: str, payload: dict) -> tuple[str, str] | None:
    """Find the Markdown section that mentions this vacancy's ID or posting URL."""
    lines = text.splitlines()
    for token in _tokens(payload):
        for index, line in enumerate(lines):
            if token not in line:
                continue
            if line.lstrip().startswith("|"):
                # A research table row: keep the descriptive cells, drop links and dates.
                cells = [plain(cell) for cell in line.strip().strip("|").split("|")]
                cells = [cell for cell in cells if cell and not re.fullmatch(r"[\d.\-/ ]+", cell)]
                heading = next(
                    (
                        lines[i].lstrip("# ").strip()
                        for i in range(index, -1, -1)
                        if lines[i].lstrip().startswith("#")
                    ),
                    "",
                )
                # Research tables lead with role, place and status; the substance follows.
                return heading, " · ".join(cells[3:] if len(cells) >= 4 else cells)
            start = next(
                (i for i in range(index, -1, -1) if lines[i].lstrip().startswith("#")), None
            )
            if start is None:
                continue
            level = len(lines[start]) - len(lines[start].lstrip("#"))
            end = next(
                (
                    i
                    for i in range(start + 1, len(lines))
                    if lines[i].startswith("#")
                    and len(lines[i]) - len(lines[i].lstrip("#")) <= level
                ),
                len(lines),
            )
            heading = lines[start].lstrip("# ").strip()
            body = [
                line
                for line in lines[start + 1 : end]
                if plain(line)
                and not re.match(r"^\s*[-*]\s*(canonical|url|источник|ссылка)", line, re.IGNORECASE)
            ]
            return heading, "\n".join(body)
    return None


def describe(home: Path, payload: dict, legacy: dict[str, str], artifacts: set[str]) -> dict | None:
    """Return {excerpt, path, kind, heading?, meta?} for a vacancy payload."""

    def resolve(reference: object) -> str | None:
        if not isinstance(reference, str):
            return None
        path = reference if reference in artifacts else legacy.get(reference)
        return path if path and PurePosixPath(path).suffix.casefold() in TEXT_SUFFIXES else None

    posting = resolve(payload.get("posting"))
    if posting and (text := read_text(home / posting)):
        meta, body = parse_posting(text)
        if body:
            return {
                "kind": "posting",
                "path": posting,
                "excerpt": excerpt(body),
                "meta": {
                    key: value
                    for key, value in meta.items()
                    if key in {"salary", "location", "source"} and value
                },
            }
    if isinstance(payload.get("text"), str) and payload["text"].strip():
        return {"kind": "record", "path": None, "excerpt": excerpt(payload["text"])}
    for reference in payload.get("evidence") or []:
        path = resolve(reference)
        text = read_text(home / path) if path else None
        found = research_section(text, payload) if text else None
        if found and plain(found[1]):
            body = plain(found[1])
            # Start at the substance of the role when the research names it explicitly.
            focus = re.search(r"(Мандат|Posting|Mandate|Scope|Роль|Role|Обязанности)\s*:\s*", body)
            return {
                "kind": "research",
                "path": path,
                "heading": found[0],
                "excerpt": excerpt(body[focus.end() :] if focus else body),
            }
    return None
