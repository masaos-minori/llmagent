"""tests/test_workflow_state_store.py
Unit tests for agent/workflow/state_store.py.
Uses a temp workflow.sqlite to avoid touching /opt/llm/db/.
"""

from __future__ import annotations

import sqlite3
import threading
import time
from pathlib import Path
from unittest.mock import patch

import pytest
from agent.workflow.approval_ops import (
    find_latest_pending_approval,
    find_pending_approval_by_session,
    get_latest_approval,
    request_approval,
    resolve_approval,
)
from agent.workflow.artifact_ops import record_artifact
from agent.workflow.attempt_ops import count_attempts, finish_attempt, start_attempt
from agent.workflow.idempotency_ops import begin_stage_if_new, is_event_processed
from agent.workflow.task_ops import (
    create_task,
    get_task_by_idempotency_key,
    update_task_status,
)
from db.config import DbConfig
from db.create_schema import create_workflow_schema


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
        create_workflow_schema()
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
        task = create_task(store._db, "sess1", 1, "1.0.0", "wf-test")
        assert task.session_id == "sess1"
        assert task.turn_number == 1
        assert task.workflow_version == "1.0.0"
        assert task.status == "pending"
        assert task.idempotency_key == "sess1:1"

    def test_idempotency_key_unique(self, store) -> None:
        create_task(store._db, "sess1", 1, "1.0.0", "wf-test")
        with pytest.raises(sqlite3.IntegrityError):
            create_task(store._db, "sess1", 1, "1.0.0", "wf-test")

    def test_get_by_idempotency_key(self, store) -> None:
        original = create_task(store._db, "sess2", 5, "1.0.0", "wf-test")
        found = get_task_by_idempotency_key(store._db, "sess2:5")
        assert found is not None
        assert found.task_id == original.task_id

    def test_get_by_idempotency_key_missing(self, store) -> None:
        assert get_task_by_idempotency_key(store._db, "nosuchkey") is None


class TestUpdateTaskStatus:
    def test_update_status(self, store) -> None:
        task = create_task(store._db, "sess1", 1, "1.0.0", "wf-test")
        update_task_status(store._db, task.task_id, "running")
        found = get_task_by_idempotency_key(store._db, "sess1:1")
        assert found is not None
        assert found.status == "running"


class TestAttempts:
    def test_start_attempt_returns_record(self, store) -> None:
        task = create_task(store._db, "s", 1, "1.0.0", "wf-test")
        attempt = start_attempt(store._db, task.task_id, "plan")
        assert attempt.task_id == task.task_id
        assert attempt.stage_id == "plan"
        assert attempt.status == "running"

    def test_count_attempts(self, store) -> None:
        task = create_task(store._db, "s", 1, "1.0.0", "wf-test")
        start_attempt(store._db, task.task_id, "execute")
        start_attempt(store._db, task.task_id, "execute")
        assert count_attempts(store._db, task.task_id, "execute") == 2

    def test_finish_attempt_completed(self, store) -> None:
        task = create_task(store._db, "s", 1, "1.0.0", "wf-test")
        attempt = start_attempt(store._db, task.task_id, "plan")
        finish_attempt(store._db, attempt.attempt_id, "completed")
        rows = store._db.fetchall(
            "SELECT status FROM attempts WHERE attempt_id=?", (attempt.attempt_id,)
        )
        assert rows[0][0] == "completed"

    def test_finish_attempt_with_error(self, store) -> None:
        task = create_task(store._db, "s", 1, "1.0.0", "wf-test")
        attempt = start_attempt(store._db, task.task_id, "execute")
        finish_attempt(store._db, attempt.attempt_id, "failed", "timeout")
        rows = store._db.fetchall(
            "SELECT status, error_msg FROM attempts WHERE attempt_id=?",
            (attempt.attempt_id,),
        )
        assert rows[0][0] == "failed"
        assert rows[0][1] == "timeout"


class TestIdempotency:
    def test_event_not_processed_initially(self, store) -> None:
        assert is_event_processed(store._db, "evt-1") is False

    def test_begin_stage_if_new_returns_attempt(self, store) -> None:
        task = create_task(store._db, "s", 1, "1.0.0", "wf-test")
        result = begin_stage_if_new(store._db, "evt-1", task.task_id, "plan")
        assert result is not None
        assert result.stage_id == "plan"

    def test_begin_stage_if_new_skips_duplicate(self, store) -> None:
        task = create_task(store._db, "s", 1, "1.0.0", "wf-test")
        begin_stage_if_new(store._db, "evt-1", task.task_id, "plan")
        result = begin_stage_if_new(store._db, "evt-1", task.task_id, "plan")
        assert result is None

    def test_event_processed_after_begin(self, store) -> None:
        task = create_task(store._db, "s", 1, "1.0.0", "wf-test")
        begin_stage_if_new(store._db, "evt-2", task.task_id, "execute")
        assert is_event_processed(store._db, "evt-2") is True


