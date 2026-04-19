# The 80% Problem — And What LLMs Actually Changed

The demo was on Thursday. On Monday, the team had nothing. By Wednesday night, Claude had written most of a working app — auth, an API, a dashboard, even a settings page. Thursday's demo went great.

Then they spent six weeks shipping it.

Not building it. *Shipping* it. Password reset emails sent to the wrong tenant. A race condition in session refresh. An admin role that quietly inherited from a deleted parent. A Stripe webhook handler that worked for 99% of events and silently dropped the other 1%.

None of it showed up in the demo. All of it showed up in production.

## The oldest rule in software

In 1985, Tom Cargill of Bell Labs described the pattern like this:

> "The first 90% of the code accounts for the first 90% of the development time. The remaining 10% accounts for the other 90%."

Forty years on, it's still true. Software gets built in two phases that feel nothing alike. Phase one is fast and visible. Phase two is slow, edge-cased, and invisible — and it's where systems either harden or quietly rot.

## What LLMs actually changed

Phase one has collapsed. What took two weeks takes two days. What took two days takes two hours.

Phase two is untouched.

Because phase two was never about writing code. It's about uncovering the thing nobody asked about. A webhook handler is fifty lines. Knowing that Stripe retries with the same idempotency key for 24 hours but stops after — that's the part no LLM hands you unprompted.

The new bottleneck isn't *can we build this?* It's *did we think about this deeply enough?*

## Answers are cheap. Questions are the asset.

In the old world, you had to build something to find out what was missing. Production taught you. Incidents taught you. Users taught you. The tuition was high.

In the new world, the code exists in an afternoon. But the *questions* — the ones that would have surfaced the webhook edge case, the tenant boundary, the silent role inheritance — those still only come from people who've watched systems fail.

And most of them aren't in the room when the code gets written.

## What a pre-mortem actually sounds like

Imagine the team from the top of this piece had spent thirty minutes on Wednesday in a room with four people:

> **Shaama** (backend, 20 years of on-call scars): *What's the failure mode when Stripe retries after 24 hours with a different idempotency key?*
>
> **Senthil** (security): *If I can get my email into another tenant's user table, what's the blast radius?*
>
> **Prabagar** (PM): *What's the support cost of a wrong-tenant email — one ticket, ten, a hundred?*
>
> **Vel** (infrastructure diagnostician): *What's the alarm on silent webhook failures? Is it on the logs, the metric, or nothing?*

Four questions. Thirty minutes. Probably five of the six weeks saved.

## Where Huddle fits

Huddle runs repo-aware, multi-persona engineering discussions. 21 personas — a backend engineer with scars, a security mind, a PM who knows MEDDPICC, a strategist, a builder who ships — in the room with you, before the code is locked in. You see what you'd otherwise discover in production.

```bash
npx skills add muthuishere-agent-skills/huddle
```

Better systems aren't built by faster answers. They're built by better questions, asked at the right time.
