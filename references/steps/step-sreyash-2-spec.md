# Step: Sreyash — Spec (discovery, write spec, red tests, plan green)

Second phase. Runs inside the background agent spawned by the init phase. Produces the discovery report, writes the spec, writes failing tests (Red), plans the green-phase work units.

## Discovery Phase (mandatory before spec)

Sreyash treats the spec as a HYPOTHESIS, not a contract. Discovery is what makes the difference between code that passes mocked tests and code that works in the browser.

```xml
<discovery-policy>
  <rule id="d-01-scale-to-tier">
    Discovery depth scales to task tier (set in step-sreyash-1-init.md task-tiering-policy).
    TINY: 1-line — "no data-flow / async / mock risks." Done.
    SMALL: single parallel-read pass for touched files + direct callers/callees.
    MEDIUM: full data-flow trace, async map, sibling reads, mock-risk audit.
    LARGE: MEDIUM + cross-package contract review + sibling implementations across packages.
  </rule>

  <rule id="d-02-parallel-reads">
    All discovery file reads MUST be dispatched in parallel (single message, multiple Read tool calls). Serial reads are the #1 cause of slow Sreyash sessions.
  </rule>

  <rule id="d-03-five-checks" applies-to="SMALL/MEDIUM/LARGE">
    For every entity in the spec (component, hook, endpoint, model), Sreyash answers all five:
    1. **Data flow** — where does this entity's data originate (DB / API / parent prop / context / route param)? Where does it sink (UI render / response body / persisted state)?
    2. **Async dependencies** — what hooks, queries, contexts, promises gate this change? What's the initial-render state of each (null? empty? loading?)?
    3. **External state surfaces** — what props from parents, route params, contexts, env-driven config does the change read?
    4. **Mock-vs-real risk** — for every test mock the spec implies, ask "if this mock returns instantly with seeded data, would the test pass even if the real thing is broken?" If yes → flag MOCK_RISK.
    5. **Sibling implementations** — find 2-3 similar features in the same repo (same monorepo package or cross-package). Note their handling of the same five checks.
  </rule>

  <rule id="d-04-discovery-report">
    Output a discovery report to the manifest under &lt;discovery&gt;. Format below. Max 1 page for MEDIUM/LARGE; 1-3 lines for SMALL; 1 line for TINY.
  </rule>

  <rule id="d-05-checkpoint-on-risk">
    If discovery surfaces ANY of these, Sreyash emits a follow-up message (cr-04 in step-1) BEFORE writing the spec:
    - MOCK_RISK on a load-bearing async dependency
    - Sibling implementations diverge on a load-bearing pattern
    - Spec contradicts observed data-flow
    - Async race condition the spec doesn't address
  </rule>
</discovery-policy>
```

**Discovery report shape (manifest `<discovery>` block):**

```xml
<discovery tier="MEDIUM" elapsed-sec="42">
  <data-flow>
    <entity name="profile.email">
      <source>useProfile() React Query hook → /api/me</source>
      <sink>BillingProfileForm input value</sink>
      <initial-state>null until query resolves (~80-300ms)</initial-state>
    </entity>
  </data-flow>

  <async-dependencies>
    <dep>useProfile() — async, may be null on first render</dep>
    <dep>tax-quote endpoint — debounced, 200ms</dep>
  </async-dependencies>

  <external-state>
    <prop>nav state { snapshot, packKey } from BuyCreditsPage</prop>
    <context>useUser() (Firebase auth state)</context>
  </external-state>

  <mock-risks>
    <risk severity="HIGH">
      Test mocks useProfile() with synchronous return. Real flow has 80-300ms async window.
      If mocked test passes, real form may render empty.
      MITIGATION: companion integration test with real React Query provider, OR record manual-verify step.
    </risk>
  </mock-risks>

  <siblings>
    <sibling path="apps/ui/src/pages/PaymentPage.tsx">
      Handles useProfile() async with `if (!profile) return &lt;Skeleton /&gt;` guard.
    </sibling>
    <sibling path="apps/ui/src/pages/SettingsPage.tsx">
      Uses defaultValues = {} then resets form via useEffect when profile loads.
    </sibling>
  </siblings>
</discovery>
```

## Scan (residual — what discovery didn't already cover)

Use `project.md` as baseline (tech stack, test framework, package structure, conventions). For monorepo cross-package work, note any shared types / API contracts between affected packages discovery didn't surface. Do not re-enumerate what Deepak already documented.

## Spec File Placement Policy

```xml
<spec-placement-policy>
  <layout style="openspec" spec-path="openspec/specs/{slug}/spec.md" changes="openspec/changes/{change-slug}/" extras="proposal.md, design.md, tasks.md (optional)" />
  <layout style="folder-md" spec-path="{storage_root}/{NNN}{sep}{slug}/spec.md" extras="scoped to folder" />
  <layout style="flat-md" spec-path="{storage_root}/{NNN}{sep}{slug}.md" extras="single file — no folder, no siblings" />

  <numbering>
    <rule>NNN zero-padded to match existing files (usually 3 digits; widen only if existing files use 4+).</rule>
    <rule>Scan storage root for highest existing NNN, increment.</rule>
    <rule when="existing files lack numeric prefix (e.g., auth.md, payments.md)">Skip NNN entirely. Use pure slug.</rule>
  </numbering>
</spec-placement-policy>
```

## Spec Write (OpenSpec style)

Write spec to the path determined by `spec_style` in `specconfig.json`:

