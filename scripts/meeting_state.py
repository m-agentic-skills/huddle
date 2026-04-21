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

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import project_state


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
# Shell / probes
# ---------------------------------------------------------------------------

def _run(cmd, cwd=None):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, timeout=10)
        return r.returncode, r.stdout.strip()
    except Exception:
        return 1, ""


def _parse_owner_repo(remote_url):
    m = re.search(r"[:/]([^/]+)/([^/]+?)(?:\.git)?$", remote_url or "")
    if not m:
        return "", ""
    return m.group(2), f"{m.group(1)}/{m.group(2)}"


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

def _maybe_spawn_migration():
    """First-time only: if the new config root doesn't exist but the old one
    does, spawn scripts/migrate.py detached so huddle init isn't blocked.
    The migration is idempotent; meeting_state creating files concurrently is
    safe because migrate.py never overwrites existing targets.
    """
    old_root = pathlib.Path.home() / "config" / "muthuishere-agent-skills"
    if skills_root().exists() or not old_root.is_dir():
        return
    script = pathlib.Path(__file__).parent / "migrate.py"
    if not script.exists():
        return
    try:
        subprocess.Popen(
            [sys.executable, str(script)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except Exception:
        pass


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

    _maybe_spawn_migration()

    uc = _load_userconfig()
    folder_name = pathlib.Path(project_root).name
    repo_config = _load_repo_config(folder_name)

    cached_user          = uc.get("git_user", "")
    cached_python_bin    = uc.get("python_bin", "")
    cached_gh_available  = uc.get("gh_available")
    cached_reponame      = repo_config.get("reponame", "")
    cached_owner_repo    = repo_config.get("owner_repo", "")
    cached_branch        = repo_config.get("local_branch", "main")

    python_bin = cached_python_bin or (detect_python_bin() or "")

    # --- PHASE 1: fire every independent shell probe in parallel ---
    with ThreadPoolExecutor(max_workers=8) as pool:
        f_user     = pool.submit(_run, ["git", "config", "user.name"], project_root) if not cached_user else None
        f_branch   = pool.submit(_run, ["git", "branch", "--show-current"], project_root)
        f_remote   = pool.submit(_run, ["git", "remote", "get-url", "origin"], project_root) if not cached_reponame else None
        f_gh_auth  = pool.submit(_run, ["gh", "auth", "status"]) if cached_gh_available is None else None
        f_status   = pool.submit(probe_git_status, project_root)
        f_log      = pool.submit(probe_git_log, project_root)
        f_head     = pool.submit(_run, ["git", "rev-parse", "HEAD"], project_root)
        f_toplevel = pool.submit(_run, ["git", "rev-parse", "--show-toplevel"], project_root)

    # Resolve identity
    git_user = cached_user
    if f_user is not None:
        rc, out = f_user.result()
        git_user = out if rc == 0 and out else "unknown"

    rc, branch = f_branch.result()
    if rc != 0 or not branch:
        branch = cached_branch

    if cached_reponame:
        repo_name, owner_repo = cached_reponame, cached_owner_repo
    else:
        rc, remote_url = f_remote.result()
        if rc == 0 and remote_url:
            repo_name, owner_repo = _parse_owner_repo(remote_url)
        else:
            repo_name, owner_repo = folder_name, ""

    rc, _ = f_toplevel.result()
    has_git_repo = rc == 0

    rc, head = f_head.result()
    if rc != 0:
        head = ""

    gh_available = cached_gh_available
    if gh_available is None:
        rc, _ = f_gh_auth.result()
        gh_available = rc == 0 and bool(owner_repo)

    git_status = f_status.result()
    git_log    = f_log.result()

    # Inline project-scan decision — no second Python subprocess
    project_scan = project_state.evaluate_scan(
        repo_name,
        has_git_repo=has_git_repo,
        has_remote=bool(owner_repo),
        head=head,
    )

    # Persist caches now that we've resolved everything
    uc_changed = False
    if git_user and not cached_user:
        uc["git_user"] = git_user
        uc_changed = True
    if python_bin and not cached_python_bin:
        uc["python_bin"] = python_bin
        uc_changed = True
    if cached_gh_available is None:
        uc["gh_available"] = gh_available
        uc_changed = True
    if uc_changed:
        _save_userconfig(uc)

    if repo_name != folder_name and not cached_reponame:
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

    state_file, note_file = _ensure_state_files(repo_name, branch, date_str)

    # --- PHASE 2: probes that needed repo_name / gh_available ---
    with ThreadPoolExecutor(max_workers=2) as pool:
        f_prs     = pool.submit(probe_open_prs, project_root, gh_available)
        f_history = pool.submit(probe_recent_huddle_history, repo_name, branch, date_str)
    open_prs = f_prs.result()
    history  = f_history.result()

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
