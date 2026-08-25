#!/usr/bin/env python3
"""
board_scan.py — delta scanner for the daily job search (added 2026-07-28).

Why: senior PM roles trickle. Re-reading the same 200-job ATS boards every day
produced repeated zeros. This tool remembers the job-ID set it saw per board and,
on the next scan, reports ONLY the postings that are new since last time — so the
every-2-3-day sweep is cheap and catches roles the day they post.

The agent fetches each board's API JSON in the Chrome browser (the API hosts are
outside web_fetch provenance), then feeds it here. This script does NO network I/O.

State: _registry/seen_jobs/<slug>.json = {"last_scan","count","ids":{id:title}}.

Commands:
  # Feed a board's raw API JSON (Greenhouse / Ashby / Lever shapes auto-detected):
  python3 engine/lib/board_scan.py diff <slug> --json /path/to/board.json
  # Or feed IDs directly (optionally id:title pairs, comma-separated):
  python3 engine/lib/board_scan.py diff <slug> --ids "123,456,789"
  python3 engine/lib/board_scan.py diff <slug> --ids "123:VP Product,456:Head of Growth"

  python3 engine/lib/board_scan.py status            # last-scan date + count per board
  python3 engine/lib/board_scan.py show <slug>       # dump stored ids/titles for a board

Notes:
  - `diff` prints the NEW postings, then updates stored state to the current set.
  - Pass --dry to preview new postings WITHOUT updating state (e.g. to re-run).
  - Removed postings (filled/pulled) are dropped from state silently on each diff.
"""
import json, os, sys, argparse, datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths  # noqa: E402

# Code lives in engine/lib/; scan state lives with the user. See paths.py.
STATE_DIR = paths.SEEN_JOBS_DIR


def today():
    return datetime.date.today().isoformat()


def state_path(slug):
    safe = "".join(c for c in slug if c.isalnum() or c in "-_")
    return os.path.join(STATE_DIR, f"{safe}.json")


def load_state(slug):
    p = state_path(slug)
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    return {"last_scan": "", "count": 0, "ids": {}}


