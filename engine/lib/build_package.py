#!/usr/bin/env python3
"""Build a complete application package and refuse to finish until it audits clean.

    python3 engine/lib/build_package.py --app app.json

One `app.json` drives the whole thing:

    {
      "company": "Acme",
      "role":    "Director of Product",
      "date":    "20260824",                     folder + filename prefix
      "url":     "https://acme.com/jobs/123",    optional, writes the .webloc
      "jd_file": "/tmp/cvbuild/jd.txt",          optional, enables keyword checks
      "tailor":  { … },                          optional CV overlay
      "letter":  { "paragraphs": [ … ] },        cover letter body
      "outreach":{ "hiring_manager": [ … ] }     optional research
    }

What it guarantees, and why each part exists:

- **Everything is generated into a scratch directory**, never the application
  folder. `soffice` and `pdftoppm` drop working files beside their input, and
  an application folder that ends up holding anything but deliverables is a bug
  in the build rather than something to tidy up afterwards.
- **`soffice` is checked before use.** It fails silently - no error, no exit
  code, no PDF - so a build can look successful while shipping half a package.
- **The audit is the exit condition.** If `check_cv.py` fails, this fails, and
  nothing is copied into the application folder. A package that does not audit
  clean should not exist to be sent by accident.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths  # noqa: E402
import check_cv  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))


def have_soffice():
    return shutil.which("soffice") or shutil.which("libreoffice")


def to_pdf(docx_path, outdir):
    exe = have_soffice()
    subprocess.run([exe, "--headless", "--convert-to", "pdf", "--outdir", outdir, docx_path],
                   check=False, capture_output=True)
    pdf = os.path.join(outdir, os.path.splitext(os.path.basename(docx_path))[0] + ".pdf")
    return pdf if os.path.exists(pdf) else None


def run(cmd):
    r = subprocess.run([sys.executable] + cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write(r.stdout + r.stderr)
        sys.exit(f"failed: {' '.join(cmd)}")
    return r.stdout.strip()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--app", required=True, help="the per-application JSON")
    ap.add_argument("--into", help="application folder (default: derived from company/role/date)")
    ap.add_argument("--config", default=os.path.join(paths.CONFIG_DIR, "documents.json"))
    ap.add_argument("--dry-run", action="store_true",
                    help="build and audit in scratch, but do not copy anything back")
    args = ap.parse_args()

    app = json.load(open(args.app))
    for key in ("company", "role"):
        if key not in app:
            sys.exit(f"--app is missing required key: {key}")

    if not have_soffice():
        sys.exit("soffice not found. DOCX to PDF conversion is required for a complete "
                 "package, and soffice fails silently rather than erroring, so this stops "
                 "here.\nInstall LibreOffice, then re-run.")

    cfg = json.load(open(args.config))
    identity = json.load(open(os.path.join(paths.PROFILE_DIR, "identity.json")))
    slug = identity["name"]["filename_slug"]
    date = app.get("date") or __import__("datetime").date.today().strftime("%Y%m%d")

    folder = args.into or os.path.join(
        paths.PROJECT_ROOT, f"{date} {app['company']} - {app['role']}"[:120])

    scratch = tempfile.mkdtemp(prefix="cvbuild-")
    cv_name = f"{date}_{slug}_CV_v1.docx"
    cl_name = f"{date}_{slug}_CoverLetter_v1.docx"
    made = []

    print(f"building in {scratch}")

    # --- CV ---------------------------------------------------------------
    cv_cmd = [os.path.join(HERE, "build_cv.py"), "-o", os.path.join(scratch, cv_name)]
    if app.get("tailor"):
        tp = os.path.join(scratch, "_tailor.json")
        json.dump(app["tailor"], open(tp, "w"))
        cv_cmd += ["--tailor", tp]
    print("  " + run(cv_cmd).splitlines()[0])
    made.append(cv_name)

    # --- cover letter -----------------------------------------------------
    if app.get("letter"):
        letter = dict(app["letter"])
        letter.setdefault("company", app["company"])
        letter.setdefault("role", app["role"])
        lp = os.path.join(scratch, "_letter.json")
        json.dump(letter, open(lp, "w"))
        print("  " + run([os.path.join(HERE, "build_cover_letter.py"),
                          "--letter", lp, "-o", os.path.join(scratch, cl_name)]).splitlines()[0])
        made.append(cl_name)
    else:
        print("  no letter block in --app, skipping the cover letter")

    # --- PDFs -------------------------------------------------------------
    for name in list(made):
        pdf = to_pdf(os.path.join(scratch, name), scratch)
        if not pdf:
            sys.exit(f"soffice produced no PDF for {name} - stopping rather than "
                     "shipping half a package")
        made.append(os.path.basename(pdf))
    print(f"  converted {len([m for m in made if m.endswith('.pdf')])} PDF(s)")

    # --- outreach plan ----------------------------------------------------
    if app.get("outreach"):
        plan = dict(app["outreach"])
        plan.setdefault("company", app["company"])
        plan.setdefault("role", app["role"])
        plan.setdefault("jd_url", app.get("url", "n/a"))
        pp = os.path.join(scratch, "_plan.json")
        json.dump(plan, open(pp, "w"))
        out_name = f"{date} outreach plan.md"
        print("  " + run([os.path.join(HERE, "build_outreach.py"),
                          "--plan", pp, "-o", os.path.join(scratch, out_name)]).splitlines()[0])
        made.append(out_name)

    # --- webloc -----------------------------------------------------------
    if app.get("url"):
        wl = f"{app['role']} - {app['company']}.webloc"[:120]
        with open(os.path.join(scratch, wl), "w") as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n'
                    '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" '
                    '"http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
                    '<plist version="1.0"><dict><key>URL</key>'
                    f'<string>{app["url"]}</string></dict></plist>\n')
        made.append(wl)

    # --- audit: the exit condition ----------------------------------------
    for junk in ("_tailor.json", "_letter.json", "_plan.json"):
        p = os.path.join(scratch, junk)
        if os.path.exists(p):
            os.remove(p)

    print("\naudit:")
    rep, _ = check_cv.audit(folder=scratch, jd=app.get("jd_file"), config_path=args.config)
    print(rep.render())

    if rep.failed:
        print(f"\nFAILED - nothing copied. The package is in {scratch} for inspection.")
        print("Fix the FAILs and re-run. A package that does not audit clean should not "
              "exist somewhere it can be sent by accident.")
        return 1

    if args.dry_run:
        print(f"\nclean, but --dry-run: left in {scratch}")
        return 0

    os.makedirs(folder, exist_ok=True)
    for name in made:
        shutil.copy2(os.path.join(scratch, name), os.path.join(folder, name))
    shutil.rmtree(scratch, ignore_errors=True)

    print(f"\ndelivered {len(made)} files to:\n  {folder}")
    print("\nlog it:  python3 engine/lib/registry.py add --company "
          f"\"{app['company']}\" --role \"{app['role']}\" --url \"{app.get('url','')}\" "
          "--source \"…\" --fit \"Strong\" --notes \"fit + honest gap\"")
    return 0


if __name__ == "__main__":
    sys.exit(main())
