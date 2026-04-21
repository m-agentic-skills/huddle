# Step 00: Pre-flight

Run these two commands. Do not run any git, gh, or persona/cross-branch read commands before or between them.

**Call 1 — volatile repo state (git/gh probes, all parallel):**

```bash
python3 {skill-root}/scripts/meeting_state.py ensure {project-root} {YYYY-MM-DD}
```

Store the full JSON output as `HUDDLE_INIT`.

**Call 2 — static file-based context (persona roster + cross-branch notes):**

```bash
{PYTHON_BIN} {skill-root}/scripts/bundle_context.py {REPO_NAME} {BRANCH}
```

`{REPO_NAME}` and `{BRANCH}` come from `HUDDLE_INIT`. Store the output as `HUDDLE_CONTEXT`.
No shell commands run here — it's pure file reads, safe to re-call anytime.

`{project-root}` = the user's project directory (absolute path).
`{YYYY-MM-DD}` = today's date.

## Session Variables

Extract and store these for the entire session:

- `{PYTHON_BIN}` = `HUDDLE_INIT.python_bin` — the detected Python binary path. Use this for **all** subsequent `python` invocations. Never hardcode `python3` or `python`.
- `{HUDDLE_DIR}` = `HUDDLE_INIT.huddle_dir`
- `{REPO_NAME}` = `HUDDLE_INIT.repo_name`
- `{BRANCH}` = `HUDDLE_INIT.branch`
- `{SKILL_ROOT}` = the installed root folder of this skill
- `{PERSONA_ROSTER}` = `HUDDLE_CONTEXT.persona_roster_xml`
- `{CROSS_BRANCH_CONTEXT}` = `HUDDLE_CONTEXT.cross_branch_context`

If `python_bin` is `null`, stop immediately: "Python not found. Install Python 3.x."

Proceed to step-01.