def save_state(slug, ids_map):
    os.makedirs(STATE_DIR, exist_ok=True)
    data = {"last_scan": today(), "count": len(ids_map), "ids": ids_map}
    with open(state_path(slug), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def parse_board_json(raw):
    """Return {id(str): title(str)} from Greenhouse / Ashby / Lever JSON shapes."""
    data = json.loads(raw) if isinstance(raw, str) else raw
    out = {}

    # Lever: top-level list of postings [{id, text, categories:{location}}]
    if isinstance(data, list):
        rows = data
    # Greenhouse/Ashby: {"jobs":[...]}
    elif isinstance(data, dict) and "jobs" in data:
        rows = data["jobs"]
    elif isinstance(data, dict) and "postings" in data:
        rows = data["postings"]
    else:
        rows = []

    for r in rows:
        if not isinstance(r, dict):
            continue
        jid = r.get("id") or r.get("jobId") or r.get("job_id")
        title = (
            r.get("title")            # Greenhouse / Ashby
            or r.get("text")          # Lever
            or r.get("name")
            or ""
        )
        loc = r.get("location")
        if isinstance(loc, dict):
            loc = loc.get("name") or loc.get("locationName") or ""
        elif loc is None:
            cats = r.get("categories") or {}
            loc = cats.get("location", "") if isinstance(cats, dict) else ""
        label = title if not loc else f"{title}  [{loc}]"
        if jid is not None:
            out[str(jid)] = label.strip()
    return out


def parse_ids_arg(s):
    """'123,456' or '123:VP Product,456:Head of Growth' -> {id:title}."""
    out = {}
    for chunk in s.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        if ":" in chunk:
            jid, title = chunk.split(":", 1)
            out[jid.strip()] = title.strip()
        else:
            out[chunk] = ""
    return out


def cmd_diff(args):
    if args.json:
        with open(args.json, encoding="utf-8") as f:
            current = parse_board_json(f.read())
    elif args.ids:
        current = parse_ids_arg(args.ids)
    else:
        sys.exit("diff needs --json <file> or --ids \"...\"")

    if not current:
        print(f"[{args.slug}] parsed 0 postings — check the JSON shape / slug.")
        return

    prev = load_state(args.slug)
    prev_ids = set(prev.get("ids", {}).keys())
    new_ids = [i for i in current if i not in prev_ids]

    print(f"[{args.slug}] total now={len(current)}  previously seen={len(prev_ids)}"
          f"  NEW={len(new_ids)}  (last scan {prev.get('last_scan') or 'never'})")
    if new_ids:
        print("--- NEW postings (run these through the level/domain filter) ---")
        for i in new_ids:
            print(f"  {i}\t{current[i]}")
    else:
        print("  (nothing new since last scan)")

    if args.dry:
        print("[dry run — state NOT updated]")
    else:
        save_state(args.slug, current)


# Boards that MUST show a scan within every 3-day cycle = Tier 1 of
# job_board_scan_list.md (restructured 2026-08-14: tiers are scan priority, not
# location posture). A missing/stale entry here means the sweep silently skipped
# it — most of these are browser-only boards with no JSON API, which is exactly
# why they got under-scanned historically. Extend as boards are seeded.
CORE_BOARDS = [
    # home-metro offices (browser-scan, highest miss risk)
    "amazon", "microsoft", "starbucks", "expedia", "ebay", "tmobile",
    "chewy", "alaskaair", "robinhood", "uber", "meta", "google",
    # API-scannable Tier 1
    "doordashusa", "stripe", "visa", "instacart", "affirm", "reddit",
    "whatnot", "block", "salesforce",
]
STALE_DAYS = 3

def cmd_status(args):
    t = datetime.date.today()
    seen = {}
    if os.path.isdir(STATE_DIR):
        for fn in sorted(f for f in os.listdir(STATE_DIR) if f.endswith(".json")):
            with open(os.path.join(STATE_DIR, fn), encoding="utf-8") as f:
                seen[fn[:-5]] = json.load(f)
    if not seen:
        print("no scans recorded yet.")
    else:
        print(f"{'board':28} {'last scan':12} {'jobs':>5}  {'age':>4}")
        print("-" * 55)
        for slug, d in seen.items():
            try:
                age = (t - datetime.date.fromisoformat(d.get("last_scan",""))).days
                agestr = f"{age}d" + ("  << STALE" if age > STALE_DAYS else "")
            except ValueError:
                agestr = "?"
            print(f"{slug:28} {d.get('last_scan',''):12} {d.get('count',0):>5}  {agestr}")
    missing = [b for b in CORE_BOARDS if b not in seen]
    stale = [b for b in CORE_BOARDS if b in seen and
             (not seen[b].get("last_scan") or
              (t - datetime.date.fromisoformat(seen[b]["last_scan"])).days > STALE_DAYS)]
    if missing or stale:
        print(f"\nWARNING - core (Tier 1) boards not covered this cycle:")
        if missing: print(f"  never scanned: {', '.join(missing)}")
        if stale:   print(f"  stale (> {STALE_DAYS}d): {', '.join(stale)}")
        print("  Scan these FIRST next run (job_board_scan_list.md: Tier 1 runs every sweep).")


def cmd_show(args):
    d = load_state(args.slug)
    print(f"[{args.slug}] last scan {d.get('last_scan') or 'never'}  "
          f"count {d.get('count',0)}")
    for i, t in d.get("ids", {}).items():
        print(f"  {i}\t{t}")


def main():
    ap = argparse.ArgumentParser(description="Delta scanner for job-board sweeps.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("diff", help="report NEW postings vs last scan, update state")
    d.add_argument("slug")
    d.add_argument("--json", help="path to saved board API JSON")
    d.add_argument("--ids", help="comma-separated ids or id:title pairs")
    d.add_argument("--dry", action="store_true", help="preview only, don't save state")
    d.set_defaults(func=cmd_diff)

    s = sub.add_parser("status", help="last-scan date + count per board")
    s.set_defaults(func=cmd_status)

    sh = sub.add_parser("show", help="dump stored ids for a board")
    sh.add_argument("slug")
    sh.set_defaults(func=cmd_show)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
