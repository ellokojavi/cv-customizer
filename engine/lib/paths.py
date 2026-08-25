"""Project path resolution, shared by the engine's CLI tools.

Code lives in `engine/lib/`. **State does not.** The registry CSV, the per-board
scan state, and the application folders belong to the user, not the engine, and
must survive `engine/` being replaced wholesale on an upgrade.

That separation is the whole reason this module exists. Resolving state relative
to `__file__` - the obvious thing - would drag the user's data along with the
code the moment the code moves.

Override the state location with CV_STATE_DIR if you keep it elsewhere.
"""

import os

# Files that mark the project root. CLAUDE.md is the entry point; config/ and
# engine/ are structural. Any one is enough.
_ROOT_MARKERS = ("CLAUDE.md", "config", "engine")


def find_project_root(start=None):
    """Walk up from `start` until a directory looks like the project root.

    Falls back to two levels above this file (engine/lib/ -> root), which is
    correct for a normal checkout and keeps the tools working even if they are
    invoked from somewhere unexpected.
    """
    here = os.path.dirname(os.path.abspath(__file__))
    default = os.path.abspath(os.path.join(here, "..", ".."))

    cur = os.path.abspath(start or here)
    while True:
        if sum(os.path.exists(os.path.join(cur, m)) for m in _ROOT_MARKERS) >= 2:
            return cur
        parent = os.path.dirname(cur)
        if parent == cur:          # hit the filesystem root
            return default
        cur = parent


PROJECT_ROOT = find_project_root()

# User state. Kept out of engine/ so `engine/` stays disposable.
STATE_DIR = os.environ.get("CV_STATE_DIR") or os.path.join(PROJECT_ROOT, "_registry")
CSV_PATH = os.path.join(STATE_DIR, "processed_jobs.csv")
SEEN_JOBS_DIR = os.path.join(STATE_DIR, "seen_jobs")

# Config and identity layers.
CONFIG_DIR = os.path.join(PROJECT_ROOT, "config")
PROFILE_DIR = os.path.join(PROJECT_ROOT, "profile")


def version():
    """The engine's version string, or 'unknown' outside a checkout."""
    try:
        with open(os.path.join(PROJECT_ROOT, "VERSION")) as f:
            return f.read().strip()
    except OSError:
        return "unknown"


def ensure_state_dirs():
    """Create the state directories if this is a fresh install."""
    os.makedirs(STATE_DIR, exist_ok=True)
    os.makedirs(SEEN_JOBS_DIR, exist_ok=True)
