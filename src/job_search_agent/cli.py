"""CLI entrypoints. Mutations are private/local; the sole network command is discover."""

from __future__ import annotations

import argparse
import fcntl
import json
import os
import sys
import webbrowser
from contextlib import contextmanager
from pathlib import Path

from . import activity, backup, privacy, report, sources, stats, workflow
from .core import TRACKS, Store, atomic_write, digest, encode, init_home, public_root, read_json


@contextmanager
def locked(store: Store):
    with (store.home / ".lock").open("a") as handle:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError("Another workflow is running for this workspace") from None
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def verify(store: Store) -> dict:
    errors = []
    for path, sha, size in store.db.execute("SELECT path,sha256,bytes FROM artifacts"):
        target = store.path(path)
        if (
            not target.is_file()
            or target.stat().st_size != size
            or digest(target.read_bytes()) != sha
        ):
            errors.append("artifact_missing_or_changed")
    companies = {c["id"] for c in store.all("companies")}
    vacancies = {v["id"] for v in store.all("vacancies")}
    for vacancy in store.all("vacancies"):
        if vacancy["company_id"] not in companies:
            errors.append("vacancy_company_missing")
    pending = 0
    for package in store.all("packages"):
        if package.get("kind") != "master" and package["vacancy_id"] not in vacancies:
            errors.append("package_vacancy_missing")
        if package["current_version"] not in {v["id"] for v in package["versions"]}:
            errors.append("package_current_version_missing")
        for version in package["versions"]:
            errors.extend(workflow.version_checks(store, version))
            if version.get("review_status") != "passed" or "reviews" not in version:
                pending += 1
    integrity = store.db.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    return {
        "passed": not errors and integrity,
        "errors": errors,
        "pending_or_legacy_reviews": pending,
        "counts": {k: len(store.all(k)) for k in ("companies", "vacancies", "packages", "events")},
        "note": "Integrity is not content approval or proof of an open vacancy",
    }


def seed_demo(store: Store) -> dict:
    if not read_json(store.home / "workspace.json").get("synthetic"):
        raise ValueError("Demo requires an explicitly synthetic workspace")
    facts = {
        "schema_version": 1,
        "candidate": {"name": "Alex Example", "contacts": ["alex@example.invalid"]},
        "facts": [
            {
                "id": "sample-book",
                "text": "Author of a fictional handbook on platform products (synthetic example).",
                "section": "distinctions",
                "verification": "verified",
                "claim_type": "credential",
                "tracks": list(TRACKS),
                "sources": ["synthetic fixture"],
                "tags": ["platforms"],
                "substantive": True,
            },
            {
                "id": "sample-job",
                "text": "2020-2025 | Example Systems | Engineering Manager. Led a fictional platform team; this is not a real candidate.",
                "section": "experience",
                "verification": "verified",
                "claim_type": "historical",
                "tracks": list(TRACKS),
                "sources": ["synthetic fixture"],
                "tags": ["leadership"],
                "substantive": True,
            },
        ],
        "profiles": {
            track: {
                "headline": "Product leadership" if track == "product" else "Technical leadership",
                "summary": "Synthetic demonstration profile, not for applications.",
                "distinction_ids": ["sample-book"],
            }
            for track in TRACKS
        },
    }
    atomic_write(store.home / "facts.json", encode(facts))
    store.put(
        "companies",
        {
            "id": "example-systems",
            "name": "Example Systems (fictional)",
            "about": "Fictional platform developer",
            "business_areas": ["platforms"],
            "size": {
                "metric": "employees",
                "value": None,
                "as_of": None,
                "scope": "fictional",
                "source_url": None,
            },
        },
    )
    store.observe_vacancy(
        {
            "id": "demo-platform-lead",
            "company_id": "example-systems",
            "title": "Platform Product Lead",
            "location": "Example City",
            "market": "intl",
            "target_track": "product",
            "role_family": "product",
            "urls": ["https://example.invalid/jobs/platform-lead"],
            "availability": "unknown",
            "requirements": [
                {
                    "id": "req-platform",
                    "text": "Explain platform adoption metrics",
                    "tag": "platforms",
                    "mandatory": True,
                    "gap_type": "knowledge",
                }
            ],
        },
        "synthetic",
        "synthetic",
    )
    return {"synthetic": True, "vacancy_id": "demo-platform-lead"}


