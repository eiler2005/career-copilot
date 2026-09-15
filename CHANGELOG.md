# Changelog

Notable changes to Career Copilot. Dates are release dates; there are no published version tags yet.

## 2026-09-15 — Collection, clear conditions and vacancy tabs

### Added
- **Vacancy conditions.** Adapters and added vacancies store `conditions`: the original salary range with currency, period and tax basis (never an invented monthly figure), a provider conversion kept separately, work format, employment, required languages, allowed work geography (remote without a country list stays unknown) and publication dates, each with its source. `ajh maintenance reextract-conditions` derives them for existing vacancies.
- **Search campaigns** in `settings.json` (market, track, roles, levels, countries, format, language, employment, salary, exclusions) with per-criterion `match`/`mismatch`/`unknown` and a basis; preferences only. `ajh campaigns list|set|match`; dashboard editor through `campaign_upsert` requests with a version check.
- **Collection runs.** `discover` records new and changed vacancies, possible duplicates across sources and source errors with the last success (`ajh collection runs`). A misconfigured source becomes `config_error` without stopping the others.
- **Add a vacancy** by public link (hh.ru API, JSON-LD, page text) or pasted text: `ajh vacancy add` or the dashboard form. The original is kept; unknown companies are created for review.
- **Dashboard.** Vacancy cards in the order title and pay → company and place → conditions → fit and campaigns → next step → dates and source → actions; a market switcher; vacancy tabs Vacancy · Fit · Company · CV · Preparation; personal decision, coding flag, assessment, CV tailoring and vacancy brief requests; a Sources section with collection, campaigns and the request and task queue.

### Changed
- A shorter excerpt never replaces a more complete retained text, an unknown availability from a later listing never overwrites a recorded one, and only an employer's own board listing sets the verification date during collection.

## 2026-09-15 — Requests, agent tasks and accurate pipeline stages

### Added
- **Request queue.** The dashboard stores validated requests (`POST /api/requests`) in its state directory instead of editing the journal. `ajh inbox import|list|apply|reject` brings them into `inbox_requests` and applies them oldest first with a record-version check, so a record changed in between becomes a visible `conflict` rather than a lost update.
- **Agent tasks.** Requests that need authored or researched work become `tasks`. `ajh tasks next` hands the oldest one to an agent session with an activity template; the task follows the real activity (`running`, `done`, `blocked`, `failed`) and is never shown as done without a finished activity.
- `Store.version` and `Store.patch` (compare-and-set with a `record_updated` event holding the fields before and after); every dashboard record exposes its `version`.
- Product research of 2026-09-15 (English and Russian) linked from the README.

### Fixed
- Pipeline stages: interview practice and feedback no longer count as an employer interview; "applied" requires a user-confirmed submission with `sent_at` and evidence; an employer response with status `interview` or `offer` moves a vacancy to the interview stage; stage dates come from `sent_at` and `received_at`. A package flagged as submitted without a confirmed submission gets a reminder instead of the "applied" stage.

## 2026-09-15 — Clear vacancy cards and in-browser documents

### Changed
- Vacancy cards and details show the company with country and city, a short verbatim description, open/closed status with check age, the posting link, the full description and the learning plan; everything technical moved into a collapsed block. Filters are collapsed by default.

### Added
- Short descriptions quoted from retained postings or from the research section naming the vacancy (`display.description`).
- In-browser reader for Markdown and text files with a download button; long single-line postings are split into sections and short paragraphs; shared research files highlight the selected vacancy's row.

## 2026-09-15 — Availability checks, pipeline and a cleaner journal

### Added
- **Availability checks.** `ajh availability check` reads stored posting URLs (public addresses only, at most five redirects, no login/CAPTCHA/bot-protection bypass) and records `status`, `reason`, `confidence`, visible evidence, HTTP status and time per vacancy, with a 20-entry history and an event. A human-recorded closed state is never reopened by a medium-confidence signal; it becomes `conflicting`. The dashboard runs the same check on demand through `POST /api/availability/check` when started with `--state-dir`; `ajh availability import` brings those results back into the journal.
- **Pipeline and reminders.** A dashboard section places each active vacancy in its furthest stage (found → assessed → documents → reviewed → applied → response → interview) with stage dates, days in stage and rule-based reminders; the overview shows the most important ones.
- **Data age.** "Checked N days ago" on vacancies with fresh / aging / stale / never highlighting and a filter.
- **Content translations.** `ajh translations export|import` stores Russian and English renderings of journal text as `text_translations` with the translator's model identity; originals are never rewritten. The dashboard switches between translated and original text and uses the translations in plan PDFs.
- **Maintenance.** `ajh maintenance dedupe` and `ajh maintenance rename-artifacts` (dry run unless `--apply`) archive duplicate results and give existing files readable names, with manifests and events.

### Changed
- `evaluate` and `learn` no longer accumulate duplicates for the same vacancy and track: an unchanged conclusion keeps the current record; a changed one becomes current and the previous result moves to `superseded_records`. `current_learning` joins `current_assessments`.
- Generated files use `<date>-<context>-<sha8><suffix>` names (evidence, activity inputs, learning plans, reviews, imports, facts history, source snapshots) and reuse identical content; preserved legacy names are shortened to 200 bytes.
- The container image creates a writable `/data/state` volume for availability results; the workspace mount stays read-only.

### Security
- The availability endpoint accepts only IDs of stored vacancies (never arbitrary URLs), requires JSON, a custom header and a same-host `Origin`, limits batches to 10, serialises runs and caches results for 10 minutes. DNS results must be public addresses before every request and redirect.

## 2026-09-15 — Plans, sources and history

### Added
- Complete preparation plans on the page with PDF (Russian/English) and Markdown downloads; superseded plan versions behind a toggle.
- Source catalog: configured collectors with schedule and results, plus every website referenced by the journal with individual links.
- History as a day-grouped timeline with times, readable summaries and linked records.
- Vacancy references with company, found date, availability and a direct posting link wherever vacancies appear.

## 2026-09-14 — Public HTTPS access and dashboard quality

### Added
- Optional authenticating Caddy gateway (`compose.public.yaml`): TLS via TLS-ALPN-01 behind an exact-SNI edge route, Basic Auth, loopback-only publication.
- Shareable URL state, faceted filters, localized countries, labels for journal fields, journal freshness in the footer, file list.

### Fixed
- Presentation defects found in a journal audit: alphabetical "latest vacancies", next actions from completed work, unreachable `.tex` files and import records, hidden never-checked sources, duplicate-looking assessments and local filesystem paths in the browser.
