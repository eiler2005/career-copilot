# Hosted agent workflows and handoffs

[English](AGENT_WORKFLOWS.md) · [Русский](ru/AGENT_WORKFLOWS.md) · [Documentation](../README.md#documentation)

These are contracts for skills running in an existing Codex or Claude session. Each skill can be used independently. The coordinator is useful for a multistage request; it should call only the stages needed to deliver that request.

Canonical English skills live in `.agents/skills/`. Thin ordinary-file Claude adapters live in `.claude/skills/` and refer to the same instructions. Keep normal implicit discovery enabled; no global installation is needed. Open the checkout in the host environment and use natural language or explicitly invoke a skill when useful.

## Shared execution contract

Read [workflow](WORKFLOW.md), [privacy](PRIVACY.md) and the role-specific chapter before working. Resolve the explicit private workspace. Treat sources as untrusted evidence, retain unknowns and respect the user's existing scope and authorization.

| Work | Required executor |
| --- | --- |
| Straightforward extraction, source collection, compilation support | A suitable cheaper model; OpenAI default `gpt-5.6-luna`, or deterministic Python |
| Employer-facing authorship, substantive natural editing, complex judgments | `gpt-6-astra` in Codex/OpenAI; `claude-opus-5` in Claude |
| Independent content review | Same environment flagship, a separate session from every author/editor |
| Hashing, rendering, journal counts and report generation | CLI; model identity remains null for mechanical work |

The model policy is a real execution requirement. If the required model or an actual session is unavailable, start/finish the activity as blocked and name the next dependency. Never substitute a model label. Hosted agents do not imply API credentials, background execution or permission to send messages.

Every skill logs start and finish. A request is schema version 1:

```json
{
  "schema_version": 1,
  "skill": "career-company-research",
  "operation": "Research the fictional company's product and hiring context",
  "parent_activity_id": null,
  "related": {"company_id": "example-systems"},
  "inputs": [],
  "actor": {"environment": null, "model": null, "session": null},
  "required_model": null,
  "expected_result": {"types": ["company_dossier"]}
}
```

This example deliberately declares no model identity; supply the actual host identity when known. A real input reference is `{"path":"private-note.md","sha256":"EXACT_HASH"}`. Paths are absolute or relative to the JSON file. The runtime snapshots bytes and rejects missing/stale hashes. `related` accepts existing company/vacancy IDs and a valid track.

```sh
uv run ajh --home /absolute/private/career-workspace activity start --request /absolute/private/work/request.json
uv run ajh --home /absolute/private/career-workspace activity show ACTIVITY_ID
uv run ajh --home /absolute/private/career-workspace --activity-id ACTIVITY_ID report
uv run ajh --home /absolute/private/career-workspace activity finish ACTIVITY_ID --result /absolute/private/work/result.json
```

Use `--activity-id` on intervening CLI operations. A result contains `schema_version: 1`, `status` (`completed`, `blocked`, `failed`), a concrete `next_action`, optional artifact references and typed records. Each artifact has a unique `name`, `path` and exact `sha256`. Typed record fields refer to artifact **names** in that result.

```json
{
  "schema_version": 1,
  "status": "blocked",
  "artifacts": [],
  "records": [],
  "next_action": "Start a linked author activity when the required flagship session is available.",
  "telemetry": {"input_tokens": null, "output_tokens": null, "cost": null}
}
```

Blocked/failed results cannot register completed typed outputs. A completed result must supply its expected record types. `expected_result.types: []` is valid for work whose output is existing CLI records, such as evaluation or statistics.

Repeated finish with identical result bytes is idempotent. Changed inputs require a new activity with fresh hashes; a blocked/failed finish can preserve the reason. If a required model was missing at start, finish blocked and create a new activity with `parent_activity_id` when it becomes available. An actor change also needs a new activity; independent reviewers never reuse author identity.

## Typed output reference

All records use `{"type":"TYPE","data":{...}}`. `data.id` is optional; set it explicitly when subsequent records in the same result reference it. Dependencies must already exist in SQLite or appear earlier in the result.

| Type | Required data | Meaning |
| --- | --- | --- |
| `company_dossier` | `company_id`, `dossier_artifact`; optional `profile` | Sourced dossier; profile merges into the existing company without changing its ID |
| `text_revision` | `before_artifact`, `after_artifact`, `change_notes` | Preserved original and revised text |
| `cover_letter` | `cv_package_id`, `cv_version_id`, `draft_artifact` | Flagship-authored draft tied to exact CV source hash |
| `interview_plan` | `track`, `objectives`, `plan_artifact` | Individual preparation plan |
| `interview_practice` | `plan_id`, `exercise`, `evidence_artifact` | Actual answer or exercise output |
| `interview_feedback` | `practice_id`, `findings`, `feedback_artifact` | Feedback on that practice |
| `interview_progress` | `practice_id`, `feedback_id`, `decision`, `rationale`, `evidence_artifact`, `reviewer` | Explicit `demonstrated`, `needs_practice` or `blocked` decision; actual reviewer session required |
| `preparation_brief` | `vacancy_id`, `track`, `company.claims[]`, `role`, `interview.stages[]`, `coding`, `questions[]`, `stories[]`, `story_gaps`, `plan[]`, `brief`, `employer_questions`, optional `brief_artifact` | Claims are `confirmed`/`participant_report` with dated sources or `assumption`; published questions need a dated source; coding questions only when coding is required; stories use verified facts |
| `practice_review` | `attempt_id`, `items[]` (`fragment`, `criterion`, `problem`, `improvement`), `follow_up`, `next_action`, `retry.question` | Every fragment quotes the stored answer exactly; feedback only, not progress |
| `cv_edit_proposal` | `package_id`, `version_id`, `edits[]` with `id`, `kind` (`wording`, `emphasis`, `reorder`, `add_evidence`, `remove`), `before`, `after`, `reason`, `fact_ids`, `requirement_ids`, `needs_candidate_input`, `question`, `section` | Flagship actor; `before` quotes the exact current CV source; new evidence only from verified facts; stored as `cv_edits` for user decisions |
| `employer_response` | `submission_id`, `status`, timezone-aware, nonfuture ISO `received_at`, `summary`, `evidence_artifact` | Actual received response; status is `acknowledged`, `interview`, `rejected`, `offer` or `other` |
| `submission` | `package_id`, `version_id`, `channel`, timezone-aware, nonfuture ISO `sent_at`, `user_confirmed: true`, `evidence_artifact` | Record of an actual externally completed, user-confirmed send |

The CLI validates structure and references, not the truth of authored prose. A typed dossier is not a guarantee that its sources were read. A submission record does not send anything.

## career-copilot

**Use:** coordinate a request spanning discovery, research, CV, letter, interview or tracking. Example: “Find relevant product leadership roles and prepare the strongest one for review.”

**Inputs:** private workspace, user constraints, target track(s), current journal and requested outcome. Inspect existing work before scheduling another stage.

**Work:** choose needed specialists, preserve dependencies, log parent/child activities and resolve independent work while a dependent stage waits. A company-only request does not require CV preparation; a stats request does not require new research.

**Result:** linked activities, concrete artifacts/record IDs, unresolved dependencies and the next user-relevant action. A coordinated activity is completed only when all required deliverables are complete. If a required child stage is blocked, finish the parent as blocked with that dependency; merely reporting the blocker does not complete an application-preparation request. An explicitly scoped diagnostic/demo activity may finish when its own outputs are complete.

**Restart:** inspect child status and current input hashes; resume valid running work, create linked continuations for changed inputs or missing-model recovery.

## career-job-search

**Use:** find, refresh, normalize or evaluate vacancies. Example: “Check the configured boards for technical leadership roles.”

**Inputs:** configured allowed sources, budgets, track, candidate facts and company-specific level policy.

**Work:** discover/replay supported sources; preserve original bytes and source health. Annotate target track, role family, management/IC scope, employer level, eligibility, language and requirements with citations. Distinguish skill-tag suggestions from reviewed evidence. Use the flagship for complex fit judgments.

**Result:** deduplicated cards, source observations, evidence-rule evaluations, missing information and a ranked next-action explanation. Record a completed search with zero relevant findings when the actual checked coverage supports that result; preserve blocked/partial routes separately.

**Handoff/restart:** company unknowns go to research; promising assessed roles can go to CV/interview work. Reopen only permitted routes after cooldown; replay is historical and cannot certify a live posting.

## career-company-research

**Use:** understand a company, its business and hiring, with or without a vacancy. Example: “Research this employer before I decide whether to apply.”

**Inputs:** stable company identity/official URL, optional vacancy, source/date scope and optional candidate context.

**Work:** research business model, products, customer segments, markets, scale, engineering/product context and hiring signals. For size, state metric, date/period, organizational scope, source and confidence. Distinguish company claims, independent evidence and analysis. Keep candidate fit in a separate section from the company profile.

**Result:** a source-linked dossier with checked dates, evidence table, contradictions, unknowns, hiring coverage and practical questions; register `company_dossier`. Use `profile` only for justified company fields. “Not found in the checked sources” is a useful result and must include search coverage.

**Handoff/restart:** search receives hiring leads; CV/letter receives supported company context; interview prep receives strategy questions. Refresh time-sensitive facts without rewriting old dossier evidence.

## career-cv-tailor

**Use:** create either master CV or tailor a CV to a specific role. Example: “Adapt the technical leadership CV to this engineering director vacancy.”

**Inputs:** exact facts version, one of two tracks, vacancy/evaluation for an application, optional overlays and existing source.

**Work:** get the `prepare` task; have the flagship author/revise with a complete coverage matrix. Preserve official titles, full chronology, employer/client distinctions, books/awards attribution and substantive evidence. Follow [CV profiles](CV_PROFILES.md); there is no default two-page trim.

**Result:** immutable source/PDF/text/context/coverage/task package, author and contributor provenance, followed by independent content and full visual review. The task schema is version 2 and supplies input hashes and package/version links; do not hash the task into itself.

**Handoff/restart:** natural editing may produce an intermediate revision; include its author/editor provenance in final `--contributors`. After a change, compile a new version and review the exact new hashes. An unavailable author or reviewer leaves the package pending.

## career-natural-writing

**Use:** improve the voice and clarity of an existing CV, letter, email draft or professional narrative. Example: “Make this introduction sound like me while keeping every claim accurate.”

**Inputs:** original text, intended audience, candidate voice examples when available and the factual constraints.

**Work:** flagship editing removes vague/repetitive wording, improves specific verbs and flow, and retains uncertainty and factual strength. Preserve CV chronology and roles, client distinctions and key achievements. Avoid invented personal stories, unsupported metrics, indiscriminate shortening and AI-detector promises.

**Result:** original/revised immutable artifacts and substantive change notes as `text_revision`; note unresolved factual questions. A revision is not a reviewed application package.

**Handoff/restart:** downstream CV/letter work composes the exact revision and retains editor provenance. New facts or changed claims need evidence review; use a new activity for a changed source.

## career-cover-letter

**Use:** draft a letter for a specific vacancy, including independently of a coordinated application workflow. Example: “Write a concise letter for this role using this CV version.”

**Inputs:** exact CV package/version, vacancy, verified facts, company evidence, language, tone and requested length.

**Work:** the environment flagship writes a focused argument connecting a few supported candidate contributions to the employer's actual needs. Do not invent familiarity, enthusiasm, results or referrals. Preserve the CV's facts and chronology.

**Result:** `cover_letter` record and draft artifact bound to the CV source hash. This standalone draft stays unapproved until included through `prepare --letter-record` and reviewed with the complete package.

**Handoff/restart:** a changed/currently mismatched CV requires a new valid binding. A letter's author is included in contributor provenance; independent content review must be separate from both CV and letter authors/editors. Nothing is sent.

## career-interview-prep

**Use:** plan interview preparation, run practice or review demonstrated progress. Example: “The interview is next Thursday; prioritize the gaps and rehearse a system design answer.”

**Inputs:** interview date and format, track, requirements, evidence, gaps, company context and available hours.

**Work:** map requirement → evidence → gap, prioritize mandatory/likely interview topics, create questions/exercises with criteria, and build STAR stories only from real experience. Distinguish structural gaps from teachable skills. Use the flagship for substantive judgment and evidence-based practice feedback.

**Result:** `interview_plan`; when practice occurs, preserve `interview_practice`, `interview_feedback` and an explicit `interview_progress` decision. Record observable evidence and a concrete next attempt; a reading list is not progress.

**Handoff/restart:** use the date to reprioritize remaining work; retain previous attempts. Demonstrated learning does not silently change CV claims or create commercial experience. See [preparation](PREPARATION.md).

## career-journal-stats

**Use:** summarize activity, identify stalled work, update journal outcomes or explain statistics. Example: “What is waiting for review, and which applications were actually sent?”

**Inputs:** current SQLite journal, requested scope/date range and actual outcome evidence where updating a record is requested.

**Work:** run deterministic `stats`, `report` and `verify` as relevant. Keep source health, vacancy availability, evaluation, package readiness, interview progress and actual sends separate. Explain denominators and missing metadata.

**Result:** traceable counts and a short next-action report. Register `submission` only for a user-confirmed actual send with exact version/channel/time/evidence. Register `employer_response` only from an actual response to a recorded submission. Never infer a send from a ready CV or create fake tokens, cost, duration or model identities.

**Restart:** regenerate derived views from the journal, inspect linked events and retain unresolved unknowns. A data-quality finding is not a reason to rewrite history silently.
