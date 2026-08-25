#!/usr/bin/env python3
"""
Application Registry - single source of truth for every JD assessed in this project.

Canonical data file: _registry/processed_jobs.csv
Schema (columns):
  job_id, company, role_title, location, url, source,
  first_seen_date, fit_verdict, cv_generated, applied, applied_date, jd_folder, notes

Commands:
  python3 engine/lib/registry.py sync                  Reconcile CSV against JD folders on disk (idempotent).
  python3 engine/lib/registry.py check "<query>"       Dedup check. Query = url, job_id, or "company role".
  python3 engine/lib/registry.py add --company C --role R [--url U --location L --source S --fit F --folder D --id I]
                                           Add a new application; refuses (flags) if already present.
  python3 engine/lib/registry.py applied "<query>" [--date YYYY-MM-DD]
                                           Mark a matching application as applied.
  python3 engine/lib/registry.py cvdone "<query>" [--folder D]
                                           Mark cv_generated=TRUE (and set folder) for a match.
  python3 engine/lib/registry.py list [all|applied|cv|pending|skipped]
  python3 engine/lib/registry.py stats

Matching (dedup) precedence: exact job_id, then normalized url, then exact jd_folder,
then (company lowercased AND first 18 chars of role lowercased).
"""
import csv, os, sys, re, argparse, datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths  # noqa: E402

# Code lives in engine/lib/; state lives with the user. See paths.py.
PROJECT = paths.PROJECT_ROOT
CSV_PATH = paths.CSV_PATH
COLS = ["job_id","company","role_title","location","url","source",
        "first_seen_date","fit_verdict","cv_generated","applied","applied_date",
        "status","status_date","outreach_status","next_action","next_action_date",
        "jd_folder","notes"]
# status lifecycle: "" (open/active) | applied | rejected (chose not to apply) | cancelled (posting gone)
#                   | expired (Partial auto-expired, no build decision) | free-form interview stages
#                   (e.g. recruiter_screen, onsite, offer, closed) set via `setstatus`.
# outreach_status: free-form log of hiring-manager/recruiter outreach ("emailed HM 2026-08-04; LI 2026-08-09").
# next_action / next_action_date: the single next follow-up step and when it is due (drives `followups`).

def norm_url(u):
    if not u: return ""
    u = u.strip().lower().rstrip("/")
    u = re.sub(r"^https?://(www\.)?", "", u)
    u = u.split("?")[0].split("#")[0]
    return u

def role_key(r):
    return re.sub(r"[^a-z0-9]","", (r or "").lower())[:18]

def today():
    return datetime.date.today().isoformat()

def load():
    rows = []
    if os.path.exists(CSV_PATH):
        with open(CSV_PATH, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                # normalize legacy rows to full schema
                rows.append({c: (r.get(c,"") or "") for c in COLS})
    return rows

def save(rows):
    # On a fresh install the state directory does not exist yet, and the first
    # write is an `add` rather than a `sync`. Create it here rather than making
    # every caller remember to.
    paths.ensure_state_dirs()
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c,"") for c in COLS})

def match(rows, query, company=None, role=None, url=None, job_id=None, folder=None):
    """Return the first matching row dict, or None."""
    q = (query or "").strip()
    qn = norm_url(q)
    for r in rows:
        if job_id and r["job_id"] and r["job_id"] == job_id: return r
        if url and r["url"] and norm_url(r["url"]) == norm_url(url): return r
        if folder and r["jd_folder"] and r["jd_folder"] == folder: return r
        if q:
            if r["job_id"] and r["job_id"] == q: return r
            if r["url"] and norm_url(r["url"]) == qn and qn: return r
            if r["jd_folder"] and r["jd_folder"].lower() == q.lower(): return r
    # fuzzy company+role
    if company and role:
        for r in rows:
            if r["company"].lower()==company.lower() and role_key(r["role_title"])==role_key(role):
                return r
    if q and not (company or role):
        # try "company role..." free text (compare against UNtruncated key — role_key's
        # 18-char cap dropped the role when the company name was long, e.g. "LawnStarter Director...")
        qk = re.sub(r"[^a-z0-9]","", q.lower())
        for r in rows:
            if r["company"] and r["company"].lower() in q.lower() and role_key(r["role_title"])[:8] and role_key(r["role_title"])[:8] in qk:
                return r
        # company-only fallback: unambiguous if exactly one non-terminal row for that company
        cand = [r for r in rows if r["company"] and r["company"].lower().rstrip("!") == q.lower().rstrip("!")]
        if len(cand) == 1: return cand[0]
        live = [r for r in cand if r.get("status","") not in ("rejected","cancelled","expired","closed")]
        if len(live) == 1: return live[0]
    return None

