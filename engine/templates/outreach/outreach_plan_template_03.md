# Outreach Plan — {{COMPANY}}, {{ROLE_TITLE}}

_Created: {{YYYY-MM-DD}} | Applied: {{YYYY-MM-DD}} | Fit: {{Strong|Partial}} ({{one-clause reason}}) | JD: {{JD_URL}}_

## Context & framing

{{Location and remote policy. Posted comp band, and whether it clears the configured floor.}}
{{Where the fit is strongest, in the JD's own vocabulary.}} {{The honest gap, named plainly — the same
gap the cover letter names; the outreach note leads with the strength and does not oversell the gap.}}
{{Any title guardrail that applies: sell the work, never a title the candidate has not held.}}

**Primary channel: {{email | LinkedIn}}.** {{Why — the rule: a small, remote, or founder-led company means
the hiring manager's inbox is reachable, so email leads; a large formal enterprise means LinkedIn leads and
email is the backup.}}

## Targets

### Primary hiring manager ({{closest domain owner | safest senior target}})
- **{{Full Name}}** — {{Title}}, {{Company}} ({{one line of relevant background}})
  - LinkedIn: {{linkedin.com/in/slug}} — {{Nth}} degree, mutuals: {{Name, Name}}
  - Email guess (pattern `{{first.last@}}`, {{confidence}}%): **{{first.last@company.com}}** | alt `{{flast@company.com}}`
  - Confidence: {{HIGH|MEDIUM|LOW}} on identity. {{Why this person owns the role.}}

### Alternate / skip-level ({{verify before contacting}})
- **{{Full Name}}** — {{Title}} @ {{Company}} — {{linkedin.com/in/slug}} ({{degree}}; mutuals {{Name}}) — guess `{{flast@company.com}}`
- {{Note any open peer req the role may report into once filled, or any name-spelling that press sources disagree on. Verify before using a name.}}

### Warm internal paths (ask for a referral before cold-emailing)
- **{{Full Name}}** — {{Title}} @ {{Company}} — {{linkedin.com/in/slug}} ({{degree}}; mutual {{Name}})
- {{Second-degree people in the same function are the referral ask; a soft intro beats a cold note.}}

### Recruiter (backup channel)
- {{Named recruiter from the application-confirmation email — the ATS the company uses will surface one.}}
  Otherwise LinkedIn: "{{Company}} {{technical|executive}} recruiter, {{metro}}". {{Coordinators are not
  decision-makers; prefer the hiring manager.}}

## Approach & sequence

1. **Applied via {{ATS or careers page}} (done {{YYYY-MM-DD}}).**
2. {{Any verification step that must happen first — confirm the HM's identity, exact name spelling, or LinkedIn slug.}}
3. **Same day or next day: {{email | LinkedIn message}} the confirmed hiring manager** with the note below.
4. **~4-5 days silent → {{the other channel}}.** One channel per message; never the same text on both at once.
5. {{If a warm mutual exists, consider asking for a soft intro instead of cold-contacting.}}
6. Log every touch: `registry.py outreach "{{Company}}" --note "{{what was sent, to whom}}" --next "{{next step}}" --due {{YYYY-MM-DD}}`

---

## Templates

Each message uses the same three-part spine; only length and channel change.
**(1) Opener** — applied through the careers page, plus one sober line on why this company.
**(2) About me** — three or four lines, anchored on the strongest role-relevant credential, every claim
carrying a number, nothing the candidate cannot defend in an interview.
**(3) One ask** — a short conversation about fit with the role. Never hedge, never offer to be redirected.

### 1. Email
**To:** {{first.last@company.com}}  (alt: {{flast@company.com}})
**Subject:** {{Role Title}} — application + intro

Hi {{First name}},

I came across the {{Role Title}} role and applied through the {{Company}} careers page. I wanted to introduce myself directly.

A bit about me: {{three or four lines of the strongest role-relevant evidence, each with a number. Lead with the credential the JD's first responsibility asks for.}}

Would you be open to a short conversation to see if there's a fit with the role?

Best,
{{Full Name}}
{{linkedin.com/in/slug}}

### 2. LinkedIn message (long — if connected, or via InMail)

Hi {{First name}} — I applied for the {{Role Title}} role and wanted to reach out directly. {{Two or three
sentences of the same evidence, compressed.}} {{One sentence naming what this company is doing that makes the
role the one worth moving for — sober, not gushing.}} Would you be open to a short conversation to see if there's a fit?
— {{First name}}

### 3. LinkedIn connection request (short, hard cap 300 characters)

Hi {{First name}} — I applied for the {{Role Title}} role and wanted to connect. {{One line of evidence with
the two or three strongest proof points.}} Would welcome a short conversation about fit with the role.

<!--
BUILD NOTES (delete when filling this out)

Email patterns — verify before sending, a bounce burns the contact:
  first.last@company.com   most common at mid/large companies
  flast@company.com        common at large enterprises
  first@company.com        usual at founder-led and small shops
  New company → web-search "<company> email format". Never present a guess as verified.

Confidence labels: HIGH = identity confirmed on LinkedIn or the company leadership page; MEDIUM = inferred
from org structure; LOW = press-only, unverified spelling.

Name collisions are common. Confirm the person is at this company, in this function, before using their name.

No CV attached — it is already in the ATS, and attachments from unknown senders hurt deliverability.
-->
