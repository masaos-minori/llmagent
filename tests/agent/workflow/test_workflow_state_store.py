"""tests/test_workflow_state_store.py
Unit tests for agent/workflow/state_store.py.
Uses a temp workflow.sqlite to avoid touching /opt/llm/db/.
"""

from __future__ import annotations

import sqlite3
import threading
import time
import uuid
from pathlib import Path
from unittest.mock import patch

import pytest
from agent.workflow.artifact_ops import record_artifact
from agent.workflow.attempt_ops import count_attempts, finish_attempt, start_attempt
from agent.workflow.idempotency_ops import begin_stage_if_new, is_event_processed
from agent.workflow.task_ops import (
    create_task,
    get_task_by_id,
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
        assert uuid.UUID(task.idempotency_key)  # UUID4, not a composite
        assert task.idempotency_key != "sess1:1"

    def test_same_session_turn_across_runs_no_collision(self, store) -> None:
        """T-1 / AC-1: two simulated runs with the same (session, turn) must not collide."""
        t1 = create_task(store._db, "sess1", 1, "1.0.0", "wf-test")
        t2 = create_task(store._db, "sess1", 1, "1.0.0", "wf-test")
        assert t1.idempotency_key != t2.idempotency_key
        assert uuid.UUID(t1.idempotency_key)
        assert uuid.UUID(t2.idempotency_key)

    def test_get_by_idempotency_key(self, store) -> None:
        original = create_task(store._db, "sess2", 5, "1.0.0", "wf-test")
        found = get_task_by_idempotency_key(store._db, original.idempotency_key)
        assert found is not None
        assert found.task_id == original.task_id

    def test_get_by_idempotency_key_missing(self, store) -> None:
        assert get_task_by_idempotency_key(store._db, "nosuchkey") is None

    def test_create_task_without_session_id(self, store) -> None:
        task = create_task(store._db, None, None, "1.0.0", "wf-test")
        assert task.session_id is None
        assert task.turn_number is None
        assert task.status == "pending"

    def test_retained_db_compatibility(self, store) -> None:
        """T-3 / AC-4: a pre-existing composite-key row stays readable after a normal insert."""
        old_key = ":0"
        store._db.execute(
            "INSERT INTO tasks (task_id, session_id, turn_number, idempotency_key, status, workflow_version, workflow_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("old-task", "sess-old", 0, old_key, "pending", "1.0.0", "wf-old"),
        )
        store._db.commit()
        fresh = create_task(store._db, "sess-new", 1, "1.0.0", "wf-new")
        old_row = get_task_by_idempotency_key(store._db, old_key)
        assert old_row is not None
        assert old_row.task_id == "old-task"
        fresh_row = get_task_by_id(store._db, fresh.task_id)
        assert fresh_row is not None
        assert fresh_row.task_id == fresh.task_id

    def test_state_store_create_task_issues_unique_keys(self, store) -> None:
        first = store.create_task("X", 1, "1.0.0", "wf-test")
        second = store.create_task("X", 1, "1.0.0", "wf-test")
        uuid.UUID(first.idempotency_key)
        uuid.UUID(second.idempotency_key)
        assert first.idempotency_key != second.idempotency_key
        assert first.idempotency_key != "X:1"
        assert second.idempotency_key != "X:1"


class TestUpdateTaskStatus:
    def test_update_status(self, store) -> None:
        task = create_task(store._db, "sess1", 1, "1.0.0", "wf-test")
        update_task_status(store._db, task.task_id, "running")
        found = get_task_by_idempotency_key(store._db, task.idempotency_key)
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


class TestDiagnosticQueries:
    """Characterization tests for StateStore's session-scoped diagnostic counters.

    These methods (get_task_count, get_workflow_count,
    get_execute_attempt_count, get_artifact_uris) were previously exercised only
    via mocks in tests/agent/test_repl.py — added here to lock behavior before
    extracting the shared count-query pattern.
    """

    def test_get_task_count(self, store) -> None:
        create_task(store._db, "sess-diag", 1, "1.0.0", "wf-a")
        create_task(store._db, "sess-diag", 2, "1.0.0", "wf-a")
        create_task(store._db, "sess-other", 1, "1.0.0", "wf-a")

        assert store.get_task_count("sess-diag") == 2
        assert store.get_task_count("sess-other") == 1
        assert store.get_task_count("sess-none") == 0

    def test_get_workflow_count_counts_distinct(self, store) -> None:
        create_task(store._db, "sess-diag", 1, "1.0.0", "wf-a")
        create_task(store._db, "sess-diag", 2, "1.0.0", "wf-a")
        create_task(store._db, "sess-diag", 3, "1.0.0", "wf-b")

        assert store.get_workflow_count("sess-diag") == 2
        assert store.get_workflow_count("sess-none") == 0

    def test_get_execute_attempt_count_filters_by_stage(self, store) -> None:
        task = create_task(store._db, "sess-diag", 1, "1.0.0", "wf-a")
        start_attempt(store._db, task.task_id, "execute")
        start_attempt(store._db, task.task_id, "execute")
        start_attempt(store._db, task.task_id, "plan")

        assert store.get_execute_attempt_count("sess-diag") == 2
        assert store.get_execute_attempt_count("sess-none") == 0

    def test_get_artifact_uris(self, store) -> None:
        task = create_task(store._db, "sess-diag", 1, "1.0.0", "wf-a")
        record_artifact(store._db, task.task_id, "execute", "file:///tmp/a.txt")
        record_artifact(store._db, task.task_id, "execute", "file:///tmp/b.txt")

        uris = store.get_artifact_uris("sess-diag")

        assert sorted(uris) == ["file:///tmp/a.txt", "file:///tmp/b.txt"]
        assert store.get_artifact_uris("sess-none") == []


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

    def test_recover_multiple_stale_attempts(self, workflow_db) -> None:
        """Multiple stale attempts should all be marked as failed."""
        from unittest.mock import patch

        from agent.workflow.state_store import StateStore

        with patch(
            "db.helper.build_db_config", return_value=_make_cfg(str(workflow_db))
        ):
            s = StateStore()
        try:
            old_ts = time.strftime(
                "%Y-%m-%dT%H:%M:%S", time.localtime(time.time() - 100)
            )

            task_id = "task-multi"
            conn = sqlite3.connect(str(workflow_db))
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
                ("att-multi-1", task_id, "execute", old_ts),
            )
            conn.execute(
                "INSERT INTO attempts (attempt_id, task_id, stage_id, status, started_at) VALUES (?, ?, ?, 'running', ?)",
                ("att-multi-2", task_id, "execute", old_ts),
            )
            conn.commit()
            conn.close()

            count = s.recover_stale_attempts(s._db)
            assert count == 2

            rows = s._db.fetchall(
                "SELECT status FROM attempts WHERE attempt_id IN ('att-multi-1', 'att-multi-2')"
            )
            for row in rows:
                assert row[0] == "failed"
        finally:
            s.close()

    def test_recover_no_stale_attempts(self, workflow_db) -> None:
        """Calling recover_stale_attempts when none are stale should return 0."""
        from unittest.mock import patch

        from agent.workflow.state_store import StateStore

        with patch(
            "db.helper.build_db_config", return_value=_make_cfg(str(workflow_db))
        ):
            s = StateStore()
        try:
            now_ts = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())
            task_id = "task-none"
            conn = sqlite3.connect(str(workflow_db))
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
                    now_ts,
                    now_ts,
                ),
            )
            conn.execute(
                "INSERT INTO attempts (attempt_id, task_id, stage_id, status, started_at) VALUES (?, ?, ?, 'running', ?)",
                ("att-none", task_id, "execute", now_ts),
            )
            conn.commit()
            conn.close()

            count = s.recover_stale_attempts(s._db)
            assert count == 0
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
                s = StateStore()
                count = s.recover_stale_attempts(s.get_connection())
                results.append(count)
                s.close()
            except Exception as e:  # noqa: BLE001 — capturing for assertion, not swallowing silently
                errors.append(e)

        # Patch once in the main thread: mock.patch is not thread-safe, so entering
        # it from each worker can leak the mock into db.helper after the test.
        with patch(
            "db.helper.build_db_config",
            return_value=DbConfig(
                rag_db_path="/tmp/rag.sqlite",
                session_db_path="/tmp/session.sqlite",
                workflow_db_path=str(workflow_db),
            ),
        ):
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
