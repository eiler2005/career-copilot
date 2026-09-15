# CRM module specification

[English](CRM_MODULE.md) · [Русский](ru/CRM_MODULE.md) · [Documentation](../README.md#documentation)

**Status:** specification only. No code, data kinds or settings exist for this module. Vacancies, matching, CV and Preparation work without it.

## Purpose

Remember the people and agreements around a search: who referred, interviewed or recruited, what was discussed, what was promised and when to follow up. It complements company and vacancy records; it never becomes a source of qualification evidence or a sending channel.

## Future switch

Settings → Modules → CRM, **off by default**. Turning it on shows a Contacts section and a Contacts tab in vacancy and company details. Turning it off hides them and **keeps all data**; turning it on again restores the same records. The switch changes visibility, never retention; deletion is a separate explicit action with a backup first.

## Records

| Kind | Fields | Rules |
| --- | --- | --- |
| `contacts` | `id`, `name`, `role`, `organization_company_id`, `channels[]` (type, value, consent note), `source` (how the contact was obtained), `created_at` | Personal data stays in the private workspace; public examples are fictional |
| `contact_links` | `contact_id`, `target` (`companies`, `vacancies`, `packages`), `target_id`, `relation` (`recruiter`, `referrer`, `interviewer`, `hiring_manager`, `other`) | A contact can be linked to several targets |
| `interactions` | `id`, `contact_ids[]`, `at`, `channel`, `direction` (`inbound`, `outbound`), `summary`, `evidence` artifact (optional), `related` IDs | Recorded after the fact by the user; no automatic mail or calendar import |
| `agreements` | `id`, `interaction_id`, `text`, `owner` (`candidate`, `contact`), `due_on`, `status` (`open`, `done`, `cancelled`) | Changing status keeps history through `record_updated` events |
| `reminders` | `id`, `about` (agreement or interaction), `due_at`, `status` (`scheduled`, `done`, `dismissed`) | Shown in the dashboard; no background scheduler sends anything |

## Behaviour

- Interface writes use the existing request queue (`contact_upsert`, `interaction_add`, `agreement_update`, `reminder_update`) with version checks; the journal stays the single source of truth.
- Employer responses and submissions stay in their existing kinds; an interaction may link to them but never replaces their evidence rules.
- Reminders join the pipeline reminders and a future next-action queue (F03).
- Import from mail or calendar (F13) needs a separate decision about integrations and consent.

## Acceptance for a future implementation

Switching the module off and on keeps every record; no page outside the module requires CRM data; private contact data never appears in public files, tests or logs; each interaction and agreement is traceable to the user's own entry.
