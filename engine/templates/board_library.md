# Building and scanning a board library

A starter for `config/boards.md` — your own tiered list of company career boards.

**This file deliberately contains no company list.** A curated set of employers is specific to
one person's field, level, and metro; copying someone else's is worse than useless because it
looks like coverage while pointing at the wrong market. What generalizes is *how to choose
boards, how to scan them, and how to keep the list honest.* That is what follows.

---

## The tier model

**Tiers are scan priority, not location.** This is the single most useful correction to make
early: an early version of this system tiered boards by where the company was, which meant the
scan order tracked geography rather than probability, and the highest-yield boards got scanned
last or not at all.

| Tier | What earns a place | Cadence |
|---|---|---|
| **1 — Core** | Clears all five bars below. Highest probability of a real match. | Every sweep, before anything else |
| **2 — Rotation** | Strong domain and a verified board, but one bar is soft. | ~12 per sweep; full coverage across each cycle |
| **3 — Long tail** | Conditional, thin, or unproven. Includes boards that keep returning nothing. | Weekly, or when 1–2 come up dry |
| **4 — Watchlist** | Not scannable yet — no board, no local org, or no relevant layer. | Monthly, or on news |
| **S — Sources** | Not companies: investor-portfolio boards, ecosystem boards, aggregators, email digests. | Per source |

Location becomes a **column**, not a tier — one of "local office", "remote-eligible", or "verify
per role".

### The five bars for Tier 1

A board belongs in Tier 1 only if it clears all five. Anything less starts in Tier 2 and earns
promotion with evidence.

1. **Domain match** — the company is in one of your top-priority domains, not merely adjacent.
2. **Level density** — the board actually carries roles at your target level. Many good companies
   post only individual-contributor roles publicly and fill senior ones through recruiters.
3. **Location fit** — office in your metro, or genuinely remote-eligible in your state.
4. **A scannable board** — you can enumerate its postings reliably, by API or rendered browser.
5. **Evidence** — it has produced at least one real match, or there is a concrete reason to
   expect it will.

**Demote on evidence, not on feel.** If a Tier 1 board returns nothing at your level across two
or three consecutive sweeps, drop it to Tier 2 and record why. A list that only ever grows stops
being a priority ordering.

---

## ATS platforms and how to scan them

Most company boards run on a handful of platforms. Identifying the platform gives you the
enumeration method immediately.

### Platforms with a public JSON endpoint

These can be swept in bulk, no browser needed:

```
Greenhouse   https://boards-api.greenhouse.io/v1/boards/<slug>/jobs
Ashby        https://api.ashbyhq.com/posting-api/job-board/<slug>?includeCompensation=true
Lever        https://api.lever.co/v0/postings/<slug>?mode=json
```

The slug is usually the company name, but **not always** — verify it rather than assuming. A
board page that renders client-side often uses a different slug from its public URL, and a
guessed slug that 404s looks identical to a company with no openings.

### Platforms that usually need a rendered browser

Enterprise systems — Workday, iCIMS, Eightfold, Radancy, SmartRecruiters, and in-house boards —
typically render listings client-side, paginate aggressively, or reject non-browser requests.
Note the tenant and site identifiers when you find them; Workday in particular is
`<tenant>.wdN.myworkdayjobs.com/<site>` and both halves matter.

Two practical notes:

- **Some render slowly enough to look empty.** Re-read once before recording a zero.
- **Filter parameters are often non-obvious.** A plain `search=` frequently does nothing while a
  structured `filter[category]`-style parameter works. Find the working parameter once and write
  it down in the row.

### Always look for an endpoint before assuming there isn't one

**"No API path" is usually an untested assumption.** Open the board in a browser, watch the
network tab while listings load, and look for the request that returns the data. Boards
documented as browser-only have turned out to have a plain JSON endpoint all along — including
ones labelled as a platform that normally has none.

This matters more than it sounds. Boards with easy APIs get scanned; boards without them get
skipped. Letting that asymmetry stand quietly narrows the search to companies with modern
tooling, which is rarely the same set as companies with the right jobs.

---

## Delta scanning

Re-reading the same boards in full every day produces repeated zeros and real cost. Instead,
diff each board's current posting-ID set against what was seen last time:

```bash
python3 engine/lib/board_scan.py diff <slug> --ids "id1,id2,…"   # prints only NEW ids
python3 engine/lib/board_scan.py diff <slug> --json board.json
python3 engine/lib/board_scan.py status                          # per-board age + staleness
```

Only new IDs proceed to the title, level, and domain filter.

**Every scan must end by recording its IDs.** An untracked scan is indistinguishable from a
skipped one — which means coverage claims cannot be verified and quietly stop being true. Open
each sweep with `status` and clear its staleness warnings first.

---

## Keeping the list honest

Record for every board: the working URL, the platform and slug, the domains it covers, the
location posture, any scan quirk you had to discover, and the date and result of the last scan.

- **Fix the row when a slug 404s or a board moves.** A stale row silently becomes a skipped board.
- **Record the technique, not just the URL** — the pagination trick or filter parameter you
  worked out is the expensive part, and you will not remember it next month.
- **Keep a do-not-scan list** of boards that proved to be dead ends, aggregator decoys, or
  duplicates of another entry. Without it, the same bad board gets rediscovered and re-added
  every few weeks.
