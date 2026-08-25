# CV Customizer

A job-application engine that runs inside [Claude Code](https://claude.com/claude-code). You
give it a job posting; it assesses whether the role is worth your time, and if it is, builds a
tailored CV, cover letter, and outreach plan — then mechanically audits them before you send.

It is built around one stubborn idea: **the constraint on a senior job search is not how many
applications you send, it is whether each one is true and whether anyone replies.** So the
engine optimizes for honesty and response rate, not throughput.

---

## What it actually does

**Assesses first, builds second.** Every posting gets a five-part fit verdict — what matches,
what does not, a seniority check, and a clear go/no-go — before a single document is written.
It will tell you not to apply. That is the feature.

**Refuses to lie for you.** You write down, once, the things you cannot defend in an interview:
titles you never held, figures that drifted, tools you never touched, work someone else owned.
The auditor then hard-fails any CV or cover letter containing them. This matters because a
keyword-optimizing model is *structurally* inclined to overclaim, and prose rules alone do not
stop it — in the archive this was built against, banned claims shipped in real CVs while the
rule forbidding them sat in context.

**Audits mechanically, not by vibes.** `check_cv.py` measures page extent with real geometry,
counts em-dashes, verifies the font, checks date format and right tab stops, tests
reverse-chronological order, confirms every bullet carries a number, rebuilds and verifies the
hyperlink set, checks filenames, scans JD keyword coverage and repetition, and runs your
guardrails. Exit 1 means fix something. A checklist a human re-reads is a checklist that decays.

**Tracks the pipeline.** A registry dedups every posting you have seen, and a follow-up engine
surfaces stale applications so they get an outreach attempt instead of rotting.

## What it does not do

It does not apply on your behalf, auto-send email, or scrape behind logins. It does not
guarantee interviews. It does not invent achievements to fill a gap — if a posting needs
something you lack, it says so and expects you to decide.

It is also **not general-purpose yet.** It encodes a senior individual doing a targeted search
in the US market. Levels, domains, and geography live in config so adjacent fields work, but
if you are early-career or outside that shape, expect to edit more than a config file.

---

## The layer model

The one design decision everything else follows from: **five kinds of content, four homes.**
Mixing them is what makes systems like this impossible to share or upgrade.

| Layer | What it is | Ships publicly? |
|---|---|---|
| `engine/` | **Method.** How to assess, build, audit, search. Names no person, employer, city, figure, or path. | Yes |
| `config/` | **Policy.** Page caps, fonts, comp floor, geography, cadence. Reads personal; is actually parameters. | Ships as `*.example.json` |
| `profile/` | **Identity.** Your career facts, canonical links, and never-claim guardrails. | **Never** |
| `_registry/`, application folders | **State.** Your posting registry, per-board scan state, and every package you have built. | **Never** |

The test for anything in `engine/`: *if a sentence names a person, an employer, a city, a
dollar figure, or a machine path, it is misfiled.*

The payoff: `engine/` holds no user data, so upgrading means replacing `engine/` and keeping
everything else untouched.

---

## Install

Requires Claude Code, Python 3.9+, and LibreOffice (`soffice`) for DOCX→PDF. `pymupdf` is
optional and only powers the page-geometry check.

```bash
git clone <this repo> cv-customizer && cd cv-customizer
cp .claude/settings.example.json .claude/settings.json   # replace <PROJECT_ROOT>
cp config/search.example.json    config/search.json
cp config/documents.example.json config/documents.json
cp -r profile.example            profile
python3 engine/lib/check_cv_tests.py                     # should pass
claude
```

Then follow **[QUICKSTART.md](QUICKSTART.md)** — the profile is the part that determines
whether any of this is worth running, and it deserves a real half hour.

## Commands

| Command | What it does |
|---|---|
| `/setup [cv.docx]` | Guided first run: build the profile and config, ending in a clean audit |
| `/jd <url>` | Assess a posting; if it is a strong fit, build the full package |
| `/daily-search` | Run the full search sweep across every configured source |
| `/followups` | Post-application worklist: due actions, stale applies, outreach drafts |
| `/reaudit <company>` | Re-check a built-but-unsent package against current rules |
| `/hygiene` | Sweep for build junk, damaged files, and structural rot |
| `/refresh` | Periodic maintenance so the profile, boards, and packages do not rot |

## The tools underneath

Every command is ordinary Python you can run yourself.

```bash
python3 engine/lib/build_package.py --app app.json    # the whole set, gated on the audit
python3 engine/lib/check_cv.py "<folder>" [--jd jd.txt]
python3 engine/lib/check_cv_tests.py                  # guardrail regression suite

python3 engine/lib/build_cv.py -o cv.docx [--tailor t.json]
python3 engine/lib/build_cover_letter.py --letter l.json -o letter.docx
python3 engine/lib/build_outreach.py --plan p.json -o "outreach plan.md"
python3 engine/lib/extract_career.py <existing_cv.docx> -o profile/career.json

python3 engine/lib/registry.py check|add|applied|followups|expire|sync
python3 engine/lib/board_scan.py diff <slug> --ids "…" | status
python3 engine/lib/publish.py --to ../public-copy    # assemble + refuse on any leak
```

`build_package.py` is the one that matters: it generates everything in a scratch directory and
copies it into the application folder **only if the audit passes**. A package that does not audit
clean should not exist somewhere you can send it by accident.

## Privacy

`profile/`, `config/*.json` (your live values), and every application folder are git-ignored by
default. They contain your complete professional history and, once you start outreach, other
people's contact details. Before sharing anything, check what is actually in it — and note that
deleting files later does not remove them from git history.

## License

Engine code and templates: MIT. See [LICENSE](LICENSE). Your profile, your documents, and your
application history are yours and are not covered by this repository.
