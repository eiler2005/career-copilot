# Configuration reference

[English](CONFIGURATION.md) · [Русский](ru/CONFIGURATION.md) · [Documentation](../README.md#documentation)

Configuration is private JSON in the initialized workspace. The CLI has no implicit candidate data directory. Keep credentials in environment variables and personal priorities outside the public checkout.

## Workspace selection and environment

| Setting | Meaning |
| --- | --- |
| Global `--home ABSOLUTE_PATH` | Explicit private workspace; place before the subcommand |
| `AI_JOB_HUNTER_HOME` | Default workspace when `--home` is omitted |
| `AJH_PRIVACY_DICTIONARY` | Private dictionary path for publication checks |
| Git `ajh.privateDictionary` | Local dictionary fallback |
| Source `proxy_env` | Name of a source-specific environment variable holding its proxy URL |

`--home` overrides the environment value. `privacy` and `restore` do not require an active workspace. Supported platforms are macOS and Linux; locking uses `fcntl`. A Codex/Claude session supplies model capabilities separately from Python installation.

## settings.json

The initial effective settings are:

```json
{
  "sources": [],
  "policy": {
    "bigtech_company_ids": [],
    "company_levels": {},
    "russia_director_only": false,
    "market_effort": {}
  },
  "max_requests_per_run": 20,
  "weeks": 6,
  "hours_per_week": 6,
  "model_routing": {
    "openai": "gpt-6-astra",
    "claude": "claude-opus-5"
  }
}
```

| Field | Default and interpretation |
| --- | --- |
| `sources` | Empty: no network sources are enabled by initialization |
| `max_requests_per_run` | 20 total discovery requests |
| `weeks` / `hours_per_week` | 6 / 6 for the baseline learning plan |
| `pdf_font` | Optional installed Unicode TTF; otherwise common DejaVu/Arial locations are checked |
| `policy.bigtech_company_ids` | Empty private company-ID list; selects employer-specific level rules |
| `policy.company_levels` | Empty map; each company uses `accepted`, `below`, `source` |
| `policy.russia_director_only` | False; when true, non-selected Russian employers use the director-title filter |
| `policy.market_effort` | Empty planning metadata; does not impose a result quota |
| `model_routing` | Documents environment flagships; it does not start models or grant API access |

Company-specific level mapping example, using fictional labels:

```json
{
  "example-systems": {
    "accepted": ["Example-Senior-Leadership"],
    "below": ["Example-Associate"],
    "source": "https://example.invalid/fictional-level-policy"
  }
}
```

A real mapping requires a checked source, the vacancy's `level.raw` and `level.source`, and a substantive scope/role-family assessment. Unknown labels stay unresolved. Title filters are mechanical heuristics, not proof of responsibilities.

## Registered Telegram channels

Use this private `sources` entry:

```json
{"id":"telegram-1001","provider":"telegram","board":"fictional_jobs","name":"Example board","collection_mode":"external_export","enabled":true,"limit":100,"lookback_days":90}
```

`id` contains the numeric channel ID from the export; `board` is its public username without @. No `company_id` is needed. An external runner translates `limit` and `lookback_days` into exporter `--limit` and timezone-aware `--since`; these settings do not install a scheduler. Set `enabled: false` and `disabled_reason` to keep paused channels visible. `discover` skips disabled entries and reports `external_export_required` for enabled channels without HTTP. Import with `vacancy import-telegram`.

## Source fields

The disabled [example configuration](../examples/source-config.json) can be adapted privately. Merge the `sources` value into the existing settings; do not discard unrelated settings.

| Field | Required/default | Effect |
| --- | --- | --- |
| `id`, `provider`, `company_id` | Required (`company_id` not needed for aggregators) | Stable source/company identity and parser; aggregators and LinkedIn Salaries assign employers per listing |
| `board` | Greenhouse, Lever, Ashby, SmartRecruiters, Workable, Recruitee | Public board token or company subdomain |
| `employer_id` | HH | Employer filter |
| `query` | HH text search, Remotive, Jobicy, Get on Board, Trudvsem | Search text or tag; for HH it switches to vacancy search without an employer filter |
| `area`, `period`, `professional_role`, `experience`, `schedule` | HH text search, optional | Passed to the HH search |
| `category`, `tag`, `geo`, `limit`, `region` | Remotive/Jobicy/Remote OK/Trudvsem, optional | Provider filters (see [sources](SOURCES.md#provider-reference)) |
| `url` | Corporate/manual or LinkedIn Salaries | Source endpoint/page; LinkedIn Salaries uses `https://linkedinsalaries.com/jobs.json` |
| `enabled` | True when omitted | Participates in discovery |
| `company_name`, `market` | Optional; market defaults `unknown` | Initial company label and vacancy market |
| `include_title` | Optional regex | Case-insensitive title filter after snapshot preservation |
| `skip_off_profile` | False | Do not add cards that the [profile relevance](RELEVANCE.md) screen marks `off_profile`; the snapshot keeps them and `source_health.screened_out` counts them |
| `max_pages` | 3; clamped 1–20 | Bounded pagination for paginated providers |
| `request_gap_seconds` | 4; clamped 4–30 | Host/request spacing |
| `interval_seconds` | 3600; minimum 4 (Remotive 21600) | Persisted next permitted attempt; provider minimums apply |
| `allowed_hosts` | Optional list | Explicit host allowance; endpoint host is included |
| `user_agent` | Read-only client identity | HTTP User-Agent |
| `proxy_allowed` | False | Explicit source permission for proxy use |
| `proxy_env` | Optional | Proxy environment-variable name; requires permission |
| `proxy_mode` | `always` | `always` sends every request through the proxy; `fallback` requests directly and retries once through the proxy only after a timeout or failed connection, never after an HTTP refusal (see [routes](SOURCE_ARCHITECTURE.md#network-routes-and-the-proxy)) |

The client disables redirects and ambient proxy inheritance, uses a 25-second timeout and a 5 MB post-download response check. See [sources](SOURCES.md) for retry and access policy. Source rules are not a full network sandbox.

## LinkedIn Salaries source

Add this object to the private `settings.json` → `sources` array, preserving other settings. It is disabled until you deliberately set `enabled: true`; source selection for replay also requires the source to be enabled.

```json
{
  "id": "linkedinsalaries-public",
  "provider": "linkedinsalaries",
  "company_id": "linkedinsalaries-index",
  "url": "https://linkedinsalaries.com/jobs.json",
  "enabled": false,
  "allowed_hosts": ["linkedinsalaries.com"],
  "max_pages": 1,
  "interval_seconds": 86400,
  "request_gap_seconds": 4,
  "proxy_allowed": false
}
```

The URL selects the publisher's public `jobs.json` dataset, not a LinkedIn page or the site's HTML. `company_id` is a required source identifier here; the parser assigns each listing a separate employer ID rather than assigning every job to the aggregator.

The example's 86,400-second interval suggests at most a daily collection attempt; it does not change the general 3,600-second default or install a scheduler. This provider reads one response, so higher `max_pages` values do not request more records. Global request budgets, host spacing, cooldown and response-size limits still apply. Keep `proxy_allowed: false` and omit `proxy_env`; this route does not use proxies.

After enabling the source:

```sh
uv run ajh --home /absolute/private/career-workspace discover --source linkedinsalaries-public
uv run ajh --home /absolute/private/career-workspace discover --source linkedinsalaries-public --replay snapshots/linkedinsalaries-public/SNAPSHOT.txt
```

Use the actual saved snapshot path for `SNAPSHOT.txt`. Replay reads the original dataset JSON from private storage and makes no network request.

An optional `include_title` expression filters locally after snapshot retention. It does not alter the dataset request, map a career track or establish seniority. Compensation retains the source's `salaryCite` text and `salaryUsdMo` figure with `aggregated` reliability; unavailable numeric data stays null. New listings remain `availability: unknown` until a separate official employer/ATS check. See [source scope and field meanings](SOURCES.md#linkedin-salaries-salary-context-for-new-leads).

## Candidate constraints

`candidate` is an optional private object used by matching as mandatory constraints. Missing values stay unknown; nothing is inferred.

| Field | Effect |
| --- | --- |
| `work_authorization` | Map of country or region → `yes` / `no` / `unknown`; a requirement with `authorization` becomes a match or a confirmed mismatch only from `yes` or `no` |
| `work_countries` | Where the candidate can work; compared with a vacancy's explicitly listed allowed countries |
| `languages` | ISO language codes the candidate works in; a required language outside the list is a question, not a rejection |

Changing `candidate` marks affected assessments as needing an update.

## Profile relevance

`settings.json → relevance` tunes the screen that decides which vacancies fit the candidate's profile: `target_level` (`top`, `near`, `lead`, `any`), per-market `market_levels`, `top_companies` and `program_roles`, extra `roles` per track, `levels`, `exclude_title`, `ignore_in_title` (phrases such as banking products removed before the function check), explicit `domains`, extra `vocabulary` per domain, saved `queries` (`{name, query, include}`) and `extend_defaults`. Without the section the screen uses built-in words, `policy.tracks`, and domains derived from fact tags and `policy.interests`. `policy.russia_director_only` and `policy.bigtech_company_ids` also shape the level check. Replace the section with `ajh relevance set PATH`. Full rules, query grammar and tuning: [profile relevance](RELEVANCE.md#configuration).

## Search campaigns

`campaigns` is an optional list in `settings.json`. Fields and matching rules are in the [data model](DATA_MODEL.md#search-campaigns). Edit it with `ajh campaigns set PATH` or through a `campaign_upsert` request from the dashboard; both validate the whole list. Example with fictional values:

```json
[
  {
    "id": "intl-platform",
    "name": "International platform product",
    "market": "intl",
    "track": "product",
    "role_titles": ["Product Lead", "Head of Product"],
    "work_countries": ["Canada"],
    "work_modes": ["remote", "hybrid"],
    "languages": ["en"],
    "salary": {"min": 150000, "currency": "USD", "period": "year", "gross_net": "gross"},
    "exclusions": ["gambling"]
  }
]
```

Role titles, levels and exclusions match whole words. A campaign never widens where the candidate may legally work and never changes an assessment.

## Facts and policy changes

Use `facts import PATH` to version evidence; do not treat `facts.json` as a CV template. Imported facts need unique IDs, sources and verification states `verified`, `self_reported` or `conflicting`. Profiles must contain exactly `product` and `technical-leadership`.

A local source is a real file resolved relative to the imported JSON. A descriptive string such as “candidate interview” is not a file reference. HTTP(S) references are retained as URLs; import does not itself verify their claims. See [data model](DATA_MODEL.md).

After changing facts, company information, vacancy requirements or level policy, rerun evaluation. Existing packages retain their original context; build and review a new version when the content changes.

## Features configured elsewhere

The CLI does not install a scheduler, manage a calendar, enforce a monetary model budget, call an LLM API, encrypt backups or submit applications. Host model availability, consent for external services, off-device backup, retention and allowed manual source routes need explicit environment/operational setup. Adding an unsupported JSON key does not create those features.
