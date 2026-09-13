# RepositoryGateway._gate_write() skips preflight when approval is pending

## Priority
High

## Summary
Fix `RepositoryGateway._gate_write()` to reject write operations when approval is pending instead of skipping the policy preflight check and executing them anyway, which violates the security boundary.

## Background
`RepositoryGateway` is documented as a "single enforcement boundary for all repository write/delete/API-write operations" (repository_gateway.py:47). Its `_gate_write` method enforces policy via `check_preflight()` before execution. However, when `ctx.turn.pending_approval_id is not None`, the method skips the preflight check and executes the tool call directly.

Evidence:
- `repository_gateway.py:103-108`: Skips preflight and executes when `pending_approval_id is not None`
- `repository_gateway.py:98-100`: Docstring says "Approval is expected to have already been granted by the caller's batch-level gate"
- `orchestrator.py:187-188`: Orchestrator blocks turn processing when `ctx.workflow.approval_pending` is True
- `workflow_engine_adapter.py:339-340`: Both `ctx.turn.pending_approval_id` and `ctx.workflow.approval_pending` are set together when approval is required

## Problem
The code at line 103-108 contradicts the documented precondition: "Approval is expected to have already been granted by the caller's batch-level gate." When approval is pending (not granted), the tool call should NOT be executed.

While the orchestrator blocks turn processing at line 188 when approval is pending (so no tool calls reach `RepositoryGateway.execute()` under normal circumstances), the code at line 103-108 is reachable in edge cases:

1. **Caller bypass**: A caller that invokes `RepositoryGateway.execute()` directly without going through the orchestrator's approval gate
2. **Race condition**: If the orchestrator's blocking check and the gateway's approval check are not synchronized
3. **Future refactoring**: If someone later modifies the orchestrator to not block when approval is pending

In any of these cases, a write operation could execute without both user approval AND policy compliance — violating two layers of the security boundary.

Additionally, the comment "Skip gateway preflight when workflow approval is active" is misleading. "Active" suggests the approval process is in effect, but `pending_approval_id is not None` means the user has NOT yet approved. The tool call should be rejected, not executed.

## Reason for Change
Allowing write operations to execute without policy preflight when approval is pending creates a security gap. Even though the orchestrator currently prevents this path, the gateway should enforce its own approval check independently — defense in depth.

## Implementation Intent
Change the behavior when `pending_approval_id is not None` from "execute without preflight" to "reject with a denial reason." The gateway should enforce its own approval check, not rely on the caller to do it. This aligns with the documented precondition and ensures the security boundary is maintained even if callers bypass the orchestrator.

## Target Files or Areas
- `/home/sugimoto/llmagent/scripts/agent/repository_gateway.py`

## Required Changes
- Replace the early-return-with-execute pattern at line 103-108 with an early-return-with-denial pattern
- Return `_denied_result("Approval pending — use /approve or /reject to grant access.")` instead of `await self._executor.execute(tool_name, args)`
- Update the comment to clarify that approval must be granted before execution
- Consider adding a similar check in `execute()` for read-only tools (though they don't require approval)

## Constraints
- Must preserve existing error response format (`_denied_result`)
- Must not change the public API surface
- Must handle the case where approval is granted between the orchestrator's check and the gateway's check (unlikely but possible)

## Acceptance Criteria
- Write operations are rejected when approval is pending, not executed
- Denial message clearly indicates the user must approve/reject via `/approve` or `/reject`
- No regressions in normal tool execution flow
- Gateway enforces its own approval check independently of the orchestrator

## Testing Expectations
- Unit test verifying write operations are rejected when `pending_approval_id is not None`
- Unit test verifying write operations are allowed when `pending_approval_id is None`
- Integration test covering the full approval flow (request → approve → execute)
- Regression test for read-only tools (should not be affected)

## Documentation Impact
Update docstrings for `_gate_write` to clarify that approval must be granted before execution, not just "expected to have been granted."

## Out of Scope
- Adding new approval mechanisms
- Changing the approval flow in the orchestrator
- Modifying the approval gate in `tool_runner.py`

## Dependencies
N/A: none

## Unresolved Questions
- Should the denial message include the pending approval ID for debugging purposes?
- Is there any legitimate use case for executing a tool while approval is pending?
- Should the gateway also check `ctx.workflow.approval_pending` in addition to `ctx.turn.pending_approval_id`?

## AI Implementation Instruction
Do not add new functionality. Simply change the early-return at line 103-108 from executing the tool to denying it with a clear message. Preserve the existing `_denied_result` format. Verify no test code relies on the current behavior of executing tools during pending approval.

## Traceability
- **Workflow phase**: python-code-review + issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260913-172700
- **Related target files**: scripts/agent/repository_gateway.py
