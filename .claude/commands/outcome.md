---
description: Record what happened to an application, and calibrate the system against reality
argument-hint: [company] or "calibrate" or "backfill"
---

Record outcomes and feed them back: $ARGUMENTS

Every judgement this system makes — the fit verdict, the comp floor, which sources to scan
first, whether outreach is worth the effort — is a hypothesis. This is the only command that
checks any of them against what actually happened.

---

## Recording an outcome (`/outcome <company>`)

Ask what happened, then write it with **both** the stage and the reason, because the two are
separate facts and the registry historically conflated them:

```bash
python3 engine/lib/registry.py setstatus "<company>" --to <status> --note "<what happened>"
```

Statuses that mean **they moved us forward**: `recruiter_screen`, `onsite`, `offer`, `hired`.
Statuses that mean **it ended**: `closed` (with a note saying *why* — rejection email, went
silent, posting pulled) or `rejected` (only when *we* declined).

**Write the note so a stranger could classify it.** `engine/lib/outcomes.py` reads note text to
tell "they rejected us" from "we passed", and a note like *"closed 2026-08-04"* is unclassifiable
forever. Say `rejection email after the screen`, or `never replied, closing at 60 days`, or
`passed — off-domain`.

**Then archive the materials.** Copy the CV and cover letter that were actually sent, plus the
posting text, into the application folder if they are not already there. When an interview comes,
`/interview`-style prep needs *the exact documents the interviewer read*, not a regenerated
approximation — a CV rebuilt from today's profile is not what they have in front of them.

**Record it the day you learn it.** A rate computed from half-recorded data misleads twice: once
by being wrong, and once by looking like a measurement.

## Calibrating (`/outcome calibrate`)

```bash
python3 engine/lib/calibrate.py
```

Reports conversion by fit verdict, source channel, and outreach — with the arithmetic visible and
an explicit **INSUFFICIENT EVIDENCE** label on any split too thin to read.

**Respect that label.** Job-search samples are tiny and slow; a difference between 6% and 8% on
thirty applications is noise. When the tool says the evidence is insufficient, the correct action
is to report the counts and change nothing. Acting on noise is worse than acting on instinct,
because it feels justified.

When a split *does* clear the bar, act on it:

- **Fit verdict shows no relationship** to advancing → the fit framework is decorative. Tighten
  what "Strong" requires, or stop letting it gate effort.
- **One source channel dominates** → reorder `config/search.json` → `cadence.source_order`.
- **Outreach shows no lift** → either the notes are not landing, or the premise is wrong. Both
  are worth knowing; the system is built on that premise.

## Backfilling (`/outcome backfill`)

```bash
python3 engine/lib/calibrate.py --backfill
```

Lists rows whose outcome cannot be determined. Resolve each with the human's own memory — never
guess. An invented outcome propagates into every rate computed afterwards, and unlike a missing
one, it is invisible.

---

**Close by stating what is now decidable and what still is not.** The honest answer at small
sample sizes is usually "nothing yet, keep recording" — say that plainly rather than dressing up
noise as a finding.
