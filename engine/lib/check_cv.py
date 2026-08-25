#!/usr/bin/env python3
"""Deterministic pre-delivery auditor for a job-application package.

Person-agnostic by construction. Nothing in this module names a person, an
employer, a city, a figure, or a machine path; it reads two layers instead:

    config/documents.json   POLICY   page caps, format rules, thresholds
    profile/                IDENTITY canonical links, never-claim guardrails

Only the first ships with the engine. A missing profile is not an error - the
identity checks SKIP with a reason, so a fresh install runs before the user has
authored anything.

Usage
-----
    python3 engine/lib/check_cv.py "<job folder>"          # audit a package
    python3 engine/lib/check_cv.py --cv <file.docx>        # audit one CV
    python3 engine/lib/check_cv.py "<folder>" --jd jd.txt  # + keyword checks
    python3 engine/lib/check_cv.py "<folder>" --json       # machine-readable

Exit code is 1 if any check FAILs, else 0. WARNs never fail the build.

Only the page-geometry check needs a third-party module (pymupdf); everything
else is standard library, so the auditor still runs on a bare machine.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
import zipfile
from collections import Counter
from xml.etree import ElementTree as ET

def normalize_canonical(canonical):
    """profile/links.json canonical table -> [(anchor_text, url)].

    A value is either a bare URL string, in which case the key doubles as the
    anchor text, or {"anchor": …, "url": …} when the two differ. The explicit
    form exists because keys must be unique while anchor text need not be: two
    press links can both be anchored on the same publication name, and there is
    no way to express that with the key alone.
    """
    out = []
    for key, val in (canonical or {}).items():
        if isinstance(val, dict):
            out.append((val.get("anchor") or key, val.get("url", "")))
        else:
            out.append((key, val))
    return out


W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"

PASS, WARN, FAIL, SKIP = "PASS", "WARN", "FAIL", "SKIP"

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
DEFAULT_CONFIG = os.path.join(PROJECT_ROOT, "config", "documents.json")
DEFAULT_PROFILE = os.path.join(PROJECT_ROOT, "profile")

EM_DASH, EN_DASH = "—", "–"


# --------------------------------------------------------------------------
# result plumbing
# --------------------------------------------------------------------------

class Report:
    def __init__(self):
        self.rows = []

    def add(self, name, status, detail=""):
        self.rows.append({"check": name, "status": status, "detail": detail})

    @property
    def failed(self):
        return any(r["status"] == FAIL for r in self.rows)

    def render(self):
        width = max((len(r["check"]) for r in self.rows), default=10)
        colour = {PASS: "\033[32m", WARN: "\033[33m", FAIL: "\033[31m", SKIP: "\033[90m"}
        tty = sys.stdout.isatty()
        out = []
        for r in self.rows:
            tag = r["status"]
            if tty:
                tag = f"{colour[r['status']]}{r['status']}\033[0m"
            out.append(f"  {r['check']:<{width}}  {tag}  {r['detail']}")
        return "\n".join(out)


# --------------------------------------------------------------------------
# docx reading (stdlib only: a .docx is a zip of XML)
# --------------------------------------------------------------------------

class Docx:
    def __init__(self, path):
        self.path = path
        with zipfile.ZipFile(path) as z:
            self.document = ET.fromstring(z.read("word/document.xml"))
            try:
                rels = z.read("word/_rels/document.xml.rels").decode("utf-8")
            except KeyError:
                rels = ""
            try:
                self.styles_xml = z.read("word/styles.xml").decode("utf-8")
            except KeyError:
                self.styles_xml = ""
        self.rels = dict(
            re.findall(r'Id="([^"]+)"[^>]*Target="(http[^"]+)"', rels)
        )
        self.paragraphs = [self._para(p) for p in self.document.iter(W + "p")]

    def _para(self, p):
        """One paragraph as {text, style, tabs, link_ids}.

        `w:tab` is overloaded in OOXML: inside `w:pPr/w:tabs` it declares a tab
        *stop*, inside a run it is a literal tab *character*. Only the latter
        belongs in the text, so the properties subtree is walked separately.
        """
        pPr = p.find(W + "pPr")
        runs = []
        for run in p.iter(W + "r"):
            for node in run.iter():
                if node.tag == W + "t":
                    runs.append(node.text or "")
                elif node.tag == W + "tab":
                    runs.append("\t")
                elif node.tag in (W + "br", W + "cr"):
                    runs.append("\n")
        style_el = p.find(f"{W}pPr/{W}pStyle")
        tabs = []
        if pPr is not None:
            for t in pPr.iter(W + "tab"):
                pos, align = t.get(W + "pos"), t.get(W + "val")
                if pos is not None:  # a tab stop, in twips
                    tabs.append((int(pos) / 1440.0, align))
        links = [
            h.get(R + "id")
            for h in p.iter(W + "hyperlink")
            if h.get(R + "id")
        ]
        return {
            "text": "".join(runs),
            "style": style_el.get(W + "val") if style_el is not None else None,
            "tabs": tabs,
            "link_ids": links,
        }

    @property
    def text(self):
        return "\n".join(p["text"] for p in self.paragraphs)

    def hyperlinks(self):
        """[(anchor_text, url)] in document order."""
        out = []
        for p_el in self.document.iter(W + "p"):
            for h in p_el.iter(W + "hyperlink"):
                rid = h.get(R + "id")
                if not rid:
                    continue
                anchor = "".join(t.text or "" for t in h.iter(W + "t"))
                out.append((anchor.strip(), self.rels.get(rid, "")))
        return out

    def page_geometry(self):
        """(page_w_pt, page_h_pt, top_pt, bottom_pt, right_tab_in) from sectPr."""
        sect = None
        for s in self.document.iter(W + "sectPr"):
            sect = s
        if sect is None:
            return None
        pg = sect.find(W + "pgSz")
        mar = sect.find(W + "pgMar")
        if pg is None or mar is None:
            return None
        tw = lambda v: int(v) / 20.0  # twips -> points
        w_pt, h_pt = tw(pg.get(W + "w")), tw(pg.get(W + "h"))
        top, bottom = tw(mar.get(W + "top")), tw(mar.get(W + "bottom"))
        left, right = tw(mar.get(W + "left")), tw(mar.get(W + "right"))
        right_tab_in = (w_pt - left - right) / 72.0
        return w_pt, h_pt, top, bottom, right_tab_in

    def fonts(self):
        names = set()
        for rf in self.document.iter(W + "rFonts"):
            for attr in ("ascii", "hAnsi", "cs"):
                v = rf.get(W + attr)
                if v:
                    names.add(v)
        for m in re.finditer(r'w:ascii="([^"]+)"', self.styles_xml):
            names.add(m.group(1))
        return names


# --------------------------------------------------------------------------
# individual checks
# --------------------------------------------------------------------------

def check_length(rep, pdf_path, cap, label, geom):
    """Measure real page extent: full pages + fraction of the last one used."""
    if not pdf_path or not os.path.exists(pdf_path):
        rep.add(f"{label} length", SKIP, "no PDF found")
        return
    try:
        import pymupdf
    except ImportError:
        rep.add(f"{label} length", SKIP, "pymupdf not installed")
        return

    top = geom[2] if geom else 36.0
    doc = pymupdf.open(pdf_path)
    n = doc.page_count
    last = doc[n - 1]
    usable = last.rect.height - 2 * top
    blocks = [b for b in last.get_text("blocks") if (b[4] or "").strip()]
    if not blocks:
        ratio = float(n - 1)
    else:
        bottom = max(b[3] for b in blocks)
        ratio = (n - 1) + (bottom - top) / usable
    doc.close()

    detail = f"{ratio:.2f} pages (cap {cap:.2f}), {n} sheet(s)"
    if n > 1:
        detail += f"; last page {100 * (ratio - (n - 1)):.0f}% full"
    rep.add(f"{label} length", FAIL if ratio > cap + 1e-9 else PASS, detail)


def check_dashes(rep, docx, label):
    text = docx.text
    em, en = text.count(EM_DASH), text.count(EN_DASH)
    if em or en:
        sample = []
        for line in text.splitlines():
            if EM_DASH in line or EN_DASH in line:
                sample.append(line.strip()[:60])
        rep.add(f"{label} dashes", FAIL,
                f"{em} em-dash, {en} en-dash: " + " | ".join(sample[:3]))
    else:
        rep.add(f"{label} dashes", PASS, "no em-dashes or en-dashes")


def check_font(rep, docx, expected, label):
    found = docx.fonts()
    stray = sorted(f for f in found if f != expected)
    if not found:
        rep.add(f"{label} font", WARN, "no explicit font runs found")
    elif stray:
        rep.add(f"{label} font", FAIL, f"expected {expected!r}, also found: {', '.join(stray)}")
    else:
        rep.add(f"{label} font", PASS, expected)


def check_filenames(rep, files, pattern, max_len):
    rx = re.compile(pattern)
    bad = [os.path.basename(f) for f in files if not rx.match(os.path.basename(f))]
    long = [os.path.basename(f) for f in files if len(os.path.basename(f)) > max_len]
    if bad:
        rep.add("Filenames", FAIL, f"off-pattern: {', '.join(bad)}")
    elif long:
        rep.add("Filenames", FAIL, f"over {max_len} chars: {', '.join(long)}")
    else:
        rep.add("Filenames", PASS, f"{len(files)} file(s) match pattern, all < {max_len} chars")


def check_links(rep, docx, cfg):
    links = docx.hyperlinks()
    urls = [u for _, u in links]
    canonical = cfg.get("canonical")
    if canonical is None:
        rep.add("Hyperlinks", SKIP,
                f"{len(links)} links; no profile/links.json to check them against")
        return
    canon_urls = {u for _, u in normalize_canonical(canonical)}
    lo, hi = cfg.get("min", 8), cfg.get("max", 12)

    problems = []
    for anchor, url in links:
        clean = url.replace("&amp;", "&")
        for bad in cfg.get("deny_substrings", []):
            if bad in clean:
                problems.append(f"banned host {bad!r} on {anchor!r}")
        if cfg.get("deny_bare_homepage", True) and clean not in canon_urls:
            path = re.sub(r"^https?://[^/]+", "", clean)
            if path in ("", "/"):
                problems.append(f"bare homepage {clean!r} on {anchor!r}")
    off_list = [u.replace("&amp;", "&") for u in urls
                if u.replace("&amp;", "&") not in canon_urls]
    if off_list:
        problems.append("not in canonical table: " + ", ".join(off_list[:3]))

    if problems:
        rep.add("Hyperlinks", FAIL, f"{len(links)} links; " + "; ".join(problems[:4]))
    elif not (lo <= len(links) <= hi):
        rep.add("Hyperlinks", WARN, f"{len(links)} links, target {lo}-{hi}; all canonical")
    else:
        rep.add("Hyperlinks", PASS, f"{len(links)} links, all canonical")


def check_dates(rep, docx, cfg):
    """Date ranges: right-aligned on the role line, correct format, no 'Present'."""
    fmt = re.compile(cfg.get("date_format", r"^[A-Z][a-z]{2} \d{4} - [A-Z][a-z]{2} \d{4}$"))
    geom = docx.page_geometry()
    want_tab = round(geom[4], 2) if geom else None

    dated, bad_fmt, bad_tab = [], [], []
    for p in docx.paragraphs:
        if "\t" not in p["text"]:
            continue
        left, _, right = p["text"].partition("\t")
        right = right.strip()
        if not re.search(r"\d{4}", right):
            continue
        dated.append(right)
        if not fmt.match(right) and not re.match(r"^[A-Z][a-z]{2} \d{4}$", right):
            bad_fmt.append(right)
        stops = [round(pos, 2) for pos, align in p["tabs"] if align == "right"]
        if want_tab is not None and want_tab not in stops:
            bad_tab.append(f"{left.strip()[:32]!r}")

    banned = [d for d in dated if re.search(cfg.get("banned_date_word", r"\bPresent\b"), d)]
    if banned:
        rep.add("Dates", FAIL, f"'Present' used in: {', '.join(banned)}")
    elif bad_tab:
        rep.add("Dates", FAIL,
                f"missing right tab stop at {want_tab}in on: {', '.join(bad_tab[:3])}")
    elif bad_fmt:
        rep.add("Dates", WARN,
                f"{len(dated)} dated lines, right-aligned at {want_tab}in; "
                f"off-format: {', '.join(bad_fmt)}")
    else:
        rep.add("Dates", PASS, f"{len(dated)} lines right-aligned at {want_tab}in, format ok")


def check_chronology(rep, docx, cfg):
    """Experience section must run strictly reverse-chronological."""
    heads = cfg.get("section_headings", {})
    exp, edu = heads.get("experience", "PROFESSIONAL EXPERIENCE"), heads.get("education", "EDUCATION")
    inside, ends = False, []
    for p in docx.paragraphs:
        t = p["text"].strip()
        if t == exp:
            inside = True
            continue
        if t == edu:
            inside = False
            continue
        if inside and "\t" in t:
            years = re.findall(r"(\d{4})", t.split("\t", 1)[1])
            if years:
                ends.append((int(years[-1]), t.split("\t", 1)[0].strip()[:34]))
    if not ends:
        rep.add("Chronology", SKIP, "no dated experience entries found")
        return
    out_of_order = [
        f"{ends[i][1]!r} ({ends[i][0]}) after ({ends[i - 1][0]})"
        for i in range(1, len(ends)) if ends[i][0] > ends[i - 1][0]
    ]
    if out_of_order:
        rep.add("Chronology", FAIL, "; ".join(out_of_order))
    else:
        rep.add("Chronology", PASS, f"{len(ends)} roles, reverse-chronological")


def check_structure(rep, docx, cfg):
    heads = cfg.get("section_headings", {})
    order = cfg.get("section_order", [])
    present = [p["text"].strip() for p in docx.paragraphs
               if p["text"].strip() in set(order)]
    missing = [s for s in order if s not in present]
    if missing:
        rep.add("Sections", FAIL, f"missing: {', '.join(missing)}")
    elif present != [s for s in order if s in present]:
        rep.add("Sections", FAIL, f"out of order: {' > '.join(present)}")
    else:
        rep.add("Sections", PASS, " > ".join(present))

    # no forced page break immediately before EDUCATION
    edu = heads.get("education", "EDUCATION")
    xml = ET.tostring(docx.document, encoding="unicode")
    idx = xml.find(f">{edu}<")
    if idx > 0 and 'w:type="page"' in xml[max(0, idx - 1200):idx]:
        rep.add("Page breaks", FAIL, f"forced page break before {edu}")
    else:
        rep.add("Page breaks", PASS, f"no forced break before {edu}")


def check_bullets(rep, docx, cfg):
    style = cfg.get("bullet_style", "ListParagraph")
    bullets = [p["text"].strip() for p in docx.paragraphs
               if (p["style"] or "").replace(" ", "") == style and p["text"].strip()]
    if not bullets:
        rep.add("Bullets", SKIP, f"no paragraphs with style {style!r}")
        return
    numberless = [b[:44] for b in bullets if not re.search(r"\d", b)]
    if numberless:
        rep.add("Bullets", FAIL,
                f"{len(numberless)}/{len(bullets)} carry no number: "
                + " | ".join(numberless[:2]))
    else:
        rep.add("Bullets", PASS, f"all {len(bullets)} bullets carry a number")


def check_facts(rep, docx, rules, label):
    """Profile guardrails: claims that must never appear.

    Three escape hatches keep these from firing on legitimate text:
      `requires`      - satisfied elsewhere in the document (e.g. a term is
                        allowed as long as it is defined somewhere).
      `allow_context` - this particular occurrence sits in an exonerating
                        window, e.g. naming the VP role being applied *for*
                        rather than claiming the title.
    """
    if not rules:
        rep.add(f"{label} facts", SKIP, "no profile/guardrails.json found")
        return
    text = docx.text
    hits = []
    for rule in rules:
        flags = re.IGNORECASE if rule.get("ignore_case") else 0
        rx = re.compile(rule["pattern"], flags)
        if rule.get("requires") and re.search(rule["requires"], text, flags):
            continue
        allow = re.compile(rule["allow_context"], flags) if rule.get("allow_context") else None
        for m in rx.finditer(text):
            if allow:
                window = text[max(0, m.start() - 60):m.end() + 80]
                if allow.search(window):
                    continue
            snippet = text[max(0, m.start() - 20):m.end() + 30].replace("\n", " ")
            hits.append(f"{rule['message']} (...{snippet.strip()}...)")
            break
    if hits:
        rep.add(f"{label} facts", FAIL, "; ".join(hits))
    else:
        rep.add(f"{label} facts", PASS, f"{len(rules)} guardrails clear")


def check_keywords(rep, docx, jd_text, cfg):
    if not jd_text:
        rep.add("Keywords", SKIP, "no --jd supplied")
        return
    stop = set(cfg.get("stopwords", []))
    tok = lambda s: [w for w in re.findall(r"[a-z][a-z\-/&]{3,}", s.lower()) if w not in stop]
    jd_terms = {w for w, c in Counter(tok(jd_text)).items() if c >= 2}
    cv_counts = Counter(tok(docx.text))
    matched = sorted(t for t in jd_terms if cv_counts[t] > 0)
    lo, hi = cfg.get("min", 15), cfg.get("max", 25)
    cap = cfg.get("repeat_cap", 5)

    # Words like "product" or "director" recur structurally in role titles and
    # section headings; counting those as keyword stuffing is noise.
    exempt = set(cfg.get("repeat_exempt", []))
    over = [(t, cv_counts[t]) for t in matched
            if cv_counts[t] > cap and t not in exempt]
    egregious = [f"{t}x{n}" for t, n in over if n > 2 * cap]
    mild = [f"{t}x{n}" for t, n in over if n <= 2 * cap]

    if egregious:
        rep.add("Keywords", FAIL,
                f"{len(matched)} matched; stuffed past {2 * cap}x: {', '.join(egregious)}")
    elif mild:
        rep.add("Keywords", WARN,
                f"{len(matched)} matched (target {lo}-{hi}); slightly over {cap}x cap: "
                + ", ".join(mild))
    elif len(matched) < lo:
        rep.add("Keywords", WARN, f"only {len(matched)} JD terms matched, target {lo}-{hi}")
    else:
        rep.add("Keywords", PASS, f"{len(matched)} JD terms matched, none over {cap}x cap")


def check_folder(rep, folder, cfg):
    allowed = cfg.get("allowed_globs", [])
    junk = cfg.get("junk_globs", [])
    names = sorted(os.listdir(folder))
    found_junk = [n for n in names
                  if any(glob.fnmatch.fnmatch(n, g) for g in junk)]
    stray = [n for n in names
             if not any(glob.fnmatch.fnmatch(n, g) for g in allowed)
             and n not in found_junk and not n.startswith(".")]
    if found_junk:
        rep.add("Folder hygiene", FAIL, f"build junk present: {', '.join(found_junk[:5])}")
    elif stray:
        rep.add("Folder hygiene", WARN, f"unexpected files: {', '.join(stray[:5])}")
    else:
        rep.add("Folder hygiene", PASS, f"{len(names)} files, deliverables only")

    if cfg.get("require_webloc", True):
        has = any(n.endswith(".webloc") for n in names)
        rep.add("Webloc", PASS if has else WARN,
                "posting shortcut present" if has else "no .webloc shortcut in folder")


# --------------------------------------------------------------------------
# driver
# --------------------------------------------------------------------------

def load_config(config_path, profile_dir):
    """Merge the policy layer with the identity layer.

    `config/documents.json` is publishable policy: page caps, format rules,
    thresholds. `profile/` is the user's identity: their canonical link table
    and their never-claim guardrails. Keeping them in separate files is what
    lets the engine ship without carrying anyone's career in it.

    A missing profile is not an error - the checker degrades to the checks that
    do not need one, so a fresh install runs before the user has authored
    anything. Checks that lose their data SKIP with a reason rather than pass
    silently, because a guardrail that quietly does nothing is worse than none.
    """
    if not os.path.exists(config_path):
        sys.exit(f"config not found: {config_path}\nCreate it or pass --config.")
    with open(config_path) as f:
        cfg = json.load(f)

    cfg.setdefault("links", {})
    links_path = os.path.join(profile_dir, "links.json")
    if os.path.exists(links_path):
        with open(links_path) as f:
            profile_links = json.load(f)
        cfg["links"]["canonical"] = profile_links.get("canonical", {})
        cfg["links"]["deny_substrings"] = profile_links.get("deny_substrings", [])
    else:
        cfg["links"]["canonical"] = None  # signals "no profile" to check_links

    rails_path = os.path.join(profile_dir, "guardrails.json")
    if os.path.exists(rails_path):
        with open(rails_path) as f:
            cfg["guardrails"] = json.load(f).get("guardrails", [])
    else:
        cfg["guardrails"] = []

    cfg["_profile_dir"] = profile_dir
    cfg["_has_profile"] = os.path.exists(links_path) or os.path.exists(rails_path)
    return cfg


def find_package(folder, cfg):
    """Locate the CV and cover-letter DOCX/PDF pairs inside a job folder."""
    out = {}
    for kind, marker in (("cv", cfg["cv_marker"]), ("cl", cfg["cover_letter_marker"])):
        for ext in ("docx", "pdf"):
            hits = sorted(glob.glob(os.path.join(folder, f"*{marker}*.{ext}")))
            hits = [h for h in hits if not os.path.basename(h).startswith("~$")]
            out[f"{kind}_{ext}"] = hits[-1] if hits else None
    return out


def audit(folder=None, cv=None, jd=None, config_path=DEFAULT_CONFIG,
          profile_dir=DEFAULT_PROFILE):
    cfg = load_config(config_path, profile_dir)
    rep = Report()
    jd_text = open(jd).read() if jd and os.path.exists(jd) else None

    if cv:
        pkg = {"cv_docx": cv,
               "cv_pdf": os.path.splitext(cv)[0] + ".pdf",
               "cl_docx": None, "cl_pdf": None}
    else:
        pkg = find_package(folder, cfg)

    if not pkg["cv_docx"]:
        rep.add("CV present", FAIL, "no CV .docx found in folder")
        return rep, cfg

    cv_doc = Docx(pkg["cv_docx"])
    geom = cv_doc.page_geometry()

    check_length(rep, pkg["cv_pdf"], cfg["cv_page_cap"], "CV", geom)
    check_dashes(rep, cv_doc, "CV")
    check_font(rep, cv_doc, cfg["font"], "CV")
    check_dates(rep, cv_doc, cfg)
    check_chronology(rep, cv_doc, cfg)
    check_structure(rep, cv_doc, cfg)
    check_bullets(rep, cv_doc, cfg)
    check_links(rep, cv_doc, cfg["links"])
    check_facts(rep, cv_doc, cfg.get("guardrails", []), "CV")
    check_keywords(rep, cv_doc, jd_text, cfg["keywords"])

    if pkg["cl_docx"]:
        cl_doc = Docx(pkg["cl_docx"])
        check_length(rep, pkg["cl_pdf"], cfg["cover_letter_page_cap"], "Letter",
                     cl_doc.page_geometry())
        check_dashes(rep, cl_doc, "Letter")
        check_font(rep, cl_doc, cfg["font"], "Letter")
        check_facts(rep, cl_doc, cfg.get("guardrails", []), "Letter")
    else:
        rep.add("Letter present", FAIL if not cv else SKIP, "no cover letter .docx found")

    for kind in ("cv", "cl"):
        if pkg[f"{kind}_docx"] and not (pkg[f"{kind}_pdf"] and os.path.exists(pkg[f"{kind}_pdf"])):
            rep.add(f"{kind.upper()} PDF", FAIL, "DOCX present but PDF missing")

    files = [p for p in pkg.values() if p and os.path.exists(p)]
    check_filenames(rep, files, cfg["filename_pattern"], cfg["filename_max_len"])

    if folder:
        check_folder(rep, folder, cfg["folder"])

    return rep, cfg


def main():
    ap = argparse.ArgumentParser(description="Pre-delivery auditor for a CV package.")
    ap.add_argument("folder", nargs="?", help="job folder to audit")
    ap.add_argument("--cv", help="audit a single CV .docx instead of a folder")
    ap.add_argument("--jd", help="JD text file, enables keyword checks")
    ap.add_argument("--config", default=DEFAULT_CONFIG,
                    help="policy layer (default: config/documents.json)")
    ap.add_argument("--profile", default=DEFAULT_PROFILE,
                    help="identity layer (default: profile/)")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of a table")
    args = ap.parse_args()

    if not args.folder and not args.cv:
        ap.error("give a job folder or --cv")

    rep, cfg = audit(args.folder, args.cv, args.jd, args.config, args.profile)

    if args.json:
        print(json.dumps(rep.rows, indent=2))
    else:
        target = args.cv or args.folder
        print(f"\n{os.path.basename(os.path.normpath(target))}")
        if not cfg.get("_has_profile"):
            print(f"  (no profile at {cfg['_profile_dir']} - identity checks skipped)")
        print(rep.render())
        counts = Counter(r["status"] for r in rep.rows)
        print(f"\n  {counts[PASS]} pass · {counts[WARN]} warn · "
              f"{counts[FAIL]} fail · {counts[SKIP]} skipped\n")

    return 1 if rep.failed else 0


if __name__ == "__main__":
    sys.exit(main())
