---
description: Guided first-run setup — build the profile and config from scratch
argument-hint: [path to an existing CV, if you have one]
---

Set this project up for a new user: $ARGUMENTS

Everything downstream is bounded by the profile, so this is an **interview, not a form**. Ask
real questions, listen to the answers, and write files as you go. Do not dump a wall of
questions and wait — ask a few at a time and keep moving.

---

## 1. Intake what already exists

If they gave a CV path, extract it rather than retyping:

```bash
python3 engine/lib/extract_career.py "<their_cv.docx>" -o profile/career.json
```

Read the result back to them in summary — roles, dates, bullet counts — and ask what is missing,
stale, or wrong. If they have no CV, build `profile/career.json` from
`profile.example/career.json` as the shape and interview them role by role.

Copy the config and profile scaffolding if it is not there yet:

```bash
cp config/search.example.json config/search.json
cp config/documents.example.json config/documents.json
cp -r profile.example profile      # only if profile/ does not exist
```

## 2. Interview what a parse cannot infer

These do not appear in any CV and must be asked directly. Write each answer straight into
`profile/identity.json`.

- **The real title ceiling.** The most senior title they *actually held*, not the one they are
  targeting. Explain why: they may apply above it, but their history never inflates to match, and
  this is the most common way a tailored CV starts lying.
- **Employment status**, and if they have left, the end month. This is what stops "Present"
  quietly persisting for months.
- **Defensible scope per role.** For each significant number: *could you say this out loud in an
  interview and defend it?* Write the defensible version, not the flattering one. If revenue grew
  and they owned part of it, record the part they owned.
- **Employers they will not return to**, and why.
- **Target level, comp floor, geography, and domains in priority order** → `config/search.json`.
  Geography is a hard filter, not a preference: press on whether they would genuinely relocate.

## 3. The honesty pass — the highest-value part of setup

Ask the uncomfortable question directly:

> **What would a job description ask for that you would have to admit, in an interview, you have
> not actually done?**

Every honest answer becomes a guardrail in `profile/guardrails.json`. Probe for the six shapes
demonstrated in `profile.example/guardrails.json`: a title never held, a figure that drifted
between CVs, a tool never touched hands-on, work someone else owned, an internal codename
meaningless outside, and an inconsistent tenure figure.

For each guardrail, write **at least one case that must fire and one that must not** into
`profile/guardrail_tests.json`. Explain why the second kind matters: a rule tested only in the
firing direction is a rule they will delete the first time it cries wolf on a legitimate
sentence.

```bash
python3 engine/lib/check_cv_tests.py     # must pass before moving on
```

## 4. Links

Fill `profile/links.json` with their canonical anchor-to-URL table. Rules: partial-text anchors
only, never a bare company homepage, and only anchors whose text will actually appear in the CV.
If two entries share the same anchor text, give each an explicit `{"anchor": …, "url": …}`.

## 5. Smoke test — do not declare setup finished without it

```bash
python3 engine/lib/build_cv.py -o /tmp/base_cv.docx
soffice --headless --convert-to pdf --outdir /tmp /tmp/base_cv.docx
python3 engine/lib/check_cv.py --cv /tmp/base_cv.docx
```

Show them the rendered pages and the audit. Fix what it flags **together** — the first clean
audit is the real end of setup, and walking through one failure teaches the loop they will use
from then on.

Then run one real posting end to end with `/jd` so they see the whole pipeline once.

---

**Close by telling them the two rules that keep this working:**

1. When a guardrail fires on legitimate text, that is a bug in the **pattern**. Add the sentence
   to `guardrail_tests.json`, then loosen `allow_context`. Never reword a CV to slip past a
   guardrail.
2. The build is not finished until `check_cv.py` exits 0.
