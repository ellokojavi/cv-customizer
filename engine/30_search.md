# 30 — Searching for postings

Every filter — level, compensation, geography, domains, cadence, source order — comes from
`config/search.json`. This file is the method only.

---

## Never skip a source

A delta search filters for **new postings within** each source. It does not skip whole sources,
and it does not defer a tier to a multi-day rotation. If time is short, scan every source more
shallowly rather than dropping any, and say so honestly in the report.

This rule exists because source-skipping is invisible in the output. A run that covered eight of
twelve sources looks exactly like a run that covered twelve, and the gap only surfaces when a
strong-fit role turns up somewhere that was quietly dropped.

## Run the hardest tier first

`config/search.json` → `cadence.first_tier_each_run` names the tier that goes first. It is
deliberately the one with **no JSON API**, because that is the one that silently gets skipped.

The general trap: boards that expose a JSON endpoint can be swept in bulk in a single pass, and
boards that require a rendered browser cannot. Letting convenience set the order quietly narrows
the entire search to whichever companies happen to have modern tooling — often exactly the wrong
subset. Order by value, not by ease.

Before assuming a board has no API, **look**. Open it in a browser and watch the network tab
while the listings load. "No API path" is frequently an assumption nobody has retested, and
boards that were browser-only last year often are not.

Common endpoint shapes worth trying first:

```
Greenhouse   https://boards-api.greenhouse.io/v1/boards/<slug>/jobs
Ashby        https://api.ashbyhq.com/posting-api/job-board/<slug>?includeCompensation=true
Lever        https://api.lever.co/v0/postings/<slug>?mode=json
```

## Verify live, or do not report

404s, board-index redirects, and stale aggregator caches produce false positives reliably enough
that an unverified role is worse than no role — it costs assessment effort and erodes trust in
the whole report. Open the posting on the employer's own applicant tracking system before
believing its title, level, location, or existence.

Two specific traps:

- **Aggregators synthesize.** Some rewrite titles and locations outright. Treat every
  aggregator-sourced field as fabricated until confirmed at the source.
- **Job-board stubs often will not render** their body without authentication, though titles and
  locations do. Never assess from a stub; resolve it to the canonical posting.
- Some enterprise boards render slowly enough to look empty. Re-read once before discarding.

## Mine the inbox

Job-alert digests are a first-class source, not a fallback. **Parse the full body of each
digest, not just the subject line** — the subject usually shows one role and the body carries
several. Push every link through the same pipeline as everything else.

## The source types, in priority order

Company boards first, everything else additive. Board coverage and technique live in
`engine/templates/board_library.md`; the instance's actual list lives in the user's own board
file.

**1. Direct company boards (primary).** Company-owned applicant tracking systems are fresher
than any aggregator, carry no dead reposts, and are filterable. Delta-scan them.

**2. Search-engine fan-out (secondary).** Catches companies not on the list. Treat every result
as a lead to verify, never as truth — aggregator cache rots and produces confident false
positives. Rotate query templates across ATS hosts and target titles rather than reusing one
query, which returns the same stale page set every time:

```
site:<ats-host> "<target title>" (<domain terms>) <year>
"<target title>" (<domain terms>) remote <year>
```

**3. Inbox mining (mandatory, every run).** Job-alert digests are a first-class source. Two
rules, both learned expensively:

- **Parse the full body, not the subject line.** Digests headline one role and list several more
  inside, often as secondary cards. A real strong-fit role has been found only in that position.
- **Never trust the digest's title or location text.** Resolve every link to the employer's own
  posting before believing anything about it.

Also action the *status* signals sitting in the inbox: rejections, confirmations, and withdrawn
postings all update registry state. Read only; never send.

**4. Professional-network job feeds.** High signal on level and location, but they rank on title
and seniority match rather than domain defensibility — so they surface level-perfect,
domain-wrong roles constantly. Use them as a competitiveness and compensation signal layered on
top of the domain filter, never as a reason to relax it.

Where the platform offers a recency filter, note that a **24-hour window makes a missed day a
permanent gap.** Those searches run every pass, not on the slower board cadence. Run two: one
national remote-eligible, one pinned to the home metro for hybrid and on-site — the national
search does not reliably surface local hybrid roles, which is a real and easily-missed hole.

**5. Investor-portfolio and local-ecosystem boards.** Public company boards rarely post the most
senior roles; at growth-stage companies that layer lives on investor talent boards instead. Most
are aggregators with keyword and location filters. Local-ecosystem boards are weighted toward
the home metro by construction, which matters most when location is the binding constraint.

**6. Referral paths and inbound (highest conversion, lowest volume).** Before cold-applying to a
verified fit, check for a warm path into the company. Referrals convert far better than cold
applications; a day's delay to ask is usually worth it. Inbound recruiter interest belongs in the
same bucket — surface it rather than letting it sit in an inbox.

## One pipeline for every candidate

**dedup → live-verify in a real browser → assess → log.**

No exceptions and no shortcuts, regardless of how a posting arrived. Dedup first: reassessing a
role already in the registry wastes the effort twice and can produce a second application to the
same posting.

Track what was scanned. An untracked scan is indistinguishable from a skipped one, which means
coverage claims cannot be checked and gradually stop being true.
