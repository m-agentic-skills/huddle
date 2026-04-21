"""
Manage repo-scoped huddle state under ~/.config/muthuishere-agent-skills/{reponame}/{branch}/huddle/.

Usage:
    python meeting_state.py ensure <project_root> <date>

project_root  = absolute path to the user's project directory
date          = YYYY-MM-DD

Returns a single JSON blob with everything Claude needs to open the huddle.
All probes run in parallel. Claude reads next_action and acts — no extra shell calls needed.

next_action values:
  "deepak_doc_offer"  → project docs missing; Deepak must offer first, stop and wait
  "resume_summary"    → today's note has content; summarize and ask where to pick up
  "show_roster"       → fresh start; brief repo state, show roster, ask what to discuss
"""

import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone


# ---------------------------------------------------------------------------
# Python binary detection — resolved once, used everywhere
# ---------------------------------------------------------------------------

def detect_python_bin():
    """Return the first available Python 3 binary path, or None."""
    for name in ("python3", "python"):
        found = shutil.which(name)
        if found:
            return found
    return None


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

def skills_root():
    return pathlib.Path.home() / ".config" / "muthuishere-agent-skills"


def userconfig_path():
    return skills_root() / "userconfig.json"


def repo_dir(reponame):
    return skills_root() / reponame


def branch_dir(reponame, branch):
    safe = branch.replace("/", "-").lstrip(".") or "unknown-branch"
    return repo_dir(reponame) / safe


def huddle_dir(reponame, branch):
    return branch_dir(reponame, branch) / "huddle"


def huddle_state_path(reponame, branch):
    return huddle_dir(reponame, branch) / "huddle-state.json"


def huddle_note_path(reponame, branch, date_str):
    return huddle_dir(reponame, branch) / f"{date_str}.md"


# ---------------------------------------------------------------------------
# Repo identity — cached in config after first detection
# ---------------------------------------------------------------------------

def _run(cmd, cwd=None):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, timeout=10)
        return r.returncode, r.stdout.strip()
    except Exception:
        return 1, ""


def _detect_repo_name_and_owner(project_root):
    """Detect repo_name and owner_repo from git remote. Fallback to folder name."""
    root = str(project_root)
    rc, remote_url = _run(["git", "remote", "get-url", "origin"], cwd=root)
    if rc == 0 and remote_url:
        m = re.search(r"[:/]([^/]+)/([^/]+?)(?:\.git)?$", remote_url)
        if m:
            return m.group(2), f"{m.group(1)}/{m.group(2)}"
    return pathlib.Path(root).name, ""


def derive_repo_identity(project_root, cached_config=None):
    """Return (repo_name, owner_repo, branch, gh_available) from project_root.

    Uses cached_config values when available. Only branch is always fresh
    (it changes between sessions). repo_name, owner_repo, and gh_available
    are detected once and cached.
    """
    root = str(project_root)
    cfg = cached_config or {}

    # Branch — always fresh (changes between sessions)
    rc, branch = _run(["git", "branch", "--show-current"], cwd=root)
    if rc != 0 or not branch:
        branch = cfg.get("local_branch", "main")

    # repo_name + owner_repo — use cached, detect only on first run
    repo_name = cfg.get("reponame", "")
    owner_repo = cfg.get("owner_repo", "")
    if not repo_name:
        repo_name, owner_repo = _detect_repo_name_and_owner(root)

    # gh_available — use cached, detect only on first run
    gh_available = cfg.get("gh_available")
    if gh_available is None:
        rc, _ = _run(["gh", "auth", "status"])
        gh_available = rc == 0 and bool(owner_repo)

    return repo_name, owner_repo, branch, gh_available


# ---------------------------------------------------------------------------
# Parallel probes
# ---------------------------------------------------------------------------

def probe_git_status(project_root):
    rc, out = _run(["git", "status", "--short"], cwd=project_root)
    if rc != 0 or not out:
        return []
    return [line for line in out.splitlines() if line.strip()]


