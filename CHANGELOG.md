# Changelog

## Unreleased

- **Search and scanning are now documented in the README.** Roughly half the engine was
  invisible to anyone discovering the project. Stated honestly: `board_scan.py` performs zero
  network I/O, there is no crawler, and nothing runs on a timer unless you schedule it.
- **Fixed: a board list shipped inside the engine.** `board_scan.py` hardcoded 21 board slugs
  and a staleness threshold, so a new user was warned about companies they had never heard of.
  Moved to `config/search.json` → `boards.core`, shipped empty. Found by verifying a README
  claim against the running code rather than trusting it.
- **Fixed: `python-docx` was undocumented** despite being required to generate any document.
- README now leads with a runnable 60-second demo, a rendered sample, real audit output, and a
  real guardrail refusal.

## v1.0.0 — 2026-08-24

First complete release. The engine generates a full application package from structured
profile data and refuses to deliver one that does not audit clean.

### What works end to end

- **`/setup`** — guided first run: extract career data from an existing CV, interview the
  things a parse cannot infer, run the honesty pass that produces the guardrails, smoke-test
  by generating a CV.
- **`/jd <url>`** — assess a posting against the configured hard filters, deliver a five-part
  fit verdict, and on a strong fit build the whole package.
- **`build_package.py`** — CV, cover letter, outreach plan, both PDFs, and the `.webloc` in one
  call, generated in scratch and copied into the application folder **only if the audit
  passes**.
- **`check_cv.py`** — the pre-delivery gate: measured page extent, dashes, font, date format and
  right tab stops, chronology, section order, forced page breaks, bullet metrics, the hyperlink
  table, filenames, folder hygiene, JD keyword coverage, and the profile guardrails.
- **`/daily-search`, `/followups`, `/reaudit`, `/hygiene`, `/refresh`** — search, the
  post-application worklist, re-checking unsent packages, and maintenance.
- **`publish.py`** — assembles the shippable subset and refuses on any identity term, reading
  inside `.docx` and `.pdf`.

### The design decisions worth knowing

**Four layers, strictly separated.** `engine/` (method) names no person, employer, city, figure,
or path. `config/` holds policy. `profile/` holds identity. `_registry/` holds state. Only the
first two ship, so upgrading means replacing `engine/` and keeping everything else.

**Honesty is mechanical, not aspirational.** A model optimizing a CV against a job description is
structurally inclined to overclaim. The never-claim list lives as machine-checkable patterns and
the auditor hard-fails any document containing them. Corollary: a guardrail firing on legitimate
text is a bug in the *pattern* — add the case to the fixtures, then loosen `allow_context`. Never
reword a document to slip past a guardrail.

**Generate, do not copy.** Copying last month's CV preserves formatting but not link correctness:
press links decay into homepages and half the set silently vanishes. Generating from data removes
the bug class instead of auditing for it.

### Known limitations

- Scoped to a senior individual running a targeted search in the US market. Levels, domains, and
  geography are configurable, so adjacent fields work, but early-career or non-US searches will
  need more than a config edit.
- Cover-letter paragraphs and outreach research are human input. The engine guarantees the
  packaging, not the judgement.
- The board library ships technique, not companies. A curated employer list is specific to one
  field, level, and metro.
- `soffice` (LibreOffice) is required for PDF conversion and fails silently if absent, so
  `build_package.py` checks for it up front and stops.
