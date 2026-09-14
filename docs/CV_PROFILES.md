# Two master CV profiles

[English](CV_PROFILES.md) · [Русский](ru/CV_PROFILES.md) · [Documentation](../README.md#documentation)

Two master profiles share one evidence base. A vacancy-specific CV selects and explains relevant evidence from the chosen profile.

| Track key | Roles | Evidence to foreground |
| --- | --- | --- |
| `product` | Product Manager, Product Lead, Head/Director of Product, CPO | Customer needs, discovery, strategy, metrics, commercialization, P&L and product growth |
| `technical-leadership` | Engineering Manager, Head/Director of Engineering, CTO; suitable senior technical leadership | Architecture, engineering organization, platforms, quality, reliability, scale and teams |

AI, payments, enterprise/API, developer tools and industrial technology are overlays. They change emphasis and ordering within a track; they do not create another master CV or a competing biography. The technical track applies across industries.

Adapt in this order: **verified facts → master track → domain overlay → company and level**. Preserve official job titles even when target positioning differs. Filled profiles and individual priorities remain private.

## Document structure

1. Contact details and target positioning.
2. A short track-specific professional summary.
3. Selected achievements and professional distinctions.
4. Employment history with official titles, dates, responsibilities and results.
5. Relevant projects, clients and international partnerships.
6. Independently created products and engineering projects.
7. Education, competencies, full bibliography and remaining verified achievements.

Place the distinctions block immediately after the summary, visible on page one. Select three to five meaningful facts when the evidence supports them: authorship, accurately attributed participation in an award-winning project, a shipped product and its demonstrated use, a verified expert role, or evidence spanning technical, management and commercial responsibilities.

Product positioning gives priority to product recognition, authorship, commercial effect and international experience. Technical positioning foregrounds engineering products, architectural outcomes, publications, expertise and team scale. Verified books and awards remain visible in both versions when applicable. A template category never authorizes inventing an achievement.

A private publication/award note can start verification. Distinguish a personal award from recognition of a client project; state the candidate's contribution and verification status. Self-reported claims cannot become “independently verified” through editing.

## Preserve the evidence

There is no default two-page cutoff. Readable three- or four-page CVs can be appropriate when they preserve relevant evidence. Review density, hierarchy and readability; page count is not a quality score. A concise opening must not erase important clients, chronology or engineering projects.

The coverage JSON includes exactly one row for every fact in the package context, with `fact_id`, boolean `included` and a specific nonempty `reason`. Explain where an included fact appears or why it is omitted. “It did not fit” calls for a layout/structure decision, not automatic deletion.

Keep employers, clients, partners and independent projects distinct. Retain dates and official roles. Planned savings, target revenue and expected outcomes stay targets until confirmed as results. Practice projects do not create commercial tenure; a skill keyword does not prove ability.

Natural editing should preserve the candidate's voice, meaning, confidence and factual limits. Remove vague boilerplate and repetitive phrasing while retaining precise claims. Do not add anecdotes or numerical outcomes to sound more human. There is no promise of passing AI detectors.

## Level and role-family policy

Configure level rules privately. Selected large technology employers can use a confirmed L5+ policy in both tracks and all markets, including Russia. Apply this exception before the Russian director filter for other companies. Public defaults contain no personal employer list.

Preserve `level.raw`, its source, role family, management/IC status and evidence of threshold equivalence. `policy.company_levels` stores company-specific accepted and below-threshold labels with a source. The same number at two employers need not mean the same level; there is no universal numerical conversion table.

Unknown or unmapped levels require clarification. Technical leadership primarily targets management. A senior IC role at a large technology company needs its own evidence-based assessment of leadership scope and candidate experience. L5+ alone does not make every engineering or research opening relevant.

A market effort ratio, for example 70/30, guides research time. It is not a result quota or a reason to discard a suitable vacancy.

## Acceptance

Each package preserves source Markdown, PDF, extracted text, optional letter, fact/vacancy context, coverage, version metadata and reviews. Authorship follows [the workflow model policy](WORKFLOW.md#people-models-and-authority).

Review every PDF page, reading order, line breaks, Unicode characters, contacts, links, page-one distinctions and extracted text. When a letter is included, review its full PDF and text too. Source, renderer or font changes require a new version and new applicable reviews.

Generating a PDF, counting its pages or matching its checksum establishes no content or visual approval. See [operations](OPERATIONS.md#document-review) for the exact review fields.
