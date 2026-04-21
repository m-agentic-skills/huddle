#!/usr/bin/env python3
"""
File-based context bundle — no shell commands.

Returns a single JSON blob with:
  persona_roster_xml    : contents of references/persona-roster.xml
  cross_branch_context  : [{branch, date, summary}, ...] for sibling branches
                          of this repo, prioritizing main/master/dev/develop

Runs after meeting_state.py so repo_name and current branch are known.
Cheap and safe to re-call — pure filesystem reads.

Usage:
    python bundle_context.py <reponame> <current_branch>
"""

from __future__ import annotations

import json
import pathlib
import sys


SKILL_ROOT = pathlib.Path(__file__).resolve().parent.parent
ROSTER_PATH = SKILL_ROOT / "references" / "persona-roster.xml"
CONFIG_ROOT = pathlib.Path.home() / ".config" / "muthuishere-agent-skills"

PRIORITY_BRANCHES = ("main", "master", "dev", "develop")
MAX_CROSS_BRANCH = 4


def _read_roster() -> str:
    if not ROSTER_PATH.exists():
        return ""
    try:
        return ROSTER_PATH.read_text(encoding="utf-8")
    except Exception:
        return ""


def _sanitize_branch(branch: str) -> str:
    return branch.replace("/", "-").lstrip(".") or "unknown-branch"


def _latest_summary(note_path: pathlib.Path) -> str:
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


def _scan_branch(branch_dir: pathlib.Path) -> dict | None:
    huddle_dir = branch_dir / "huddle"
    if not huddle_dir.is_dir():
        return None
    notes = sorted(huddle_dir.glob("????-??-??.md"), reverse=True)
    if not notes:
        return None
    latest = notes[0]
    return {
        "branch": branch_dir.name,
        "date": latest.stem,
        "summary": _latest_summary(latest),
    }


def _cross_branch(reponame: str, current_branch: str) -> list[dict]:
    repo_dir = CONFIG_ROOT / reponame
    if not repo_dir.is_dir():
        return []

    current_safe = _sanitize_branch(current_branch)
    entries = []
    for child in repo_dir.iterdir():
        if not child.is_dir() or child.name == current_safe:
            continue
        found = _scan_branch(child)
        if found:
            entries.append(found)

    def sort_key(entry):
        idx = PRIORITY_BRANCHES.index(entry["branch"]) if entry["branch"] in PRIORITY_BRANCHES else len(PRIORITY_BRANCHES)
        return (idx, -ord(entry["date"][0]) if entry["date"] else 0, entry["branch"])

    entries.sort(key=sort_key)
    return entries[:MAX_CROSS_BRANCH]


def bundle(reponame: str, current_branch: str) -> dict:
    return {
        "persona_roster_xml": _read_roster(),
        "cross_branch_context": _cross_branch(reponame, current_branch),
    }


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    print(json.dumps(bundle(sys.argv[1], sys.argv[2]), indent=2))
