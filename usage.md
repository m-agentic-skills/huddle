# Huddle — Where the LLM Stops and Your Team Starts

You already have Claude. You can ask it anything — "review my auth flow," "what should I build first," "help me think through this migration." And it gives you a solid, balanced answer.

So why would you need Huddle?

Because a single coherent answer is exactly the problem.

## What an LLM gives you vs. what Huddle gives you

When you ask an LLM "should I use Redis or Postgres here?", you get a well-structured pros-and-cons list. Balanced. Reasonable. Safe.

When you ask Huddle the same question, Shaama — a backend engineer who spent two decades doing painful on-call rotations — says "Redis adds operational burden you'll pay for at 2am. What's the failure mode when this cache goes cold?" And Suren — an architect whose scar is watching teams distribute systems before the problem demanded it — says "The access pattern will outgrow Postgres. But can your team actually evolve a Redis-backed architecture?"

That's not a balanced answer. That's a tension. And tensions are where real decisions get made.

**An LLM gives you answers. Huddle gives you the argument you need to hear before you decide.**

Here's what that looks like in practice:

| You ask Claude directly | You ask the same thing in Huddle |
|---|---|
| One coherent, balanced response | 2-3 opinionated perspectives that disagree with each other |
| Advice disappears when you close the tab | Decisions, open questions, action items saved to disk — resume tomorrow |
| Generic best practices | Grounded in your repo — your branch, your recent commits, your open PRs |
| The LLM decides the framing | You decide. Personas present, then stop and wait for your call |
| "Here are the security considerations" as a bullet point | Senthil asks "who controls that input?" and won't move on until you answer |
| One conversation, then gone | Elango silently tracks every decision in the background and produces specs, notes, and decision graphs on demand |
| "Here's how to implement it" | You hand the build to Sreyash — he spawns a background crew, writes spec + tests + code, reports back |
| "Check your configuration" when something breaks | Vel runs differential diagnosis with parallel scouts, names root cause and layer, hands fix to Sreyash with a failing repro test |

## How it works

```
You: "huddle up — should we split the monolith?"
```

Three things happen:

1. **Huddle reads your repo.** Git user, branch, recent commits, modified files, open PRs. It knows what you've been working on.

2. **Two personas are picked** based on the topic — not randomly, not all twenty-two. The artifact owner first, then a domain expert, then maybe one counterweight if it sharpens the decision. Small room by default.

3. **They give short, opinionated takes** grounded in your code, disagree with each other where it matters, surface the core tension — and then stop. They wait for you.

You make the call. The decision is recorded as yours. Then you say what's next — or wrap up and resume tomorrow with full context.

## The 22 personas — and what they actually do that an LLM doesn't

An LLM can roleplay any perspective. But it doesn't maintain character, doesn't have blind spots, doesn't push back with the same instinct every time. These personas do.

Each one was designed around a real working scar — a failure they carry that shapes how they think. Their voices are deepened with named thinker references (Rumelt, Porter, Hickey, Tufte, Duarte, MEDDIC, DORA, Fowler, and more) so their challenges land with force, not as generic LLM output.

Some personas talk in the room. Some take over for a sub-task (brainstorming, project docs, diagnostics, building). Some work silently in the background. They're all part of the same team.

### Technical

**Shaama** ⚙️ — Backend Engineer. Two decades of backend systems and painful on-call. Functional-pragmatic, performance-aware, allergic to SOLID ceremony. Classes and DI are fine; acronym frameworks aren't. His scar is every elegant design that looked smart until the pager went off. Where an LLM says "consider operational complexity," Shaama says "who's on-call for this service at 2am, and what do they do when this breaks?"

**Luca** 🖥️ — Frontend / Mobile / Games. Ships UI across browsers, phones, tablets, kiosks, and game screens. His scar is every feature that was "done" in the design tool but broke under real browser behavior — or shipped to mobile with web assumptions about memory, lifecycle, and network. Where an LLM says "consider client-side state management," Luca says "what happens on the actual device — not the mock? Touch target minimums? Thumb zones? And for the love of testing, push logic into pure functions so we don't need a DOM to validate it."

**Suren** 🏛️ — System Architect. His scar is every platform that distributed itself before the problem demanded it. Speaks in DORA metrics, Team Topologies, bounded contexts, and "choose boring technology." Where an LLM gives you an architecture diagram, Suren asks "what's the actual load? Can this team evolve this architecture?"

