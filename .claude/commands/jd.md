---
description: Assess a job posting and, if Strong, build the full application package
argument-hint: <job posting URL, or pasted JD text>
---

Run the full pipeline for this posting: $ARGUMENTS

Follow `CLAUDE.md` and `_system/AGENT_CONTEXT.md` exactly. Filters come from
`config/search.json`; identity and the never-claim list come from `profile/` and
`_system/CANDIDATE_FACTS.md`. Do not hardcode either from memory. In order:

1. **Dedup first.** `python3 engine/lib/registry.py check "<url>"`. If it is already in the registry, stop and report the existing row rather than reassessing.
2. **Read the JD live** in Chrome. Never assess from a LinkedIn stub; resolve to the company's canonical ATS. Capture company, title, location/remote policy, level, must-haves, comp. Save the JD text to `/tmp/cvbuild/jd.txt` — the keyword check needs it later.
3. **Check the hard filters before anything else**, per `config/search.json`: geography (`geography.accepts` / `geography.rejects` — a hard filter, not a preference), level (`level.titles`, or a conditional title that clears `level.equivalence_test`), and `level.comp_floor_base_usd`. Then check `profile/identity.json` → `auto_reject_employers`. If a filter fails, say so and stop.
4. **Read the career-context document** named in `profile/identity.json` → `source_documents.career_context` before writing a word of assessment. It is authoritative over every other file.
5. **Deliver the fit assessment** in the five-part structure. Nothing else first.
6. **Apply the build trigger.** Strong -> build immediately (CV + cover letter, DOCX + PDF) and scout direct outreach. Partial -> ask, then add to the triage batch. Poor -> log with a do-not-resurface note.
7. **Log it:** `registry.py add` with the live URL, source, fit, and an honest one-line gap note. Never leave `--source` blank.

If you build: work in `/tmp/cvbuild`, copy the newest JD folder's CV as the base, and rebuild every hyperlink from `profile/links.json` rather than trusting the inherited base.

**The build is not done until the auditor exits 0:**

```bash
python3 engine/lib/check_cv.py "<job folder>" --jd /tmp/cvbuild/jd.txt
```

Fix every FAIL and re-run; report the final summary line. Do not tell me it is done off a hand-check.
