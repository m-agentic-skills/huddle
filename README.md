# Huddle

```bash
npx skills add muthuishere-agent-skills/huddle
```

**An LLM gives you the answer. Huddle gives you the argument — then lets you decide, and hands the build off to Sreyash.**

## What it is

A single LLM gives you one balanced answer. Huddle gives you 2-3 opinionated perspectives that disagree with each other, grounded in your repo, and then stops and waits for your call.

Ask the same question two ways:

> **To Claude directly:** "Should I use Redis or Postgres?" → a balanced pros-and-cons list.
>
> **In Huddle:** Shaama (backend, 20 years of on-call scars) says *"Redis adds operational burden you'll pay for at 2am. What's the failure mode when this cache goes cold?"* Suren (architect) counters *"Postgres won't hold at this access pattern — but can your team actually evolve a Redis-backed architecture?"*

That's not an answer. That's a tension. Tensions are where decisions get made.

## Who's in the room

21 personas — each carries a scar/win identity and named influences (Rumelt, Porter, Hickey, Tufte, Duarte, MEDDIC, DORA, Fowler, House, and more). Some talk in the room, some take sub-tasks, some work silently.

| | Name | Role | What they do that an LLM doesn't |
|---|---|---|---|
| 🧠 | Maya | Strategy | Diagnosis before plan; names the non-goals |
| 🖥️ | Luca | Frontend / Mobile / Games | Device reality — not the mock |
| ⚙️ | Shaama | Backend | Failure modes, rollback, anti-ceremony |
| 🎨 | Suna | Design | User jobs, not team mental models |
| 📋 | Prabagar | PM | Value metric, measured vs borrowed pricing |
| 🔒 | Senthil | Security | Blast radius, trust boundaries |
| 🎯 | Babu | Demand Reality | Names the actual human; kills borrowed benchmarks |
| 🔥 | Dileep | Founder Visionary | Distribution-first, SEO, wartime instincts |
| 🧪 | Nina | Tester (QA + E2E) | Angry-path scenarios; docker-compose/testcontainers |
| 🏛️ | Suren | Architect | Capacity math, DORA, Team Topologies, boring tech |
| 🔍 | Vidya | Pre-Sales | MEDDPICC, economic buyer, paper process |
| 📝 | Deepak | Tech Writer | Docs that survive handoffs; auto-scans the repo |
| 📊 | Wei | Data Analyst | Dashboard design; denominator discipline |
| 🎼 | Kishore | Storyteller & Presentation | Kills bullet points; narrative + deck craft |
| 📡 | Amara | Trend Researcher | Live ecosystem scanning; signal vs hype |
| 🔬 | Vel | Infrastructure Diagnostician | Differential diagnosis with parallel scouts; names root cause and layer |
| 💡 | Elanchezian | Brainstorming | 4-phase progressive brainstorm, room control |
| 📐 | Elango | Spec Architect | Silent background state; synthesizes notes/specs/graphs on demand |
| ⚡ | Sreyash | Builder | Spec + TDD + parallel build crew; "Sreyash, build this" |
| 🛠️ | Hari | Builder (sibling) | Picks up when Sreyash is busy |
| 🧰 | Harshvardhan | Builder (sibling) | Picks up when Sreyash and Hari are both busy |

Hand a task: *"Sreyash, build the auth flow."* He writes an OpenSpec-style spec, runs TDD red→green→refactor, spawns up to 12 named parallel workers, and returns with artifacts. Three parallel tasks max — overflow delegates transparently.

## Eight modes

Discussion · Research · Planning · Verification · **Build-Readiness** · Brainstorming · Spec Review · Wrap-Up. Huddle routes based on what you're asking for.

## What persists

Nothing lives in your repo unless you put it there. Huddle stores decisions, open questions, action items, and a conversation graph at `~/.config/muthuishere-agent-skills/{repo}/{branch}/huddle/`. Resume any time: *"resume the huddle."*

On demand, Elango synthesizes an interactive graph view — 💡 issues, ✅ decisions, ⚔️ challenges, ❓ open questions, 📚 evidence — with edges linking them, plus a Timeline tab and the full Spec.

## When to use Huddle

- Choosing between approaches and need tradeoffs surfaced, not just listed.
- Stuck in a circle — fresh tensions break deadlocks.
- About to ship and want someone to find the failure path you missed.
- Need to brainstorm past idea #15 into where breakthroughs live.
- Want the discussion to survive — decisions, rationale, rejected paths, resumable.
- Something is broken in prod and you need root cause, not guesses.
- Want to hand the build off to Sreyash while you keep moving.

Use Claude directly for straightforward coding; use Huddle when the shape of the question matters more than the answer.

## Install

```bash
npx skills add muthuishere-agent-skills/huddle
```

Works without git too — falls back to local-folder mode.

## More

Full walkthrough in [`usage.md`](./usage.md). Technical components: see [`SKILL.md`](./SKILL.md), [`references/`](./references), [`scripts/`](./scripts), [`docs/`](./docs).

## Inspired by

[BMad Method](https://bmadcode.com/) · [OpenSpec](https://openspec.org/).
