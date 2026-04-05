# Step 00: Pre-flight

Run this before anything else. Derive the best available project identity before the huddle starts.

All commands in this step run from `{project-root}`.

## Check

```bash
git rev-parse --show-toplevel
git remote get-url origin
```

| What went wrong | Error contains | Tell the user |
|---|---|---|
| Not in a git repo | `not a git repository` / exit non-zero | "Not a git repo. Using local folder mode." |
| No remote | `fatal` / empty output | "No git remote found. This skill works best with a remote set up." — continue anyway using directory name as repo name. |

### Derive REPO_NAME and OWNER_REPO

From `git remote get-url origin`, parse the remote URL:

- HTTPS: `https://github.com/owner/repo.git` → `REPO_NAME=repo`, `OWNER_REPO=owner/repo`
- SSH: `git@github.com:owner/repo.git` → same
- No remote or non-GitHub remote: use `basename $(git rev-parse --show-toplevel)` as `REPO_NAME`, leave `OWNER_REPO` empty.
- Not in git at all: use `basename {project-root}` as `REPO_NAME`, leave `OWNER_REPO` empty, and default `BRANCH=main`.

If the project is not in git and the user wants that local identity remembered, bootstrap it once:

```bash
python {skill-root}/scripts/config_helper.py bootstrap {project-root}
```

This writes local defaults to repo `config.json` so future huddles can reuse:
- local project root
- repo name
- default branch
- local user

Pass `REPO_NAME` and `OWNER_REPO` to step-01. Continue.

## gh CLI (optional)

Do not require `gh`. Check silently:

```bash
gh auth status
```

- If available and authenticated: set `GH_AVAILABLE=true` — enables PR listing in step-01.
- If missing or unauthenticated: set `GH_AVAILABLE=false` — skip all `gh` calls silently, no error shown.
- If authenticated but there is no git remote, still set `GH_AVAILABLE=false` for this huddle run. Auth alone is not enough to query PRs.
- If not in a git repo, set `GH_AVAILABLE=false`.
