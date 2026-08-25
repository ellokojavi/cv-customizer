#!/usr/bin/env python3
"""Assemble the shippable subset into a clean tree, refusing on any leak.

    python3 engine/lib/publish.py --to ../cv-customizer [--check-only]

Two jobs, and the second is the important one.

**Assemble.** Copy only the person-agnostic layers: engine/, the .example
configs, profile.example/, the commands, and the public docs. Never profile/,
never config/*.json holding live values, never _registry/, never an
application folder.

**Refuse.** Scan every assembled file against the identity terms in
`config/publish_denylist.json` and exit non-zero on any hit. The scan reads
INSIDE .docx and .pdf, because a text grep cannot see either and the templates
are both. That is not hypothetical: the templates were verified clean only by
unzipping the DOCX and extracting the PDF text.

Note what this tool does NOT do: push. The public repository must be a FRESH
`git init`, never a subtree split of the private one - filtering paths does not
filter commit messages, and the private history names people, employers, and
figures in text no path filter will ever touch.
"""

import argparse
import json
import os
import re
import shutil
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))

# What ships. Everything else is excluded by omission, which is the safe default.
INCLUDE = [
    ("README.md", "README.md"),
    ("QUICKSTART.md", "QUICKSTART.md"),
    ("LICENSE", "LICENSE"),
    ("engine", "engine"),
    ("profile.example", "profile.example"),
    (".claude/commands", ".claude/commands"),
    (".claude/settings.example.json", ".claude/settings.example.json"),
]
INCLUDE_GLOBS = [("config", "config", "*.example.json")]

# Never copied, even if they appear under an included directory.
SKIP_NAMES = {".DS_Store", "__pycache__", ".git"}
SKIP_SUFFIX = (".pyc", ".tmp", ".bak")

GITIGNORE = """# Your data. None of this belongs in the product repo.
profile/
_registry/
state/

# Your live config - copy the .example files and edit those.
config/*.json
!config/*.example.json

# Your applications
[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9] */

# Local runtime config (holds absolute machine paths)
.claude/settings.json
.claude/settings.local.json

# Build junk. pdftoppm prefixes its output, hence the leading wildcard.
.~lock.*#
lu*.tmp
*.tmp
*page-*.jpg
*page-*.jpeg
*page-*.png
~$*
.DS_Store
__pycache__/
*.pyc
"""


def text_of(path):
    """Readable text for scanning, including inside .docx and .pdf."""
    low = path.lower()
    try:
        if low.endswith(".docx"):
            z = zipfile.ZipFile(path)
            out = []
            for name in z.namelist():
                if name.endswith(".xml") or name.endswith(".rels"):
                    out.append(z.read(name).decode("utf-8", "ignore"))
            return "\n".join(out)
        if low.endswith(".pdf"):
            try:
                import pymupdf
            except ImportError:
                return None          # cannot verify -> treated as a failure
            doc = pymupdf.open(path)
            return "\n".join(p.get_text() for p in doc)
        with open(path, encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception:
        return None


def scan(tree, terms):
    """[(relpath, [terms found])] plus files that could not be read."""
    rx = re.compile("|".join(terms), re.IGNORECASE)
    hits, unreadable = [], []
    for base, dirs, files in os.walk(tree):
        dirs[:] = [d for d in dirs if d not in SKIP_NAMES]
        for fn in sorted(files):
            path = os.path.join(base, fn)
            rel = os.path.relpath(path, tree)
            body = text_of(path)
            if body is None:
                unreadable.append(rel)
                continue
            found = sorted({m.group(0).lower() for m in rx.finditer(body)})
            if found:
                hits.append((rel, found))
    return hits, unreadable


def copy_tree(dest):
    for src_rel, dst_rel in INCLUDE:
        src = os.path.join(ROOT, src_rel)
        dst = os.path.join(dest, dst_rel)
        if not os.path.exists(src):
            sys.exit(f"missing required path: {src_rel}")
        if os.path.isdir(src):
            shutil.copytree(
                src, dst, dirs_exist_ok=True,
                ignore=lambda d, names: [
                    n for n in names
                    if n in SKIP_NAMES or n.endswith(SKIP_SUFFIX)
                ],
            )
        else:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)

    import glob
    for src_rel, dst_rel, pattern in INCLUDE_GLOBS:
        os.makedirs(os.path.join(dest, dst_rel), exist_ok=True)
        for src in glob.glob(os.path.join(ROOT, src_rel, pattern)):
            shutil.copy2(src, os.path.join(dest, dst_rel, os.path.basename(src)))

    with open(os.path.join(dest, ".gitignore"), "w") as f:
        f.write(GITIGNORE)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--to", required=True, help="destination directory")
    ap.add_argument("--denylist", default=os.path.join(ROOT, "config", "publish_denylist.json"))
    ap.add_argument("--check-only", action="store_true",
                    help="scan an existing tree without rebuilding it")
    ap.add_argument("--force", action="store_true", help="overwrite a non-empty destination")
    args = ap.parse_args()

    terms = json.load(open(args.denylist))["terms"]
    dest = os.path.abspath(args.to)

    if not args.check_only:
        if os.path.exists(dest) and os.listdir(dest) and not args.force:
            keep = os.path.join(dest, ".git")
            others = [n for n in os.listdir(dest) if n != ".git"]
            if others and not args.force:
                sys.exit(f"{dest} is not empty (use --force to overwrite its contents)")
            _ = keep
        os.makedirs(dest, exist_ok=True)
        copy_tree(dest)
        n = sum(len(f) for _, _, f in os.walk(dest))
        print(f"assembled {n} files into {dest}")

    hits, unreadable = scan(dest, terms)

    if unreadable:
        print(f"\nCOULD NOT READ {len(unreadable)} file(s) - cannot certify these:")
        for r in unreadable:
            print(f"   {r}")

    if hits:
        print(f"\nREFUSING TO PUBLISH - identity terms found in {len(hits)} file(s):")
        for rel, found in hits:
            print(f"   {rel}: {', '.join(found)}")
        print("\nMove the offending content to profile/ or config/, then re-run.")
        return 1

    if unreadable:
        print("\nUnreadable files block publication. Install pymupdf, or remove them.")
        return 1

    print(f"\nleak scan CLEAN against {len(terms)} identity terms "
          f"(read inside .docx and .pdf, not just text files)")
    print("Public repo must be a FRESH git init - never a subtree split of the private one.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
