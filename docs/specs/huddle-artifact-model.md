# Huddle Artifact Model

## Goal

Define the persisted artifacts Huddle should maintain for every session and the transient review projection derived from them:

1. Markdown spec / notes
2. Raw graph log
3. Readable graph view on request

This keeps Huddle readable for humans while also making the reasoning flow, participant influence, and evidence grounding explicit.

## Decision

Huddle should not choose between Markdown and graph.

It should keep both:

- Markdown for durable human-readable output
- Raw graph log for structural discussion capture
- A readable graph view derived on request for what a human should inspect

The visible product should feel like a huddle:

- the user drives
- named participants contribute
- Elango maintains state in the background
- the renderer shows what changed, how the room moved, and where it stands now

## The 3 Artifacts

### 1. Markdown Spec

Purpose:

- human-readable artifact
- summary, notes, spec, or action-item export
- easy to review, save, and share

Examples:

- meeting summary
- feature spec
- decision note
- action-item list

Owner:

- Elango

Characteristics:

- readable
- structured
- export-friendly
- not the only source of truth

### 2. Raw Graph Log

Purpose:

- preserve discussion structure over time
- capture branches, objections, reversals, rejected paths, refinements, joins, and evidence attachments
- stay stable even if the renderer or review surface changes

Questions it should answer:

- what structurally changed in the room?
- who added or challenged what?
- what evidence got attached?
- what branch was opened, deferred, or rejected?

Owner:

- Elango

Characteristics:

- append-oriented
- structural
- participant-aware through actor ids
- source-aware through source refs
- maintained by an internal background pass, not by visible persona chatter

### 3. Readable Graph View

Purpose:

- show the latest human-readable room picture
- show what stands out, who mattered, which moments changed the room, what evidence grounded it, and how the main branches connect

Questions it should answer:

- what the room was trying to solve
- who shaped the discussion
- what stood out immediately
- which moments changed the room
- what evidence grounded the room
- how branches, objections, and decisions connect

Characteristics:

- derived from the raw graph log
- human-readable
- participant-aware
- evidence-aware
- optimized for orientation, not raw replay
- not persisted by default

## Suggested Storage

Store these under the branch huddle directory:

```text
<user-home>/.config/muthuishere-agent-skills/<repo>/<branch>/huddle/
├── huddle-state.json
├── <YYYY-MM-DD>.md
├── graph-raw.json
```

Meaning:

- `huddle-state.json`
  - lightweight session state for routing/resume
- `<YYYY-MM-DD>.md`
  - human-readable session artifact
- `graph-raw.json`
  - append-oriented structural room changes
- transient readable graph view
  - generated from the raw graph when the user asks for review

## Visible State Model

Huddle should present state in 3 layers:

### 1. Visible Room

Show:

- the user
- the active named participants for the current round
- their icons and names
- who influenced the round when that is worth surfacing

Do not show:

- generic boxes like `Experts (LLMs)`
- abstract system-only labels unless they help the user understand the room

### 2. State Updates

Show updates in human terms:

- what was added
- what was challenged
- what was linked
- what was agreed
- what was deferred
- what stayed open

This is the readable surface of the evolving graph.

### 3. Current State

Show the latest room picture:

- current problem
- current context
- chosen direction
- open questions
- next actions
- current status of major branches

## Icon Legend

Use a small, stable icon set across history, current state, and rendered review views.

### Status Icons

- `✅` Agreed
- `⏸️` Deferred
- `❓` Open
- `⚔️` Challenged
- `🔗` Linked
- `💡` Added
- `📝` Captured in spec

### Participant Representation

Participants should appear with:

- their existing icon
- their display name
- short text only

Examples:

- `🧠 Maya`
- `🏛️ Suren`
- `📚 Kishore`
- `📐 Elango`

The renderer should avoid oversized persona labels. The room should feel neat, compact, and readable.

## Source of Presentation State

The HTML renderer should not invent presentation meaning on its own.

Elango should write presentation-oriented state into the JSON artifacts, and the renderer should primarily display that state.

### Derived Graph Should Carry

