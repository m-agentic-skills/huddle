# Huddle Flow Control — Architecture Spec

**Date:** 2026-04-05
**Status:** Implemented
**Informed by:** BMAD party-mode patterns, Suren's architecture review

---

## Why This Exists

Huddle is a resumable, multi-persona discussion tool. Without explicit flow-control rules,
agents running sub-tasks (Deepak writing docs, Amara researching, Elango producing specs)
had no formal contract for how to hand back control to the huddle. The result was:

- Sub-tasks completing and immediately chaining into another action without waiting
- Resume opening a fresh huddle instead of restoring the saved session
- Wrap-up and pause being treated the same way, losing the "deliberate pause" state
- No clear signal to the agent about when to stop vs when to keep going

The goal: every transition — round end, sub-task completion, resume, persona handoff,
exit — has one correct, predictable behaviour.

---

## Core Principle: {GIT_USER} Always Drives

The agent never advances the agenda on its own. After every round or sub-task:
- STOP
- Wait for {GIT_USER}'s natural response
- Only then continue

This is not a menu shown after every round. Normal rounds end with a question or an
open prompt and then wait. The wrap-up checkpoint appears only when a topic/task
naturally completes.

---

## The Four Transitions

### 1. STOP — End of a Normal Round

After every persona round or output:
- End with a question to {GIT_USER} or a clear open prompt
- Do not chain into the next persona or topic automatically
- Wait

**What triggers wrap-up checkpoint (not every round — only on genuine completion):**

When the round clearly completed {GIT_USER}'s stated objective, the facilitator surfaces:

```
We've covered the main objective for this round.
Done: X, Y, Z
Open: A
{GIT_USER}, want to wrap here, save and pause, or keep going?
```

**What triggers immediate smart exit:**

Recognised phrases route directly to `step-03-smart-exit.md`:
- "that's enough", "wrap up", "end meeting", "close the huddle"
- "save and pause", "pause here", "stop here", "good for now"

---

### 2. RETURN — Sub-Task Completes, Hands Back

When a persona runs a task (Deepak documents, Amara researches, Elango produces a spec):

**Every sub-task step file must end with this RETURN PROTOCOL block:**

```
1. Announce completion briefly
2. Re-read step-02-discussion.md to restore the discussion loop
3. Read huddle-state.json — restore active_personas and current_topic
4. Ask: "{GIT_USER}, want to pick up where we left off or take this in a new direction?"
5. Wait. Do not start another persona round or sub-task.
```

Elango updates `huddle-state.json` silently after the return, before the next turn.

**Why in the step file, not just in routing XML?**

Central routing rules get ignored when an agent is deep inside a sub-task step.
Putting the RETURN PROTOCOL at the bottom of each step file ensures the agent
reads and follows it at exactly the right moment — after it finishes the task.
This is the pattern BMAD uses in `step-03-graceful-exit.md`.

---

### 3. RESUME — Re-entering After a Break

When the huddle opens and today's note already has content → always resume, never restart.

Resume behaviour is driven by `meeting_status` in `huddle-state.json`:

| `meeting_status` | Behaviour |
|---|---|
| `"active"` | Mid-session resume. Restore room and continue from last point. |
| `"paused"` | Deliberate pause. Summarise what was covered, ask where to pick up. |
| `"closed"` | Previous session ended. Start fresh but load history as context. |

On resume:
- Restore `active_personas` from `huddle-state.json` — do not show the full roster
- Summarise open questions and action items
- Note any new repo activity since last save
- Ask {GIT_USER} where to pick up. Wait.

---

### 4. HANDOFF — Persona Takes a Task

When {GIT_USER} directs a persona to do something:
- That persona runs the task
- Announces completion
- Invokes RETURN PROTOCOL
- Does not continue conversationally

Handoffs are single-turn. One persona runs, returns result, hands back.
No chaining to another persona before {GIT_USER} responds.

---

## State Contract — `meeting_status`

`meeting_status` is written by `step-03-smart-exit.md` on every exit path:

```json
{
  "meeting_status": "paused"
}
```

Values:
- `"active"` — set at huddle open, maintained throughout the session
- `"paused"` — set when user deliberately pauses (saves state, intends to resume)
- `"closed"` — set when user fully ends the session

---

## Project Documentation State — `project-state.json`

Separate from huddle state. Repo-scoped (not branch-scoped).

Path: `~/.config/muthuishere-agent-skills/{reponame}/project-state.json`

```json
{
  "reponame": "huddle",
  "project_doc": "~/.config/muthuishere-agent-skills/huddle/project.md",
  "generated_at": "2026-04-05T15:00:00+00:00",
  "last_commit": "abc1234",
  "stack": ["Python", "JavaScript"]
}
```

`project_state.py check` gates (all must pass for scan to be offered):
1. Git repo present
2. `gh` authenticated
3. Git remote exists
4. At least one commit

Refresh logic (Option B — weekly gate):
- No state → first time → scan
- Age < 7 days → silent skip
- Age ≥ 7 days, same HEAD → silent skip
- Age ≥ 7 days, new commits → Deepak offers refresh once per session

---

## Deepak's Document Flow

```
Huddle opens
  └─ project_state.py check
       ├─ scan=false (gates failed or within 7 days) → silent, no offer
       └─ scan=true
            ├─ no project.md → PROJECT_DOC_MISSING=true
            │    └─ Deepak offers: "I don't see any project docs yet. Want me to write one?"
            │         ├─ No  → DEEPAK_DOC_OFFERED=true, continue huddle
            │         └─ Yes → step-deepak-document.md runs
            │                    └─ RETURN PROTOCOL → back to huddle
            └─ project.md exists but stale
                 └─ Deepak offers: "Docs are N days old and repo has changed. Refresh?"
                      ├─ No  → DEEPAK_DOC_OFFERED=true, continue huddle
                      └─ Yes → step-deepak-document.md runs
                                 └─ RETURN PROTOCOL → back to huddle
```

Deepak offers at most once per session regardless of answer.

---

## Files Involved

| File | Role |
|---|---|
| `references/activation-routing.xml` | `<flow-control>` policy — STOP, SMART EXIT, RETURN, RESUME, HANDOFF |
| `references/steps/step-01-meeting-init.md` | Runs `project_state.py check`, sets `PROJECT_SCAN` and `PROJECT_DOC_MISSING` |
| `references/steps/step-02-discussion.md` | `<deepak-doc-rules>` — Deepak offer logic, `DEEPAK_DOC_OFFERED` tracking |
| `references/steps/step-03-smart-exit.md` | Writes `meeting_status` — `"paused"` or `"closed"` |
| `references/steps/step-deepak-document.md` | Deepak's scan + write + RETURN PROTOCOL |
| `scripts/project_state.py` | `check` / `read` / `write` for `project-state.json` |

---

## What Was Deliberately Not Adopted from BMAD

| BMAD pattern | Why not adopted |
|---|---|
| `[E] Exit` shown after every round | Too mechanical for huddle — normal rounds just wait naturally |
| Multiple scan modes (initial, full rescan, deep dive) | Huddle only needs a quick one-pager, not a 6-file doc suite |
| Frontmatter YAML for state tracking | Huddle uses `huddle-state.json` — already established pattern |
| Agent farewell sequence on exit | Huddle exits are practical saves, not theatrical goodbyes |

BMAD's **RETURN PROTOCOL** pattern (in step-03-graceful-exit.md) was adopted directly —
it is the right mechanism for sub-tasks handing back to a parent flow.
