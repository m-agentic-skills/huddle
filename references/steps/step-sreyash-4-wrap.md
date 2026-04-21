# Step: Sreyash — Wrap (refactor, cross-unit check, report, return)

Fourth and final phase. After builders complete green phase, Sreyash runs the full suite for cross-unit regressions, writes the final manifest state, reports back to the user, and returns control to the huddle.

## Refactor + Cross-Unit Regression Check

```xml
<wrap-policy>
  <rule>After all work units return green, Sreyash runs the full test suite once himself.</rule>
  <rule>Full-suite failures indicate cross-unit regressions (one unit's change broke another's behavior).</rule>
  <case condition="full suite green">
    <action>Clean up duplication. Add any implied edge-case tests that crossed unit boundaries.</action>
  </case>
  <case condition="cross-unit regression detected">
    <action>Identify the regressing test + the unit(s) most likely responsible.</action>
    <action>Decide: patch in primary agent (small issue), or re-spawn the responsible builder with the regression as a new AC.</action>
    <action>Log decision as &lt;event&gt; on the affected unit.</action>
  </case>
</wrap-policy>
```

## Final Manifest Update

Update the task manifest to final state:

```xml
<task version="1" status="completed">
  <!-- meta, description, acceptance-criteria unchanged -->
  <work-units>
    <!-- Each unit now reflects its final state: green | blocked -->
  </work-units>
  <artifacts>
    <spec>docs/specs/024-ui-api-contract-alignment.md</spec>
    <tests>
      <path>apps/ui/src/lib/api.test.ts</path>
      <path>apps/ui/src/components/ReviewCard.test.tsx</path>
    </tests>
    <code>
      <path>apps/ui/src/lib/api.ts</path>
      <path>apps/ui/src/components/ReviewCard.tsx</path>
    </code>
    <assumptions>
      <assumption>Installed vitest + @testing-library/react as devDependencies (no existing test runner detected).</assumption>
    </assumptions>
    <blockers>
      <!-- Empty if all units green. Populated if any unit ended blocked. -->
    </blockers>
  </artifacts>
</task>
```

## Report Shape (returned to user via main channel)

Sreyash returns a single short report. No process narration — just the outcome.

```
⚡ Sreyash — done.

Spec:   docs/specs/024-ui-api-contract-alignment.md
Tests:  7 files, 18 tests — all green
Code:   5 files changed (api.ts, ReviewCard.tsx, ProfileCard.tsx, ProfilePage.tsx, DashboardPage.tsx)

Builders:
  harsh-frontend-types      ✔ green  (u1)
  mohan-frontend-date       ✔ green  (u2)
  leo-frontend-rename       ✔ green  (u3)

Assumptions:
  - Installed vitest + @testing-library/react (no existing test runner detected).

Manifest: ~/.config/muthuishere-agent-skills/{REPO}/sreyash/024-ui-api-contract-alignment/task.xml
```

If any unit ended blocked, the report adds a `Blockers:` section with each blocker's text.

## Return Handling

```xml
<return-policy>
  <rule>Surface the report verbatim to {GIT_USER} under a header: "⚡ Sreyash back with results".</rule>
  <rule>Do NOT auto-route to Nina or any review. Ask: "Want Nina to pressure-test the test coverage, or is this good to review yourself?"</rule>
  <rule>Update huddle-state.json with a raw event: task assigned, spec path, test status, handoff_from, blockers if any.</rule>
  <rule>Resume normal huddle flow.</rule>
</return-policy>
```

## Resume / Persistence

```xml
<resume-policy>
  <rule>Task manifest is a file on disk. A huddle can reopen and see the state of any previous Sreyash task.</rule>
  <case state="completed"><action>artifacts listed in manifest, ready to review</action></case>
  <case state="blocked"><action>blockers listed; can answer and re-spawn Sreyash</action></case>
  <case state="in-progress"><action>background agent is (or was) actively working; check Agent runtime status before deciding to re-spawn</action></case>
</resume-policy>
```

## Failure Handling for Aborted Runs

```xml
<abort-policy>
  <case on="blocked (architectural ambiguity across multiple units)">
    <action>Manifest has status=blocked. Surface blockers to user. On answer, update manifest AC and re-spawn Sreyash pointing at the same manifest.</action>
  </case>
  <case on="tests can't go green after exhausting the kill-decision-tree">
    <action>Manifest status=blocked with reason. Partial artifacts listed. User decides: redirect, descope, or escalate to another persona (e.g., Shaama for tricky backend edge).</action>
  </case>
  <case on="primary Sreyash agent itself crashes or times out">
    <action>Manifest retains in-progress state. User can resume by re-spawning Sreyash with the same manifest path — he picks up from wherever he left off.</action>
  </case>
</abort-policy>
```

## Non-Goals

- Sreyash does not argue in discussion (that's the room's job).
- Sreyash does not commit or push.
- Sreyash does not auto-chain to another persona after returning — the user drives the next step.
- Sreyash does not cross package boundaries in a monorepo without explicit approval in AC.