class TestArtifacts:
    def test_record_artifact(self, store) -> None:
        task = create_task(store._db, "s", 1, "1.0.0", "wf-test")
        ref = record_artifact(
            store._db, task.task_id, "execute", "file:///tmp/result.json"
        )
        assert ref.task_id == task.task_id
        assert ref.uri == "file:///tmp/result.json"


class TestApprovals:
    def test_request_approval_returns_pending_record(self, store) -> None:
        task = create_task(store._db, "s", 1, "1.0.0", "wf-test")
        approval = request_approval(store._db, task.task_id)
        assert approval.task_id == task.task_id
        assert approval.status == "pending"
        assert approval.stage_id is None
        assert approval.resolved_at is None

    def test_request_approval_with_stage(self, store) -> None:
        task = create_task(store._db, "s", 1, "1.0.0", "wf-test")
        approval = request_approval(store._db, task.task_id, stage_id="execute")
        assert approval.stage_id == "execute"

    def test_get_latest_approval_returns_latest(self, store) -> None:
        task = create_task(store._db, "s", 1, "1.0.0", "wf-test")
        request_approval(store._db, task.task_id)
        found = get_latest_approval(store._db, task.task_id)
        assert found is not None
        assert found.status == "pending"

    def test_get_latest_approval_returns_none_when_absent(self, store) -> None:
        task = create_task(store._db, "s", 1, "1.0.0", "wf-test")
        assert get_latest_approval(store._db, task.task_id) is None

    def test_resolve_approval_approved(self, store) -> None:
        task = create_task(store._db, "s", 1, "1.0.0", "wf-test")
        approval = request_approval(store._db, task.task_id)
        resolve_approval(store._db, approval.approval_id, "approved", "looks good")
        found = get_latest_approval(store._db, task.task_id)
        assert found is not None
        assert found.status == "approved"
        assert found.reason == "looks good"
        assert found.resolved_at is not None

    def test_resolve_approval_rejected(self, store) -> None:
        task = create_task(store._db, "s", 1, "1.0.0", "wf-test")
        approval = request_approval(store._db, task.task_id)
        resolve_approval(store._db, approval.approval_id, "rejected", "too risky")
        found = get_latest_approval(store._db, task.task_id)
        assert found is not None
        assert found.status == "rejected"
        assert found.reason == "too risky"

    def test_create_task_without_session_id(self, store) -> None:
        task = create_task(store._db, None, None, "1.0.0", "wf-test")
        assert task.session_id is None
        assert task.turn_number is None
        assert task.status == "pending"


class TestFindPendingApprovalBySession:
    def test_returns_none_when_no_pending_approval(self, store) -> None:
        """Returns None when no tasks with pending_approval status exist for the session."""
        result = find_pending_approval_by_session(store._db, "session-99")
        assert result is None

    def test_returns_approval_for_matching_session(self, store) -> None:
        """Returns (task_id, ApprovalRecord) when a pending approval exists for the session."""
        session_id = "session-find-test"
        task = create_task(store._db, session_id, 1, "1.0.0", "wf-test")
        update_task_status(store._db, task.task_id, "pending_approval")
        approval = request_approval(store._db, task.task_id, stage_id="stage-1")

        result = find_pending_approval_by_session(store._db, session_id)

        assert result is not None
        returned_task_id, returned_approval = result
        assert returned_task_id == task.task_id
        assert returned_approval.approval_id == approval.approval_id
        assert returned_approval.status == "pending"

    def test_returns_none_for_different_session(self, store) -> None:
        """Does not return an approval belonging to a different session."""
        task = create_task(store._db, "session-other", 1, "1.0.0", "wf-test")
        update_task_status(store._db, task.task_id, "pending_approval")
        request_approval(store._db, task_id=task.task_id, stage_id="s1")

        result = find_pending_approval_by_session(store._db, "session-mine")
        assert result is None

    def test_returns_most_recent_when_multiple(self, store) -> None:
        """Returns the most recently created approval when multiple pending exist."""
        session_id = "session-multi"
        task1 = create_task(store._db, session_id, 1, "1.0.0", "wf-test")
        update_task_status(store._db, task1.task_id, "pending_approval")
        request_approval(store._db, task_id=task1.task_id, stage_id="s1")

        task2 = create_task(store._db, session_id, 2, "1.0.0", "wf-test")
        update_task_status(store._db, task2.task_id, "pending_approval")
        latest = request_approval(store._db, task_id=task2.task_id, stage_id="s2")

        result = find_pending_approval_by_session(store._db, session_id)
        assert result is not None
        _, returned_approval = result
        assert returned_approval.approval_id == latest.approval_id


