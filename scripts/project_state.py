"""
Check and manage project documentation state.

Usage:
    python project_state.py check  <reponame>                        # -> JSON {scan, reason, ...}
    python project_state.py read   <reponame>                        # -> JSON state or NOT_FOUND
    python project_state.py write  <reponame> <last_commit> <stack>  # -> JSON {written, state}

check gates (all must pass for scan=true):
    1. git repo present
    2. git remote exists
    3. at least one commit
    then Option B weekly logic:
    - no state      → scan=true  (first time)
    - age < 7 days  → scan=false (silent skip)
    - age >= 7 days, same HEAD → scan=false
    - age >= 7 days, new HEAD  → scan=true (offer refresh)
"""

import json
import pathlib
import subprocess
import sys
from datetime import datetime, timezone

SCAN_INTERVAL_DAYS = 7


def state_path(reponame):
    return pathlib.Path.home() / "config" / ".m-agent-skills" / reponame / "project-state.json"


def load_state(reponame):
    p = state_path(reponame)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.returncode, r.stdout.strip()


def cmd_check(reponame):
    # Gate 1: git repo
    rc, _ = run(["git", "rev-parse", "--show-toplevel"])
    if rc != 0:
        print(json.dumps({"scan": False, "reason": "not a git repo"}))
        return

    # Gate 2: remote exists (docs scan skipped without remote — caller should surface this)
    rc, _ = run(["git", "remote", "get-url", "origin"])
    if rc != 0:
        print(json.dumps({"scan": False, "reason": "no git remote"}))
        return

    # Gate 3: at least one commit
    rc, head = run(["git", "rev-parse", "HEAD"])
    if rc != 0:
        print(json.dumps({"scan": False, "reason": "no commits yet"}))
        return

    state = load_state(reponame)

    # No state → first time → scan
    if state is None:
        print(json.dumps({"scan": True, "reason": "no project docs yet", "head": head}))
        return

    # Parse age
    generated_at = state.get("generated_at", "")
    try:
        generated = datetime.fromisoformat(generated_at.replace("Z", "+00:00"))
        age_days = (datetime.now(timezone.utc) - generated).days
    except Exception:
        age_days = 999

    # Within interval → silent skip
    if age_days < SCAN_INTERVAL_DAYS:
        print(json.dumps({
            "scan": False,
            "reason": f"docs are {age_days}d old, within {SCAN_INTERVAL_DAYS}d window"
        }))
        return

    # Older than interval — check HEAD
    last_commit = state.get("last_commit", "")
    if last_commit == head:
        print(json.dumps({
            "scan": False,
            "reason": f"docs are {age_days}d old but no commits since last scan"
        }))
        return

    # Stale + new commits → offer refresh
    print(json.dumps({
        "scan": True,
        "reason": f"docs are {age_days}d old and repo has changed since last scan",
        "head": head,
        "age_days": age_days,
        "last_commit": last_commit
    }))


def cmd_read(reponame):
    state = load_state(reponame)
    if state is None:
        print("NOT_FOUND")
    else:
        print(json.dumps(state, indent=2))


def cmd_write(reponame, last_commit, stack_csv):
    p = state_path(reponame)
    p.parent.mkdir(parents=True, exist_ok=True)
    state = {
        "reponame": reponame,
        "project_doc": str(p.parent / "project.md"),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "last_commit": last_commit,
        "stack": [s.strip() for s in stack_csv.split(",") if s.strip()],
    }
    p.write_text(json.dumps(state, indent=2), encoding="utf-8")
    print(json.dumps({"written": str(p), "state": state}, indent=2))


if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) < 2:
        print(__doc__)
        sys.exit(1)

    cmd, reponame = args[0], args[1]

    if cmd == "check":
        cmd_check(reponame)
    elif cmd == "read":
        cmd_read(reponame)
    elif cmd == "write":
        if len(args) < 4:
            print("ERROR: write requires <reponame> <last_commit> <stack_csv>", file=sys.stderr)
            sys.exit(1)
        cmd_write(reponame, args[2], args[3])
    else:
        print(f"ERROR: unknown command '{cmd}'", file=sys.stderr)
        sys.exit(1)
