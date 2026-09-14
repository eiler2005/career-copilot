# Privacy and publication

[English](PRIVACY.md) · [Русский](ru/PRIVACY.md) · [Documentation](../README.md#documentation)

Public code and private candidate work have different contents and histories. Keep real evidence, search targets, assessments and documents in an explicit external workspace. Public familiarity with a person's biography does not authorize using it as a pipeline example.

The [dashboard](DASHBOARD.md) is a private viewing surface. Its Docker image contains public code and browser assets; an external workspace is mounted read-only at runtime. Preserve the host-loopback port binding and access it through SSH. A public domain requires a separately reviewed authentication gateway and TLS. Do not publish the generated private HTML/JSON or copy a workspace into an image layer. Dockerfile, Compose and `.dockerignore` are allowed public configuration files, with the same content and secret checks as source code.

## Public contents and history

Allowed public material is source code, process documentation, synthetic examples/tests, build/CI configuration and the license. Private material includes candidate facts, contact details, real publications and awards, clients, target companies, evaluations, CVs, source snapshots, private absolute paths, activity logs, personal-data dictionaries and secrets.

Start the public repository with clean history. Do not transfer a private project's `.git`, commits or complete workspace archive. `.gitignore` helps avoid some accidental additions but does not inspect already tracked files, staged blobs, deleted historical material or release artifacts.

## Local checks and private dictionary

A private dictionary lives outside the project. It contains personal strings and spelling variants that a generic secret scanner cannot know. Its format is a JSON object with a `terms` string array, for example:

```json
{"terms": ["FICTIONAL_PRIVATE_MARKER"]}
```

Update it as new identifiers appear. Reports should name the violation type and a nonprivate identifier without printing matched values, source lines or secret paths.

From the public checkout:

```sh
uv run ajh privacy check --scope worktree --dictionary /absolute/private/privacy-dictionary.json --gitleaks
uv run ajh privacy check --scope index --dictionary /absolute/private/privacy-dictionary.json --gitleaks
uv run ajh privacy check --scope history --dictionary /absolute/private/privacy-dictionary.json --gitleaks
```

The path is a portable example, not a bundled dictionary. A real dictionary needs persistent private storage. It can also be selected with `AJH_PRIVACY_DICTIONARY` or local Git config `ajh.privateDictionary`; its contents must never enter Git. `--root` selects the public checkout explicitly. Privacy commands do not require a candidate `--home`.

After installing Gitleaks and configuring the dictionary, enable the supplied hooks for this clone:

```sh
git config --local core.hooksPath .githooks
chmod +x .githooks/pre-commit .githooks/pre-push
git config --local ajh.privateDictionary /absolute/private/privacy-dictionary.json
```

`pre-commit` checks the exact staging area with Gitleaks; `pre-push` checks staging and history. Do not bypass these hooks. Local Git settings are not transferred by cloning, so configure them in each clone. Check `dictionary_loaded: true`; an absent dictionary is not a complete personal-data check.

## Three different scopes

| Scope | Actual object | When it matters |
| --- | --- | --- |
| `worktree` | Current files | Before choosing public changes |
| `index` | Exact staged Git blobs | After the final explicit `git add`, before commit |
| `history` | Git history, including deleted contents | Before first publication and outgoing history changes |

Stage explicit paths only. A prior staged scan becomes stale after staging changes; a history scan becomes stale after commits change. Full history checking is stronger than scanning only the current diff and is required before initial publication.

Gitleaks complements the personal-data/content scanner. Use redacted output. For `index`, the CLI materializes staged blobs into a temporary directory and scans those exact bytes. For `history`, it checks all refs with `--all`. Missing Gitleaks or a skipped run cannot be described as a passed publication gate.

CI runs the same classes of checks and synthetic tests, but it does not replace the local private dictionary and must not receive that dictionary as a public artifact. See [checks.yml](../.github/workflows/checks.yml), [pre-commit](../.githooks/pre-commit) and [pre-push](../.githooks/pre-push).

## Documents, binaries and releases

Text search cannot establish that PDF, DOCX, images or archives contain no private material. Unsupported formats block publication by default. For a necessary binary, explicitly allow its exact type and purpose, inspect extracted text and metadata, examine every page/layer and record the hash of the reviewed file.

Archives require safe path validation, inspection of every member and safe extraction when another scanner needs files. If the scanner does not support a format, do not add it to the allowed release set by assumption.

Build wheel/sdist into a separate directory and inspect both member paths and contents. Packaging can include unexpected files. The built-in wheel/ZIP and tar.gz inspection is:

```sh
uv run ajh privacy check --artifact /absolute/build/job_search_agent-0.1.0-py3-none-any.whl --dictionary /absolute/private/privacy-dictionary.json
```

It inspects archive contents without unpacking into the checkout and rejects unsafe paths/formats. Run Gitleaks separately on independently and safely extracted release contents. `--artifact` cannot be combined with `--gitleaks`; scanning the source tree is not scanning the release.

Repeat after rebuilding. Retain a private report with Git revision, tool versions, scope, time, artifact hashes and outcomes, without matched values. A successful CI run or a single clean scan is not proof of the entire privacy boundary.

## Incident response and external actions

On a match, stop the affected commit, push or release. Remove private material from the public set while preserving its private original, then rerun all affected scopes. If a value is already in history, editing the current file is insufficient: prepare and inspect a separate clean history.

Rewriting already published history and revoking an exposed secret are separately authorized operations. Do not repeat the secret in an incident report.

Source adapters only read. Applications, recruiter messages, CV uploads and sending personal material to external model services require the applicable explicit user authorization. A ready package or authorization for network research does not supply permission for these actions.

## Repository skills and inspectable diagrams

The public allowlist includes only the eight approved skill IDs under `.agents/skills/` and `.claude/skills/`; unrelated hidden configuration is not admitted. Public skill adapters are ordinary files, not symlinks.

SVG and DOT are allowed specifically under `docs/assets/`. SVG is parsed as XML and both raw and decoded text/attributes are inspected. Scripts, event handlers, foreign content, external resources, data URLs, unsafe declarations and unsupported elements block publication. Local fragment references used by static diagrams are allowed. This narrow static-graphics support does not authorize arbitrary binaries or private screenshots. Inspect regenerated diagrams visually and rerun privacy checks on their exact bytes.