def match_candidates(rows, query):
    """Every row a company-only query could plausibly mean."""
    q = (query or "").strip().lower().rstrip("!")
    if not q:
        return []
    return [r for r in rows
            if r["company"] and r["company"].lower().rstrip("!") == q]


def resolve_for_write(rows, query, action="modify"):
    """Match a row for a MUTATING command, refusing to guess between candidates.

    `match()` has a convenience fallback: when several rows share a company it
    picks the single non-terminal one. That is fine for a dedup CHECK and
    actively dangerous for a write - it silently mutated the wrong row of two
    same-company applications, appending a rejection to a role that had never
    been applied to. A read that guesses wrong costs a second look; a write
    that guesses wrong corrupts the record it was meant to correct.

    Exact matches (job_id, url, folder) still win. A company-only query that
    could mean more than one row stops and asks.
    """
    exact = match(rows, query, url=query)
    cands = match_candidates(rows, query)
    if len(cands) > 1:
        qn = norm_url(query)
        q = (query or "").lower()
        decisive = (any(r["job_id"] and r["job_id"] == query for r in cands)
                    or (qn and any(r["url"] and norm_url(r["url"]) == qn for r in cands))
                    or any(r["jd_folder"] and r["jd_folder"].lower() == q for r in cands))
        if not decisive:
            print(f'AMBIGUOUS: {len(cands)} rows match "{query}". '
                  f"Refusing to {action} one of them by guessing.\n")
            for r in cands:
                print(f"  - {r['role_title']}")
                print(f"      status={r['status'] or '(open)'}  applied={r['applied']}  "
                      f"id={r['job_id'] or '(none)'}")
                if r["jd_folder"]:
                    print(f"      folder={r['jd_folder']}")
            print("\nRe-run with the job_id, the full posting URL, or the exact folder name.")
            # Exit here rather than returning None: callers print "No match found",
            # which is the opposite of the actual problem and would send someone
            # looking for a missing row instead of choosing between two.
            sys.exit(2)
    return exact


def parse_folder(name):
    m = re.match(r"^(\d{8})\s+(.*)$", name)
    date = ""; rest = name
    if m:
        d = m.group(1); date = f"{d[:4]}-{d[4:6]}-{d[6:8]}"; rest = m.group(2)
    if " - " in rest:
        company, role = rest.split(" - ", 1)
    else:
        company, role = rest, ""
    return date, company.strip(), role.strip()

def folder_has_cv(folder):
    p = os.path.join(PROJECT, folder)
    if not os.path.isdir(p): return False
    return any("CV" in f and f.lower().endswith((".pdf",".docx")) for f in os.listdir(p))

def cmd_sync(args):
    rows = load()
    added, linked, cvflag = 0, 0, 0
    folders = sorted(d for d in os.listdir(PROJECT)
                     if re.match(r"^\d{8}\s", d) and os.path.isdir(os.path.join(PROJECT, d)))
    for folder in folders:
        date, company, role = parse_folder(folder)
        has_cv = folder_has_cv(folder)
        r = match(rows, folder, company=company, role=role, folder=folder)
        if r is None:
            rows.append({
                "job_id": "", "company": company, "role_title": role, "location": "",
                "url": "", "source": "folder-sync", "first_seen_date": date,
                "fit_verdict": "", "cv_generated": "TRUE" if has_cv else "FALSE",
                "applied": "FALSE", "applied_date": "", "jd_folder": folder, "notes": ""})
            added += 1
        else:
            if not r["jd_folder"]:
                r["jd_folder"] = folder; linked += 1
            newcv = "TRUE" if has_cv else (r["cv_generated"] or "FALSE")
            if r["cv_generated"] != newcv and has_cv:
                r["cv_generated"] = "TRUE"; cvflag += 1
            if not r["first_seen_date"]: r["first_seen_date"] = date
            if not r["company"]: r["company"] = company
            if not r["role_title"]: r["role_title"] = role
            if not r["applied"]: r["applied"] = "FALSE"
    save(rows)
    print(f"sync complete: {len(folders)} folders scanned, {added} added, {linked} linked, {cvflag} cv-flags set. Total rows: {len(rows)}")

