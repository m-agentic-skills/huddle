# Elango Graph Contract

## Goal

Define how Elango captures raw huddle movement during discussion and how a later projection pass converts that raw structure into the human-readable graph view used by the review surface.

The contract should support:

- who shaped the room
- what stood out
- key moments in the discussion
- evidence and references
- the visible graph of nodes and edges

## Decision

Elango should stay lightweight during the huddle.

He should **not** write polished UI-ready semantics on every turn.

Instead:

- Elango writes `graph-raw.json`
- a projection pass turns `graph-raw.json` into a transient readable graph view
- the renderer consumes only that transient readable graph view

## Artifact Set

```text
<user-home>/config/muthuishere-agent-skills/<repo>/<branch>/huddle/
├── <YYYY-MM-DD>.md
├── graph-raw.json
```

Meaning:

- `<YYYY-MM-DD>.md`
  - readable spec / notes / summary
- `graph-raw.json`
  - append-oriented structural event log
- transient graph view
  - human-readable projection used by the UI

## Design Principles

### Raw First

`graph-raw.json` is the source of graph truth.

It should be:

- cheap to update every round
- append-oriented
- stable across renderer changes
- structural rather than presentational

### View Later

The readable graph view is a derived artifact.

It should be generated:

- when the user asks to inspect the graph
- when wrap-up is requested
- when a meaningful checkpoint is reached

It should optimize for:

- human readability
- visible conversation flow
- strong evidence grounding
- showing what the room got right
- showing what the room missed

### Renderer Simplicity

The renderer should:

- read the transient readable graph view
- display it
- avoid inventing business meaning

## What The User Should See

When a user opens the graph, they should quickly understand:

- what the room was trying to solve
- what decision or direction is currently strongest
- who materially shaped the discussion
- what stood out immediately
- which moments changed the room
- what evidence grounded the room
- how branches, objections, and decisions connect

## Readable Graph View

This is the final human-facing artifact at review time.

### Top-Level Shape

```json
{
  "session_id": "2026-04-05-main",
  "generated_at": "2026-04-05T12:10:00Z",
  "main_question": "How should huddle render conversation flow?",
  "decision": "Keep Elango raw-first, derive the readable graph view later.",
  "decision_why": "The room wanted readable discussion flow instead of a technical dashboard graph.",
  "what_stands_out": [],
  "people_involved": [],
  "key_moments": [],
  "evidence": [],
  "nodes": [],
  "edges": []
}
```

### `what_stands_out`

Purpose:

- fast orientation before reading the graph

Each item should include:

- `icon`
- `text`

Example:

```json
{
  "icon": "❓",
  "text": "Do we need a separate current-state artifact?"
}
```

### `people_involved`

Purpose:

- show who materially shaped the room

Each item should include:

- `id`
- `name`
- `icon`
- `meta`
- `influence`

Example:

```json
{
  "id": "suna",
  "name": "Suna",
  "icon": "🎨",
  "meta": "Design",
  "influence": "Pushed the room toward a graph that reads like a real conversation."
}
```

### `key_moments`

Purpose:

- capture the meaningful turns that changed the room
- avoid replaying every raw event

Each item should include:

- `id`
- `icon`
- `title`
- `detail`

Optional:

- `ts`
- `actor_id`
- `kind`
- `status`
- `node_refs`
- `evidence_refs`

Example:

```json
{
  "id": "m1",
  "icon": "💡",
  "title": "Renderer feels technical instead of conversational.",
  "detail": "This set the main product problem for the graph.",
  "actor_id": "suna",
  "kind": "raised",
  "status": "active",
  "node_refs": ["n-renderer-tone"],
  "evidence_refs": ["src-screenshots"]
}
```

### `evidence`

Purpose:

- show what grounded the room
- preserve provenance for repo, local, web, GitHub, or user-supplied references

Each item should include:

- `id`
- `icon`
- `label`
- `kind`
- `ref`
- `note`

Allowed `kind` values:

- `repo`
- `local`
- `github`
- `web`
- `user`

Examples:

```json
{
  "id": "src-poc",
  "icon": "📚",
  "label": "Current renderer screenshots",
  "kind": "local",
  "ref": "local://docs/cytoscape-poc.html",
  "note": "Showed why the graph needed simplification."
}
```

```json
{
  "id": "src-github",
  "icon": "🔗",
  "label": "Relevant GitHub issue",
  "kind": "github",
  "ref": "https://github.com/org/repo/issues/123",
  "note": "Captured prior product reasoning around graph readability."
}
```

### `nodes`

Purpose:

- define the visible graph objects
- preserve branches, ideas, decisions, missed questions, and evidence-bearing topics

Each node should include:

- `id`
- `kind`
- `label`
- `status`
- `icon`
- `why_it_matters`

Optional:

- `source_refs`
- `position`

Allowed `kind` values:

- `issue`
- `idea`
- `option`
- `challenge`
- `decision`
- `missing-question`
- `deferred`
- `rejected`
- `unresolved`
- `evidence`

Allowed `status` values:

- `active`
- `agreed`
- `deferred`
- `open`
- `rejected`
- `challenged`

### `edges`

Purpose:

- define meaningful relationships between visible graph nodes

Each edge should include:

- `from`
- `to`
- `relation`
- `label`

Optional:

- `status`
- `source_refs`

Allowed `relation` values:

- `raised`
- `challenged`
- `supported`
- `linked`
- `led_to`
- `deferred`
- `rejected`
- `left_open`
- `grounded_by`

## `graph-raw.json`

This is the source-of-truth structural log Elango maintains during the huddle.

### Top-Level Shape

```json
{
  "session_id": "2026-04-05-main",
  "actors": [],
  "sources": [],
  "events": []
}
```

### `actors`

Purpose:

- stable lookup table for named participants

Each item should include:

- `id`
- `name`
- `icon`
- `meta`

### `sources`

Purpose:

- stable lookup table for evidence references used in raw events

Each item should include:

- `id`
- `kind`
- `label`
- `ref`

Optional:

- `note`

### `events`

Purpose:

- append-only structural record of what changed in the room

Each event should include:

- `ts`
- `actor_id`
- `op`
- `target`
- `payload`

Optional:

- `note`

Allowed `op` values:

- `node_added`
- `node_updated`
- `edge_added`
- `status_changed`
- `source_attached`
- `question_missing`
- `decision_recorded`
- `deferred`
- `rejected`

### Raw Event Example

```json
{
  "ts": "2026-04-05T10:08:00Z",
  "actor_id": "suren",
  "op": "question_missing",
  "target": {
    "id": "n-current-state",
    "kind": "missing-question"
  },
  "payload": {
    "label": "Do we need a separate current-state artifact?",
    "status": "open",
    "source_refs": ["src-poc"]
  },
  "note": "Opened the duplication question without resolving it."
}
```

## Projection Rules

The projection pass should:

- compress raw events into a smaller set of key moments
- generate `what_stands_out`
- rank `people_involved` by influence
- collect `evidence` from attached source refs
- produce only meaningful nodes and edges for the visible graph

The projection pass should **not**:

- blindly mirror every raw event
- generate duplicate graph nodes for the same branch
- drop source provenance when evidence mattered to the discussion

## Recommendation

Treat the transient readable graph view as the renderer contract.

Treat `graph-raw.json` as the durable capture Elango updates every round.
