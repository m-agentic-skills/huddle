---
name: team-meeting
description: Repo-aware multi-persona team meeting for daily development discussions. Use when the user wants a team sync, daily meeting, multiple perspectives on repo work, to resume today's meeting, or to capture decisions and action items. Load personas from markdown files, orchestrate a party-mode style discussion in our style, and persist meeting state under ~/m-agentic-skills-config/{reponame}/team-meetings/.
---

# Team Meeting

Use this skill as the repo's daily AI team room.

This is party mode converted into a practical team meeting workflow:

- repo-aware
- resumable by date
- saves a meeting document every day
- keeps open questions and action items in repo memory
- uses multiple labeled personas without turning into theatrical roleplay

## Read Order

1. `steps/step-01-meeting-init.md`
2. `steps/step-02-discussion.md`
3. `steps/step-03-smart-exit.md`

## Core Rules

- Identify the repo with `gh repo view --json name,nameWithOwner`.
- Store meeting memory in `~/m-agentic-skills-config/{reponame}/team-meetings/`.
- Today's meeting file is `{YYYY-MM-DD}.md`.
- Shared state file is `meeting-state.json`.
- Always load today's meeting file if it exists and resume from it.
- Always update the daily meeting file and state file after meaningful discussion.
- Use the persona markdown files in `./personas/`.
- Keep persona output short, opinionated, and useful. Label each contribution with the persona name.
- Allow disagreement and cross-reference between personas.
- When the user is clearly wrapping up, summarize, persist the state, and tell them how to resume.