- participant icon, name, and short meta
- event status
- event display tag
- event display title
- event display detail
- node status
- node display tag
- node display detail

### Renderer Should Do

- read those fields
- map them into cards, chips, and graph labels

### Renderer Should Not Do

- derive the core business meaning of the discussion
- invent statuses that Elango did not record
- become the place where huddle logic lives

Elango owns the semantics.
The HTML layer owns presentation.

## Graph Model

### Node Types

Minimum node types:

- `problem`
- `context`
- `option`
- `argument`
- `tension`
- `decision`
- `question`
- `action`
- `result`

Optional later:

- `constraint`
- `risk`
- `artifact`
- `assumption`
- `evidence`
- `participant`
- `update`

### Edge Types

Minimum edge types:

- `has_context`
- `suggests`
- `supports`
- `opposes`
- `refines`
- `leads_to`
- `decides`
- `opens`
- `resolves`
- `results_in`

Optional later:

- `depends_on`
- `supersedes`
- `blocked_by`
- `agrees_with`
- `disagrees_with`
- `defers`

## State Representation

The graph is not only a technical structure. It is the underlying representation of the huddle.

### Raw Graph Should Represent

- who introduced a thread
- when a branch opened
- when two ideas were linked
- when something was challenged
- when the room converged
- when something was deferred instead of decided

### Graph View Should Represent

- what is currently active
- what has been agreed
- what is still open
- what has been deferred
- what should happen next
- which participants most recently influenced the state, when useful

### Markdown Should Represent

- the readable decision/spec layer
- rationale
- rejected paths
- deferred items
- open questions
- next actions

Markdown is a projection of the graph, not the source of truth.

## Graph View Shape

This should represent the latest human-readable room picture.

Example:

```json
{
  "session_id": "2026-04-05-main",
  "generated_at": "2026-04-05T12:00:00Z",
  "main_question": "How should Huddle show reasoning flow?",
  "decision": "Keep raw graph capture and derive the readable graph later.",
  "decision_why": "The room wanted stable capture and clearer inspection.",
  "what_stands_out": [
    { "icon": "✅", "text": "Raw-first capture, view-later projection." }
  ],
  "people_involved": [
    { "id": "user", "name": "Muthu", "icon": "🎼", "meta": "You", "influence": "Directed the product shape." },
    { "id": "suren", "name": "Suren", "icon": "🏛️", "meta": "Architect", "influence": "Pushed for clearer state boundaries." }
  ],
  "key_moments": [
    { "id": "m1", "icon": "💡", "title": "Renderer felt too technical.", "detail": "This set the main product problem.", "actor_id": "user" }
  ],
  "evidence": [
    { "id": "src1", "icon": "📚", "label": "Local renderer screenshots", "kind": "local", "ref": "local://docs/cytoscape-poc.html", "note": "Grounded the rendering discussion." }
  ],
  "nodes": [
    { "id": "n1", "kind": "issue", "label": "Renderer felt technical", "status": "active", "icon": "💡", "why_it_matters": "This was the main UX problem." },
    { "id": "n2", "kind": "decision", "label": "Use raw-first graph capture", "status": "agreed", "icon": "✅", "why_it_matters": "It keeps Elango lightweight and stable." }
  ],
  "edges": [
    { "from": "n1", "to": "n2", "relation": "led_to", "label": "led to" }
  ]
}
```

## Raw Graph Shape

Raw graph should preserve structural change over time.

Recommended model:

- append-only event stream
- actor and source lookup tables

Recommended structure:

```json
{
  "session_id": "2026-04-05-main",
  "actors": [
    { "id": "user", "name": "Muthu", "icon": "🎼", "meta": "You" }
  ],
  "sources": [
    { "id": "src1", "kind": "local", "label": "Renderer screenshot", "ref": "local://docs/cytoscape-poc.html" }
  ],
  "events": [
    {
      "ts": "2026-04-05T11:10:00Z",
      "actor_id": "user",
      "op": "node_added",
      "target": { "id": "n1", "kind": "issue" },
      "payload": { "label": "Renderer felt technical", "status": "active", "source_refs": ["src1"] }
    }
  ]
}
```

