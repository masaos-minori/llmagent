# Make runtime policy reload reversible and mandatory for execution

## Priority
Medium

## Summary
Runtime tool policy currently appears to mutate effective tool visibility cumulatively, so once a tool is disabled it cannot be re-enabled by a later reload, and routing may still resolve a tool that has been hidden from LLM presentation — this issue recomputes effective policy from immutable discovery data on every reload and enforces the same allowlist at both presentation and execution boundaries.

## Background
N/A: covered by Summary — this is a direct code-level finding in the runtime policy reload path, not derived from a prior design decision document.

## Problem
If effective policy is derived by mutating prior state rather than recomputing from a fixed discovery-time baseline plus the current policy, a tool disabled in one reload cannot become visible again in a later reload that intends to re-enable it. Separately, execution-path enforcement of `allowed_tools` may not be mandatory at every direct executor/invoker call site, so a tool hidden from the LLM could still be executable if called by name through a path that bypasses the preflight check.

## Reason for Change
Runtime policy currently mutates effective visibility cumulatively, making disabled tools impossible to re-enable. Routing can still resolve a hidden tool, so presentation policy and execution policy may diverge unless preflight enforcement is mandatory.

## Implementation Intent
Recompute effective policy from immutable discovery data on each reload and enforce the same allowlist at LLM presentation and execution boundaries.

## Target Files or Areas
- `scripts/shared/runtime_tool_registry.py`
- `scripts/agent/tool_policy.py`
- `scripts/shared/tool_executor.py`
- `scripts/agent/tool_runner.py`
- `tests/shared/test_runtime_tool_registry.py`
- `tests/agent/test_tool_policy.py`

## Required Changes
- Store immutable discovery-time LLM visibility separately from policy-derived visibility.
- Recompute effective visibility from the base value and the complete new policy on every reload.
- Enforce `allowed_tools` in the mandatory execution preflight path.
- Verify that no direct executor or invoker call bypasses preflight authorization.
- Apply policy updates through atomic registry replacement or equivalent synchronization.
- Add disable, direct-execution, reload, and re-enable tests.

## Constraints
N/A: none stated in source review.

## Acceptance Criteria
- A policy can disable and later re-enable an originally visible tool.
- A policy-disabled tool cannot be executed by name through any public path.
- Reload changes only documented policy fields.
- Concurrent readers observe either the old complete policy or the new complete policy.

## Testing Expectations
Add or update automated tests for every modified behavior and failure path (see Acceptance Criteria and Required Changes' test items). Run unit tests, integration tests, static analysis, and type checks.

## Documentation Impact
Update ADRs and the active known-issue inventory only after executable verification is available.

## Out of Scope
- Unrelated refactoring outside the design and implementation boundary described in this issue.

## Dependencies
Shares `scripts/shared/runtime_tool_registry.py` and `scripts/shared/tool_executor.py` with `mcpagent01` (startup publication) and `mcpagent05` (lifecycle/invocation gate unification) — coordinate ordering so the atomic-registry-replacement mechanism is not implemented divergently in more than one of these issues.

## Unresolved Questions
N/A: none.

## AI Implementation Instruction
Keep changes scoped to policy-reload recomputation and execution-preflight enforcement; do not rewrite unrelated registry construction logic beyond what atomic replacement requires. If `mcpagent01` or `mcpagent05` have already introduced an atomic-registry-replacement mechanism, reuse it rather than introducing a second one. Verify that logs and tool results do not expose credentials, payloads, raw response bodies, or sensitive configuration.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260914-103138
- **Related target files**: scripts/shared/runtime_tool_registry.py, scripts/agent/tool_policy.py, scripts/shared/tool_executor.py, scripts/agent/tool_runner.py, tests/shared/test_runtime_tool_registry.py, tests/agent/test_tool_policy.py
