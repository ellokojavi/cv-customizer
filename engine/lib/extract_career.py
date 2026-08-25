#!/usr/bin/env python3
"""Extract a structured career record from an existing CV .docx.

    python3 engine/lib/extract_career.py <cv.docx> [-o profile/career.json]

The generator needs the candidate's history as data, not as a formatted
document. Retyping it by hand would introduce exactly the drift the generator
exists to prevent, so derive it from a CV that already passed the auditor and
diff the result.

What it does NOT do: judge, rewrite, or improve anything. Bullets come out
verbatim. Tailoring happens later, against a known-good baseline.
"""

import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from check_cv import Docx  # noqa: E402

BULLET_STYLE = "ListParagraph"


def _split_dated(text):
    """'Role Title\\tMon YYYY - Mon YYYY' -> ('Role Title', 'Mon YYYY - Mon YYYY')."""
    left, _, right = text.partition("\t")
    return left.strip(), right.strip()


def extract(path, headings):
    doc = Docx(path)
    paras = doc.paragraphs
    heads = {v: k for k, v in headings.items()}

    out = {
        "header": {"name": "", "contact_line": ""},
        "summary": "",
        "competencies": [],
        "experience": [],
        "education": [],
        "additional": [],
    }

    # Header is everything before the first known section heading.
    first = next((i for i, p in enumerate(paras) if p["text"].strip() in heads), len(paras))
    header = [p["text"].strip() for p in paras[:first] if p["text"].strip()]
    if header:
        out["header"]["name"] = header[0]
    if len(header) > 1:
        out["header"]["contact_line"] = header[1]

    section, role = None, None
    for p in paras[first:]:
        text = p["text"].strip()
        if not text:
            continue
        if text in heads:
            section, role = heads[text], None
            continue

        is_bullet = (p["style"] or "").replace(" ", "") == BULLET_STYLE

        if section == "summary":
            out["summary"] = text

        elif section == "competencies":
            out["competencies"] = [c.strip() for c in re.split(r"\s*\|\s*", text) if c.strip()]

        elif section == "experience":
            if is_bullet:
                if role is not None:
                    role["bullets"].append(text)
            elif "\t" in text:
                title, dates = _split_dated(text)
                role = {"title": title, "dates": dates, "company": "",
                        "location": "", "bullets": []}
                out["experience"].append(role)
            elif role is not None and not role["company"]:
                # "Company, descriptor   Location" - split on the run of spaces
                parts = re.split(r"\s{2,}", text)
                role["company"] = parts[0].strip()
                role["location"] = parts[-1].strip() if len(parts) > 1 else ""

        elif section == "education":
            title, dates = _split_dated(text) if "\t" in text else (text, "")
            # Degree lines follow their institution; attach rather than orphan.
            if out["education"] and not out["education"][-1].get("detail"):
                out["education"][-1]["detail"] = title
                out["education"][-1]["location"] = dates
            else:
                out["education"].append({"institution": title, "date": dates,
                                         "detail": "", "location": ""})

        elif section == "additional":
            label, sep, body = text.partition(":")
            out["additional"].append(
                {"label": label.strip(), "text": body.strip()} if sep
                else {"label": "", "text": text}
            )

    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("cv", help="an existing CV .docx to extract from")
    ap.add_argument("-o", "--out", help="write JSON here instead of stdout")
    ap.add_argument("--config", help="config/documents.json, for section headings")
    args = ap.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    cfg_path = args.config or os.path.join(here, "..", "..", "config", "documents.json")
    order = json.load(open(cfg_path))["section_order"]
    # SUMMARY -> summary, CORE COMPETENCIES -> competencies, etc.
    keys = {"SUMMARY": "summary", "CORE COMPETENCIES": "competencies",
            "PROFESSIONAL EXPERIENCE": "experience", "EDUCATION": "education",
            "ADDITIONAL": "additional"}
    headings = {keys[h]: h for h in order if h in keys}

    data = extract(args.cv, headings)
    data["_source"] = os.path.basename(args.cv)
    data["_note"] = ("Extracted verbatim from a CV that passed the auditor. "
                     "Bullets are the master copy; tailoring edits a working "
                     "copy, never this file.")

    text = json.dumps(data, indent=2, ensure_ascii=False)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text + "\n")
        roles = len(data["experience"])
        bullets = sum(len(r["bullets"]) for r in data["experience"])
        print(f"wrote {args.out}: {roles} roles, {bullets} bullets, "
              f"{len(data['competencies'])} competencies, "
              f"{len(data['education'])} education entries")
    else:
        print(text)


if __name__ == "__main__":
    main()
