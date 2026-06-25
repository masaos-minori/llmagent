# test_workflow_state_store.py — add find_latest_pending_approval tests

**Plan:** `plans/20260625-092947_plan.md` (req #60)
**Target:** `tests/test_workflow_state_store.py`

## What to add

Add a new class `TestFindLatestPendingApproval` after the existing `TestFindPendingApprovalBySession`
class (after line 236).

```python
class TestFindLatestPendingApproval:
    def test_returns_none_when_no_pending_approval(self, store) -> None:
        """Returns None when no pending approvals exist globally."""
        result = store.find_latest_pending_approval()
        assert result is None

    def test_returns_most_recent_globally(self, store) -> None:
        """Returns the most recently created pending approval, regardless of session."""
        task1 = store.create_task("session-a", 1, "1.0.0")
        store.update_task_status(task1.task_id, "pending_approval")
        store.request_approval(task_id=task1.task_id, stage_id="s1")

        task2 = store.create_task("session-b", 1, "1.0.0")
        store.update_task_status(task2.task_id, "pending_approval")
        latest = store.request_approval(task_id=task2.task_id, stage_id="s2")

        result = store.find_latest_pending_approval()
        assert result is not None
        returned_task_id, returned_approval = result
        assert returned_task_id == task2.task_id
        assert returned_approval.approval_id == latest.approval_id
        assert returned_approval.status == "pending"

    def test_cross_session_recovery(self, store) -> None:
        """Returns approval for a task created in a different session (simulates restart)."""
        old_session_id = "session-old"
        task = store.create_task(old_session_id, 1, "1.0.0")
        store.update_task_status(task.task_id, "pending_approval")
        approval = store.request_approval(task_id=task.task_id, stage_id="plan")

        # After restart, a new session_id would be used — but find_latest_pending_approval()
        # returns the approval regardless of session.
        result = store.find_latest_pending_approval()

        assert result is not None
        returned_task_id, returned_approval = result
        assert returned_task_id == task.task_id
        assert returned_approval.approval_id == approval.approval_id
```

## Validation

```
uv run pytest tests/test_workflow_state_store.py::TestFindLatestPendingApproval -v
uv run pytest tests/test_workflow_state_store.py -q
```
