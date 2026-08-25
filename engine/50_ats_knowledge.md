# 50 — ATS and screening mechanics

How the documents get read before a human reads them, and what that implies. Thresholds live in
`config/documents.json` → `keywords`.

---

## Keywords

**Use the posting's exact phrasing.** Keyword matching is literal: "project management" does not
match "program management," and "experimentation" does not match "A/B testing." Where the
candidate's experience genuinely supports the posting's term, use the posting's term.

**Target the configured range**, capping any single term at the configured repetition limit.
Aim for roughly 65–75% coverage of the posting's meaningful terms. Below about 60%, most systems
drop the candidate before a human sees anything.

**Frontload.** The summary and first competency line carry a disproportionate share of the
match — treat the first hundred words as the highest-value real estate in the document.

**Do not stuff.** Repetition past the cap degrades the LLM-screening pass (below) more than it
helps the keyword pass, and it reads badly to the human at the end. Structural words that recur
naturally in titles and headings are exempt from the cap; genuine domain terms are not.

---

## Bullets

**XYZ form: accomplished X, as measured by Y, by doing Z.** Every bullet carries at least one
number.

This is the rule most often quietly broken, because a metric-less bullet reads fine in isolation
and only looks weak beside its neighbours. It is mechanically checked for exactly that reason. A
bullet without a number is a claim without evidence, and reviewers discount it accordingly.

Where a number is genuinely unavailable, prefer scope over vagueness: team size, surface count,
number of markets, volume handled. "Led a team" is weak; "led a team of nine across three
surfaces" is not.

---

## The LLM screening pass

Modern applicant tracking systems increasingly run a language model over the application before
a recruiter sees it. It evaluates differently from keyword matching, and the two want different
things:

- **Career trajectory** — direction and acceleration, which is why reverse-chronological order
  matters and relevance-ordering backfires.
- **Inferred soft skills**, read from strong action verbs rather than adjectives. "Collaborative"
  scores nothing; "negotiated," "aligned," "unblocked" do.
- **Real-world impact**, read from metrics in context.
- **Transferability** when the domain is not an exact match — this is the one you can actively
  help. When the candidate's domain differs from the posting's, **bridge the analogy explicitly
  in one clause** rather than hoping the reader constructs it. An unstated bridge is usually not
  crossed.

It rewards natural language and penalizes keyword stuffing. The two screening layers therefore
pull in opposite directions at the margin, and natural phrasing that happens to contain the
posting's terms is what satisfies both.

---

## Format hygiene

Single column, left-aligned, standard section labels only.

**No icons, graphics, logos, photos, headers, footers, text boxes, or layout tables.** Every one
of these either fails to parse or parses into scrambled text. Multi-column layouts in particular
tend to interleave into nonsense. Native selectable-text PDF only — never a scanned image, and
never a PDF whose text layer has been stripped.

Filenames follow the configured pattern and stay short. Some systems truncate long filenames and
a few reject unusual characters outright.
