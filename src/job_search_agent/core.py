"""Explicit private workspace, durable records and content-addressed evidence."""

from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

TRACKS = ("product", "technical-leadership")
FLAGSHIPS = {"openai": "gpt-6-astra", "claude": "claude-opus-5"}


def now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def encode(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)


def digest(value: bytes | Any) -> str:
    return hashlib.sha256(value if isinstance(value, bytes) else encode(value).encode()).hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def atomic_write(path: Path, value: str | bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    data = value.encode() if isinstance(value, str) else value
    fd, name = tempfile.mkstemp(prefix=".ajh-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def safe_id(value: str) -> str:
    if not re.fullmatch(r"[\w.-]{1,180}", value) or value in {".", ".."}:
        raise ValueError("Invalid identifier")
    return value


def canonical_url(url: str) -> str:
    parts = urlsplit(url)
    if parts.scheme not in {"http", "https"} or not parts.hostname or parts.username:
        raise ValueError("Expected an HTTP(S) URL without embedded credentials")
    query = [(k, v) for k, v in parse_qsl(parts.query) if not k.startswith("utm_")]
    return urlunsplit(
        (parts.scheme, parts.netloc.lower(), parts.path.rstrip("/"), urlencode(sorted(query)), "")
    )


def public_root() -> Path:
    return Path(__file__).resolve().parents[2]


def validate_home(value: str | Path) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        raise ValueError("Workspace must be an explicit absolute path")
    path = path.resolve()
    if path in {Path("/"), Path.home()} or len(path.parts) < 3:
        raise ValueError("Refusing a broad workspace root")
    root = public_root()
    if path == root or path.is_relative_to(root) or root.is_relative_to(path):
        raise ValueError("Private workspace must be separate from the public source tree")
    return path


def init_home(value: str | Path, *, demo: bool = False) -> Path:
    home = validate_home(value)
    if home.exists() and any(home.iterdir()):
        raise ValueError("Initialization requires a new or empty directory")
    home.mkdir(parents=True, mode=0o700, exist_ok=True)
    atomic_write(home / "workspace.json", encode({"schema_version": 1, "synthetic": demo}))
    atomic_write(
        home / "settings.json",
        encode(
            {
                "sources": [],
                "policy": {
                    "bigtech_company_ids": [],
                    "company_levels": {},
                    "russia_director_only": False,
                    "market_effort": {},
                },
                "max_requests_per_run": 20,
                "weeks": 6,
                "hours_per_week": 6,
                "model_routing": FLAGSHIPS,
            }
        ),
    )
    atomic_write(
        home / "facts.json",
        encode(
            {
                "schema_version": 1,
                "candidate": {"name": "", "contacts": []},
                "facts": [],
                "profiles": {},
            }
        ),
    )
    return home


class Store:
    def __init__(self, home: str | Path):
        self.activity_id: str | None = None
        self.home = validate_home(home)
        if not (self.home / "workspace.json").is_file():
            raise ValueError("Workspace is not initialized; use ajh init --home ABSOLUTE_PATH")
        self.db = sqlite3.connect(self.home / "journal.sqlite", timeout=30, isolation_level=None)
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS records (
              kind TEXT NOT NULL, id TEXT NOT NULL, payload TEXT NOT NULL,
              PRIMARY KEY(kind,id));
            CREATE TABLE IF NOT EXISTS artifacts (
              path TEXT PRIMARY KEY, sha256 TEXT NOT NULL, bytes INTEGER NOT NULL);
            CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        """)

    def close(self) -> None:
        self.db.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    @property
    def settings(self) -> dict:
        return read_json(self.home / "settings.json")

    @property
    def facts(self) -> dict:
        return read_json(self.home / "facts.json")

    def path(self, relative: str) -> Path:
        path = (self.home / relative).resolve()
        if not path.is_relative_to(self.home):
            raise ValueError("Artifact escapes private workspace")
        return path

    def get(self, kind: str, key: str) -> dict | None:
        row = self.db.execute(
            "SELECT payload FROM records WHERE kind=? AND id=?", (kind, key)
        ).fetchone()
        return json.loads(row[0]) if row else None

    def all(self, kind: str) -> list[dict]:
        return [
            json.loads(row[0])
            for row in self.db.execute(
                "SELECT payload FROM records WHERE kind=? ORDER BY id", (kind,)
            )
        ]

    def put(self, kind: str, value: dict, *, immutable: bool = False) -> None:
        old = self.get(kind, value["id"])
        if immutable and old and old != value:
            raise ValueError(f"Immutable {kind} conflict")
        self.db.execute(
            "INSERT INTO records VALUES(?,?,?) ON CONFLICT(kind,id) "
            "DO UPDATE SET payload=excluded.payload",
            (kind, value["id"], encode(value)),
        )

    def event(self, action: str, entities: list[str], details: dict) -> str:
        value = {"type": action, "entity_ids": entities, "details": details}
        key = "evt-" + digest(value)[:24]
        if not self.get("events", key):
            self.put("events", {"id": key, "at": now(), **value}, immutable=True)
        if self.activity_id:
            link = {"activity_id": self.activity_id, "event_id": key}
            link_id = "link-" + digest(link)[:24]
            if not self.get("activity_events", link_id):
                self.put("activity_events", {"id": link_id, "at": now(), **link}, immutable=True)
        return key

    def artifact_intact(self, relative: str) -> bool:
        row = self.db.execute(
            "SELECT sha256,bytes FROM artifacts WHERE path=?", (relative,)
        ).fetchone()
        path = self.path(relative)
        return bool(
            row
            and path.is_file()
            and path.stat().st_size == row[1]
            and digest(path.read_bytes()) == row[0]
        )

    def insertion_order(self, kind: str) -> list[dict]:
        """Stable insertion chronology for immutable records predating explicit pointers."""
        return [
            json.loads(row[0])
            for row in self.db.execute(
                "SELECT payload FROM records WHERE kind=? ORDER BY rowid", (kind,)
            )
        ]

    def artifact(self, relative: str, data: str | bytes) -> str:
        value = data.encode() if isinstance(data, str) else data
        path = self.path(relative)
        if path.exists() and path.read_bytes() != value:
            raise ValueError("Immutable artifact conflict; create a new version")
        if not path.exists():
            atomic_write(path, value)
        self.db.execute(
            "INSERT OR IGNORE INTO artifacts VALUES(?,?,?)", (relative, digest(value), len(value))
        )
        return relative

    def observe_vacancy(
        self, value: dict, source_id: str, snapshot: str, *, replay: bool = False
    ) -> str:
        urls = [canonical_url(u) for u in value.get("urls", [])]
        candidates = [
            v
            for v in self.all("vacancies")
            if v["company_id"] == value["company_id"]
            and (
                v["id"] == value["id"]
                or set(v.get("urls", [])) & set(urls)
                or (
                    value.get("external_id")
                    and v.get("external_id") == value["external_id"]
                    and v.get("provider") == value.get("provider")
                )
            )
        ]
        if len(candidates) > 1:
            raise ValueError("Ambiguous vacancy identity; resolve aliases manually")
        old = candidates[0] if candidates else None
        key = old["id"] if old else safe_id(value["id"])
        observation = {
            "id": "obs-" + digest([key, source_id, snapshot, value])[:24],
            "vacancy_id": key,
            "source_id": source_id,
            "snapshot": snapshot,
            "value": value,
        }
        self.put("observations", observation, immutable=True)
        if replay and old:
            return key
        merged = {
            **(old or {}),
            **value,
            "id": key,
            "first_seen": (old or {}).get("first_seen", now()),
            "last_seen": now(),
            "urls": sorted(set((old or {}).get("urls", []) + urls)),
        }
        if old:
            for field in ("decision", "assessments", "review_status", "requirements", "level"):
                if field in old:
                    merged[field] = old[field]
            if not value.get("text") and old.get("text"):
                merged["text"] = old["text"]
                merged["content_scope"] = old.get("content_scope", "full")
        merged["source_observation"] = observation["id"]
        self.put("vacancies", merged)
        return key


def import_legacy(store: Store, registry: Path, *, dry_run: bool = False) -> dict:
    registry = registry.resolve()
    base = registry.parent.parent
    raw = registry.read_bytes()
    data = json.loads(raw)
    if data.get("schema_version") != 2:
        raise ValueError("Only the documented v2 legacy registry is supported")
    files: dict[str, bytes] = {}
    missing: list[str] = []

    def gather(value: Any):
        if isinstance(value, dict):
            for item in value.values():
                gather(item)
        elif isinstance(value, list):
            for item in value:
                gather(item)
        elif isinstance(value, str) and value.startswith(("ai-job-search/", "research/")):
            path = (base / value).resolve()
            if not path.is_relative_to(base):
                raise ValueError("Legacy path escapes source root")
            if path.is_file():
                files[value] = path.read_bytes()

    gather(data)
    for package in data["packages"]:
        for version in package["versions"]:
            for label, name in version["files"].items():
                if name not in files:
                    missing.append(name)
                elif digest(files[name]) != version["sha256"].get(label):
                    raise ValueError("Legacy document checksum mismatch")
    counts = {kind: len(data[kind]) for kind in ("companies", "vacancies", "packages", "events")}
    counts["versions"] = sum(len(p["versions"]) for p in data["packages"])
    result = {
        "counts": counts,
        "files": len(files),
        "missing": missing,
        "registry_sha256": digest(raw),
        "dry_run": dry_run,
    }
    if missing:
        raise ValueError(f"Legacy import blocked: {len(missing)} required documents missing")
    for kind in ("companies", "vacancies", "packages", "events"):
        for value in data[kind]:
            existing = store.get(kind, value["id"])
            if existing and existing != value:
                raise ValueError(
                    "Import would overwrite newer data; explicit reconciliation required"
                )
    if dry_run:
        return result
    store.db.execute("BEGIN IMMEDIATE")
    try:
        store.artifact("imports/" + digest(raw) + ".json", raw)
        for name, body in files.items():
            relative = "legacy/" + name
            store.artifact(relative, body)
            store.put(
                "legacy_files",
                {"id": name, "path": relative, "sha256": digest(body)},
                immutable=True,
            )
        for kind in ("companies", "vacancies", "packages", "events"):
            for value in data[kind]:
                store.put(kind, value, immutable=True)
        store.put("imports", {"id": digest(raw), **result}, immutable=True)
        store.event("legacy_imported", [], {"registry_sha256": digest(raw), "counts": counts})
        store.db.execute("COMMIT")
    except Exception:
        store.db.execute("ROLLBACK")
        raise
    return result
