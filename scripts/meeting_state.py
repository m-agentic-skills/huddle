"""
Manage repo-scoped huddle state under ~/config/.m-agent-skills/{reponame}/{branch}/huddle/.

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
import pathlib
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

def repo_dir(reponame):
    return pathlib.Path.home() / "config" / ".m-agent-skills" / reponame


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
# Repo identity — derived entirely from project_root, no pre-calls needed
# ---------------------------------------------------------------------------

def _run(cmd, cwd=None):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, timeout=10)
        return r.returncode, r.stdout.strip()
    except Exception:
        return 1, ""


def derive_repo_identity(project_root):
    """Return (repo_name, owner_repo, branch, gh_available) from project_root."""
    root = str(project_root)

    # Branch
    rc, branch = _run(["git", "branch", "--show-current"], cwd=root)
    if rc != 0 or not branch:
        branch = "main"

    # Remote URL → parse repo_name and owner_repo
    rc, remote_url = _run(["git", "remote", "get-url", "origin"], cwd=root)
    if rc == 0 and remote_url:
        # SSH: git@github.com:owner/repo.git
        m = re.search(r"[:/]([^/]+)/([^/]+?)(?:\.git)?$", remote_url)
        if m:
            owner, repo_name = m.group(1), m.group(2)
            owner_repo = f"{owner}/{repo_name}"
        else:
            repo_name = pathlib.Path(root).name
            owner_repo = ""
    else:
        repo_name = pathlib.Path(root).name
        owner_repo = ""

    # gh available?
    rc, _ = _run(["gh", "auth", "status"])
    gh_available = rc == 0 and bool(owner_repo)

    return repo_name, owner_repo, branch, gh_available


# ---------------------------------------------------------------------------
# Parallel probes
# ---------------------------------------------------------------------------

def probe_git_user(project_root):
    rc, out = _run(["git", "config", "user.name"], cwd=project_root)
    return out if rc == 0 and out else "unknown"


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

def ensure(project_root_str, date_str):
    project_root = str(pathlib.Path(project_root_str).resolve())

    # Derive identity (fast, sequential — needed for path setup)
    repo_name, owner_repo, branch, gh_available = derive_repo_identity(project_root)

    # Create files before parallel probes so paths are stable
    state_file, note_file = _ensure_state_files(repo_name, branch, date_str)

    # Run all probes in parallel
    with ThreadPoolExecutor(max_workers=6) as pool:
        f_git_user      = pool.submit(probe_git_user, project_root)
        f_git_status    = pool.submit(probe_git_status, project_root)
        f_git_log       = pool.submit(probe_git_log, project_root)
        f_open_prs      = pool.submit(probe_open_prs, project_root, gh_available)
        f_project_scan  = pool.submit(probe_project_scan, repo_name, project_root)
        f_history       = pool.submit(probe_recent_huddle_history, repo_name, branch, date_str)

    git_user      = f_git_user.result()
    git_status    = f_git_status.result()
    git_log       = f_git_log.result()
    open_prs      = f_open_prs.result()
    project_scan  = f_project_scan.result()
    history       = f_history.result()

    saved_state = _load_state(state_file)
    is_resume = _note_has_content(note_file)

    project_doc_file = repo_dir(repo_name) / "project-state.json"
    project_doc_missing = bool(project_scan.get("scan") and not project_doc_file.exists())

    warnings = []
    if not owner_repo:
        warnings.append("No git remote configured — PR listing and project docs scan skipped.")

    if project_doc_missing:
        next_action = "deepak_doc_offer"
    elif is_resume:
        next_action = "resume_summary"
    else:
        next_action = "show_roster"

    print(json.dumps({
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
