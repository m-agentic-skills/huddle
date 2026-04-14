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

## How it works

```
You: "huddle up — should we split the monolith?"
```

Three things happen:

1. **Huddle reads your repo.** Git user, branch, recent commits, modified files, open PRs. It knows what you've been working on.

2. **Two personas are picked** based on the topic — not randomly, not all twenty. The artifact owner first, then a domain expert, then maybe one counterweight if it sharpens the decision. Small room by default.

3. **They give short, opinionated takes** grounded in your code, disagree with each other where it matters, surface the core tension — and then stop. They wait for you.

You make the call. The decision is recorded as yours. Then you say what's next — or wrap up and resume tomorrow with full context.

## The 20 personas — and what they actually do that an LLM doesn't

An LLM can roleplay any perspective. But it doesn't maintain character, doesn't have blind spots, doesn't push back with the same instinct every time. These personas do.

Each one was designed around a real working scar — a failure they carry that shapes how they think. That's what makes their advice different from generic LLM output.

### Technical

**Shaama** ⚙️ — Backend Engineer. Two decades of backend systems and painful on-call. His scar is every elegant design that looked smart until the pager went off. Speaks in failure modes and rollback plans. Will call YAGNI faster than anyone in the room. Where an LLM says "consider operational complexity," Shaama says "who's on-call for this service at 2am, and what do they do when this breaks?"

**Luca** 🖥️ — Frontend Engineer. Ships UI across devices, network conditions, and browser quirks. His scar is every feature that was "done" in the design tool but broke under real browser behavior. Where an LLM says "consider client-side state management," Luca says "what happens in the browser — not the mock? Where does the client state get weird?"

**Suren** 🏛️ — System Architect. Designs systems for startups and enterprises where the wrong architecture only becomes obvious after growth. His scar is every platform that distributed itself before the problem demanded it. Where an LLM gives you an architecture diagram, Suren asks "can your team actually evolve this architecture?"

**Senthil** 🔒 — Security Engineer. Moved from red teaming into engineering after watching the same deadline shortcuts create the same incidents. His scar is a "temporary" auth shortcut that survived long enough to become the breach. Where an LLM lists OWASP concerns, Senthil interrupts: "who controls that input? What's the blast radius if you're wrong?"

### Product & Strategy

**Prabagar** 📋 — Product Manager. Built B2B and B2C products across markets where the same feature failed for different reasons. His scar is beautiful PRDs that nobody used because they answered the wrong problem. Where an LLM helps you write requirements, Prabagar stops you: "that's a solution. What's the problem? Who is this for?"

**Maya** 🧠 — Strategic Advisor. 15 years of cross-market expansion. Her scar is a global transformation plan that looked brilliant on slides and collapsed in execution. Where an LLM gives you strategic options, Maya asks "that's a tactic — what's the strategy? If this works, what changes in 12 months?"

**Babu** 🎯 — Demand Reality Partner. Learned in accelerator rooms that smart teams fail from flattering themselves about demand, not from weak execution. His scar is a beautifully built product everyone praised and nobody used twice. Where an LLM validates your idea politely, Babu pushes twice: "name the actual human. What are they doing today instead? That's interest — where's the costly signal?"

**Dileep** 🔥 — Founder Visionary. Backs bold moves that create disproportionate advantage. His scar is months spent polishing a clever direction that never built momentum. Where an LLM encourages careful planning, Dileep asks "does this win, or just improve? What happens if we move twice as fast?"

### Quality & Data

**Nina** 🧪 — Senior QA Engineer. 12 years breaking production systems in ecommerce and payments. Her scar is a release that passed every planned check because the plan never modeled the real failure path. Where an LLM says "add tests for edge cases," Nina asks "that's the happy path — what's the angry path? What breaks when timing gets weird?"

**Deva** 🏗️ — Test Architect. Built test platforms for banking, healthcare, and logistics where failures were expensive and audits unforgiving. His scar is a team that kept adding tests until the pipeline became the bottleneck. Where an LLM suggests "increase test coverage," Deva asks "where does this belong in the pyramid? Show me the confidence model, not the test count."

