"""The outcome vocabulary, and how to read it out of messy legacy rows.

Why this module exists
----------------------
Calibration asks one question: **of the roles we applied to, which advanced?**
Answering it needs two facts the registry did not cleanly record.

1. **Who ended it.** `rejected` was used both for "we decided not to apply"
   (off-domain, wrong city) and for "the employer said no after an interview".
   Those are opposite outcomes. Counting a self-decline as an application
   failure understates conversion and poisons every comparison built on it.

2. **Whether we actually applied.** The `applied` flag disagrees with `status`
   on real rows - there is a `recruiter_screen` row flagged `applied=FALSE`,
   which cannot be true. Status is the more reliable signal, so it wins.

The vocabulary below separates those. `classify()` maps legacy rows onto it
using status first and note text second, and returns UNKNOWN rather than
guessing - an outcome tool that quietly invents outcomes is worse than none,
because every number downstream inherits the invention.
"""

import re

# --- the vocabulary -------------------------------------------------------
# Terminal outcomes, grouped by who ended it.

WE_DECLINED = "we_declined"        # never applied: filtered, passed at triage, expired
APPLIED_PENDING = "applied_pending"  # submitted, still open, no decision yet
ADVANCED = "advanced"              # reached a human stage: screen, onsite, offer
EMPLOYER_REJECTED = "employer_rejected"  # they said no, at any stage
GHOSTED = "ghosted"                # applied, no response, closed by us
POSTING_PULLED = "posting_pulled"  # role removed or filled before a decision
UNKNOWN = "unknown"                # cannot be determined without a human

#: Outcomes that mean an application was actually submitted. Everything else
#: is either pre-application or unknowable, and must be excluded from any
#: conversion rate - including it is how a self-decline becomes a "failure".
SUBMITTED = {APPLIED_PENDING, ADVANCED, EMPLOYER_REJECTED, GHOSTED, POSTING_PULLED}

#: The numerator: outcomes that count as the pipeline working.
SUCCESS = {ADVANCED}

LABELS = {
    WE_DECLINED: "we declined / never applied",
    APPLIED_PENDING: "applied, awaiting decision",
    ADVANCED: "advanced to a human stage",
    EMPLOYER_REJECTED: "employer rejected",
    GHOSTED: "applied, no response",
    POSTING_PULLED: "posting pulled or filled",
    UNKNOWN: "unknown - needs a human",
}

ADVANCED_STATUSES = {"recruiter_screen", "screen", "onsite", "final", "offer",
                     "offer_declined", "hired"}

# Note-text signals. Ordered: the first match wins, so put the least ambiguous
# phrasings first.
_NOTE_RULES = [
    (EMPLOYER_REJECTED, r"rejection email|failed the (?:cases|interview|screen)|"
                        r"did not advance|not (?:moving|progressing) forward|"
                        r"went with another candidate|unsuccessful"),
    (POSTING_PULLED,    r"posting (?:removed|pulled|closed)|req (?:closed|pulled)|"
                        r"role (?:filled|cancelled)|no longer (?:listed|posted)"),
    (GHOSTED,           r"never replied|no response|no reply|cold, clos|went cold|"
                        r"silence"),
    (WE_DECLINED,       r"off-domain|off-categ|off-lane|location gap|location fail|"
                        r"not wa-eligible|relocation|declined|passed at triage|"
                        r"chose not to|not worth|do not surface|do-not-resurface|"
                        r"do not resurface|auto-expired|title stretch|too junior|too senior"),
]


def classify(row):
    """(outcome, confidence) for a registry row.

    confidence is "status" when the row's own status was decisive, "note" when
    it came from note text, and "weak" when the two disagreed or nothing
    matched. Weak rows are the backfill worklist.
    """
    status = (row.get("status") or "").strip().lower()
    notes = (row.get("notes") or "").lower()

    # Status first, where it is unambiguous.
    if status in ADVANCED_STATUSES:
        return ADVANCED, "status"
    if status == "applied":
        return APPLIED_PENDING, "status"
    if status in ("expired", "cancelled"):
        # cancelled = posting gone; expired = we never decided. Both pre-application,
        # unless a note says an application actually went in.
        if status == "cancelled" and re.search(_NOTE_RULES[1][1], notes):
            return POSTING_PULLED, "note"
        return WE_DECLINED, "status"

    # `rejected` and `closed` are the overloaded pair - the note decides.
    if status in ("rejected", "closed"):
        for outcome, pattern in _NOTE_RULES:
            if re.search(pattern, notes):
                return outcome, "note"
        return UNKNOWN, "weak"

    if not status:
        # No status at all: assessed but never moved on.
        return WE_DECLINED, "status"

    return UNKNOWN, "weak"


def submitted(outcome):
    return outcome in SUBMITTED


def advanced(outcome):
    return outcome in SUCCESS


# --- source channel normalisation ----------------------------------------
# `source` is free text and drifts. One real registry accumulated ~25 spellings
# of about six actual channels - the same job board capitalised three ways, plus
# variants carrying a requisition ID. Left as-is, no amount of extra data makes
# the channel comparison readable, because every bucket has n=1. Normalise for
# analysis; the raw value stays in the CSV so nothing is lost.

_SOURCE_RULES = [
    ("referral/inbound", r"referral|inbound"),
    ("inbox digest",     r"digest|alert|lensa|ladders|inbox"),
    ("linkedin",         r"linkedin"),
    ("board scan",       r"daily-search|board|tier|greenhouse|ashby|lever|"
                         r"smartrecruiters|workday|icims|\.jobs\b|careers"),
    ("user-supplied",    r"user-|direct|provided|supplied|request"),
    ("folder sync",      r"folder-sync"),
]


def normalize_source(raw):
    """Map a free-text source onto a canonical channel, or 'other'."""
    v = (raw or "").strip().lower()
    if not v:
        return None
    for label, pattern in _SOURCE_RULES:
        if re.search(pattern, v):
            return label
    return "other"
