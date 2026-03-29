---
name: team-meeting-workflow
---

# Team Meeting Workflow

Run a repo-scoped, daily, resumable team meeting with saved state.

## Workflow Architecture

- Step 1 loads repo identity, meeting memory, and personas
- Step 2 runs the multi-persona discussion loop
- Step 3 handles natural wrap-up, summary, and state persistence

## Meeting Memory

For repo `{REPO_NAME}`, use:

- `~/m-agentic-skills-config/{REPO_NAME}/config.json`
- `~/m-agentic-skills-config/{REPO_NAME}/team-meetings/{YYYY-MM-DD}.md`
- `~/m-agentic-skills-config/{REPO_NAME}/team-meetings/meeting-state.json`

## Execution

1. Read `steps/step-01-meeting-init.md`
2. Read `steps/step-02-discussion.md`
3. If the user is wrapping up, read `steps/step-03-smart-exit.md`
