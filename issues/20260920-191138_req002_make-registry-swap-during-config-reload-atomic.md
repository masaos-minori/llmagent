# Make Registry Swap During Config Reload Atomic

## Priority
Medium

## Summary
Ensure that the registry replacement during config reload is atomic — preventing intermediate states where some tools route through the old registry while others route through the new one, which could cause inconsistent routing decisions.

## Background
Config reload swaps the tool registry by replacing `self._tools` with a new dict built from `apply_policy()`. This is tracked as REQ-002 in `docs/00_governance_03_issue-and-uncertainty-management.md`. The current implementation in `RuntimeToolRegistry.apply_policy()` (line 175) directly assigns `self._tools = new_tools`, creating a non-atomic transition window.

## Problem
During config reload, the registry swap is not atomic. If the swap fails partway through (e.g., due to an exception after some tools have been processed), some tools may route through the old registry while others route through the new one. This inconsistency could lead to unauthorized tool access or incorrect fallback behavior.

## Reason for Change
A non-atomic registry swap introduces a race condition window where routing decisions are inconsistent across tools. Even brief exposure to mixed-state routing can cause security violations or incorrect tool resolution.

## Implementation Intent
Implement a two-phase commit pattern for registry replacement:
1. Build the complete new registry state without modifying the existing one
2. Atomically swap references once the new state is fully validated
3. Ensure rollback capability if validation fails mid-process

## Target Files or Areas
- `scripts/shared/runtime_tool_registry.py::apply_policy()` — registry swap logic
- `scripts/shared/config_loader.py` — config reload entry point
- `tests/` — test coverage for atomicity invariant

## Required Changes
- Implement a two-phase commit pattern: build new registry completely before swapping
- Add validation step between phase 1 (build) and phase 2 (swap) to ensure integrity
- Replace direct `self._tools = new_tools` assignment with an atomic swap operation
- Add unit tests verifying atomicity under concurrent access scenarios
- Update `docs/00_governance_03_issue-and-uncertainty-management.md` to resolve REQ-002 once implemented

## Constraints
- Must preserve existing public API behavior for valid visibility updates
- Cannot break backward compatibility with tools that legitimately update visibility within bounds
- The enforcement must not introduce blocking errors for normal operations; consider logging warnings for policy violations

## Acceptance Criteria
- [ ] After config reload, all tools use the same registry consistently
- [ ] No tool routes through both old and new registries simultaneously during reload
- [ ] Failed reload attempts leave the system in its original state (rollback works)
- [ ] Existing tests pass without modification
- [ ] New tests verify atomicity under concurrent access scenarios

## Testing Expectations
- Unit tests for `apply_policy()` verifying atomic swap under concurrent access
- Integration test simulating full config reload cycle with partial failures
- Regression tests confirming no breaking changes to existing routing behavior

## Documentation Impact
Update `docs/00_governance_03_issue-and-uncertainty-management.md` to mark REQ-002 as resolved. Document the two-phase commit pattern used for registry swap.

## Out of Scope
- Changing the underlying data structure (`dict[str, RuntimeTool]`)
- Adding new routing capabilities beyond atomic swap
- Implementing distributed lock mechanisms (single-process assumption holds)

## Dependencies
- REQ-001 (immutability of `llm_visibility_base`) — may benefit from similar immutability patterns
- CI-003 (config reload path testing) — overlapping test infrastructure

## Unresolved Questions
- Should the two-phase commit use a lock-based approach or a compare-and-swap mechanism?
- Are there any existing concurrency primitives in the codebase that should be reused?
- How should the system behave during a failed reload — immediate rollback or gradual recovery?

## AI Implementation Instruction
Focus on minimal changes to the config reload path only. Do not rewrite unrelated files. Preserve public behavior for valid visibility updates. Stop and report open questions if requirements are unclear. Do not implement out-of-scope items like new visibility fields or runtime hot-reload.
