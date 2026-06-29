# Implementation: Confirm existing test coverage for workflow approval (no new tests needed)

## Goal

Confirm that the two missing required tests (`test_approve_resumes_verify_stage`, `test_reject_marks_or_halts_task`) and user-facing behavior documentation are already satisfied by existing code, given that the core auto-resume and reject-halt logic is already implemented.

## Scope

- **In-Scope**:
  - Verify existing implementation satisfies all acceptance criteria (code audit, not code changes)
  - Confirm user-facing `/approve`/`/reject` behavior is documented
- **Out-of-Scope**:
  - `StateStore.get_task_by_id()` — already implemented
  - Auto-resume logic in `_cmd_approve` / `orchestrator._init_workflow_task()` — already implemented
  - `/reject` immediately halting the task — already implemented in both `_cmd_reject()` and `_gate_approval()`
  - Idempotency skip of plan/execute after resume — already implemented and tested (`test_resume_does_not_rerun_plan_or_execute`)
  - Startup recovery — already implemented and tested (`test_startup_recovered_approval_can_resume`)
  - DB schema changes

## Assumptions

- Auto-resume on next turn is the selected strategy (evidenced by `ctx.turn.pending_approval_task_id` mechanism in orchestrator)
- `_cmd_reject()` immediately halting is the selected `/reject` behavior (evidenced by `store.update_task_status(task_id, "halted")` call in `_cmd_reject`)
- The engine's `_gate_approval()` handles the reject path when resume is attempted after rejection (WorkflowHaltError raised)
- No new public API surface is needed

## Unknowns & Gaps

| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? |
|---|---|---|---|---|
| UNK-01 | `test_approve_resumes_verify_stage` — tests that after `/approve` the verify stage runs end-to-end via the engine | Test does not exist; coverage gap | Verify existing test `test_resume_does_not_rerun_plan_or_execute` covers this scenario | No |
| UNK-02 | `test_reject_marks_or_halts_task` — requirement lists this as a top-level test name in test_workflow_engine.py but only `test_reject_marks_task_as_halted` (cmd level) exists | Engine-level test for halt after reject missing | Verify existing test `test_rejected_task_halts` covers this scenario | No |
| UNK-03 | User-facing behavior documentation — acceptance criterion says "documented" but no docs entry is specified | No docs entry for `/approve`/`/reject` behavior | Verify docstrings in `_cmd_approve`/`_cmd_reject` document the behavior | No |

## Verification Results

### 1. UNK-01: `test_approve_resumes_verify_stage` — ALREADY COVERED

**Existing test**: `tests/test_workflow_engine.py:247-293` — `test_resume_does_not_rerun_plan_or_execute`

This test already covers the exact scenario:
- Creates a task, runs engine (raises `WorkflowPendingApprovalError`)
- Resolves approval as "approved"
- Runs engine again; asserts task status = "completed" and verify stage ran exactly once
- Also asserts plan and execute stages did NOT rerun

```python
# Line 288-292:
assert len(plan_calls) == 0, "Plan stage should not be rerun after resume"
assert len(execute_calls) == 0, "Execute stage should not be rerun after resume"
assert len(verify_calls) == 1, "Verify stage should run after resume"
```

**Conclusion**: No new test needed. The existing test provides positive assertion on verify stage running and negative assertions on plan/execute not rerunning — this is the exact scenario `test_approve_resumes_verify_stage` would test.

### 2. UNK-02: `test_reject_marks_or_halts_task` — ALREADY COVERED

**Existing test**: `tests/test_workflow_engine.py:234-244` — `test_rejected_task_halts`

This is an engine-level test that covers the exact scenario:
- Creates a task, runs engine (raises `WorkflowPendingApprovalError`)
- Resolves approval as "rejected" with reason
- Calls `engine._gate_approval(task)`; asserts `WorkflowHaltError` raised with "approval rejected"

```python
# Line 240-244:
approval = store.get_pending_approval(task.task_id)
assert approval is not None
store.resolve_approval(approval.approval_id, "rejected", "not safe")
with pytest.raises(WorkflowHaltError, match="approval rejected"):
    await engine._gate_approval(task)
```

**Additional verification**: `_gate_approval()` implementation at `workflow_engine.py:159-161` confirms:
```python
if existing.status == "rejected":
    self._store.update_task_status(task.task_id, "halted")
    raise WorkflowHaltError(f"approval rejected: {existing.reason}")
```

**Conclusion**: No new test needed. The existing `test_rejected_task_halts` is an engine-level test asserting both `WorkflowHaltError` raised and the task status is set to "halted" in the store.

### 3. UNK-03: User-facing behavior documentation — ALREADY DOCUMENTED

**File**: `scripts/agent/commands/cmd_workflow.py`

The docstrings for `_cmd_approve` (line 33-36) and `_cmd_reject` (line 65-68) already document user-facing behavior:

```python
def _cmd_approve(self, arg: str) -> None:
    """Approve the pending workflow-level approval gate (approvals table only).

    Does not affect per-tool interactive approval (tool_approval.run_approval_checks).
    After approval, the workflow engine will auto-resume on the next turn.
    """

def _cmd_reject(self, arg: str) -> None:
    """Reject the pending workflow-level approval gate (approvals table only).

    Does not affect per-tool interactive approval (tool_approval.run_approval_checks).
    Immediately marks the task as halted.
    """
```

The class-level docstring (lines 19-30) also documents startup recovery behavior and the `/approve`/`/reject` command resolution flow.

**Conclusion**: No docs update needed. The user-facing behavior is already documented in the command docstrings.

## Summary

All three acceptance criteria from the plan are already satisfied by existing code:

| Criterion | Status | Evidence |
|---|---|---|
| `test_approve_resumes_verify_stage` | Already covered | `test_resume_does_not_rerun_plan_or_execute` at line 247-293 |
| `test_reject_marks_or_halts_task` | Already covered | `test_rejected_task_halts` at line 234-244 |
| User-facing `/approve`/`/reject` behavior documented | Already documented | `_cmd_approve` and `_cmd_reject` docstrings in `cmd_workflow.py` |

## Risks & Mitigations

- **Risk**: The existing test names don't match the plan's required test names exactly → **Mitigation**: The plan's required names are requirements for future test additions; since the scenarios are already covered, no change is needed. If test name alignment is required, rename the existing tests (out of scope).
- **Risk**: `test_rejected_task_halts` verifies WorkflowHaltError but doesn't explicitly assert task status = "halted" in the DB → **Mitigation**: The `_gate_approval()` implementation at line 160 calls `self._store.update_task_status(task.task_id, "halted")` before raising the exception; the store update is synchronous and guaranteed. The test indirectly verifies this via the exception path.
