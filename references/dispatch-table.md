# Dispatch Table — parallel subagent progress convention

Shared by **Vel** (scouts) and **Sreyash** (builders). When either spawns parallel subagents via the `Agent` tool, a status table is rendered in-line so the user sees progress without asking.

## Mechanics

1. **Spawn with `run_in_background: true`.** Backgrounded agents send a completion notification automatically.
2. **Spawn all parallel subagents in a single message** (multiple `Agent` tool calls in one turn). Serial dispatch defeats parallelism.
3. **Render the table immediately after dispatch.** First in the response, above any prose.
4. **Re-render when it's relevant:** on completion notification, when synthesizing, when the user asks. Not in every unrelated response — the user may have moved on; respect that.
5. **Non-blocking.** If the user switches topics mid-flight, respond to the new topic; subagents keep running; the table comes back when there's news.

## Status icons

| Icon | Meaning |
|------|---------|
| `🏃` | running in background |
| `✅` | returned with observation / artifact |
| `❌` | failed, timed out, or errored |
| `⏹️` | canceled mid-flight |
| `⚠` | blocked (builders only) |

## Vel's scouts

```
### Vel's scouts — differential in flight

| id | task | status | elapsed | observation |
|----|------|--------|---------|-------------|
| vel-alpha | grep kamal logs for smtp errors, last 24h | ✅ | 8s  | `dial tcp :465: i/o timeout` from Apr 15 14:02 UTC |
| vel-beta  | SSH 78.46.65.254 → TCP probe 465 + 587     | 🏃 | 42s | — |
| vel-gamma | diff .env.dev vs .env.production SES block | ✅ | 3s  | identical keys, no drift |
```

- **id** — `vel-alpha`, `vel-beta`, ... (Greek, lowercase).
- **task** — one short line, what Vel asked.
- **elapsed** — rough time since dispatch; update on re-render.
- **observation** — one-line summary. `—` while running. Full detail goes in Vel's synthesis paragraph below the table.

## Sreyash's builders

```
### Sreyash's builders — in flight

| id | unit | status | progress | artifacts |
|----|------|--------|----------|-----------|
| sreyash-alpha | u1 — frontend types | ✅ | 3/3 | `apps/ui/src/lib/api.ts` (+12 lines) |
| sreyash-beta  | u2 — api validation | 🏃 | 2/4 | `apps/api/src/modules/profile/profile.service.ts` |
| sreyash-gamma | u3 — rename sweep   | 🏃 | 4/5 | 4 files touched |
```

- **id** — `{orchestrator}-{greek}`. Sibling pools: `hari-alpha`, `harshvardhan-alpha`. Past 12 letters, continue `alpha-2`, `beta-2` — never fall back to personality names.
- **unit** — work unit id + one-line scope.
- **progress** — `N/M` tests green, or `N/M` files touched.
- **artifacts** — files written, paths, counts. `—` while running.

## Example turn (Vel)

```
Differential for "prod emails broken":
  H1 credentials wrong       → vel-alpha (logs) + vel-gamma (env diff)
  H2 egress port blocked     → vel-beta (SSH probe)

### Vel's scouts — differential in flight

| id | task | status | elapsed | observation |
|----|------|--------|---------|-------------|
| vel-alpha | grep kamal logs for smtp errors, last 24h | 🏃 | 0s | — |
| vel-beta  | SSH 78.46.65.254 → TCP probe 465 + 587     | 🏃 | 0s | — |
| vel-gamma | diff .env.dev vs .env.production SES block | 🏃 | 0s | — |
```

Next turn, after alpha and gamma return:

```
### Vel's scouts — differential in flight

| id | task | status | elapsed | observation |
|----|------|--------|---------|-------------|
| vel-alpha | grep kamal logs for smtp errors, last 24h | ✅ | 8s  | `dial tcp :465: i/o timeout` from Apr 15 14:02 UTC |
| vel-beta  | SSH 78.46.65.254 → TCP probe 465 + 587     | 🏃 | 42s | — |
| vel-gamma | diff .env.dev vs .env.production SES block | ✅ | 3s  | identical keys, no drift |

H1 dead (creds identical across dev-where-it-works and prod-where-it-doesn't).
Waiting on vel-beta to confirm H2.
```
