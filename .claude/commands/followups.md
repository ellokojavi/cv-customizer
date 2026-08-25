---
description: Post-application worklist — due actions, stale applies, outreach drafts
---

Work the post-application pipeline. Response rate, not application count, is the binding
constraint here. Thresholds come from `config/search.json` → `post_application`; voice and
signature come from `profile/identity.json` → `voice`.

1. `python3 engine/lib/registry.py followups` — show due next actions and stale applications (applied past the configured `stale_application_days`, no response, no outreach).
2. Mine Gmail read-only for recruiter responses on live applications; update statuses with `registry.py setstatus`.
3. For every application inside the configured `outreach_window_days` with no response and no outreach: run the outreach scout. Identify the likely hiring manager (at founder-led or smaller companies often the CEO; check whether the role is a backfill and who held it last) and an in-house recruiter as backup. Verify identity carefully, name collisions are common.
4. Draft each outreach note in the candidate's own voice per `_system/outreach_playbook.md`: direct opener, a 3-4 line "A bit about me" anchored on the credential named in `profile/identity.json` → `voice.anchor` plus the most role-relevant one, and ONE honest closing ask. No CV attached — it is already in their ATS, and attachments from unknown senders hurt deliverability. Sign per `voice.signature`.
5. Batch-present the drafts for approval rather than sending anything.
6. Run Partial triage and `registry.py expire` for anything that has sat through the configured number of triage batches undecided.

Close with a 5-line pipeline summary.
