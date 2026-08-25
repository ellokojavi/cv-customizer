#!/usr/bin/env python3
"""Tests for the registry's write-safety guard.

    python3 engine/lib/registry_tests.py

`match()` has a convenience fallback: when several rows share a company name it
picks the single non-terminal one. That is right for a dedup CHECK and wrong
for a write.

It was wrong in exactly the way that is hard to notice: asked to record a
rejection against a company with two roles, it silently chose the *other* row -
the one never applied to - and appended an outcome that had not happened to it,
while leaving the real application untouched. Nothing errored. Both rows were
plausible afterwards.

A read that guesses wrong costs a second look. A write that guesses wrong
corrupts the record it was meant to correct, and the corruption looks like
data.
"""

import io
import os
import sys
from contextlib import redirect_stdout

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import registry as R  # noqa: E402


def row(company, role, **kw):
    r = {c: "" for c in R.COLS}
    r.update(company=company, role_title=role)
    r.update(kw)
    return r


TWO_ROLES = [
    row("Acme", "Director, Widgets", status="", applied="FALSE",
        job_id="AC-1", url="https://acme.example/jobs/1"),
    row("Acme", "Director, Gadgets", status="closed", applied="TRUE",
        job_id="AC-2", url="https://acme.example/jobs/2",
        jd_folder="20260101 Acme - Director Gadgets"),
]
ONE_ROLE = [row("Solo", "Head of Product", status="", applied="FALSE", job_id="S-1")]


def expect_refusal(rows, query, label):
    buf = io.StringIO()
    try:
        with redirect_stdout(buf):
            R.resolve_for_write(rows, query, "test")
    except SystemExit as e:
        out = buf.getvalue()
        ok = e.code == 2 and "AMBIGUOUS" in out
        # The refusal must be actionable: it has to name both candidates.
        named = all(r["role_title"] in out for r in rows)
        return ok and named, ("refused and listed both candidates" if ok and named
                              else f"refused but unhelpfully: {out[:80]!r}")
    return False, f"{label}: did NOT refuse - it picked a row and would have written to it"


def expect_match(rows, query, want_role, label):
    buf = io.StringIO()
    try:
        with redirect_stdout(buf):
            r = R.resolve_for_write(rows, query, "test")
    except SystemExit:
        return False, f"{label}: refused, but this query is unambiguous"
    if r is None:
        return False, f"{label}: found nothing"
    return r["role_title"] == want_role, f"resolved to {r['role_title']!r}"


def main():
    checks = [
        ("company-only, two roles -> refuse",
         lambda: expect_refusal(TWO_ROLES, "Acme", "company-only")),
        ("job_id disambiguates -> write allowed",
         lambda: expect_match(TWO_ROLES, "AC-2", "Director, Gadgets", "by id")),
        ("url disambiguates -> write allowed",
         lambda: expect_match(TWO_ROLES, "https://acme.example/jobs/1",
                              "Director, Widgets", "by url")),
        ("folder disambiguates -> write allowed",
         lambda: expect_match(TWO_ROLES, "20260101 Acme - Director Gadgets",
                              "Director, Gadgets", "by folder")),
        ("single row for a company -> write allowed",
         lambda: expect_match(ONE_ROLE, "Solo", "Head of Product", "single")),
    ]

    failures = []
    for label, fn in checks:
        ok, detail = fn()
        if not ok:
            failures.append(f"{label}: {detail}")
        print(f"  {'ok  ' if ok else 'BAD '} {label:<46} {detail}")

    print(f"\n  {len(checks) - len(failures)}/{len(checks)} passed")
    for f in failures:
        print(f"    {f}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
