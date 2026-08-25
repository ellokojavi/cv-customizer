#!/usr/bin/env python3
"""Tests for the outcome classifier.

    python3 engine/lib/outcomes_tests.py

The classifier is load-bearing: a misclassification does not raise, it just
silently moves a row from one side of a conversion rate to the other. The case
that matters most is the overloaded pair - `rejected` and `closed` were both
used for "we passed on them" AND "they passed on us", and confusing those
inverts the meaning of the headline number.

Cases are person-agnostic; the fixtures below are paraphrases of real note
shapes, not real rows.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import outcomes as OC  # noqa: E402

# (status, notes, expected_outcome, why)
CASES = [
    # --- the overloaded pair: who ended it? --------------------------------
    ("rejected", "off-domain. graph database tooling, no commerce hook",
     OC.WE_DECLINED, "we passed at triage"),
    ("rejected", "location gap, onsite in another metro",
     OC.WE_DECLINED, "we passed on location"),
    ("rejected", "failed the cases/interview stage; did not advance",
     OC.EMPLOYER_REJECTED, "they rejected us AFTER an interview"),
    ("closed", "rejection email received",
     OC.EMPLOYER_REJECTED, "they rejected us"),
    ("closed", "never replied; closing at 60 days",
     OC.GHOSTED, "applied, silence"),
    ("closed", "posting removed from the board, no response",
     OC.POSTING_PULLED, "role disappeared"),
    ("rejected", "two-level title stretch, do not surface again",
     OC.WE_DECLINED, "we passed on level"),

    # --- unambiguous statuses ---------------------------------------------
    ("recruiter_screen", "", OC.ADVANCED, "reached a human"),
    ("onsite", "", OC.ADVANCED, "reached a human"),
    ("offer", "", OC.ADVANCED, "reached a human"),
    ("applied", "", OC.APPLIED_PENDING, "submitted, undecided"),
    ("expired", "", OC.WE_DECLINED, "never decided, so never applied"),
    ("", "assessed, partial fit", OC.WE_DECLINED, "no status: never progressed"),

    # "off-core" is the same idea as "off-domain" and was missed by the pattern.
    ("rejected", "off-core B2B agreements domain, not defensible",
     OC.WE_DECLINED, "we passed on domain, phrased differently"),

    # --- genuinely ambiguous must stay UNKNOWN ----------------------------
    ("closed", "partial fit; strong consumer fintech growth",
     OC.UNKNOWN, "describes the FIT, says nothing about what happened"),
    ("rejected", "", OC.UNKNOWN, "no note at all, overloaded status"),
]

SOURCE_CASES = [
    ("daily-search", "board scan"),
    ("daily-search (Tier B, employer careers site)", "board scan"),
    ("greenhouse", "board scan"),
    ("LinkedIn", "linkedin"),
    ("linkedin-top-applicant", "linkedin"),
    ("LinkedIn 4410846682", "linkedin"),
    ("user-referral", "referral/inbound"),
    ("inbound", "referral/inbound"),
    ("email-board-lensa", "inbox digest"),
    ("LinkedIn job alert digest", "inbox digest"),
    ("user-provided (live posting)", "user-supplied"),
    ("folder-sync", "folder sync"),
    ("", None),
]


def main():
    failures = []

    print("outcome classification")
    for status, notes, expected, why in CASES:
        got, conf = OC.classify({"status": status, "notes": notes})
        ok = got == expected
        if not ok:
            failures.append(f"status={status!r} notes={notes[:40]!r}: "
                            f"expected {expected}, got {got}")
        print(f"  {'ok  ' if ok else 'BAD '} {status or '(none)':<17} -> "
              f"{got:<18} {why}")

    print("\nsource normalisation")
    for raw, expected in SOURCE_CASES:
        got = OC.normalize_source(raw)
        ok = got == expected
        if not ok:
            failures.append(f"source {raw!r}: expected {expected}, got {got}")
        print(f"  {'ok  ' if ok else 'BAD '} {raw or '(empty)':<36} -> {got}")

    # You cannot be rejected by an employer you never applied to, and you cannot
    # apply without a CV. So an ambiguous status plus no CV and no application is
    # a self-decline by construction, not a guess.
    no_cv = {"status": "rejected", "notes": "some note with no decisive wording",
             "applied": "FALSE", "cv_generated": "FALSE"}
    got, conf = OC.classify(no_cv)
    print(f"\n  {'ok  ' if got == OC.WE_DECLINED else 'BAD '} no CV + not applied "
          f"-> {got} [{conf}]  (cannot be rejected by someone you never applied to)")
    if got != OC.WE_DECLINED:
        failures.append("ambiguous status with no CV and no application must be WE_DECLINED")

    # A property worth asserting directly: a self-decline must never be counted
    # as a submitted application, or every conversion rate is understated.
    if OC.submitted(OC.WE_DECLINED):
        failures.append("WE_DECLINED must not count as a submitted application")
    if not OC.submitted(OC.EMPLOYER_REJECTED):
        failures.append("EMPLOYER_REJECTED must count as a submitted application")
    if OC.submitted(OC.UNKNOWN):
        failures.append("UNKNOWN must not be counted in either direction")

    total = len(CASES) + len(SOURCE_CASES) + 4
    print(f"\n  {total - len(failures)}/{total} passed")
    for f in failures:
        print(f"    {f}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
