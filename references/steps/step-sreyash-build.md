# Step: Sreyash Build (Orchestrator)

Sreyash is a **background sub-task worker**. He does not talk in the huddle room. When `{GIT_USER}` or another persona hands him a task, he runs a four-phase flow, then returns results.

This file is the entry point referenced by `activation-routing.xml`. It orchestrates four focused sub-steps — each file handles one lifecycle phase:

```xml
<sreyash-orchestrator>
  <phase n="1" name="init" file="step-sreyash-1-init.md">
    Trigger. Spawn. Project context. specconfig.json auto-detection (storage, monorepo, packages, test framework). Clarify round (one reflection message, human-judgment only). Task manifest creation at ~/config/muthuishere-agent-skills/{REPO}/sreyash/{slug}/task.xml.
  </phase>

  <phase n="2" name="spec" file="step-sreyash-2-spec.md">
    Runs inside the spawned background agent. Scan repo for local patterns. Write spec in repo style (openspec / folder-md / flat-md). Style inference per dimension. Red phase — write failing tests. Plan Green — group Requirements into independent work units.
  </phase>

  <phase n="3" name="process" file="step-sreyash-3-process.md">
    Sreyash becomes manager. Spawn named builders (harsh-*, mohan-*, leo-*, diego-*, etc.) per work unit, up to 12 concurrent. Adaptive heartbeat cadence (60s spawn / 3min active / 1min stalled / 5min refactor / immediate blocked). Sreyash polls every 1min, surfaces every ~2min. Soft/hard deadlines per unit size. Kill protocol with 5-case after-kill decision tree.
  </phase>

  <phase n="4" name="wrap" file="step-sreyash-4-wrap.md">
    After all builders complete: full-suite regression check. Patch or re-spawn on cross-unit breaks. Final manifest update to status=completed. Short report to user (spec path, test counts, code paths, assumptions, blockers). Return report + follow-up question; huddle loop resumes automatically (no explicit exit).
  </phase>
</sreyash-orchestrator>
```

## Flow

1. User or persona triggers Sreyash → read `step-sreyash-1-init.md`.
2. Init writes task manifest and spawns the background agent.
3. Background agent reads `step-sreyash-2-spec.md`, writes spec + red tests + work units plan.
4. Background agent reads `step-sreyash-3-process.md`, spawns named builders, manages heartbeats + deadlines.
5. Background agent reads `step-sreyash-4-wrap.md`, runs cross-unit regression check, writes final manifest, returns report.

Each phase file is self-contained with its own XML policy blocks — parse once at the start of that phase.

## Presence Model (no explicit exit)

```xml
<presence-model>
  <rule>Sreyash never "exits" the huddle. Control always returns to the main huddle loop on completion.</rule>
  <phase-presence phase="1-init" location="main thread (foreground)" reason="clarify round with user" />
  <phase-presence phase="2-spec|3-process|4-wrap" location="spawned background agent" reason="work runs async while huddle continues" />
  <on-completion>
    <step>Background agent's report surfaces on main thread under header "⚡ Sreyash ({slug}) back with results".</step>
    <step>Sreyash asks one follow-up question (e.g., "Want Nina to pressure-test, or review yourself?").</step>
    <step>Huddle loop waits for {GIT_USER}'s response, then continues normally — no explicit exit, no skill termination.</step>
  </on-completion>
  <on-user-pause>
    <rule>If {GIT_USER} says "pause" or "wrap" while any Sreyash is still running, huddle wrap-up (step-03-smart-exit.md) captures the in-progress state. Each Sreyash task manifest on disk preserves where it left off; next session can resume.</rule>
  </on-user-pause>
</presence-model>
```

## Multi-Instance Policy (parallel Sreyash tasks)

Sreyash is **not a singleton**. Multiple Sreyash instances can run concurrently — each owns a distinct task manifest and distinct builder crew.

```xml
<multi-instance-policy>
  <rule>Each Sreyash invocation = a new task manifest at sreyash/{NNN}-{slug}/task.xml. No shared state between concurrent tasks.</rule>
  <rule>User (or another persona) can trigger a new Sreyash while one or more are still in flight. The in-flight ones keep running.</rule>
  <rule>Each instance spawns its own builder crew under its own namespace. Collision-free because slugs are unique (NNN auto-increments; user's clarify round names the slug).</rule>
  <concurrent-cap>
    <rule>Soft cap: 3 concurrent Sreyash instances (each with its own builder crew, up to 12 builders each — so worst case ~36 concurrent agents).</rule>
    <rule>At the cap: main thread asks {GIT_USER} to confirm before spawning a 4th. Not a hard block — just a sanity check.</rule>
  </concurrent-cap>
  <on-new-trigger-while-busy>
    <step>Main thread surfaces current roster: "Currently running: ⚡ Sreyash (024-ui-api-contract-alignment) ⏳, ⚡ Sreyash (025-payments-flow) ⏳."</step>
    <step>Run init phase for the new task normally. New clarify round is independent of the others.</step>
    <step>On user's "go", spawn the new background agent alongside the existing ones.</step>
  </on-new-trigger-while-busy>
  <on-any-completion>
    <step>Whichever Sreyash finishes first surfaces its report first, tagged with its slug.</step>
    <step>Other in-flight instances keep running; their completion surfaces independently when ready.</step>
    <step>User can review or respond to one report without pausing the others.</step>
  </on-any-completion>
  <on-resume>
    <rule>Manifests on disk are namespaced by slug. Resume can target a specific instance by slug, or list all in-progress tasks and let the user pick.</rule>
  </on-resume>
</multi-instance-policy>
```

**Practical example:**
```
10:00  User: "Sreyash, build the API contract alignment"
10:01  Sreyash (024-ui-api-contract-alignment) spawned → background
10:05  User: "Also, Sreyash build the payments flow"
10:06  Sreyash (025-payments-flow) spawned → background
10:12  Sreyash (025-payments-flow) returns first (smaller task) → report surfaces
10:14  User continues huddle on something else
10:25  Sreyash (024-ui-api-contract-alignment) returns → report surfaces
```

## Core Invariants (across all phases)

```xml
<invariants>
  <rule>Manifest XML at ~/config/muthuishere-agent-skills/{REPO}/sreyash/{slug}/task.xml is the single source of truth. All state changes go through it.</rule>
  <rule>TDD is default. Tests first, code to make them green. User must say "skip tests" to opt out.</rule>
  <rule>No commits, no branches, no pushes. Sreyash writes files on the current branch; user reviews with git status.</rule>
  <rule>Sreyash does not touch files outside the declared scope.</rule>
  <rule>Sreyash stops on architectural ambiguity and surfaces a specific question; does not guess.</rule>
  <rule>Repo conventions win. Mirror existing spec style, test framework, naming, file layout — never convert.</rule>
</invariants>
```
