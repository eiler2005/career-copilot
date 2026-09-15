# CLI reference

[English](CLI.md) · [Русский](ru/CLI.md) · [Documentation](../README.md#documentation)

Run from the public checkout with `uv run ajh`. Global options precede the command:

```sh
uv run ajh --home /absolute/private/career-workspace --activity-id ACTIVITY_ID evaluate VACANCY_ID --track product
```

Omit `--activity-id` outside a running hosted-skill activity. `AI_JOB_HUNTER_HOME` can supply the workspace. Commands print JSON; `report --open` also opens a local browser file.

The separate `uv run ajh-dashboard --home ABSOLUTE_WORKSPACE [--host 127.0.0.1] [--port 8080] [--allowed-host HOSTNAME] [--state-dir PATH]` entry point runs a private read-only web server in the foreground. `--state-dir` (outside the workspace) enables availability checks from the interface. Repeat `--allowed-host` (or set comma-separated `AJH_DASHBOARD_ALLOWED_HOSTS`) only for a hostname served by an authenticating reverse proxy. Its workspace option belongs to that command; it does not start a skill activity or alter journal records. See [dashboard and deployment](DASHBOARD.md).

## Commands and effects

| Command | Input/options | Result |
| --- | --- | --- |
| `init [--demo]` | New/empty external workspace | Workspace marker, settings, empty facts |
| `demo` | Explicitly synthetic workspace | Fictional facts, company and vacancy |
| `facts import PATH` | Fact JSON and real local source files/URLs | Versioned facts and copied evidence |
| `record companies PATH` | Complete company JSON | Whole record replacement and before/after event |
| `record vacancies PATH` | Complete vacancy JSON | Whole record replacement and before/after event |
| `discover` | Optional `--source ID`; configured sources | Snapshots, observations and per-source status |
| `discover --source ID --replay PATH` | Workspace-relative compatible snapshot | Offline historical observation; no live-status refresh |
| `evaluate [ID] --track TRACK` | Optional vacancy; track defaults to product | Evidence-rule assessments |
| `prepare ID --track TRACK` | Vacancy or `master`; track required | Versioned document package and agent task |
| `review PACKAGE_ID --report PATH` | Exact-version content/visual JSON | Review record and recomputed readiness |
| `learn [ID] --track TRACK` | Optional vacancy; track defaults to product | Baseline/requirement-based learning plan |
| `report [--open]` | Current journal | Private HTML and JSON views |
| `stats` | Current journal | Deterministic counts, separate workflow states and available telemetry |
| `verify` | Workspace artifacts/database | Integrity result and pending review count |
| `activity start --request PATH` | Schema-v1 hosted work request | Unique activity, snapshotted inputs and model-availability state |
| `activity show ID` | Existing activity | Inputs, integrity, linked events, resumability and next action |
| `activity finish ID --result PATH` | Schema-v1 terminal result | Immutable result/artifacts and typed records |
| `import-legacy PATH [--dry-run]` | Supported legacy schema-v2 registry | Validated/reconciled import |
| `backup --destination PATH` | New destination | Database/files snapshot and manifest |
| `restore SNAPSHOT --destination PATH` | Valid backup; new destination | Restored workspace; no active `--home` needed |
| `privacy check` | `--scope`, `--root`, dictionary, optional Gitleaks/artifact | Public-content/privacy result |
| `availability check [ID ...]` | `--unverified`, `--stale-days N`, `--limit N`, `--delay S` | Read-only check of stored posting URLs; availability, `availability_check`, history and event |
| `availability import PATH` | Dashboard `availability-checks.json` | Applies newer web-interface checks to the journal |
| `translations export --output PATH [--all]` | Current journal | Translatable texts missing a Russian or English rendering |
| `translations import PATH` | Export file with translations and actual translator `actor.model` | `text_translations` records; originals unchanged |
| `maintenance dedupe [--apply]` | Current journal | Keeps the newest assessment/learning plan per vacancy and track; archives the rest |
| `maintenance rename-artifacts [--apply]` | Current journal | Renames hash-named or over-long files to readable names; updates references and writes a manifest |

`TRACK` is exactly `product` or `technical-leadership`. Use `uv run ajh COMMAND --help` for parser syntax.

## Availability, translations and maintenance

`availability check` reads only URLs already stored on vacancies, follows at most five redirects to public addresses and never bypasses a login, CAPTCHA or bot protection. Without IDs it checks active vacancies (not closed, archived or rejected). Each result records `status` (`open`, `closed`, `unknown`), `reason`, `confidence`, the visible `evidence`, HTTP status, final URL and time. Rules: HTTP 404/410 or an explicit visible closed/archived message → closed (high); a redirect that drops the posting identifier → closed (medium); a visible apply control or a published structured job posting → open (medium); blocked access, errors or no reliable signal → unknown. A recorded closed or archived state is never reopened by a medium-confidence signal — it becomes `conflicting` for a human decision.

`maintenance` commands are dry runs until `--apply`. Take a `backup` first. `dedupe` moves older results into `superseded_records` (with `superseded_by`) and sets `current_assessments`/`current_learning` pointers; old links keep resolving. `rename-artifacts` applies the naming scheme described in the [data model](DATA_MODEL.md#artifact-file-names), moves files, rewrites references in records and `facts.json`, and records a manifest under `maintenance/`. Both are idempotent.

## Dashboard requests and agent tasks

| Command | Effect |
| --- | --- |
| `inbox import PATH` | Copies request files (a directory, one file or a JSON array) into `inbox_requests` as `pending`; already imported IDs are skipped, invalid files are counted |
| `inbox list [--status S]` | Lists imported requests |
| `inbox apply [--id ID]` | Applies pending requests oldest first, each in its own transaction with a version check; results are `applied`, `queued_for_agent`, `conflict` or `failed` with a reason |
| `inbox reject ID --reason TEXT` | Rejects a pending request and keeps the reason |
| `tasks list [--status S]` | Lists agent tasks |
| `tasks next` | Returns the oldest queued task with an activity request template (`related.task_id` included) |

Applying twice is safe: only `pending` requests are processed. A conflict leaves the record unchanged; create a new request from the current state. A task changes to `running` when `activity start` names it and closes only through `activity finish` of that activity. Request types and their fields are described in the [data model](DATA_MODEL.md#record-versions-and-requests).

## Preparing authored documents

A mechanical package is useful for inspecting the handoff and remains pending:

```sh
uv run ajh --home /absolute/private/career-workspace prepare master --track product
```

After the required flagship actually writes the private source and coverage:

```sh
uv run ajh --home /absolute/private/career-workspace prepare VACANCY_ID --track product \
  --cv /absolute/private/drafts/cv.md \
  --coverage /absolute/private/drafts/coverage.json \
  --author-model ACTUAL_FLAGSHIP_MODEL \
  --author-session ACTUAL_AUTHOR_SESSION
```

These identity placeholders must be replaced with actual provenance. `--letter PATH` includes a requested letter. The coverage file is an array of `{"fact_id":"ID","included":true,"reason":"Specific location or exclusion rationale"}` rows for every fact in package context.

For multi-author/editor provenance, `--contributors PATH` accepts:

```json
{
  "schema_version": 1,
  "contributors": [{
    "role": "author",
    "environment": "openai",
    "model": "ACTUAL_FLAGSHIP_MODEL",
    "session": "ACTUAL_SESSION",
    "outputs": [{"document": "cv", "path": "cv.md", "sha256": "EXACT_SOURCE_HASH"}]
  }]
}
```

Roles are `author` or `editor`; document names are `cv` or `letter`. Paths are absolute or relative to the contributor JSON. Across contributors, outputs must cover the final source hash of every included document; intermediate revision snapshots may also be retained. Author fields can derive from the first contributor when omitted. Explicit author fields must be valid and match a supplied contributor. Known authors/editors of a bound CV or letter are inherited automatically; supplying a new contributor list cannot erase that lineage. Content reviewer sessions must differ from **all** contributor sessions as well as the legacy author session.

For a previously registered standalone letter, use `--letter-record RECORD_ID` with `--cv`. It is mutually exclusive with `--letter`. The CV source hash and current referenced version must match the letter's recorded binding. A changed CV needs reconsideration and a new correctly linked letter, not a silent reuse.

## Activity results and statistics

[Agent workflows](AGENT_WORKFLOWS.md) defines activity JSON and typed results. Pass global `--activity-id` to link intervening CLI operations to the activity. Input hashes are checked against retained copies and original files before continuation.

`stats` computes counts from SQLite. It distinguishes source health, availability, evaluation, readiness, interview evidence and actual user-confirmed submissions. Missing model identity, token counts or monetary cost remain unknown; do not substitute zero or estimated claims. Duration is recorded wall time, not proof of active thinking or human effort.

## Exit status and recovery

The CLI returns 1 for a top-level result with `passed: false`, 2 for handled input/operation errors and normal parser failures, and 0 for other results. Discovery returns a list: individual source errors can therefore coexist with exit code 0. Inspect every result's status and scope.

`verify` can pass while reviews are pending. Check both integrity and `pending_or_legacy_reviews`. It does not establish current vacancy availability, factual truth or authorization to send.

On interrupted work, inspect the activity and verify the workspace. An unchanged repeated finish is idempotent; a different terminal result requires a new activity. Changed inputs require a fresh activity with new hashes; blocked model work resumes as a linked child when the required model is available. See [operations](OPERATIONS.md) for recovery.
