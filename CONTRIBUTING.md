# Contributing to Career Copilot

[English](CONTRIBUTING.md) · [Русский](CONTRIBUTING.ru.md) · [Project overview](README.md)

Contributions should make a concrete part of career work more reliable: better source coverage, clearer evidence, correct versioning, usable documents or recoverable private state. Start with [AGENTS.md](AGENTS.md), [workflow](docs/WORKFLOW.md) and [privacy](docs/PRIVACY.md).

## Development setup

Use macOS/Linux, Python 3.12+ and uv. Install development dependencies with `uv sync --all-groups`. The supported CLI is `uv run ajh`; compatibility package/module names remain unchanged.

Create a synthetic workspace outside the checkout with [the offline walkthrough](docs/GETTING_STARTED.md). Use fictional people, companies and source responses in tests and documentation. Do not copy a real profile, target list, CV, source snapshot, dictionary or private absolute path into an issue, patch or fixture—even if some facts are publicly known.

## Scope a change

Explain the observable problem and intended result. For a source adapter, preserve raw bytes, stable identity, bounded access and distinguish empty/partial/error states. For a schema or migration change, preserve original IDs/events/files, reject unsupported versions and rehearse restoration. For document changes, preserve evidence, exact artifact hashes and independent review.

Use `apply_patch` for source edits. Keep unrelated work out of the change and stage explicit paths. Never bypass privacy hooks. User authorization remains scoped: a code change does not authorize an application, message, release or push.

## Validation

```sh
uv run ruff check .
uv run ruff format --check .
uv run pytest
uv run python scripts/check_docs.py
```

Run meaningful behavior tests when code changes. Useful cases include blocked sources preserving earlier observations, idempotent replay, changed inputs invalidating a handoff, contributor independence, unknown telemetry and round-trip restoration. Do not create tests that merely match the wording you just wrote.

For an end-to-end change, run `scripts/demo_workflow.py` with a fresh external directory and inspect its actual outputs. Never fabricate positive model/content/visual reviews to make a demo green.

For skill changes, validate each affected `SKILL.md` with the available skill-creator validator and inspect triggers, scope, references and handoff behavior. Keep canonical skills concise, normal discovery enabled and Claude adapters ordinary Markdown files.

## Documentation and graphics

English is the default README/docs language. Maintain `README.ru.md`, `CONTRIBUTING.ru.md` and the corresponding `docs/ru/` chapter with comparable practical detail. Keep old canonical guide paths working and add language/navigation links.

Describe implemented behavior, required human/model work and limitations separately. Examples must execute with their stated prerequisites; non-URL fact sources must name real files. Reference official provider documentation for API behavior and recheck it when changing an adapter.

Architecture graphics live under `docs/assets/`. The supplied diagrams have DOT sources and regenerate with `uv run python scripts/render_diagrams.py`; `--check` verifies regeneration and requires Graphviz. Inspect the final SVG visually. Keep labels readable, both languages current and content synthetic.

## Before commit, push or release

Follow the full [publication procedure](docs/PRIVACY.md): private dictionary plus Gitleaks, exact worktree/index/history scopes, explicit staging and release-member inspection. A clean current tree does not clean past commits. CI cannot substitute for a local private dictionary.

A reviewable change description should state the concrete trigger/problem, resulting behavior, relevant validation and material limitations. Do not claim tests or reviews you did not run. Do not include private diagnostics or matched secret values.

The project uses the [MIT license](LICENSE). Keep additions compatible with that distribution and retain attribution where required.
