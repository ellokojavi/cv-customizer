---
description: Sweep the project folder for junk, corrupt files, and structural rot
---

Sweep the project for build junk, damaged deliverables, and structural rot. The junk and
allowed-file patterns are defined once in `config/documents.json` → `folder`; use those
rather than a list retyped from memory, so this command and the auditor never disagree.

1. **Junk scan.** Find anything matching `folder.junk_globs` across all application folders.
   These come from the document toolchain: LibreOffice drops `.~lock.*#` and `lu*.tmp` beside
   its input, and `pdftoppm` drops render output beside its target — note the globs are
   `*page-*.jpg`, not `page-*.jpg`, because that output gets prefixed (`cvpage-1.jpg`).
   Report the count before and after.

2. **Integrity check — verify, do not assume.** `unzip -tqq` every DOCX (they are zip
   archives), and confirm every PDF starts with `%PDF-` and ends with an EOF marker.
   `~$*.docx` files are ~162-byte Word owner-locks and are the only things that routinely
   fail a zip test. They are junk, **not** damaged deliverables — never report one as a
   corrupt CV.

3. **Structural rot.** Application folders holding only a `.webloc` with no package ever
   built; the same role applied to twice under two dated folders; packages missing their
   PDF or DOCX half. Run the auditor across every folder to catch the last class
   mechanically:

   ```bash
   for d in <application folders>; do python3 engine/lib/check_cv.py "$d"; done
   ```

4. **Registry reconciliation.** `python3 engine/lib/registry.py sync`.

5. **Config and profile integrity.** Every file referenced by `profile/identity.json` →
   `source_documents` exists on disk; `profile/guardrail_tests.json` still passes via
   `python3 engine/lib/check_cv_tests.py`; every `config/` and `profile/` file parses as
   valid JSON.

**Prevention beats cleanup.** Every conversion and render belongs in a scratch directory,
never in the application folder — copy the DOCX to scratch, run the toolchain there, and
move only the finished PDF back. A folder that ends up containing anything other than
deliverables means a build skipped that rule.

Report what you found and what you changed. Ask before deleting anything not matched by
`folder.junk_globs`.
