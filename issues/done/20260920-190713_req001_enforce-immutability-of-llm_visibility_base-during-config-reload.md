# Enforce Immutability of `llm_visibility_base` During Config Reload

## Priority
High

## Summary
Prevent `llm_visibility_base` — an immutable discovery-time visibility field on `RuntimeTool` — from being overridden by config reload, which could unhide tools hidden from the LLM at discovery time and violate the security boundary established by REQ-001.

## Background
`llm_visibility_base` is defined as an immutable discovery-time visibility field on `RuntimeTool` (confirmed: 11 matches across `scripts/shared/runtime_tool.py`). The `apply_policy()` formula uses this field as the immutable base for visibility computation (confirmed: `scripts/shared/runtime_tool_registry.py` lines 166-167). However, no enforcement prevents config reload from overriding this field. This gap is tracked as REQ-001 in `docs/00_governance_03_issue-and-uncertainty-management.md`.

## Problem
A tool hidden from the LLM at discovery time could become visible again through config reload, violating the security boundary established by REQ-001. The current code reads `llm_visibility_base` as the starting point for visibility computation but allows the config reload path to modify tool visibility without respecting this constraint.

## Reason for Change
This is a security-sensitive design gap: a hidden tool becoming visible after config reload bypasses the intentional discovery-time restriction. Without enforcement, operators can inadvertently expose tools that were deliberately hidden at startup.

## Implementation Intent
Add immutability enforcement for `llm_visibility_base` in the config reload path. The fix should ensure that any visibility modification during reload respects the original `llm_visibility_base` value — either by rejecting overrides or by computing the new visibility relative to the original base rather than replacing it entirely.

## Target Files or Areas
- `scripts/shared/runtime_tool.py` — `llm_visibility_base` definition
- `scripts/shared/runtime_tool_registry.py::apply_policy()` — visibility computation logic
- `scripts/shared/config_loader.py` — config reload entry point
- `tests/` — test coverage for the invariant

## Required Changes
- Add validation in `apply_policy()` or its callers to reject attempts to set visibility values that contradict `llm_visibility_base`
- Ensure the config reload path computes visibility as a delta from `llm_visibility_base` rather than replacing it outright
- Add unit tests asserting that hidden tools remain hidden after config reload
- Update `docs/00_governance_03_issue-and-uncertainty-management.md` to resolve REQ-001 once implemented

## Constraints
- Must preserve existing public API behavior for valid visibility updates
- Cannot break backward compatibility with tools that legitimately update visibility within bounds
- The enforcement must not introduce blocking errors for normal operations; consider logging warnings for policy violations

## Acceptance Criteria
- [ ] After config reload, a tool with `llm_visibility_base=False` cannot have its visibility set to `True` via config
- [ ] A tool with `llm_visibility_base=True` retains visibility `True` after reload unless explicitly set to `False` within bounds
- [ ] Attempting to override `llm_visibility_base` logs a warning and rejects the invalid visibility change
- [ ] Existing tests pass without modification
- [ ] New tests cover the three scenarios above

## Testing Expectations
- Unit tests for `apply_policy()` verifying immutability enforcement under each scenario
- Integration test simulating full config reload cycle with hidden tools
- Regression tests confirming no breaking changes to existing visibility update paths

## Documentation Impact
Update `docs/00_governance_03_issue-and-uncertainty-management.md` to mark REQ-001 as resolved. Consider documenting the immutability guarantee in `scripts/shared/runtime_tool.py`'s docstring.

## Out of Scope
- Modifying `llm_visibility_base` itself (it remains immutable by design)
- Adding new visibility fields or changing the visibility model
- Implementing runtime hot-reload of visibility policies outside of config reload

## Dependencies
- REQ-002 (atomic registry swap invariant) — may benefit from similar immutability patterns
- CI-003 (config reload path testing) — overlapping test infrastructure

## Unresolved Questions
- Should the enforcement raise an exception or log a warning and skip the invalid update?
- Does the fix need to handle edge cases where multiple tools share the same visibility state?
- Is there a need for audit logging of all visibility changes during reload?

## AI Implementation Instruction
Focus on minimal changes to the config reload path only. Do not rewrite unrelated files. Preserve public behavior for valid visibility updates. Stop and report open questions if requirements are unclear. Do not implement out-of-scope items like new visibility fields or runtime hot-reload.
