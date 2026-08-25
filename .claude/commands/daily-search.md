---
description: Run the full daily job search sweep
---

Run today's job search exactly as `_registry/daily_search_playbook.md` specifies. Every
filter — level, comp floor, geography, domain priority, source order — comes from
`config/search.json`. Read it; do not work from memory.

Non-negotiables for this run:

- **Never skip a source.** A delta search filters for new postings *within* each source; it does not skip sources. Cover all Tier 1 boards, the Tier 2/3 rotation, and every Tier S source. If time is tight, scan everything shallower rather than dropping anything, and say so honestly in the report.
- **Run the first tier named in `config/search.json` → `cadence.first_tier_each_run` first.** Those boards expose no JSON API, so they get skipped whenever API convenience is allowed to set the order. That is a bug, not a shortcut.
- **Open with** `python3 engine/lib/board_scan.py status` and report any stale-board warnings.
- **Inbox mining is mandatory**, not optional. Parse the full body of each job-alert digest, not just subject lines. Treat every aggregator-sourced title and location as fabricated until confirmed on the employer's own ATS — Lensa in particular invents both.
- **Both LinkedIn searches**, using the parameters in `config/search.json` → `geography.linkedin`: national remote filtered to the home state, and home-metro hybrid/on-site by geo ID.
- Every candidate runs the same pipeline: dedup -> live-verify in a real browser -> assess -> log. Never report a role that was not verified live.
- Strong fits build immediately, no go-ahead needed.

Close the run with:

1. `python3 engine/lib/registry.py followups` — act on anything due, and flag stale applications for the outreach scout.
2. The Partial triage batch: one line per open Partial (company | role | comp | honest gap) so I can decide in a single reply.
3. A short coverage statement: which sources were scanned, and anything you could not reach.
