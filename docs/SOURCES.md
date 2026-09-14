# Sources, collection and honest coverage

[English](SOURCES.md) · [Русский](ru/SOURCES.md) · [Documentation](../README.md#documentation)

Career Copilot collects published vacancies through five adapters and can replay compatible saved responses offline. It does not discover every employer automatically or guarantee that a previously observed vacancy is still open.

![Source collection and fallback routes](assets/sources.en.svg)

## Provider reference

| Provider | Private configuration | Implemented route | Official reference |
| --- | --- | --- | --- |
| `greenhouse` | `board` | Public jobs list with `content=true` | [Greenhouse Job Board API](https://docs.greenhouse.io/job-board.html) |
| `lever` | `board` | Postings list, `limit=100`, bounded `skip` pagination | [Lever Postings API](https://github.com/lever/postings-api) |
| `ashby` | `board` | Public job-board endpoint with compensation requested | [Ashby Job Postings API](https://developers.ashbyhq.com/docs/public-job-posting-api) |
| `hh` | `employer_id` | Employer vacancies, `per_page=100`, bounded pages | [HH API documentation](https://api.hh.ru/openapi/redoc) |
| `corporate` | `url` | Static HTML containing JSON-LD `JobPosting` objects | [Schema.org JobPosting](https://schema.org/JobPosting) |

The adapter implementation is [sources.py](../src/job_search_agent/sources.py). Provider APIs offer more operations than this client implements. It performs read-only collection; application submission endpoints are not used. Current API behavior should be checked against the linked provider documentation when adding or changing a source.

The HH list can contain excerpts. Retrieve the full official posting through an allowed route before assessing mandatory requirements. Absence from an excerpt is not evidence that a requirement does not exist. Corporate HTML without usable JSON-LD needs browser/manual research; the adapter is not a general JavaScript browser.

## Configure the source registry

Private `settings.json` contains `sources`. Each entry needs a stable `id`, `provider`, `company_id` and the provider's board/employer/URL value. Optional fields include `company_name`, `market`, `enabled`, `allowed_hosts`, `include_title`, `user_agent`, request interval, page budget and explicit proxy settings. [Configuration](CONFIGURATION.md) lists defaults and limits.

`include_title` is a case-insensitive regular expression applied after the full snapshot is stored. It is a search filter, not a level or fit judgment. `count` reports retained cards; `observed_total` reports observed items before filtering and must be interpreted with the source attempt/history rather than as a market total.

Company size research needs a named metric, value or range, date/period, organizational scope, source URL and confidence. An unknown headcount remains unknown. Marketing language and the candidate's impressions are not independent corroboration.

## Collection and replay

Prefer an official API/ATS, then the official website, an ordinary browser for dynamic content, a search lead, and manual import. Use only routes allowed for that source. A failed route does not authorize a bypass.

```sh
uv run ajh --home /absolute/private/career-workspace discover --source SOURCE_ID
uv run ajh --home /absolute/private/career-workspace discover --source SOURCE_ID --replay snapshots/SOURCE_ID/SNAPSHOT.txt
```

A replay path is relative to the private workspace. Save original response/page bytes with URL, retrieval time, access method, coverage and hash. Replay expects the adapter's JSON response or HTML with JSON-LD. Screenshots and arbitrary prose need explicit manual normalization; they are not API responses. A manual JSON envelope uses `{"vacancies": [...]}` and the `manual` parser for offline ingestion.

Replay does not make a network request, refresh live source health or establish current availability. Replayed observations are historical; vacancy availability is unknown until a current authorized check establishes otherwise. Existing research annotations and document history must survive recollection and replay.

## Results and failure states

| Source state | Interpretation | Next action |
| --- | --- | --- |
| `success_nonempty` | Successful collection retained vacancies | Review scope, titles and freshness |
| `success_empty` | This successful attempt retained no vacancies | Inspect filters and observed coverage; do not claim the company has no jobs |
| `partial` | Some results were saved but collection did not finish | Inspect `failure_status` and limits; retain saved records |
| `cooldown` | Next permitted attempt has not arrived | Wait until `next_attempt` |
| `rate_limited` | Provider returned HTTP 429 | Respect Retry-After and persisted cooldown |
| `blocked`, `auth_required` | Access is denied or requires authentication | Stop that route; use a permitted alternative |
| `timeout`, `network_error`, `http_error` | Retrieval failed | Preserve prior success and diagnose the specific failure |
| `parse_changed` | Response no longer matches the parser | Inspect saved bytes and update/test the adapter |
| `redirect_requires_review` | Redirect was not followed | Review destination and source configuration |
| `budget_exhausted`, `response_too_large` | A configured/runtime limit stopped collection | Adjust an appropriate budget after inspection |

Source failures often appear as entries in a JSON list with process exit code zero. Check each result's `status`, not only the exit code. The journal retains last attempt, last success, count, HTTP status and next permitted attempt. An error does not erase successful observations or prove a vacancy closed.

Availability states such as `open`, `archived`, `expired_copy` and `unknown` describe evidence about the posting. A fresh successful official list can support `open`; missing data, blocked access or stale copies do not support a confident live-status claim.

## Limits and access policy

The default run budget is 20 requests. Page count defaults to 3 and is clamped to 1–20; inter-request spacing is clamped to 4–30 seconds, including a host-level record across commands. The default source interval is 3,600 seconds. The HTTP client has a 25-second timeout, refuses automatic redirects and rejects responses larger than 5 MB after receiving them. These are runtime controls, not provider rate-limit guarantees.

HTTP 429 stores Retry-After/cooldown; repeated rate limits increase the wait, with at least an hour after the third recorded attempt. There is no automatic retry loop, daemon or scheduler. Earlier successful pages are retained on a later failure.

Use HTTPS and approved hosts. Embedded credentials and obvious local/private literal addresses are rejected, but this is not a complete DNS-rebinding defense. Treat source configuration as trusted private input. Do not claim comprehensive network sandboxing.

The client ignores ambient proxy configuration. Proxy use requires `proxy_allowed: true` and `proxy_env` naming an environment variable for that source. Keep credentials outside JSON and Git. Do not rotate proxies after blocks; no CAPTCHA bypass, login bypass or anti-bot evasion. LinkedIn proxy routes are forbidden. Browser and search fallback are agent/user work outside this CLI.

Never send a CV, contact a recruiter or submit an application because collection succeeded. Each external action requires its applicable user authorization.

## Adding an adapter

Check the provider's primary documentation and permitted read-only route. Define source fields and limits, then make the parser operate on saved bytes without a network dependency. Preserve stable external IDs, original URLs, provenance and content scope. The transport saves originals before normalization and reports partial coverage explicitly.

Use synthetic fixtures for empty lists, duplicates, schema changes, pagination, 429, authorization failures, malformed JSON, JSON-LD and ambiguous identity. Do not add application or messaging methods under the label of a collection adapter.