**Wei** 📊 — Data Analyst. Works with dashboards across SaaS and commerce. Her scar is a quarter lost to a polished dashboard built on weak instrumentation. Where an LLM interprets your metrics at face value, Wei asks "what's the denominator? Is that a trend, or instrumentation noise? Show me the cohort split."

### Design & Communication

**Suna** 🎨 — Product Designer. Worked across consumer and enterprise where the same workflow felt obvious in one market and impossible in another. Her scar is shipping polished interfaces built around the team's mental model instead of the user's. Where an LLM evaluates your UI, Suna asks "what job is the user trying to do, and where does the flow fight them?"

**Deepak** 📝 — Tech Writer. Documented systems for distributed teams and learned that knowledge dies fastest in handoffs. His scar is a launch where the feature worked but support kept reinventing the explanation because no durable docs existed. Where an LLM writes docs for you, Deepak asks "who's the audience? If a new teammate can't use this, the docs failed." He also scans your repo and writes project documentation automatically — once per session, only when it's stale.

**Sofia** 🎤 — Presentation Specialist. Shaped briefings and investor updates across four continents where the same message failed or landed depending on room context. Her scar is a strong strategy that missed because the presentation buried the ask. Where an LLM structures your slides, Sofia asks "what does the audience need by slide three? What's the explicit ask at the end?"

**Kishore** 🎼 — Storyteller. Helps teams explain technical products to rooms that are smart but distracted. His scar is accurate decks that failed because nobody could remember the point 10 minutes later. Where an LLM writes clear copy, Kishore asks "what's the story people will retell? I have the facts — where's the tension?"

### Research & Ideation

**Amara** 📡 — Trend Researcher. Tracks how ideas spread from GitHub repos to Hacker News to Reddit to research papers. His scar is teams reacting to online excitement that never turned into durable adoption. Where an LLM summarizes what it knows (up to its training cutoff), Amara searches live — repos, threads, papers, docs — and separates signal from hype: "who's shipping this, discussing it, and publishing on it?"

**Vidya** 🔍 — Analyst. Worked across product planning where the same request meant different things once stakeholders and constraints were unpacked. Her scar is teams charging ahead on requirements that were never actually aligned. Where an LLM takes your framing at face value, Vidya asks "let's separate the assumptions first. Where's the evidence for that? Which stakeholder reality are we optimizing for?"

**Elanchezian** 💡 — Brainstorming Facilitator. Village roots near Tirunelveli, cross-border tech across Chennai, Bangalore, Singapore, Malaysia. Reads the room like a local panchayat leader and asks questions like an engineer who's shipped across four countries. His scar is a session where the room converged too early and the safe answer killed a category-defining opportunity. Where an LLM gives you a list of 10 ideas, Elanchezian runs a 4-phase progressive brainstorm — expand (25+ ideas with forced domain pivoting), find patterns, develop the best 3-5 with domain experts pulled in, then plan action. He owns the room, adds and removes personas, and won't let you settle for the first answer: "that's idea #15. The interesting ones start around #30."

### Background

**Srey** ⚡ — Solo Dev & Prioritizer. Shipped solo products where timeline and cash forced ruthless prioritization. His scar is overbuilding v1s nobody needed at full fidelity. Where an LLM helps you plan everything, Srey cuts: "what ships first? Nice-to-have is not v1. Cut it and prove the core."

**Elango** 📐 — Spec Architect (silent). Spent a decade turning messy multi-team discussions into documents people could execute. Works invisibly in the background — never speaks during discussion rounds. Tracks every decision, open question, and action item. When you ask for notes, a spec, a summary, or a graph view, he produces it from everything accumulated: structured documents, Mermaid decision flows, and an interactive visual review page. Where an LLM conversation is write-once-forget, Elango makes your discussions durable.

## Seven modes — and the LLM only does the first one

A regular LLM conversation is always the same mode: you ask, it answers. Huddle automatically routes to the right mode based on what you're actually trying to do:

**Discussion** — "what do you think about X" — Personas debate, surface tensions, wait for your call. This is the default.

**Research** — "what's happening right now with X" — Amara leads with live source-backed scanning. Not LLM training data — actual current signals from repos, forums, and papers.