def import_facts(store: Store, source: Path) -> dict:
    data = read_json(source)
    ids = [f["id"] for f in data["facts"]]
    if len(ids) != len(set(ids)) or set(data["profiles"]) != set(TRACKS):
        raise ValueError("Unique facts and exactly two master profiles required")
    for fact in data["facts"]:
        if not fact.get("sources") or fact.get("verification") not in {
            "verified",
            "self_reported",
            "conflicting",
        }:
            raise ValueError("Every fact requires provenance and a verification classification")
        original = list(fact["sources"])
        materialized = []
        for reference in original:
            if reference.startswith(("https://", "http://")):
                materialized.append(reference)
            else:
                path = (source.parent / reference).resolve()
                if not path.is_file():
                    raise ValueError("Fact source missing; evidence import cannot silently skip it")
                body = path.read_bytes()
                materialized.append(store.artifact(f"evidence/{digest(body)}{path.suffix}", body))
        fact["original_sources"] = original
        fact["sources"] = materialized
    for profile in data["profiles"].values():
        if not set(profile.get("distinction_ids", [])).issubset(ids):
            raise ValueError("Unknown distinction fact ID")
    old = store.facts
    store.artifact(f"facts-history/{digest(old)}.json", encode(old))
    store.artifact(f"facts-history/{digest(data)}.json", encode(data))
    atomic_write(store.home / "facts.json", encode(data))
    store.event("facts_imported", [], {"sha256": digest(data), "fact_count": len(ids)})
    return {"facts": len(ids), "profiles": list(data["profiles"]), "sha256": digest(data)}


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description="Private-by-design job search agent")
    root.add_argument(
        "--home",
        default=os.environ.get("AI_JOB_HUNTER_HOME"),
        help="Explicit external private workspace",
    )
    root.add_argument("--activity-id", help="Link command events to a running activity")
    commands = root.add_subparsers(dest="command", required=True)
    actions = commands.add_parser("activity").add_subparsers(dest="activity_command", required=True)
    actions.add_parser("start").add_argument("--request", required=True, type=Path)
    actions.add_parser("show").add_argument("activity")
    finish = actions.add_parser("finish")
    finish.add_argument("activity")
    finish.add_argument("--result", required=True, type=Path)
    commands.add_parser("stats")
    init = commands.add_parser("init")
    init.add_argument("--demo", action="store_true")
    commands.add_parser("demo")
    facts = commands.add_parser("facts").add_subparsers(dest="facts_command", required=True)
    facts.add_parser("import").add_argument("source", type=Path)
    record = commands.add_parser("record")
    record.add_argument("kind", choices=("companies", "vacancies"))
    record.add_argument("source", type=Path)
    imp = commands.add_parser("import-legacy")
    imp.add_argument("registry", type=Path)
    imp.add_argument("--dry-run", action="store_true")
    collect = commands.add_parser("discover")
    collect.add_argument("--source")
    collect.add_argument("--replay", help="Private snapshot-relative path; requires --source")
    for name in ("evaluate", "learn"):
        cmd = commands.add_parser(name)
        cmd.add_argument("vacancy_id", nargs="?")
        cmd.add_argument("--track", choices=TRACKS, default="product")
    prepare = commands.add_parser("prepare")
    prepare.add_argument("vacancy_id", help="Vacancy ID or 'master'")
    prepare.add_argument("--track", choices=TRACKS, required=True)
    for option in ("cv", "letter", "coverage"):
        prepare.add_argument("--" + option, type=Path)
    prepare.add_argument("--author-model")
    prepare.add_argument("--author-session")
    prepare.add_argument("--contributors", type=Path)
    prepare.add_argument("--letter-record")
    review = commands.add_parser("review")
    review.add_argument("package_id")
    review.add_argument("--report", type=Path, required=True)
    overview = commands.add_parser("report")
    overview.add_argument("--open", action="store_true")
    commands.add_parser("verify")
    snapshot = commands.add_parser("backup")
    snapshot.add_argument("--destination", type=Path, required=True)
    restore = commands.add_parser("restore")
    restore.add_argument("snapshot", type=Path)
    restore.add_argument("--destination", type=Path, required=True)
    private = commands.add_parser("privacy").add_subparsers(dest="privacy_command", required=True)
    scan = private.add_parser("check")
    scan.add_argument("--scope", choices=("worktree", "index", "history"), default="worktree")
    scan.add_argument("--root", type=Path, default=public_root())
    scan.add_argument("--dictionary", type=Path, default=os.environ.get("AJH_PRIVACY_DICTIONARY"))
    scan.add_argument("--gitleaks", action="store_true")
    scan.add_argument(
        "--artifact", type=Path, help="Inspect built wheel/sdist contents instead of source tree"
    )
    return root


