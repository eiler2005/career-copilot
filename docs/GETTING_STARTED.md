# Get from installation to a reviewable workflow

[English](GETTING_STARTED.md) · [Русский](ru/GETTING_STARTED.md) · [Documentation](../README.md#documentation)

The offline walkthrough uses fictional data and no model API. It shows evidence import, both CV tracks, company research records, preparation plans, package versions, replay, journal statistics and verified recovery. Documents intentionally remain pending review.

## Install

You need macOS or Linux, Python 3.12+, [uv](https://docs.astral.sh/uv/getting-started/installation/) and a Unicode TTF font. Linux commonly uses DejaVu Sans; macOS commonly has Arial. Set a different installed font through private `settings.json` → `pdf_font` if rendering fails.

```sh
git clone https://github.com/eiler2005/career-copilot.git
cd career-copilot
uv sync --all-groups
uv run ajh --help
```

The repository name is Career Copilot; `job-search-agent`, `job_search_agent` and `ajh` remain the distribution/module/CLI compatibility names.

## Run the complete offline demonstration

Choose a **new nonexistent** absolute destination. Its sibling paths ending in `-backup` and `-restored` must also be unused.

```sh
uv run python scripts/demo_workflow.py --home /tmp/career-copilot-demo-EXAMPLE
uv run ajh --home /tmp/career-copilot-demo-EXAMPLE report --open
uv run ajh --home /tmp/career-copilot-demo-EXAMPLE stats
uv run ajh --home /tmp/career-copilot-demo-EXAMPLE verify
```

The script seeds only fictional facts, imports a real synthetic evidence file, records hosted-work handoffs, evaluates both tracks, prepares both masters and an application package, creates learning work and replays a saved Greenhouse response twice. It checks repeat-finish behavior and backup/restore consistency. No external request, application or model authorship is fabricated.

Inspect:

| Output | What to look for |
| --- | --- |
| `report/index.html` | Companies, vacancies, packages, reviews, learning and events |
| `demo-results.json` | The actual run's artifact/record references and verification results |
| `packages/` | Source, PDF, extracted text, coverage, context and agent task |
| `activities/` | Completed deterministic work and an honestly blocked required-model task |
| Sibling `-backup` and `-restored` directories | Manifest-checked copy and restored private workspace |

A passing integrity check with pending reviews is the expected outcome. The demonstration does not pretend that a flagship authored its mechanical CV or that a reviewer inspected it. Open the PDFs to see the renderer; real content/visual approval is a separate hosted-agent exercise.

A rerun must use a new destination; the script does not overwrite an earlier workspace or backup. Temporary storage is appropriate for the demo, not real career records.

## Start your own private workspace

Choose a persistent directory outside the public checkout:

```sh
uv run ajh --home /absolute/private/career-workspace init
```

Populate a private facts JSON with candidate details, evidence references and exactly `product` and `technical-leadership` profiles. Use the [data model](DATA_MODEL.md#candidate-facts) as a shape reference. Every non-URL evidence reference must be an existing file relative to the import JSON.

```sh
uv run ajh --home /absolute/private/career-workspace facts import /absolute/private/import/facts.json
uv run ajh --home /absolute/private/career-workspace record companies /absolute/private/import/company.json
uv run ajh --home /absolute/private/career-workspace record vacancies /absolute/private/import/vacancy.json
```

Records are replaced in full. Preserve fields when updating a card. Set target tracks and source-linked requirements before evaluating. Configure sources and level rules privately using [configuration](CONFIGURATION.md); the public source example is disabled until adapted.

## Work with Codex or Claude

Open the checkout in your existing agent environment. Repository-local skills are normally discoverable: no global installation or API key is added by this project. Claude adapters refer to canonical English instructions; user-facing work can be in the candidate's requested language.

Useful independent requests include:

- “Research this company's products, markets and hiring; keep unknown size figures unknown.”
- “Tailor the product CV to this vacancy and preserve every substantive fact in the coverage matrix.”
- “Improve the voice of this introduction without changing its claims.”
- “My interview is next Thursday. Prioritize the gaps and rehearse a real example.”
- “Show which documents await review and which applications were actually sent.”

The coordinator can combine stages when asked. Every skill starts/finishes an activity with actual actor metadata and hashed inputs/results. External text and complex judgments require Astra in Codex or Opus in Claude; a missing required model produces a blocked handoff. See [agent workflows](AGENT_WORKFLOWS.md).

## Complete a real package and preserve it

Use `prepare` to obtain the task, supply actual flagship-authored source and coverage, then have an independent flagship session review the exact version. Visual review covers every page and extracted text. [CLI](CLI.md) describes author/contributor and letter-version bindings; [operations](OPERATIONS.md) gives the review fields.

After useful work, regenerate the report, inspect statistics, verify integrity and create a backup. Rehearse restoration. Document readiness does not mean an application was sent; record actual outcomes only from evidence and user confirmation.

Before contributing public changes, follow [privacy](PRIVACY.md) and [contribution guidance](../CONTRIBUTING.md). Real candidate data stays out of source files, screenshots, tests, logs and Git history.
