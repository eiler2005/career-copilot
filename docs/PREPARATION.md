# Interview preparation that follows the evidence

[English](PREPARATION.md) · [Русский](ru/PREPARATION.md) · [Documentation](../README.md#documentation)

Start with the interview date, expected format, vacancy requirements and demonstrated experience. The output is a prioritized plan the candidate can actually execute, with exercises, questions, real STAR stories and criteria for reviewing practice.

## Requirements and gaps

For each requirement retain its source, mandatory/optional status, evidence fact IDs and reviewer decision. Tags locate possible evidence; they do not establish proficiency. Relevant evidence must match the requirement's context and scale.

| Gap type | Meaning | What can demonstrate progress |
| --- | --- | --- |
| `knowledge` | Concepts or understanding are missing | Explain a new example and correct misunderstandings |
| `practice` | Understanding exists; application is unproven | A reviewed exercise, project or problem-solving artifact |
| `experience_framing` | Experience exists but is poorly evidenced | A source-linked account with accurate role and outcome |
| `interview` | Answers lack structure, clarity or timing | Recorded practice, concrete feedback and another attempt |
| `structural` | Tenure, work authorization, license or another objective prerequisite | Employer clarification or documentary evidence; a course cannot remove the constraint |

A learning project remains a learning project. Completing exercises never adds commercial years to a CV. Document readiness, vacancy fit and learning progress are recorded independently.

## Company context and STAR bank

For priority companies, prepare sourced notes on products, customers, markets, business model and strategy questions, with dates. Keep unknown figures unknown and distinguish published facts from analysis.

Link STAR stories—situation, task, personal action and verified result—to fact IDs. Cover success, mistakes, conflict, ambiguity, influence without authority and team development where the candidate has real examples. Preserve the limits of personal contribution. Rehearse short and detailed versions, employer questions and the explanation of movement between product and technical contexts.

Do not invent a successful story to fill an interview category. Record the missing example, ask for real evidence when needed, or practice how to acknowledge the limitation.

## Six weeks at six hours per week

The default plan spans six weeks and six hours per week. A useful allocation is two hours of study, two hours of exercises, one hour of experience framing and one hour of practice and feedback. This is a scheduling assumption, not a claim that the candidate has mastered the subject.

| Week | Product track | Technical leadership | Observable result |
| --- | --- | --- | --- |
| 1 | Product sense, discovery, segments and needs | System design and architecture | Case analysis with assumptions and success criteria |
| 2 | Strategy, prioritization and constraints | Distributed systems and tradeoffs | Decision with alternatives and reasons for rejecting them |
| 3 | Metrics, experiments and causality | Reliability, SLOs and incidents | Testable experiment plan or incident analysis |
| 4 | Pricing, GTM, economics and P&L | Engineering organization, quality and delivery | Case grounded in inputs and constraints |
| 5 | Stakeholders, influence and commercial negotiation | Hiring, feedback and engineer development | Real STAR answer and a difficult management decision |
| 6 | Product mock interview | Technical leadership mock interview | Recording, rubric, error list and repeat attempt |

Add coding when the actual interview requires it. In both tracks, an AI module can cover evaluation quality, model limits, cost, safety and operation at the depth the role needs. Ask for a metric choice, error analysis and a quality/cost tradeoff case, not a list of fashionable terms.

## Preparation module: two entries and a practice cycle

Preparation starts from the Preparation section or from a vacancy's Preparation tab. Neither entry needs a finished CV or a scheduled interview.

**For a vacancy.** An agent session produces a `preparation_brief` (task `prepare_vacancy_brief`). Company and interview-stage claims are marked `confirmed` or `participant_report` (both need a source URL and the date it was read) or `assumption`. The brief lists role tasks linked to requirement IDs, interview stages and format, the coding requirement (`required`, `not_required`, `unknown` with basis, source and date), questions with type (`behavioral`, `leadership`, `product_case`, `system_design`, `self_presentation`, `coding`), what each question tests and its provenance (`published` with a dated source, or `generated`), STAR stories tied to verified facts (missing stories are listed as gaps), a plan for the available hours, a short brief and questions for the employer. Coding questions appear only when coding is required with a basis; the flag is never inferred from a job title and LeetCode is never assigned automatically. A researched coding flag fills the vacancy unless the user already set one.

**General gaps.** `ajh prep plan --track T --goal TEXT --hours N [--experience TEXT] [--vacancies IDS]` (or the dashboard form) builds a `track_plans` record. Topics come from requirements whose route is `preparation` across current assessments; identical gaps merge, and duplicate postings of the same role at the same company add no weight. Without such gaps the plan is explicitly a baseline for the direction. Each topic has why, where it was found, weight, exercise, criterion, materials and a status derived only from practice: `open`, `attempted`, `reviewed`. Reading materials never changes the status; an agent adds dated materials through the `track_plan_materials` task.

**Unified overview.** A `preparation_overview` activity result (task or direct agent work) reviews both tracks at once: a summary, shared conclusions, per-track positioning, market notes, themes (what vacancies require and what the candidate has) with an evidence label (`verified` only from verified facts, `reported` from candidate-reported facts, `gap`, `unknown`) and an action (`verify_evidence`, `cv_edit`, `preparation`, `clarify`), what interviews will probe, priority vacancies, facts to back with evidence, a unified weekly plan with goals, tasks and exercises, a question bank, STAR stories with cautions and missing stories, CV advice and a "do not" list. Exercises and questions are practised like any plan topic (`plan_kind: preparation_overviews`); coding exercises are not accepted here. The overview changes no facts, CV or assessment.

**Practice from any plan.** A practice question can belong to a general-gap plan, a vacancy learning plan (a week `week-N` or a gap) or stand alone: `plan_id` with `plan_kind` (`track_plans`, `learning`, `interview_plans`) and `topic_id`. Each week and non-structural gap therefore shows its status (`open`, question ready, `attempted`, `reviewed`); structural gaps route to clarification in the vacancy instead of practice.

**Text practice.** A practice question (`prep_create` request) records its type, what it tests and provenance. An answer (`practice_answer`) is stored as an artifact and queues `review_practice`. The review (`practice_review` result) quotes exact fragments of the answer with criterion, problem and improvement, may ask a follow-up and proposes a retry question. A follow-up answer and a retry are new attempts linked to the earlier one, so the same rubric can be compared. Practice never creates experience, never changes the CV and does not replace the `interview_progress` decision by an independent reviewer. Voice and video practice are not implemented.

## Use the CLI and adapt the plan

`learn --track product` and `learn --track technical-leadership` use current assessments. `learn VACANCY_ID --track TRACK` limits the context to one vacancy. The plan keeps topics, gaps, next actions and the interview date when available. With no annotated requirements, the output is explicitly a baseline plan, not purported employer requirements.

The CLI does not automatically reschedule a calendar or select verified learning links. The agent checks primary learning material, adds exercises and sets an observable acceptance criterion. An approaching interview takes priority: mandatory gaps and expected formats first, a mock interview next, then time for corrections. Explicitly defer work that does not fit.

For each practice result record the date, artifact or answer transcript, criterion, reviewer, evidence-based feedback and next action. Feedback should identify what the answer demonstrated, what remains unsupported and what a better next attempt should change. A `done` status requires demonstrated output. Time spent, a reading list and confidence alone are insufficient.

Changing the assessment of a competency needs a separate substantive decision. Changing CV claims then requires a new document version and review. See [interview skill handoffs](AGENT_WORKFLOWS.md#career-interview-prep).
