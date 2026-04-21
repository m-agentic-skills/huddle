# Step 01: Huddle Init

`HUDDLE_INIT` is already available from step-00. Do not re-run shell commands.

## Extract from HUDDLE_INIT

Set these variables for use throughout the session:

- `{GIT_USER}` = `HUDDLE_INIT.git_user`
- `{BRANCH}` = `HUDDLE_INIT.branch`
- `{REPO_NAME}` = `HUDDLE_INIT.repo_name`
- `{HUDDLE_STATE_FILE}` = `HUDDLE_INIT.huddle_state_file`
- `{HUDDLE_NOTE_FILE}` = `HUDDLE_INIT.huddle_note_file`

## Also Extract: Current Session Context

Review everything in this conversation that happened **before the huddle was triggered** — any Claude, Codex, or other agent output. Extract:
- What was the user working on or trying to solve?
- What files were being edited or created?
- What errors or blockers came up?

Store as `{SESSION_CONTEXT}`. Empty if nothing preceded the trigger.

## Load Persona Roster

Read `{skill-root}/references/persona-roster.xml`.

Use it as the lightweight roster source of truth: `id`, `icon`, `name`, `title`, `domains`, persona file reference.

Do not load full persona body files during init. Only load the full persona file for the 2-3 personas selected for the current round, plus any persona explicitly named by `{GIT_USER}`.

## Surface Warnings (all paths)

If `HUDDLE_INIT.warnings` is non-empty, show each warning as a brief note before any greeting or persona output:

> ⚠️ {warning text}

Example: `⚠️ No git remote configured — PR listing and project docs scan skipped.`

## Act on next_action

Read `HUDDLE_INIT.next_action` and act immediately:

### `"deepak_doc_offer"`

**Guard:** If the repo/folder has fewer than 20 files (empty or near-empty project), skip this entirely — treat as `show_roster` instead. The Python preflight already checks this, but if it slips through, do not offer docs for a nearly empty folder.

Deepak speaks first. Do not show the roster yet.

Brief `{GIT_USER}` on repo state from `HUDDLE_INIT.repo_work_state`, then Deepak says:

> 📝 **Deepak** _(Tech Writer)_ — I don't see any project documentation yet. Want me to do a quick scan and write one?

**Stop. Wait for `{GIT_USER}` to answer.**

- If yes → route to `steps/step-deepak-document.md` immediately
- If no → set `DEEPAK_DOC_OFFERED=true`, show the roster, ask what to discuss

### `"resume_summary"`

Today's note already has content. From `HUDDLE_INIT.saved_state`, surface:
- Last topic discussed
- Open questions and action items
- Active personas

If `{SESSION_CONTEXT}` or `HUDDLE_INIT.repo_work_state` shows new activity since last save, surface it:
> "I can also see you've been working on X since we last met."

Restore active personas from `saved_state.active_personas`. Do not show the full roster unless `{GIT_USER}` asks to change the team.

Ask `{GIT_USER}`: "Where do you want to pick up?" Wait. Load step-02.

### `"show_roster"`

Fresh start. Greet `{GIT_USER}` by name. Write the huddle note header.

Brief the team with what you've already observed:

```
**Before we start — here's what I'm seeing:**

[If {SESSION_CONTEXT} is not empty]
**This session:** {2-4 bullet summary}

[If repo_work_state.git_status or recent_commits are non-empty]
**Repo state:** {modified/staged files and recent commits}

[If open_prs is non-empty]
**Open PRs:** {title + author, one line each}

[If recent_huddle_history is non-empty]
**Last huddle(s):** {1-line summary per note}
```

Omit any section with nothing to show. If all sections are empty, skip the brief entirely.

Show the persona roster (displayName + title + icon, one line each) and ask:
> "{GIT_USER}, what do you want to work through today?"

Wait for `{GIT_USER}` to respond before loading step-02.

## Cross-Branch Context (all three paths)

Scan sibling branch folders under `~/.config/muthuishere-agent-skills/{REPO_NAME}/`. For each other branch, read its most recent huddle note's `## Latest Summary` and `## Decisions` sections. Prioritise `main`, `master`, `dev`, `develop`. Store as `{CROSS_BRANCH_CONTEXT}` and surface if relevant.
