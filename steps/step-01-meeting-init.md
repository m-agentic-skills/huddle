# Step 01: Meeting Init

## 1. Identify the repo

Run:

```bash
gh repo view --json name,nameWithOwner
```

If it fails because `gh` is missing, auth is missing, or this is not a GitHub repo, stop and say so plainly.

Set:

- `REPO_NAME` = `.name`
- `OWNER_REPO` = `.nameWithOwner`

## 2. Prepare repo meeting memory

Use the bundled helpers:

```bash
python {skill-root}/scripts/config_helper.py read {REPO_NAME}
python {skill-root}/scripts/meeting_state.py ensure {REPO_NAME} {YYYY-MM-DD}
```

Use:

```text
~/m-agentic-skills-config/{REPO_NAME}/
├── config.json
└── team-meetings/
    ├── meeting-state.json
    └── {YYYY-MM-DD}.md
```

Create missing directories and files if needed.

If `config.json` does not exist, initialize it with:

```json
{
  "reponame": "{REPO_NAME}"
}
```

The `meeting_state.py ensure` command should create:

- `meeting-state.json`
- today's `{YYYY-MM-DD}.md`

## 3. Load today's state

Load:

- today's meeting file, if it exists
- `meeting-state.json`, if it exists

Extract:

- unresolved topics
- open questions
- action items
- prior decisions from today
- most recent active personas

## 4. Load personas

Read all markdown files in `./personas/`.

For each persona, use:

- frontmatter fields
- body content

Required fields:

- `name`
- `displayName`
- `title`
- `role`
- `identity`
- `communicationStyle`
- `principles`
- `domains`
- `capabilities`

If persona files are missing or invalid, stop and say which files are missing required fields.

## 5. Start context

If a meeting exists for today, begin by briefly summarizing:

- what was already discussed
- what remains unresolved

Otherwise, start a fresh meeting note with:

- repo
- date
- participants
- opening topic
