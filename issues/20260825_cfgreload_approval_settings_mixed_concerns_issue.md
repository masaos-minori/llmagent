# `_reload_approval_settings()` mixes approval, tool-allowlist, memory, and security concerns

## Priority
Medium

## Summary
`_reload_approval_settings()` calls `_reload_approval_config()` but also directly handles `allowed_tools`, `memory_retention_days`, `memory_local_only`, and `security_profile` / `security_lockdown_enabled`. The function name implies "approval" only, so unrelated concerns are hidden inside an approval-named function, reducing readability and discoverability.

## Background
N/A: covered by Summary.

## Problem
Verified: `scripts/agent/services/config_reload.py`'s `_reload_approval_settings()` (starting at line 446) calls `self._reload_approval_config(ctx, new_cfg)` and then, in the same function body, also updates `ctx.cfg.tool.allowed_tools`, `ctx.cfg.memory.memory_retention_days`, `ctx.cfg.memory.memory_local_only`, and (via a nested `try`/import) `ctx.cfg.mcp.security_profile` / `security_lockdown_enabled`. These four groups of fields belong to four different config domains (tool, memory, memory, mcp/security) that have nothing to do with `ApprovalConfig`.

## Reason for Change
A reader looking for where `allowed_tools` or `security_profile` is reloaded would not think to look inside a function named `_reload_approval_settings`. This reduces maintainability and increases the risk that a future change to one concern accidentally affects another due to shared code.

## Implementation Intent
Extract cohesive helpers so each function name matches its actual responsibility:
- `_reload_approval_config()` — approval fields only (unchanged scope, already correctly named).
- `_reload_tool_allowlist()` — `allowed_tools`.
- `_reload_memory_runtime()` — `memory_retention_days`, `memory_local_only`.
- `_reload_security_profile()` — `security_profile`, `security_lockdown_enabled`.
Call each explicitly from `apply_config_dict()` in place of the current single `_reload_approval_settings()` call. This is a pure refactor — no behavior change.

## Target Files or Areas
- `scripts/agent/services/config_reload.py`

## Required Changes
- Split `_reload_approval_settings()` into the four helpers listed above.
- Update `apply_config_dict()` to call all four helpers explicitly instead of one combined function.
- Remove `_reload_approval_settings()` once its logic has been fully redistributed (or keep it only if it turns out to still serve as a thin dispatcher — decide during implementation based on what reads best).

## Constraints
- Behavior must be unchanged — this is a pure refactor. Field update order relative to other `apply_config_dict()` steps must be preserved unless verified to be order-independent.

## Acceptance Criteria
- [ ] Each new helper handles exactly one, name-consistent concern.
- [ ] Behavior is unchanged for all four field groups (verified by existing tests passing unmodified, or with only mechanical updates for renamed internals).

## Testing Expectations
- Existing `config_reload` tests covering `allowed_tools`, `memory_retention_days`, `memory_local_only`, `security_profile`, `security_lockdown_enabled`, and the approval fields must pass unchanged.
- No new test cases are required beyond confirming the refactor preserves behavior (a pure refactor issue does not need new coverage unless the split reveals an untested field).

## Documentation Impact
N/A: internal code organization only, not part of any documented public behavior.

## Out of Scope
- Changing which fields are hot-reloadable.
- Changing the field update logic itself (only the function boundaries/names change).

## Dependencies
- Coordinate ordering with `issues/20260825_cfgreload_gitops_push_blocked_not_reloadable_issue.md` (adds a field to `_reload_approval_config()`) if both land in the same window — that issue's change is inside `_reload_approval_config()`, which this issue does not rename or restructure, so the two can land in either order without conflict.

## Unresolved Questions
- Whether `_reload_approval_settings()` should be deleted entirely or retained as a thin wrapper calling the four new helpers in sequence (for callers that may still expect a single entry point). Confirm by checking whether anything outside `apply_config_dict()` calls `_reload_approval_settings()` directly.

## AI Implementation Instruction
This is a pure refactor — preserve exact behavior and field update order unless you can positively confirm order independence. Do not use this issue as an opportunity to also fix `gitops_push_blocked` (tracked separately) or change which fields are validated — scope is limited to function boundaries and naming.
