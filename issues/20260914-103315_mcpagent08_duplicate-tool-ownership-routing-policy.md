# Unify duplicate-tool ownership detection and routing policy

## Priority
Medium

## Summary
Production discovery excludes duplicate tool names and treats them as fatal, but `build_discovery_map()` (confirmed at `scripts/shared/route_resolver.py` line 33, referenced by `tests/shared/test_tool_registry.py`, `tests/shared/test_routing_duplicate_ownership.py`, and `tests/shared/test_route_resolver.py`) and its tests may still preserve first-wins routing for duplicates, representing the same ownership invariant with disagreeing behavior; this issue unifies both under one duplicate-ownership policy.

## Background
N/A: covered by Summary — this is a direct code-level finding comparing `build_discovery_map()`'s behavior against production discovery's duplicate-exclusion policy.

## Problem
`build_discovery_map()` in `scripts/shared/route_resolver.py` returns both a route map and a set of detected duplicates (per its existing tests), but it is not confirmed whether the returned route map itself excludes the duplicated tool from routing or silently keeps a first-registered owner — if the latter, this diverges from production discovery's policy that a duplicate tool name is a fatal startup finding.

## Reason for Change
Production discovery excludes duplicate tool names and marks them fatal, while an older utility and its tests preserve first-wins routing. Both implementations represent the same ownership invariant and must not disagree.

## Implementation Intent
Maintain one duplicate-ownership policy: a duplicated tool is excluded from routing and causes a fatal startup finding.

## Target Files or Areas
- `scripts/shared/route_resolver.py`
- `scripts/agent/services/mcp_tool_discovery.py`
- `tests/shared/test_route_resolver.py`
- `tests/agent/services/test_mcp_tool_discovery.py`
- `tests/shared/test_tool_registry.py` (Confirmed by repository search: references `build_discovery_map()` and its duplicate-warning behavior — not cited in source review, added here as directly relevant)
- `tests/shared/test_routing_duplicate_ownership.py` (Confirmed by repository search: dedicated duplicate-ownership test file for `build_discovery_map()` — not cited in source review, added here as directly relevant)

## Required Changes
- Find every reference to `build_discovery_map()`.
- Remove the function and its tests if it is obsolete.
- If it remains necessary for diagnostics, change it so duplicate tools are absent from the routing map.
- Centralize duplicate detection in the discovery service or a shared helper with one policy.
- Update tests to reject first-wins behavior.

## Constraints
N/A: none stated in source review.

## Acceptance Criteria
- No production or test utility silently selects the first owner of a duplicate tool.
- Duplicate tools are excluded from routable results.
- One test suite defines and verifies the duplicate-ownership policy.

## Testing Expectations
Add or update automated tests for every modified behavior and failure path (see Acceptance Criteria and Required Changes' test items); update `tests/shared/test_tool_registry.py` and `tests/shared/test_routing_duplicate_ownership.py` (found during repository verification, not in the original source review) if they assert first-wins behavior. Run unit tests, integration tests, static analysis, and type checks.

## Documentation Impact
Update ADRs and the active known-issue inventory only after executable verification is available.

## Out of Scope
- Unrelated refactoring outside the design and implementation boundary described in this issue.

## Dependencies
Coordinates with `mcpagent01` (MCP server availability/startup publication), which also requires "duplicate tool ownership always prevents startup" as one of its Acceptance Criteria — implement together or reconcile the duplicate-detection policy if implemented separately.

## Unresolved Questions
Whether `build_discovery_map()`'s returned route map currently already excludes duplicates (only the diagnostic duplicate-set differs) or whether it genuinely returns a first-wins route map — resolve by reading the function during implementation rather than assuming either outcome. Non-blocking.

## AI Implementation Instruction
Keep changes scoped to duplicate-tool detection/routing in `route_resolver.py` and its direct callers; do not rewrite unrelated discovery logic. Read `build_discovery_map()`'s current implementation first to confirm whether the Unresolved Question's premise (first-wins routing) actually holds before deciding whether to remove or fix the function. Coordinate with `mcpagent01` if implemented in the same session. Verify that logs and tool results do not expose credentials, payloads, raw response bodies, or sensitive configuration.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260914-103315
- **Related target files**: scripts/shared/route_resolver.py, scripts/agent/services/mcp_tool_discovery.py, tests/shared/test_route_resolver.py, tests/agent/services/test_mcp_tool_discovery.py, tests/shared/test_tool_registry.py, tests/shared/test_routing_duplicate_ownership.py
