"""
Read and write per-repo config at ~/m-agentic-skills-config/{reponame}/config.json.

Usage:
    python config_helper.py read   <reponame>
    python config_helper.py get    <reponame> <key>
    python config_helper.py set    <reponame> <key> <value>
"""

import json
import pathlib
import sys


def config_path(reponame):
    return pathlib.Path.home() / "m-agentic-skills-config" / reponame / "config.json"


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


if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) < 2:
        print(__doc__)
        sys.exit(1)

    command = args[0]
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
