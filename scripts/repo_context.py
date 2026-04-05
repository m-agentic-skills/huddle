"""
Gather repo context safely for huddle startup.

Usage:
    python repo_context.py snapshot
"""

from __future__ import annotations

import getpass
import json
import pathlib
import subprocess
import sys


def run(cmd: list[str]) -> tuple[int, str, str]:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def config_path(reponame: str) -> pathlib.Path:
    return pathlib.Path.home() / "config" / ".m-agent-skills" / reponame / "config.json"


def load_config(reponame: str) -> dict[str, object]:
    p = config_path(reponame)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def load_config_for_project_root(project_root: pathlib.Path) -> tuple[str, dict[str, object]]:
    base_dir = pathlib.Path.home() / "config" / ".m-agent-skills"
    if not base_dir.exists():
        return "", {}

    target = str(project_root.resolve())
    for config_file in base_dir.glob("*/config.json"):
        try:
            config = json.loads(config_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if str(config.get("local_project_root", "")) == target:
            return config_file.parent.name, config
    return "", {}


def main() -> int:
    cwd = pathlib.Path.cwd().resolve()
    guessed_repo_name = cwd.name
    stored_repo_name, stored_config = load_config_for_project_root(cwd)
    if not stored_config:
        stored_repo_name = guessed_repo_name
        stored_config = load_config(guessed_repo_name)

    snapshot: dict[str, object] = {
        "git_user": str(stored_config.get("local_user", "")),
        "branch": str(stored_config.get("local_branch", "main")),
        "repo_root": str(stored_config.get("local_project_root", cwd)),
        "repo_name": str(stored_config.get("local_repo_name", stored_repo_name or guessed_repo_name)),
        "owner_repo": "",
        "has_remote": False,
        "gh_available": False,
        "status": "",
        "diff_stat": "",
        "recent_log": "",
        "open_prs": [],
        "mode": "local",
        "warnings": [],
    }

    code, out, _ = run(["git", "config", "user.name"])
    if code == 0 and out:
        snapshot["git_user"] = out

    code, out, err = run(["git", "rev-parse", "--show-toplevel"])
    if code != 0:
        snapshot["warnings"].append("not a git repo; using local folder mode")
        if not snapshot["git_user"]:
            snapshot["git_user"] = getpass.getuser()
        print(json.dumps(snapshot, indent=2))
        return 0

    snapshot["mode"] = "git"
    snapshot["repo_root"] = out
    snapshot["repo_name"] = out.rstrip("/").split("/")[-1]

    code, out, _ = run(["git", "branch", "--show-current"])
    if code == 0 and out:
        snapshot["branch"] = out

    code, out, _ = run(["git", "remote", "get-url", "origin"])
    if code == 0 and out:
        snapshot["has_remote"] = True
        if "github.com" in out:
            cleaned = out.removesuffix(".git")
            if cleaned.startswith("git@github.com:"):
                snapshot["owner_repo"] = cleaned.split("git@github.com:", 1)[1]
            elif "github.com/" in cleaned:
                snapshot["owner_repo"] = cleaned.split("github.com/", 1)[1]
            if snapshot["owner_repo"]:
                snapshot["repo_name"] = str(snapshot["owner_repo"]).split("/")[-1]
    else:
        snapshot["warnings"].append("no git remote found")

    code, _, _ = run(["gh", "auth", "status"])
    snapshot["gh_available"] = code == 0 and bool(snapshot["has_remote"])
    if code == 0 and not snapshot["has_remote"]:
        snapshot["warnings"].append("gh authenticated, but PR queries skipped because repo has no remote")

    code, out, err = run(["git", "status", "--short"])
    if code == 0:
        snapshot["status"] = out
    else:
        snapshot["warnings"].append(err or "git status failed")

    code, out, err = run(["git", "rev-parse", "--verify", "HEAD"])
    has_head = code == 0 and bool(out)
    if has_head:
        code, out, err = run(["git", "diff", "--stat", "HEAD"])
        if code == 0:
            snapshot["diff_stat"] = out
        else:
            snapshot["warnings"].append(err or "git diff --stat HEAD failed")

        code, out, err = run(["git", "log", "--oneline", '--since=8 hours ago'])
        if code == 0:
            snapshot["recent_log"] = out
        else:
            snapshot["warnings"].append(err or "git log failed")
    else:
        snapshot["warnings"].append("repo has no commits yet; skipped HEAD-based diff/log")

    if snapshot["gh_available"]:
        code, out, err = run(
            [
                "gh",
                "pr",
                "list",
                "--limit",
                "5",
                "--json",
                "number,title,author,headRefName,isDraft",
            ]
        )
        if code == 0 and out:
            try:
                snapshot["open_prs"] = json.loads(out)
            except json.JSONDecodeError:
                snapshot["warnings"].append("gh pr list returned invalid JSON")
        elif code != 0:
            snapshot["warnings"].append(err or "gh pr list failed")

    if not snapshot["git_user"]:
        snapshot["git_user"] = str(stored_config.get("local_user", "")) or getpass.getuser()

    print(json.dumps(snapshot, indent=2))
    return 0


if __name__ == "__main__":
    args = sys.argv[1:]
    if args != ["snapshot"]:
        print(__doc__)
        sys.exit(1)
    sys.exit(main())
