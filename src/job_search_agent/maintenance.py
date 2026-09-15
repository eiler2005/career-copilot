"""Journal maintenance: remove duplicate results and give artifacts readable names.

Both operations are dry runs unless `apply=True`. Applied runs are transactional
for SQLite, move files with rollback on failure, keep superseded results in the
`superseded_records` archive, and write a manifest plus an event.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path, PurePosixPath

from .core import Store, atomic_write, digest, encode, now
from .naming import MAX_COMPONENT_BYTES, day, readable_name, shorten_component
from .workflow import supersede

HASH_NAME = re.compile(r"^(?:[0-9a-f]{64}|learning-[0-9a-f]{24})$")
DEDUPE_KINDS = (
    ("assessments", "at", "current_assessments", "assessment_id"),
    ("learning", "created_at", "current_learning", "learning_id"),
)


def dedupe(store: Store, apply: bool = False) -> dict:
    """Keep the newest assessment and learning plan per vacancy and track."""
    plan = []
    for kind, stamp, pointer_kind, pointer_field in DEDUPE_KINDS:
        groups: dict[tuple, list[dict]] = {}
        for record in store.insertion_order(kind):
            groups.setdefault((record.get("vacancy_id"), record.get("track")), []).append(record)
        for (vacancy_id, track), items in groups.items():
            ordered = sorted(
                enumerate(items), key=lambda pair: (str(pair[1].get(stamp) or ""), pair[0])
            )
            keep = ordered[-1][1]
            plan.append(
                {
                    "kind": kind,
                    "vacancy_id": vacancy_id,
                    "track": track,
                    "keep": keep["id"],
                    "supersede": [item["id"] for _, item in ordered[:-1]],
                    "pointer": (pointer_kind, pointer_field),
                }
            )
    superseded = sum(len(item["supersede"]) for item in plan)
    result = {
        "applied": False,
        "superseded": superseded,
        "groups": [
            {k: v for k, v in item.items() if k != "pointer"} for item in plan if item["supersede"]
        ],
    }
    if not apply:
        return result
    store.db.execute("BEGIN IMMEDIATE")
    try:
        for item in plan:
            pointer_kind, pointer_field = item["pointer"]
            for old_id in item["supersede"]:
                old = store.get(item["kind"], old_id)
                if old:
                    supersede(
                        store,
                        item["kind"],
                        old,
                        item["keep"],
                        "duplicate result for vacancy and track",
                    )
            owner = (
                (item["vacancy_id"] or "all-vacancies")
                if item["kind"] == "learning"
                else item["vacancy_id"]
            )
            store.put(
                pointer_kind,
                {
                    "id": f"{owner}:{item['track']}",
                    "vacancy_id": item["vacancy_id"],
                    "track": item["track"],
                    pointer_field: item["keep"],
                },
            )
        if superseded:
            store.event(
                "records_deduplicated",
                [],
                {"superseded": superseded, "method": "newest-per-vacancy-track"},
            )
        store.db.execute("COMMIT")
    except Exception:
        store.db.execute("ROLLBACK")
        raise
    return {**result, "applied": True}


def _walk_strings(value: object, visit) -> object:
    if isinstance(value, str):
        return visit(value)
    if isinstance(value, list):
        return [_walk_strings(item, visit) for item in value]
    if isinstance(value, dict):
        return {visit(key): _walk_strings(item, visit) for key, item in value.items()}
    return value


def _references(store: Store) -> dict[str, list[tuple[str, dict]]]:
    """Map each string value found in records to the records containing it."""
    found: dict[str, list[tuple[str, dict]]] = {}
    for kind, payload in store.db.execute("SELECT kind, payload FROM records"):
        record = json.loads(payload)

        def visit(text: str, kind: str = kind, record: dict = record) -> str:
            found.setdefault(text, []).append((kind, record))
            return text

        _walk_strings(record, visit)
    return found


def _event_time(
    store: Store, event_type: str, detail: str | None = None, value: str | None = None
) -> str | None:
    for event in reversed(store.insertion_order("events")):
        if event.get("type") != event_type:
            continue
        if detail and (event.get("details") or {}).get(detail) != value:
            continue
        return day(event.get("at") or event.get("date"))
    return None


def _proposed_name(
    store: Store, path: str, sha: str, refs: dict, facts_sources: dict
) -> str | None:
    posix = PurePosixPath(path)
    name, suffix, stem = posix.name, posix.suffix, posix.stem
    root = posix.parts[0]
    if HASH_NAME.match(stem):
        users = refs.get(path, [])
        if root == "activity-artifacts":
            original, date = None, None
            for kind, record in users:
                for candidate in _dicts(record):
                    if candidate.get("path") == path and candidate.get("original_path"):
                        original = PurePosixPath(
                            str(candidate["original_path"]).replace("\\", "/")
                        ).stem
                date = date or day(record.get("started_at") or record.get("created_at"))
            return readable_name([original or "activity-input"], sha, suffix, date)
        if root == "evidence":
            original = facts_sources.get(path)
            label = PurePosixPath(original).stem if original else "evidence"
            return readable_name([label], sha, suffix, _event_time(store, "facts_imported"))
        if root == "learning":
            record = store.get("learning", stem) or (
                store.get("superseded_records", f"learning--{stem}") or {}
            ).get("payload")
            if record:
                parts = [record.get("track"), record.get("vacancy_id") or "all-vacancies"]
                return readable_name(parts, sha, suffix, day(record.get("created_at")))
            return readable_name(["learning-plan"], sha, suffix)
        if root == "imports":
            return readable_name(
                ["legacy-registry"],
                sha,
                suffix,
                _event_time(store, "legacy_imported", "registry_sha256", stem),
            )
        if root == "facts-history":
            date = _event_time(store, "facts_imported", "sha256", stem)
            return readable_name(
                ["facts-imported" if date else "facts-snapshot"], sha, suffix, date
            )
        if root == "reviews":
            for kind, record in users:
                if kind == "packages":
                    for version in record.get("versions", []):
                        if path in version.get("reviews", []):
                            review_kind = _review_kind(store, path)
                            parts = [record["id"], version.get("id"), review_kind]
                            return readable_name(parts, sha, suffix, day(version.get("date")))
            return readable_name(["review", _review_kind(store, path)], sha, suffix)
        if root == "snapshots":
            return readable_name(["response"], sha, suffix)
    if len(name.encode("utf-8")) > MAX_COMPONENT_BYTES:
        return shorten_component(name, sha)
    return None


def _review_kind(store: Store, path: str) -> str:
    try:
        return str(json.loads(store.path(path).read_text(encoding="utf-8")).get("kind") or "review")
    except (OSError, ValueError):
        return "review"


def _dicts(value: object):
    if isinstance(value, dict):
        yield value
        for item in value.values():
            yield from _dicts(item)
    elif isinstance(value, list):
        for item in value:
            yield from _dicts(item)


def rename_artifacts(store: Store, apply: bool = False) -> dict:
    """Rename content-hash and over-long artifact files to the readable naming scheme."""
    refs = _references(store)
    facts = store.facts if (store.home / "facts.json").is_file() else {"facts": []}
    facts_sources = {}
    for fact in facts.get("facts", []):
        for current, original in zip(
            fact.get("sources", []), fact.get("original_sources", []), strict=False
        ):
            facts_sources[current] = original
    rows = list(store.db.execute("SELECT path, sha256 FROM artifacts ORDER BY path"))
    existing = {path for path, _ in rows}
    mapping: dict[str, str] = {}
    for path, sha in rows:
        name = _proposed_name(store, path, sha, refs, facts_sources)
        if not name:
            continue
        target = str(PurePosixPath(path).parent / name)
        if target != path and target not in existing and target not in mapping.values():
            mapping[path] = target
    result = {"applied": False, "renamed": len(mapping), "mapping": mapping}
    if not apply or not mapping:
        return result
    for old in mapping:
        if not store.artifact_intact(old):
            raise ValueError("Artifact missing or changed; run ajh verify before renaming")
    moved: list[tuple[Path, Path]] = []
    try:
        for old, new in mapping.items():
            source, target = store.path(old), store.path(new)
            target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            os.replace(source, target)
            moved.append((source, target))
        store.db.execute("BEGIN IMMEDIATE")
        try:
            for old, new in mapping.items():
                store.db.execute("UPDATE artifacts SET path=? WHERE path=?", (new, old))
            visit = lambda text: mapping.get(text, text)
            for kind, key, payload in list(
                store.db.execute("SELECT kind, id, payload FROM records")
            ):
                value = json.loads(payload)
                updated = _walk_strings(value, visit)
                if updated != value:
                    store.db.execute(
                        "UPDATE records SET payload=? WHERE kind=? AND id=?",
                        (encode(updated), kind, key),
                    )
            if facts.get("facts"):
                updated_facts = _walk_strings(facts, lambda text: mapping.get(text, text))
                if updated_facts != facts:
                    atomic_write(store.home / "facts.json", encode(updated_facts))
            manifest = {"created_at": now(), "renamed": mapping}
            manifest_path = f"maintenance/artifact-renames-{now()[:19].replace(':', '')}.json"
            atomic_write(store.path(manifest_path), encode(manifest))
            store.event(
                "artifacts_renamed",
                [],
                {"count": len(mapping), "manifest_sha256": digest(manifest)},
            )
            store.db.execute("COMMIT")
        except Exception:
            store.db.execute("ROLLBACK")
            if facts.get("facts"):
                atomic_write(store.home / "facts.json", encode(facts))
            raise
    except Exception:
        for source, target in reversed(moved):
            if target.exists() and not source.exists():
                os.replace(target, source)
        raise
    return {**result, "applied": True, "manifest": manifest_path}


def reextract_conditions(store: Store, apply: bool = False) -> dict:
    """Derive `conditions` for existing vacancies from what the journal already retains.

    Sources, in order: the retained posting file (header fields and body), the vacancy
    text, and the research section that names the vacancy (explicit salary lines only).
    Values already present stay unless the new extraction states something unknown
    before. Dry run unless `apply`.
    """
    from . import descriptions, vacancy_fields

    legacy = {
        item["id"]: item["path"]
        for item in store.all("legacy_files")
        if isinstance(item.get("path"), str)
    }
    registered = {row[0] for row in store.db.execute("SELECT path FROM artifacts")}
    changes = []
    for vacancy in store.all("vacancies"):
        location = str(vacancy.get("location") or "")
        found = descriptions.describe(store.home, vacancy, legacy, registered)
        extracted = None
        if found and found["kind"] == "posting":
            text = descriptions.read_text(store.home / found["path"]) or ""
            meta, body = descriptions.parse_posting(text)
            extracted = vacancy_fields.from_posting(body, meta, location, "posting")
        elif isinstance(vacancy.get("text"), str) and vacancy["text"].strip():
            extracted = vacancy_fields.from_posting(vacancy["text"], None, location, "vacancy_text")
        else:
            section = ""
            if found and found["kind"] == "research":
                text = descriptions.read_text(store.home / found["path"]) or ""
                match = descriptions.research_section(text, vacancy)
                section = match[1] if match else ""
            extracted = vacancy_fields.from_posting(section, None, location, "research")
            # Research notes describe the role in the researcher's words, not the posting's.
            extracted["posting_language"] = vacancy_fields.UNKNOWN
            extracted["language"] = vacancy_fields.field([])
        merged = vacancy_fields.merge(vacancy.get("conditions"), extracted)
        fields = vacancy_fields.changed_fields(vacancy.get("conditions"), merged)
        if fields:
            changes.append({"vacancy_id": vacancy["id"], "fields": fields, "conditions": merged})
    result = {
        "applied": False,
        "vacancies": len(store.all("vacancies")),
        "changed": len(changes),
        "known_after": {
            "salary": sum(1 for item in changes if item["conditions"].get("salary")),
            **{
                name: sum(
                    1
                    for item in changes
                    if item["conditions"][name]["value"] not in (vacancy_fields.UNKNOWN, [])
                )
                for name in ("work_mode", "employment", "language")
            },
            "allowed_geography": sum(
                1
                for item in changes
                if item["conditions"]["allowed_geography"]["status"] != vacancy_fields.UNKNOWN
            ),
        },
        "changes": [{k: v for k, v in item.items() if k != "conditions"} for item in changes],
    }
    if not apply or not changes:
        return result
    store.db.execute("BEGIN IMMEDIATE")
    try:
        for item in changes:
            store.patch(
                "vacancies",
                item["vacancy_id"],
                {"conditions": item["conditions"]},
                None,
                "maintenance reextract-conditions",
            )
        store.event("conditions_reextracted", [], {"changed": len(changes)})
        store.db.execute("COMMIT")
    except Exception:
        store.db.execute("ROLLBACK")
        raise
    return {**result, "applied": True}
