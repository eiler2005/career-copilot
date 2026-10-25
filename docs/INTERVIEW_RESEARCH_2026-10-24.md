# Interview preparation research — 2026-10-24

[English](INTERVIEW_RESEARCH_2026-10-24.md) · [Русский](ru/INTERVIEW_RESEARCH_2026-10-24.md) · [Preparation workflow](PREPARATION.md)

The practical priority is a smaller set of role-specific questions with clear evidence and follow-up criteria. Career Copilot already supports sourced briefs and reviewed text attempts. This digest guides the agent's selection and authorship; it adds no automatic Atlas import, model evaluator or coding lab.

## Official sources and research

Sources below were read on 2026-10-24. The Amazon guides are undated general-role baselines, not proof of an AI-specialist loop or of the exact questions in a preparation bank.

| Source | Supported preparation choice |
| --- | --- |
| [Amazon PM guide](https://www.amazon.jobs/content/en/how-we-hire/product-manager-interview-prep) | Prepare product decisions, stakeholder work, real experience and written communication. |
| [Amazon SDM guide](https://www.amazon.jobs/content/en/how-we-hire/sdm-interview-prep) | Combine system design with people leadership and operational judgment. Do not infer a coding requirement from the title. |
| [Amazon TPM guide](https://www.amazon.jobs/content/en/how-we-hire/tpm-interview-prep) | Rehearse technical dependencies, escalation, end-to-end delivery, system design and writing. |
| [GitLab Director, Engineering](https://handbook.gitlab.com/job-description-library/engineering/development/management/director/) | Keep its actual Hiring Process section separate from responsibilities. Its general Director scope helps frame cross-team leadership; it does not supply AI interview questions. The page reports modification on 2026-03-12. |
| [METR productivity experiment update, 2026-02-24](https://metr.org/blog/2026-02-24-uplift-update/) | Ask how task/participant selection and parallel-agent time accounting affect a productivity claim. The authors describe unreliable estimation; do not turn earlier or later results into a universal AI effect. This is research reading, not interview evidence. |
| [Google SRE: SLOs](https://sre.google/workbook/implementing-slos/) and [incident response](https://sre.google/workbook/incident-response/) | Ground reliability practice in user-facing indicators, decision ownership and coordinated response. These operational references support answer quality, not an employer attribution. |

## Forum findings, kept separate

Two publicly readable Reddit threads offer qualitative context, checked on 2026-10-24. The [AI PM discussion](https://www.reddit.com/r/ProductManagement_IN/comments/1s9vuqd/quick_rant_are_interviews_becoming_tougher_these/) contains a self-described PM-1/PM-2 candidate's account of latency, cost, accuracy and stakeholder discussions. It does not identify employers or establish senior-leadership expectations. The [engineering-manager discussion](https://www.reddit.com/r/EngineeringManagers/comments/1wshvqk/how_are_experienced_engineering_managers_handling/) describes interviewing engineers and uncertainty about permitted AI tools; it is not an account of interviewing for an EM role.

Retrieved views showed conflicting relative ages: six/seven months for the PM thread and 26 days/nine hours for the EM thread. Exact publication and interview dates remain unverified, as do identities and completeness. These accounts motivate practice choices and recruiter clarifications, not market-frequency claims or automatic `confirmed` labels. No access controls were bypassed. An unavailable page remains unavailable rather than proving that a process has ended.

## Select by role and authority

These are editorial practice themes. They are not claims that a named employer asked the question. Product and technical-leadership remain the two master tracks; the scopes below refine practice within them.

| Scope | Start with | Observable review criterion |
| --- | --- | --- |
| AI Product | AI suitability, discovery, outcome metrics, pricing and a stop-investment decision | Names the workflow and non-AI baseline; connects quality, latency and cost to a customer outcome. |
| Engineering/Platform leadership | People decisions, platform boundaries, provider changes, reliability and productivity measurement | States technical and organisational ownership, failure modes and the evidence behind a tradeoff. |
| Head/Director | Portfolio allocation, management through managers, hiring and organisational change | Explains decision rights across teams and evidence at the candidate's real scope; separates delegation from personal execution. |
| TPM/Delivery | Dependencies, uncertain milestones, readiness and an incident without immediate rollback | Identifies the critical dependency, escalation owner, containment and restart evidence; distinguishes coordination from incident command. |
| AI Engineering | System design, evaluation, retrieval, tool use, reliability and cost at the role's depth | Explains the mechanism, failure case and measurement plan; include coding only when the actual interview requires it. |

The separate [AI Interview Atlas](https://github.com/eiler2005/ai-interview-atlas) is a sourced reference bank. An agent can select and adapt its public material, preserving source dates, evidence strength and generated/published distinctions. Its role tags indicate practice usefulness unless source evidence explicitly names the role. There is no automatic import in the current preparation workflow; transferring material requires an agent-authored brief or plan and never transfers a reviewed practice status.

## Use the existing preparation cycle

1. **Brief first:** record the actual role, requirement IDs, expected format, tool policy and coding basis in `preparation_brief`. Keep role duties, official stages, participant reports and assumptions distinct. A secondary prep guide must not be relabelled as an employer confirmation or first-person report.
2. **Choose a bounded practice set:** start with one decision case, one real experience account and one follow-up that changes a constraint. Add dated reading through `track_plan_materials` where it addresses a specific gap. Prioritise available hours and the interview's actual format.
3. **Review the answer:** use `practice_answer` and `practice_review` to retain the attempt, quote its relevant passages, identify a missed criterion and propose a retry. Use the same rubric on the next attempt. Reading and confidence do not demonstrate mastery.

These are recommendations for agent-authored work using the [existing module](PREPARATION.md#preparation-module-two-entries-and-a-practice-cycle), not new product automation. Candidate evidence, attempts and personal interview research stay in the external private workspace. The public digest contains no candidate assessment and does not change a CV or fit decision.
