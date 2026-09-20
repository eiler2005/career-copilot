# PDF documents and reading packs

[English](PDF.md) · [Русский](ru/PDF.md) · [Documentation](../README.md#documentation)

Use one local PDF pipeline for study plans, preparation notes, CV rendering and reading packs. It renders Markdown, inspects PDFs, assembles ordered A4 binders and extracts selected pages. Source content and all persistent outputs stay inside the explicitly selected private workspace.

The CLI `render` command uses a 12 pt body font and at least 11 pt table text by default. Use `--font-size 11` or another finite value from 8 through 18 for a different density. The Python API keeps its legacy 9.5 pt default when `render_markdown()` omits `font_size`, preserving existing CV and dashboard output. At the default size, headings remain larger.

Binders keep fit-to-A4 behavior by default. Use `pdf bind ... --preserve-size` to retain source page geometry and 100% text size; the binder label is stamped in a 4 mm bottom margin, so inspect that margin before delivery. Font and geometry options are recorded in the manifest.

## Render a plan

The following paths are examples; create the source inside your own workspace first. Global `--home` precedes the command, source paths may be relative to that workspace, and output paths are workspace-relative.

```sh
uv run ajh --home /absolute/private/career-workspace pdf render learning/plan.md \
  --output learning/pdf/plan-v1.pdf \
  --title "Preparation plan" --subtitle "Study, practice and review"
uv run ajh --home /absolute/private/career-workspace pdf inspect learning/pdf/plan-v1.pdf
uv run ajh --home /absolute/private/career-workspace verify
```

Add `--landscape` when the source needs more horizontal space. Changing orientation is a layout choice, not a reason to drop content. For a revised source or changed rendering options, choose a new output filename.

The renderer supports headings, paragraphs, emphasis, ordered and unordered lists, nested lists, block quotes, fenced code, tables, links and standalone local PNG/JPEG illustrations. Table headings repeat when a table spans pages; images inside table cells are not supported. Use `<!-- pagebreak -->` between sections for an explicit page break. HTTP(S) and mail links can be clickable; they are not fetched. Local links print their label without an active target. Images resolve relative to the Markdown file and must remain within the private workspace, including after symlink resolution. CLI exports embed these local illustrations; dashboard plan downloads keep image captions only and do not read image resources.

This is a Markdown document renderer, not a browser: HTML is printed literally; arbitrary HTML/CSS layout, scripts and remote image downloads are unsupported. Keep tables readable and use landscape or restructure an overly wide table when necessary. A code block is printable text, never executable input. Requires the project's Python dependencies (ReportLab, pypdf and markdown-it-py) and a Unicode TTF font; `uv sync --all-groups` installs the Python dependencies. The Docker image supplies DejaVu fonts.

## Assemble and extract

`bind` takes PDFs in the supplied order, fits their pages to A4 and adds page numbering and document bookmarks. Render Markdown sources first, then assemble the outputs:

```sh
uv run ajh --home /absolute/private/career-workspace pdf bind \
  learning/pdf/plan-v1.pdf learning/pdf/practice-v1.pdf \
  --output learning/pdf/reading-pack-v1.pdf --title "Preparation reading pack"
uv run ajh --home /absolute/private/career-workspace pdf extract \
  learning/pdf/reading-pack-v1.pdf --pages 1 3 \
  --output learning/pdf/selected-pages-v1.pdf
```

The extraction example selects pages 1 and 3, not a range. Inspect the final file after assembly or extraction: its page numbers and geometry may differ from the inputs. Retain the individual PDFs and Markdown alongside a binder so a later revision can be rebuilt from its sources.

## Artifacts and repeatability

Persistent commands register the PDF and a sibling `OUTPUT.pdf.manifest.json` through the workspace artifact store. The manifest records input hashes, resource hashes where applicable and output metadata. Each export also registers an immutable `pdf_documents` record and a `pdf_exported` event. The record links the manifest and output; its ID is `pdf-` followed by the first 20 characters of the manifest's SHA-256. Identical reruns reuse identical artifacts and the same document record; different bytes at an occupied path are rejected. Avoid editing or replacing a registered file manually. Use a new output path and retain the previous version.

`pdf inspect` reports the existing PDF's page count, SHA-256 and byte size without rewriting it. `verify` checks registered artifact integrity. Neither command checks factual truth, readability or learning progress. The generic PDF commands do not create a CV package, author identity, review approval or a completed practice result. Employer-facing documents still follow the [package authorship and review contract](CV_PROFILES.md).

The CLI is a mechanical compiler. Complex planning, architecture and substantive judgments belong to the active flagship (`gpt-6-astra` in Codex/OpenAI, `claude-opus-5` in Claude); straightforward research and extraction can use a cheaper model such as `gpt-5.6-luna`. Independent content review uses a separate flagship session from every author/editor. Record actual identities only; compilation does not imply model authorship. See [workflow](WORKFLOW.md).

## Inspect the pages

Extract text to check that the ending, section titles, links and Cyrillic survived. Then render every page to an image with Poppler and inspect the images at a readable size:

```sh
pdftotext /absolute/private/career-workspace/learning/pdf/plan-v1.pdf \
  /absolute/private/career-workspace/learning/pdf/plan-v1.txt
pdftoppm -png -r 120 /absolute/private/career-workspace/learning/pdf/plan-v1.pdf \
  /absolute/private/career-workspace/learning/pdf/plan-v1-page
```

Check margins, image proportions, table rows and repeated headers, list indentation, page breaks, typography and the final page. Fix the source or renderer and create a new artifact when anything is clipped, overlapping or unreadable. Record a visual pass only after inspecting the exact delivered bytes; successful rendering and tests are not a visual review.

Previews, extracted text and manifests contain private material too. Keep them outside the public checkout and follow [privacy](PRIVACY.md). See [architecture](ARCHITECTURE.md#shared-pdf-layer) for module ownership and [CLI](CLI.md) for the command reference.