**Senthil** 🔒 — Security Engineer. Moved from red teaming into engineering after watching deadline shortcuts create the same incidents. His scar is a "temporary" auth shortcut that survived long enough to become the breach. Where an LLM lists OWASP concerns, Senthil interrupts: "who controls that input? What's the blast radius if you're wrong?"

### Product & Strategy

**Prabagar** 📋 — Product Manager. His scar is beautiful PRDs that nobody used because they answered the wrong problem. Owns pricing and conversion economics — value metric selection, freemium/expansion revenue, willingness-to-pay research. Where an LLM helps you write requirements, Prabagar stops you: "that's a solution. What's the problem? Is that 3% pay-rate measured in our funnel, or borrowed from a SaaS benchmark post?"

**Maya** 🧠 — Strategic Advisor. Rumelt kernel (diagnosis → guiding policy → coherent action), Porter non-goals, retention-curve PMF. Her scar is a global transformation plan that looked brilliant on slides and collapsed in execution. Where an LLM gives you strategic options, Maya asks "what's the diagnosis before we pick a policy? What are we explicitly NOT doing this year?"

**Babu** 🎯 — Demand Reality Partner. Learned in accelerator rooms that smart teams fail from flattering themselves about demand. Benchmark-vs-evidence discipline — borrowed industry numbers get killed on sight. Where an LLM validates your idea politely, Babu pushes twice: "name the actual human. Measured, assumed, or borrowed — pick one for each metric."

**Dileep** 🔥 — Founder Visionary. Distribution-first, SEO as a product surface, wartime CEO instincts, growth-stall diagnosis. His scar is a product that shipped and priced beautifully but waited for users who never arrived. Where an LLM encourages careful planning, Dileep asks "if we ship this tomorrow, who finds us — and why would they care?"

### Quality & Data

**Nina** 🧪 — Tester (QA + E2E + Test Strategy). 12 years breaking production systems. Absorbed the test-architecture role too — owns test pyramid shape, contract tests, CI speed, flaky-test triage, pragmatic E2E via docker-compose or testcontainers. Her scar is a release that passed every planned check because the plan never modeled the real failure path. Where an LLM says "add tests for edge cases," Nina says "spin it up in docker-compose, invoke, assert. What's the angry path? Show me the rollback."

**Wei** 📊 — Data Analyst & Dashboard Designer. Tufte, Stephen Few, Cole Nussbaumer. Her scar is a quarter lost to a polished dashboard built on weak instrumentation. Where an LLM interprets your metrics at face value, Wei asks "what question is this dashboard supposed to answer in one sentence? What's the denominator? Is that a trend, or instrumentation noise?"

### Design & Communication

**Suna** 🎨 — Product Designer. Her scar is shipping polished interfaces built around the team's mental model instead of the user's. Where an LLM evaluates your UI, Suna asks "what job is the user trying to do, and where does the flow fight them?"

**Deepak** 📝 — Tech Writer. His scar is a launch where the feature worked but support kept reinventing the explanation because no durable docs existed. Also writes project documentation automatically — once per session, only when stale. Where an LLM writes docs for you, Deepak asks "who's the audience? If a new teammate can't use this, the docs failed."

**Kishore** 🎼 — Storyteller & Presentation Specialist. Duarte, Garr Reynolds, Tufte for slides. His scars: accurate decks that failed because nobody could remember the point 10 minutes later, and strong strategies that missed because the presentation buried the ask in a wall of bullets. Where an LLM writes clear copy and structures slides, Kishore asks "what's the story people will retell? What does the audience need by slide three? What's the explicit ask at the end?" He kills bullet points on sight.

### Infrastructure & Diagnostics

**Vel** 🔬 — Infrastructure Diagnostician. Part Gregory House, part Brendan Gregg. Always in the room, usually quiet — activates when something is broken, down, flaky, or "works locally but not in prod." His scar is a three-hour prober-building detour that a 30-second log tail would have ended. Carries the "everybody lies" reflex: trusts observed evidence, not reassurance. Won't accept "I already checked" without the command and the output. Where an LLM suggests "check your configuration," Vel runs a differential diagnosis — lists ranked hypotheses, dispatches parallel read-only scouts (vel-alpha, vel-beta, vel-gamma) to gather evidence simultaneously, eliminates hypotheses against evidence, and names the root cause with the layer (network / host / config / data / app / cert / clock). Every fix must include a failing test that reproduces the bug AND the instrumentation that would have caught it without him. Hands the actual fix to Sreyash's pool.

### Research & Analysis

**Amara** 📡 — Trend Researcher. Tracks how ideas spread from GitHub repos to Hacker News to Reddit to papers. Where an LLM summarizes what it knows (up to its training cutoff), Amara searches live — repos, threads, papers, docs — and separates signal from hype: "who's shipping this, discussing it, and publishing on it?"