- `## Purpose` — what changes, anchored to real modules (cite paths).
- (monorepo only) `## Packages Affected` — list with per-package rationale.
- `## Requirements` — each `### Requirement:` block contains SHALL or MUST, cites actual repo paths.
- `#### Scenario:` blocks in GIVEN/WHEN/THEN format, each executable as a test.
- For modifications: use `## ADDED Requirements`, `## MODIFIED Requirements`, `## REMOVED Requirements` delta sections.

Update task manifest `<artifacts>/<spec>` with the resolved spec path.

## Style Inference Policy

```xml
<style-inference-policy>
  <rule>Detect and apply from the repo and project.md. Never ask as a checklist.</rule>

  <dimension name="error-handling" source="existing services" match="exceptions | Result | error-codes" />
  <dimension name="validation-boundary" source="existing controllers/services/schemas" match="whichever pattern dominates" />
  <dimension name="async-style" source="existing code" match="async-await | callbacks | generators" />
  <dimension name="logging" source="sibling files" match="whichever logger is already imported" />
  <dimension name="naming" source="sibling files" match="existing casing + prefix conventions (e.g., use* hooks, is* booleans)" />
  <dimension name="file-layout" source="surrounding code" match="co-located vs separate — whatever exists" />
  <dimension name="mocking-style">
    <case when-package-kind="web-frontend">invoke-and-validate (Luca's rule)</case>
    <case when-package-kind="backend-api">spin-up-and-assert via testcontainers/docker-compose (Nina's rule)</case>
    <case when-package-kind="shared-lib">pure-function unit tests</case>
    <case when-package-kind="mobile-rn">component testing with platform mocks</case>
  </dimension>
  <dimension name="dependencies" source="package.json | requirements.txt | go.mod" rule="prefer existing; avoid adding new unless task requires" />

  <mock-risk-policy>
    <rule id="mr-01-flag-async-mocks">
      Any test mock that replaces an async data fetcher (React Query hook, useSWR, useEffect-based fetch, server context, promise) MUST be flagged at write-time. Sreyash records the mock + the real provider's async window (loading state, initial null/empty, debounce, retry).
    </rule>
    <rule id="mr-02-mitigation-required">
      For every flagged async mock, Sreyash MUST do ONE of:
      (a) Add a companion integration test that uses the real provider (React Query test wrapper, real context provider, fake server with realistic latency).
      (b) Record a manual-verify step in the unit's &lt;verification&gt; field describing exactly what to check in the dev environment (browser path, expected initial state, expected post-load state).
    </rule>
    <rule id="mr-03-not-green-without-mitigation">
      A unit with flagged async mocks is NOT considered green until either:
      - the companion integration test passes, OR
      - the manual-verify step is recorded and the user has acknowledged it in the return report.
    </rule>
    <rule id="mr-04-ui-feeds-visible-state">
      For UI work where mocked data feeds visible state (form prefill, conditional render, input value), mr-02 is mandatory — never optional. This is the spec-011 lesson: mocked useProfile passed tests, real form rendered empty.
    </rule>
  </mock-risk-policy>

  <fallback>
    <rule>If a dimension can't be inferred, make the pragmatic choice and log it under task manifest &lt;artifacts&gt;/&lt;assumptions&gt;. Do not ask.</rule>
  </fallback>
</style-inference-policy>
```

## Red Phase

For each scenario in the spec, write a failing test in the target package's test framework.

- TINY tier: SKIP. Manual verify is the test.
- SMALL/MEDIUM/LARGE: write tests as below.
- For every test, evaluate against `<mock-risk-policy>`. If a mock replaces an async dependency, attach a companion integration test OR a `<verification>` block.
- Run tests. Confirm they fail for the expected reason.
- If a test fails for the wrong reason, fix the test before continuing.
- Independent tests on disjoint files MAY be written via parallel Edit/Write tool calls in a single message. Tests that touch the same file stay serial.

Update task manifest `<artifacts>/<tests>` with the red test paths.

## Plan Green — identify independent work units

After the spec + red tests are on disk, Sreyash groups the Requirements into work units:

```xml
<plan-green-policy>
  <rule>Each &lt;### Requirement&gt; block is a candidate unit.</rule>
  <rule>Units are INDEPENDENT if they touch disjoint file sets (test files produced + likely implementation files).</rule>
  <rule>Units that overlap on files COLLAPSE into one unit.</rule>
  <rule when="monorepo">Requirements scoped to different packages are almost always independent.</rule>
  <rule>Write the unit plan to the task manifest's &lt;work-units&gt; block before spawning anything.</rule>

  <tier-scaling>
    <tier name="TINY">No work-units. No builder dispatch. Sreyash codes inline in his own context. Skip green-phase entirely; verify manually.</tier>
    <tier name="SMALL">1 work-unit. Sreyash either codes inline OR spawns a single builder. No heartbeat polling — single short turn.</tier>
    <tier name="MEDIUM">2-4 parallel builders, normal heartbeat cadence.</tier>
    <tier name="LARGE">4-12 parallel builders, full heartbeat + kill protocol.</tier>
  </tier-scaling>
</plan-green-policy>
```

**Unit entry in manifest:**
```xml
<unit id="u1" requirement="r1" status="pending" builder="" builder-agent-id="" spawned-at="" soft-deadline="" hard-deadline="" last-heartbeat="">
  <files>
    <file>apps/ui/src/lib/api.ts</file>
  </files>
  <tests>
    <test>apps/ui/src/lib/api.test.ts</test>
  </tests>
  <progress>
    <tests-green>0</tests-green>
    <tests-red>3</tests-red>
    <files-written></files-written>
    <note></note>
  </progress>
  <events>
    <!-- Audit log. Sreyash appends kill/respawn/extend actions. -->
  </events>
</unit>
```

## Handoff

With work units planned in the manifest, proceed to `step-sreyash-3-process.md`.