def probe_git_log(project_root):
    rc, out = _run(["git", "log", "--oneline", "--since=8 hours ago"], cwd=project_root)
    if rc != 0 or not out:
        return []
    return out.splitlines()


def probe_open_prs(project_root, gh_available):
    if not gh_available:
        return []
    rc, out = _run(
        ["gh", "pr", "list", "--limit", "5",
         "--json", "number,title,author,headRefName,isDraft"],
        cwd=project_root,
    )
    if rc != 0 or not out:
        return []
    try:
        return json.loads(out)
    except Exception:
        return []


def has_enough_files(project_root, threshold=20):
    """Fast check: at least `threshold` files exist (skips .git)."""
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


def probe_project_scan(reponame, project_root):
    script = pathlib.Path(__file__).parent / "project_state.py"
    if not script.exists():
        return {"scan": False, "reason": "project_state.py not found"}
    try:
        r = subprocess.run(
            [sys.executable, str(script), "check", reponame],
            capture_output=True, text=True, cwd=project_root, timeout=15,
        )
        return json.loads(r.stdout)
    except Exception as e:
        return {"scan": False, "reason": str(e)}


def probe_recent_huddle_history(reponame, branch, today_str):
    hdir = huddle_dir(reponame, branch)
    if not hdir.exists():
        return []
    notes = sorted(
        [p for p in hdir.glob("????-??-??.md") if p.stem != today_str],
        reverse=True,
    )[:3]
    results = []
    for note in notes:
        try:
            text = note.read_text(encoding="utf-8")
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
            results.append({"date": note.stem, "summary": summary.strip()})
        except Exception:
            pass
    return results


# ---------------------------------------------------------------------------
# State file helpers
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

EMPTY_NOTE_TEMPLATE = (
    "# Huddle\n\n## Repo\n\n## Date\n\n## Participants\n\n"
    "## Topics Discussed\n\n## Decisions\n\n## Open Questions\n\n"
    "## Action Items\n\n## Latest Summary\n"
)


def _note_has_content(path):
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8").strip()
    return bool(text) and text != EMPTY_NOTE_TEMPLATE.strip()


def _ensure_state_files(reponame, branch, date_str):
    root = huddle_dir(reponame, branch)
    root.mkdir(parents=True, exist_ok=True)

    state_file = huddle_state_path(reponame, branch)
    if not state_file.exists():
        s = dict(EMPTY_STATE)
        s["reponame"] = reponame
        s["branch"] = branch
        s["last_huddle_date"] = date_str
        state_file.write_text(json.dumps(s, indent=2) + "\n", encoding="utf-8")

    note_file = huddle_note_path(reponame, branch, date_str)
    if not note_file.exists():
        note_file.write_text(EMPTY_NOTE_TEMPLATE, encoding="utf-8")

    return state_file, note_file


def _load_state(state_file):
    try:
        return json.loads(state_file.read_text(encoding="utf-8"))
    except Exception:
        return dict(EMPTY_STATE)


# ---------------------------------------------------------------------------
# ensure
# ---------------------------------------------------------------------------

def _load_userconfig():
    """Load global userconfig.json, or return empty dict."""
    p = userconfig_path()
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def _save_userconfig(uc):
    """Save global userconfig.json."""
    p = userconfig_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(uc, indent=2) + "\n", encoding="utf-8")


def _load_repo_config(reponame):
    """Load existing config.json for this repo, or return empty dict."""
    p = repo_dir(reponame) / "config.json"
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def _save_repo_config(reponame, config):
    """Save config.json for this repo."""
    p = repo_dir(reponame) / "config.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")