**Vidya** 🔍 — Pre-Sales. MEDDPICC, JOLT, Challenger reframe. Her scar is teams charging ahead on requirements that were never actually aligned. Where an LLM takes your framing at face value, Vidya asks "who is the economic buyer? Is our champion strong, or are we single-threaded? What's the paper process?"

**Elanchezian** 💡 — Brainstorming Facilitator. Reads the room like a local panchayat leader and asks questions like an engineer who's shipped across four countries. His scar is a session where the room converged too early and the safe answer killed a category-defining opportunity. Where an LLM gives you a list of 10 ideas, Elanchezian runs a 4-phase progressive brainstorm — expand (25+ ideas with forced domain pivoting), find patterns, develop the best 3-5, then plan action: "that's idea #15. The interesting ones start around #30."

### State & Build

**Elango** 📐 — Spec Architect. Works invisibly during discussion — never speaks unless asked. Tracks every decision, open question, action item. When you ask for notes, a spec, a summary, or a graph view, he produces it from accumulated state: structured documents, decision graphs with issues/challenges/evidence/open-questions as first-class nodes, and an interactive visual review page. Where an LLM conversation is write-once-forget, Elango makes your discussions durable.

**Sreyash** ⚡ — Builder. When you hand him a task ("Sreyash, build the auth flow"), he detects your repo conventions silently, runs a short clarify round, then disappears to work. Inside, he writes an OpenSpec-style spec grounded in real repo paths, lands red tests, then spawns up to 12 named builders in parallel (harsh-frontend-types, mohan-api-validation, leo-rename-sweep, etc.) with adaptive heartbeats and kill/respawn protocols. Fowler-flavored: Rule of Three before abstraction, preparatory refactoring, characterization tests before legacy. Returns with a short report when done.

**Hari** 🛠️ and **Harshvardhan** 🧰 — Sreyash's siblings. Same capabilities, same flow. When you say "Sreyash, build X" and Sreyash is already in flight, the orchestrator delegates transparently:

> "⚡ Sreyash is busy on {auth-flow}; 🛠️ Hari is picking this one up."

Three parallel tasks maximum. You always address Sreyash; the overflow is handled for you.

## Eight modes — and the LLM only does the first one

A regular LLM conversation is always the same mode: you ask, it answers. Huddle automatically routes to the right mode based on what you're actually trying to do.

**Discussion** — "what do you think about X" — Personas debate, surface tensions, wait for your call. Default.

**Research** — "what's happening right now with X" — Amara leads with live source-backed scanning. Not LLM training data — actual current signals from repos, forums, and papers.

**Planning** — "how should we implement this" — Turns a chosen direction into execution sequence with dependencies.

**Verification** — "does this hold up" — Pressure-tests your decision before you commit. The LLM's "looks good" becomes "show me the rollback plan."

**Build-Readiness** — "are we ready to build" — Opt-in checkpoint before implementation. Suren + Shaama + Nina pressure-test architecture, backend, and test strategy. Offered once when you say "let's ship it."

**Brainstorming** — "I need ideas" — Elanchezian takes the room through 4 structured phases with anti-bias domain pivoting.

**Spec Review** — "give me the action items" / "write the spec" / "show me the graph" — Elango synthesizes accumulated state into structured output.

**Wrap-Up** — "save and pause" — Persists full state. Resume tomorrow with complete context, active personas restored, new repo activity surfaced.

## Hand a build to Sreyash

Huddle isn't just discussion. When you've made a decision and want to actually build it, say:

```
You: "Sreyash, build this"
```

Sreyash runs a four-phase flow:

1. **Init** — detects your repo's spec style (`openspec/` convention, flat `docs/specs/NNN-name.md`, or folder-per-spec), test framework, monorepo layout. Runs one short clarify round if anything genuinely needs your judgment.
2. **Spec** — writes an OpenSpec-style spec in your repo's existing convention. Purpose, SHALL/MUST Requirements, GIVEN/WHEN/THEN Scenarios. Real paths, not abstract names.
3. **Process** — lands red tests serially, then spawns up to 12 parallel green-phase builders with adaptive heartbeats, soft/hard deadlines, and a 5-case after-kill decision tree. If a unit stalls, he splits it, respawns with a different builder, or surfaces the blocker to you.
4. **Wrap** — runs full suite for cross-unit regressions, writes final manifest, returns a short report.

No branches, no commits — Sreyash writes files on your current branch; you review with `git status`. TDD is default; say "skip tests" to opt out.

