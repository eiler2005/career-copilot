# Operating and recovering a private workspace

[English](OPERATIONS.md) · [Русский](ru/OPERATIONS.md) · [Documentation](../README.md#documentation)

Use an explicit persistent private workspace, preserve original evidence and test restoration before relying on a backup. The public repository is not a backup destination for candidate data.

## Environment and settings

macOS and Linux are supported with Python 3.12+, `uv` and a Unicode TrueType font. The renderer checks common DejaVu and Arial locations; set `pdf_font` to an installed TTF when needed. Do not replace Cyrillic text with transliteration to make rendering pass.

`--home` precedes the command. `AI_JOB_HUNTER_HOME` is an alternative. `init` requires a new or empty directory; `init --demo` explicitly marks a synthetic workspace. The demo seeder refuses non-synthetic workspaces. See [getting started](GETTING_STARTED.md) for a complete offline run.

Private settings cover sources, policy, request budget, learning horizon and PDF font. A JSON field does not implement a new runtime feature merely because it is present. [Configuration](CONFIGURATION.md) distinguishes active controls from human planning metadata.

## Legacy migration rehearsal

The importer supports a legacy JSON registry with `schema_version: 2`, companies, vacancies, packages with versions and events. It is not a generic folder importer. Back up the original registry and documents, create a new destination workspace and retain the original unchanged.

```sh
uv run ajh --home /absolute/private/new-workspace import-legacy /absolute/private/legacy/journal/registry.json --dry-run
uv run ajh --home /absolute/private/new-workspace import-legacy /absolute/private/legacy/journal/registry.json
uv run ajh --home /absolute/private/new-workspace verify
```

Dry-run validates the format, conflicts, required documents and checksums and reports expected counts without importing records. Import preserves original JSON, IDs, events and version payloads. Files are copied under private `legacy/` with a path mapping.

Compare company, vacancy, package, version, original-event and file counts, every original ID and each document SHA-256. A new migration event is expected; it does not replace original events. Import the same source again to check idempotency. Conflicts with newer records, missing required files or hash mismatches block migration instead of overwriting data. Correct the cause and repeat dry-run.

## Document review

`prepare master --track product` and `prepare master --track technical-leadership` create separate logical master packages with version histories. Vacancy packages have their own identities and track links. Edit working source files and call `prepare` again instead of modifying retained artifacts in place.

`review PACKAGE_ID --report PATH` reads a typed JSON report bound to the current `version_id` and complete `sha256` dictionary. Common fields are `kind` (`content` or `visual`), actual `model` and `session`, boolean `passed` and substantive `findings`.

For content approval, the reviewer model must be the author's required flagship and the session must differ from every author/editor session. `coverage_complete: true` is required. The saved coverage array must contain exactly one row per fact ID in context, boolean `included` and a nonempty `reason`.

For visual approval, `checked_pages` must contain every CV page in order starting at 1; `extracted_text_checked: true` records actual comparison of extracted text. If a letter exists, `letter_checked_pages` must cover all its pages too, and the extracted letter text must be checked. A negative report with meaningful findings is valid before every check is complete and does not make the package ready.

A report outline for an actual failed content check is:

```json
{
  "kind": "content",
  "version_id": "COPY_CURRENT_VERSION_ID",
  "sha256": {},
  "model": "ACTUAL_REVIEWER_MODEL",
  "session": "ACTUAL_SEPARATE_REVIEW_SESSION",
  "passed": false,
  "coverage_complete": false,
  "findings": ["The achievement is not supported by the supplied source."]
}
```

Populate `sha256` with the complete dictionary from the real version. These placeholders deliberately do not constitute an executable positive approval. The reviewer must read the evidence and all delivered artifacts.

The renderer supports single-column A4 Markdown with Unicode fonts, page numbers, headings, paragraphs and simple lists. Links are expanded as text. Arbitrary HTML, complex tables and multi-column CV layouts are outside the supported format. Font, renderer or source changes require a new version and applicable content and visual reviews.

`verify` detects technical inconsistency. Pending reviews need not mean corruption, but they do prevent a claim of readiness.

## Backup and restore

```sh
uv run ajh --home /absolute/private/career-workspace backup --destination /absolute/private/backups/career-snapshot
uv run ajh restore /absolute/private/backups/career-snapshot --destination /absolute/private/career-restored
uv run ajh --home /absolute/private/career-restored verify
uv run ajh --home /absolute/private/career-restored report --open
```

Use fresh destinations outside the active workspace. A backup contains a consistent SQLite snapshot, settings, facts and artifacts, plus a manifest with file hashes. Restore validates the manifest into a new directory. Compare entity counts, IDs, versions and hashes, then inspect restored documents and the report. A successful restore establishes that this copy is usable.

A suggested retention policy is 14 daily and 8 weekly copies. This is operational guidance: the CLI neither installs cron nor rotates backups. Configure scheduling and controlled retention separately, retaining a known-good copy until its replacement is verified.

For a frozen assessment batch, keep the cohort manifest beside the private journal and include it in the backup. After restore, compare its IDs and source hashes with the restored evidence, run `verify`, and regenerate the report from that restored workspace before resuming. Do not use a copied report as proof that the batch completed.

Pause writers while backing up artifacts. A consistent database snapshot alone does not make concurrently changing files consistent. A local copy on the same disk does not protect against device loss; off-device encrypted backup needs its own destination, keys, scheduling and restore test. Do not describe a local directory as encrypted or remote without that setup.

## Troubleshooting and restart

| Symptom | Inspect | Recovery |
| --- | --- | --- |
| Empty discovery output | Enabled source selection, status, filters, snapshot and last success | Correct source scope or use an allowed route; preserve prior records |
| PDF failure or missing glyphs | TTF path, source characters, supported Markdown | Install/configure a Unicode font and rebuild a new version |
| Rejected review | Version ID, all hashes, actual reviewer/session, coverage and pages | Review the actual current version and correct the report |
| Immutable path conflict | Origin, prior hash and intended version | Preserve prior bytes and create a new artifact/version |
| Unknown or conflicting vacancy identity | Company/provider ID, canonical URLs and aliases | Reconcile evidence before merging |
| Interrupted activity | `activity show ID`, recorded artifacts and last event | Finish failed/blocked with a next action or start a linked continuation |
| Integrity failure | Missing/changed artifact and database integrity | Preserve diagnostics and restore from a verified copy |
| Request `conflict` | `inbox list --status conflict`, the record's current state | Repeat the action from the current state; the old request stays for audit |
| Request `failed` | The request `error` (for example an unreadable page for `vacancy_add`) | Fix the input (paste the text instead of a blocked link) and create a new request |
| Task stuck in `running` or `blocked` | `tasks list`, the linked `activity show ID` | Finish the activity as blocked/failed with a next action, or start a new linked activity for the task |
| Assessment "needs update" | Changed input parts shown in the Fit tab | `evaluate --stale` after reviewing the change |
| Campaigns ignored | `campaigns_error` in the dashboard or `campaigns list` | Fix the list; an invalid list is ignored as a whole |

Data migrations for the September 2026 releases are dry runs by default and idempotent: `maintenance reextract-conditions [--apply]` derives vacancy conditions from retained texts, and `evaluate --stale` re-runs assessments whose inputs changed. Take `backup` first and run `verify` afterwards.

Before schema changes, back up and rehearse restoration. Migrations should accept an explicit source schema, preserve originals, operate transactionally and support dry-run and repeated execution. Unknown schema versions require a stop; arbitrary future migrations are not promised.

Before handing off code, run formatting, lint, tests and the applicable privacy checks in [PRIVACY](PRIVACY.md). Publication and release are separate actions against an exact reviewed artifact set.
