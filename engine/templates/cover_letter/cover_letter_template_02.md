# Cover Letter Template 02 — "Classic Serif, One Page"

Person-agnostic base for the cover-letter half of the package. Built the same way as
`cv_template_01`: only the text inside existing `<w:t>` nodes was rewritten, so every formatting
attribute is the original.

- **File:** `cover_letter_template_02.docx`
- **Generated:** 2026-08-23, from its matching cover letter via `engine/lib/neutralize_docx.py … cover_letter`
- **Measured length with the placeholder content:** 1 page, 0.594 fill. Body runs **261 words**, inside the 250-400 target.
- **Residual personal strings:** none, including the `mailto:` target.

---

## Page and type setup

| Property | Value |
|---|---|
| Page | 8.5 × 11 in (US Letter) |
| Margins | 0.75 in on all four sides |
| Font | Times New Roman throughout |
| Name | 15 pt bold |
| Everything else | 11 pt regular |
| Alignment | left throughout |
| Not present | tables, bullets, numbering, borders, headers/footers, images |

**Note a real inconsistency with the CV.** The pre-delivery checklist says the cover letter carries
"the same header as the CV", but the two differ: the CV header is 10 pt on 0.625 in margins and
includes a GitHub handle; this letter is 11 pt on 0.75 in margins and does not. The letter also
hyperlinks the email address, which the CV does not. Neither is wrong, but the generator should
make this a deliberate choice — either unify the header block across both documents or record
the difference as intended. Left as-is in the template so nothing was changed silently.

---

## Paragraph map

11 paragraphs. Indices are stable and are what the generator writes into.

| Idx | Slot | Placeholder |
|---|---|---|
| 0 | Name | `FIRSTNAME LASTNAME` |
| 1 | Contact line (2 hyperlinks: email, LinkedIn) | `City, ST │ first.last@example.com │ LinkedIn │ Work Authorization` |
| 2 | Date | `Month DD, YYYY` |
| 3 | Addressee | `Hiring Team` |
| 4 | Company | `Company Name` |
| 5 | Salutation | `Dear Hiring Team,` |
| 6 | ¶1 — the role, and why this intersection | lorem, ~370 chars |
| 7 | ¶2 — evidence, every claim with a number | lorem, ~740 chars |
| 8 | ¶3 — the honest gap, then the ask | lorem, ~570 chars |
| 9 | Sign-off | `Best regards,` |
| 10 | Name | `Firstname Lastname` |

Three body paragraphs is the working shape; the rule allows three or four. A fourth is added by
inserting after index 7, which shifts the sign-off indices — the generator should address the
sign-off by matching its text rather than by a fixed index.

---

## Invariants the generator must preserve

1. **250-400 words** across the body paragraphs, half a page ideal.
2. **8-12 JD keywords**, no single keyword more than 2-3 times, in the JD's exact phrasing.
3. **Keyword-load the opening paragraph** — it carries the most screening weight.
4. **The third paragraph names the gap honestly**, then asks. This is the paragraph that makes the letter credible; it is not optional padding.
5. **Zero em dashes and en dashes.**
6. **One page.** Never two.
7. **Date written out** (`Month DD, YYYY`), matching the application date.
8. **Addressee**: a named hiring manager when one is known and verified, otherwise `Hiring Team`. Never invent a name.
