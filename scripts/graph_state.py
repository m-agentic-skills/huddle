#!/usr/bin/env python3
"""Manage raw and derived graph artifacts for huddle state.

Usage:
    python graph_state.py ensure <reponame> <branch> <date>
    python graph_state.py append-raw <reponame> <branch> <event-json>
"""

from __future__ import annotations

import json
import pathlib
import sys
from datetime import datetime, timezone


def repo_dir(reponame: str) -> pathlib.Path:
    return pathlib.Path.home() / "config" / ".m-agent-skills" / reponame


def branch_dir(reponame: str, branch: str) -> pathlib.Path:
    safe_branch = branch.replace("/", "-").lstrip(".") or "unknown-branch"
    return repo_dir(reponame) / safe_branch


def huddle_dir(reponame: str, branch: str) -> pathlib.Path:
    return branch_dir(reponame, branch) / "huddle"


def raw_path(reponame: str, branch: str) -> pathlib.Path:
    return huddle_dir(reponame, branch) / "graph-raw.json"


def read_json(path: pathlib.Path, default: dict) -> dict:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: pathlib.Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def require_fields(obj: dict, fields: list[str], context: str) -> None:
    missing = [field for field in fields if not obj.get(field)]
    if missing:
        raise ValueError(f"{context} missing required fields: {', '.join(missing)}")


def validate_actor(actor: dict, context: str) -> None:
    require_fields(actor, ["id", "name", "icon", "meta"], context)


def validate_source(source: dict, context: str) -> None:
    require_fields(source, ["id", "kind", "label", "ref"], context)


def validate_raw_event(event: dict, index: int | None = None) -> None:
    context = f"events[{index}]" if index is not None else "event"
    require_fields(event, ["ts", "actor_id", "op", "target", "payload"], context)
    require_fields(event["target"], ["id", "kind"], f"{context}.target")


def validate_raw_state(data: dict) -> None:
    require_fields(data, ["session_id"], "graph_raw")
    for index, actor in enumerate(data.get("actors", [])):
        validate_actor(actor, f"actors[{index}]")
    for index, source in enumerate(data.get("sources", [])):
        validate_source(source, f"sources[{index}]")
    for index, event in enumerate(data.get("events", [])):
        validate_raw_event(event, index)


def ensure(reponame: str, branch: str, date_str: str) -> None:
    root = huddle_dir(reponame, branch)
    root.mkdir(parents=True, exist_ok=True)

    raw = raw_path(reponame, branch)
    if not raw.exists():
        write_json(
            raw,
            {
                "session_id": f"{date_str}-{branch}",
                "actors": [],
                "sources": [],
                "events": [],
            },
        )

    print(
        json.dumps(
            {
                "graph_raw_file": str(raw),
            },
            indent=2,
        )
    )


def append_raw(reponame: str, branch: str, event_json: str) -> None:
    path = raw_path(reponame, branch)
    data = read_json(path, {"session_id": "", "actors": [], "sources": [], "events": []})
    event = json.loads(event_json)
    event.setdefault("ts", iso_now())
    validate_raw_event(event)
    data.setdefault("events", []).append(event)
    validate_raw_state(data)
    write_json(path, data)
    print(json.dumps({"graph_raw_file": str(path), "events_count": len(data["events"])}, indent=2))

if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(1)

    cmd = args[0]
    if cmd == "ensure" and len(args) == 4:
        ensure(args[1], args[2], args[3])
    elif cmd == "append-raw" and len(args) == 4:
        append_raw(args[1], args[2], args[3])
    else:
        print(__doc__)
        sys.exit(1)