def cmd_check(args):
    rows = load()
    r = match(rows, args.query, url=args.query)
    if r:
        st = r.get("status") or "open"
        print("DUPLICATE - already in registry:")
        print(f"  {r['company']} | {r['role_title']}")
        print(f"  first seen {r['first_seen_date']} | fit {r['fit_verdict'] or 'n/a'} | cv {r['cv_generated']} | status {st.upper()} {r.get('status_date','')}")
        print(f"  folder: {r['jd_folder'] or '(none)'}")
        if st in ("rejected","cancelled"):
            print(f"  >>> Do NOT reopen: this role was {st}. {r['notes']}")
        sys.exit(0)
    print("NEW - not found in registry. Safe to assess/build.")
    sys.exit(1)

def cmd_add(args):
    rows = load()
    r = match(rows, args.url or "", company=args.company, role=args.role, url=args.url, job_id=args.id)
    if r:
        print("ALREADY EXISTS - not adding. Existing entry:")
        print(f"  {r['company']} | {r['role_title']} | cv {r['cv_generated']} | applied {r['applied']}")
        return
    rows.append({
        "job_id": args.id or "", "company": args.company, "role_title": args.role,
        "location": args.location or "", "url": args.url or "", "source": args.source or "manual",
        "first_seen_date": args.date or today(), "fit_verdict": args.fit or "",
        "cv_generated": "TRUE" if args.folder else "FALSE", "applied": "FALSE",
        "applied_date": "", "jd_folder": args.folder or "", "notes": args.notes or ""})
    save(rows)
    print(f"ADDED: {args.company} | {args.role}")

def cmd_applied(args):
    rows = load()
    r = resolve_for_write(rows, args.query, "mark applied")
    if not r:
        print("No match found. Use exact url, job_id, folder, or 'Company Role'."); sys.exit(1)
    r["applied"] = "TRUE"; r["applied_date"] = args.date or today()
    r["status"] = "applied"; r["status_date"] = r["applied_date"]
    # default follow-up: outreach scout due 2 days after applying, unless one is already set
    if not r.get("next_action"):
        due = (datetime.date.fromisoformat(r["applied_date"]) + datetime.timedelta(days=2)).isoformat()
        r["next_action"] = "outreach scout: identify HM + recruiter, draft note"
        r["next_action_date"] = due
    save(rows)
    print(f"MARKED APPLIED: {r['company']} | {r['role_title']} on {r['applied_date']}")
    if r.get("next_action"): print(f"  next action: {r['next_action']} (due {r['next_action_date']})")

def _set_status(args, status, label, default_note):
    rows = load()
    r = resolve_for_write(rows, args.query, "close")
    if not r:
        print("No match found. Use exact url, job_id, folder, or 'Company Role'."); sys.exit(1)
    r["status"] = status; r["status_date"] = args.date or today()
    reason = getattr(args, "reason", None) or default_note
    if reason:
        r["notes"] = (r["notes"] + " | " if r["notes"] else "") + f"{label} {r['status_date']}: {reason}"
    save(rows)
    print(f"MARKED {label.upper()}: {r['company']} | {r['role_title']} ({r['status_date']})"
          + (f" - {reason}" if reason else ""))

def cmd_reject(args):
    # user decided NOT to apply to this role
    _set_status(args, "rejected", "rejected", "chose not to apply")

def cmd_cancel(args):
    # posting no longer available / pulled
    _set_status(args, "cancelled", "cancelled", "posting no longer available")

def cmd_reopen(args):
    rows = load()
    r = resolve_for_write(rows, args.query, "reopen")
    if not r:
        print("No match found."); sys.exit(1)
    r["status"] = ""; r["status_date"] = ""
    if r.get("applied") == "TRUE":
        r["applied"] = "FALSE"; r["applied_date"] = ""
    save(rows)
    print(f"REOPENED (status cleared): {r['company']} | {r['role_title']}")

def cmd_cvdone(args):
    rows = load()
    r = resolve_for_write(rows, args.query, "update")
    if not r:
        print("No match found."); sys.exit(1)
    r["cv_generated"] = "TRUE"
    if args.folder: r["jd_folder"] = args.folder
    save(rows)
    print(f"CV marked generated: {r['company']} | {r['role_title']}")

