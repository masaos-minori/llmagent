# Implementation: tests/test_cmd_workflow_approval.py — Approval fail-closed tests

## Goal

Test all pending-count cases: zero, one, multiple; explicit ID vs no ID; audit event fields; restart recovery.

## Scope

**In**: Unit tests for `_cmd_approve` and `_cmd_reject`. Tests use in-memory workflow.sqlite fixtures.

**Out**: Source file changes.

## Assumptions

1. Tests use a minimal `StateStore` backed by in-memory SQLite.
2. `CommandRegistry` requires `AgentContext` — use a lightweight mock.
3. `_parse_approval_arg()` can be tested independently.

## Implementation

### Target file
`tests/test_cmd_workflow_approval.py`

### Procedure
Write parameterized pytest tests for each acceptance criterion.

### Method

```python
# Test: zero pending → clear error message
def test_approve_no_pending(mock_ctx, in_memory_workflow_db):
    registry = make_registry(mock_ctx)
    registry._cmd_approve("")
    assert "No pending approval" in mock_ctx.out.last_error

# Test: one pending, no ID → backward compat
def test_approve_single_pending_no_id(mock_ctx, in_memory_workflow_db):
    task, approval = create_pending_approval(in_memory_workflow_db)
    registry = make_registry(mock_ctx)
    registry._cmd_approve("")
    approval_row = fetch_approval(in_memory_workflow_db, approval.approval_id)
    assert approval_row["status"] == "approved"

# Test: multiple pending, no ID → fail closed
def test_approve_multiple_pending_no_id(mock_ctx, in_memory_workflow_db):
    create_pending_approval(in_memory_workflow_db)
    create_pending_approval(in_memory_workflow_db)
    registry = make_registry(mock_ctx)
    registry._cmd_approve("")
    assert "2 pending approvals" in mock_ctx.out.last_error
    # No approval resolved
    assert count_pending(in_memory_workflow_db) == 2

# Test: multiple pending, explicit ID → resolves correct one
def test_approve_multiple_pending_with_id(mock_ctx, in_memory_workflow_db):
    task1, approval1 = create_pending_approval(in_memory_workflow_db)
    task2, approval2 = create_pending_approval(in_memory_workflow_db)
    registry = make_registry(mock_ctx)
    registry._cmd_approve(f"{approval2.approval_id} my reason")
    assert fetch_approval(in_memory_workflow_db, approval2.approval_id)["status"] == "approved"
    assert fetch_approval(in_memory_workflow_db, approval1.approval_id)["status"] == "pending"

# Test: rejection + task halted
def test_reject_halts_task(mock_ctx, in_memory_workflow_db):
    task, approval = create_pending_approval(in_memory_workflow_db)
    registry = make_registry(mock_ctx)
    registry._cmd_reject("")
    assert fetch_approval(in_memory_workflow_db, approval.approval_id)["status"] == "rejected"
    assert fetch_task(in_memory_workflow_db, task.task_id)["status"] == "halted"

# Test: audit event fields
def test_approve_emits_audit_event(mock_ctx, in_memory_workflow_db):
    task, approval = create_pending_approval(in_memory_workflow_db, workflow_id="wf-123")
    mock_audit = MockAuditLogger()
    mock_ctx.services_required.audit_logger = mock_audit
    registry = make_registry(mock_ctx)
    registry._cmd_approve("approved for testing")
    event = mock_audit.last_event
    assert event["approval_id"] == approval.approval_id
    assert event["task_id"] == task.task_id
    assert event["workflow_id"] == "wf-123"
    assert event["decision"] == "approved"
    assert event["reason"] == "approved for testing"

# Test: _parse_approval_arg UUID detection
def test_parse_approval_arg_uuid():
    from agent.commands.cmd_workflow import _parse_approval_arg
    uid = "12345678-1234-1234-1234-123456789abc"
    approval_id, reason = _parse_approval_arg(f"{uid} some reason")
    assert approval_id == uid
    assert reason == "some reason"

def test_parse_approval_arg_no_uuid():
    from agent.commands.cmd_workflow import _parse_approval_arg
    approval_id, reason = _parse_approval_arg("my reason text")
    assert approval_id is None
    assert reason == "my reason text"
```

## Validation plan

- `uv run pytest tests/test_cmd_workflow_approval.py -v` — all pass.
- `ruff check tests/test_cmd_workflow_approval.py` — 0 errors.
