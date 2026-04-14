# Step: Mission Execute — Worker Dispatch

This step dispatches workers to implement features. Workers run in parallel
(one per feature) using isolated git worktrees, or sequentially in the current
checkout, depending on the execution backend chosen in step-mission-plan.

---

## Prerequisites

- `{HUDDLE_DIR}/mission/contract.md` exists (validation contract approved)
- `{HUDDLE_DIR}/mission/features.json` exists (features approved)
- `{HUDDLE_DIR}/mission/status.json` exists with `state: "planned"` or `state: "fixing"`
- Execution backend chosen by {GIT_USER}

---

## 1. Load Mission State

Read:
- `{HUDDLE_DIR}/mission/features.json` — the full feature plan
- `{HUDDLE_DIR}/mission/status.json` — current execution state
- `{HUDDLE_DIR}/mission/contract.md` — for worker context

Identify the current milestone from `status.json.current_milestone`.
Collect all features in that milestone with status `pending` or `fixing`.

If no features remain in the current milestone → all executed. Proceed to
`step-mission-validate.md`.

---

## 2. Dispatch — Parallel Worktree Agents (Option 1)

**This is the core parallel execution mechanism.**

For each feature in the current milestone that is `pending` or `fixing`:

1. Update `status.json`: set feature status to `executing`
2. Build the worker prompt (see Worker Prompt Template below)
3. Create an `Agent` tool call with `isolation: "worktree"`

**CRITICAL: Issue ALL Agent calls in a SINGLE message.**

When Claude Code receives multiple tool calls in one message, it executes
them concurrently. Each `Agent(isolation="worktree")` gets its own git
worktree — a full independent checkout. Workers cannot interfere with each other.

```
# Pseudo-code for what Claude does:

features_to_dispatch = [f for f in current_milestone.features
                        if status[f.id] in ("pending", "fixing")]

# ALL of these go in ONE message — they run in parallel:
for feature in features_to_dispatch:
    Agent(
        description=f"Worker: {feature.name}",
        isolation="worktree",
        prompt=build_worker_prompt(feature, contract, repo_context)
    )
```

**Do NOT issue agents one at a time. Do NOT wait for one to finish before
starting the next. The whole point is parallel execution.**

### Worker Prompt Template

```
You are a focused worker agent implementing a single feature.
You have a clean git worktree — your own independent checkout.

## Your Feature
Name: {feature.name}
ID: {feature.id}

## Specification
{feature.spec}

## Success Criteria
{feature.success_criteria — numbered list}

## Context Files (read these first for understanding)
{feature.context_files — list of paths}

## Files You Will Create or Modify
{feature.estimated_files — list of paths}

## Validation Contract (for reference)
{contract.md contents — so the worker understands the bigger picture}

## Instructions

1. Read the context files to understand the existing codebase
2. Write tests FIRST that verify your success criteria
3. Implement the feature until tests pass
4. Run the full test suite to check for regressions
5. Commit your work: git add {files} && git commit -m "feat({feature.id}): {feature.name}"

## Rules

- Only touch files listed in your estimated files unless absolutely necessary
- If you must touch additional files, keep changes minimal
- Write tests before implementation — test-driven
- If you are blocked (missing dependency, unclear spec, can't proceed):
  - Do NOT guess or work around it
  - Report exactly what blocked you and stop
  - Include: what you tried, what failed, what you need
- Do not push — leave your work on the worktree branch
- Do not modify files outside your feature scope
- Do not install new dependencies without documenting why

## Output Format

When done, report:
- STATUS: done | blocked
- FILES_CHANGED: [list]
- TESTS_WRITTEN: [list]
- TESTS_PASS: true | false
- BLOCKED_REASON: null | "description"
- NOTES: any relevant observations
```

### Collecting Results

When all Agent calls complete, Claude receives results from each worker.
Each result contains:
- The worker's status report
- The worktree path and branch name (if changes were made)

For each completed worker:
1. Update `status.json`: set feature status to `executed`, record `worker_branch`
2. If worker reported `blocked`: set feature status to `blocked`, record `block_reason`

---

## 3. Dispatch — Sequential (Option 2)

For each feature in milestone order:

1. Update `status.json`: set feature status to `executing`
2. Show {GIT_USER}: "Starting feature: {feature.name}"
3. Read context files
4. Write tests first
5. Implement until tests pass
6. Commit: `git add {files} && git commit -m "feat({feature.id}): {feature.name}"`
7. Update `status.json`: set feature status to `executed`
8. Show {GIT_USER} what was done
9. Ask: "Continue to next feature, or review this one first?"
10. **Wait.**

---

## 4. Dispatch — External (Option 3)

Write individual spec files for each feature:

For each feature, write `{HUDDLE_DIR}/mission/specs/{feature.id}.md`:

```markdown
# Feature: {feature.name}

## ID: {feature.id}

## Specification
{feature.spec}

## Success Criteria
{feature.success_criteria}

## Context Files
{feature.context_files}

## Files to Create/Modify
{feature.estimated_files}

## Validation Contract
{contract.md contents}

## Instructions
1. Read context files
2. Write tests first
3. Implement until tests pass
4. Report results via:
   {PYTHON_BIN} {SKILL_ROOT}/scripts/huddle_writer.py {HUDDLE_DIR} '{"type":"feature_complete","feature_id":"{feature.id}","branch":"your-branch","status":"done","tests_pass":true}'
```

Tell {GIT_USER}:

> Feature specs written to `{HUDDLE_DIR}/mission/specs/`.
> Dispatch your agents pointed at these files.
> When they're done, say "workers are done" and I'll collect results and validate.

**Wait.**

---

## 5. Post-Dispatch Status Report

After all workers complete (or report blocked), present:

```
## Mission Status — Milestone {milestone.name}

| Feature | Status | Branch | Tests |
|---------|--------|--------|-------|
| {name}  | done   | {branch} | pass |
| {name}  | blocked | — | — |

{N}/{total} features completed.
{blocked_count} blocked.
```

If any features are blocked:
- Show the block reasons
- Ask {GIT_USER}: "Want to unblock these, skip them, or adjust the plan?"
- **Wait.**

If all features completed:
- Ask {GIT_USER}: "All workers done. Ready to validate?"
- **Wait.**

When {GIT_USER} approves validation, read `step-mission-validate.md`.

---

## 6. Worktree Merge Strategy

After validation passes (handled in step-mission-validate), the worktree
branches need to be merged into the main branch. Options:

**Option A: Sequential merge (default)**
```bash
git merge {worker_branch_1} --no-ff -m "feat(m1): merge {feature.name}"
git merge {worker_branch_2} --no-ff -m "feat(m1): merge {feature.name}"
```

**Option B: Single merge commit**
```bash
git merge {branch_1} {branch_2} {branch_3} -m "feat(m1): merge milestone 1"
```

**Option C: User reviews each**
Show diffs from each worktree branch, let {GIT_USER} approve individually.

Present merge options to {GIT_USER} after validation passes.

---

## RETURN PROTOCOL

If {GIT_USER} cancels execution mid-dispatch:

1. Any running agents will complete (they can't be cancelled mid-run)
2. Update `status.json` with whatever completed
3. Set `status.json.state` to `"paused"`
4. **Re-read** `references/steps/step-02-discussion.md`
5. **Read** `huddle-state.json` — restore `active_personas` and `current_topic`
6. Tell {GIT_USER}: "Mission paused. {N} features completed, {M} pending. Resume with 'continue the mission'."
7. Ask: "Want to go back to the huddle, or something else?"
8. **Wait.**
