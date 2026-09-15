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
| `collection_runs` | One discovery run: `new` vacancy IDs, `changed` IDs with field names, `unchanged` count, `possible_duplicates` (never merged automatically) and source `errors` with status, HTTP code, reason and last success |
| `preparation_overviews` | Unified agent-authored review of both tracks with evidence-labelled themes, a weekly plan, question bank, stories and CV advice (see [preparation](PREPARATION.md#preparation-module-two-entries-and-a-practice-cycle)) |
| `preparation_briefs`, `track_plans`, `practice_sessions`, `practice_attempts`, `practice_reviews` | Vacancy briefs with provenance; plans for general gaps or baseline; practice questions (linked to a plan by `plan_id`, `plan_kind` and `topic_id`), answers (artifacts) with retry/follow-up links and reviews (see [preparation](PREPARATION.md#preparation-module-two-entries-and-a-practice-cycle)) |
| `cv_edits`, `cv_edit_decisions`, `cv_imports` | Proposed CV edits for an exact version; immutable user decisions with `sequence`; imported CV structure with its fact-extraction task (see [CV profiles](CV_PROFILES.md)) |
| `inbox_requests` | A dashboard request (`type`, `base{kind,id,version}`, `payload`) with `status` `pending`, `applied`, `queued_for_agent`, `conflict`, `failed` or `rejected`, its `result` or `error` |
| `tasks` | Work for an agent session: `type`, `skill`, `status` `queued`, `running`, `blocked`, `failed` or `done`, `related` IDs, `request_id`, `activity_id`, `result_refs` |

### Record versions and requests

A record version is the first 16 hex characters of the SHA-256 of its canonical JSON payload (`Store.version`). `Store.patch(kind, id, changes, expected_version, reason)` changes top-level fields in one `BEGIN IMMEDIATE` transaction: if the stored version differs from `expected_version`, nothing is written (`VersionConflict`); otherwise the record is updated and a `record_updated` event stores the changed fields before and after, both versions and the reason. A field set to `null` is removed; `id` never changes.

The dashboard never writes the journal. It stores requests as `requests/<id>.json` in its state directory. `ajh inbox import` copies them into `inbox_requests`, and `ajh inbox apply` runs each one in its own transaction: a request that changes a record carries the version the user saw, so a record changed in between becomes `conflict` instead of a lost update. Deterministic request types are applied by controlled operations: `vacancy_decision` (personal `interested`/`not_interested` with reason, or `cleared`; evidence is untouched), `clarification_answer`, `coding_requirement` (`required`/`not_required`/`unknown` with basis and source), `evaluate`, `vacancy_add` (link or text), `cv_edit_decision` (`accept`, `reject` or `edit` with text), `cv_import` (pasted CV text and track), `prep_plan`, `prep_create`, `practice_answer` and `campaign_upsert` (checked against the version of the stored campaign; `null` for a new one). Requests that need authored or researched work create `tasks`; an agent session picks one up with `ajh tasks next`, starts an activity with `related.task_id`, and the task mirrors the real activity outcome (`running` → `done`, `blocked` or `failed`). A task is never marked done without a finished activity.

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

### Vacancy conditions and dates

`conditions` (method `conditions-v1`) keeps what a source states, each value with its `source`:

| Field | Content |
| --- | --- |
| `salary` | `min`, `max`, `currency`, `period` (`month`, `year`, `hour`, `unknown`), `gross_net` (`gross`, `net`, `unknown`), `raw` wording and `source`; `null` when not stated. A single amount appears only when the source gives one; no monthly figure is derived |
| `provider_conversion` | A provider's recalculation (for example the LinkedIn Salaries monthly USD estimate), kept apart from the employer's range |
| `work_mode`, `employment`, `language` | `{value, source, raw?}`; `value` is `remote`/`hybrid`/`office`, `full_time`/`part_time`/`contract`/`internship`/`temporary`, a list of ISO language codes, or `unknown` |
| `posting_language` | Language of the retained text (`ru`, `en`, `unknown`), not a requirement |
| `allowed_geography` | `status` `listed` (explicit countries), `office_location` or `unknown`, with `countries`, `basis` and `source`. Remote without a country list stays `unknown` |
| `published_on`, `updated_on`, `valid_through` | Dates published by the source |

Discovery (`first_seen`), last listing (`last_seen`) and verification (`status_checked_on`, availability checks) stay separate from publication. Only an employer's own board listing (Greenhouse, Lever, Ashby, HH) sets `status_checked_on` during collection; aggregator cards, corporate pages and replays do not. A merge keeps known condition values when a later source is silent, never replaces a more complete text (`full` > `page_text` > `excerpt` > card) and does not turn a recorded availability into `unknown`.

`ajh vacancy add` stores the original response or pasted text under `snapshots/intake/` and merges it as an observation from source `intake`. A company that cannot be matched by name or alias is created with `needs_review: true`.

### Search campaigns

`settings.json → campaigns[]` describes what the user is looking for: `id`, `name`, `market` (`ru`, `intl`, `any`), `track`, `role_titles`, `levels`, `work_countries`, `work_modes`, `languages`, `employment`, `salary {min, currency, period, gross_net}`, `exclusions`, `source_ids`, `active`. Matching a vacancy against a campaign yields `match`, `mismatch` or `unknown` per criterion with a basis and an overall status (any mismatch → `mismatch`, any unknown → `unknown`). Salaries in another currency or period are `unknown`; no conversion is assumed. Campaigns are preferences only and never change a qualification assessment; one vacancy stays one record when several campaigns fit it. An invalid campaign list is ignored as a whole and reported.

The dashboard preserves these fields under each API record's `payload`. Its separate `display.location` contains `raw`, `country`, `city` and `remote` for presentation and filtering. Explicit country/city fields and supported unambiguous geographic formats inform that projection; unsupported places remain unknown. This does not migrate records, overwrite the source location or treat remote work as permission to work from any country. See [dashboard](DASHBOARD.md) for the read-only API and deployment contract.

Requirements use stable `id`, `text`, `source`, `mandatory`, optional `tag`, `evidence_fact_ids`, `evidence_reviewed` and `gap_type`. Structural fields such as `minimum_years`, `authorization` and `license` override a generic learning gap. Gates `language_gate`, `eligibility_gate` and `role_family_gates[TRACK]` use explicit pass/fail/unknown judgments.

`record companies PATH` and `record vacancies PATH` are **whole-record replacement**. Read the current record and merge deliberately in a private working JSON; submitting only an ID and one changed field loses other fields.

## Assessments and document versions

### Explainable fit (`evidence-rules-v2`)

An assessment has an `outcome` without any score or hiring probability:

| Outcome | When |
| --- | --- |
| `insufficient_data` | No annotated requirements, or no verified facts for the track |
| `not_fit_mandatory` | A mandatory requirement with a confirmed mismatch (`confirmed_unmet`, work authorization `no` in `settings.candidate`) or a failed mandatory constraint |
| `has_questions` | A mandatory requirement is not a confirmed match, or a constraint is unknown |
| `fits_verified` | Every mandatory requirement is backed by reviewed verified facts and every constraint passes |

`not_assessed` is shown when no assessment exists. `reason` names the first blocking item; `reason_ref` points to it (`requirement`, `constraint`, `data`, `all_mandatory`) with a `code`. Each row of `requirements` has `category` (`qualification`, `constraint`), `mandatory`, `evidence` (`fact_id`, `verification`, `source`), `suggested_facts`, `status` (`match`, `gap`, `unknown`), `basis` with a stable `basis_code` and `action.type`:

| Situation | Status → action |
| --- | --- |
| Linked verified facts, reviewed (`evidence_reviewed`) | `match` → `none` |
| Linked verified facts, not reviewed | `unknown` → `cv_edit` |
| Structural requirement (years, authorization, license) without evidence | `unknown` → `clarify` |
| Verified facts share the requirement tag, or `experience_framing` | `unknown` → `cv_edit` — a missing word in the CV is not missing experience |
| Annotator compared and found no evidence (`evidence_checked: true`) | `gap` → `preparation` |
| Not compared yet (a tag alone never proves absence) | `unknown` → `clarify` |
| Confirmed mismatch | `gap` → `decision_basis` |

`constraints` lists `track`, `seniority`, `language`, `eligibility` and, when `settings.candidate` defines them, `geography` (allowed countries against `work_countries`) and `required_languages`, each `pass`, `fail` or `unknown` with a basis. `preferences` holds the search campaign matches, which never change the outcome. `completeness` records the description scope, requirement counts and verified facts for the track. The legacy `decision` field is still written for older readers.

`inputs` stores per-part digests (`vacancy` without availability, check and personal-decision fields, `company`, `facts`, `policy`, `candidate`). The `current_assessments` pointer stores `checked_inputs` and `checked_at` from the latest run, even when an unchanged conclusion kept an older record; the dashboard compares them with the current journal and marks the assessment as needing an update with the changed parts. `ajh evaluate --stale` re-runs only those. Requirements are replaced through `ajh vacancy requirements ID PATH`, which validates IDs, text, `mandatory`, `gap_type` (`knowledge`, `practice`, `experience_framing`, `structural`), `category`, fact IDs and flags. Clarification answers (`clarification_answer` requests) are stored on the vacancy with the requirement ID, appear in the matrix and make the assessment stale until it is re-run.

An assessment's input hash covers the vacancy, company, candidate facts and policy. Re-running `evaluate` or `learn` for the same vacancy and track does not accumulate duplicates: an unchanged conclusion keeps the current record even when inputs were refreshed, and a changed conclusion becomes current while the previous one moves to `superseded_records`.

A vacancy's `availability_check` holds the latest automated check (`status`, `reason`, `confidence`, `evidence`, `http_status`, `final_url`, `checked_at`, `method`) and `availability_history` keeps the last 20. A determined result also sets `availability` and `status_checked_on`; see [CLI](CLI.md#availability-translations-and-maintenance) for the rules. Rule decisions are `priority`, `needs_clarification`, `not_suitable` or `watch`. A tag match is only a suggestion; coverage requires reviewed links to verified nontarget facts. These conservative rules are not a semantic ranking model.

A package version preserves source, PDF, extracted text, optional letter, context, coverage, task, author identity, contributor provenance, page counts and file hashes. Identical inputs reuse the version; changed inputs create a new one. Reviews bind to the full hash set and exact `version_id`.

Standalone letters reference an exact CV package/version and CV source hash. They remain drafts until composed into a reviewed package. A text revision records before/after artifacts and change notes; it does not mutate an old package.

See [CLI](CLI.md) for command syntax, [agent workflows](AGENT_WORKFLOWS.md) for request/result schemas and [operations](OPERATIONS.md) for review and migration acceptance.
