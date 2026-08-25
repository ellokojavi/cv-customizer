# Quickstart

Roughly 45 minutes, most of it in step 2. The quality of everything this system produces is
bounded by your profile, so that is where the time goes.

---

## 1. Install (5 min)

```bash
cp .claude/settings.example.json .claude/settings.json
cp config/search.example.json    config/search.json
cp config/documents.example.json config/documents.json
cp -r profile.example            profile
```

Open `.claude/settings.json` and replace every `<PROJECT_ROOT>` with the absolute path of your
checkout. Permission rules are matched literally — a relative path silently fails to match.

Verify the toolchain:

```bash
python3 engine/lib/check_cv_tests.py     # 17/17 against the example profile
soffice --version                        # needed for DOCX to PDF
```

---

## 2. Write your profile (30 min — the part that matters)

Edit the four files in `profile/`. Do not skim this step; everything downstream inherits from it.

**`identity.json`** — name, contact, and three things the system cannot infer:

- **`title_ceiling.highest_real_title`** — the most senior title you *actually held*. You may
  apply to roles above it. Your history is never inflated to match. This is the most common way
  a tailored CV starts lying, and it happens gradually.
- **`employment_status`** — whether you are currently employed, and if not, when the last role
  ended. Prevents "Present" quietly persisting in a date range for months.
- **`auto_reject_employers`** — places you will not go back to. Saves you re-deciding every time
  one appears in a search.

**`guardrails.json`** — the honesty pass, and the highest-value thing in setup. Ask yourself the
uncomfortable version of the question:

> *What would a job description ask for that I would have to admit, in an interview, I have not
> actually done?*

Every honest answer becomes a guardrail. Typical shapes, all demonstrated in the example file:

| Shape | Example |
|---|---|
| A title you never held | `VP` / `Vice President` |
| A figure that drifted between CVs | an old `$500K` where the defensible number is `$250K` |
| A tool you never touched hands-on | `Kafka`, `Flink` |
| Work someone else owned | `P&L` |
| A codename meaningless to outsiders | `Nightjar`, unless defined at first mention |
| An inconsistent tenure figure | `9 years` where you say `12` everywhere else |

**`guardrail_tests.json`** — for each guardrail, at least one case that must fire and one that
must *not*. The second kind matters more than it looks: a rule you only tested in the firing
direction is a rule you will delete the first time it cries wolf on a legitimate sentence.

**`links.json`** — the canonical anchor→URL table. Every build rebuilds links from this file
rather than inheriting them, because copying a previous CV preserves formatting but *not* link
correctness: press links decay into homepages and half the set goes missing, silently.

Also drop your existing career document into `profile/source/` and point
`identity.json → source_documents.career_context` at it. A long messy one beats a polished
short one — this is the system's source of truth for every metric and date.

Check your work:

```bash
python3 engine/lib/check_cv_tests.py     # your own cases must pass
```

---

## 3. Set your search policy (5 min)

Edit `config/search.json`:

- **`level`** — target titles, the equivalence test for borderline ones, and your comp floor.
- **`geography`** — a **hard filter**, not a preference. If you will not relocate, say so here
  and the system stops surfacing roles that waste your time. For the LinkedIn geo ID, run a
  filtered search in a browser and copy the `geoId` parameter out of the URL.
- **`domains_priority`** — ranked. The bottom of the list is volume expansion, not permission
  to stretch.

`config/documents.json` holds page caps, font, and the filename pattern. The defaults are
reasonable; change them to taste.

---

## 4. Generate your base CV (2 min)

```bash
python3 engine/lib/build_cv.py -o /tmp/base_cv.docx
soffice --headless --convert-to pdf --outdir /tmp /tmp/base_cv.docx
python3 engine/lib/check_cv.py --cv /tmp/base_cv.docx
```

Out of the box, with the example profile untouched, that produces a CV and the auditor reports
**zero failures**. Do the same with your own `career.json` and fix what it flags — that is your
baseline, and every tailored version starts from it.

If you already have a CV you trust, seed the data from it rather than typing it out:

```bash
python3 engine/lib/extract_career.py <your_cv.docx> -o profile/career.json
```

Links are rebuilt from `profile/links.json` on every generation, so they cannot drift the way
they do when you copy last month's document. If two links share the same anchor text, give each
an explicit anchor:

```json
"Press mention (2024)": { "anchor": "TechCrunch", "url": "https://…" }
```

## 5. First real run (5 min)

```bash
claude
```

```
/jd https://example.com/careers/some-real-posting
```

You should get a fit verdict *before* any document work. If the posting fails a hard filter, the
run stops there — that is correct behavior, not a failure.

If it builds, audit it:

```bash
python3 engine/lib/check_cv.py "<the new application folder>"
```

Exit 0 means it passed. Anything else, fix and re-run.

---

## Two rules that keep this working

**When a guardrail fires on legitimate text, that is a bug in the pattern — not in the CV.**
Add the sentence to `guardrail_tests.json`, then loosen `allow_context` in `guardrails.json`.
Never reword a CV to slip past a guardrail; that inverts the entire mechanism and you will not
notice until something untrue has shipped.

**Build in a scratch directory, never in the application folder.** LibreOffice and `pdftoppm`
both drop working files beside their input. Copy in, convert there, move only the finished PDF
back.

---

## Troubleshooting

**Everything SKIPs on identity checks** — `profile/` is missing or misnamed. The auditor degrades
deliberately rather than failing, so a fresh install runs; it says so at the top of the report.

**Page-length check SKIPs** — install `pymupdf`, or accept that length goes unmeasured.

**Permission prompts on every command** — `<PROJECT_ROOT>` was not replaced in
`.claude/settings.json`, or was replaced with a relative path.

**A `~$something.docx` fails an integrity check** — that is a Word owner-lock file, about 162
bytes. It is junk, not a damaged CV. Delete it.
