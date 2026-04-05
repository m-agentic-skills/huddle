# Huddle Global Roster Rename

## Goal

Adjust the huddle persona roster so it keeps some existing names, adds broader global appeal, and preserves clear role ownership.

This change is naming-only at first. Role titles, capabilities, and behavior remain the source of truth for what each persona does.

## Target Roster

Keep:

- Vidya
- Suna
- Elango
- Prabagar
- Shaama
- Senthil
- Babu
- Dileep
- Suren
- Deepak
- Deva
- Kishore

Rename:

- Amy -> Maya
- Vin -> Luca
- Jana -> Nina
- Peter -> Wei
- Santio -> Sofia
- K-Prabu -> Amara
- Hari -> Srey

## Role Mapping

- Strategy -> Maya
- Frontend -> Luca
- Backend -> Shaama
- Design -> Suna
- PM -> Prabagar
- Security -> Senthil
- Demand Reality -> Babu
- Founder Visionary -> Dileep
- Tester -> Nina
- Architect -> Suren
- Analyst -> Vidya
- Tech Writer -> Deepak
- Solo Dev -> Srey
- Test Architect -> Deva
- Data Analyst -> Wei
- Presentation Specialist -> Sofia
- Storyteller -> Kishore
- Trend Researcher -> Amara
- Spec Architect -> Elango

## Constraints

- Keep persona titles and functional roles intact.
- Do not weaken routing clarity.
- Do not leave stale old-name references in active config.
- Historical notes may remain unchanged unless they cause confusion.

## Execution Plan

### Step 1: Rename files

Rename these persona files:

- `references/personas/amy-strategist.md` -> `references/personas/maya-strategist.md`
- `references/personas/vin-frontend.md` -> `references/personas/luca-frontend.md`
- `references/personas/jana-tester.md` -> `references/personas/nina-tester.md`
- `references/personas/peter-dataanalyst.md` -> `references/personas/wei-dataanalyst.md`
- `references/personas/santio-presentation.md` -> `references/personas/sofia-presentation.md`
- `references/personas/k-prabu-trendresearcher.md` -> `references/personas/amara-trendresearcher.md`
- `references/personas/hari-solodev.md` -> `references/personas/srey-solodev.md`

### Step 2: Update persona contents

For the seven renamed personas, update:

- `displayName`
- frontmatter `name`
- any direct self-name references
- any examples or signature lines that depend on the old name

### Step 3: Update routing and discussion docs

Update active references in:

- `references/steps/step-02-discussion.md`
- `references/activation-routing.xml`
- any other active docs/examples that name these personas directly

### Step 4: Sweep for stale names

Search for:

- Amy
- Vin
- Jana
- Peter
- Santio
- K-Prabu
- Hari

Then replace only active-config references, leaving unrelated historical material alone unless it creates confusion.

### Step 5: Verify

Confirm:

- all active files use the new names
- file names and persona display names match
- routing examples use the new names
- no stale active references remain

## Status

- Step 1 complete: persona files renamed
- Step 2 complete: renamed persona contents updated
- Step 3 complete: active routing and discussion docs updated
- Step 4 complete: stale-name sweep run across active files
- Step 5 complete: verification passed for active skill files

Old-name references remain only in this spec as before/after mapping, which is intentional.