class TestFindLatestPendingApproval:
    def test_returns_none_when_no_pending_approval(self, store) -> None:
        """Returns None when no pending approvals exist globally."""
        result = find_latest_pending_approval(store._db)
        assert result is None

    def test_returns_most_recent_globally(self, store) -> None:
        """Returns the most recently created pending approval, regardless of session."""
        task1 = create_task(store._db, "session-a", 1, "1.0.0", "wf-test")
        update_task_status(store._db, task1.task_id, "pending_approval")
        request_approval(store._db, task_id=task1.task_id, stage_id="s1")

        task2 = create_task(store._db, "session-b", 1, "1.0.0", "wf-test")
        update_task_status(store._db, task2.task_id, "pending_approval")
        latest = request_approval(store._db, task_id=task2.task_id, stage_id="s2")

        result = find_latest_pending_approval(store._db)
        assert result is not None
        returned_task_id, returned_approval = result
        assert returned_task_id == task2.task_id
        assert returned_approval.approval_id == latest.approval_id
        assert returned_approval.status == "pending"

    def test_cross_session_recovery(self, store) -> None:
        """Returns approval for a task created in a different session (simulates restart)."""
        old_session_id = "session-old"
        task = create_task(store._db, old_session_id, 1, "1.0.0", "wf-test")
        update_task_status(store._db, task.task_id, "pending_approval")
        request_approval(store._db, task_id=task.task_id, stage_id="plan")

        # After restart, a new session_id would be used — but find_latest_pending_approval()
        # returns the approval regardless of session.
        result = find_latest_pending_approval(store._db)

        assert result is not None
        returned_task_id, returned_approval = result


class TestStateStoreGetConnection:
    def test_get_connection_returns_same_instance_as_private_attribute(
        self, store
    ) -> None:
        """get_connection() returns the same SQLiteHelper instance as _db."""
        conn = store.get_connection()
        assert conn is store._db


