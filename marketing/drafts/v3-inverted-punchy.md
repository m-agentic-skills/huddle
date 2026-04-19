# Answers Got Cheap. Questions Got Valuable.

A year ago, if you wanted a working auth flow, a dashboard, and a Stripe integration, you wrote them. Today you ask for them and press enter. The code arrives in minutes.

This has not made shipping software easier. It has made *starting* easier.

## The 90/90 rule didn't go away

Tom Cargill at Bell Labs said it in 1985, and it's still true:

> "The first 90% of the code accounts for the first 90% of the development time. The remaining 10% accounts for the other 90%."

LLMs compressed the first 90%. The second 90% — edge cases, failure paths, real usage, the assumption nobody wrote down — is exactly as hard as it was.

## The old bottleneck is gone

*Can we build this?* is no longer the interesting question. Almost anything a small team wants to build, they can now stand up in a week.

## The new bottleneck is worse

*Did we think about this deeply enough?* is much harder to answer. And it's the question that decides whether the thing you shipped survives.

Answers can be generated. Questions cannot — at least, not the ones that matter. The questions that save systems are the uncomfortable ones:

- What happens when this fails in production?
- Who controls this input?
- What assumption are we making here?
- Is this solving the real problem, or a version of it?

They come from people who have watched systems break. A backend engineer, a security mind, a product manager, an architect — each sees a different face of the same system.

Most of those people aren't in the room when the code gets written. By the time they are, the code is in production.

## Where Huddle fits

Huddle puts 21 of them in the room — Shaama on backend failure modes, Senthil on blast radius, Prabagar on value metric, Suren on capacity math, and seventeen more. Repo-aware, opinionated, disagreeing with each other, before the system is locked in.

```bash
npx skills add muthuishere-agent-skills/huddle
```

You see what you'd otherwise discover in production.
