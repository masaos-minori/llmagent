# Implementation and Test Procedure: TestFindPendingApprovalBySession in test_workflow_state_store.py

## Goal

Add `TestFindPendingApprovalBySession` to `tests/test_workflow_state_store.py` to verify that `StateStore.find_pending_approval_by_session()` returns the correct approval record or `None`.

## Scope

**In:**
- `tests/test_workflow_state_store.py` — append `TestFindPendingApprovalBySession` class

**Out:**
- Modifying `state_store.py` (already implemented)
- Testing other `StateStore` methods

## Assumptions

1. The existing `store` fixture provides a `StateStore` backed by a temp `workflow.sqlite`.
2. `store.create_task(session_id=..., idempotency_key=..., description=...)` creates a task.
3. `store.request_approval(task_id=..., stage_id=..., reason=...)` creates a pending approval record and returns `ApprovalRecord`.
4. `store.update_task_status(task_id, "pending_approval")` sets task status to `pending_approval`.
5. `find_pending_approval_by_session(session_id)` returns `tuple[str, ApprovalRecord] | None`.
6. `ApprovalRecord` is importable from `agent.workflow.state_store`.

## Implementation

### Target file
`tests/test_workflow_state_store.py`

### Procedure
Append the following class after the existing `TestApprovals` class (before the trailing `test_create_task_without_session_id` test or at end of file).

### Method
Use the existing `store` fixture. Create a task, set its status to `pending_approval`, add an approval record, then call `find_pending_approval_by_session`. Verify the returned tuple.

### Details

```python
class TestFindPendingApprovalBySession:
    def test_returns_none_when_no_pending_approval(self, store) -> None:
        """Returns None when no tasks with pending_approval status exist for the session."""
        result = store.find_pending_approval_by_session("session-99")
        assert result is None

    def test_returns_approval_for_matching_session(self, store) -> None:
        """Returns (task_id, ApprovalRecord) when a pending approval exists for the session."""
        session_id = "session-find-test"
        task = store.create_task(
            session_id=session_id,
            idempotency_key="idem-find-01",
            description="test task",
        )
        store.update_task_status(task.task_id, "pending_approval")
        approval = store.request_approval(
            task_id=task.task_id,
            stage_id="stage-1",
            reason="needs review",
        )

        result = store.find_pending_approval_by_session(session_id)

        assert result is not None
        returned_task_id, returned_approval = result
        assert returned_task_id == task.task_id
        assert returned_approval.approval_id == approval.approval_id
        assert returned_approval.status == "pending"
        assert returned_approval.reason == "needs review"

    def test_returns_none_for_different_session(self, store) -> None:
        """Does not return an approval belonging to a different session."""
        task = store.create_task(
            session_id="session-other",
            idempotency_key="idem-other",
            description="other task",
        )
        store.update_task_status(task.task_id, "pending_approval")
        store.request_approval(task_id=task.task_id, stage_id="s1", reason="r")

        result = store.find_pending_approval_by_session("session-mine")
        assert result is None

    def test_returns_most_recent_when_multiple(self, store) -> None:
        """Returns the most recently created approval when multiple pending exist."""
        session_id = "session-multi"
        task1 = store.create_task(
            session_id=session_id,
            idempotency_key="idem-m1",
            description="task 1",
        )
        store.update_task_status(task1.task_id, "pending_approval")
        store.request_approval(task_id=task1.task_id, stage_id="s1", reason="first")

        task2 = store.create_task(
            session_id=session_id,
            idempotency_key="idem-m2",
            description="task 2",
        )
        store.update_task_status(task2.task_id, "pending_approval")
        latest = store.request_approval(task_id=task2.task_id, stage_id="s2", reason="second")

        result = store.find_pending_approval_by_session(session_id)
        assert result is not None
        _, returned_approval = result
        assert returned_approval.approval_id == latest.approval_id
```

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Test discovery | `uv run pytest tests/test_workflow_state_store.py::TestFindPendingApprovalBySession -v` | 4 tests collected |
| Tests pass | `uv run pytest tests/test_workflow_state_store.py::TestFindPendingApprovalBySession -v` | PASSED |
| No regression | `uv run pytest tests/test_workflow_state_store.py -v` | all pass |
| Lint | `uv run ruff check tests/test_workflow_state_store.py` | 0 errors |
