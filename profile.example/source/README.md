# profile/source/

Put your raw career material here, then point
`profile/identity.json → source_documents.career_context` at the main one.

**What to put in:**

- Your current CV, in whatever state it is in
- A career document: roles, dates, scope, team sizes, and the numbers you can actually defend
- A LinkedIn PDF export (Profile → More → Save to PDF), if you have nothing better
- Old CVs, performance reviews, brag documents, launch write-ups

**A long messy document beats a short polished one.** This is the system's source of truth for
every metric and date, and it is what the auditor diffs factual claims against. Detail you leave
out here is detail no CV can use — and worse, detail the model may be tempted to approximate.

**Two things worth writing down explicitly, because nothing else captures them:**

1. **For every number: could you defend it out loud?** Write the defensible version, not the
   flattering one. If revenue grew and you owned part of that, write the part you owned.
2. **What you did *not* do.** The work adjacent to yours that someone else owned. That list
   becomes `guardrails.json`, and it is the thing that stops a keyword-matching model from
   quietly promoting you into someone else's accomplishments.

This directory is git-ignored along with the rest of `profile/`. Nothing here leaves your machine.
