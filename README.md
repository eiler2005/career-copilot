# Career Copilot

[English](README.md) · [Русский](README.ru.md)

![Career Copilot — evidence-led career work](docs/assets/hero.svg)

**Turn a private career history into a focused job search, credible CVs and better-prepared interviews.** Career Copilot gives Codex and Claude eight independent skills backed by a local evidence journal, versioned documents and a readable browser overview.

Start with the result you need: research an employer, find suitable roles, tailor a CV, improve a paragraph, write a letter, practice an interview or understand what is stalled. A coordinator connects stages when your request needs several of them.

| You want to… | Skill | Concrete result |
| --- | --- | --- |
| Move a search through several stages | `career-copilot` | Linked work, dependencies and next actions |
| Find and assess roles | `career-job-search` | Source-backed vacancies and requirement/evidence assessments |
| Understand an employer | `career-company-research` | Business, products, markets, scale and hiring dossier |
| Build or tailor a CV | `career-cv-tailor` | Versioned source/PDF/text, coverage and review handoff |
| Make existing writing sound natural | `career-natural-writing` | Original/revised text with factual meaning preserved |
| Write a targeted letter | `career-cover-letter` | Draft bound to an exact CV version |
| Prepare and practice for interviews | `career-interview-prep` | Prioritized plan, exercises, real STAR stories and feedback |
| See progress and record outcomes | `career-journal-stats` | Deterministic counts and evidence-backed application history |

## Two directions, one factual history

`product` covers product management and leadership: discovery, strategy, customer outcomes, commercialization and P&L. `technical-leadership` covers engineering management and senior technical leadership: architecture, platforms, reliability, delivery and teams.

There are exactly two master CVs. AI, payments, enterprise/API and other domains are overlays within them. Both draw from the same private fact set. Official roles, chronology, clients, publications and properly attributed awards remain traceable; there is no automatic two-page cutoff.

## Try it in a few commands

