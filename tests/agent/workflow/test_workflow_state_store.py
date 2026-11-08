"""tests/test_workflow_state_store.py
Unit tests for agent/workflow/state_store.py.
Uses a temp workflow.sqlite to avoid touching /opt/llm/db/.
"""

from __future__ import annotations

import os
import sqlite3
import threading
import time
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest
from agent.workflow import tool_call_state_ops
from agent.workflow.artifact_ops import record_artifact
from agent.workflow.attempt_ops import count_attempts, finish_attempt, start_attempt
from agent.workflow.idempotency_ops import begin_stage_if_new, is_event_processed
from agent.workflow.task_ops import (
    create_task,
    get_task_by_id,
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


def _iso(seconds_ago: float) -> str:
    """Production-format Z timestamp N seconds in the past (REQ-009)."""
    return (datetime.now(UTC) - timedelta(seconds=seconds_ago)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )


def _iso_future(seconds: float) -> str:
    """Production-format Z timestamp N seconds in the future."""
    return (datetime.now(UTC) + timedelta(seconds=seconds)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
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
        assert uuid.UUID(task.task_nonce)  # UUID4, not a composite
        assert task.task_nonce != "sess1:1"

    def test_same_session_turn_across_runs_no_collision(self, store) -> None:
        """T-1 / AC-1: two simulated runs with the same (session, turn) must not collide."""
        t1 = create_task(store._db, "sess1", 1, "1.0.0", "wf-test")
        t2 = create_task(store._db, "sess1", 1, "1.0.0", "wf-test")
        assert t1.task_nonce != t2.task_nonce
        assert uuid.UUID(t1.task_nonce)
        assert uuid.UUID(t2.task_nonce)

    def test_create_task_without_session_id(self, store) -> None:
        task = create_task(store._db, None, None, "1.0.0", "wf-test")
        assert task.session_id is None
        assert task.turn_number is None
        assert task.status == "pending"

    def test_retained_db_compatibility(self, store) -> None:
        """T-3 / AC-4: a pre-existing composite-key row stays readable after a normal insert."""
        old_key = ":0"
        store._db.execute(
            "INSERT INTO tasks (task_id, session_id, turn_number, task_nonce, status, workflow_version, workflow_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("old-task", "sess-old", 0, old_key, "pending", "1.0.0", "wf-old"),
        )
        store._db.commit()
        fresh = create_task(store._db, "sess-new", 1, "1.0.0", "wf-new")
        old_row = get_task_by_id(store._db, "old-task")
        assert old_row is not None
        assert old_row.task_id == "old-task"
        fresh_row = get_task_by_id(store._db, fresh.task_id)
        assert fresh_row is not None
        assert fresh_row.task_id == fresh.task_id

    def test_state_store_create_task_issues_unique_keys(self, store) -> None:
        first = store.create_task("X", 1, "1.0.0", "wf-test")
        second = store.create_task("X", 1, "1.0.0", "wf-test")
        uuid.UUID(first.task_nonce)
        uuid.UUID(second.task_nonce)
        assert first.task_nonce != second.task_nonce
        assert first.task_nonce != "X:1"
        assert second.task_nonce != "X:1"
        assert first.task_id != second.task_id  # REQ-006: duplicate call is a new task


class TestUpdateTaskStatus:
    def test_update_status(self, store) -> None:
        task = create_task(store._db, "sess1", 1, "1.0.0", "wf-test")
        update_task_status(store._db, task.task_id, "running")
        found = get_task_by_id(store._db, task.task_id)
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
    """Recovery on the real fixture DB under lease semantics (wflease001)."""

    def _insert_task_and_attempt(
        self,
        store,
        attempt_id,
        task_id,
        stage_id,
        status,
        started_at,
        owner_id=None,
        lease_expires_at=None,
    ):
        """Helper to insert a task and its attempt together."""
        store._db.execute(
            "INSERT INTO tasks (task_id, session_id, turn_number, task_nonce, status, workflow_version, workflow_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (task_id, "sess-test", 1, f"{task_id}:1", "pending", "1.0.0", "wf-test"),
        )
        store._db.execute(
            "INSERT INTO attempts (attempt_id, task_id, stage_id, status, started_at, owner_id, lease_expires_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                attempt_id,
                task_id,
                stage_id,
                status,
                started_at,
                owner_id,
                lease_expires_at,
            ),
        )
        store._db.commit()

    def _open_store(self, workflow_db):
        from agent.workflow.state_store import StateStore

        with patch(
            "db.helper.build_db_config", return_value=_make_cfg(str(workflow_db))
        ):
            return StateStore()

    def test_stale_attempt_marked_failed(self, workflow_db) -> None:
        """A lease-less attempt older than the legacy age is marked as failed."""
        s = self._open_store(workflow_db)
        try:
            self._insert_task_and_attempt(
                s, "att-stale", "task-1", "execute", "running", "2026-01-01T00:00:00Z"
            )

            count = s.recover_stale_attempts(s._db)
            assert count == 1

            rows = s._db.fetchall(
                "SELECT status FROM attempts WHERE attempt_id='att-stale'"
            )
            assert rows[0][0] == "failed"
            assert s.last_recovery_report.legacy_recovered == 1
        finally:
            s.close()

    def test_fresh_attempt_not_marked_failed(self, workflow_db) -> None:
        """A lease-less attempt within the legacy age is NOT marked as failed."""
        s = self._open_store(workflow_db)
        try:
            self._insert_task_and_attempt(
                s, "att-fresh", "task-2", "execute", "running", _iso(5)
            )

            s.recover_stale_attempts(s._db)

            rows = s._db.fetchall(
                "SELECT status FROM attempts WHERE attempt_id='att-fresh'"
            )
            assert rows[0][0] == "running"
            assert s.last_recovery_report.still_live == 1
        finally:
            s.close()

    def test_completed_attempt_not_modified(self, workflow_db) -> None:
        """A completed attempt is not modified by recovery."""
        s = self._open_store(workflow_db)
        try:
            self._insert_task_and_attempt(
                s, "att-done", "task-3", "plan", "completed", "2026-01-01T00:00:00Z"
            )

            s.recover_stale_attempts(s._db)

            rows = s._db.fetchall(
                "SELECT status FROM attempts WHERE attempt_id='att-done'"
            )
            assert rows[0][0] == "completed"
        finally:
            s.close()

    def test_expired_lease_attempt_marked_failed(self, workflow_db) -> None:
        """AC-4/AC-6: an expired lease is stale even when the row is young."""
        s = self._open_store(workflow_db)
        try:
            self._insert_task_and_attempt(
                s,
                "att-lease",
                "task-5",
                "execute",
                "running",
                _iso(60),
                owner_id="host-a",
                lease_expires_at=_iso(30),
            )

            count = s.recover_stale_attempts(s._db)
            assert count == 1

            rows = s._db.fetchall(
                "SELECT status, error_msg FROM attempts WHERE attempt_id='att-lease'"
            )
            assert rows[0][0] == "failed"
            assert "lease expired" in (rows[0][1] or "")
            assert s.last_recovery_report.legacy_recovered == 0
        finally:
            s.close()

    def test_live_lease_attempt_not_recovered(self, workflow_db) -> None:
        """AC-4: an unexpired lease is live no matter how old the row is."""
        s = self._open_store(workflow_db)
        try:
            self._insert_task_and_attempt(
                s,
                "att-live",
                "task-6",
                "execute",
                "running",
                "2026-01-01T00:00:00Z",
                owner_id="host-a",
                lease_expires_at=_iso_future(600),
            )

            count = s.recover_stale_attempts(s._db)
            assert count == 0

            rows = s._db.fetchall(
                "SELECT status FROM attempts WHERE attempt_id='att-live'"
            )
            assert rows[0][0] == "running"
        finally:
            s.close()

    def test_unparseable_timestamp_reported_and_row_left_running(
        self, workflow_db, caplog
    ) -> None:
        """AC-3: an unparseable started_at is reported, never recovered or skipped."""
        import logging

        s = self._open_store(workflow_db)
        try:
            self._insert_task_and_attempt(
                s, "att-bad", "task-7", "execute", "running", "not-a-date"
            )
            with caplog.at_level(logging.WARNING, logger="agent.workflow.state_store"):
                count = s.recover_stale_attempts(s._db)
            assert count == 0
            rows = s._db.fetchall(
                "SELECT status FROM attempts WHERE attempt_id='att-bad'"
            )
            assert rows[0][0] == "running"
            assert s.last_recovery_report.unparseable == 1
            assert any(
                "unparseable workflow attempt timestamp" in rec.getMessage()
                for rec in caplog.records
            )
        finally:
            s.close()

    @pytest.mark.parametrize("tz_name", ["UTC", "Asia/Tokyo"])
    def test_recovery_is_timezone_independent(
        self, workflow_db, monkeypatch, request, tz_name: str
    ) -> None:
        """AC-2: identical seeds classify identically under UTC and non-UTC TZ."""
        if not hasattr(time, "tzset"):
            pytest.skip("time.tzset() is POSIX-only")
        previous_tz = os.environ.get("TZ")

        def _restore_tz() -> None:
            if previous_tz is None:
                os.environ.pop("TZ", None)
            else:
                os.environ["TZ"] = previous_tz
            time.tzset()

        request.addfinalizer(_restore_tz)
        monkeypatch.setenv("TZ", tz_name)
        time.tzset()

        s = self._open_store(workflow_db)
        try:
            self._insert_task_and_attempt(
                s, "att-tz-legacy", "task-tz1", "execute", "running", _iso(7200)
            )
            self._insert_task_and_attempt(
                s,
                "att-tz-lease",
                "task-tz2",
                "execute",
                "running",
                _iso(60),
                owner_id="host-a",
                lease_expires_at=_iso(30),
            )
            self._insert_task_and_attempt(
                s,
                "att-tz-live",
                "task-tz3",
                "execute",
                "running",
                _iso(60),
                owner_id="host-a",
                lease_expires_at=_iso_future(600),
            )

            count = s.recover_stale_attempts(s._db)
            assert count == 2

            statuses = {
                row[0]: row[1]
                for row in s._db.fetchall(
                    "SELECT attempt_id, status FROM attempts "
                    "WHERE attempt_id IN ('att-tz-legacy', 'att-tz-lease', 'att-tz-live')"
                )
            }
            assert statuses["att-tz-legacy"] == "failed"
            assert statuses["att-tz-lease"] == "failed"
            assert statuses["att-tz-live"] == "running"
            report = s.last_recovery_report
            assert (report.recovered, report.still_live) == (2, 1)
            assert (report.legacy_recovered, report.unparseable) == (1, 0)
        finally:
            s.close()

    def test_find_stale_returns_only_old_attempts(self, workflow_db) -> None:
        """find_stale_running_attempts returns only lease-expired or legacy-old attempts."""
        s = self._open_store(workflow_db)
        try:
            self._insert_task_and_attempt(
                s, "att-1", "task-1", "execute", "running", "2026-01-01T00:00:00Z"
            )
            self._insert_task_and_attempt(
                s, "att-2", "task-2", "execute", "running", _iso(5)
            )

            stale = s.find_stale_running_attempts(s._db)

            stale_ids = [item["attempt_id"] for item in stale]
            assert "att-1" in stale_ids
            assert "att-2" not in stale_ids
        finally:
            s.close()

    def test_recovered_attempt_has_ended_at_set(self, workflow_db) -> None:
        """A recovered stale attempt has ended_at populated."""
        s = self._open_store(workflow_db)
        try:
            self._insert_task_and_attempt(
                s, "att-end", "task-4", "execute", "running", "2026-01-01T00:00:00Z"
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
        s = self._open_store(workflow_db)
        try:
            old_ts = _iso(7200)

            task_id = "task-multi"
            conn = sqlite3.connect(str(workflow_db))
            conn.execute(
                "INSERT INTO tasks (task_id, session_id, turn_number, task_nonce, status, workflow_version, workflow_id, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
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
        s = self._open_store(workflow_db)
        try:
            now_ts = _iso(5)
            task_id = "task-none"
            conn = sqlite3.connect(str(workflow_db))
            conn.execute(
                "INSERT INTO tasks (task_id, session_id, turn_number, task_nonce, status, workflow_version, workflow_id, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
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
        from unittest.mock import patch

        from agent.workflow.state_store import StateStore
        from db.config import DbConfig

        # Setup: create a legacy-stale attempt (lease-less, older than the
        # 3600 s legacy age) directly in the DB.
        old_ts = _iso(7200)

        # Use raw connection to seed data
        conn = sqlite3.connect(str(workflow_db))
        task_id = "task-concurrent"
        attempt_id = "att-concurrent"
        conn.execute(
            "INSERT INTO tasks (task_id, session_id, turn_number, task_nonce, status, workflow_version, workflow_id, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
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


class TestToolCallStateOps:
    """tool_call_state helpers (toolexec001 row 07): record, pending, finalize, stale."""

    def test_record_then_pending_returns_row_for_that_task_only(self, store) -> None:
        t1 = create_task(store._db, "sess1", 1, "1.0.0", "wf-test")
        t2 = create_task(store._db, "sess2", 2, "1.0.0", "wf-test")
        store.record_tool_call(
            t1.task_id, "key-1", "calculator__calculate", "retryable"
        )
        pending1 = store.pending_tool_calls(t1.task_id)
        assert [c.idempotency_key for c in pending1] == ["key-1"]
        assert pending1[0].state == "pending"
        assert pending1[0].tool == "calculator__calculate"
        assert pending1[0].retry_class == "retryable"
        # Task isolation: the other task sees nothing (completion criterion).
        assert store.pending_tool_calls(t2.task_id) == []

    def test_lifecycle_works_on_legacy_shape_with_unused_snapshot_column(
        self, store
    ) -> None:
        """A database created before the snapshot retirement keeps working.

        The legacy shape carries an ``execution_snapshots`` table and a nullable
        ``tool_call_state.snapshot_id`` foreign-key column that no code names.
        """
        store._db.execute(
            "CREATE TABLE execution_snapshots ("
            " snapshot_id TEXT PRIMARY KEY, snapshot_json TEXT NOT NULL,"
            " recorded_at REAL NOT NULL)"
        )
        store._db.execute(
            "ALTER TABLE tool_call_state ADD COLUMN snapshot_id TEXT"
            " REFERENCES execution_snapshots(snapshot_id)"
        )
        store._db.commit()
        task = create_task(store._db, "sess-legacy", 1, "1.0.0", "wf-test")
        store.record_tool_call(
            task.task_id, "key-legacy", "calculator__calculate", "retryable"
        )
        assert [c.idempotency_key for c in store.pending_tool_calls(task.task_id)] == [
            "key-legacy"
        ]
        store.finalize_tool_call("key-legacy", "completed")
        assert store.pending_tool_calls(task.task_id) == []

    def test_record_duplicate_key_is_ignored(self, store) -> None:
        task = create_task(store._db, "sess1", 1, "1.0.0", "wf-test")
        store.record_tool_call(
            task.task_id, "key-dup", "deepresearch__search", "retryable"
        )
        store.record_tool_call(
            task.task_id, "key-dup", "deepresearch__search", "retryable"
        )
        assert len(store.pending_tool_calls(task.task_id)) == 1

    def test_finalize_moves_state_and_bumps_updated_at(self, store) -> None:
        task = create_task(store._db, "sess1", 1, "1.0.0", "wf-test")
        store.record_tool_call(
            task.task_id, "key-f", "calculator__calculate", "non_retryable"
        )
        before = store.pending_tool_calls(task.task_id)[0]
        store.finalize_tool_call("key-f", "failed")
        row = tool_call_state_ops.get_tool_call_state(store._db, "key-f")
        assert row is not None and row.state == "failed"
        assert row.updated_at >= before.updated_at
        assert store.pending_tool_calls(task.task_id) == []

    def test_pending_ordered_by_created_at(self, store) -> None:
        task = create_task(store._db, "sess1", 1, "1.0.0", "wf-test")
        for i in range(3):
            store.record_tool_call(
                task.task_id, f"key-{i}", "calculator__calculate", "retryable"
            )
            time.sleep(0.01)
        keys = [c.idempotency_key for c in store.pending_tool_calls(task.task_id)]
        assert keys == ["key-0", "key-1", "key-2"]

    def test_classify_stale_pending_only_expired_rows_and_idempotent(
        self, store
    ) -> None:
        task = create_task(store._db, "sess1", 1, "1.0.0", "wf-test")
        store.record_tool_call(
            task.task_id, "old", "calculator__calculate", "retryable"
        )
        store.record_tool_call(
            task.task_id, "fresh", "calculator__calculate", "retryable"
        )
        # Backdate 'old' past the timeout.
        store._db.execute(
            "UPDATE tool_call_state SET created_at=? WHERE idempotency_key='old'",
            (time.time() - 120,),
        )
        store._db.commit()
        stale = store.classify_stale_pending(task.task_id, 60.0)
        assert [c.idempotency_key for c in stale] == ["old"]
        assert stale[0].state == "interrupted"
        # Fresh row still pending; expired row interrupted.
        assert [c.idempotency_key for c in store.pending_tool_calls(task.task_id)] == [
            "fresh"
        ]
        # Idempotent on re-run: nothing transitions twice.
        assert store.classify_stale_pending(task.task_id, 60.0) == []
