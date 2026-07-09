# Implementation: docs — add TURN_LIMIT_HINT cross-reference to tool_results_turn_max_chars

## Goal

Add a cross-reference from the `TURN_LIMIT_HINT` section in `docs/05_agent_06_tool-execution-and-approval.md` to the `tool_results_turn_max_chars` field in `docs/05_agent_08_configuration.md`.

## Scope

- `docs/05_agent_06_tool-execution-and-approval.md` — line 236 (TURN_LIMIT_HINT section)

## Assumptions

1. `TURN_LIMIT_HINT` is already documented at line 236 of the target file.
2. No code changes required.

## Implementation

### Target file

`docs/05_agent_06_tool-execution-and-approval.md`

### Procedure

1. Locate line 236 in `docs/05_agent_06_tool-execution-and-approval.md` (TURN_LIMIT_HINT section).
2. Add a note:
   "This hint is appended when `tool_results_turn_max_chars` (see 05_agent_08_configuration.md) is exceeded."

### Details

- Single sentence addition after the existing TURN_LIMIT_HINT description.

## Validation plan

| Check | Tool / Command | Target |
|---|---|---|
| Cross-reference present | `rg "tool_results_turn_max_chars" docs/05_agent_06_tool-execution-and-approval.md` | 1 match |
