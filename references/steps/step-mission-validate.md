# Step: Mission Validate — Independent Verification

This step spawns fresh-context validators to independently verify completed work.
Validators have NO implementation context. They evaluate against the validation
contract and success criteria only.

The key insight: **an agent that built something is biased toward confirming its
own work. A fresh reviewer with no implementation context catches more bugs.**

---

## Prerequisites

- All features in the current milestone have status `executed` in `status.json`
- `{HUDDLE_DIR}/mission/contract.md` exists
- `{HUDDLE_DIR}/mission/features.json` exists
- Worker branches are available (from worktree execution) or changes are committed

---

## 1. Load Mission State

Read:
- `{HUDDLE_DIR}/mission/status.json` — feature statuses and worker branches
- `{HUDDLE_DIR}/mission/contract.md` — the validation contract
- `{HUDDLE_DIR}/mission/features.json` — feature specs and success criteria

Increment `validation_rounds` in `status.json`.

---

## 2. Validator Types

Two types of validators run at each milestone:

### Scrutiny Validators (per-feature)
- One per completed feature
- Reviews the implementation AND the worker's test coverage
- Checks: does the code actually satisfy the success criteria?
- Checks: are the tests meaningful or just green-passing stubs?
- Has access to: the code diff, the tests, the feature spec, the contract
- Does NOT have: the worker's conversation/reasoning, implementation history

### Black-Box Validators (per-milestone)
- One for the entire milestone
- Tests the system as a whole against the validation contract
- Exercises behavioral assertions end-to-end
- Has access to: only the validation contract and the running system
- Does NOT have: any feature specs, implementation details, or code review

---

## 3. Dispatch Scrutiny Validators

For each feature with status `executed`:

Create an `Agent` tool call (no worktree needed — validators are read-only):

```
Agent(
    description="Validate: {feature.name}",
    prompt=scrutiny_validator_prompt(feature, contract)
)
```

**Issue ALL scrutiny validator Agent calls in a SINGLE message for parallel execution.**

### Scrutiny Validator Prompt Template

```
You are an independent code validator. You have NO knowledge of how this
feature was built — only what it should do. Your job is to find gaps,
not to fix them.

## Feature Under Review
Name: {feature.name}
ID: {feature.id}

## Specification
{feature.spec}

## Success Criteria
{feature.success_criteria — numbered list}

## Validation Contract (full mission context)
{contract.md contents}

## Files Changed by the Worker
{list of files from worker result or git diff}

## Instructions

1. Read all changed files carefully
2. Read the tests the worker wrote
3. Run the tests: verify they actually pass
4. For EACH success criterion, independently assess:
   - Is it fully implemented?
   - Is it tested meaningfully (not just a stub)?
   - Are there edge cases the worker missed?
5. Check for:
   - Security issues (injection, auth bypass, data exposure)
   - Error handling gaps
   - Performance concerns (N+1 queries, unbounded loops)
   - Code that contradicts the specification
   - Tests that pass but don't actually verify the criterion

## Rules

- You do NOT implement fixes. You report only.
- Be specific: "line 42 of token.ts handles expiry but doesn't check clock skew"
  not "token handling could be improved"
- If something is ambiguous in the spec, flag it as a GAP, not a FAIL
- Do not penalize style choices, naming conventions, or patterns that work correctly

## Output Format

For each success criterion:
```
CRITERION {n}: {criterion text}
VERDICT: PASS | FAIL | GAP
EVIDENCE: {what you observed}
DETAIL: {specific issue if FAIL or GAP, or confirmation if PASS}
```

Then a summary:
```
OVERALL: PASS | FAIL
PASS_COUNT: {n}/{total}
FAIL_COUNT: {n}
GAP_COUNT: {n}
CRITICAL_ISSUES: [{list of blocking issues}]
NON_CRITICAL: [{list of suggestions}]
```
```

---

## 4. Dispatch Black-Box Validator

After (or in parallel with) scrutiny validators, dispatch one black-box
validator for the entire milestone:

```
Agent(
    description="Black-box validate milestone {milestone.id}",
    prompt=blackbox_validator_prompt(contract, milestone)
)
```

### Black-Box Validator Prompt Template

