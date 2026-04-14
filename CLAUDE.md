# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

Huddle is a Claude Code skill that runs repo-aware, multi-persona engineering discussions. Users trigger it with phrases like "start a huddle" or "huddle up". The user drives all decisions; personas provide perspectives, then stop and wait.

## Skill Structure

```
SKILL.md                          # Skill registry entry (name, trigger phrases)
references/
  activation-routing.xml          # Mode router and flow-control policy (the brain)
  workflow.md                     # Variable definitions and execution sequence
  persona-roster.xml              # Lightweight persona index
  personas/                       # Full persona definitions (voice, principles)
  steps/
    step-00-preflight.md          # Single-command startup via meeting_state.py
    step-01-meeting-init.md       # Load user, config, state, personas
    step-02-discussion.md         # Main discussion loop (all modes route here)
    step-03-smart-exit.md         # Wrap-up / pause persistence
    step-deepak-document.md       # Project documentation sub-task
    step-elanchezian-brainstorm.md # Progressive brainstorming sub-task
scripts/                          # Python helpers (no external deps, stdlib only)
e2e/run.py                       # Smoke tests
```

## Key Architecture Decisions

- **Append-only raw writes, synthesis on demand.** During live discussion, NO file writes happen on normal rounds. On decisions/milestones, a single raw event JSON file is written directly to `{huddle_dir}/raw/` using the Write tool — no Python script, no background process. When the user asks for notes or wraps up, synthesis reads all `raw/*.json` + conversation context, writes `huddle-state.json` + `.md`, and deletes the raw files.
- **`huddle-state.json` is the synthesized source of truth** for all huddle state (decisions, participants, key moments, open questions, action items). Written only on explicit ask or wrap-up — not every round.
- **User-level config at `~/config/.m-agent-skills/userconfig.json`** stores `git_user`, `python_bin`, and `gh_available` — detected once globally on first ever huddle run, shared across all repos. Repo-level config at `~/config/.m-agent-skills/{reponame}/config.json` stores only repo-specific values (`reponame`, `owner_repo`, `default_branch`).
- **`PYTHON_BIN` detected once globally.** Stored in `userconfig.json` after first detection. All subsequent script calls use this variable. Never hardcode `python3` or `python`.
- **Graph views are derived on demand** by Elango from `huddle-state.json` + conversation context. The HTML review surface (`docs/index.html`) derives presentation client-side.
- **`activation-routing.xml`** is the central policy file. It defines modes (discussion, planning, verification, research, spec-review, wrap-up), flow-control rules, and disambiguation logic. Changes to huddle behavior almost always start here.
- **Steps execute in order** defined by `workflow.md`. Steps never skip; they stop and report on failure.
- **Personas are selected per-topic** (small room by default). The roster is in `persona-roster.xml`; full persona behavior is in individual markdown files under `references/personas/`.

## Scripts

All scripts are Python 3, stdlib-only, and output JSON to stdout.

| Script | Usage | Purpose |
|---|---|---|
| `meeting_state.py` | `python3 scripts/meeting_state.py ensure <project_root> <date>` | Single entry point for preflight — derives repo identity, detects `python_bin`, creates state files, runs parallel probes (git user/status/log, PRs, project scan, history), returns JSON with `next_action` and `python_bin` |
| `huddle_writer.py` | `{PYTHON_BIN} scripts/huddle_writer.py <huddle_dir> '<event_json>'` | Standalone event writer for non-Claude agents (Codex, Copilot, Windsurf). Claude uses Write tool directly instead. |
| `config_helper.py` | `{PYTHON_BIN} scripts/config_helper.py read|get|set|bootstrap ...` | Per-repo config CRUD at `~/config/.m-agent-skills/{reponame}/config.json` |
| `repo_context.py` | `{PYTHON_BIN} scripts/repo_context.py snapshot` | Gathers repo context (git state, PRs, remote info); supports non-git local-folder mode |
| `project_state.py` | `{PYTHON_BIN} scripts/project_state.py check|read|write ...` | Weekly project documentation freshness gate |
| `md_to_html.py` | `{PYTHON_BIN} scripts/md_to_html.py <note.md> [base_url]` | Bundles huddle note + `huddle-state.json` into a gzip+base64 URL fragment and opens the hosted review page |

## Running Tests

```bash
python3 e2e/run.py
```

This smoke-tests `meeting_state.py ensure`, `md_to_html.py` bundling, and verifies removed files stay removed. Uses a temp `$HOME` so it won't touch real config.

## State Storage Layout

```
~/config/.m-agent-skills/
  userconfig.json                # Global: git_user, python_bin, gh_available (detected once)
  {reponame}/
    config.json                  # Repo-scoped: reponame, owner_repo, default_branch
    project-state.json           # Project doc freshness metadata
    {branch}/huddle/
      huddle-state.json          # Synthesized state (written on demand/wrap-up only)
      {YYYY-MM-DD}.md            # Daily huddle note (written on demand/wrap-up only)
      raw/                       # Append-only event files (direct Write tool)
        {ts}_decision.json       # One file per decision
        {ts}_milestone.json      # One file per milestone
```

Branch names are sanitized for filesystem (`feature/login` -> `feature-login`). Cross-branch reads scan sibling branch folders for context.

## Installation

```bash
./install.sh    # Symlinks skill into ~/.claude/skills/huddle (or ~/.agents/skills/)
./uninstall.sh  # Removes the symlink
```

## Non-Git Mode

Huddle works without git. Falls back to local-folder mode using folder name as repo identity. Bootstrap a local identity with:
```bash
python3 scripts/config_helper.py bootstrap <project_root> [repo_name] [branch] [user]
```
