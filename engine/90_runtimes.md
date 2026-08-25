# 90 — Runtimes

The rules are identical everywhere; only the plumbing differs. Check which environment you are in
before assuming a capability.

---

## Claude Code (primary)

Launched with `claude` from the project root. `CLAUDE.md` and its `@` imports load automatically.

A real local shell: `rm`, `soffice`, `pdftoppm`, and `python3` all operate directly on the files.
No bridge, no staging, no size caps. Files are written in place — there is nothing to "deliver,"
so say where the file is rather than presenting it.

Browser automation requires a subscription login. An API key or auth token silently disables both
the browser and any connectors, which presents as tools simply being absent rather than as an
error. Check the active credential first when browsing stops working.

Scheduled runs are OS-level jobs invoking the CLI headlessly.

## Bridged / desktop runtimes (legacy)

The folder is reached over a device bridge. Three consequences that change how you work:

- **Deletion may be unavailable.** Junk has to be moved to a staging directory for the user to
  remove by hand. Prevention matters more here than anywhere else.
- **Files are staged in and committed back** rather than edited in place.
- **Deliverables reach the user through a file card**, not a path.

Fetching board JSON may be blocked by a provenance allowlist that refuses URLs not already seen
in a prior result. Where that applies, fetch through the browser's scripting tool instead. Under
a real shell, try a direct fetch first and fall back to the browser only if blocked.

---

## The single-writer rule

**This is the one thing that actually breaks.**

The registry CSV and the per-board scan state have **no merge logic**. If two runtimes both run
searches against the same folder, the copies diverge silently and logged postings are lost — with
no error, no conflict marker, and no way to tell which side is correct afterwards.

**Exactly one runtime may have scheduled jobs enabled at a time.** Before enabling them in one,
disable them in the other. Verify rather than assume; a scheduled job that was set up months ago
and forgotten is exactly the one that will corrupt the registry.

The same applies to a synced copy of the folder: two machines running searches against a synced
directory is the same failure with extra steps.

---

## Sync and backup

Mirroring finished packages to cloud storage belongs to a file-level sync tool on a timer, not to
the model. Hand-uploading through a connector was tried and failed badly: an audit found one of
nineteen folders correctly mirrored, with several partial and two files corrupted in transit —
one expanded, one truncated mid-transfer.

The general lesson is worth keeping: **a model moving binary files one at a time will silently
lose some.** Checksum-verified file sync is the right tool, costs nothing per run, and can
backfill history in one pass.