```
You are a user-testing validator. You test the system as a black box.
You know NOTHING about how it was built — only what it should do.

## Validation Contract
{contract.md contents — this is your ONLY reference}

## Instructions

1. Read the validation contract carefully
2. For EACH behavioral assertion in the contract:
   a. Devise a test scenario that would verify it
   b. Execute the test (run commands, call APIs, check outputs)
   c. Record pass or fail with evidence
3. Also try:
   - Unexpected inputs (empty strings, special characters, huge payloads)
   - Boundary conditions mentioned or implied by the contract
   - Sequences that the contract implies should work (e.g., create then delete)

## Rules

- You are a user, not a developer. Test from outside.
- Do not read source code to decide what to test — only use the contract
- If you can't test an assertion (e.g., requires infrastructure you don't have),
  mark it UNTESTABLE with the reason
- Be honest: if it works, it works. Don't manufacture issues.

## Output Format

For each contract assertion:
```
ASSERTION {n}: {assertion text}
TEST: {what you did}
RESULT: PASS | FAIL | UNTESTABLE
EVIDENCE: {output, error message, or observation}
```

Then:
```
OVERALL: PASS | FAIL
ASSERTIONS_TESTED: {n}/{total}
ASSERTIONS_PASSED: {n}
ASSERTIONS_FAILED: {n}
UNTESTABLE: {n}
CRITICAL_FAILURES: [{list}]
```
```

---

## 5. Collect and Synthesize Validator Reports

After all validators complete:

1. Parse each scrutiny validator's output
2. Parse the black-box validator's output
3. Write individual reports to `{HUDDLE_DIR}/mission/reports/{feature_id}.json`:

```json
{
  "feature_id": "f1",
  "feature_name": "JWT token service",
  "validation_round": 1,
  "scrutiny": {
    "overall": "FAIL",
    "pass_count": 3,
    "fail_count": 1,
    "gap_count": 1,
    "critical_issues": [
      {
        "criterion": 2,
        "detail": "Token expiry check doesn't account for clock skew between services"
      }
    ],
    "non_critical": [
      "Consider adding rate limiting on token generation endpoint"
    ]
  },
  "timestamp": "2026-04-14T10:30:00Z"
}
```

4. Write milestone report to `{HUDDLE_DIR}/mission/reports/milestone_{milestone_id}.json`:

```json
{
  "milestone_id": "m1",
  "validation_round": 1,
  "blackbox": {
    "overall": "FAIL",
    "tested": 10,
    "passed": 8,
    "failed": 2,
    "untestable": 0,
    "critical_failures": [
      {
        "assertion": 4,
        "detail": "Expired tokens still return 200 instead of 401"
      }
    ]
  },
  "scrutiny_summary": {
    "features_passed": 2,
    "features_failed": 1,
    "total_critical_issues": 1
  },
  "overall_verdict": "FAIL",
  "timestamp": "2026-04-14T10:30:00Z"
}
```

---

## 6. Present Results to {GIT_USER}

Format the validation results clearly:

```
## Validation Report — Milestone {milestone.name} (Round {n})

### Black-Box Results
{passed}/{total} contract assertions passed.

**Failures:**
- Assertion {n}: {text} — {what failed}

### Per-Feature Scrutiny
| Feature | Verdict | Pass | Fail | Gap | Critical Issues |
|---------|---------|------|------|-----|-----------------|
| {name}  | PASS    | 3/3  | 0    | 0   | —               |
| {name}  | FAIL    | 2/4  | 1    | 1   | Clock skew...   |

### Critical Issues (must fix)
1. {feature}: {issue detail}

### Suggestions (non-blocking)
1. {suggestion}
```

Then:

If ALL pass:
> Milestone {name} validated. All contract assertions pass, all features verified.
> Ready to merge the worktree branches and move to the next milestone?

If ANY fail:
> {N} issues found. Want me to generate fix-features and re-dispatch workers?

**Wait for {GIT_USER}.**

If {GIT_USER} approves fixes → read `step-mission-fix.md`.
If {GIT_USER} approves merge → execute merge strategy from step-mission-execute.
If {GIT_USER} wants to review manually → show diffs, wait.

---

## Validation Round Limits

- Maximum 4 validation rounds per milestone
- If milestone hasn't converged after 4 rounds, halt and report to {GIT_USER}:
  > "Milestone {name} hasn't converged after {n} rounds. Remaining issues: {list}.
  > This might need a plan change rather than more fixes. Want to discuss in the huddle?"
- Route back to step-02 discussion if {GIT_USER} agrees

---

## RETURN PROTOCOL

If {GIT_USER} cancels validation or wants to return to the huddle:

1. Save all validator reports collected so far
2. Update `status.json` with current state
3. **Re-read** `references/steps/step-02-discussion.md`
4. **Read** `huddle-state.json` — restore `active_personas` and `current_topic`
5. Tell {GIT_USER}: "Validation paused. Reports saved. Resume with 'continue validation'."
6. Ask: "Want to go back to the huddle?"
7. **Wait.**
