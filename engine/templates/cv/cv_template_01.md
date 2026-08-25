# CV Template 01 — "Classic Serif, Two-Page"

Person-agnostic base for `build_cv.py`. Derived from a real, ATS-tested CV by rewriting only
the text inside existing `<w:t>` nodes, so every formatting attribute is the original one, not
a reconstruction. All personal content is replaced with lorem ipsum and placeholder labels.

- **File:** `cv_template_01.docx`
- **Generated:** 2026-08-23, from the project owner's newest CV via `engine/lib/neutralize_docx.py … cv`
- **Measured length with the placeholder content:** 2 pages, **1.570** on the fill-ratio measure — identical to the source CV, so the template doubles as a length-calibration reference.
- **Residual personal strings:** none. Verified by scanning every part in the zip.

---

## Page and type setup

| Property | Value |
|---|---|
| Page | 8.5 × 11 in (US Letter) |
| Margins | left/right 0.625 in · top/bottom 0.5 in |
| Font | Times New Roman throughout, no exceptions |
| Name | 15 pt bold |
| Contact line | 10 pt regular |
| Section headings | 10.5 pt bold + bottom border (`single`, `#000000`, `sz 6`, `space 2`) |
| Body, bullets, dates | 10 pt |
| Right tab stop | **7.25 in** = page width − left margin − right margin |
| Summary alignment | justified; everything else default left |
| Bullets | style `List Paragraph` + `numPr` (`ilvl 0`, `numId 1`) |
| Not present | tables, text boxes, headers/footers, images, columns, colour |

**The tab stop must be derived, not hardcoded.** `CLAUDE.md` §6 quotes 7.1 in, which is correct
only at 0.7 in margins. The rule is `page_width - left_margin - right_margin`; this template's
0.625 in margins put it at 7.25 in. A hardcoded 7.1 here would leave the dates 0.15 in short of
the margin.

---

## Paragraph map

48 paragraphs, addressed by index. Indices are stable for this template and are what
`build_cv.py` writes into.

| Idx | Slot | Placeholder |
|---|---|---|
| 0 | Name | `FIRSTNAME LASTNAME` |
| 1 | Contact line (2 hyperlinks) | `City, ST │ first.last@example.com │ LinkedIn │ GitHub: username │ Work Authorization` |
| 2 | Section heading | `SUMMARY` |
| 3 | Summary prose (justified) | lorem, ~600 chars |
| 4 | Section heading | `CORE COMPETENCIES` |
| 5 | Competencies, ` │ `-separated | `Competency Area One … Twelve` |
| 6 | Section heading | `PROFESSIONAL EXPERIENCE` |
| 7 | Role 1 line: title `\t` dates | `Most Recent Role Title, …` + `Jan 2023 - Dec 2025` |
| 8 | Role 1 company line | `Company One (parenthetical descriptor)   City, ST` |
| 9-11 | Role 1 bullets ×3 | lorem |
| 12-16 | Role 2: line, company, 3 bullets (one with an inline link) | |
| 17-20 | Role 3: line, company (link in company name), 2 bullets | |
| 21-24 | Role 4: line, company, 2 bullets (one with 3 inline links) | |
| 25-27 | Role 5: line, company, 1 bullet with link | |
| 28-31 | Role 6: line, company, 2 bullets (one with link) | |
| 32-34 | Role 7: line, company, 1 bullet | |
| 35-37 | Role 8: line, company, 1 bullet | |
| 38 | Section heading | `EDUCATION` |
| 39 | School 1 `\t` date | `Graduate School or University Name` + `Jun 2015` |
| 40 | Degree line `\t` location | `Degree │ GPA 0.0/0.0 │ Honors or Distinction` + `City, ST` |
| 41-42 | School 2 + degree line | |
| 43 | Section heading | `ADDITIONAL` |
| 44-47 | Four labelled categories, bold label + body, links inline | `Category One:` … `Category Four:` |

Eight experience entries and two education entries are the **maximum** shape. A shorter career
deletes trailing role blocks rather than leaving them empty; the layout is designed to be cut
down, not padded out.

---

## Invariants `build_cv.py` must preserve

1. **Never rebuild the DOCX from scratch.** Write text into existing runs. The section borders, numbering definition, and tab stops are fragile and expensive to recreate.
2. **Dates on the role line, right-aligned via one tab character and a right tab stop.** Never a two-column table, never text boxes, never manual spaces — tables and boxes break Workday and Taleo parsing, and spaces drift with font metrics.
3. **Date format `Mon YYYY - Mon YYYY`.** A hyphen, not an en dash. Never "Present".
4. **Zero em dashes and en dashes** anywhere in the document.
5. **Education flows directly after Experience** with no forced page break.
6. **Every bullet carries at least one number** once real content lands.
7. **Hyperlinks are partial-text anchors** on a product, publication, or project word, never a whole title line and never a bare company homepage. The template ships 11 anchors pointing at `example.com`; the generator overwrites every target from the user's canonical link list rather than inheriting any of them.
8. **Length is measured, not eyeballed** — `(pages - 1) + (last_content_y - top_margin) / usable_height`, capped at the configured maximum (default 1.60).

---

## Regenerating this template

`engine/lib/neutralize_docx.py <real_cv.docx> <template.docx> cv` turns any real CV into a
template of this kind: it lorem-fills prose at matching character length, keeps structural
labels, swaps hyperlink targets for `example.com`, and clears document metadata. Explicit
per-paragraph overrides live in its `CV_OVERRIDES` map and will need adjusting if the source CV
has a different paragraph count or ordering.
