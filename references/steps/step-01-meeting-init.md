# Step 01: Huddle Init

`{skill-root}` = installed root folder of this skill.

## Inputs from Pre-flight

`REPO_NAME` and `OWNER_REPO` are already set by step-00. Use them directly.

If step-00 or `repo_context.py` reports local folder mode, continue normally using:
- repo name from config or current folder name
- branch = configured branch or `main`
- user = configured local user or system username

## 1. Get Git User and Branch

```bash
git config user.name
git branch --show-current
```

- Set `GIT_USER` to the user.name output. Use this name throughout. If empty, use "you".
- Set `BRANCH` to the current branch. Sanitise for filesystem: replace `/` with `-`, strip leading dots.
  - Example: `feature/login-timeout` → `feature-login-timeout`
- Set `BRANCH_DIR` = `~/config/.m-agent-skills/{REPO_NAME}/{BRANCH}/`
- Set `HUDDLE_DIR` = `{BRANCH_DIR}/huddle/`

If available, prefer this one-shot helper instead of multiple brittle shell calls:

```bash
python {skill-root}/scripts/repo_context.py snapshot
```

Use its JSON output as the source for:
- `GIT_USER`
- `BRANCH`
- `REPO_NAME`
- repo work state
- whether `gh` / PR lookup should be skipped
- warnings like "no remote found", "no commits yet", or "using local folder mode"

## 2. Shared Config and Huddle Memory Layout

```
~/config/.m-agent-skills/{REPO_NAME}/
├── config.json
└── {BRANCH}/                      ← current branch folder for all skill state
    └── huddle/
        ├── huddle-state.json
        └── {YYYY-MM-DD}.md
```

## 3. Load or Create Config

```
python {skill-root}/scripts/config_helper.py read {REPO_NAME}
```

- `NOT_FOUND` → initialize with `{ "reponame": "{REPO_NAME}" }` and save.
- JSON output → use stored values.

## 4. Ensure Huddle Memory

```
python {skill-root}/scripts/meeting_state.py ensure {REPO_NAME} {BRANCH} {YYYY-MM-DD}
```

Creates missing directories (including `{HUDDLE_DIR}`), `huddle-state.json`, and today's `{YYYY-MM-DD}.md` if they don't exist.

This initialization should also ensure:
- `graph-raw.json`
- transient graph review derived from `graph-raw.json` when needed

## 5. Gather Session Context (Highest Priority)

This is the most important context source. Run before loading any huddle notes.

### 5a. Current conversation history

Review everything in the current session that happened **before the huddle was triggered**. This includes any Claude, Codex, or other agent activity visible in the conversation. Extract:

- What was the user working on or trying to solve?
- What files were being edited or created?
- What errors, blockers, or decisions came up?
- What was left unresolved or in progress?

Store this as `{SESSION_CONTEXT}`. If nothing preceded the meeting trigger, `{SESSION_CONTEXT}` is empty.

### 5b. Current repo work state

Run from `{project-root}`. Prefer the helper above. If you gather manually, run each command independently and do not let one failure cancel the others:

```bash
git status --short
git diff --stat HEAD
git log --oneline --since="8 hours ago"
```

Rules:
- If `git rev-parse --verify HEAD` fails, skip `git diff --stat HEAD` and `git log`; this repo has no commits yet.
- Never chain these into one shell command.
- A failure in one probe must not cancel the rest.

This captures what any tool (Claude, Codex, shell, IDE) has touched in this work session — modified files, staged changes, recent commits. Store as `{REPO_WORK_STATE}`.

### 5c. Open PRs (only if `GH_AVAILABLE=true`)

```bash
gh pr list --limit 5 --json number,title,author,headRefName,isDraft
```

Only run this if both of these are true:
- `GH_AVAILABLE=true`
- `OWNER_REPO` is non-empty or `git remote get-url origin` succeeded

If not, skip silently — leave `{OPEN_PRS}` empty.

## 6. Load Today's State

**Current branch** (`{HUDDLE_DIR}`):

If today's huddle note exists, extract:
- topics already discussed
- open questions
- action items
- decisions recorded (all attributed to `{GIT_USER}`)
- most recently active personas

Also read the last 3 previous huddle notes from `{HUDDLE_DIR}` (by date, most recent first) and extract their `## Latest Summary` sections. Store as `{RECENT_MEETING_HISTORY}`.

**Cross-branch context:**

Scan all sibling branch folders under `~/config/.m-agent-skills/{REPO_NAME}/`. For each other branch:
- Read its most recent `huddle/` note's `## Latest Summary` and `## Decisions` sections only
- Prioritise: `main`, `master`, `dev`, `develop` first, then any branch whose name shares keywords with the current topic
- Store as `{CROSS_BRANCH_CONTEXT}` — a brief per-branch digest, 1–2 lines each

This gives the team awareness of decisions made in other branches without overloading context.

## 6a. Search Scope Policy

When the huddle needs to answer "where do we stand?", "what changed?", "what's the current state?", or any similar status/review question, search across all relevant repo context, not just one huddle note:

- current branch huddle state
- recent huddle history on the current branch
- relevant sibling-branch summaries
- current repo work state (`git status`, `git diff --stat`, recent commits)
- current session context before the huddle started

Treat the current huddle Markdown file as the rendered review artifact, but not as the only source of truth.

## 7. Load Personas

Read all markdown files in `{skill-root}/references/personas/`.

Startup optimization:
- During init, load only lightweight persona metadata needed to show the roster and select candidates:
  - `name`, `displayName`, `title`, `icon`, `role`, `domains`
- Do not fully read every persona body during startup.
- Only load the full persona file for the 2-3 personas selected for the current round, plus any persona explicitly named by `{GIT_USER}`.

For each persona, load and hold in memory:
- frontmatter fields for the lightweight roster: `name`, `displayName`, `title`, `icon`, `role`, `domains`
- defer `capabilities`, `identity`, `communicationStyle`, `principles`, and body sections until the persona is actually selected

If any file is missing `name`, `displayName`, `communicationStyle`, or `principles`, stop and name the file.

Build a roster in memory. These will be used for selection and character consistency in step-02.

## 8. Open the Huddle

**If resuming** (today's huddle note already has content):
> Briefly summarize what was covered and what's unresolved. If `{SESSION_CONTEXT}` or `{REPO_WORK_STATE}` shows new activity since the last save, surface it: "I can also see you've been working on X since we last met." Then ask {GIT_USER}: "Where do you want to pick up?"

**If starting fresh**:

Greet {GIT_USER} by name. Start the huddle note with repo, date, and driver.

Then, before asking what's on their mind, brief the team with what you've already observed. Format:

```
**Before we start — here's what I'm seeing:**

[If {SESSION_CONTEXT} is not empty]
**This session:** {2-4 bullet summary of what was happening before the meeting — what was being worked on, errors hit, decisions in flight}

[If {REPO_WORK_STATE} shows changes]
**Repo state:** {modified/staged files and recent commits — what's in progress or just shipped}

[If {OPEN_PRS} is not empty]
**Open PRs:** {list titles and authors, 1 line each}

[If {RECENT_MEETING_HISTORY} is not empty]
**Last huddle(s) on `{BRANCH}`:** {1-line summary per recent huddle — key decisions and open items}

[If {CROSS_BRANCH_CONTEXT} is not empty]
**Other branches:** {1-line per branch — branch name + most recent decision or open item}
```

Omit any section that has nothing to show. If all sections are empty, skip the brief entirely.

Then show the available personas (displayName + title + icon, one line each) and ask:
> "{GIT_USER}, what do you want to work through today?"

Wait for {GIT_USER} to respond before loading step-02.
