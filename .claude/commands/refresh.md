---
description: Periodic maintenance — keep the profile, boards, and built packages from rotting
---

Run the maintenance pass. Three cadences, one command; do whichever are due and say which you
skipped.

---

## Event-driven — whenever something changed

A new role, a new metric, a correction ("never say X"), or an interview outcome. Append it to
`profile/` or the rule library. This is how the knowledge base grows; it just needs an explicit
entry point so it does not depend on someone remembering.

If the correction is a new never-claim, add it as a guardrail **and** add its test cases:

```bash
python3 engine/lib/check_cv_tests.py
```

## Profile freshness

- **Dates drifting.** Any role that ended should say so. Check nothing has crept back to
  "Present" if the config bans it.
- **Employment status** in `profile/identity.json` still accurate.
- **Metrics still defensible.** Numbers age: a figure true two years ago may now be stale or
  superseded. Re-check the largest claims against the career document.
- **Links still resolve.** A press link that 404s is worse than no link, because a reader clicks
  it. Spot-check the canonical table.

## Pipeline and board health

```bash
python3 engine/lib/registry.py followups          # due actions + stale applications
python3 engine/lib/registry.py expire --days 7    # dry run: what is about to lapse
python3 engine/lib/board_scan.py status           # per-board age + staleness warnings
python3 engine/lib/registry.py sync               # reconcile folders against the registry
```

Fix any board row whose slug 404s or whose URL moved. A stale row silently becomes a skipped
board, and skipped boards are invisible in the output.

## Re-audit built-but-unsent packages

**Packages rot as rules change.** A set that passed two months ago may fail today's page cap,
filename pattern, or guardrails — and the failure is silent, because nothing re-checks a finished
folder.

```bash
for d in <application folders with nothing logged as applied>; do
  python3 engine/lib/check_cv.py "$d"
done
```

Anything still unsent and failing gets regenerated with `build_package.py` rather than patched by
hand.

## Calibration — has anything become decidable?

```bash
python3 engine/lib/calibrate.py
python3 engine/lib/calibrate.py --backfill   # rows whose outcome is unknown
```

Every judgement the system makes is a hypothesis: the fit verdict, the comp floor, the source
ordering, the premise that outreach lifts response rate. This is the only thing that checks any
of them.

**Respect an INSUFFICIENT EVIDENCE label.** At small samples the right action is to report the
counts and change nothing — acting on noise is worse than acting on instinct, because it feels
justified. When a split does clear the bar, say what it implies and change the config, not the
prose.

Resolve any UNKNOWN rows while the memory is fresh. An unrecorded outcome is gone.

## Config drift

- Does `config/search.json` still describe the search actually being run? Level, comp floor,
  geography, and domain priority all drift as a search matures.
- Does `config/documents.json` still match what is being sent?

---

Close with a short summary: what changed, what is now due, and anything you could not check.
