# Step 02: Discussion

This is the party-mode conversation loop, rewritten in our style.

## Select speakers

For each user message:

1. analyze the topic
2. pick 2-4 relevant personas
3. rotate participation over time instead of always using the same pair
4. if the user names a persona, always include that persona

## Response style

Use short labeled sections such as:

- `Emma (PM):`
- `Bob (Engineer):`
- `Carol (Designer):`
- `Devon (Security):`
- `Alice (Strategy):`

Rules:

- each persona must sound distinct based on `communicationStyle`
- personas may agree, disagree, or build on one another
- keep it useful, not theatrical
- if a persona asks the user a direct question, stop there and wait for the answer

## Meeting memory updates

After each meaningful round, update today's meeting file with:

- topic discussed
- key points
- decisions made
- open questions
- action items
- active personas in that round

Also update `meeting-state.json` with:

- `last_meeting_date`
- `current_topic`
- `open_questions`
- `action_items`
- `latest_summary`
- `active_personas`

## Meeting document shape

Keep `{YYYY-MM-DD}.md` in this structure:

```md
# Team Meeting

## Repo

## Date

## Participants

## Topics Discussed

## Decisions

## Open Questions

## Action Items

## Latest Summary
```

Append or refresh sections rather than duplicating them.

## Wrap-up detection

If the user is clearly wrapping up, do not just stop. Move to `step-03-smart-exit.md`.
