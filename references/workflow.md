---
name: huddle-workflow
---

# Huddle Workflow

Run a repo-scoped, daily, resumable discussion with multi-perspective analysis and user-driven decisions.

## Variables

- `{project-root}` = user's active project folder. All `gh` and `git` commands run from here when available.
- `{skill-root}` = installed root folder of this skill (where `scripts/`, `references/steps/`, `references/` live).
- `{config-dir}` = `~/.config/muthuishere-agent-skills/{REPO_NAME}/`
- `{GIT_USER}` = result of `git config user.name`, or configured/system local user in non-git mode — used to address the user throughout.

## Meeting Memory Layout

```
{config-dir}/
├── config.json                          ← shared repo preferences
└── {BRANCH_NAME}/                       ← branch root for all future skill state
    └── huddle/
        ├── huddle-state.json            ← synthesized state (written on demand or wrap-up, not every round)
        ├── {YYYY-MM-DD}.md              ← daily huddle note (written on demand or wrap-up, not every round)
        └── raw/                         ← append-only event files (fire-and-forget background writes)
            ├── {ts}_decision.json       ← one file per decision
            └── {ts}_milestone.json      ← one file per milestone
```

Branch name is sanitised for the filesystem (e.g. `feature/login` → `feature-login`).

Cross-branch reads: when loading context, scan **all** sibling branch folders under `{config-dir}` to surface decisions made in other branches — especially `main`/`master` and any branch whose name overlaps with the current topic. Read only their `huddle/` state if present.

## Core Rules

- Run all `gh` and `git` commands from `{project-root}`.
- User drives — never advance the agenda, make decisions, or move to a new topic without `{GIT_USER}` signalling to do so.
- After presenting perspectives, always end with a question to `{GIT_USER}`.
- Config is memory — ask for repo config once, never again.

## Process

1. Read `references/steps/step-00-preflight.md` — derive project identity, decide whether git/gh can actually be used, and fall back to local folder mode when needed.
2. Read `references/activation-routing.xml` — confirm the route and goal.
3. Read `references/steps/step-01-meeting-init.md` — get git username, load repo config, and huddle memory.
4. Read `references/steps/step-02-discussion.md` — run multi-perspective discussion loop, user drives.
5. When user wraps up, read `references/steps/step-03-smart-exit.md` — summarize, persist, give resume hint.

Persona metadata source:
- `references/persona-roster.xml` is the lightweight roster and file lookup source
- persona markdown files remain the source for full persona behavior and voice

State write behavior:
- during live discussion, NO file writes happen on normal rounds
- on decisions/milestones: Write tool appends a single raw event JSON file to `raw/` — no Python script, no background process, just a direct file write
- on explicit ask ("give me notes") or wrap-up: synthesis reads `raw/*.json` + conversation → writes `huddle-state.json` + `.md` → deletes `raw/`
- use `{PYTHON_BIN}` (detected once in preflight) for script invocations (md_to_html.py, project_state.py, etc.) — never hardcode python3/python

Graph review behavior:
- state lives in `huddle-state.json` only — no `graph-raw.json`
- never auto-open the graph review page; only run `{PYTHON_BIN} scripts/md_to_html.py {note_path}` when {GIT_USER} explicitly asks to see the graph
- `index.html` derives graph nodes/edges from `decisions[]` client-side