def run(args) -> dict | list:
    if args.command == "privacy":
        dictionary = args.dictionary
        if not dictionary:
            import subprocess

            found = subprocess.run(
                ["git", "-C", str(args.root), "config", "--get", "ajh.privateDictionary"],
                capture_output=True,
                text=True,
                check=False,
            )
            dictionary = Path(found.stdout.strip()) if found.returncode == 0 else None
        result = (
            privacy.check_artifact(args.artifact, dictionary)
            if args.artifact
            else privacy.check(args.root, args.scope, dictionary)
        )
        if args.artifact and args.gitleaks:
            raise ValueError(
                "Run Gitleaks on an independently unpacked release; archive scan is structural/privacy only"
            )
        if args.gitleaks:
            result["gitleaks"] = privacy.gitleaks_check(args.root, args.scope)
            result["passed"] = result["passed"] and result["gitleaks"]["passed"]
        return result
    if args.command == "restore":
        return backup.restore(args.snapshot, args.destination)
    if not args.home:
        raise ValueError(
            "Pass --home ABSOLUTE_PATH or set AI_JOB_HUNTER_HOME; no implicit data directory"
        )
    if args.command == "init":
        return {"home": str(init_home(args.home, demo=args.demo)), "initialized": True}
    with Store(args.home) as store, locked(store):
        if args.activity_id:
            activity.bind(store, args.activity_id)
        if args.command == "activity":
            if args.activity_command == "start":
                return activity.start(store, args.request)
            if args.activity_command == "show":
                return activity.show(store, args.activity)
            return activity.finish(store, args.activity, args.result)
        if args.command == "stats":
            return stats.compute(store)
        if args.command == "demo":
            return seed_demo(store)
        if args.command == "facts":
            return import_facts(store, args.source)
        if args.command == "record":
            value = read_json(args.source)
            old = store.get(args.kind, value["id"])
            store.event(
                "record_updated", [value["id"]], {"kind": args.kind, "before": old, "after": value}
            )
            store.put(args.kind, value)
            return {"id": value["id"], "recorded": True}
        if args.command == "import-legacy":
            from .core import import_legacy

            return import_legacy(store, args.registry, dry_run=args.dry_run)
        if args.command == "discover":
            if args.replay and not args.source:
                raise ValueError("Replay requires an explicit source")
            return sources.discover(store, source_id=args.source, replay=args.replay)
        if args.command == "evaluate":
            return workflow.evaluate(store, args.vacancy_id, args.track)
        if args.command == "learn":
            return workflow.learning_plan(store, args.vacancy_id, args.track)
        if args.command == "prepare":
            return workflow.prepare(
                store,
                args.vacancy_id,
                args.track,
                cv=args.cv,
                author_model=args.author_model,
                author_session=args.author_session,
                letter=args.letter,
                coverage_file=args.coverage,
                contributors_file=args.contributors,
                letter_record=args.letter_record,
            )
        if args.command == "review":
            return workflow.record_review(store, args.package_id, args.report)
        if args.command == "report":
            path = report.render(store)
            if args.open:
                webbrowser.open(path.as_uri())
            return {"report": str(path)}
        if args.command == "verify":
            return verify(store)
        if args.command == "backup":
            return backup.backup(store, args.destination)
    raise ValueError("Unsupported command")


def main() -> int:
    args = parser().parse_args()
    try:
        result = run(args)
        print(encode(result))
        return 1 if isinstance(result, dict) and result.get("passed") is False else 0
    except (ValueError, OSError, KeyError, json.JSONDecodeError) as error:
        # Network errors are handled in sources; never expose credential-bearing exceptions.
        print(
            encode(
                {"error": str(error) if isinstance(error, ValueError) else type(error).__name__}
            ),
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