Task manifest lives skill-private at `~/config/muthuishere-agent-skills/{repo}/sreyash/{NNN}-{slug}/task.xml` (or under `hari/` / `harshvardhan/` when siblings pick up). Resumable across sessions.

## When to actually use this

Huddle isn't for every question. If you know what to build and just need help coding, use Claude directly.

**Use Huddle when:**

- You're choosing between approaches and need the tradeoffs surfaced, not just listed
- You're stuck and going in circles — fresh tensions break deadlocks
- You're about to ship and want someone to find the failure path you missed
- You need to brainstorm beyond the obvious — past idea #15 into the territory where breakthroughs live
- You want to validate whether real users actually want what you're building
- You need the discussion to survive — decisions, rationale, rejected paths, action items saved and resumable
- You need current ecosystem signals, not training-data knowledge
- You've decided and want the build handed off to Sreyash while you keep moving

**Don't use Huddle when:**

- You have a straightforward coding task
- You already know the answer and just need execution help
- The question has one right answer, not tradeoffs

## How domains use it

**Backend teams** start a huddle when designing APIs, data models, or service boundaries. Shaama thinks in failure modes. Suren maps system shape. Senthil checks trust boundaries. Nina pressure-tests with spin-up E2E.

> "huddle up — we need to design the payment webhook handler"

**Frontend teams** use it for component architecture, state management, mobile lifecycle, and UX decisions. Luca focuses on what actually happens on the device (web, mobile, game). Suna focuses on what the user is trying to do.

> "what does the team think about this form wizard approach on mobile"

**Product people** bring Huddle in when scoping what to build. Prabagar keeps focus on outcomes and pricing value-metric. Babu pressure-tests demand. Sreyash then builds what you decided on.

> "help me think through whether to build or buy"

**Solo developers and founders** get the team they don't have. Dileep pushes for distribution and category advantage. Babu validates demand. Maya protects long-term focus. Sreyash (+ Hari + Harshvardhan) parallelizes the implementation.

> "I'm a solo dev — what should I ship first? huddle up"

**When something is broken** — production down, flaky deploys, "works locally but not in prod" — Vel activates automatically. Runs differential diagnosis with parallel scouts, names the root cause, hands the fix to Sreyash with a failing test attached.

> "prod emails stopped working after the deploy"

**Security reviews** become lightweight threat modeling. Senthil leads with attack surface thinking. Nina finds the angry path.

> "review the auth flow for this new endpoint"

**Before presentations**, Kishore structures the narrative and the deck — story, slides, delivery.

> "I need to present this to the exec team — huddle up"

**Data decisions** bring Wei for metric validity, dashboard design, and instrumentation quality.

**Research before technology commitment** — Amara scans live sources while Vidya separates evidence from assumptions.

## What persists (and why it matters)

LLM conversations are ephemeral. Huddle conversations survive.

Decisions and milestones are written as raw event files during the session — one file per event, no merges, no locks. Normal discussion rounds write nothing. When you ask for notes or wrap up, Elango synthesizes everything into:

- **`huddle-state.json`** — machine-readable source of truth, conforms to a documented XML schema. Decisions, issues, challenges, evidence, open questions, participants, key moments, action items.
- **`YYYY-MM-DD.md`** — daily huddle note with topics, perspectives, rationale, rejected paths.
- **Interactive graph review** — an HTML page that visualizes the conversation graph: 💡 issues, ✅ decisions, ⚔️ challenges, ❓ open questions, 📚 evidence, with edges linking them (informs, challenges, supports, needs-answer). Includes zoom controls, a Timeline tab with a narrative view, and a Spec tab with the full markdown note. Never auto-opens — only launches when you explicitly say "show me the graph."

State lives at `~/config/muthuishere-agent-skills/{repo}/{branch}/huddle/`. Branch-scoped. Cross-branch aware — it reads what was decided on `main` while you're on your feature branch. Background builder manifests live alongside, namespaced per sibling (`sreyash/`, `hari/`, `harshvardhan/`).

Resume any time: "resume the huddle." It restores context, active personas, and surfaces new repo activity since your last session.

## Install

```bash
npx skills add muthuishere-agent-skills/huddle
```

Or:

```bash
./install.sh
```

Works without git — falls back to local folder mode. Bootstrap a local identity with:

```bash
python3 scripts/config_helper.py bootstrap <project_root> [repo_name] [branch] [user]
```

## The one-line version

**An LLM gives you the answer. Huddle gives you the argument — then lets you decide, and hands the build off to Sreyash.**
