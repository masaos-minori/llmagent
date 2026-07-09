# Implementation: docs — fix stale tool_results_turn_max_chars description

## Goal

Replace stale `"Deprecated — tool_results table removed; no longer enforced"` description in `docs/05_agent_08_configuration.md` with accurate description of current enforcement.

## Scope

- `docs/05_agent_08_configuration.md` — line 250 field description

## Assumptions

1. `tool_results_turn_max_chars` is actively enforced in `tool_runner.py` as a cumulative per-turn limit.
2. No code changes required.

## Implementation

### Target file

`docs/05_agent_08_configuration.md`

### Procedure

1. Locate line 250 in `docs/05_agent_08_configuration.md`.
2. Replace the stale description with:
   "Maximum cumulative tool result characters added to LLM context in a single turn. Protects against excessive per-turn context growth from multiple tool outputs. When exceeded, omitted results are replaced with TURN_LIMIT_HINT."

### Details

- Single-line replacement in the config field table.
- Confirm no other stale references via `rg "tool_results.*deprecated\|no longer enforced" docs/`.

## Validation plan

| Check | Tool / Command | Target |
|---|---|---|
| No stale wording | `rg "tool_results.*deprecated" docs/` | 0 matches |
| No stale wording | `rg "no longer enforced" docs/` | 0 matches |
