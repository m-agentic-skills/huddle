# Huddle Config And Local Mode

## Goal

Document the agreed storage layout for huddle state and the fallback behavior for projects that are not in git.

## Decisions

- Huddle state should live under the user's config area, not directly under the home directory.
- The base root is:
  - `<user-home>/.config/muthuishere-agent-skills/`
- Storage should be branch-first so other branch-scoped systems can reuse the same branch folder later.
- Huddle state should live inside a dedicated `huddle/` folder under the branch root.
- `config.json` should remain repo-scoped, not branch-scoped.

## Final Layout

```text
<user-home>/.config/muthuishere-agent-skills/
└── <repo>/
    ├── config.json
    └── <branch>/
        └── huddle/
            ├── huddle-state.json
            └── <YYYY-MM-DD>.md
```

Meaning:

- repo config:
  - `<user-home>/.config/muthuishere-agent-skills/<repo>/config.json`
- branch root:
  - `<user-home>/.config/muthuishere-agent-skills/<repo>/<branch>/`
- huddle state:
  - `<user-home>/.config/muthuishere-agent-skills/<repo>/<branch>/huddle/`

## Why This Split

- `config.json` stays repo-scoped because it stores shared repo preferences.
- `<repo>/<branch>/` stays available for future branch-scoped systems beyond huddle.
- `huddle/` isolates meeting artifacts from any future branch-local state such as notes, plans, generated assets, or other skill data.

## Non-Git Mode

Huddle must still work when the current folder is not a git repository.

Fallback behavior:

- repo name:
  - use configured local repo name if present
  - otherwise use the current folder name
- branch:
  - use configured local branch if present
  - otherwise default to `main`
- user:
  - use configured local user if present
  - otherwise use the system username
- remote / PR state:
  - disabled

In non-git mode, huddle should not stop. It should run in local folder mode and record a warning internally that git context is unavailable.

## Bootstrap Command

To avoid re-entering local project identity every time, huddle supports a one-time bootstrap command:

```bash
python3 scripts/config_helper.py bootstrap <project_root> [repo_name] [branch] [user]
```

This writes local defaults into repo `config.json`.

Example:

```bash
python3 scripts/config_helper.py bootstrap /path/to/project MyProject main Muthukumaran
```

Stored fields:

- `reponame`
- `local_project_root`
- `local_repo_name`
- `local_branch`
- `local_user`
- `non_git_mode`

## Runtime Behavior

At startup, huddle should:

1. Try git-based discovery first.
2. If git is unavailable:
   - fall back to local folder mode
   - reuse stored config by matching `local_project_root`
3. Use the resolved repo name and branch to place huddle state under:
   - `<user-home>/.config/muthuishere-agent-skills/<repo>/<branch>/huddle/`

## Implemented

- `scripts/config_helper.py`
  - supports repo-scoped config
  - supports `bootstrap`
- `scripts/repo_context.py`
  - supports git mode and local folder mode
  - reuses stored config for non-git projects
- `scripts/meeting_state.py`
  - creates branch-first huddle directories under the new config root
