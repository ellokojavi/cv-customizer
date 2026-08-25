#!/usr/bin/env python3
"""Ask the registry what actually converted, and refuse to overclaim.

    python3 engine/lib/calibrate.py                # the report
    python3 engine/lib/calibrate.py --backfill     # rows a human must classify
    python3 engine/lib/calibrate.py --json

Why
---
Every judgement the system makes - the fit verdict, the comp floor, which
sources to scan first, whether outreach is worth the effort - has been running
unmeasured. This reads the outcomes already sitting in the registry and reports
which of those judgements have any observed relationship with advancing.

The honesty constraint
----------------------
Job-search data is tiny and slow. A few dozen applications with a handful of
successes cannot support a confident claim about anything, and a tool that
prints "Strong fits convert 6%" next to "Partial 5%" invites a conclusion the
sample cannot carry.

So every comparison is reported with the arithmetic visible, and any split
whose evidence is too thin is labelled INSUFFICIENT rather than ranked. The
tool states what it would take to know - see `needed_for_signal`. A calibration
report that manufactures confidence is worse than no report, because the whole
point is to stop trusting unvalidated judgement.
"""

import argparse
import csv
import json
import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths  # noqa: E402
import outcomes as OC  # noqa: E402

#: Below this many submitted applications in a bucket, report counts only.
MIN_BUCKET = 10
#: Below this many total successes, no comparison between buckets is meaningful.
MIN_SUCCESSES = 5


