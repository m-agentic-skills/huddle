# Step 03: Smart Exit

Use natural wrap-up detection, not keyword triggers.

## Trigger this step when

The user's primary intent is to end or pause the meeting, for example:

- "that's enough for today"
- "let's stop here"
- "this was helpful"
- "we've covered it"
- "good for now"

Do not trigger if the phrase is incidental inside a larger question.

## Exit flow

1. summarize what the meeting covered today
2. list current decisions
3. list open questions
4. list action items
5. persist all of it to today's meeting file and `meeting-state.json`
6. tell the user they can resume later by starting `team-meeting` again in the same repo

## Final response format

Keep it short:

- `Summary`
- `Open`
- `Actions`

Then a one-line resume hint.
