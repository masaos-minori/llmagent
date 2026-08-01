# Confirm and document hot-reload path for RuntimeToolRegistry in docs/04_mcp_03_06

## Priority
Medium

## Summary
`docs/04_mcp_03_06_tool-runtime-availability-metadata.md` documents the `/v1/tools` endpoint as reflecting RuntimeToolRegistry's current state, and describes the config_dependent/enabled/disabled_reason 4-state model, but does not state whether changing `config/agent.toml` and reloading actually rebuilds RuntimeToolRegistry, or whether a full process restart is required. This may relate to `docs/04_mcp_06_17`'s stated constraint that `/reload` does not affect `[mcp_servers.*]`.

## Reason for Change
An operator who changes config and reloads, expecting the change to take effect, could unknowingly continue operating on stale tool-availability state if a restart is actually required — a real operational risk this review flags as unconfirmed.

## Implementation Intent
Investigate the actual reload/restart requirement via source inspection, and document the confirmed behavior — or, if the investigation is inconclusive, register the gap explicitly as a Needs Confirmation item rather than leaving it silently unaddressed.

## Target Files or Areas
`docs/04_mcp_03_06_tool-runtime-availability-metadata.md`, cross-referenced against `docs/04_mcp_06_17`

## Required Changes
- Investigate whether changing `config/agent.toml` and calling `/reload` (or an equivalent mechanism) actually rebuilds RuntimeToolRegistry, or whether a full process restart is required.
- Add the confirmed finding to `03_06`, explicitly cross-referencing `06_17`'s existing `/reload` scope constraint (`[mcp_servers.*]` is out of scope for reload) if related.
- If the investigation cannot conclusively determine the behavior, add an explicit Needs Confirmation note rather than asserting an unverified answer.

## Acceptance Criteria
`03_06` states, as confirmed fact, whether config changes require a restart to take effect for tool availability — or explicitly marks this as an open Needs Confirmation item.

## Testing Expectations
Not required (documentation-only) unless a live reload-then-check-tools experiment is performed to confirm behavior, which would strengthen the finding if feasible.

## Documentation Impact
`docs/04_mcp_03_06` gains a confirmed (or explicitly open) reload-behavior statement.

## Out of Scope
Do not implement a hot-reload mechanism for RuntimeToolRegistry in this issue if one does not currently exist — documentation only, reflecting current reality.

## AI Implementation Instruction
Investigate via source reading (and a live reload test if feasible) before writing the finding — do not guess based on the plausibility of either answer.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_mcp.md §4 強化候補 (03_06 ホットリロード経路), §6B (ホットリロード経路の有無)
- Generated at: 2026-08-02
