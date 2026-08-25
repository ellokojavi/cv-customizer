# 22 — Outreach plan and the post-application engine

**Response rate, not application count, is the binding constraint.** Cold applications through
an ATS convert poorly enough that the follow-up motion, not the submission, is where the leverage
is. This file is why the system does not consider an application finished when it is submitted.

The outreach plan is a standard deliverable: build it automatically for every Strong fit, and for
any role the moment it moves to `applied`.

---

## Scouting contacts

**Identify the likely hiring manager.** At founder-led or smaller companies this is often the
CEO. Check whether the role is a backfill and who held it last — a departing predecessor's
LinkedIn tells you the reporting line, the team size, and sometimes why the seat is open.
Identify an in-house recruiter as backup.

**Verify identity carefully.** Name collisions are routine: similarly-named companies, agencies
with the employer's name in their handle, and unrelated organizations sharing an acronym. Getting
this wrong sends a personal note to a stranger, which is worse than sending nothing.

**Guess the email pattern, then verify before sending.** Small and founder-led companies skew to
`first@company`; larger ones to `first.last@company` or `firstinitiallast@company`. Record the
pattern and your confidence in it, and never send to a guess you would not defend.

---

## The plan file

One markdown file in the application folder containing:

- **Contacts** — hiring manager and recruiter: name, title, LinkedIn, shared background or
  mutuals, email-pattern guess, and a confidence level for each.
- **Warm paths** — anyone already in the candidate's network who can make an internal referral.
  A referral outperforms every cold channel and is worth an extra day of delay.
- **Sequence** — which channel, in what order, with what spacing.
- **Three ready-to-send drafts** — email with To: and Subject: lines, a long LinkedIn message,
  and a LinkedIn connection request under 300 characters.

## Writing the note

Anchor on `profile/identity.json` → `voice`. The shape:

- **Direct opener.** Name the role and say you applied through their careers page. No throat
  clearing, no flattery about the company's mission.
- **Three or four lines about you**, anchored on the credential the candidate most wants
  remembered plus the single most role-relevant one. Not a CV summary — the CV is already in
  their ATS.
- **One honest closing ask.** A short conversation about fit. Never imply curiosity the candidate
  does not have, never hedge with "if there's a good fit," and never pre-emptively offer to be
  redirected to "the right person" — that hands the reader an easy exit.

**No CV attached.** It is already in their ATS, and attachments from unknown senders hurt
deliverability. Signature is name plus profile URL.

**Sequence:** apply through the canonical ATS → same-day email to the hiring manager → LinkedIn
connection note after four or five days of silence. **One channel per message.** Never send the
same text on two channels simultaneously; it reads as a mail merge, which is exactly what it is
trying not to be.

---

## Keeping it alive

Thresholds are in `config/search.json` → `post_application`.

- Marking a role `applied` auto-sets a next action to scout outreach, due two days out.
- Record outreach and interview stages in the registry as they happen. An untracked send is
  indistinguishable from one that never went out.
- The follow-up worklist surfaces due actions plus stale applications — applied past the stale
  threshold, no response, no outreach. Check it every run; act on it every weekly review.
- Applications inside the outreach window with no response and no outreach get the scout. Outside
  the window, let them go; there is more value in the next application than in a fourth touch on
  a silent one.
