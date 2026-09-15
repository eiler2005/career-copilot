"""A local, read-only HTTP view over an existing private journal.

The CLI's :class:`Store` deliberately creates and upgrades its SQLite schema.  This
module must not use it: a dashboard request is a read-only SQLite connection with a
single transaction, so it observes a coherent WAL snapshot without changing the
workspace.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import os
import re
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path, PurePosixPath
from urllib.parse import quote, unquote, urlsplit

from .core import safe_id, validate_home

ALLOWED_KINDS = frozenset(
    {
        "activities",
        "activity_events",
        "assessments",
        "companies",
        "company_dossiers",
        "cover_letters",
        "current_assessments",
        "employer_responses",
        "events",
        "interview_feedback",
        "interview_plans",
        "interview_practices",
        "imports",
        "interview_progress",
        "learning",
        "legacy_files",
        "observations",
        "packages",
        "source_health",
        "source_settings",
        "submissions",
        "text_revisions",
        "vacancies",
    }
)

WORKSPACE_GROUPS = {
    "companies": ("companies", "company_dossiers"),
    "vacancies": ("vacancies", "assessments", "current_assessments", "observations"),
    "documents": ("packages", "cover_letters", "text_revisions"),
    "legacy_files": ("legacy_files",),
    "activities": ("activities", "activity_events"),
    "preparations": (
        "learning",
        "interview_plans",
        "interview_practices",
        "interview_feedback",
        "interview_progress",
    ),
    "sources": ("source_health", "source_settings"),
    "history": ("events", "submissions", "employer_responses", "imports"),
}

COUNTRY_NAMES = {
    "argentina": "Argentina",
    "australia": "Australia",
    "austria": "Austria",
    "belarus": "Belarus",
    "belgium": "Belgium",
    "brazil": "Brazil",
    "bulgaria": "Bulgaria",
    "canada": "Canada",
    "chile": "Chile",
    "china": "China",
    "colombia": "Colombia",
    "croatia": "Croatia",
    "cyprus": "Cyprus",
    "czech republic": "Czech Republic",
    "czechia": "Czech Republic",
    "denmark": "Denmark",
    "estonia": "Estonia",
    "finland": "Finland",
    "france": "France",
    "germany": "Germany",
    "greece": "Greece",
    "hungary": "Hungary",
    "india": "India",
    "indonesia": "Indonesia",
    "ireland": "Ireland",
    "israel": "Israel",
    "italy": "Italy",
    "japan": "Japan",
    "kazakhstan": "Kazakhstan",
    "latvia": "Latvia",
    "lithuania": "Lithuania",
    "luxembourg": "Luxembourg",
    "malaysia": "Malaysia",
    "mexico": "Mexico",
    "netherlands": "Netherlands",
    "new zealand": "New Zealand",
    "norway": "Norway",
    "philippines": "Philippines",
    "poland": "Poland",
    "portugal": "Portugal",
    "romania": "Romania",
    "russia": "Russia",
    "russian federation": "Russia",
    "serbia": "Serbia",
    "singapore": "Singapore",
    "slovakia": "Slovakia",
    "slovenia": "Slovenia",
    "south africa": "South Africa",
    "south korea": "South Korea",
    "spain": "Spain",
    "sweden": "Sweden",
    "switzerland": "Switzerland",
    "thailand": "Thailand",
    "turkey": "Turkey",
    "ukraine": "Ukraine",
    "united arab emirates": "United Arab Emirates",
    "united kingdom": "United Kingdom",
    "united states": "United States",
    "vietnam": "Vietnam",
    "россия": "Russia",
}
COUNTRY_ALIASES = {
    "uae": "United Arab Emirates",
    "uk": "United Kingdom",
    "u.k.": "United Kingdom",
    "us": "United States",
    "u.s.": "United States",
    "usa": "United States",
    "u.s.a.": "United States",
}
REMOTE_WORDS = re.compile(r"\b(remote|distributed|удал[её]н\w*)\b", re.IGNORECASE)
HYBRID_WORDS = re.compile(r"\b(hybrid|гибрид\w*)\b", re.IGNORECASE)
ONSITE_WORDS = re.compile(r"\b(on[ -]?site|in[ -]?office|офис\w*)\b", re.IGNORECASE)
WORK_MODE_PARENS = re.compile(
    r"\(\s*(?:remote|distributed|hybrid|on[ -]?site|in[ -]?office|удал[её]н\w*|гибрид\w*|офис\w*)\s*\)",
    re.IGNORECASE,
)
ARTIFACT_DIRECTORIES = frozenset(
    {
        "activities",
        "activity-artifacts",
        "evidence",
        "learning",
        "legacy",
        "packages",
        "reviews",
        "snapshots",
    }
)
ARTIFACT_SUFFIXES = frozenset(
    {
        ".csv",
        ".docx",
        ".html",
        ".htm",
        ".jpeg",
        ".jpg",
        ".json",
        ".md",
        ".odt",
        ".pdf",
        ".png",
        ".rtf",
        ".svg",
        ".tex",
        ".txt",
        ".webp",
        ".xml",
    }
)
KNOWN_CITY_LOCATIONS = {
    ("москва",): ("Russia", "Москва"),
    ("moscow",): ("Russia", "Moscow"),
    ("paris",): ("France", "Paris"),
    ("seattle",): ("United States", "Seattle"),
    ("new york", "ny"): ("United States", "New York"),
    ("new york",): ("United States", "New York"),
    ("mountain view", "ca"): ("United States", "Mountain View"),
    ("mountain view",): ("United States", "Mountain View"),
    ("redmond", "wa"): ("United States", "Redmond"),
    ("redmond",): ("United States", "Redmond"),
    ("london", "england"): ("United Kingdom", "London"),
    ("greater london", "england"): ("United Kingdom", "London"),
    ("london",): ("United Kingdom", "London"),
    ("san francisco", "ca"): ("United States", "San Francisco"),
    ("san francisco",): ("United States", "San Francisco"),
    ("santa clara",): ("United States", "Santa Clara"),
    ("bellevue", "wa"): ("United States", "Bellevue"),
    ("bellevue",): ("United States", "Bellevue"),
    ("foster city", "ca"): ("United States", "Foster City"),
    ("foster city",): ("United States", "Foster City"),
    ("abu dhabi", "abu dhabi emirate"): ("United Arab Emirates", "Abu Dhabi"),
    ("abu dhabi",): ("United Arab Emirates", "Abu Dhabi"),
    ("dubai",): ("United Arab Emirates", "Dubai"),
    ("dubai", "dubai"): ("United Arab Emirates", "Dubai"),
    ("singapore",): ("Singapore", "Singapore"),
    ("hong kong sar",): ("Hong Kong", "Hong Kong"),
}
KNOWN_JURISDICTIONS = frozenset({("hong kong sar",)})
LOOPBACK_HOSTS = frozenset({"localhost", "127.0.0.1", "[::1]"})
HOSTNAME = re.compile(
    r"(?=.{1,253}$)[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)*"
)
ALLOWED_HOSTS_ENV = "AJH_DASHBOARD_ALLOWED_HOSTS"


def allowed_hosts(values: list[str] | tuple[str, ...] = ()) -> frozenset[str]:
    """Return loopback names plus explicitly configured reverse-proxy hostnames.

    A public hostname is accepted only when an operator names it, so DNS rebinding
    protection stays on for every other Host header.
    """
    names = set(LOOPBACK_HOSTS)
    for value in values:
        for item in value.split(","):
            name = item.strip().rstrip(".").casefold()
            if not name:
                continue
            if not HOSTNAME.fullmatch(name) or name.replace(".", "").isdecimal():
                raise ValueError("Allowed dashboard hosts must be DNS hostnames without ports")
            names.add(name)
    return frozenset(names)


def _normalise_location(value: object) -> str | None:
    if isinstance(value, str):
        value = value.strip()
        return value or None
    if isinstance(value, dict):
        for key in ("raw", "display", "name", "location"):
            if isinstance(value.get(key), str) and value[key].strip():
                return value[key].strip()
    return None


def _country(value: str) -> str | None:
    key = re.sub(r"\s+", " ", value.strip().casefold())
    return COUNTRY_ALIASES.get(key) or COUNTRY_NAMES.get(key)


def _explicit_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


def _location_parts(raw: str) -> list[str]:
    without_modes = WORK_MODE_PARENS.sub("", raw)
    without_modes = REMOTE_WORDS.sub("", without_modes)
    return [part.strip() for part in re.split(r"[,;]", without_modes) if part.strip()]


def location_display(value: dict) -> dict[str, str | None]:
    """Return only unambiguous, presentation-only location information.

    A city is inferred only when an explicit country follows it.  A lone city,
    state, region, or a multi-location list is deliberately left unknown.
    """
    structured = value.get("location") if isinstance(value.get("location"), dict) else {}
    raw = _normalise_location(value.get("location"))
    explicit_country = _explicit_text(value.get("country")) or _explicit_text(
        structured.get("country")
    )
    country = _country(explicit_country) if explicit_country else None
    country = country or explicit_country
    city = _explicit_text(value.get("city")) or _explicit_text(structured.get("city"))
    if raw:
        parts = _location_parts(raw)
        inferred_country = _country(parts[-1]) if parts else None
        recognized_countries = {_country(part) for part in parts if _country(part)}
        if len(recognized_countries) > 1:
            inferred_country = None
        if country is None:
            country = inferred_country
        location_parts = parts[:-1] if inferred_country else parts
        location_key = tuple(part.casefold() for part in location_parts)
        known = KNOWN_CITY_LOCATIONS.get(location_key)
        has_country_scope = (inferred_country or country) == known[0] if known else False
        is_state_scoped = len(location_key) > 1
        is_russia_market = value.get("market") == "ru" and known and known[0] == "Russia"
        is_jurisdiction = location_key in KNOWN_JURISDICTIONS
        if (
            city is None
            and known
            and (has_country_scope or is_state_scoped or is_russia_market or is_jurisdiction)
            and (country is None or country == known[0])
        ):
            country, city = known

    work_mode = value.get("work_mode")
    remote_value = value.get("remote")
    mode = "unknown"
    explicit = work_mode if isinstance(work_mode, str) else remote_value
    if isinstance(explicit, bool):
        mode = "remote" if explicit else "onsite"
    elif isinstance(explicit, str):
        lowered = explicit.casefold().strip()
        if lowered in {"remote", "hybrid", "onsite", "on-site", "in-office"}:
            mode = "onsite" if lowered in {"on-site", "in-office"} else lowered
    if mode == "unknown" and raw:
        if HYBRID_WORDS.search(raw):
            mode = "hybrid"
        elif REMOTE_WORDS.search(raw):
            mode = "remote"
        elif ONSITE_WORDS.search(raw):
            mode = "onsite"
    return {"raw": raw, "country": country, "city": city, "remote": mode}


LOCAL_PATH = re.compile(
    r"^(?:~/|/(?:Users|home|private|var/folders|tmp|root|opt|srv|mnt|Volumes)/|[A-Za-z]:\\)"
)
SOURCE_SETTING_FIELDS = (
    "id",
    "company_id",
    "company_name",
    "provider",
    "board",
    "market",
    "enabled",
    "interval_seconds",
    "max_pages",
    "include_title",
    "source_verified_url",
)


def redact_local_paths(value: object) -> object:
    """Hide operator filesystem layout; keep the file name so the reference stays useful."""
    if isinstance(value, str):
        if LOCAL_PATH.match(value) and "\n" not in value:
            name = PurePosixPath(value.replace("\\", "/")).name
            return f"[local]/{name}" if name else "[local]"
        return value
    if isinstance(value, list):
        return [redact_local_paths(item) for item in value]
    if isinstance(value, dict):
        return {key: redact_local_paths(item) for key, item in value.items()}
    return value


def _record(kind: str, payload: dict, row_id: str) -> dict:
    payload = redact_local_paths(payload)
    return {
        "id": payload.get("id", row_id),
        "kind": kind,
        "payload": payload,
        "display": {"location": location_display(payload)},
    }


def _mark_superseded_assessments(records: list[dict]) -> None:
    """Flag older assessments of the same vacancy and track; the newest stays current."""
    newest: dict[tuple[str, str], dict] = {}
    for record in records:
        if record["kind"] != "assessments":
            continue
        payload = record["payload"]
        key = (str(payload.get("vacancy_id")), str(payload.get("track")))
        stamp = str(payload.get("at") or payload.get("created_at") or "")
        record["display"]["current"] = True
        best = newest.get(key)
        if best is None or stamp > str(
            best["payload"].get("at") or best["payload"].get("created_at") or ""
        ):
            if best is not None:
                best["display"]["current"] = False
            newest[key] = record
        else:
            record["display"]["current"] = False


@dataclass(frozen=True)
class Journal:
    home: Path

    @classmethod
    def open(cls, home: str | Path) -> Journal:
        home_path = validate_home(home)
        if (
            not (home_path / "workspace.json").is_file()
            or not (home_path / "journal.sqlite").is_file()
        ):
            raise ValueError("Workspace journal is unavailable")
        return cls(home_path)

    @contextmanager
    def snapshot(self) -> Iterator[sqlite3.Connection]:
        database = self.home / "journal.sqlite"
        try:
            connection = sqlite3.connect(
                f"{database.as_uri()}?mode=ro", uri=True, timeout=10, isolation_level=None
            )
            connection.execute("PRAGMA query_only=ON")
            connection.execute("BEGIN")
            yield connection
        except sqlite3.Error as error:
            raise ValueError(
                "Read-only journal is unavailable; mount a deployment snapshot in rollback journal mode or the live journal with its SQLite WAL sidecars"
            ) from error
        finally:
            if "connection" in locals():
                connection.close()

    def source_settings(self, connection: sqlite3.Connection) -> list[dict]:
        """Configured sources with their latest health, limited to non-secret fields.

        Never-checked sources stay visible instead of disappearing from the view.
        """
        try:
            settings = json.loads((self.home / "settings.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return []
        sources = settings.get("sources") if isinstance(settings, dict) else None
        result = []
        for source in sources if isinstance(sources, list) else []:
            if not isinstance(source, dict) or not isinstance(source.get("id"), str):
                continue
            try:
                safe_id(source["id"])
            except ValueError:
                continue
            payload = {key: source[key] for key in SOURCE_SETTING_FIELDS if key in source}
            health = connection.execute(
                "SELECT payload FROM records WHERE kind='source_health' AND id=?", (source["id"],)
            ).fetchone()
            if health:
                payload["health"] = json.loads(health[0])
            result.append(_record("source_settings", payload, source["id"]))
        return result

    def records(self, connection: sqlite3.Connection, kind: str) -> list[dict]:
        if kind == "source_settings":
            return self.source_settings(connection)
        if kind == "source_health":
            configured = {item["id"] for item in self.source_settings(connection)}
            return [
                record
                for record in self._stored_records(connection, kind)
                if record["id"] not in configured
            ]
        return self._stored_records(connection, kind)

    @staticmethod
    def _stored_records(connection: sqlite3.Connection, kind: str) -> list[dict]:
        return [
            _record(kind, json.loads(row[1]), row[0])
            for row in connection.execute(
                "SELECT id, payload FROM records WHERE kind=? ORDER BY id", (kind,)
            )
        ]

    def record(self, connection: sqlite3.Connection, kind: str, key: str) -> dict | None:
        if kind == "source_settings":
            return next(
                (item for item in self.source_settings(connection) if item["id"] == key), None
            )
        row = connection.execute(
            "SELECT id, payload FROM records WHERE kind=? AND id=?", (kind, key)
        ).fetchone()
        return _record(kind, json.loads(row[1]), row[0]) if row else None

    @staticmethod
    def artifacts(connection: sqlite3.Connection) -> list[dict]:
        return [
            {"path": row[0], "sha256": row[1], "bytes": row[2]}
            for row in connection.execute("SELECT path, sha256, bytes FROM artifacts ORDER BY path")
            if _eligible_artifact_path(row[0])
        ]

    def workspace(self) -> dict:
        with self.snapshot() as connection:
            grouped = {
                name: [record for kind in kinds for record in self.records(connection, kind)]
                for name, kinds in WORKSPACE_GROUPS.items()
            }
            artifacts = self.artifacts(connection)
        _mark_superseded_assessments(grouped["vacancies"])
        counts = {name: len(records) for name, records in grouped.items()}
        return {
            "meta": {
                "title": "Private career workspace",
                "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
                "journal_updated_at": self.journal_updated_at(),
                "counts": counts,
            },
            **grouped,
            "artifacts": artifacts,
        }

    def journal_updated_at(self) -> str | None:
        """Last write to the journal or its WAL, so a remote snapshot shows its age."""
        times = []
        for name in ("journal.sqlite", "journal.sqlite-wal"):
            try:
                times.append((self.home / name).stat().st_mtime)
            except OSError:
                continue
        if not times:
            return None
        return datetime.fromtimestamp(max(times), UTC).isoformat(timespec="seconds")

    def healthy(self) -> bool:
        with self.snapshot() as connection:
            connection.execute("SELECT 1 FROM records LIMIT 1").fetchone()
            connection.execute("SELECT 1 FROM artifacts LIMIT 1").fetchone()
        return True

    def artifact(self, relative: str) -> tuple[Path, int] | None:
        if not _eligible_artifact_path(relative):
            return None
        with self.snapshot() as connection:
            row = connection.execute(
                "SELECT sha256, bytes FROM artifacts WHERE path=?", (relative,)
            ).fetchone()
        if not row:
            return None
        candidate = self.home.joinpath(*PurePosixPath(relative).parts)
        if any((self.home / part).is_symlink() for part in _parents(relative)):
            return None
        try:
            resolved = candidate.resolve(strict=True)
        except OSError:
            return None
        if not resolved.is_relative_to(self.home) or not resolved.is_file():
            return None
        expected_hash, expected_bytes = row
        if resolved.stat().st_size != expected_bytes:
            return None
        with resolved.open("rb") as handle:
            current_hash = hashlib.file_digest(handle, "sha256").hexdigest()
        if current_hash != expected_hash:
            return None
        return resolved, expected_bytes


def _parents(relative: str) -> Iterator[str]:
    path = PurePosixPath(relative)
    current = Path()
    for part in path.parts:
        current /= part
        yield str(current)


def _safe_relative_path(value: str) -> bool:
    if not value or "\\" in value or any(ord(char) < 32 or ord(char) == 127 for char in value):
        return False
    path = PurePosixPath(value)
    return not path.is_absolute() and all(part not in {"", ".", ".."} for part in path.parts)


def _eligible_artifact_path(value: str) -> bool:
    if not _safe_relative_path(value):
        return False
    path = PurePosixPath(value)
    return path.parts[0] in ARTIFACT_DIRECTORIES and path.suffix.casefold() in ARTIFACT_SUFFIXES


def _content_disposition(path: Path) -> str:
    original = path.name
    suffix = re.sub(r"[^A-Za-z0-9.]", "", path.suffix.encode("ascii", "ignore").decode())
    stem = path.stem.encode("ascii", "ignore").decode()
    fallback_stem = re.sub(r"[^A-Za-z0-9_-]+", "_", stem).strip("_") or "download"
    fallback = f"{fallback_stem}{suffix}"
    return f"attachment; filename=\"{fallback}\"; filename*=UTF-8''{quote(original, safe='')}"


class DashboardHandler(BaseHTTPRequestHandler):
    server: DashboardServer
    protocol_version = "HTTP/1.1"

    def log_message(self, _format: str, *_args: object) -> None:
        """Do not put private paths, record identifiers, or source URLs into logs."""

    def do_HEAD(self) -> None:
        self._dispatch(head_only=True)

    def do_GET(self) -> None:
        self._dispatch(head_only=False)

    def do_POST(self) -> None:
        self._error(HTTPStatus.METHOD_NOT_ALLOWED)

    def _dispatch(self, *, head_only: bool) -> None:
        try:
            if not self._trusted_host():
                self._error(HTTPStatus.BAD_REQUEST)
                return
            path = urlsplit(self.path).path
            if path == "/healthz":
                self.server.journal.healthy()
                self._json({"status": "ok"}, head_only)
            elif path == "/api/workspace":
                self._json(self.server.journal.workspace(), head_only)
            elif path.startswith("/api/records/"):
                self._record(path, head_only)
            elif path.startswith("/api/artifacts/"):
                self._artifact(path, head_only)
            elif path in {"/", "/index.html"}:
                self._static("index.html", head_only)
            elif path in {"/assets/styles.css", "/assets/app.js"}:
                self._static(path.removeprefix("/assets/"), head_only)
            else:
                self._error(HTTPStatus.NOT_FOUND)
        except BrokenPipeError:
            return
        except (OSError, ValueError):
            try:
                self._error(HTTPStatus.SERVICE_UNAVAILABLE)
            except BrokenPipeError:
                return

    def _trusted_host(self) -> bool:
        """Reject DNS-rebound requests before exposing a local private response."""
        value = self.headers.get("Host", "")
        host, separator, port = value.rpartition(":")
        if value.startswith("["):
            match = re.fullmatch(r"(\[::1\])(?::(\d+))?", value)
            if not match:
                return False
            host, port = match.group(1), match.group(2) or ""
        elif not separator:
            host, port = value, ""
        if host.casefold() not in self.server.allowed_hosts:
            return False
        return not port or (port.isdecimal() and 1 <= int(port) <= 65535)

    def _record(self, path: str, head_only: bool) -> None:
        parts = path.split("/")
        if len(parts) != 5:
            self._error(HTTPStatus.NOT_FOUND)
            return
        kind, key = unquote(parts[3]), unquote(parts[4])
        if kind not in ALLOWED_KINDS:
            self._error(HTTPStatus.NOT_FOUND)
            return
        try:
            valid_key = _safe_relative_path(key) if kind == "legacy_files" else safe_id(key)
        except ValueError:
            valid_key = False
        if not valid_key:
            self._error(HTTPStatus.NOT_FOUND)
            return
        with self.server.journal.snapshot() as connection:
            record = self.server.journal.record(connection, kind, key)
        if record is None:
            self._error(HTTPStatus.NOT_FOUND)
            return
        self._json(record, head_only)

    def _artifact(self, path: str, head_only: bool) -> None:
        relative = unquote(path.removeprefix("/api/artifacts/"))
        artifact = self.server.journal.artifact(relative)
        if artifact is None:
            self._error(HTTPStatus.NOT_FOUND)
            return
        target, size = artifact
        self.send_response(HTTPStatus.OK)
        self._security_headers()
        self.send_header("Content-Type", "application/octet-stream")
        self.send_header("Content-Disposition", _content_disposition(target))
        self.send_header("Content-Length", str(size))
        self.end_headers()
        if not head_only:
            with target.open("rb") as handle:
                while chunk := handle.read(64 * 1024):
                    self.wfile.write(chunk)

    def _static(self, name: str, head_only: bool) -> None:
        target = self.server.assets / name
        if not target.is_file():
            self._error(HTTPStatus.NOT_FOUND)
            return
        content_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        data = target.read_bytes()
        self.send_response(HTTPStatus.OK)
        self._security_headers()
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        if not head_only:
            self.wfile.write(data)

    def _json(self, value: dict, head_only: bool) -> None:
        data = json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self._security_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        if not head_only:
            self.wfile.write(data)

    def _error(self, status: HTTPStatus) -> None:
        data = json.dumps({"error": status.phrase}).encode("utf-8")
        self.send_response(status)
        self._security_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        if status == HTTPStatus.METHOD_NOT_ALLOWED:
            self.send_header("Allow", "GET, HEAD")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(data)

    def _security_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        self.send_header("Pragma", "no-cache")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("X-Robots-Tag", "noindex, nofollow, noarchive")
        self.send_header(
            "Permissions-Policy", "camera=(), geolocation=(), microphone=(), payment=(), usb=()"
        )
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; base-uri 'none'; object-src 'none'; frame-ancestors 'none'; "
            "form-action 'none'; connect-src 'self'; img-src 'self' data:; "
            "script-src 'self'; style-src 'self'",
        )


class DashboardServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(
        self,
        address: tuple[str, int],
        journal: Journal,
        assets: Path,
        hosts: frozenset[str] = LOOPBACK_HOSTS,
    ):
        self.journal = journal
        self.assets = assets
        self.allowed_hosts = hosts
        super().__init__(address, DashboardHandler)


def assets_path() -> Path:
    return Path(__file__).with_name("web_assets")


def serve(
    home: str | Path,
    host: str = "127.0.0.1",
    port: int = 8080,
    hosts: frozenset[str] = LOOPBACK_HOSTS,
) -> None:
    if host not in {"127.0.0.1", "0.0.0.0"}:
        raise ValueError("Dashboard host must be 127.0.0.1 or the container bind address 0.0.0.0")
    if not 1 <= port <= 65535:
        raise ValueError("Dashboard port must be between 1 and 65535")
    with DashboardServer((host, port), Journal.open(home), assets_path(), hosts) as server:
        server.serve_forever()


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Read-only private Career Copilot dashboard")
    result.add_argument("--home", required=True, help="Explicit external private workspace")
    result.add_argument("--host", default="127.0.0.1")
    result.add_argument("--port", default=8080, type=int)
    result.add_argument(
        "--allowed-host",
        action="append",
        default=[],
        help=f"Hostname served by an authenticating reverse proxy; repeatable (or {ALLOWED_HOSTS_ENV})",
    )
    return result


def main() -> int:
    args = parser().parse_args()
    try:
        hosts = allowed_hosts([*args.allowed_host, os.environ.get(ALLOWED_HOSTS_ENV, "")])
        serve(args.home, args.host, args.port, hosts)
    except ValueError as error:
        parser().error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
