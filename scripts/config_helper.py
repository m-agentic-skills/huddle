"""
Read and write per-repo config at ~/.config/muthuishere-agent-skills/{reponame}/config.json.

Usage:
    python config_helper.py read   <reponame>
    python config_helper.py get    <reponame> <key>
    python config_helper.py set    <reponame> <key> <value>
    python config_helper.py bootstrap <project_root> [repo_name] [branch] [user]
"""

import getpass
import json
import pathlib
import sys


def config_path(reponame):
    return pathlib.Path.home() / ".config" / "muthuishere-agent-skills" / reponame / "config.json"


def load(reponame):
    p = config_path(reponame)
    if not p.exists():
        return None
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def save(reponame, config):
    p = config_path(reponame)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
    return p


def cmd_read(reponame):
    config = load(reponame)
    if config is None:
        print("NOT_FOUND")
    else:
        print(json.dumps(config, indent=2))


def cmd_get(reponame, key):
    config = load(reponame)
    if config is None:
        print("")
    else:
        print(config.get(key, ""))


def cmd_set(reponame, key, value):
    config = load(reponame) or {}
    config["reponame"] = reponame
    config[key] = value
    p = save(reponame, config)
    print(f"Saved {key}={value}")
    print(f"Config: {p}")


def cmd_bootstrap(project_root, repo_name="", branch="", user=""):
    root = pathlib.Path(project_root).expanduser().resolve()
    resolved_repo_name = repo_name or root.name
    resolved_branch = branch or "main"
    resolved_user = user or getpass.getuser()

    config = load(resolved_repo_name) or {}
    config.update(
        {
            "reponame": resolved_repo_name,
            "local_project_root": str(root),
            "local_repo_name": resolved_repo_name,
            "local_branch": resolved_branch,
            "local_user": resolved_user,
            "non_git_mode": True,
        }
    )
    p = save(resolved_repo_name, config)
    print(json.dumps({"config_file": str(p), "config": config}, indent=2))


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(1)

    command = args[0]

    if command == "bootstrap":
        if len(args) < 2:
            print("ERROR: bootstrap requires <project_root> [repo_name] [branch] [user]", file=sys.stderr)
            sys.exit(1)
        project_root = args[1]
        repo_name = args[2] if len(args) >= 3 else ""
        branch = args[3] if len(args) >= 4 else ""
        user = args[4] if len(args) >= 5 else ""
        cmd_bootstrap(project_root, repo_name, branch, user)
        sys.exit(0)

    if len(args) < 2:
        print(__doc__)
        sys.exit(1)

    reponame = args[1]

    if command == "read":
        cmd_read(reponame)
    elif command == "get":
        if len(args) < 3:
            print("ERROR: get requires <reponame> <key>", file=sys.stderr)
            sys.exit(1)
        cmd_get(reponame, args[2])
    elif command == "set":
        if len(args) < 4:
            print("ERROR: set requires <reponame> <key> <value>", file=sys.stderr)
            sys.exit(1)
        cmd_set(reponame, args[2], args[3])
    else:
        print(f"ERROR: unknown command '{command}'", file=sys.stderr)
        sys.exit(1)
