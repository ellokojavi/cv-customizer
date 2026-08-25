---
description: Re-audit a built-but-unsubmitted package against the current rules
argument-hint: <company name or JD folder>
---

Re-audit the package for: $ARGUMENTS

Packages rot as rules change. A finished set is never assumed compliant.

**Run the mechanical auditor first — do not hand-check what a script already checks:**

```bash
python3 engine/lib/check_cv.py "<job folder>"          # add --jd <file> for keyword checks
```

It measures page ratio, dashes, font, date format and right tab stops, chronology, section
order and page breaks, bullet metrics, the canonical hyperlink table, filename pattern,
folder hygiene, and the profile guardrails. Thresholds come from `config/documents.json`,
identity from `profile/`. Exit code 1 means something FAILed. Report its output verbatim,
then fix every FAIL and re-run until it exits 0. WARNs are judgment calls — decide and say why.

Two things the script cannot judge, so check them by hand afterwards:

- **Rendered fidelity.** Convert in `/tmp/cvbuild` and actually look at the pages: dates flush
  right on the role baseline with no wrap, no orphaned headings. `w:ptab` does not survive the
  LibreOffice conversion; a real right tab stop does.
- **Truth.** Diff the factual claims against the career-context document named in
  `profile/identity.json` → `source_documents.career_context`, not just against the JD. The
  guardrails catch known-banned phrasings, not new overreach, and previously-corrected facts
  silently reappear when a CV is built from an older base.

If a guardrail fires on legitimate text, add the case to `profile/guardrail_tests.json` and
loosen `allow_context` in `profile/guardrails.json` — never silence it by editing the CV
around it. Re-run `python3 engine/lib/check_cv_tests.py` after any such change.

The checks the script encodes, for reference: CV within the page cap measured with pymupdf
rather than eyeballed · cover letter within its own cap · dates in the configured format,
never "Present", right-aligned via a real right tab stop derived from the section margins ·
filename pattern and length · zero em-dashes or en-dashes · the configured font throughout ·
hyperlinks rebuilt from `profile/links.json`, none on the denylist, no bare company homepages ·
reverse-chronological experience · Education flowing after Experience with no forced page
break · every bullet carrying a number · JD keyword coverage within range with no term over
the repetition cap · `.webloc` present when a live posting URL exists · job folder containing
only deliverables.
