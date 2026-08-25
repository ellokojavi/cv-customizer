# 10 — Fit assessment and the build trigger

The assessment always comes first. Do not write the CV, do not list clarifying questions, do not
summarize the posting back. Assess, then build if the trigger fires.

---

## Step 1 — Ingest the posting

- **Read it live in a browser.** Never assess from an aggregator or job-board stub: titles,
  levels, and locations on those are frequently wrong, and some aggregators synthesize them
  outright. Resolve every posting to the employer's own applicant tracking system before
  believing anything about it.
- Capture: company, exact role title, location and remote policy, level, top responsibilities,
  must-haves, nice-to-haves, and compensation if listed.
- Save the posting text to a scratch file — the keyword check needs it at audit time.
- Research the company briefly: recent news, product, stage, market. Enough to inform fit and
  tailoring, not a full brief.
- **Dedup before anything else.** Check the registry. If the posting is already logged, stop and
  report the existing row rather than reassessing it.

## Step 2 — Apply the hard filters

Read these from `config/search.json`; do not work from memory. If any fails, say so and stop —
a filter failure is a complete answer, not a partial one.

1. **Geography** (`geography.accepts` / `geography.rejects`). This is a hard filter, not a
   preference. A posting that fails it is out even on exceptional domain fit; the alternative is
   spending real effort on roles that cannot be taken.
2. **Level** (`level.titles`, or a conditional title clearing `level.equivalence_test`).
3. **Compensation** (`level.comp_floor_base_usd`). Below the floor is normally out. If scope and
   domain are genuinely exceptional, it may still be surfaced — but the gap must be stated
   explicitly and never buried.
4. **Employer exclusions** (`profile/identity.json` → `auto_reject_employers`).

## Step 3 — Read the career document

Read the file named in `profile/identity.json` → `source_documents.career_context` **before
writing a word of assessment.** It is authoritative over every other file, including the
candidate's own profile summary. Assessments written from memory drift toward the posting.

## Step 4 — Deliver the assessment

Five parts, in this order, and nothing else first:

1. **Fit verdict**, stated plainly at the top: **Strong fit / Go all in** · **Partial fit /
   Apply with tweaks** · **Poor fit / Don't apply**.
2. **What matches** — specific requirements the candidate's experience directly covers.
   Concrete, tied to real work, not generic strengths.
3. **What doesn't match** — honest mismatches, no sugarcoating. If a must-have is missing, that
   belongs here in plain words.
4. **Seniority check** — too junior, too senior, or right-level. Over-qualification is a real
   rejection reason and is worth naming.
5. **Recommendation** — clear go/no-go with one or two sentences of rationale.

---

## The build trigger

| Verdict | Action |
|---|---|
| **Strong** | Build immediately. No go-ahead needed. Also run the outreach scout. |
| **Partial** | Ask first, batched — one line per open Partial (company, role, comp, honest gap) so the decision happens in a single reply. |
| **Poor** | Log it with a do-not-resurface note and move on. |

**Partials must never rot silently.** Batching exists because per-role questions go unanswered
and the role expires undecided. Anything that sits through roughly two triage batches without a
decision auto-expires to `expired` status, recoverable on request but never silently
resurfaced.

**Every build ships the full set:** CV and cover letter, DOCX and PDF, plus the outreach plan.
Partial deliveries create the impression of a finished application that has not actually been
finished.
