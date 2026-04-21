# Step: Deepak — Document Project

Deepak runs this step when the user explicitly asks to document the project,
or when they say yes to Deepak's natural offer during a huddle.

This step runs AT MOST ONCE per session. It is skipped entirely if
`project_state.py check` returned `scan: false` for any gate reason.

---

## 1. Change Detection

Run before any scan work:

```bash
python3 {skill-root}/scripts/project_state.py check {REPO_NAME}
```

| Result | Action |
|---|---|
| `scan: true`, reason contains "no project docs" | Proceed to scan — first time |
| `scan: true`, reason contains "changed since last scan" | Tell user: "Project docs are {age_days} days old and the repo has changed. Refreshing now." Proceed to scan. |
| `scan: false`, any reason | Tell user docs are current or gates failed. Do not scan. Return to huddle. |

If user explicitly asked (via route trigger), bypass the weekly gate and always proceed.

---

## 2. Quick Scan — Sources (read in order, skip missing silently)

### Identity
- `README.md`

### Packages & Versions
- `package.json` — `dependencies`, `devDependencies`, versions
- `pyproject.toml` or `requirements.txt`
- `go.mod`
- `Gemfile`
- `Cargo.toml`
- `pom.xml` — Maven dependencies + versions
- `build.gradle` or `build.gradle.kts` — Gradle dependencies + versions

### Task Runners & Key Commands
- `Makefile` — targets
- `Taskfile.yml` or `Taskfile.yaml` — tasks
- `package.json` — `scripts` block
- `build.gradle` — task names

### Environment Variables
- `.env.example` or `.env.sample`
- `docker-compose.yml` — `environment:` blocks
- grep `process\.env|os\.environ|os\.getenv` in `src/` (top 30 matches only, file + line)

### Tests
- `pytest.ini`, `jest.config.*`, `vitest.config.*`, `build.gradle` test config
- Folder structure of `tests/`, `__tests__/`, `spec/`, `test/`
- First 5 test file names found (for naming style)

### Styles / UI
- `tailwind.config.*`
- CSS framework in deps (`styled-components`, `sass`, `less`, etc.)

### CI / Security / Performance
- `.github/workflows/` — list files, read first 30 lines of each
- `Dockerfile` — read fully

### PRs (only if GH_AVAILABLE=true)
```bash
gh pr list --state open  --limit 10 --json number,title,author,headRefName
gh pr list --state closed --limit 10 --json number,title,mergedAt
```

### Recent Git Activity
```bash
git log --oneline --since="30 days ago"
```

---

## 3. Infer — Do Not Hallucinate

For any section where no evidence is found, write exactly:
> *Not documented — could not be inferred from repo.*

Never guess. Never fabricate requirements, env vars, or features.

---

## 4. Write `project.md`

Save to: `~/.config/muthuishere-agent-skills/{REPO_NAME}/project.md`

Project docs live in the skill config folder only — not in the repo. Keeps repos clean and state skill-private.

### Sections (in order)

**1. Project Identity**
Name, purpose (1 paragraph), project type (web app / CLI / library / API / other), primary language(s).

**2. Tech Stack & Packages**
Runtime deps and dev deps with versions. Group by package manager if multiple present.

**3. Functional Requirements**
What the system does — inferred from README, docs, folder names, and PR titles. Bullet list.

**4. Non-Functional Requirements**
Performance targets, scalability notes, deployment target, browser/platform support, auth model — inferred from config and CI only.

**5. Environment Variables**
Table: `Variable | Required | Description`. Source from `.env.example` and grep results.

**6. Test Strategy**
Test runner, coverage setup, test types present (unit / integration / e2e), how to run tests.

**7. Test File Style**
Co-located (`*.test.ts` next to source) vs separate (`tests/` folder). Naming convention. Framework confirmed.

**8. Package Structure Style**
Inferred from folder shape only — do not read source files:
- Layered (controllers / services / repos)
- Feature-based (feature folders with own components + tests)
- Monorepo (`packages/` or `apps/` subfolders)
- Flat (everything at root)
- Domain-driven (domain folders)

**9. Performance Considerations**
Caching (deps, CI cache steps), connection pooling (inferred from deps), build optimisation (multi-stage Docker, tree shaking), perf-related env vars.

**10. Security Considerations**
Auth mechanism (inferred from deps — passport, spring-security, bcrypt, JWT etc.), secret management pattern, CI security scans (Snyk, CodeQL, Dependabot), non-root Docker user, sensitive env vars.

**11. Styles / UI**
CSS approach, component library, design token files. Omit entirely if no frontend detected.

**12. Key Commands**
Install, dev, build, test, lint, deploy — from Makefile, Taskfile, Gradle, npm scripts.

**13. Folder Structure**
Two levels deep. Exclude `node_modules/`, `.git/`, `dist/`, `build/`, `__pycache__/`. Annotate each top-level folder with inferred purpose.

**14. PR Snapshot + Recent Activity**
Open PRs (what's in flight), last 10 closed PRs (what shipped), git log last 30 days.

---

## 5. Write `project-state.json`

After writing `project.md`, get current HEAD and detected stack, then run:

```bash
python3 {skill-root}/scripts/project_state.py write {REPO_NAME} {HEAD_SHA} {stack_csv}
```

Example:
```bash
python3 scripts/project_state.py write huddle abc1234 "Python,JavaScript"
```

---

## 6. Announce Completion

Tell the user:

> "📝 Deepak: Project doc written. {N} sections captured.{flag_note}"

Where `{flag_note}` = " {X} sections had no evidence and are flagged." only if any sections were unfilled.

---

## RETURN PROTOCOL

This is a sub-task step. After announcing completion, execute this protocol exactly:

1. **Re-read** `references/steps/step-02-discussion.md` to restore the discussion loop context.
2. **Read** `huddle-state.json` — restore `active_personas` and `current_topic`.
3. **Ask {GIT_USER}:**
   > "📝 **Deepak** _(Tech Writer)_ — Done. Want to pick up where we left off, or take this in a new direction?"
4. **Wait.** Do not start a persona round, do not continue conversationally.
5. **When {GIT_USER} responds with "yes" or "pick up" or affirmative:**
   - If `current_topic` is set → restore `active_personas`, re-open that topic in step-02, address it directly
   - If `current_topic` is null or empty → this was a first-time doc offer before any discussion; show the persona roster and ask: "{GIT_USER}, what do you want to work through today?"
6. **When {GIT_USER} responds with a new topic or direction** → treat their message as the first topic, route into step-02 normally.

Do not chain into another sub-task or persona round before {GIT_USER} responds.

