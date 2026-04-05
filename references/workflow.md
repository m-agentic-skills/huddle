---
name: huddle-workflow
---

# Huddle Workflow

Run a repo-scoped, daily, resumable discussion with multi-perspective analysis and user-driven decisions.

## Variables

- `{project-root}` = user's active project folder. All `gh` and `git` commands run from here when available.
- `{skill-root}` = installed root folder of this skill (where `scripts/`, `references/steps/`, `references/` live).
- `{config-dir}` = `~/config/.m-agent-skills/{REPO_NAME}/`
- `{GIT_USER}` = result of `git config user.name`, or configured/system local user in non-git mode — used to address the user throughout.

## Meeting Memory Layout

```
{config-dir}/
├── config.json                          ← shared repo preferences
└── {BRANCH_NAME}/                       ← branch root for all future skill state
    └── huddle/
        ├── huddle-state.json            ← open questions, action items, last topic
        └── {YYYY-MM-DD}.md              ← daily huddle note
        ├── graph-raw.json               ← append-oriented structural room changes, always updated in background
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

Graph review behavior:
- persist only `graph-raw.json`
- derive the readable graph transiently when review is requested
- bundle markdown plus raw graph into the hosted review viewer
