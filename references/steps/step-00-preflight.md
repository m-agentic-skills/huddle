# Step 00: Pre-flight

Run exactly one command. Do not run any git or gh commands before this.

```bash
python3 {skill-root}/scripts/meeting_state.py ensure {project-root} {YYYY-MM-DD}
```

`{project-root}` = the user's project directory (absolute path).
`{YYYY-MM-DD}` = today's date.

This derives repo identity, branch, git user, git status, open PRs, project scan, and huddle state all in parallel.
Store the full JSON output as `HUDDLE_INIT`. Proceed to step-01.
