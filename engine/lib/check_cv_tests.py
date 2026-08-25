#!/usr/bin/env python3
"""Generic harness for the guardrail matcher in check_cv.py.

The harness is method and ships with the engine. The CASES are identity and do
not: they live in `profile/guardrail_tests.json`, alongside the guardrails they
exercise. Point --profile elsewhere to test a different person's pack.

    python3 engine/lib/check_cv_tests.py
    python3 engine/lib/check_cv_tests.py --profile /path/to/other/profile

These exist because a guardrail that cries wolf gets ignored, and one that stays
silent is worse than none. Every false positive found on a real package should be
added to the fixtures BEFORE its pattern is loosened.
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_cv as C  # noqa: E402


class FakeDoc:
    """Minimal stand-in for Docx: check_facts only reads .text."""

    def __init__(self, text):
        self.text = text


def run(profile_dir):
    rails = os.path.join(profile_dir, "guardrails.json")
    fixtures = os.path.join(profile_dir, "guardrail_tests.json")
    for path in (rails, fixtures):
        if not os.path.exists(path):
            print(f"  no fixtures: {path} not found - nothing to test")
            return 0

    rules = json.load(open(rails))["guardrails"]
    cases = json.load(open(fixtures))["cases"]

    failures = []
    for case in cases:
        text, should_fail = case["text"], case["should_fail"]
        rep = C.Report()
        C.check_facts(rep, FakeDoc(text), rules, "T")
        did_fail = rep.rows[0]["status"] == C.FAIL
        mark = "ok  "
        if did_fail != should_fail:
            mark = "BAD "
            kind = "false positive" if did_fail else "missed"
            failures.append(f"{kind}: {text[:60]!r} ({case.get('why', '')})")
        print(f"  {mark} expect_fail={str(should_fail):<5} {text[:62]}")

    print(f"\n  {len(cases) - len(failures)}/{len(cases)} passed "
          f"against {len(rules)} guardrails")
    for f in failures:
        print(f"    {f}")
    return 1 if failures else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--profile", default=C.DEFAULT_PROFILE)
    return run(ap.parse_args().profile)


if __name__ == "__main__":
    sys.exit(main())
