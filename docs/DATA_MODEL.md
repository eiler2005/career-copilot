# Data model and version contracts

[English](DATA_MODEL.md) · [Русский](ru/DATA_MODEL.md) · [Documentation](../README.md#documentation)

SQLite records describe current entities and retained decisions. Files preserve source evidence and exact document versions. IDs and hashes link the two; prose in a generated report is not an editable database interface.

## Workspace files

| Path | Purpose |
| --- | --- |
| `workspace.json` | Workspace schema and synthetic marker |
| `settings.json` | Sources, policies, budgets and rendering settings |
| `facts.json` | Current candidate and two profiles |
| `journal.sqlite` | JSON records, artifact registry and metadata |
| `facts-history/`, `evidence/` | Retained fact sets and local source files |
| `snapshots/` | Original provider responses/HTML |
| `packages/`, `reviews/` | Document versions, tasks and review evidence |
| `activities/`, `activity-artifacts/` | Skill requests/results and hashed input/output copies |
| `learning/`, `report/` | Plans and generated local views |
| `imports/`, `legacy/` | Original migration input and retained legacy files |

## Artifact file names

Generated files follow `<YYYY-MM-DD>-<context>-<sha256 prefix><suffix>` inside their directory, for example `learning/2026-09-14-product-demo-platform-lead-53275ec9.json`, `reviews/2026-09-14-master-product-v-86bc5079e2f59c79-content-cbfd1f49.json` or `evidence/2026-09-14-verified-distinctions-1bc1969f.md`. The date is when the material entered the journal, the context names what it is (track and vacancy, package/version/review kind, original file name) and the eight-character hash ties the name to the registered checksum and keeps it unique. Identical content registered again in the same directory reuses the existing file. Preserved legacy file names stay readable but are shortened to at most 200 bytes, below the 255-byte limit of common file systems.

All of these paths belong in private storage. Artifact references inside the journal are workspace-relative; external working paths in activity metadata can be private absolute paths and must not be published.

## Database tables

`records(kind TEXT, id TEXT, payload TEXT)` uses a composite primary key. `artifacts(path, sha256, bytes)` tracks immutable bytes. `meta(key, value)` holds runtime metadata. JSON flexibility is not complete schema validation: use the documented CLI/contracts, validate any controlled Store operation and preserve events.

| Record kind | Identity and links |
| --- | --- |
| `companies` | Company ID, business profile, size evidence and dossier references |
| `vacancies` | Company/provider/external IDs, URLs, source observation, availability, requirements and role gates |
| `observations` | Immutable relationship between vacancy, source, snapshot and parsed payload |
| `current_assessments`, `current_learning` | Current assessment and learning-plan pointers per vacancy/track |
| `superseded_records` | Archived older results (`kind`, `record_id`, `superseded_by`, full `payload`) removed from the active kinds |
| `text_translations` | Russian/English renderings of one exact journal text (ID = hash of the text) and translator identity |
| `assessments` | Vacancy + track + input hash; explicit requirement evidence and rule decision |
| `packages` | Logical master/vacancy + track; current version and retained version list |
| `events` | Concrete operation, entity IDs, details and time |
| `source_health` | Attempt/success times, status, HTTP result, counts and next attempt |
| `activities`, `activity_events` | Hosted skill scope/actor/result and links to CLI events |
| `company_dossiers`, `text_revisions`, `cover_letters` | Sourced research and standalone authored output |
| `interview_plans`, `interview_practices`, `interview_feedback`, `interview_progress` | Plan → actual practice → feedback → explicit progress decision |
| `employer_responses` | Evidence-backed received replies linked to a registered submission |
| `submissions` | User-confirmed external action tied to exact package/version |

## Candidate facts

A minimal synthetic fact set has this shape:

```json
{
  "schema_version": 1,
  "candidate": {"name": "Alex Example", "contacts": ["alex@example.invalid"]},
  "facts": [{
    "id": "example-platform",
    "text": "Led a fictional platform project.",
    "section": "experience",
    "verification": "self_reported",
    "claim_type": "historical",
    "sources": ["evidence-note.md"],
    "tracks": ["product", "technical-leadership"],
    "tags": ["platforms"],
    "substantive": true
  }],
  "profiles": {
    "product": {"headline": "Product leadership", "summary": "Synthetic example.", "distinction_ids": []},
    "technical-leadership": {"headline": "Technical leadership", "summary": "Synthetic example.", "distinction_ids": []}
  }
}
```

Create the actual `evidence-note.md` next to this JSON before importing. A non-URL source string is resolved as a file and copied into immutable evidence storage. Import checks unique fact IDs, exactly two profiles, provenance and verification classification. It preserves `original_sources` and prior/new fact sets.

`verified` is a recorded evidence classification, not a magical result of import. `self_reported` and `conflicting` must remain visible. `claim_type: target` cannot supply achieved-result evidence. Preserve additional context needed to distinguish employer/client/partner, official title, period and personal contribution.

## Company and vacancy cards

Company research should maintain `about`, `business_areas`, products, markets, customer segments and source-linked hiring information. A size object includes `metric`, `value`, `as_of`, `scope`, `source_url` and confidence/reliability. Do not replace missing headcount with an unsourced guess.

Vacancies need `id`, `company_id`, `title`, canonical `urls` and the relevant target track(s). Keep `role_family`, `role_type`, `level.raw`, `level.source`, `market`, `availability` and `status_checked_on` independent. Source-derived cards initially need human/agent annotation; discovery does not infer a reliable role-family or level mapping.

The dashboard preserves these fields under each API record's `payload`. Its separate `display.location` contains `raw`, `country`, `city` and `remote` for presentation and filtering. Explicit country/city fields and supported unambiguous geographic formats inform that projection; unsupported places remain unknown. This does not migrate records, overwrite the source location or treat remote work as permission to work from any country. See [dashboard](DASHBOARD.md) for the read-only API and deployment contract.

Requirements use stable `id`, `text`, `source`, `mandatory`, optional `tag`, `evidence_fact_ids`, `evidence_reviewed` and `gap_type`. Structural fields such as `minimum_years`, `authorization` and `license` override a generic learning gap. Gates `language_gate`, `eligibility_gate` and `role_family_gates[TRACK]` use explicit pass/fail/unknown judgments.

`record companies PATH` and `record vacancies PATH` are **whole-record replacement**. Read the current record and merge deliberately in a private working JSON; submitting only an ID and one changed field loses other fields.

## Assessments and document versions

An assessment's input hash covers the vacancy, company, candidate facts and policy. Re-running `evaluate` or `learn` for the same vacancy and track does not accumulate duplicates: an unchanged conclusion keeps the current record even when inputs were refreshed, and a changed conclusion becomes current while the previous one moves to `superseded_records`.

A vacancy's `availability_check` holds the latest automated check (`status`, `reason`, `confidence`, `evidence`, `http_status`, `final_url`, `checked_at`, `method`) and `availability_history` keeps the last 20. A determined result also sets `availability` and `status_checked_on`; see [CLI](CLI.md#availability-translations-and-maintenance) for the rules. Rule decisions are `priority`, `needs_clarification`, `not_suitable` or `watch`. A tag match is only a suggestion; coverage requires reviewed links to verified nontarget facts. These conservative rules are not a semantic ranking model.

A package version preserves source, PDF, extracted text, optional letter, context, coverage, task, author identity, contributor provenance, page counts and file hashes. Identical inputs reuse the version; changed inputs create a new one. Reviews bind to the full hash set and exact `version_id`.

Standalone letters reference an exact CV package/version and CV source hash. They remain drafts until composed into a reviewed package. A text revision records before/after artifacts and change notes; it does not mutate an old package.

See [CLI](CLI.md) for command syntax, [agent workflows](AGENT_WORKFLOWS.md) for request/result schemas and [operations](OPERATIONS.md) for review and migration acceptance.