def ensure(project_root_str, date_str):
    project_root = str(pathlib.Path(project_root_str).resolve())

    # --- User-level config (global, shared across all repos) ---
    uc = _load_userconfig()
    uc_changed = False

    # git_user: detect once globally
    git_user = uc.get("git_user", "")
    if not git_user:
        rc, out = _run(["git", "config", "user.name"], cwd=project_root)
        git_user = out if rc == 0 and out else "unknown"
        uc["git_user"] = git_user
        uc_changed = True

    # python_bin: detect once globally
    python_bin = uc.get("python_bin", "")
    if not python_bin:
        python_bin = detect_python_bin() or ""
        if python_bin:
            uc["python_bin"] = python_bin
            uc_changed = True

    # gh_available: detect once globally
    gh_available_cached = uc.get("gh_available")

    if uc_changed:
        _save_userconfig(uc)

    # --- Repo-level config ---
    initial_name = pathlib.Path(project_root).name
    repo_config = _load_repo_config(initial_name)

    # Derive identity — uses cached repo config, only branch is always fresh
    repo_name, owner_repo, branch, gh_available = derive_repo_identity(project_root, repo_config)

    # Use cached gh_available if we have it, otherwise cache the detected value
    if gh_available_cached is not None:
        gh_available = gh_available_cached
    elif not uc.get("gh_available"):
        uc["gh_available"] = gh_available
        _save_userconfig(uc)

    # Reload repo config if repo_name differs from folder name
    if repo_name != initial_name and not repo_config.get("reponame"):
        repo_config = _load_repo_config(repo_name)

    rc_changed = False

    if not repo_config.get("reponame"):
        repo_config["reponame"] = repo_name
        rc_changed = True

    if owner_repo and not repo_config.get("owner_repo"):
        repo_config["owner_repo"] = owner_repo
        rc_changed = True

    if rc_changed:
        _save_repo_config(repo_name, repo_config)

    # Create files before parallel probes so paths are stable
    state_file, note_file = _ensure_state_files(repo_name, branch, date_str)

    # Run probes in parallel — only volatile/session-specific data
    with ThreadPoolExecutor(max_workers=5) as pool:
        f_git_status    = pool.submit(probe_git_status, project_root)
        f_git_log       = pool.submit(probe_git_log, project_root)
        f_open_prs      = pool.submit(probe_open_prs, project_root, gh_available)
        f_project_scan  = pool.submit(probe_project_scan, repo_name, project_root)
        f_history       = pool.submit(probe_recent_huddle_history, repo_name, branch, date_str)

    git_status    = f_git_status.result()
    git_log       = f_git_log.result()
    open_prs      = f_open_prs.result()
    project_scan  = f_project_scan.result()
    history       = f_history.result()

    saved_state = _load_state(state_file)
    is_resume = _note_has_content(note_file)

    project_doc_file = repo_dir(repo_name) / "project-state.json"
    repo_has_content = has_enough_files(project_root)
    project_doc_missing = bool(project_scan.get("scan") and not project_doc_file.exists() and repo_has_content)

    warnings = []
    if not python_bin:
        warnings.append("Python not found. Install Python 3.x.")
    if not owner_repo:
        warnings.append("No git remote configured — PR listing and project docs scan skipped.")

    if project_doc_missing:
        next_action = "deepak_doc_offer"
    elif is_resume:
        next_action = "resume_summary"
    else:
        next_action = "show_roster"

    print(json.dumps({
        "python_bin": python_bin,
        "git_user": git_user,
        "repo_name": repo_name,
        "owner_repo": owner_repo,
        "branch": branch,
        "gh_available": gh_available,
        "huddle_dir": str(huddle_dir(repo_name, branch)),
        "huddle_state_file": str(state_file),
        "huddle_note_file": str(note_file),
        "is_resume": is_resume,
        "saved_state": saved_state,
        "repo_work_state": {
            "git_status": git_status,
            "recent_commits": git_log,
        },
        "open_prs": open_prs,
        "project_scan": project_scan,
        "project_doc_missing": project_doc_missing,
        "recent_huddle_history": history,
        "warnings": warnings,
        "next_action": next_action,
    }, indent=2))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) < 3 or args[0] != "ensure":
        print(__doc__)
        sys.exit(1)
    ensure(args[1], args[2])
