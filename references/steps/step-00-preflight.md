# Step 00: Pre-flight

Run these three commands **in parallel** (one message, three Bash tool calls). Do not run any other git, gh, or filesystem probes before or between them.

**Call 1 — `GLOBAL_STATE`** (cached across sessions; pure file read on warm cache):

```bash
python3 {skill-root}/scripts/global_state.py
```

First call ever detects `git_user`, `python_bin`, `gh_available`; caches in `~/.config/muthuishere-agent-skills/userconfig.json`. Every subsequent call is ~1ms. Also returns `persona_roster_xml`.

**Call 2 — `PROJECT_STATE`** (recomputed once per session; file reads only):

```bash
python3 {skill-root}/scripts/project_state.py snapshot {project-root}
```

Returns `reponame`, `owner_repo`, `branch`, huddle paths, project doc freshness, `cross_branch_context`, `raw_events` pending synthesis, and `saved_state` from `huddle-state.json`.

**Call 3 — `SESSION_STATE`** (always fresh; live shell probes):

```bash
python3 {skill-root}/scripts/session_state.py {project-root} {YYYY-MM-DD}
```

Returns `git_status`, `recent_commits`, `open_prs`, `is_resume`, and ensures today's huddle note file exists.

`{project-root}` = the user's project directory (absolute path).
`{YYYY-MM-DD}` = today's date.

## Session Variables

Store the three JSON blobs as `GLOBAL_STATE`, `PROJECT_STATE`, `SESSION_STATE`. Derive for use throughout the session:

- `{PYTHON_BIN}` = `GLOBAL_STATE.python_bin` — use for all subsequent `python` invocations. Never hardcode `python3` or `python`.
- `{GIT_USER}` = `GLOBAL_STATE.git_user`
- `{PERSONA_ROSTER}` = `GLOBAL_STATE.persona_roster_xml`
- `{SKILL_ROOT}` = `GLOBAL_STATE.skill_root`
- `{REPO_NAME}` = `PROJECT_STATE.reponame`
- `{BRANCH}` = `PROJECT_STATE.branch` (prefer `SESSION_STATE.branch` if it differs — user switched branches)
- `{HUDDLE_DIR}` = `PROJECT_STATE.huddle_dir`
- `{HUDDLE_STATE_FILE}` = `PROJECT_STATE.huddle_state_file`
- `{HUDDLE_NOTE_FILE}` = `SESSION_STATE.huddle_note_file`
- `{CROSS_BRANCH_CONTEXT}` = `PROJECT_STATE.cross_branch_context`

If `python_bin` is `null`, stop immediately: "Python not found. Install Python 3.x."

## next_action

Step-01 runs the full cascade (trigger topic wins, then resume, then Deepak, then roster). For reference only:

- `{INITIAL_TOPIC}` non-empty → route straight to discussion on that topic
- else `SESSION_STATE.is_resume` → `resume_summary`
- else `PROJECT_STATE.project_doc_missing` → `deepak_doc_offer` (blocking)
- else → `show_roster`

Deepak's offer downgrades to a soft end-of-round nudge in the first and fourth paths whenever `project_doc_missing` is still true (i.e., the repo genuinely has no README/CLAUDE.md/`docs/`).

Proceed to step-01.
