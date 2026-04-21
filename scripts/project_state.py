"""
Repo-scoped project state. Computed once per session, bound to a variable;
file reads only (no gh, no network). Shell work limited to cheap git
identity probes that derive reponame + branch.

Usage:
    python project_state.py snapshot <project_root>                  # -> full project state JSON
    python project_state.py check    <reponame>                      # -> JSON {scan, reason, ...}
    python project_state.py read     <reponame>                      # -> JSON state or NOT_FOUND
    python project_state.py write    <reponame> <last_commit> <stack_csv>

snapshot returns: reponame, owner_repo, branch, huddle paths, project
doc freshness, cross-branch context, raw events pending synthesis, and
the currently saved huddle state.

check gates (all must pass for scan=true):
    1. git repo present
    2. git remote exists
    3. at least one commit
    then Option B weekly logic:
    - no state      -> scan=true  (first time)
    - age < 7 days  -> scan=false (silent skip)
    - age >= 7 days, same HEAD -> scan=false
    - age >= 7 days, new HEAD  -> scan=true (offer refresh)
"""

import json
import os
import pathlib
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

SCAN_INTERVAL_DAYS = 7
CONFIG_ROOT = pathlib.Path.home() / ".config" / "muthuishere-agent-skills"
PRIORITY_BRANCHES = ("main", "master", "dev", "develop")
MAX_CROSS_BRANCH = 4


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

def state_path(reponame):
    return CONFIG_ROOT / reponame / "project-state.json"


def repo_config_path(reponame):
    return CONFIG_ROOT / reponame / "config.json"


def _sanitize_branch(branch):
    return branch.replace("/", "-").lstrip(".") or "unknown-branch"


def huddle_dir(reponame, branch):
    return CONFIG_ROOT / reponame / _sanitize_branch(branch) / "huddle"


# ---------------------------------------------------------------------------
# IO helpers
# ---------------------------------------------------------------------------

def run(cmd, cwd=None, timeout=10):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, timeout=timeout)
        return r.returncode, r.stdout.strip()
    except Exception:
        return 1, ""