def cmd_list(args):
    rows = load()
    f = (args.filter or "all").lower()
    def keep(r):
        st = r.get("status","")
        if f=="applied": return st=="applied" or r["applied"]=="TRUE"
        if f=="rejected": return st=="rejected"
        if f=="cancelled": return st=="cancelled"
        if f=="cv": return r["cv_generated"]=="TRUE"
        if f=="pending": return r["cv_generated"]=="TRUE" and st not in ("applied","rejected","cancelled") and r["applied"]!="TRUE"
        if f=="active": return st not in ("applied","rejected","cancelled")
        if f=="skipped": return r["cv_generated"]!="TRUE"
        return True
    sel = [r for r in rows if keep(r)]
    sel.sort(key=lambda r: r["first_seen_date"], reverse=True)
    for r in sel:
        st = r.get("status","")
        tag = st.upper() if st else ("CV" if r["cv_generated"]=="TRUE" else "--")
        print(f"[{tag:9}] {r['first_seen_date']} {r['company']} | {r['role_title']}"
              + (f"  ({st} {r.get('status_date','')})" if st else ""))
    print(f"\n{len(sel)} rows ({f}).")

TERMINAL = ("rejected","cancelled","expired","closed")

def cmd_outreach(args):
    """Append an outreach event to a row's outreach_status log."""
    rows = load()
    r = resolve_for_write(rows, args.query, "log outreach on")
    if not r:
        print("No match found."); sys.exit(1)
    stamp = f"{args.note} ({args.date or today()})"
    r["outreach_status"] = (r["outreach_status"] + "; " if r["outreach_status"] else "") + stamp
    if args.next:
        r["next_action"] = args.next
        r["next_action_date"] = args.due or (datetime.date.today()+datetime.timedelta(days=5)).isoformat()
    elif args.clear_next:
        r["next_action"] = ""; r["next_action_date"] = ""
    save(rows)
    print(f"OUTREACH LOGGED: {r['company']} | {stamp}"
          + (f"\n  next action: {r['next_action']} (due {r['next_action_date']})" if r.get("next_action") else ""))

def cmd_nextaction(args):
    rows = load()
    r = resolve_for_write(rows, args.query, "set an action on")
    if not r:
        print("No match found."); sys.exit(1)
    r["next_action"] = args.action or ""
    r["next_action_date"] = args.date or (datetime.date.today()+datetime.timedelta(days=5)).isoformat() if args.action else ""
    save(rows)
    print(f"NEXT ACTION: {r['company']} | {r['next_action'] or '(cleared)'} {r['next_action_date']}")

def cmd_setstatus(args):
    """Free-form pipeline stage: recruiter_screen, onsite, offer, closed, ..."""
    rows = load()
    r = resolve_for_write(rows, args.query, "set the status of")
    if not r:
        print("No match found."); sys.exit(1)
    r["status"] = args.to; r["status_date"] = args.date or today()
    if args.note:
        r["notes"] = (r["notes"] + " | " if r["notes"] else "") + f"{args.to} {r['status_date']}: {args.note}"
    save(rows)
    print(f"STATUS -> {args.to}: {r['company']} | {r['role_title']} ({r['status_date']})")

def cmd_followups(args):
    """The post-application worklist: due next_actions + stale applied roles with no outreach/response."""
    rows = load(); t = datetime.date.today(); stale_days = args.days
    due, stale = [], []
    for r in rows:
        st = r.get("status","")
        if st in TERMINAL: continue
        if r.get("next_action") and r.get("next_action_date"):
            try: d = datetime.date.fromisoformat(r["next_action_date"])
            except ValueError: d = t
            if d <= t: due.append((d, r))
        elif st == "applied" and r.get("applied_date"):
            try: age = (t - datetime.date.fromisoformat(r["applied_date"])).days
            except ValueError: continue
            if age >= stale_days and not r.get("outreach_status"):
                stale.append((age, r))
    due.sort(key=lambda x: x[0]); stale.sort(key=lambda x: -x[0])
    if due:
        print(f"DUE NEXT ACTIONS ({len(due)}):")
        for d, r in due:
            print(f"  [{d}] {r['company']} | {r['role_title']}\n        -> {r['next_action']}"
                  + (f"  (outreach so far: {r['outreach_status']})" if r['outreach_status'] else ""))
    if stale:
        print(f"\nSTALE APPLICATIONS, NO OUTREACH YET ({len(stale)}, applied >= {stale_days}d ago, no response):")
        for age, r in stale:
            print(f"  [{age:3}d] {r['applied_date']} {r['company']} | {r['role_title']}")
    if not due and not stale:
        print("Nothing due. Post-application pipeline is current.")