class TestRecoverStaleAttempts:
    def _insert_task_and_attempt(
        self, store, attempt_id, task_id, stage_id, status, started_at
    ):
        """Helper to insert a task and its attempt together."""
        store._db.execute(
            "INSERT INTO tasks (task_id, session_id, turn_number, idempotency_key, status, workflow_version, workflow_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (task_id, "sess-test", 1, f"{task_id}:1", "pending", "1.0.0", "wf-test"),
        )
        store._db.execute(
            "INSERT INTO attempts (attempt_id, task_id, stage_id, status, started_at) VALUES (?, ?, ?, ?, ?)",
            (attempt_id, task_id, stage_id, status, started_at),
        )
        store._db.commit()

    def test_stale_attempt_marked_failed(self, workflow_db) -> None:
        """An attempt older than the grace period is marked as failed."""
        from unittest.mock import patch

        from agent.workflow.state_store import StateStore

        with patch(
            "db.helper.build_db_config", return_value=_make_cfg(str(workflow_db))
        ):
            s = StateStore()
        try:
            self._insert_task_and_attempt(
                s, "att-stale", "task-1", "execute", "running", "2026-01-01T00:00:00"
            )

            s.recover_stale_attempts(s._db)

            rows = s._db.fetchall(
                "SELECT status FROM attempts WHERE attempt_id='att-stale'"
            )
            assert rows[0][0] == "failed"
        finally:
            s.close()

    def test_fresh_attempt_not_marked_failed(self, workflow_db) -> None:
        """An attempt within the grace period is NOT marked as failed."""
        from unittest.mock import patch

        from agent.workflow.state_store import StateStore

        with patch(
            "db.helper.build_db_config", return_value=_make_cfg(str(workflow_db))
        ):
            s = StateStore()
        try:
            # Use current time so it's definitely within the grace period
            now_ts = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())
            self._insert_task_and_attempt(
                s, "att-fresh", "task-2", "execute", "running", now_ts
            )

            s.recover_stale_attempts(s._db)

            rows = s._db.fetchall(
                "SELECT status FROM attempts WHERE attempt_id='att-fresh'"
            )
            assert rows[0][0] == "running"
        finally:
            s.close()

    def test_completed_attempt_not_modified(self, workflow_db) -> None:
        """A completed attempt is not modified by recovery."""
        from unittest.mock import patch

        from agent.workflow.state_store import StateStore

        with patch(
            "db.helper.build_db_config", return_value=_make_cfg(str(workflow_db))
        ):
            s = StateStore()
        try:
            self._insert_task_and_attempt(
                s, "att-done", "task-3", "plan", "completed", "2026-01-01T00:00:00"
            )

            s.recover_stale_attempts(s._db)

            rows = s._db.fetchall(
                "SELECT status FROM attempts WHERE attempt_id='att-done'"
            )
            assert rows[0][0] == "completed"
        finally:
            s.close()

    def test_find_stale_returns_only_old_attempts(self, workflow_db) -> None:
        """find_stale_running_attempts returns only attempts exceeding the grace period."""
        from unittest.mock import patch

        from agent.workflow.state_store import StateStore

        with patch(
            "db.helper.build_db_config", return_value=_make_cfg(str(workflow_db))
        ):
            s = StateStore()
        try:
            self._insert_task_and_attempt(
                s, "att-1", "task-1", "execute", "running", "2026-01-01T00:00:00"
            )
            now_ts = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())
            self._insert_task_and_attempt(
                s, "att-2", "task-2", "execute", "running", now_ts
            )

            stale = s.find_stale_running_attempts(s._db)

            stale_ids = [item["attempt_id"] for item in stale]
            assert "att-1" in stale_ids
            assert "att-2" not in stale_ids
        finally:
            s.close()

    def test_recovered_attempt_has_ended_at_set(self, workflow_db) -> None:
        """A recovered stale attempt has ended_at populated."""
        from unittest.mock import patch

        from agent.workflow.state_store import StateStore

        with patch(
            "db.helper.build_db_config", return_value=_make_cfg(str(workflow_db))
        ):
            s = StateStore()
        try:
            self._insert_task_and_attempt(
                s, "att-end", "task-4", "execute", "running", "2026-01-01T00:00:00"
            )

            s.recover_stale_attempts(s._db)

            rows = s._db.fetchall(
                "SELECT ended_at FROM attempts WHERE attempt_id='att-end'"
            )
            assert rows[0][0] is not None
        finally:
            s.close()


class TestStaleRecoveryConcurrency:
    def test_concurrent_recovery_claims_only_once(self, workflow_db: Path) -> None:
        import sqlite3
        import time
        from unittest.mock import patch

        from agent.workflow.state_store import StateStore
        from db.config import DbConfig

        # Setup: create a stale attempt manually in the DB
        old_ts = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(time.time() - 100))

        # Use raw connection to seed data
        conn = sqlite3.connect(str(workflow_db))
        task_id = "task-concurrent"
        attempt_id = "att-concurrent"
        conn.execute(
            "INSERT INTO tasks (task_id, session_id, turn_number, idempotency_key, status, workflow_version, workflow_id, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                task_id,
                "sess-test",
                1,
                f"{task_id}:1",
                "pending",
                "1.0.0",
                "wf-test",
                old_ts,
                old_ts,
            ),
        )
        conn.execute(
            "INSERT INTO attempts (attempt_id, task_id, stage_id, status, started_at) VALUES (?, ?, ?, 'running', ?)",
            (attempt_id, task_id, "execute", old_ts),
        )
        conn.commit()
        conn.close()

        results = []
        errors = []

        def worker():
            try:
                with patch(
                    "db.helper.build_db_config",
                    return_value=DbConfig(
                        rag_db_path="/tmp/rag.sqlite",
                        session_db_path="/tmp/session.sqlite",
                        workflow_db_path=str(workflow_db),
                    ),
                ):
                    s = StateStore()
                    count = s.recover_stale_attempts(s.get_connection())
                    results.append(count)
                    s.close()
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker) for _ in range(2)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Errors occurred during concurrent recovery: {errors}"
        assert sum(results) == 1, (
            f"Expected exactly 1 attempt to be recovered, but got {sum(results)}"
        )

        # Verify final state in DB
        conn = sqlite3.connect(str(workflow_db))
        rows = conn.execute(
            "SELECT status FROM attempts WHERE attempt_id=?", (attempt_id,)
        ).fetchall()
        assert rows[0][0] == "failed"
        conn.close()
