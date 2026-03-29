"""
Manage repo-scoped team meeting state under ~/m-agentic-skills-config/{reponame}/team-meetings/.

Usage:
    python meeting_state.py ensure <reponame> <date>
"""

import json
import pathlib
import sys


def repo_dir(reponame):
    return pathlib.Path.home() / "m-agentic-skills-config" / reponame


def meetings_dir(reponame):
    return repo_dir(reponame) / "team-meetings"


def state_path(reponame):
    return meetings_dir(reponame) / "meeting-state.json"


def meeting_path(reponame, date_str):
    return meetings_dir(reponame) / f"{date_str}.md"


def ensure(reponame, date_str):
    root = meetings_dir(reponame)
    root.mkdir(parents=True, exist_ok=True)

    state = state_path(reponame)
    if not state.exists():
        state.write_text(
            json.dumps(
                {
                    "reponame": reponame,
                    "last_meeting_date": date_str,
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

    meeting = meeting_path(reponame, date_str)
    if not meeting.exists():
        meeting.write_text(
            "# Team Meeting\n\n## Repo\n\n## Date\n\n## Participants\n\n## Topics Discussed\n\n## Decisions\n\n## Open Questions\n\n## Action Items\n\n## Latest Summary\n",
            encoding="utf-8",
        )

    print(
        json.dumps(
            {
                "meetings_dir": str(root),
                "state_file": str(state),
                "meeting_file": str(meeting),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) != 3 or args[0] != "ensure":
        print(__doc__)
        sys.exit(1)
    ensure(args[1], args[2])