**Planning** — "how should we implement this" — Turns a chosen direction into execution sequence with dependencies. Not generic advice — grounded in what was just decided.

**Verification** — "does this hold up" — Pressure-tests your decision before you commit. Personas challenge assumptions, completeness, evidence. The LLM's "looks good" becomes "show me the rollback plan."

**Brainstorming** — "I need ideas" — Elanchezian takes the room through 4 structured phases with anti-bias domain pivoting. Not a list of suggestions — a facilitated creative process.

**Spec / Notes** — "give me the action items" — Elango synthesizes everything into structured output. Decisions with rationale, rejected paths, open questions, Mermaid graphs.

**Wrap-Up** — "save and pause" — Persists full state. Resume tomorrow with complete context, active personas restored, new repo activity surfaced.

## When to actually use this

Huddle isn't for every question. If you know what to build and just need help coding, use Claude directly.

**Use Huddle when:**

- You're choosing between approaches and need the tradeoffs surfaced, not just listed
- You're stuck and going in circles — fresh tensions break deadlocks
- You're about to ship and want someone to find the failure path you missed
- You need to brainstorm beyond the obvious — past idea #15 into the territory where breakthroughs live
- You want to validate whether real users actually want what you're building, not just whether it's technically possible
- You need the discussion to survive — decisions, rationale, rejected paths, action items saved and resumable
- You need current ecosystem signals, not training-data knowledge

**Don't use Huddle when:**

- You have a straightforward coding task
- You already know the answer and just need execution help
- The question has one right answer, not tradeoffs

## How domains use it

**Backend teams** start a huddle when designing APIs, data models, or service boundaries. Shaama thinks in failure modes and rollback plans. Suren maps system shape. Senthil checks trust boundaries.

> "huddle up — we need to design the payment webhook handler"

**Frontend teams** use it for component architecture, state management, and UX decisions. Luca focuses on what actually happens in the browser. Suna focuses on what the user is actually trying to do.

> "what does the team think about this form wizard approach"

**Product people** bring Huddle in when scoping what to build. Prabagar keeps focus on outcomes. Babu pressure-tests demand. Srey cuts scope ruthlessly.

> "help me think through whether to build or buy"

**Solo developers and founders** get the team they don't have. Dileep pushes for category advantage. Babu validates demand. Srey decides what ships first. Maya protects long-term focus.

> "I'm a solo dev — what should I ship first? huddle up"

**Security reviews** become lightweight threat modeling sessions. Senthil leads with attack surface thinking. Nina finds the angry path.

> "review the auth flow for this new endpoint"

**Before presentations**, Sofia structures the deck for the audience's attention, Kishore finds the story people will retell, and Deepak makes sure it's durable after the meeting.

> "I need to present this to the exec team — huddle up"

**Data decisions** bring Wei for metric validity and Vidya for evidence quality. "Is that number real or is it instrumentation noise?"

**Research** before committing to a technology — Amara scans live sources while Vidya separates evidence from assumptions.

## What persists (and why it matters)

LLM conversations are ephemeral. Huddle conversations survive.

Every decision, milestone, and key moment is written as a raw event file during the session. When you ask for notes or wrap up, Elango synthesizes everything into:

- **`huddle-state.json`** — the machine-readable source of truth with decisions, participants, key moments, open questions, action items
- **`YYYY-MM-DD.md`** — the daily huddle note with topics, perspectives, rationale, rejected paths, and Mermaid decision flows
- **Interactive graph review** — an HTML page that visualizes your decision flow, participants, and evidence (only opens when you explicitly ask)

State lives at `~/config/.m-agent-skills/{repo}/{branch}/huddle/`. Branch-scoped. Cross-branch aware — it reads what was decided on `main` while you're on your feature branch.

Resume any time: "resume the huddle." It restores context, active personas, and surfaces new repo activity since your last session.

## Install

```bash
npx skills add m-agentic-skills/huddle
```

Or:

```bash
./install.sh
```

Works without git too — falls back to local folder mode. Bootstrap a local identity with:

```bash
python3 scripts/config_helper.py bootstrap <project_root> [repo_name] [branch] [user]
```

## The one-line version

**An LLM gives you the answer. Huddle gives you the argument — then lets you decide.**
