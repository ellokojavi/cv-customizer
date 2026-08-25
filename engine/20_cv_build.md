# 20 — Building the CV and cover letter

Mechanics. Parameters come from `config/documents.json`; content facts come from `profile/`.

---

## Generate from data — do not copy the last CV

```bash
python3 engine/lib/build_cv.py -o /tmp/cvbuild/CV.docx [--tailor tailor.json]
```

It renders `profile/career.json` into `engine/templates/cv/cv_template_01.docx`, rebuilding
every hyperlink from `profile/links.json`.

**Generating removes the drift bug rather than auditing for it.** The old method copied the
previous application's CV and edited it, which preserved formatting but not link correctness —
press links decayed into homepages, canonical sources were replaced by whatever was easier to
find, and half the set silently vanished. Because nothing is inherited, there is nothing to
drift: every link in the output was placed deliberately by that run.

It **writes into the template** rather than constructing a document, and clones paragraphs from
real ones in the template, so each generated paragraph inherits genuine styling. The fragile,
invisible parts — the right tab stop, the numbering definition behind the bullets, the border
under each heading — are never rebuilt.

To seed `career.json` from a CV that already passed the auditor:

```bash
python3 engine/lib/extract_career.py <existing_cv.docx> -o profile/career.json
```

Extraction is verbatim: no judging, no rewriting. Tailoring happens afterwards against a
known-good baseline, via a `--tailor` overlay that can replace the summary, select or reorder
competencies, and swap individual bullets. It cannot invent content — anything it introduces
still has to survive the auditor and the profile guardrails.

### If you must edit an existing document instead

Copy the most recent finished CV and edit runs in place — never rebuild formatting from scratch.

```python
# dump paragraph indices first - they drift as the document evolves
for i, p in enumerate(Document(F).paragraphs):
    print(i, repr(p.text[:40]))
# then set text on runs[0] and blank the rest, so run formatting survives
```

If you take this path, **re-derive the whole link set anyway** (see below). Copying preserves
formatting; it does not preserve link correctness.

**Structure:** header → SUMMARY → CORE COMPETENCIES → PROFESSIONAL EXPERIENCE → EDUCATION →
ADDITIONAL. Education flows directly after Experience — no forced page break. Use `keepNext`
and `keepLines` to hold small sections together instead.

**Professional Experience is strictly reverse-chronological.** Never reorder by relevance, and
never group roles thematically. Recruiters read for trajectory; reordering reads as concealment.

---

## Length is measured, never eyeballed

The cap is `config/documents.json` → `cv_page_cap`. Usable height is page height minus top and
bottom margins:

```python
ratio = (pages - 1) + (last_content_y - top_margin) / usable_height
```

`engine/lib/check_cv.py` computes this. Do not estimate it by looking at the page.

If it overflows, cut in this order and re-measure after each pass:

1. **Tighten the summary.** It drifts longest; five or six lines is plenty.
2. **Compress the oldest roles.** Keep the role, company, and date line; shorten or drop the
   bullet.
3. **Shorten long bullets** by removing narrative connective tissue — never the metrics or the
   keywords.
4. **Trim competencies** to the items the posting actually asks for.

**Never shrink the font, narrow the margins, drop the tab stops, or cut numbers to make room.**
Cut prose, keep evidence. Those four shortcuts all trade a real signal for an invisible one.

---

## Dates: right-aligned on the role line

Role and company flush left, date range flush right, on the same line. Implement with a **right
tab stop plus a single tab character** — never a two-column table, never a text box, never
manual spaces. Tables and text boxes break ATS parsing; spaces drift with font metrics.

**Derive the tab position from the section geometry. Never hardcode it:**

```python
s = doc.sections[0]
pos = (s.page_width - s.left_margin - s.right_margin).inches
p.paragraph_format.tab_stops.add_tab_stop(Inches(pos), WD_TAB_ALIGNMENT.RIGHT)
# text must be:  "Role Title\tMon YYYY - Mon YYYY"
```

A hardcoded position silently mismatches the moment margins change, and the failure looks like a
wrapped line rather than a wrong number.

Verify in the **rendered PDF**, not the DOCX: dates must sit flush right on the same baseline as
the role, with no wrap. If a role line is long enough to wrap, shorten the left text rather than
dropping the tab stop. Note that `w:ptab` does not survive LibreOffice conversion; a real tab
stop does.

---

## Hyperlinks: rebuild, never inherit

**Re-derive the entire link set from `profile/links.json` on every build**, overwriting whatever
the base document carried.

This exists because copying a previous CV preserves formatting but **not** link correctness.
Press links decay into homepages, canonical sources get replaced by whichever article was easier
to find, and half the set silently goes missing. The failure is invisible in the document and
obvious to anyone who clicks.

Rules: partial-text anchors only — link the product, publication, or project word, never a whole
title line. Never link a bare company homepage. Link an anchor only if that text survives in the
final document; if a bullet was cut, its link drops with it. Target range is in
`config/documents.json` → `links.min` / `links.max`.

---

## Build in scratch, never in the application folder

`soffice` writes `.~lock.*#` and `lu*.tmp` beside its input. `pdftoppm` writes render output
into its outdir, **prefixed** — `cvpage-1.jpg`, not `page-1.jpg`, which is why the junk glob
needs a leading wildcard. Copy the DOCX to scratch, convert and render there, move only the
finished PDF back.

```bash
S=/tmp/cvbuild; mkdir -p $S; cp CV.docx $S/
soffice --headless --convert-to pdf --outdir $S "$S/CV.docx"   # NOT --outdir .
pdftoppm -jpeg -r 110 "$S/CV.pdf" "$S/page"                    # then actually look at them
cp "$S/CV.pdf" .                                               # only the finished PDF
```

**Check that `soffice` actually exists before relying on it.** It fails *silently* — no error,
no exit code, simply no PDF — so a build can appear to succeed while shipping only half the
deliverable. Verify with `command -v soffice` and treat its absence as a hard stop, not a
warning.

An application folder must end up containing only deliverables. Anything else is a bug in the
build, not something to clean up afterwards.

---

## The build is not done until the auditor exits 0

```bash
python3 engine/lib/check_cv.py "<application folder>" --jd /tmp/cvbuild/jd.txt
```

Fix every FAIL and re-run. WARNs are judgment calls: decide, and say why. Report the final
summary rather than a hand-check.

Two things the auditor cannot judge, so check them yourself:

- **Rendered fidelity.** Look at the actual pages. Dates flush right, no wrapped role lines, no
  orphaned headings, no widow bullet on a near-empty final page.
- **New overreach.** The guardrails catch known-banned phrasings, not novel ones. Diff the
  factual claims against the career document every time — corrected facts silently reappear when
  a CV is built from an older base.

---

## Cover letter

250–400 words, three or four short paragraphs, half a page ideal, one page maximum. Same header
and font as the CV. Keyword-load the opening. Mirror the posting's exact language.

Name the biggest gap honestly in one clause and move on. A letter that pretends the gap is not
there invites the reader to find it themselves.
