# Huddle

Huddle is a repo-aware multi-persona discussion skill for engineering work.

It helps you think through implementation, architecture, testing, security, product tradeoffs, communication artifacts, and current ecosystem signals without turning the interaction into roleplay theater. The user drives. The room reacts. Decisions stay with the user.

## What It Does

- pulls in a small set of relevant personas for the current topic
- keeps discussion short, opinionated, and grounded in the repo
- supports research, planning, verification, wrap-up, and spec output modes
- records huddle state so discussions can be resumed later
- lets Elango turn the discussion into notes, summaries, specs, and decision flow views
- works in git repos and also supports local-folder mode for non-git projects

## Core Ideas

Huddle is designed around a few principles:

- small room by default
- artifact owner first, then domain expert, then one useful counterweight
- structured disagreement is useful; fake drama is not
- decisions belong to the user, not the personas
- notes and state should survive beyond one chat session

## Storage Model

Huddle stores state under the user's config area:

```text
<user-home>/config/.m-agent-skills/<repo>/
├── config.json
└── <branch>/
    └── huddle/
        ├── huddle-state.json
        └── <YYYY-MM-DD>.md
        └── graph-raw.json
```

That split is intentional:

- `config.json` is repo-scoped
- `<branch>/` is reserved for branch-scoped state
- `huddle/` contains only huddle artifacts
- `graph-raw.json` is the only persisted graph source of truth
- readable graph review is derived on request and opened in the hosted viewer

## Non-Git Projects

Huddle does not require git.

If the current folder is not a git repo, huddle falls back to local-folder mode:

- repo name defaults to the folder name
- branch defaults to `main`
- user defaults to the configured local user or the system username
- remote / PR behavior is skipped

To remember a local project identity once and reuse it later:

```bash
python3 scripts/config_helper.py bootstrap <project_root> [repo_name] [branch] [user]
```

## Main Components

- [`SKILL.md`](./SKILL.md): top-level skill contract
- [`references/activation-routing.xml`](./references/activation-routing.xml): routing and mode policy
- [`references/workflow.md`](./references/workflow.md): workflow overview
- [`references/steps/`](./references/steps): step-by-step execution rules
- [`references/personas/`](./references/personas): persona definitions
- [`scripts/meeting_state.py`](./scripts/meeting_state.py): huddle note/state creation
- [`scripts/repo_context.py`](./scripts/repo_context.py): tolerant startup context gathering
- [`scripts/config_helper.py`](./scripts/config_helper.py): repo config and local bootstrap support
- [`scripts/md_to_html.py`](./scripts/md_to_html.py): bundle markdown plus raw graph and open the hosted browser review surface
- [`e2e/run.py`](./e2e/run.py): smoke-test the raw state scripts and hosted review bundle flow

## Inspiration

Huddle was strongly inspired by BMAD's party-mode direction, especially:

- persona-driven multi-voice discussion
- markdown-defined agents
- resumable discussion state
- smart exit behavior

Huddle is not a BMAD copy. It adapts those ideas into a repo-first workflow with practical routing, persistent state, spec capture, and browser-review support.

It is also influenced by the stronger orchestration ideas seen in modern coding-agent systems:

- discussion separated from planning and verification
- coordinator-style routing without forcing the user to think in internal modes
- persistence and completion over one-shot cleverness
- practical tool use instead of pure conversational output

Credit belongs to BMAD for the original party-mode spark, and to the broader agent-tooling ecosystem for pushing toward better planning, verification, persistence, and completion patterns.