Requires macOS/Linux, Python 3.12+, [uv](https://docs.astral.sh/uv/getting-started/installation/) and a Unicode TTF font such as DejaVu Sans or Arial.

```sh
git clone https://github.com/eiler2005/career-copilot.git
cd career-copilot
uv sync --all-groups
uv run python scripts/demo_workflow.py --home /tmp/career-copilot-demo-EXAMPLE
uv run ajh --home /tmp/career-copilot-demo-EXAMPLE report --open
uv run ajh --home /tmp/career-copilot-demo-EXAMPLE stats
uv run ajh --home /tmp/career-copilot-demo-EXAMPLE verify
```

Use a new destination, with unused `-backup` and `-restored` siblings. The complete offline walkthrough imports synthetic evidence, evaluates both tracks, builds masters and an application package, records agent work, replays a saved response and verifies backup/restore. Its PDFs intentionally stay **pending review**; it never fabricates model authorship or an approval.

The local export is `report/index.html` inside that workspace. Source, PDF, text, coverage and author tasks are under `packages/`; `demo-results.json` records the actual run. Follow [getting started](docs/GETTING_STARTED.md) for the private setup and real authorship/review flow.

## Explore your workspace in a browser

The [private dashboard](docs/DASHBOARD.md) reads the existing SQLite journal and brings companies, vacancies, document versions, preparation, sources and history into one searchable interface. Open a record to inspect its evidence and nested fields. Vacancies show country, city and remote scope separately; ambiguous geography remains unknown and the original location stays visible.

The interface supports Russian and English, desktop and mobile, and needs no frontend build or external CDN. It only reads: changes still go through the CLI and agent workflows. Run it locally or use the included Docker configuration with a private SSH tunnel. Keep candidate data outside the image and public repository.

## How the pieces fit

![Hosted skills, public code and private workspace](docs/assets/architecture.en.svg)

The **public checkout** contains reusable Python, documentation, synthetic fixtures and repository-local skills. The **private workspace** contains candidate facts, companies, vacancies, source bytes, SQLite history, activity records and document versions. Select it explicitly with `--home` before the command; real data belongs in persistent external storage.

An existing **Codex or Claude session** does research, writing and judgment. Repository-local skill discovery is enabled normally, and each specialist can work independently. Employer-facing authorship and complex judgments use Astra (`gpt-6-astra`) in Codex or Opus (`claude-opus-5`) in Claude; independent content review uses a separate flagship session. Simple collection can use Luna. Missing required models produce a blocked handoff.

The **CLI** hashes and preserves inputs, collects supported sources, applies explicit evidence rules, renders documents and computes journal statistics. It has no embedded model API, automatic application sender or background scheduler.

## Sources and trustworthy progress

Six read-only adapters support Greenhouse, Lever, Ashby, HH, corporate pages with static JSON-LD and the public LinkedIn Salaries JSON dataset. The salary index adds leads with original pay wording and the provider's monthly USD figures; LinkedIn pages are never requested by that adapter, and discovered availability stays unknown. Original snapshots support offline replay. Collection records empty results, partial coverage, cooldowns and errors separately; a blocked page does not become “no vacancies.”

Availability, suitability, document readiness, demonstrated learning and actual submission are separate states. A technically valid PDF is not a reviewed CV. A ready package is not a sent application. Company size includes its metric, date, organizational scope and source; missing evidence remains unknown.

See [source behavior and official API references](docs/SOURCES.md), [data contracts](docs/DATA_MODEL.md) and [the complete workflow](docs/WORKFLOW.md).

## Documentation

| Guide | What it answers |
| --- | --- |
| [Getting started](docs/GETTING_STARTED.md) | Install, run the offline demo and connect private work |
| [Workflow](docs/WORKFLOW.md) | Inputs, results, ownership, stops and restart for every stage |
| [Agent workflows](docs/AGENT_WORKFLOWS.md) | Eight independent roles, activity JSON and typed handoffs |
| [CLI](docs/CLI.md) | Commands, output, identities, contributors and exit behavior |
| [Dashboard and deployment](docs/DASHBOARD.md) | Browser interface, SQLite reads, Docker, private access and updates |
| [Configuration](docs/CONFIGURATION.md) | Environment, source defaults, budgets and policy |
| [Data model](docs/DATA_MODEL.md) | Facts, records, immutable artifacts and version relationships |
| [CV profiles](docs/CV_PROFILES.md) | Two tracks, evidence coverage, role levels and acceptance |
| [Sources](docs/SOURCES.md) | Providers, access, replay, limits and failure interpretation |
| [Interview preparation](docs/PREPARATION.md) | Gap types, exercises, STAR and demonstrated progress |
| [Architecture](docs/ARCHITECTURE.md) | Public/private boundary and ownership of state |
| [Operations](docs/OPERATIONS.md) | Review, diagnostics, migration, backup and restoration |
| [Privacy](docs/PRIVACY.md) | Worktree, staged/history and release checks |
| [Contributing](CONTRIBUTING.md) | Development workflow and documentation parity |

Every guide has a full Russian counterpart in [docs/ru](docs/ru/GETTING_STARTED.md). Shared policy lives in these guides; Claude adapters refer to the canonical skills instead of maintaining another policy copy.

## Current limits

Semantic evidence matching, company-level interpretation, authorship, page inspection and progress assessment require real agent/user work. The initial CLI rules are intentionally conservative and do not replace that judgment. Browser/search fallback is manual; arbitrary JavaScript career sites are not automatically scraped.

The PDF renderer supports simple single-column Markdown. Model provenance is recorded and structurally checked, not independently proven by a model provider. Source configuration is trusted private input; network restrictions are not a complete sandbox. Local storage does not automatically encrypt backups or authorize sending personal data to hosted services.

## Contribute

Use only synthetic examples, preserve both languages and add meaningful checks for behavior changes:

```sh
uv run ruff check .
uv run ruff format --check .
uv run pytest
uv run python scripts/check_docs.py
```

Follow [CONTRIBUTING](CONTRIBUTING.md) and run the applicable local dictionary/Gitleaks checks from [PRIVACY](docs/PRIVACY.md) before publication. Real candidate material never belongs in public files or history.

[MIT license](LICENSE). The distribution `job-search-agent`, module `job_search_agent` and command `ajh` are retained for compatibility.