def cmd_expire(args):
    """Auto-expire stale Partials: fit=Partial, never applied, no status, older than N days."""
    rows = load(); t = datetime.date.today(); n = 0
    for r in rows:
        if r["fit_verdict"] != "Partial": continue
        if r["applied"] == "TRUE" or r.get("status",""): continue
        try: age = (t - datetime.date.fromisoformat(r["first_seen_date"])).days
        except ValueError: continue
        if age > args.days:
            n += 1
            print(f"  [{age:3}d] {r['first_seen_date']} {r['company']} | {r['role_title']}")
            if args.apply:
                r["status"] = "expired"; r["status_date"] = today()
                r["notes"] = (r["notes"] + " | " if r["notes"] else "") + \
                    f"auto-expired {today()}: Partial with no build decision after {args.days}d (reopen only on explicit request)"
    if args.apply and n:
        save(rows); print(f"\nEXPIRED {n} stale Partials.")
    elif n:
        print(f"\nDRY RUN: {n} Partials would expire. Re-run with --apply to commit.")
    else:
        print("No stale Partials.")

def cmd_stats(args):
    rows = load()
    total = len(rows)
    cv = sum(1 for r in rows if r["cv_generated"]=="TRUE")
    applied = sum(1 for r in rows if (r.get("status")=="applied" or r["applied"]=="TRUE"))
    rejected = sum(1 for r in rows if r.get("status")=="rejected")
    cancelled = sum(1 for r in rows if r.get("status")=="cancelled")
    expired = sum(1 for r in rows if r.get("status")=="expired")
    pending = sum(1 for r in rows if r["cv_generated"]=="TRUE" and r.get("status","") not in ("applied",)+TERMINAL and r["applied"]!="TRUE")
    outreach = sum(1 for r in rows if r.get("outreach_status"))
    instage = [r for r in rows if r.get("status","") not in ("","applied")+TERMINAL]
    print(f"Total assessed: {total}")
    print(f"CVs generated:  {cv}")
    print(f"Applied:        {applied}")
    print(f"  with outreach done: {outreach}")
    print(f"  in interview stage: {len(instage)}" + (" -> " + "; ".join(f"{r['company']} ({r['status']})" for r in instage) if instage else ""))
    print(f"Rejected (chose not to apply): {rejected}")
    print(f"Cancelled (posting gone):      {cancelled}")
    print(f"Expired (stale Partials):      {expired}")
    print(f"CV built, still open (not applied/terminal): {pending}")

def main():
    ap = argparse.ArgumentParser(description="Application registry")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("sync")
    c = sub.add_parser("check"); c.add_argument("query")
    a = sub.add_parser("add")
    a.add_argument("--company", required=True); a.add_argument("--role", required=True)
    a.add_argument("--url"); a.add_argument("--location"); a.add_argument("--source")
    a.add_argument("--fit"); a.add_argument("--folder"); a.add_argument("--id")
    a.add_argument("--date"); a.add_argument("--notes")
    p = sub.add_parser("applied"); p.add_argument("query"); p.add_argument("--date")
    rj = sub.add_parser("reject"); rj.add_argument("query"); rj.add_argument("--reason"); rj.add_argument("--date")
    cx = sub.add_parser("cancel"); cx.add_argument("query"); cx.add_argument("--reason"); cx.add_argument("--date")
    ro = sub.add_parser("reopen"); ro.add_argument("query")
    v = sub.add_parser("cvdone"); v.add_argument("query"); v.add_argument("--folder")
    l = sub.add_parser("list"); l.add_argument("filter", nargs="?", default="all")
    sub.add_parser("stats")
    o = sub.add_parser("outreach"); o.add_argument("query"); o.add_argument("--note", required=True)
    o.add_argument("--date"); o.add_argument("--next"); o.add_argument("--due"); o.add_argument("--clear-next", action="store_true")
    na = sub.add_parser("nextaction"); na.add_argument("query"); na.add_argument("--action"); na.add_argument("--date")
    ss = sub.add_parser("setstatus"); ss.add_argument("query"); ss.add_argument("--to", required=True)
    ss.add_argument("--note"); ss.add_argument("--date")
    fu = sub.add_parser("followups"); fu.add_argument("--days", type=int, default=7)
    ex = sub.add_parser("expire"); ex.add_argument("--days", type=int, default=7); ex.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    {"sync":cmd_sync,"check":cmd_check,"add":cmd_add,"applied":cmd_applied,
     "reject":cmd_reject,"cancel":cmd_cancel,"reopen":cmd_reopen,
     "cvdone":cmd_cvdone,"list":cmd_list,"stats":cmd_stats,
     "outreach":cmd_outreach,"nextaction":cmd_nextaction,"setstatus":cmd_setstatus,
     "followups":cmd_followups,"expire":cmd_expire}[args.cmd](args)

if __name__ == "__main__":
    main()
