#!/usr/bin/env python3
"""Generate the outreach plan for an application.

    python3 engine/lib/build_outreach.py --plan plan.json -o "<folder>/outreach plan.md"

The plan JSON supplies what only research can: who the hiring manager is, who
the recruiter is, and which warm paths exist. This fills in the rest — the
email-pattern guesses, the channel decision, the sequence, and three
ready-to-send drafts in the candidate's voice from profile/identity.json.

Why this is a deliverable at all: cold applications through an ATS convert
poorly enough that the follow-up, not the submission, is where the leverage
is. A plan that exists as a file gets worked; one that exists as an intention
does not.

Email patterns are GUESSES and are labelled as such with a confidence level.
Never send to a guess you would not defend — verify first.
"""

import argparse
import datetime
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths  # noqa: E402

# Ordered by how common each is at the relevant company size. Founder-led and
# small companies skew hard to first@; large enterprises to first.last@.
PATTERNS = [
    ("first.last", "{first}.{last}@{domain}"),
    ("flast", "{f}{last}@{domain}"),
    ("first", "{first}@{domain}"),
    ("firstl", "{first}{l}@{domain}"),
    ("lastf", "{last}{f}@{domain}"),
]

SIZE_PREFERENCE = {
    "startup": ["first", "first.last", "flast"],
    "small": ["first", "first.last", "flast"],
    "midsize": ["first.last", "flast", "first"],
    "large": ["first.last", "flast", "firstl"],
    "enterprise": ["first.last", "flast", "firstl"],
}


def slugify_name(full):
    parts = [re.sub(r"[^a-z]", "", p.lower()) for p in full.split() if p.strip()]
    parts = [p for p in parts if p]
    if not parts:
        return "", "", ""
    first, last = parts[0], parts[-1]
    return first, last, (first[:1], last[:1])


def guess_emails(full_name, domain, size="midsize"):
    """[(pattern_name, address)] ordered best-guess first for this company size."""
    first, last, (f, l) = slugify_name(full_name)
    if not first or not domain:
        return []
    order = SIZE_PREFERENCE.get(size, SIZE_PREFERENCE["midsize"])
    ranked = sorted(PATTERNS, key=lambda p: order.index(p[0]) if p[0] in order else 99)
    return [(name, tpl.format(first=first, last=last, f=f, l=l, domain=domain))
            for name, tpl in ranked]


def confidence(size, verified):
    """How much to trust a guessed address.

    Counter-intuitively, LARGE companies are the predictable ones: first.last@
    is near-universal at enterprise scale, while small and founder-led shops
    vary between first@, initials, and whatever the founder set up in 2015. So
    confidence rises with size, not the other way round.
    """
    if verified:
        return "HIGH"
    if size in ("large", "enterprise"):
        return "MEDIUM"
    return "LOW"


CHANNEL_RATIONALE = {
    "startup": ("email", "small enough that the hiring manager's inbox is reachable and read"),
    "small": ("email", "small enough that the hiring manager's inbox is reachable and read"),
    "midsize": ("email", "mid-sized, so a direct note still reaches the hiring manager, "
                         "though the address needs verifying"),
    "large": ("LinkedIn", "large enough that cold email is filtered aggressively; LinkedIn lands "
                          "better and email is the backup"),
    "enterprise": ("LinkedIn", "an enterprise, so cold email rarely survives filtering; LinkedIn "
                               "leads and the recruiter is the fallback"),
}


