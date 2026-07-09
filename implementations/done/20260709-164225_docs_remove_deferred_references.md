# Implementation: docs — Remove "Deferred" classification references

## Goal

Remove all Deferred classification references from:
- `docs/05_agent_08_configuration.md`: Deferred bullet, "Deferred settings" subsection, `deferred` table row
- `docs/05_agent_07_cli-and-commands.md`: Deferred row from Reload classification summary table

## Scope

- `docs/05_agent_08_configuration.md`
- `docs/05_agent_07_cli-and-commands.md`

## Implementation

### Target files

1. `docs/05_agent_08_configuration.md`
2. `docs/05_agent_07_cli-and-commands.md`

### Procedure

#### File 1: `docs/05_agent_08_configuration.md`
- Remove "Deferred" bullet from Classification definitions (lines ~78-80).
- Remove entire "Deferred settings" subsection (lines ~87-91).
- Remove `deferred` row from `ConfigReloadOutcome` fields table (line ~134).

#### File 2: `docs/05_agent_07_cli-and-commands.md`
- Remove "Deferred" row from Reload classification summary table (line ~277).

## Validation plan

| Check | Tool / Command | Target |
|---|---|---|
| No deferred in docs | `grep -rn "deferred" docs/05_agent_08_configuration.md docs/05_agent_07_cli-and-commands.md` | no matches (except unrelated uses) |