## Update Rules

### Background Prompt Pattern

Elango should update these artifacts through an internal background pass after each meaningful exchange.

Recommended structure:

```xml
  <background_pass>
  <discussion_delta />
  <raw_graph_update />
  <graph_view_projection />
  <markdown_projection />
  <visibility>internal only</visibility>
</background_pass>
```

Why:

- structured sections reduce collisions between visible conversation and hidden state work
- isolated background updates keep the user-facing room clean
- separate raw and graph-view sections prevent the model from collapsing structural capture and readable synthesis

### During Discussion

Elango should:

- append new nodes to the raw graph when a new topic/option/argument appears
- record edges when reasoning relationships become clear
- mark decisions only when the user makes the call
- mark deferred items when the room intentionally postpones them
- record rejected paths when the room clearly discards one
- preserve open questions separately from decisions
- preserve lightweight participant attribution and source refs when useful

### When Producing Graph View

Elango should:

- generate what stands out
- identify who materially shaped the room
- compress raw events into key moments
- attach evidence with readable refs
- keep only meaningful visible nodes and edges

### When Producing Markdown

Elango should:

- project graph state into human-readable form
- include rationale and rejected paths when relevant
- include agreed, deferred, and open status clearly
- optionally embed Mermaid diagrams derived from the graph

## Renderer Views

The renderer should support 3 views from the same artifact set.

### 1. Spec View

Shows:

- Markdown notes/spec
- decisions
- deferred items
- rationale
- open questions
- actions

Best for:

- reading
- review
- sharing

Zoom:

- no custom zoom surface required
- rely on browser zoom and readable layout

### 2. Conversation View

Shows:

- how the discussion evolved
- participant-driven updates over time
- branch openings and joins
- challenges and reversals
- where the room changed direction

Best for:

- replay
- understanding reasoning flow
- seeing why the room converged

Zoom:

- pan and zoom should be native
- this is a map-like surface

Animation ideas:

- stagger update reveal
- animate branch growth
- step-through timeline scrubber
- highlight newly added, challenged, agreed, and deferred nodes

### 3. Standing View

Shows:

- main question
- decision and why
- what stands out
- connected branches
- deferred items
- open questions
- evidence grounding

Best for:

- quick orientation
- standups
- resume
- "where do we stand?"

Zoom:

- pan and zoom should be native
- the user should be able to inspect branches and statuses without losing context

Animation ideas:

- pulse active nodes
- dim less-relevant branches
- smooth transitions when the graph view refreshes

## Renderer Surface Guidance

The renderer should feel like a huddle, not a generic systems graph.

### Top Strip

Show:

- user
- active participants with icon + name
- small text only

Avoid:

- oversized architecture boxes
- generic labels like `Experts (LLMs)`

### Update Language

Use readable labels such as:

- `💡 Added`
- `⚔️ Challenged`
- `🔗 Linked`
- `✅ Agreed`
- `⏸️ Deferred`
- `❓ Open`
- `📝 Captured`

### Current-State Language

Prefer:

- `Agreed`
- `Deferred`
- `Open`
- `Next`

Avoid:

- `derived nodes`
- `derived links`
- raw graph jargon unless it helps debugging

## Elango's Role

Elango should evolve from:

- silent note-taker

to:

- graph steward
- state curator
- Markdown/spec renderer

That means:

- he maintains the raw graph
- he derives a human-readable graph projection on demand
- he produces Markdown as a projection of the graph-backed session state

## Product Framing

This keeps Huddle aligned with the intended product direction without forcing execution to become the headline.

Huddle can be framed as:

- a participant-driven stateful discussion room
- with evolving shared state
- visible graph review
- human-readable spec output
- background state maintenance by Elango

Execution can stay secondary or background-capable.

## Recommended Next Step

Implement in this order:

1. add `graph-raw.json`
2. derive a readable graph projection on request
3. define Elango update rules in the skill
4. render graph-review and standing views with icons and readable labels
5. add zoomable graph map views
6. keep Markdown as the readable export layer
