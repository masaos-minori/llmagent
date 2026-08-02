# Propagate the "config tool_names is not a routing input" fact to docs/04_mcp_01_system_overview.md and 06_09

## Priority
Medium

## Summary
The fact that `[mcp_servers.*].tool_names` is not used as a routing input (it is observation/validation-only) is stated in `docs/04_mcp_03_01` but missing from `docs/04_mcp_01_system_overview.md`'s explanation of the RuntimeToolRegistry/ToolRegistry/ToolRouteResolver distinction, and from `docs/04_mcp_06_09`'s circuit-breaker state-transition documentation.

## Reason for Change
This is one of the most easily-misunderstood facts in the MCP domain (per this review, the 3-concept distinction is "the most confusing" in the domain), and readers who only read `01_system_overview.md` or `06_09` (without also reading `03_01`) would reach the wrong conclusion about routing behavior.

## Implementation Intent
Add the same clarifying fact to both files, worded consistently with `03_01` and with the related fix already applied to `docs/04_mcp_06_03` (tracked in a separate issue), so a reader arriving at any of these 4 files reaches the correct understanding.

## Target Files or Areas
`docs/04_mcp_01_system_overview.md`, `docs/04_mcp_06_09`

## Required Changes
- In `01_system_overview.md`'s RuntimeToolRegistry/ToolRegistry/ToolRouteResolver section, add: "The runtime routing authority is `RuntimeToolRegistry`; `config/agent.toml`'s `tool_names` field is not used as a routing input (observation-only). See `docs/04_mcp_06_03` for detail."
- In `06_09`'s circuit-breaker section, add a note: "`[mcp_servers.*].tool_names` does not affect circuit breaker state or routing — it is reference information only, not a routing input (consistent with `docs/04_mcp_06_03`)."

## Acceptance Criteria
Both files state the tool_names-not-routing-input fact in wording consistent with `03_01` and `06_03`.

## Testing Expectations
Not required (documentation-only).

## Documentation Impact
`docs/04_mcp_01_system_overview.md` and `docs/04_mcp_06_09` each gain one clarifying note.

## Out of Scope
Do not restructure the RuntimeToolRegistry/ToolRegistry/ToolRouteResolver explanation or the circuit-breaker state machine itself in this issue — only add the cross-referencing fact.

## AI Implementation Instruction
Keep the added text to one sentence per file, worded consistently with the equivalent fix in `docs/04_mcp_06_03` (tracked separately) so all cross-references agree verbatim or near-verbatim.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_mcp.md §4 強化候補 (01_system_overview RuntimeToolRegistry区別, 06_09 circuit breaker)
- Generated at: 2026-08-02
