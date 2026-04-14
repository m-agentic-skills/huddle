# Step: Mission Plan

The huddle becomes the orchestrator. This step converts discussion outcomes
into an executable mission with a validation contract, feature decomposition,
and milestone grouping.

This step runs when {GIT_USER} says: "execute this", "build this", "mission mode",
"turn this into a mission", "let's ship this", "make it happen".

---

## Prerequisites

- The huddle must have active state — at least one decision, a stated direction,
  or a plan that {GIT_USER} has approved in discussion.
- If no direction exists yet, tell {GIT_USER}: "We need a plan first. What are we building?"
  and route back to step-02 discussion. Do not proceed.

---

## Phase 1: Write the Validation Contract

**Do this BEFORE decomposing features.** The contract defines what "done" looks
like independently of how it gets built. Writing it first prevents implementation
bias from leaking into the definition of correctness.

Read `huddle-state.json`, raw events, and conversation context. Produce a
validation contract.

Write to `{HUDDLE_DIR}/mission/contract.md`:

```markdown
# Validation Contract

## Mission
{one-line description of what we're building}

## Context
{2-3 sentences — why this matters, what the huddle decided, constraints}

## Behavioral Assertions

Each assertion is independently testable. A validator can verify each one
without knowing how it was implemented.

1. [ ] {assertion — observable behavior, not implementation detail}
2. [ ] {assertion}
...

## Out of Scope
- {explicit exclusion to prevent scope creep}
- {explicit exclusion}

## Definition of Done
All assertions pass. No critical validator findings unresolved.
```

**Rules:**
- Assertions must describe observable behavior ("User can log in with email and password")
  not implementation details ("JWT token is generated using RS256")
- Each assertion must be independently verifiable by a fresh-context agent
- Aim for 5–15 assertions. Fewer than 5 means the mission is too vague.
  More than 15 means the mission should be split.
- Include negative assertions where relevant ("System rejects expired tokens")

Present to {GIT_USER}:

> Here's the validation contract — what "done" looks like before we define any features.
> {show contract}
> Want to adjust anything before I break down the work?

**Wait.** Do not proceed until {GIT_USER} approves.

---

## Phase 2: Decompose into Features

After contract approval, decompose the mission into features grouped by milestone.

Write to `{HUDDLE_DIR}/mission/features.json`:

```json
{
  "mission": "short description",
  "contract_assertions": 12,
  "created_at": "2026-04-14T10:00:00Z",
  "milestones": [
    {
      "id": "m1",
      "name": "Core functionality",
      "description": "what this milestone achieves",
      "features": [
        {
          "id": "f1",
          "name": "feature name",
          "spec": "precise description — what to build, not how",
          "success_criteria": [
            "criterion 1 — maps to contract assertion(s)",
            "criterion 2"
          ],
          "contract_assertions": [1, 3],
          "test_first": true,
          "depends_on": [],
          "estimated_files": ["src/auth/token.ts", "src/auth/token.test.ts"],
          "context_files": ["src/auth/config.ts"]
        }
      ]
    }
  ]
}
```

**Decomposition rules:**
- Each feature must be completable by a single isolated worker
- Features within a milestone must have NO inter-dependencies (they run in parallel)
- Dependencies between features go in separate milestones (m1 before m2)
- Success criteria must trace back to contract assertions
- `context_files` = files the worker should read for understanding but not modify
- `estimated_files` = files the worker will create or modify
- `test_first: true` means the worker writes tests before implementation

Present to {GIT_USER}:

> Here's the breakdown:
> - **{N} features** across **{M} milestones**
> - Milestone 1: {K} features that run in parallel
> {show feature list with names and success criteria}
> Ready to dispatch workers?

**Wait.** Do not proceed until {GIT_USER} approves.

---

## Phase 3: Initialize Mission State

Write to `{HUDDLE_DIR}/mission/status.json`:

```json
{
  "state": "planned",
  "current_milestone": "m1",
  "validation_rounds": 0,
  "features": {
    "f1": {
      "status": "pending",
      "worker_branch": null,
      "worker_worktree": null,
      "validator_report": null
    }
  },
  "blocked": false,
  "block_reason": null
}
```

Feature status values: `pending` → `executing` → `executed` → `validating` → `passed` | `failed` → `fixing`

---

## Phase 4: Choose Execution Backend

Present the execution options to {GIT_USER}:

> How do you want to run this?
>
> **Option 1: Parallel worktree agents** (recommended)
> I spawn one agent per feature, each in its own git worktree. They run
> concurrently, can't interfere with each other, and commit independently.
> Best for: code changes that touch different files.
>
> **Option 2: Sequential single-thread**
> I execute features one at a time in the current checkout.
> Best for: small missions, tightly coupled changes, or when you want to
> review each feature before the next starts.
>
> **Option 3: External dispatch**
> I write the specs to files. You dispatch workers yourself using Claude CLI,
> Codex, Copilot, or any other agent. They write results back via
> `huddle_writer.py`. Best for: using different models or services per worker.

**Wait for {GIT_USER}'s choice.**

After choice, read `step-mission-execute.md` to begin dispatch.

---

## Execution Backend Details (for {GIT_USER} reference)

### Option 1: Agent(isolation="worktree") — Built-in Parallel

How it works:
- Claude Code's `Agent` tool accepts `isolation: "worktree"`
- This creates a temporary git worktree — a full independent checkout
- Multiple `Agent` calls in a **single message** run **concurrently**
- Each agent has full tool access (Read, Write, Edit, Bash, Grep, etc.)
- The worktree is auto-cleaned if no changes; branch path returned if changes made
- Workers can commit in their worktree without affecting the main checkout

Constraints:
- All agents share the same Claude session's token budget
- Each agent gets fresh context (no conversation history from the huddle)
- Worktrees share the same `.git` — branches are real git branches
- Merge conflicts between worktrees must be resolved after collection

### Option 2: Sequential Execution

How it works:
- Features execute one at a time in the current working directory
- Each feature is treated as a sub-task with its own RETURN PROTOCOL
- {GIT_USER} can review and approve each feature before the next starts

### Option 3: External Dispatch

How it works:
- Mission plan files (`contract.md`, `features.json`) are written to `{HUDDLE_DIR}/mission/`
- External agents read the spec and execute independently
- Results written back via: `{PYTHON_BIN} {SKILL_ROOT}/scripts/huddle_writer.py {HUDDLE_DIR} '{event_json}'`
- Claude CLI: `claude --print "Read the spec at {path} and implement feature {id}"`
- Codex/Copilot: Point them at the feature spec file

Interop format (for any external agent):
```bash
{PYTHON_BIN} scripts/huddle_writer.py {HUDDLE_DIR} '{"type":"feature_complete","feature_id":"f1","branch":"feat-f1","status":"done","tests_pass":true}'
```

---

## RETURN PROTOCOL

If {GIT_USER} cancels or defers the mission at any phase:

1. Save whatever state was created (contract, features) to `{HUDDLE_DIR}/mission/`
2. Set `status.json` state to `"deferred"`
3. **Re-read** `references/steps/step-02-discussion.md`
4. **Read** `huddle-state.json` — restore `active_personas` and `current_topic`
5. Tell {GIT_USER}: "Mission plan saved. You can resume with 'start the mission' anytime."
6. Ask: "Want to pick up where we left off in the huddle, or take this in a new direction?"
7. **Wait.** Do not continue.
