# Hacker News post

## Option A — Show HN

**Title:**

Show HN: Huddle – multi-persona Claude Code skill for pre-mortem discussions

**Body:**

Huddle is a Claude Code skill I built to solve a pattern I kept hitting: LLMs got me to 80% done fast, and then the last 20% — edge cases, hidden assumptions, real-world usage — ate months.

Cargill's 1985 observation ("the first 90% takes the first 90% of the time; the last 10% takes the other 90%") feels sharper now than it did a year ago, because the first 90% has collapsed and the second 90% hasn't.

The thesis: what saves systems is a short list of uncomfortable questions asked early, and those questions don't come from one voice. So Huddle puts 21 opinionated personas — a backend engineer focused on failure modes, a security lens focused on blast radius, a PM focused on value metrics, an architect focused on capacity math, and so on — in the room with you, grounded in your actual repo. They disagree. They stop and wait. You decide.

Stdlib Python and markdown skill files under the hood. No cloud, no lock-in. State lives under `~/config/muthuishere-agent-skills/`, never in your repo unless you put it there. Works without git too.

Install: `npx skills add muthuishere-agent-skills/huddle`

Repo: https://github.com/muthuishere-agent-skills/huddle

Happy to take critique — especially on where this is wrong, or where it overlaps with something that already exists.

---

## Option B — Article submission (link post)

**Title:**

The 80% problem — and what LLMs actually changed

**URL:** https://github.com/muthuishere-agent-skills/huddle/blob/main/marketing/the-80-percent-problem.md
*(or wherever the article is hosted)*

*No body — HN link posts don't take one. First comment from the author should disclose Huddle affiliation in one flat sentence.*

**Suggested first comment (author disclosure):**

Author here. Disclosure: the post ends by pitching Huddle, which I built. The thesis — that LLMs moved the bottleneck from "can we build this?" to "did we think about this deeply enough?" — stands without the pitch. Curious whether others are seeing the same shift, or whether this is overstated.
