## Goal

Fix `RepositoryGateway._gate_write()` to reject write operations when approval is pending
instead of executing them without policy preflight, restoring the security boundary. Per
REQ-001, REQ-002, REQ-004.

## Scope

- Modify exactly one method in `scripts/agent/repository_gateway.py`:
  `_gate_write()` early-return logic at lines 103-108
- Change behavior from "execute-without-preflight" to "deny-with-clear-message"
  when `ctx.turn.pending_approval_id is not None`
- Update docstring to clarify that approval must be granted before execution

## Assumptions

- The `_denied_result` helper function can be reused for the denial response
- The existing error response format is sufficient for conveying approval pending status
- No legitimate use case exists for executing a tool while approval is pending
- The Plan's frozen `Implementation Target Files` section accurately reflects scope

## Design decisions

- Replace the early-return-with-execute pattern at lines 103-108 with an
  early-return-with-denial pattern using `_denied_result()`
- Include the pending approval ID in the denial message for debugging purposes
- Update the docstring to clarify that approval must be granted before execution

## Alternatives considered

- Adding a dual-check (`ctx.workflow.approval_pending` AND `ctx.turn.pending_approval_id`):
  rejected — defense in depth means each component should enforce its own checks;
  checking both would add complexity without clear benefit
- Using a different error message format: rejected — `_denied_result` already provides
  consistent formatting across the codebase

## Implementation

### Target file

`scripts/agent/repository_gateway.py`

### Procedure

1. **Replace the early-return-with-execute pattern** at lines 103-108:
   - Before: execute the tool call directly when `pending_approval_id is not None`
   - After: deny the operation with a clear message indicating approval is needed

2. **Update the docstring** to clarify that approval must be granted before execution

### Method

1. Read `repository_gateway.py` to locate the exact code at lines 103-108
2. Replace the early-return block with denial logic
3. Update the docstring comment about approval expectations
4. Verify no remaining references to the old behavior

### Details

**Step 1 — Replace the early-return block:**

Before (lines 102-108):
```python
# Skip gateway preflight when workflow approval is active
if ctx.turn.pending_approval_id is not None:
    logger.debug(
        "Skipping gateway preflight: workflow approval pending (id=%s)",
        ctx.turn.pending_approval_id,
    )
    return await self._executor.execute(tool_name, args)
```

After:
```python
# Reject write operations when approval is pending
if ctx.turn.pending_approval_id is not None:
    logger.warning(
        "gateway.write_denied tool=%r reason=pending_approval id=%s",
        tool_name,
        ctx.turn.pending_approval_id,
    )
    return _denied_result(
        f"Approval pending — use /approve or /reject to grant access."
    )
```

Key changes:
- Comment updated from "Skip gateway preflight" to "Reject write operations when approval is pending"
- Log level changed from `debug` to `warning` (security-relevant event)
- Log message changed from "Skipping gateway preflight" to "gateway.write_denied"
- Return value changed from `await self._executor.execute(...)` to `_denied_result(...)`
- Denial message includes actionable instruction referencing `/approve` or `/reject` commands

**Step 2 — Update the docstring:**

Before:
```python
"""Enforce policy, execute, audit.

Approval is expected to have already been granted by the caller's
batch-level gate (tool_runner.execute_all_tool_calls()'s
_run_approval_gate()); this method does not prompt.
"""
```

After:
```python
"""Enforce policy, execute, audit.

Approval must be granted before execution. When ctx.turn.pending_approval_id
is not None, write operations are denied until the user explicitly approves
via /approve or /reject. This method does not prompt.
"""
```

## Compatibility considerations

- Breaking change for callers relying on the current buggy behavior (executing tools during pending approval)
- This is intentional — the current behavior violates the documented precondition
- Defense in depth: orchestrator already blocks turn processing when `approval_pending`, so production impact is minimal

## Security considerations

- This fix closes a security gap where write operations could bypass policy preflight
- The denial message must clearly indicate the user action required (/approve or /reject)
- Logging level changed to warning to ensure visibility of denied operations

## Rollback considerations

- Revert the two edit steps above to restore original behavior
- No data loss risk — only behavioral change in the gateway

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/repository_gateway.py | Unit test: mock ctx.turn.pending_approval_id = "test-id", verify _denied_result returned | uv run pytest tests/agent/test_repository_gateway.py::test_gate_write_rejects_when_approval_pending | Test passes, denial result returned |
| scripts/agent/repository_gateway.py | Unit test: mock ctx.turn.pending_approval_id = None, verify normal execution | uv run pytest tests/agent/test_repository_gateway.py::test_gate_write_allows_when_no_pending_approval | Test passes, normal execution occurs |

## Completion criteria

- [ ] Early-return block replaced with denial logic at lines 103-108
- [ ] Docstring updated to clarify approval must be granted before execution
- [ ] Denial message includes actionable instruction (/approve or /reject)
- [ ] Pending approval ID included in denial message for debugging
- [ ] Log level changed to warning for security-relevant events

## Out of scope

- Adding new approval mechanisms
- Changing orchestrator approval flow
- Modifying tool_runner.py approval gate
- Adding unit tests (separate row)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: existing tests cover regression |
| 3 | Run the validation sequence (rules/toolchain.md) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | Docstring update included in Phase 1 |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001, REQ-002, REQ-004
- **Source issue**: issues/20260913-172700_repository_gateway_preflight_skip.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260913-224241_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260914-115040
- **Related target files**: scripts/agent/repository_gateway.py
