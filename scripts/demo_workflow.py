"""Run a synthetic, offline CLI walkthrough; no model calls or fabricated document reviews."""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import subprocess
import sys
from pathlib import Path


def write_json(path: Path, value) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def file_ref(path: Path, name: str | None = None) -> dict:
    result = {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    if name:
        result["name"] = name
    return result


def snapshot_records(home: Path) -> dict:
    with sqlite3.connect(f"file:{home / 'journal.sqlite'}?mode=ro", uri=True) as db:
        return {
            (kind, key): payload
            for kind, key, payload in db.execute("SELECT kind,id,payload FROM records")
        }


def walkthrough(home: Path) -> dict:
    home = home.expanduser().resolve()
    if home.exists():
        raise ValueError("The demo requires a new destination; previous demos are preserved")
    backup = home.with_name(home.name + "-backup")
    restored = home.with_name(home.name + "-restored")
    if backup.exists() or restored.exists():
        raise ValueError("Choose a new destination with unused backup/restore siblings")
    commands = []

    def call(*args: str, activity_id: str | None = None, target: Path | None = None):
        command = [sys.executable, "-m", "job_search_agent.cli", "--home", str(target or home)]
        if activity_id:
            command += ["--activity-id", activity_id]
        command += list(args)
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        if completed.returncode:
            raise RuntimeError(
                f"Demo command failed: {' '.join(args)}\n{completed.stdout}\n{completed.stderr}"
            )
        output = json.loads(completed.stdout)
        commands.append({"command": list(args), "result": output})
        return output

    call("init", "--demo")
    call("demo")
    inputs = home / "demo-inputs"
    inputs.mkdir()
    request = write_json(
        inputs / "coordinator.json",
        {
            "schema_version": 1,
            "skill": "career-copilot",
            "operation": "offline-cli-walkthrough",
            "related": {"company_id": "example-systems", "vacancy_id": "demo-platform-lead"},
            "actor": {},
            "inputs": [],
            "expected_result": {"types": []},
        },
    )
    coordinator = call("activity", "start", "--request", str(request))["id"]
    facts = json.loads((home / "facts.json").read_text(encoding="utf-8"))
    evidence = inputs / "evidence.txt"
    evidence.write_text("\n".join(f["text"] for f in facts["facts"]), encoding="utf-8")
    for fact in facts["facts"]:
        fact["sources"] = ["evidence.txt"]
    call("facts", "import", str(write_json(inputs / "facts.json", facts)), activity_id=coordinator)

    with sqlite3.connect(f"file:{home / 'journal.sqlite'}?mode=ro", uri=True) as db:
        company = json.loads(
            db.execute(
                "SELECT payload FROM records WHERE kind='companies' AND id='example-systems'"
            ).fetchone()[0]
        )
    dossier = write_json(inputs / "company-dossier.json", {"synthetic": True, "profile": company})
    company_request = write_json(
        inputs / "company-request.json",
        {
            "schema_version": 1,
            "skill": "career-company-research",
            "operation": "import-synthetic-dossier",
            "parent_activity_id": coordinator,
            "related": {"company_id": "example-systems"},
            "actor": {},
            "inputs": [file_ref(dossier)],
            "expected_result": {"types": ["company_dossier"]},
        },
    )
    company_activity = call("activity", "start", "--request", str(company_request))["id"]
    company_result = write_json(
        inputs / "company-result.json",
        {
            "schema_version": 1,
            "status": "completed",
            "artifacts": [file_ref(dossier, "dossier")],
            "records": [
                {
                    "type": "company_dossier",
                    "data": {
                        "company_id": "example-systems",
                        "dossier_artifact": "dossier",
                    },
                }
            ],
            "next_action": "Evaluate the synthetic vacancy",
        },
    )
    call("activity", "finish", company_activity, "--result", str(company_result))
    call("activity", "finish", company_activity, "--result", str(company_result))
    for track in ("product", "technical-leadership"):
        call("evaluate", "demo-platform-lead", "--track", track, activity_id=coordinator)
        call("prepare", "master", "--track", track, activity_id=coordinator)
        learning = call("learn", "--track", track, activity_id=coordinator)
        plan_file = write_json(inputs / f"interview-{track}.json", learning)
        plan_request = write_json(
            inputs / f"interview-request-{track}.json",
            {
                "schema_version": 1,
                "skill": "career-interview-prep",
                "operation": "register-mechanical-baseline",
                "parent_activity_id": coordinator,
                "related": {"track": track},
                "actor": {},
                "inputs": [file_ref(plan_file)],
                "expected_result": {"types": ["interview_plan"]},
            },
        )
        plan_activity = call("activity", "start", "--request", str(plan_request))["id"]
        plan_result = write_json(
            inputs / f"interview-result-{track}.json",
            {
                "schema_version": 1,
                "status": "completed",
                "artifacts": [file_ref(plan_file, "plan")],
                "records": [
                    {
                        "type": "interview_plan",
                        "data": {
                            "id": f"demo-interview-{track}",
                            "track": track,
                            "objectives": [str(week["focus"]) for week in learning["weeks"][:2]],
                            "plan_artifact": "plan",
                            "source_is_mechanical": True,
                        },
                    }
                ],
                "next_action": "Use the interview skill to tailor exercises and record actual practice",
            },
        )
        call("activity", "finish", plan_activity, "--result", str(plan_result))
    package = call("prepare", "demo-platform-lead", "--track", "product", activity_id=coordinator)
    repeated = call("prepare", "demo-platform-lead", "--track", "product", activity_id=coordinator)
    assert len(repeated["versions"]) == 1
    assert repeated["current_version"] == package["current_version"]
    assert package["versions"][0]["review_status"] == "pending"

    author_request = write_json(
        inputs / "author-request.json",
        {
            "schema_version": 1,
            "skill": "career-cv-tailor",
            "operation": "author-vacancy-cv",
            "parent_activity_id": coordinator,
            "related": {"vacancy_id": "demo-platform-lead", "track": "product"},
            "required_model": "gpt-6-astra",
            "actor": {},
            "inputs": [],
            "expected_result": {"types": []},
        },
    )
    author = call("activity", "start", "--request", str(author_request))
    assert author["status"] == "blocked"
    call(
        "activity",
        "finish",
        author["id"],
        "--result",
        str(
            write_json(
                inputs / "author-blocked.json",
                {
                    "schema_version": 1,
                    "status": "blocked",
                    "artifacts": [],
                    "records": [],
                    "next_action": "Invoke the CV skill in a real flagship session; the script does not call a model",
                },
            )
        ),
    )

    settings = json.loads((home / "settings.json").read_text(encoding="utf-8"))
    settings["sources"] = [
        {
            "id": "offline-board",
            "provider": "greenhouse",
            "company_id": "example-systems",
            "board": "fictional-offline-only",
        }
    ]
    write_json(home / "settings.json", settings)
    replay = write_json(
        inputs / "greenhouse.json",
        {
            "jobs": [
                {
                    "id": "offline-example",
                    "title": "Fictional Platform Lead",
                    "content": "Synthetic posting for offline parser demonstration.",
                    "absolute_url": "https://example.invalid/jobs/offline-example",
                }
            ]
        },
    )
    for _ in range(2):
        call(
            "discover",
            "--source",
            "offline-board",
            "--replay",
            str(replay.relative_to(home)),
            activity_id=coordinator,
        )
    assert call("activity", "show", coordinator)["resumable"] is True
    call(
        "activity",
        "finish",
        coordinator,
        "--result",
        str(
            write_json(
                inputs / "done.json",
                {
                    "schema_version": 1,
                    "status": "completed",
                    "artifacts": [],
                    "records": [],
                    "next_action": "Inspect the report and invoke real skills for authorship, review and interview coaching",
                },
            )
        ),
    )
    statistics = call("stats")
    assert statistics["vacancies"]["unique"] == 2
    assert statistics["companies"]["dossiers"] == 1
    assert statistics["documents"]["versions"] == 3
    assert statistics["interviews"]["plans"] == 2
    assert statistics["submissions"]["evidence_backed"] == 0
    call("report")
    assert call("verify")["passed"] is True
    before_backup = snapshot_records(home)
    call("backup", "--destination", str(backup))
    # restore does not use --home, which is harmless but not required by this CLI command.
    call("restore", str(backup), "--destination", str(restored))
    assert call("verify", target=restored)["passed"] is True
    assert snapshot_records(restored) == before_backup
    result = {
        "synthetic": True,
        "model_calls": 0,
        "submissions": statistics["submissions"]["evidence_backed"],
        "report": str(home / "report/index.html"),
        "restored_home": str(restored),
        "record_count_at_backup": len(before_backup),
        "stats": statistics,
    }
    write_json(home / "demo-results.json", {**result, "commands": commands})
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--home", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(walkthrough(args.home), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
