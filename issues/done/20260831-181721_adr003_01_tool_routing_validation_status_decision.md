# Decide whether Routing Drift validation (tool_routing_validation.py) is a current architectural decision or should be deprecated

## Priority
Medium

## Summary
`docs/adr/ADR-003-runtime-tool-registry-routing-authority.md` was revised (2026-08-31, ADR-013
merge) to remove all ADR-level content assigning `ToolRegistry`/`tool_names` a current
architectural role in Routing Drift validation. The implementation
(`scripts/shared/tool_routing_validation.py`, `ToolRegistry.validate_tool_names_match()`) still
performs this validation and is actively invoked and tested, with no current ADR governing it.

## Background
The ADR-003/ADR-013 consolidation instructions explicitly required removing all ADR content
that assigns ToolRegistry/tool_names a drift-validation role, and required reporting — not
silently retaining — any case where the implementation still contains this validation. This
issue is that reported follow-up.

## Problem
(Evidence: Explicit in code) `scripts/shared/tool_routing_validation.py` exists and is imported
by `scripts/agent/services/mcp_tool_discovery.py`. `ToolRegistry.validate_tool_names_match()`
and `ToolRegistry.get_all_tool_names()` are used at runtime. Tests reference this behavior:
`tests/agent/test_startup_routing_drift.py`, `tests/mcp_servers/cicd/test_tool_server_layer_consistency.py`,
`tests/mcp_servers/mdq/test_mdq_routing.py`, `tests/shared/test_tool_registry.py`,
`tests/shared/test_tool_safety_tiers.py`. No current ADR documents this as an approved
architectural decision — ADR-003's current Decision limits static `ToolRegistry` to
tests/expected-values/documentation-generation only.

## Reason for Change
An actively-running validation mechanism with no governing ADR is an undocumented architectural
decision. A future reader of ADR-003 could assume Drift validation is not part of the current
design and remove or bypass it without realizing `mcp_tool_discovery.py` still depends on it, or
could leave it un-reviewed indefinitely because no document tracks it as a live decision.

## Implementation Intent
Obtain an explicit decision from the architecture owner: either (a) formalize Routing Drift
validation as its own current architectural decision (a scoped Decision Detail/Invariant added
back to ADR-003, or a new ADR), or (b) deprecate and remove it because it is superseded by
`RuntimeToolRegistry` as the sole routing authority. This issue exists to force that decision
and track whichever follow-up work results — it does not implement either outcome itself.

## Target Files or Areas
- `scripts/shared/tool_routing_validation.py`
- `scripts/shared/tool_registry.py` (`validate_tool_names_match()`, `get_all_tool_names()`)
- `scripts/agent/services/mcp_tool_discovery.py` (caller)
- `docs/adr/ADR-003-runtime-tool-registry-routing-authority.md` (if formalized)

## Required Changes
- Confirm the current callers/tests of `tool_routing_validation.py` listed above are still accurate.
- Obtain an explicit architecture-owner decision: formalize or deprecate.
- If formalized: add a scoped Decision Detail and Invariant to ADR-003 (or a new ADR) describing Drift validation's exact current role and verification.
- If deprecated: remove the dead validation code and its tests, and update any Specification referencing it as current behavior.

## Constraints
- Do not change `RuntimeToolRegistry`'s routing authority — ADR-003's core Decision is unaffected by either outcome.
- Do not implement the removal or the ADR update in this issue without the architecture owner's recorded decision.

## Acceptance Criteria
- An explicit decision (formalize vs. deprecate) is recorded, either as an ADR update or a resolution note on this issue.
- If formalized, ADR-003 documents Drift validation as a current architectural decision with its own invariant and verification entry.
- If deprecated, `tool_routing_validation.py` and its now-dead callers/tests are removed, and no current document claims it as part of the routing authority.

## Testing Expectations
`uv run pytest` for the test files listed under Problem, once the direction is decided and implemented. Apply the standard validation sequence in `rules/toolchain.md`.

## Documentation Impact
ADR-003 gains or continues to omit a Decision Detail depending on the outcome. Check
`docs/04_mcp_03_02_tool-registry.md` and any Specification describing `tool_names` as
drift-validation input for consistency with whichever direction is chosen.

## Out of Scope
- Any other `ToolRegistry` responsibility (its tests/documentation-generation use is already covered by ADR-003 as-is).
- Redesigning `RuntimeToolRegistry` itself.

## Dependencies
Follows the 2026-08-31 ADR-013 → ADR-003 consolidation (see ADR-003's Out of Scope note on drift-validation removal).

## Resolution

**Decision**: Option (b) — deprecate and remove.

Routing Drift validation via `ToolRegistry.validate_tool_names_match()` is superseded by
`RuntimeToolRegistry` as the sole routing authority. Remove the following:

- `scripts/shared/tool_routing_validation.py`
- Callers/import of `validate_routing_against_live` from `scripts/agent/services/mcp_tool_discovery.py`
- Test files: `tests/agent/test_startup_routing_drift.py`,
  `tests/mcp_servers/cicd/test_tool_server_layer_consistency.py`,
  `tests/mcp_servers/mdq/test_mdq_routing.py`,
  `tests/shared/test_tool_registry.py`,
  `tests/shared/test_tool_safety_tiers.py`
- Any Specification document referencing `tool_names` as drift-validation input

After removal, verify no remaining code references these functions. Run `uv run pytest` for the
standard validation sequence in `rules/toolchain.md`.

## Status
Resolved

## Resolved at
2026-09-01

## AI Implementation Instruction
Do not remove or modify `tool_routing_validation.py`, `ToolRegistry.validate_tool_names_match()`,
or their tests without first confirming the architecture owner's formalize-vs-deprecate decision
recorded against this issue. If asked to implement this issue directly, stop and request that
decision before making any code change.
