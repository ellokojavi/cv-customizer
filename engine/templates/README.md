# engine/templates — the deliverable templates

Every document the system ships to a user is generated from one of these. They contain no
personal content: no name, no employer, no city, no figure, no live URL. Filling them is the
generator's job; a user never edits them.

| # | Deliverable | Files | Source |
|---|---|---|---|
| 01 | CV | `cv/cv_template_01.docx` · `.pdf` · `.md` | a real, ATS-tested CV, neutralized |
| 02 | Cover letter | `cover_letter/cover_letter_template_02.docx` · `.pdf` · `.md` | its matching cover letter, neutralized |
| 03 | Outreach plan | `outreach/outreach_plan_template_03.md` | the common structure of three real plans |

The `.pdf` beside each DOCX is the reference render: what the template looks like before any
content lands. The `.md` beside it is the spec — page setup, paragraph map, and the invariants
the generator must not break.

---

## How 01 and 02 were made, and why it matters

Both were derived from real documents by rewriting **only the text inside existing `<w:t>`
nodes**. Runs, run properties, tab stops, numbering definitions, paragraph borders, and section
properties were never touched.

This matters because the formatting that makes these documents work is fragile and mostly
invisible: the right tab stop that puts dates flush at the margin, the numbering definition
behind the bullets, the bottom border under each section heading. Rebuilding those from scratch
is how they drift. Inheriting them from a document that already passed real ATS screens is how
they stay correct.

The same reasoning is why the generator must **write into these templates rather than construct
a DOCX**, and why it must **rebuild every hyperlink from the user's canonical link list rather
than inherit one**. Copying preserves formatting; it does not preserve link correctness. That
distinction is the cause of a recurring bug in the pre-productization system.

`engine/lib/neutralize_docx.py <source.docx> <template.docx> <cv|cover_letter>` regenerates
either template from a newer source document. Its `OVERRIDES` maps are per-template and assume
the source's paragraph count and ordering; a restructured source needs the map adjusted.

---

## Shared invariants

Applying to every deliverable:

- **Times New Roman throughout**, single column, left-aligned. No tables, text boxes, layout columns, headers/footers, icons, or images — all of them break Workday and Taleo parsing.
- **Zero em dashes and en dashes**, anywhere.
- **Dates as `Mon YYYY - Mon YYYY`**, hyphen not en dash, and never "Present" for a role that has ended.
- **Native selectable-text PDF**, rendered from the same DOCX, never a scanned image.
- **Length is measured, not eyeballed:** `(pages - 1) + (last_content_y - top_margin) / usable_height`. CV cap 1.60 by default; cover letter exactly 1 page.
- **Build in a scratch directory, never in the application folder.** `soffice` drops `.~lock.*#` and `lu*.tmp` beside its input and `pdftoppm` drops `page-*.jpg` into its outdir; only the finished PDF moves back.
- **Hyperlinks are partial-text anchors** on a product, publication, or project word — never a whole title line, never a bare company homepage.
- **Nothing enters a deliverable that the candidate cannot defend in an interview.** This is the one rule the generator enforces rather than parameterizes.

---

## The templates deliberately fail their own audit

Run the auditor against a bare template and it reports `Bullets FAIL — 15/15 carry no number`:

```bash
python3 engine/lib/check_cv.py --cv engine/templates/cv/cv_template_01.docx
```

That is correct, not a bug. The placeholder text is lorem ipsum, and the rule is that **every
bullet carries at least one number** — XYZ form, "accomplished X as measured by Y, by doing Z".
The check exists precisely because metric-less bullets are the easiest thing to leave in and the
hardest to notice; one survived undetected across an entire archive of real applications before
this was mechanized.

So the first clean audit is a milestone, not a formality: it means every bullet says what
changed and by how much. Everything else in the template is built to pass from the start —
fonts, tab stops, section order, and the placeholder links, which match the ones in
`profile.example/links.json` so a fresh install audits clean before anything is edited.

---

## Adding a template

New variants keep the numbering (`04`, `05`, …) and the same three-file shape for DOCX
deliverables: the template, a reference render, and a spec with the paragraph map. A variant
that changes page setup — different margins, a sans-serif face, a one-page-only CV — is a new
template, not an edit to an existing one, so that anything already generated stays reproducible.
