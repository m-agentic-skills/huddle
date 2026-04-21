# Step: Sreyash — Process (green phase, parallel builders, kill protocol)

Third phase. Sreyash becomes a manager, delegates green-phase implementation to named background builders, monitors heartbeats, enforces deadlines. All rules as XML policy for deterministic parsing.

## Green-Phase Policy

```xml
<green-phase-policy>
  <naming>
    <pattern>{orchestrator}-{greek-letter}</pattern>
    <greek-letter-pool order="sequential">
      <letter>alpha</letter>
      <letter>beta</letter>
      <letter>gamma</letter>
      <letter>delta</letter>
      <letter>epsilon</letter>
      <letter>zeta</letter>
      <letter>eta</letter>
      <letter>theta</letter>
      <letter>iota</letter>
      <letter>kappa</letter>
      <letter>lambda</letter>
      <letter>mu</letter>
    </greek-letter-pool>
    <rule>Orchestrator prefix is {BUILDER} (sreyash / hari / harshvardhan) — keeps namespaces separate when sibling orchestrators run in parallel.</rule>
    <rule>Examples: sreyash-alpha, sreyash-beta, sreyash-gamma; hari-alpha, hari-beta; harshvardhan-alpha.</rule>
    <rule>Letters are assigned sequentially to work units (u1 → alpha, u2 → beta, ...). Do not attach scope tags to the builder name — the scope lives in the unit column of the dispatch table, not the builder id.</rule>
    <rule>If work exceeds 12 letters in one run, continue with alpha-2, beta-2, ... — never fall back to personality names.</rule>
  </naming>

  <role-tint note="Personality-based role tints removed. All builders are interchangeable executors. Scope discipline is enforced via file-set + test-set in the sub-agent-prompt, not via builder identity." />

  <non-blocking>
    <rule>Every spawn uses `run_in_background: true`. Main conversation never blocks on builder completion.</rule>
    <rule>If the user switches topics mid-build, respond to the new topic; builders keep running; table re-renders when relevant again (completion notification, user asks, or synthesis).</rule>
  </non-blocking>

  <assignment-protocol>
    <rule>Concurrency cap: 12 in flight. Lower if work is tightly coupled.</rule>
    <case condition="≥2 independent units AND host supports background agents">Spawn one builder per unit, up to cap, all at once.</case>
    <case condition="more units than cap">Spawn first N. Queue the rest. Freed builder picks up next unit.</case>
    <case condition="1 unit OR host lacks concurrency">Spawn one builder sequentially.</case>
  </assignment-protocol>

  <sub-agent-prompt required-fields="builder-name, manifest-path, allowed-modify, allowed-create, allowed-create-under, off-limits, test-set, hard-rules">
    <!-- Sreyash writes this spec before dispatch. Ambiguity here is the #1 cause of runaway builders. -->

    <field name="builder-name" example="sreyash-alpha" />
    <field name="manifest-path" example="~/.config/muthuishere-agent-skills/{REPO}/sreyash/{slug}/task.xml" />

    <field name="allowed-modify" description="Existing files the builder may edit. Enumerate each; no globs.">
      <example>
        apps/ui/src/lib/api.ts
        apps/ui/src/components/ProfileCard.tsx
      </example>
    </field>

    <field name="allowed-create" description="New files the builder may create. Enumerate each; no globs. Empty if pure-modify unit.">
      <example>
        apps/ui/src/lib/quality.ts
        apps/ui/src/lib/quality.test.ts
      </example>
    </field>

    <field name="allowed-create-under" required="false" description="Narrow directories for new files whose names aren't knowable up front (e.g., one test per scenario). Never repo root, never a whole app. Omit if everything is pre-listed in allowed-create.">
      <example>
        apps/ui/src/components/avatar/
      </example>
    </field>

    <field name="off-limits" description="Forbidden paths. Must include sibling builders' allowed-modify + allowed-create so parallel builders never race.">
      <example>
        apps/api/**
        infra/**
        any file assigned to sreyash-beta or sreyash-gamma this run
      </example>
    </field>

    <field name="test-set" description="Exact test files or test names to turn green. Same enumeration discipline as allowed-modify." />

    <hard-rule>Every write must match allowed-modify, allowed-create, or fall under allowed-create-under. Otherwise: stop, set status=blocked, reason `scope violation: attempted {path}`.</hard-rule>
    <hard-rule>Do not read off-limits paths for context. (That's how scope drift starts.)</hard-rule>
    <hard-rule>Do not run tests outside test-set.</hard-rule>
    <hard-rule>No commits, no branches.</hard-rule>
    <hard-rule>Update own &lt;unit&gt; element in manifest XML as you progress.</hard-rule>
    <hard-rule>Return short status: files written, tests green/red, blockers.</hard-rule>
  </sub-agent-prompt>

  <scope-spec-derivation>
    <!-- Sreyash derives scope fields from each unit before spawning. His duty, not the builder's. -->
    <rule>allowed-modify = every file a Requirement references, nothing more.</rule>
    <rule>allowed-create enumerated where possible; use allowed-create-under only when names aren't knowable up front.</rule>
    <rule>off-limits = (everything outside this unit's scope) minus (shared read-only refs). In parallel runs, it MUST include every sibling builder's allowed-modify + allowed-create.</rule>
    <rule>If scope can't be enumerated cleanly, the unit is too big or vague. Split or clarify with user. Never spawn on fuzzy scope.</rule>
    <rule>Derivation runs in background inside Sreyash's orchestrator context. Main channel stays silent; user sees only the dispatch table, blockers, and completion — not the planning.</rule>
  </scope-spec-derivation>

  <comms-bus>
    <rule>Manifest XML is the comms bus. Builders write to their &lt;unit&gt;/&lt;progress&gt;; Sreyash reads.</rule>
    <rule>User-facing turns render progress as a markdown table per `references/dispatch-table.md`. No linear status lines.</rule>
    <rule>Builders do not print to the main channel. Sreyash is the only voice there.</rule>
  </comms-bus>

  <builder-heartbeat-cadence>
    <state name="just-spawned" window="first 60s" interval="one-shot at 60s" update="parsed manifest, started, running tests" />
    <state name="active-progress" condition="tests flipping red→green OR new files written" interval="3 min" />
    <state name="stalled" condition="no manifest change for 2+ intervals OR 2+ test runs with no new greens" interval="1 min" update="what's blocking" />
    <state name="refactor-cleanup" condition="all tests green, pure housekeeping" interval="5 min" />
    <state name="blocked" condition="hit architectural ambiguity" interval="immediate" action="set status=blocked, fill &lt;blockers&gt;, stop work" />
  </builder-heartbeat-cadence>

  <sreyash-polling-cadence>
    <rule interval="1 min">Poll manifest during green phase.</rule>
    <rule interval="≤2 min">Surface one-line summary to user (noise control).</rule>
    <immediate-surface>
      <on>any builder completion (green OR blocked)</on>
      <on>any &lt;blockers&gt; entry appearing in a unit</on>
      <on>any builder hitting soft OR hard deadline</on>
    </immediate-surface>
  </sreyash-polling-cadence>

  <manager-output-templates>
    <!-- Templates follow references/dispatch-table.md. Table first, prose below. -->

    <template event="on-spawn">
      Spawned N builders in background.

      | id | unit | status | progress | artifacts |
      |----|------|--------|----------|-----------|
      | sreyash-alpha | u1 — frontend types (3 tests) | 🏃 | 0/3 | — |
      | sreyash-beta  | u2 — api validation (4 tests) | 🏃 | 0/4 | — |
      | sreyash-gamma | u3 — rename sweep (5 files)   | 🏃 | 0/5 | — |
    </template>

    <template event="periodic-or-completion">
      ### Sreyash's builders — in flight

      | id | unit | status | progress | artifacts |
      |----|------|--------|----------|-----------|
      | sreyash-alpha | u1 — frontend types | ✅ | 3/3 | `apps/ui/src/lib/api.ts` (+12 lines) |
      | sreyash-beta  | u2 — api validation | 🏃 | 2/4 | `apps/api/src/modules/profile/profile.service.ts` |
      | sreyash-gamma | u3 — rename sweep   | 🏃 | 4/5 | 4 files touched |
    </template>

    <template event="on-blocker">
      Row flips to ⚠; block reason in the artifacts column. One-line surface below the table:
      "⚠ sreyash-delta blocked: 'column type ambiguous — INT or BIGINT?'. Others continuing."
    </template>
  </manager-output-templates>

  <deadlines>
    <size name="small" criteria="≤3 tests AND ≤3 files" soft="10 min" hard="15 min" />
    <size name="medium" criteria="4-8 tests OR 4-8 files" soft="15 min" hard="25 min" />
    <size name="large" criteria=">8 tests OR cross-cutting" soft="25 min" hard="40 min" />
  </deadlines>

  <soft-deadline-action>
    <case condition="steady progress (new green in last 2-3 min, file set growing)">
      <action>extend silently by 50%</action>
    </case>
    <case condition="no progress (same test counts + same file list for 2 intervals)">
      <action>warn builder via re-read-and-status prompt, give 2 more min</action>
      <follow-up condition="still no progress after warn"><action>KILL</action></follow-up>
    </case>
  </soft-deadline-action>

  <hard-deadline-action>
    <rule>Kill unconditionally regardless of progress. Runaway builders are worse than slow ones.</rule>
  </hard-deadline-action>

  <after-kill-decision-tree>
    <case id="ak-1" condition="builder touched files outside declared set OR ran many tests without greens">
      <diagnosis>Unit was too big</diagnosis>
      <action>Split unit into 2-3 smaller units with tighter file sets. Spawn fresh builders with the next Greek letters (e.g., sreyash-eta, sreyash-theta).</action>
    </case>
    <case id="ak-2" condition="&lt;blockers&gt; entry populated OR tests failing with consistent error">
      <diagnosis>Stuck on specific obstacle</diagnosis>
      <action>Surface to user with exact obstacle. Do NOT respawn blindly.</action>
    </case>
    <case id="ak-3" condition="some greens landed, work stalled near end">
      <diagnosis>Slow but directionally right</diagnosis>
      <action>Respawn with next unused Greek letter (e.g., sreyash-beta killed → respawn as sreyash-zeta). Keep same file + test set.</action>
    </case>
    <case id="ak-4" condition="no manifest updates after 60s startup window">
      <diagnosis>Zero progress. Prompt or setup broken.</diagnosis>
      <action>Respawn once with tighter prompt. If still fails → fall through to ak-2.</action>
    </case>
    <case id="ak-5" condition="multiple kills across different builders in same window">
      <diagnosis>Host is degraded</diagnosis>
      <action>Drop back to serial. Sreyash runs remaining units himself, one at a time. Report to user.</action>
    </case>
    <audit-log>Every kill/respawn/extend action written as &lt;event&gt; under the unit in the manifest.</audit-log>
  </after-kill-decision-tree>

  <failure-handling>
    <case on="builder crashes">
      <rule>Manifest retains last &lt;unit&gt; state. Run after-kill-decision-tree.</rule>
    </case>
    <case on="builder drifts outside assigned files" detection="Sreyash polling catches file-set violation">
      <rule>Treat as ak-1 (too big). Kill and split.</rule>
    </case>
    <case on="multiple builders blocked on same thing">
      <diagnosis>Shared-context problem.</diagnosis>
      <action>Surface once to user. Hold all blocked units. Let non-blocked ones finish.</action>
    </case>
  </failure-handling>
</green-phase-policy>
```

## Handoff

When all builders complete (green or blocked), proceed to `step-sreyash-4-wrap.md`.
