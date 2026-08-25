# `gitops_push_blocked` is not updated by /reload

## Priority
High

## Summary
`ApprovalConfig.gitops_push_blocked` exists and globally blocks GitHub write operations, but `_reload_approval_config()` does not update it. Operators cannot change this security-relevant flag via `/reload`, creating a divergence between the config an operator believes is active and what is actually enforced.

## Background
N/A: covered by Summary.

## Problem
Verified: `scripts/agent/config_dataclasses.py:383` defines `gitops_push_blocked: bool = False` on `ApprovalConfig`. `scripts/agent/services/config_reload.py:_reload_approval_config()` (lines 405-430) updates nine other `ApprovalConfig` fields (`approval_risk_rules`, `approval_protected_paths`, `approval_high_risk_branches`, `approval_shell_safe_prefixes`, `approval_resource_keys`, `approval_dry_run_tools`, `tool_safety_tiers`, `allowed_root`, `approval_github_allowed_repos`) but does not reference `gitops_push_blocked` anywhere in the function.

## Reason for Change
Since `gitops_push_blocked` gates all GitHub write operations, an operator who intends to flip it via `/reload` gets no error and no effect — the flag silently stays at whatever value was set at startup. This is a security-relevant configuration gap.

## Implementation Intent
Add `gitops_push_blocked` to the set of fields `_reload_approval_config()` updates, following the same `if (vb := _get_bool(new_cfg, "...")) is not None:` pattern already used for the function's other boolean-shaped fields.

## Target Files or Areas
- `scripts/agent/services/config_reload.py`

## Required Changes
- In `_reload_approval_config()`, add:
  ```
  if (vb := _get_bool(new_cfg, "gitops_push_blocked")) is not None:
      approval.gitops_push_blocked = vb
  ```

## Constraints
- Do not change the semantics of `gitops_push_blocked` itself (what it blocks, its default) — only make it reloadable.

## Acceptance Criteria
- [ ] `/reload` updates `ctx.cfg.approval.gitops_push_blocked` when the field is present in the reload payload.
- [ ] The change is visible in the reload "applied" report.

## Testing Expectations
- Unit test: reload with `gitops_push_blocked = true` results in `ctx.cfg.approval.gitops_push_blocked == True`.
- Regression: existing `_reload_approval_config()` tests for the other nine fields continue to pass unchanged.

## Documentation Impact
If `docs/05_agent_07_06_cli-and-commands-hot-reload.md` (or the equivalent hot-reload scope doc) lists which `ApprovalConfig` fields are hot-reloadable, add `gitops_push_blocked` to that list.

## Out of Scope
- Changing GitHub write-gating semantics or default value.
- Any other `ApprovalConfig` field not already listed here.

## Dependencies
- Consider bundling with the validator re-execution issue (`issues/20260825_cfgreload_missing_validator_reexecution_issue.md`) so the reloaded boolean value is validated consistently with startup, if that issue lands first — not a hard prerequisite, since `gitops_push_blocked` has no existing `validate_*` function to reuse.

## Unresolved Questions
- N/A: none.

## AI Implementation Instruction
This is a small, well-scoped, single-line addition — do not expand scope to other `ApprovalConfig` fields not explicitly listed in Required Changes. Follow the exact existing pattern used by the function's other boolean fields for consistency.
