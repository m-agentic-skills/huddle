"""
Manage repo-scoped huddle state under ~/config/.m-agent-skills/{reponame}/{branch}/huddle/.

Usage:
    python meeting_state.py ensure <reponame> <branch> <date>
"""

import json
import pathlib
import sys


def repo_dir(reponame):
    return pathlib.Path.home() / "config" / ".m-agent-skills" / reponame


def branch_dir(reponame, branch):
    safe_branch = branch.replace("/", "-").lstrip(".") or "unknown-branch"
    return repo_dir(reponame) / safe_branch


def huddle_dir(reponame, branch):
    return branch_dir(reponame, branch) / "huddle"


def huddle_state_path(reponame, branch):
    return huddle_dir(reponame, branch) / "huddle-state.json"


def huddle_note_path(reponame, branch, date_str):
    return huddle_dir(reponame, branch) / f"{date_str}.md"


def graph_raw_path(reponame, branch):
    return huddle_dir(reponame, branch) / "graph-raw.json"


def ensure(reponame, branch, date_str):
    root = huddle_dir(reponame, branch)
    root.mkdir(parents=True, exist_ok=True)

    huddle_state = huddle_state_path(reponame, branch)
    if not huddle_state.exists():
        huddle_state.write_text(
            json.dumps(
                {
                    "reponame": reponame,
                    "branch": branch,
                    "last_huddle_date": date_str,
                    "current_topic": "",
                    "open_questions": [],
                    "action_items": [],
                    "latest_summary": "",
                    "active_personas": [],
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

    huddle_note = huddle_note_path(reponame, branch, date_str)
    if not huddle_note.exists():
        huddle_note.write_text(
            "# Huddle\n\n## Repo\n\n## Date\n\n## Participants\n\n## Topics Discussed\n\n## Decisions\n\n## Open Questions\n\n## Action Items\n\n## Latest Summary\n",
            encoding="utf-8",
        )

    raw_graph = graph_raw_path(reponame, branch)
    if not raw_graph.exists():
        raw_graph.write_text(
            json.dumps(
                {
                    "session_id": f"{date_str}-{branch}",
                    "actors": [],
                    "sources": [],
                    "events": [],
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

    print(
        json.dumps(
                {
                    "huddle_dir": str(root),
                    "branch_dir": str(branch_dir(reponame, branch)),
                    "huddle_state_file": str(huddle_state),
                    "huddle_note_file": str(huddle_note),
                    "graph_raw_file": str(raw_graph),
                },
            indent=2,
        )
    )


if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) != 4 or args[0] != "ensure":
        print(__doc__)
        sys.exit(1)
    ensure(args[1], args[2], args[3])