def render(plan, identity):
    today = plan.get("date") or datetime.date.today().isoformat()
    company = plan["company"]
    role = plan["role"]
    domain = plan.get("email_domain", "")
    size = plan.get("company_size", "midsize")
    first_name = identity["name"]["first"]
    # voice.signature is a human-readable DESCRIPTION ("name + linkedin.com/..."),
    # not a template. Render the real thing from the contact block.
    sig = (identity.get("contact", {}).get("linkedin_short")
           or identity.get("contact", {}).get("linkedin")
           or "")
    anchor = identity.get("voice", {}).get("anchor", "your most relevant credential")

    # Channel rule: reachable inbox -> email leads; filtered enterprise -> LinkedIn.
    primary, why = CHANNEL_RATIONALE.get(size, CHANNEL_RATIONALE["midsize"])

    L = []
    a = L.append
    a(f"# Outreach Plan — {company}, {role}")
    a("")
    a(f"_Created: {today} | Applied: {plan.get('applied_date', today)} | "
      f"Fit: {plan.get('fit', 'Strong')} | JD: {plan.get('jd_url', 'n/a')}_")
    a("")
    a("## Context & framing")
    a("")
    a(plan.get("context", "{{Location, remote policy, posted comp band.}}"))
    a("")
    a(f"**Strength to lead with:** {plan.get('strength', anchor)}")
    a("")
    a(f"**The honest gap:** {plan.get('gap', '{{Name it plainly — the same gap the cover letter names.}}')}")
    a("")
    a(f"**Primary channel: {primary}.** {company} is {why}.")
    a("")
    a("## Targets")
    a("")

    for kind, label in (("hiring_manager", "Primary hiring manager"),
                        ("alternate", "Alternate / skip-level"),
                        ("recruiter", "Recruiter (backup channel)")):
        people = plan.get(kind) or []
        if isinstance(people, dict):
            people = [people]
        if not people:
            continue
        a(f"### {label}")
        for p in people:
            a(f"- **{p['name']}** — {p.get('title', '')}, {company}")
            if p.get("background"):
                a(f"  - {p['background']}")
            if p.get("linkedin"):
                deg = f" — {p['degree']}" if p.get("degree") else ""
                mut = f", mutuals: {p['mutuals']}" if p.get("mutuals") else ""
                a(f"  - LinkedIn: {p['linkedin']}{deg}{mut}")
            guesses = guess_emails(p["name"], p.get("email_domain", domain), size)
            if p.get("email"):
                a(f"  - Email (**verified**): {p['email']}")
            elif guesses:
                best = guesses[0]
                alts = ", ".join(f"`{g[1]}`" for g in guesses[1:3])
                a(f"  - Email guess (pattern `{best[0]}`, confidence "
                  f"{confidence(size, False)}): **{best[1]}** | alt {alts}")
                a("  - Verify before sending. A guess that bounces is a wasted first impression.")
        a("")

    warm = plan.get("warm_paths") or []
    if warm:
        a("### Warm internal paths — ask for a referral BEFORE cold-emailing")
        for w in warm:
            a(f"- **{w['name']}** — {w.get('title', '')} @ {company}"
              + (f" — {w['linkedin']}" if w.get("linkedin") else "")
              + (f" ({w['degree']}" + (f"; mutual {w['mutuals']}" if w.get("mutuals") else "") + ")"
                 if w.get("degree") else ""))
        a("")
        a("A referral outperforms every cold channel. A day's delay to ask is usually worth it.")
        a("")

    a("## Sequence")
    a("")
    a(f"1. **Applied via {plan.get('ats', 'the careers page')}** ({plan.get('applied_date', today)}).")
    a("2. **Verify the hiring manager's identity** — name collisions are routine, and a personal "
      "note to the wrong person is worse than no note.")
    a(f"3. **Same-day {primary}** to the hiring manager (draft below).")
    a(f"4. **After 4-5 days of silence**, follow up on the other channel — never both at once. "
      "The same text on two channels reads as a mail merge, which is what it is trying not to be.")
    a("5. **Log it**: `python3 engine/lib/registry.py outreach \"" + company +
      "\" --note \"…\" --next \"…\" --due YYYY-MM-DD`")
    a("")

    hm = (plan.get("hiring_manager") or [{}])
    hm = hm[0] if isinstance(hm, list) else hm
    hm_first = (hm.get("name", "there").split() or ["there"])[0]
    about = plan.get("about_me", f"{{{{3-4 lines anchored on {anchor} plus the most role-relevant credential}}}}")
    ask = plan.get("ask", "Would you be open to a short conversation about whether that maps to what you need?")

    a("## Drafts")
    a("")
    a("### 1. Email")
    a("")
    a("```")
    a(f"To: {(hm.get('email') or (guess_emails(hm.get('name',''), hm.get('email_domain', domain), size) or [('','')])[0][1])}")
    a(f"Subject: {role} ({identity['name']['full']})")
    a("")
    a(f"Hi {hm_first},")
    a("")
    a(f"I came across the {role} role and applied through your careers page.")
    a("")
    a(about)
    a("")
    a(ask)
    a("")
    a(f"{first_name}")
    a(sig)
    a("```")
    a("")
    a("No CV attached — it is already in their ATS, and attachments from unknown senders hurt "
      "deliverability.")
    a("")
    a("### 2. LinkedIn message (if email bounces or goes unanswered)")
    a("")
    a("```")
    a(f"Hi {hm_first}, I applied for the {role} role at {company} and wanted to introduce myself directly.")
    a("")
    a(about)
    a("")
    a(ask)
    a("```")
    a("")
    a("### 3. LinkedIn connection request (under 300 characters)")
    a("")
    short = (f"Hi {hm_first}, I applied for the {role} role at {company}. "
             f"{plan.get('short_hook', anchor)}. Would welcome a short chat.")
    if len(short) > 300:
        short = short[:296].rstrip() + "..."
    a("```")
    a(short)
    a("```")
    a("")
    a(f"({len(short)} characters.)")
    a("")
    a("---")
    a("")
    a("**One ask, honestly stated.** Never imply curiosity the candidate does not have, never hedge "
      "with \"if there's a good fit,\" and never pre-emptively offer to be redirected to \"the right "
      "person\" - that hands the reader an easy exit.")

    text = "\n".join(L) + "\n"
    # Guaranteed, not hand-maintained: this project bans em and en dashes in
    # deliverables, and the drafts below get pasted straight into email and
    # LinkedIn. One pass here is safer than remembering it in twenty f-strings.
    return text.replace("\u2014", "-").replace("\u2013", "-")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--plan", required=True, help="research JSON: contacts, context, gap")
    ap.add_argument("--identity", default=os.path.join(paths.PROFILE_DIR, "identity.json"))
    args = ap.parse_args()

    for label, path in (("plan", args.plan), ("identity", args.identity)):
        if not os.path.exists(path):
            sys.exit(f"{label} not found: {path}")
    plan = json.load(open(args.plan))
    for required in ("company", "role"):
        if required not in plan:
            sys.exit(f"--plan is missing required key: {required}")

    text = render(plan, json.load(open(args.identity)))
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(text)
    n_contacts = sum(len(plan.get(k) or []) if isinstance(plan.get(k), list)
                     else (1 if plan.get(k) else 0)
                     for k in ("hiring_manager", "alternate", "recruiter", "warm_paths"))
    print(f"wrote {args.out}: {n_contacts} contact(s), 3 drafts, "
          f"{len(text.splitlines())} lines")
    if not plan.get("email_domain"):
        print("  note: no email_domain given, so no address guesses were made")


if __name__ == "__main__":
    main()
