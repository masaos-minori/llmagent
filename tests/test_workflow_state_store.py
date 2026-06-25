"""tests/test_workflow_state_store.py
Unit tests for agent/workflow/state_store.py.
Uses a temp workflow.sqlite to avoid touching /opt/llm/db/.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from unittest.mock import patch

import pytest
from db.config import DbConfig
from db.workflow_schema import init_schema


def _make_cfg(db_path: str) -> DbConfig:
    return DbConfig(
        rag_db_path="/opt/llm/db/rag.sqlite",
        session_db_path="/opt/llm/db/session.sqlite",
        workflow_db_path=db_path,
    )


@pytest.fixture()
def workflow_db(tmp_path: Path) -> Path:
    from unittest.mock import patch

    from db.config import DbConfig

    db_path = tmp_path / "workflow.sqlite"
    rag_path = tmp_path / "rag.sqlite"
    session_path = tmp_path / "session.sqlite"
    with patch(
        "db.helper.build_db_config",
        return_value=DbConfig(
            rag_db_path=str(rag_path),
            session_db_path=str(session_path),
            workflow_db_path=str(db_path),
        ),
    ):
        init_schema()
    return db_path


@pytest.fixture()
def store(workflow_db: Path):
    from agent.workflow.state_store import StateStore

    with patch("db.helper.build_db_config", return_value=_make_cfg(str(workflow_db))):
        s = StateStore()
    yield s
    s.close()


class TestCreateTask:
    def test_create_returns_task_record(self, store) -> None:
        task = store.create_task("sess1", 1, "1.0.0")
        assert task.session_id == "sess1"
        assert task.turn_number == 1
        assert task.workflow_version == "1.0.0"
        assert task.status == "pending"
        assert task.idempotency_key == "sess1:1"

    def test_idempotency_key_unique(self, store) -> None:
        store.create_task("sess1", 1, "1.0.0")
        with pytest.raises(sqlite3.IntegrityError):
            store.create_task("sess1", 1, "1.0.0")

    def test_get_by_idempotency_key(self, store) -> None:
        original = store.create_task("sess2", 5, "1.0.0")
        found = store.get_task_by_idempotency_key("sess2:5")
        assert found is not None
        assert found.task_id == original.task_id

    def test_get_by_idempotency_key_missing(self, store) -> None:
        assert store.get_task_by_idempotency_key("nosuchkey") is None


class TestUpdateTaskStatus:
    def test_update_status(self, store) -> None:
        task = store.create_task("sess1", 1, "1.0.0")
        store.update_task_status(task.task_id, "running")
        found = store.get_task_by_idempotency_key("sess1:1")
        assert found is not None
        assert found.status == "running"


class TestAttempts:
    def test_start_attempt_returns_record(self, store) -> None:
        task = store.create_task("s", 1, "1.0.0")
        attempt = store.start_attempt(task.task_id, "plan")
        assert attempt.task_id == task.task_id
        assert attempt.stage_id == "plan"
        assert attempt.status == "running"

    def test_count_attempts(self, store) -> None:
        task = store.create_task("s", 1, "1.0.0")
        store.start_attempt(task.task_id, "execute")
        store.start_attempt(task.task_id, "execute")
        assert store.count_attempts(task.task_id, "execute") == 2

    def test_finish_attempt_completed(self, store) -> None:
        task = store.create_task("s", 1, "1.0.0")
        attempt = store.start_attempt(task.task_id, "plan")
        store.finish_attempt(attempt.attempt_id, "completed")
        rows = store._db.fetchall(
            "SELECT status FROM attempts WHERE attempt_id=?", (attempt.attempt_id,)
        )
        assert rows[0][0] == "completed"

    def test_finish_attempt_with_error(self, store) -> None:
        task = store.create_task("s", 1, "1.0.0")
        attempt = store.start_attempt(task.task_id, "execute")
        store.finish_attempt(attempt.attempt_id, "failed", "timeout")
        rows = store._db.fetchall(
            "SELECT status, error_msg FROM attempts WHERE attempt_id=?",
            (attempt.attempt_id,),
        )
        assert rows[0][0] == "failed"
        assert rows[0][1] == "timeout"


class TestIdempotency:
    def test_event_not_processed_initially(self, store) -> None:
        assert store.is_event_processed("evt-1") is False

    def test_begin_stage_if_new_returns_attempt(self, store) -> None:
        task = store.create_task("s", 1, "1.0.0")
        result = store.begin_stage_if_new("evt-1", task.task_id, "plan")
        assert result is not None
        assert result.stage_id == "plan"

    def test_begin_stage_if_new_skips_duplicate(self, store) -> None:
        task = store.create_task("s", 1, "1.0.0")
        store.begin_stage_if_new("evt-1", task.task_id, "plan")
        result = store.begin_stage_if_new("evt-1", task.task_id, "plan")
        assert result is None

    def test_event_processed_after_begin(self, store) -> None:
        task = store.create_task("s", 1, "1.0.0")
        store.begin_stage_if_new("evt-2", task.task_id, "execute")
        assert store.is_event_processed("evt-2") is True


class TestArtifacts:
    def test_record_artifact(self, store) -> None:
        task = store.create_task("s", 1, "1.0.0")
        ref = store.record_artifact(task.task_id, "execute", "file:///tmp/result.json")
        assert ref.task_id == task.task_id
        assert ref.uri == "file:///tmp/result.json"


class TestApprovals:
    def test_request_approval_returns_pending_record(self, store) -> None:
        task = store.create_task("s", 1, "1.0.0")
        approval = store.request_approval(task.task_id)
        assert approval.task_id == task.task_id
        assert approval.status == "pending"
        assert approval.stage_id is None
        assert approval.resolved_at is None

    def test_request_approval_with_stage(self, store) -> None:
        task = store.create_task("s", 1, "1.0.0")
        approval = store.request_approval(task.task_id, stage_id="execute")
        assert approval.stage_id == "execute"

    def test_get_pending_approval_returns_latest(self, store) -> None:
        task = store.create_task("s", 1, "1.0.0")
        store.request_approval(task.task_id)
        found = store.get_pending_approval(task.task_id)
        assert found is not None
        assert found.status == "pending"

    def test_get_pending_approval_returns_none_when_absent(self, store) -> None:
        task = store.create_task("s", 1, "1.0.0")
        assert store.get_pending_approval(task.task_id) is None

    def test_resolve_approval_approved(self, store) -> None:
        task = store.create_task("s", 1, "1.0.0")
        approval = store.request_approval(task.task_id)
        store.resolve_approval(approval.approval_id, "approved", "looks good")
        found = store.get_pending_approval(task.task_id)
        assert found is not None
        assert found.status == "approved"
        assert found.reason == "looks good"
        assert found.resolved_at is not None

    def test_resolve_approval_rejected(self, store) -> None:
        task = store.create_task("s", 1, "1.0.0")
        approval = store.request_approval(task.task_id)
        store.resolve_approval(approval.approval_id, "rejected", "too risky")
        found = store.get_pending_approval(task.task_id)
        assert found is not None
        assert found.status == "rejected"
        assert found.reason == "too risky"

    def test_create_task_without_session_id(self, store) -> None:
        task = store.create_task(None, None, "1.0.0")
        assert task.session_id is None
        assert task.turn_number is None
        assert task.status == "pending"


class TestFindPendingApprovalBySession:
    def test_returns_none_when_no_pending_approval(self, store) -> None:
        """Returns None when no tasks with pending_approval status exist for the session."""
        result = store.find_pending_approval_by_session("session-99")
        assert result is None

    def test_returns_approval_for_matching_session(self, store) -> None:
        """Returns (task_id, ApprovalRecord) when a pending approval exists for the session."""
        session_id = "session-find-test"
        task = store.create_task(session_id, 1, "1.0.0")
        store.update_task_status(task.task_id, "pending_approval")
        approval = store.request_approval(task.task_id, stage_id="stage-1")

        result = store.find_pending_approval_by_session(session_id)

        assert result is not None
        returned_task_id, returned_approval = result
        assert returned_task_id == task.task_id
        assert returned_approval.approval_id == approval.approval_id
        assert returned_approval.status == "pending"

    def test_returns_none_for_different_session(self, store) -> None:
        """Does not return an approval belonging to a different session."""
        task = store.create_task("session-other", 1, "1.0.0")
        store.update_task_status(task.task_id, "pending_approval")
        store.request_approval(task_id=task.task_id, stage_id="s1")

        result = store.find_pending_approval_by_session("session-mine")
        assert result is None

    def test_returns_most_recent_when_multiple(self, store) -> None:
        """Returns the most recently created approval when multiple pending exist."""
        session_id = "session-multi"
        task1 = store.create_task(session_id, 1, "1.0.0")
        store.update_task_status(task1.task_id, "pending_approval")
        store.request_approval(task_id=task1.task_id, stage_id="s1")

        task2 = store.create_task(session_id, 2, "1.0.0")
        store.update_task_status(task2.task_id, "pending_approval")
        latest = store.request_approval(task_id=task2.task_id, stage_id="s2")

        result = store.find_pending_approval_by_session(session_id)
        assert result is not None
        _, returned_approval = result
        assert returned_approval.approval_id == latest.approval_id


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