def _load_json(path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def load_state(reponame):
    return _load_json(state_path(reponame))


def _load_repo_config(reponame):
    return _load_json(repo_config_path(reponame)) or {}


# ---------------------------------------------------------------------------
# Scan decision (used by `check` + `snapshot`)
# ---------------------------------------------------------------------------

def evaluate_scan(reponame, *, has_git_repo, has_remote, head):
    """Pure decision function. Callers pass pre-fetched git info so we avoid
    redundant subprocess calls.
    """
    if not has_git_repo:
        return {"scan": False, "reason": "not a git repo"}
    if not has_remote:
        return {"scan": False, "reason": "no git remote"}
    if not head:
        return {"scan": False, "reason": "no commits yet"}

    state = load_state(reponame)
    if state is None:
        return {"scan": True, "reason": "no project docs yet", "head": head}

    generated_at = state.get("generated_at", "")
    try:
        generated = datetime.fromisoformat(generated_at.replace("Z", "+00:00"))
        age_days = (datetime.now(timezone.utc) - generated).days
    except Exception:
        age_days = 999

    if age_days < SCAN_INTERVAL_DAYS:
        return {
            "scan": False,
            "reason": f"docs are {age_days}d old, within {SCAN_INTERVAL_DAYS}d window",
        }

    last_commit = state.get("last_commit", "")
    if last_commit == head:
        return {
            "scan": False,
            "reason": f"docs are {age_days}d old but no commits since last scan",
        }

    return {
        "scan": True,
        "reason": f"docs are {age_days}d old and repo has changed since last scan",
        "head": head,
        "age_days": age_days,
        "last_commit": last_commit,
    }


# ---------------------------------------------------------------------------
# Helpers for snapshot
# ---------------------------------------------------------------------------

EMPTY_STATE = {
    "reponame": "",
    "branch": "",
    "last_huddle_date": "",
    "current_topic": "",
    "open_questions": [],
    "action_items": [],
    "latest_summary": "",
    "active_personas": [],
    "decisions": [],
    "participants": [],
    "key_moments": [],
}


def _parse_owner_repo(remote_url):
    m = re.search(r"[:/]([^/]+)/([^/]+?)(?:\.git)?$", remote_url or "")
    if not m:
        return "", ""
    return m.group(2), f"{m.group(1)}/{m.group(2)}"


DOC_MARKERS = (
    "README.md", "README.rst", "README.txt", "README",
    "CLAUDE.md", "AGENTS.md", "CONTRIBUTING.md", "ARCHITECTURE.md",
)
DOC_DIRS = ("docs", "documentation", "doc")
DOC_MIN_BYTES = 200


def _detect_existing_docs(project_root):
    """Return list of relative paths of docs that actually exist and have
    non-trivial content. Used to decide whether Deepak should offer to
    generate project docs or just use what's there."""
    root = pathlib.Path(project_root)
    found = []

    for name in DOC_MARKERS:
        p = root / name
        if p.is_file() and p.stat().st_size >= DOC_MIN_BYTES:
            found.append(name)

    for dirname in DOC_DIRS:
        d = root / dirname
        if not d.is_dir():
            continue
        for md in d.rglob("*.md"):
            if md.is_file() and md.stat().st_size >= DOC_MIN_BYTES:
                found.append(str(md.relative_to(root)))
                break

    return found


def _has_enough_files(project_root, threshold=20):
    if not os.path.isdir(project_root):
        return False
    count = 0
    for entry in os.scandir(project_root):
        if entry.name == ".git":
            continue
        if entry.is_file(follow_symlinks=False):
            count += 1
        elif entry.is_dir(follow_symlinks=False):
            try:
                for sub in os.scandir(entry.path):
                    if sub.is_file(follow_symlinks=False):
                        count += 1
                        if count >= threshold:
                            return True
            except PermissionError:
                pass
        if count >= threshold:
            return True
    return False


def _latest_summary(note_path):
    try:
        text = note_path.read_text(encoding="utf-8")
    except Exception:
        return ""
    summary, in_section = "", False
    for line in text.splitlines():
        if line.startswith("## Latest Summary"):
            in_section = True
            continue
        if in_section:
            if line.startswith("## "):
                break
            if line.strip():
                summary += line.strip() + " "
    return summary.strip()


def _scan_cross_branch(reponame, current_branch):
    repo_dir = CONFIG_ROOT / reponame
    if not repo_dir.is_dir():
        return []
    current_safe = _sanitize_branch(current_branch)
    entries = []
    for child in repo_dir.iterdir():
        if not child.is_dir() or child.name == current_safe:
            continue
        hdir = child / "huddle"
        if not hdir.is_dir():
            continue
        notes = sorted(hdir.glob("????-??-??.md"), reverse=True)
        if not notes:
            continue
        entries.append({
            "branch": child.name,
            "date": notes[0].stem,
            "summary": _latest_summary(notes[0]),
        })

    def sort_key(e):
        idx = PRIORITY_BRANCHES.index(e["branch"]) if e["branch"] in PRIORITY_BRANCHES else len(PRIORITY_BRANCHES)
        return (idx, e["branch"])

    entries.sort(key=sort_key)
    return entries[:MAX_CROSS_BRANCH]


def _list_raw_events(reponame, branch):
    raw_dir = huddle_dir(reponame, branch) / "raw"
    if not raw_dir.is_dir():
        return []
    out = []
    for p in sorted(raw_dir.glob("*.json")):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            data = {}
        out.append({
            "file": p.name,
            "kind": data.get("kind") or data.get("type") or "",
            "ts": data.get("ts", ""),
        })
    return out


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_snapshot(project_root_str):
    project_root = str(pathlib.Path(project_root_str).resolve())
    folder_name = pathlib.Path(project_root).name
    cached = _load_repo_config(folder_name)

    with ThreadPoolExecutor(max_workers=4) as pool:
        f_branch   = pool.submit(run, ["git", "branch", "--show-current"], project_root)
        f_remote   = pool.submit(run, ["git", "remote", "get-url", "origin"], project_root) if not cached.get("reponame") else None
        f_head     = pool.submit(run, ["git", "rev-parse", "HEAD"], project_root)
        f_toplevel = pool.submit(run, ["git", "rev-parse", "--show-toplevel"], project_root)

    rc, branch = f_branch.result()
    if rc != 0 or not branch:
        branch = cached.get("local_branch", "main")

    if cached.get("reponame"):
        reponame = cached["reponame"]
        owner_repo = cached.get("owner_repo", "")
    else:
        rc, remote_url = f_remote.result()
        if rc == 0 and remote_url:
            reponame, owner_repo = _parse_owner_repo(remote_url)
            if not reponame:
                reponame = folder_name
        else:
            reponame, owner_repo = folder_name, ""

    rc, _ = f_toplevel.result()
    has_git_repo = rc == 0
    rc, head = f_head.result()
    if rc != 0:
        head = ""

    # Persist cache
    repo_config = _load_repo_config(reponame) or cached
    dirty = False
    if not repo_config.get("reponame"):
        repo_config["reponame"] = reponame
        dirty = True
    if owner_repo and not repo_config.get("owner_repo"):
        repo_config["owner_repo"] = owner_repo
        dirty = True
    if dirty:
        _save_json(repo_config_path(reponame), repo_config)

    scan = evaluate_scan(
        reponame,
        has_git_repo=has_git_repo,
        has_remote=bool(owner_repo),
        head=head,
    )
    project_doc_file = CONFIG_ROOT / reponame / "project-state.json"
    existing_docs = _detect_existing_docs(project_root)
    doc_missing = bool(
        scan.get("scan")
        and not project_doc_file.exists()
        and _has_enough_files(project_root)
        and not existing_docs
    )

    hdir = huddle_dir(reponame, branch)
    state_file = hdir / "huddle-state.json"
    saved_state = _load_json(state_file)
    if saved_state is None:
        saved_state = dict(EMPTY_STATE, reponame=reponame, branch=branch)

    return {
        "reponame": reponame,
        "owner_repo": owner_repo,
        "branch": branch,
        "has_git_repo": has_git_repo,
        "huddle_dir": str(hdir),
        "huddle_state_file": str(state_file),
        "project_doc_file": str(project_doc_file),
        "project_scan": scan,
        "project_doc_missing": doc_missing,
        "project_docs_found": existing_docs,
        "saved_state": saved_state,
        "raw_events": _list_raw_events(reponame, branch),
        "cross_branch_context": _scan_cross_branch(reponame, branch),
    }


def cmd_check(reponame, cwd=None):
    rc, _ = run(["git", "rev-parse", "--show-toplevel"], cwd=cwd)
    has_git_repo = rc == 0
    has_remote = False
    head = ""
    if has_git_repo:
        rc, _ = run(["git", "remote", "get-url", "origin"], cwd=cwd)
        has_remote = rc == 0
        rc, head = run(["git", "rev-parse", "HEAD"], cwd=cwd)
        if rc != 0:
            head = ""
    print(json.dumps(evaluate_scan(
        reponame, has_git_repo=has_git_repo, has_remote=has_remote, head=head,
    )))


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
    if not args:
        print(__doc__)
        sys.exit(1)

    cmd = args[0]

    if cmd == "snapshot":
        if len(args) < 2:
            print("ERROR: snapshot requires <project_root>", file=sys.stderr)
            sys.exit(1)
        print(json.dumps(cmd_snapshot(args[1]), indent=2))
    elif cmd == "check":
        if len(args) < 2:
            print("ERROR: check requires <reponame>", file=sys.stderr)
            sys.exit(1)
        cmd_check(args[1])
    elif cmd == "read":
        if len(args) < 2:
            print("ERROR: read requires <reponame>", file=sys.stderr)
            sys.exit(1)
        cmd_read(args[1])
    elif cmd == "write":
        if len(args) < 4:
            print("ERROR: write requires <reponame> <last_commit> <stack_csv>", file=sys.stderr)
            sys.exit(1)
        cmd_write(args[1], args[2], args[3])
    else:
        print(f"ERROR: unknown command '{cmd}'", file=sys.stderr)
        sys.exit(1)
