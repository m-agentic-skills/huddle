# Step: Sreyash Build (Orchestrator — shared by Sreyash, Hari, Vinish)

Three builders share this orchestrator: **Sreyash** (primary), **Hari** (sibling), **Vinish** (sibling). Same flow, same phase files, same capabilities — distinct names so the user can run parallel builds without confusion. None talk in the huddle room.

```xml
<builder-delegation-policy>
  <rule>User always addresses "Sreyash". Hari and Vinish are on-call siblings behind Sreyash's name — not directly addressable.</rule>

  <resolution-order>
    <step n="1">Scan in-flight builder tasks (look at sreyash/, hari/, vinish/ folders for manifests with status="in-progress").</step>
    <step n="2">If Sreyash has no active task → identity = Sreyash.</step>
    <step n="3">Else if Hari has no active task → identity = Hari. Surface to user: "⚡ Sreyash is busy on {sreyash-current-slug}; 🛠️ Hari is picking this one up."</step>
    <step n="4">Else if Vinish has no active task → identity = Vinish. Surface: "⚡ Sreyash and 🛠️ Hari are busy; 🧰 Vinish is picking this one up."</step>
    <step n="5">Else (all three in flight) → ask {GIT_USER}: "All three builders are busy (Sreyash on {slug-a}, Hari on {slug-b}, Vinish on {slug-c}). Want to wait for the first to finish, or drop one of those tasks to free a slot?"</step>
  </resolution-order>

  <rule>The resolved identity is referred to as {BUILDER} throughout the phase files. All user-facing output — reflection messages, completion reports, "{BUILDER} back with results" header — uses {BUILDER}, not hardcoded "Sreyash".</rule>
  <rule>Task manifest lives at ~/config/muthuishere-agent-skills/{REPO}/{builder-lowercased}/{NNN}-{slug}/task.xml. Each sibling has its own namespace so parallel tasks don't collide.</rule>
  <rule>All three are non-discussion personas; none appear in normal huddle rounds.</rule>
</builder-delegation-policy>
```

Whenever a phase file refers to "Sreyash", substitute `{BUILDER}` — the current invocation's resolved identity. Filenames keep the historical `sreyash` prefix; the runtime identity is what the user sees.

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
    <rule>Soft cap: 3 concurrent builder instances — naturally matches the three-name roster (Sreyash, Hari, Vinish). One task per builder name at a time.</rule>
    <rule>Worst case per-task: up to 12 green-phase builders per task * 3 tasks = ~36 concurrent agents across the system.</rule>
    <rule>At the cap: main thread asks {GIT_USER} to confirm before spawning a 4th (requires reusing one of the three names for a 2nd parallel task).</rule>
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
