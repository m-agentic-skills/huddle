#!/usr/bin/env python3
"""Manage raw and derived graph artifacts for huddle state.

Usage:
    python graph_state.py ensure <reponame> <branch> <date>
    python graph_state.py append-raw <reponame> <branch> <event-json>
    python graph_state.py write-view <reponame> <branch> <view-json>
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


def view_path(reponame: str, branch: str) -> pathlib.Path:
    return huddle_dir(reponame, branch) / "graph-view.json"


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


def validate_view_item(item: dict, fields: list[str], context: str) -> None:
    require_fields(item, fields, context)


def validate_graph_view(data: dict) -> None:
    require_fields(data, ["main_question", "decision", "decision_why"], "graph_view")
    for index, item in enumerate(data.get("what_stands_out", [])):
        validate_view_item(item, ["icon", "text"], f"what_stands_out[{index}]")
    for index, item in enumerate(data.get("people_involved", [])):
        validate_view_item(item, ["id", "name", "icon", "meta", "influence"], f"people_involved[{index}]")
    for index, item in enumerate(data.get("key_moments", [])):
        validate_view_item(item, ["id", "icon", "title", "detail"], f"key_moments[{index}]")
    for index, item in enumerate(data.get("evidence", [])):
        validate_view_item(item, ["id", "icon", "label", "kind", "ref", "note"], f"evidence[{index}]")
    for index, item in enumerate(data.get("nodes", [])):
        validate_view_item(item, ["id", "kind", "label", "status", "icon", "why_it_matters"], f"nodes[{index}]")
    for index, item in enumerate(data.get("edges", [])):
        validate_view_item(item, ["from", "to", "relation", "label"], f"edges[{index}]")


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

    view = view_path(reponame, branch)
    if not view.exists():
        write_json(
            view,
            {
                "session_id": f"{date_str}-{branch}",
                "generated_at": "",
                "main_question": "",
                "decision": "",
                "decision_why": "",
                "what_stands_out": [],
                "people_involved": [],
                "key_moments": [],
                "evidence": [],
                "nodes": [],
                "edges": [],
            },
        )

    print(
        json.dumps(
            {
                "graph_raw_file": str(raw),
                "graph_view_file": str(view),
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


def write_view(reponame: str, branch: str, view_json: str) -> None:
    path = view_path(reponame, branch)
    data = json.loads(view_json)
    data["generated_at"] = iso_now()
    data.setdefault("what_stands_out", [])
    data.setdefault("people_involved", [])
    data.setdefault("key_moments", [])
    data.setdefault("evidence", [])
    data.setdefault("nodes", [])
    data.setdefault("edges", [])
    validate_graph_view(data)
    write_json(path, data)
    print(
        json.dumps(
            {
                "graph_view_file": str(path),
                "people_count": len(data["people_involved"]),
                "moments_count": len(data["key_moments"]),
                "nodes_count": len(data["nodes"]),
                "edges_count": len(data["edges"]),
            },
            indent=2,
        )
    )


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
    elif cmd == "write-view" and len(args) == 4:
        write_view(args[1], args[2], args[3])
    else:
        print(__doc__)
        sys.exit(1)