def load(csv_path):
    with open(csv_path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def enrich(rows):
    out = []
    for r in rows:
        outcome, conf = OC.classify(r)
        r = dict(r)
        r["_outcome"], r["_confidence"] = outcome, conf
        out.append(r)
    return out


def bucket_stats(rows, keyfn):
    """{bucket: (submitted, advanced)} over rows that were actually submitted."""
    agg = defaultdict(lambda: [0, 0])
    for r in rows:
        if not OC.submitted(r["_outcome"]):
            continue
        k = keyfn(r)
        if not k:
            continue
        agg[k][0] += 1
        agg[k][1] += 1 if OC.advanced(r["_outcome"]) else 0
    return {k: tuple(v) for k, v in agg.items()}


def needed_for_signal(base_rate):
    """Roughly how many applications per bucket before a difference is readable.

    Deliberately crude: at these rates the binomial noise dominates, and the
    useful message is an order of magnitude ("dozens, not hundreds"), not a
    precise power calculation that would imply more rigour than the data has.
    """
    if base_rate <= 0:
        return "at least one success in any bucket before any comparison means anything"
    per_bucket = max(30, int(round(3 / base_rate)))
    return f"roughly {per_bucket}+ applications per bucket to read a real difference"


def render_split(title, stats, question):
    lines = [f"\n{title}", f"  {question}"]
    total_sub = sum(s for s, _ in stats.values())
    total_adv = sum(a for _, a in stats.values())

    if not stats:
        lines.append("  no submitted applications recorded")
        return lines, False

    width = max(len(str(k)) for k in stats)
    lines.append(f"    {'bucket':<{width}}  {'applied':>7} {'advanced':>9}  rate")
    for k, (sub, adv) in sorted(stats.items(), key=lambda kv: -kv[1][0]):
        rate = f"{adv / sub * 100:.0f}%" if sub else "-"
        flag = "" if sub >= MIN_BUCKET else "   (thin)"
        lines.append(f"    {str(k):<{width}}  {sub:>7} {adv:>9}  {rate:>4}{flag}")

    readable = total_adv >= MIN_SUCCESSES and all(
        s >= MIN_BUCKET for s in (v[0] for v in stats.values()) if s
    )
    if not readable:
        base = total_adv / total_sub if total_sub else 0
        lines.append(f"    -> INSUFFICIENT EVIDENCE: {total_adv} success(es) across "
                     f"{total_sub} applications.")
        lines.append(f"       Need {needed_for_signal(base)}.")
        lines.append("       Report the counts; do not act on the rates.")
    return lines, readable


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--csv", default=paths.CSV_PATH)
    ap.add_argument("--backfill", action="store_true",
                    help="list rows whose outcome could not be determined")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if not os.path.exists(args.csv):
        # A fresh install has nothing to calibrate. Say so usefully rather than
        # erroring - the same principle as the auditor skipping identity checks
        # when no profile exists yet.
        print(f"\nNo registry yet at {args.csv}")
        print("\nCalibration needs outcomes, and outcomes need applications. Log postings")
        print("with `registry.py add`, mark them `applied`, and record what happened with")
        print("`/outcome`. Come back once a dozen or so have resolved.")
        print("\nNothing here is measurable before then, and pretending otherwise is the")
        print("failure mode this tool exists to prevent.")
        return 0
    rows = enrich(load(args.csv))
    if not rows:
        print("\nThe registry is empty. Nothing to calibrate yet.")
        return 0

    dist = Counter(r["_outcome"] for r in rows)
    weak = [r for r in rows if r["_confidence"] == "weak"]
    submitted = [r for r in rows if OC.submitted(r["_outcome"])]
    advanced = [r for r in rows if OC.advanced(r["_outcome"])]

    if args.backfill:
        print(f"{len(weak)} row(s) need a human outcome call.\n")
        print("These have an ambiguous status ('rejected' and 'closed' were used both for")
        print("'we passed' and 'they passed on us') and no decisive note. Resolve each with:")
        print('  python3 engine/lib/registry.py setstatus "<company>" --to <status> --note "<what happened>"\n')
        for r in weak:
            print(f"  {r['company'][:26]:<28} {r['status'] or '(none)':<12} "
                  f"{(r['notes'] or '')[:74]}")
        return 0

    if args.json:
        print(json.dumps({
            "outcome_distribution": dict(dist),
            "submitted": len(submitted),
            "advanced": len(advanced),
            "unclassified": len(weak),
            "fit": bucket_stats(rows, lambda r: r["fit_verdict"] or None),
            "source": bucket_stats(rows, lambda r: OC.normalize_source(r["source"])),
            "outreach": bucket_stats(
                rows, lambda r: "outreach done" if r.get("outreach_status") else "no outreach"),
        }, indent=2))
        return 0

    print(f"\nCALIBRATION  ({len(rows)} registry rows)")
    print("=" * 64)

    print("\nWhat happened to everything")
    for outcome, n in dist.most_common():
        print(f"    {OC.LABELS[outcome]:<34} {n:>4}")
    if weak:
        print(f"\n    {len(weak)} row(s) are UNKNOWN - run --backfill. Until they are")
        print("    resolved every rate below is a lower bound, not a measurement.")

    base = len(advanced) / len(submitted) if submitted else 0
    print(f"\nHeadline: {len(advanced)} of {len(submitted)} submitted applications reached a "
          f"human stage ({base * 100:.0f}%).")

    blocks = [
        ("FIT VERDICT", bucket_stats(rows, lambda r: r["fit_verdict"] or None),
         "Does the fit assessment predict which applications advance?"),
        ("SOURCE CHANNEL", bucket_stats(rows, lambda r: OC.normalize_source(r["source"])),
         "Which sources produce applications that go anywhere?"),
        ("OUTREACH", bucket_stats(
            rows, lambda r: "outreach done" if r.get("outreach_status") else "no outreach"),
         "Does hiring-manager outreach change the outcome?"),
    ]
    any_readable = False
    for title, stats, question in blocks:
        lines, readable = render_split(title, stats, question)
        any_readable = any_readable or readable
        print("\n".join(lines))

    print("\n" + "=" * 64)
    if not any_readable:
        print("VERDICT: nothing here is decidable yet, and that IS the finding.")
        print("Every judgement in this system - the fit framework, the comp floor, the")
        print("source ordering, the outreach premise - is still unvalidated. Keep")
        print("recording outcomes; re-run when the numbers grow.")
        print("\nThe most useful thing you can do meanwhile is make each application")
        print("recordable: resolve the UNKNOWN rows, and set an outcome the day you")
        print("learn one. A rate computed from half-recorded data misleads twice.")
    else:
        print("Some splits now carry enough evidence to act on. Treat the rest as counts.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
