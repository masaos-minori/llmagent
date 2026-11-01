# Audit drops denied gateway tool calls

## Priority
Medium

## Summary
`audit_tool_exec()` silently returns without writing a structured audit event whenever both `mcp_request_id` and `source` are falsy. `RepositoryGateway._denied_result()` builds its denial result with empty `request_id` and `source`, so every write/delete/API-write call denied at the gateway by the policy preflight produces no entry in the structured audit log. Narrow the early-return guard so a denial decision is always recorded.

## Background
Found during an adversarial code review (`python-code-review` skill) of the REPL's tool-execution/approval-gating and audit subsystem (`scripts/agent/tool_audit.py`, `scripts/agent/repository_gateway.py`).

## Problem
`scripts/agent/tool_audit.py::audit_tool_exec()` starts with `if not mcp_request_id and not source: return`. `scripts/agent/repository_gateway.py::_denied_result()` builds a `ToolCallResult` with `request_id=""`, `server_key=""` and `error_type="denied"`, keeping the default `source=""`. `_gate_write()` returns it when `check_preflight()` raises `PolicyViolationError`. `tool_runner.execute_one_tool_call()` then calls `audit_tool_exec(..., source=result.source)` with both values falsy, so no structured audit event is written. The only trace is the free-text `logger.warning("gateway.policy_denied ...")` line in the ordinary application log. Note: the earlier second denial path (`ctx.turn.pending_approval_id`) no longer exists; the approval-recovery code that set it was removed.

## Reason for Change
An attempted write that the gateway policy preflight denies (a blocked path or command) is the kind of security-relevant event the audit trail exists to capture. It currently leaves no record in the `audit_logger` pipeline.

## Implementation Intent
Narrow the early-return guard so it distinguishes "nothing happened, don't bother logging" from "a policy decision happened and must be recorded." A denial (`error_type="denied"`) must always produce an audit record regardless of whether `mcp_request_id`/`source` are populated.

## Target Files or Areas
- `scripts/agent/tool_audit.py` (`audit_tool_exec()`)
- `scripts/agent/repository_gateway.py` (`_denied_result()`, `_gate_write()`)

## Required Changes
- Change `audit_tool_exec()`'s early-return condition so a result with `error_type="denied"` is always logged, even when `mcp_request_id` and `source` are both empty.
- Add a test asserting that a `RepositoryGateway` write call denied by `check_preflight()` produces a structured audit event.

## Constraints
- Do not change the audit event schema or fields beyond ensuring a denial is recorded.
- Do not remove the existing free-text `gateway.policy_denied` log line; add the structured record alongside it.
- Coordinate with `issues/20261003-180336_assertaudit001_audit-assert-risks-post-execution-crash.md`: once a denial passes the guard, it reaches the `assert ctx.workflow.workflow_id` in the same function.

## Acceptance Criteria
- A write/delete/API-write call denied via `check_preflight()` produces a structured audit event with `error_type="denied"`.
- The early-return behavior for genuinely no-op cases (if any remain after narrowing) is preserved.

## Testing Expectations
Unit test driving the preflight denial path in `RepositoryGateway` and asserting the audit log receives a record. Run `tests/agent/test_tool_audit.py` and `tests/agent/test_repository_gateway.py` after the change.

## Documentation Impact
N/A: no operator-facing documentation describes this specific audit-logging gap today.

## Out of Scope
- `tool_approval.check_approval()`'s own gate.
- Any change to how workflow approval state is set or cleared.

## Dependencies
Shares `audit_tool_exec` with `issues/20261003-180336_assertaudit001_audit-assert-risks-post-execution-crash.md` and `issues/20261101-073823_idemaudit001_audit-idempotency-key-mismatch.md`, and `implementations/20261030-102825_05_scripts_agent_tool_audit.py.md` also edits it; the function now also emits `dedup_state` and `execution_snapshot_json`; the early-return guard is unchanged. Coordinate the order of changes.

## Unresolved Questions
N/A: none — the early-return condition and `_denied_result()`'s `source=""` default were both confirmed by reading `tool_audit.py` and `repository_gateway.py` directly.

## AI Implementation Instruction
Narrow the guard in `audit_tool_exec()` precisely; do not simply remove it, since it may still serve a purpose for genuinely empty no-op calls. Add the regression test described above before considering this done. Do not touch `tool_approval.check_approval()`.

## Traceability
- **Workflow phase**: python-code-review -> issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261003-180330
- **Related target files**: scripts/agent/tool_audit.py, scripts/agent/repository_gateway.py
