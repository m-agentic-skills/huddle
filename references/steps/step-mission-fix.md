# Step: Mission Fix — Fix Loop Orchestration

This step takes validator findings, converts actionable issues into targeted
fix-features, and re-dispatches workers. It then re-validates until the
milestone passes or the round limit is reached.

---

## Prerequisites

- Validator reports exist in `{HUDDLE_DIR}/mission/reports/`
- At least one feature or contract assertion failed validation
- {GIT_USER} has approved generating fixes

---

## 1. Analyze Validator Findings

Read all reports from `{HUDDLE_DIR}/mission/reports/`:
- Per-feature scrutiny reports (`{feature_id}.json`)
- Milestone black-box report (`milestone_{milestone_id}.json`)

Classify each finding:

| Classification | Action |
|---|---|
| **Critical failure** — code is wrong, test fails, contract assertion violated | Create a fix-feature |
| **Gap** — spec was ambiguous, criterion not fully testable | Ask {GIT_USER} to clarify, then create fix-feature if needed |
| **Non-critical suggestion** — style, optimization, nice-to-have | Log for {GIT_USER}, do NOT create fix-feature |
| **Duplicate** — same issue surfaced by both scrutiny and black-box | Deduplicate, create one fix-feature |

---

## 2. Generate Fix-Features

For each actionable finding, create a fix-feature. These are structured
identically to original features but are scoped to the specific issue.

Update `features.json` — add fix-features to the current milestone:

```json
{
  "id": "f1-fix1",
  "name": "Fix: {original feature name} — {issue summary}",
  "spec": "The validator found: {specific issue}. Fix this by: {what needs to change}.",
  "success_criteria": [
    "{the original criterion that failed, unchanged}",
    "{any additional criterion from the validator's finding}"
  ],
  "contract_assertions": [4],
  "test_first": true,
  "depends_on": ["f1"],
  "estimated_files": ["src/auth/token.ts", "src/auth/token.test.ts"],
  "context_files": ["src/auth/config.ts"],
  "is_fix": true,
  "original_feature": "f1",
  "validator_finding": "Clock skew not handled in token expiry check"
}
```

**Rules:**
- Fix-features must be narrowly scoped — fix the specific issue, nothing more
- Success criteria must include the original failing criterion (unchanged)
- Fix-features inherit the original feature's file scope
- A fix-feature that would require architectural changes is NOT a fix-feature —
  escalate to {GIT_USER} as a plan change

---

## 3. Present Fix Plan to {GIT_USER}

> ## Fix Plan — Validation Round {n}
>
> **{N} issues → {M} fix-features**
>
> | Fix | Original Feature | Issue | Scope |
> |-----|-----------------|-------|-------|
> | f1-fix1 | JWT token service | Clock skew in expiry | token.ts |
> | f3-fix1 | Rate limiting | Missing edge case | limiter.ts |
>
> **Skipped (non-critical):**
> - {suggestion that was logged but not fixed}
>
> **Needs clarification:**
> - {gap that requires {GIT_USER} input}
>
> Ready to dispatch fix workers?

**Wait for {GIT_USER}.**

---

## 4. Dispatch Fix Workers

Fix workers run exactly like original workers (step-mission-execute),
but with additional context:

- The validator's finding is included in the prompt
- The original worker's branch is the starting point
- The fix-feature spec is narrowly scoped

Update `status.json`: set fix-feature statuses to `pending`, set state to `"fixing"`.

Read `step-mission-execute.md` and dispatch. The execute step handles both
original features and fix-features identically — it reads `status.json`
and dispatches anything that is `pending` or `fixing`.

---

## 5. Re-Validate

After fix workers complete, read `step-mission-validate.md` again.
Validators run fresh — they don't know what was fixed. They re-evaluate
everything.

This creates the loop:

```
Execute → Validate → Fix → Execute → Validate → ...
```

The loop terminates when:
1. **All pass** — milestone validated, proceed to merge + next milestone
2. **Round limit reached** (4 rounds) — halt, escalate to {GIT_USER}
3. **{GIT_USER} cancels** — pause mission, return to huddle

---

## 6. Milestone Completion

When a milestone passes validation:

1. Update `status.json`:
   - All features in milestone: status `passed`
   - `current_milestone` → next milestone ID (or `null` if last)
   - `state` → `"advancing"` (or `"complete"` if last milestone)

2. Present to {GIT_USER}:

> ## Milestone {name} Complete
>
> - **Features:** {N} implemented, {M} fix rounds
> - **Validation rounds:** {n}
> - **Contract assertions covered:** {n}/{total}
>
> **Worktree branches to merge:**
> {list of branches}
>
> Next milestone: {next.name} ({K} features)
>
> Want to merge and continue, or review the branches first?

**Wait.**

If {GIT_USER} approves merge → execute merge strategy, then dispatch next milestone.
If last milestone → mission complete (see below).

---

## 7. Mission Complete

When all milestones pass:

1. Update `status.json`: `state: "complete"`

2. Run final synthesis — update `huddle-state.json` with:
   - Mission outcome as a decision
   - All features as action items (completed)
   - Validator findings as key moments

3. Write a raw event to `{HUDDLE_DIR}/raw/`:
```json
{
  "type": "milestone",
  "ts": 1744307200000,
  "topic": "Mission complete: {mission name}",
  "content": "All {N} features implemented across {M} milestones. {V} validation rounds total. {F} fix-features generated.",
  "personas": [],
  "by": "{GIT_USER}"
}
```

4. Present:

> ## Mission Complete
>
> **{mission name}** — all contract assertions verified.
>
> | Metric | Value |
> |--------|-------|
> | Features | {N} |
> | Fix features | {F} |
> | Milestones | {M} |
> | Validation rounds | {V} |
> | Contract assertions | {A}/{A} passed |
>
> All branches merged. {GIT_USER}, anything else?

---

## RETURN PROTOCOL

If {GIT_USER} cancels or pauses during the fix loop:

1. Save current state — fix-features generated, execution progress, validator reports
2. Update `status.json.state` to `"paused"`
3. **Re-read** `references/steps/step-02-discussion.md`
4. **Read** `huddle-state.json` — restore `active_personas` and `current_topic`
5. Tell {GIT_USER}: "Mission paused at fix round {n}. {N} fixes pending. Resume with 'continue the mission'."
6. Ask: "Want to go back to the huddle?"
7. **Wait.**
