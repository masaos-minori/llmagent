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
from agent.workflow.attempt_ops import finish_attempt
from agent.workflow.idempotency_ops import begin_stage_if_new, is_event_processed
from agent.workflow.models import ArtifactRef, AttemptRecord
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
        assert uuid.UUID(task.task_nonce)  # UUID4
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
        # wfaudit005 REQ-002: out-of-vocabulary status raises and writes nothing.
        with pytest.raises(ValueError, match="invalid tasks.status 'done'"):
            update_task_status(store._db, task.task_id, "done")
        found = get_task_by_id(store._db, task.task_id)
        assert found is not None
        assert found.status == "running"


class TestAttempts:
    def test_begin_stage_returns_record(self, store) -> None:
        task = create_task(store._db, "s", 1, "1.0.0", "wf-test")
        attempt = begin_stage_if_new(store._db, "evt-ta-1", task.task_id, "plan")
        assert attempt is not None
        assert attempt.task_id == task.task_id
        assert attempt.stage_id == "plan"
        assert attempt.status == "running"

    def test_attempt_count_via_inline_query(self, store) -> None:
        task = create_task(store._db, "s", 1, "1.0.0", "wf-test")
        begin_stage_if_new(store._db, "evt-ta-2", task.task_id, "execute")
        begin_stage_if_new(store._db, "evt-ta-3", task.task_id, "execute")
        rows = store._db.fetchall(
            "SELECT COUNT(*) as cnt FROM attempts WHERE task_id=? AND stage_id='execute'",
            (task.task_id,),
        )
        assert int(rows[0]["cnt"]) == 2

    def test_finish_attempt_completed(self, store) -> None:
        task = create_task(store._db, "s", 1, "1.0.0", "wf-test")
        attempt = begin_stage_if_new(store._db, "evt-ta-4", task.task_id, "plan")
        assert attempt is not None
        finish_attempt(store._db, attempt.attempt_id, "completed")
        rows = store._db.fetchall(
            "SELECT status FROM attempts WHERE attempt_id=?", (attempt.attempt_id,)
        )
        assert rows[0][0] == "completed"
        # wfaudit005 REQ-002: out-of-vocabulary status raises and writes nothing.
        with pytest.raises(ValueError, match="invalid attempts.status 'done'"):
            finish_attempt(store._db, attempt.attempt_id, "done")
        rows = store._db.fetchall(
            "SELECT status FROM attempts WHERE attempt_id=?", (attempt.attempt_id,)
        )
        assert rows[0][0] == "completed"

    def test_finish_attempt_with_error(self, store) -> None:
        task = create_task(store._db, "s", 1, "1.0.0", "wf-test")
        attempt = begin_stage_if_new(store._db, "evt-ta-5", task.task_id, "execute")
        assert attempt is not None
        finish_attempt(store._db, attempt.attempt_id, "failed", "timeout")
        rows = store._db.fetchall(
            "SELECT status, error_msg FROM attempts WHERE attempt_id=?",
            (attempt.attempt_id,),
        )
        assert rows[0][0] == "failed"
        assert rows[0][1] == "timeout"

    def test_begin_stage_if_new_stamps_lease_columns(self, store) -> None:
        """begin_stage_if_new stamps owner_id/lease_expires_at only with lease_duration_sec (REQ-002)."""
        task = create_task(store._db, "s", 1, "1.0.0", "wf-test")
        stamped = begin_stage_if_new(
            store._db, "evt-ta-lease", task.task_id, "execute", lease_duration_sec=900
        )
        assert stamped is not None
        stamped_rows = store._db.fetchall(
            "SELECT owner_id, lease_expires_at, started_at FROM attempts WHERE attempt_id=?",
            (stamped.attempt_id,),
        )
        assert stamped_rows[0][0] is not None  # owner_id
        assert stamped_rows[0][1] is not None  # lease_expires_at
        assert stamped_rows[0][2] is not None  # started_at
        assert (
            stamped_rows[0][1] > stamped_rows[0][2]
        )  # Z-format string compare: later time

        leaseless = begin_stage_if_new(
            store._db, "evt-ta-nolease", task.task_id, "execute"
        )
        assert leaseless is not None
        leaseless_rows = store._db.fetchall(
            "SELECT owner_id, lease_expires_at FROM attempts WHERE attempt_id=?",
            (leaseless.attempt_id,),
        )
        assert leaseless_rows[0][0] is None  # owner_id
        assert leaseless_rows[0][1] is None  # lease_expires_at


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

    def test_store_facade_begin_stage_if_new_delegates(self, store) -> None:
        """StateStore.begin_stage_if_new produces the same rows as the ops function."""
        task = create_task(store._db, "s", 1, "1.0.0", "wf-test")
        first = store.begin_stage_if_new("evt-1", task.task_id, "plan")
        assert isinstance(first, AttemptRecord)
        second = store.begin_stage_if_new("evt-1", task.task_id, "plan")
        assert second is None
        assert is_event_processed(store._db, "evt-1") is True


class TestArtifacts:
    def test_record_artifact(self, store) -> None:
        task = create_task(store._db, "s", 1, "1.0.0", "wf-test")
        ref = record_artifact(
            store._db, task.task_id, "execute", "file:///tmp/result.json"
        )
        assert ref.task_id == task.task_id
        assert ref.uri == "file:///tmp/result.json"

    def test_store_facade_record_artifact_delegates(self, store) -> None:
        """StateStore.record_artifact produces the same rows as the ops function."""
        task = create_task(store._db, "s", 1, "1.0.0", "wf-test")
        ref = store.record_artifact(task.task_id, "execute", "file:///tmp/facade.json")
        assert isinstance(ref, ArtifactRef)
        assert ref.task_id == task.task_id
        assert ref.uri == "file:///tmp/facade.json"
        assert "file:///tmp/facade.json" in store.get_artifact_uris(task.session_id)


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
        begin_stage_if_new(store._db, "evt-diag-1", task.task_id, "execute")
        begin_stage_if_new(store._db, "evt-diag-2", task.task_id, "execute")
        begin_stage_if_new(store._db, "evt-diag-3", task.task_id, "plan")

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

    def test_fresh_attempt_not_marked_failed(self, workflow_db) -> None:
        """A lease-less attempt stays running (adrrev005 REQ-004: no age fallback)."""
        s = self._open_store(workflow_db)
        try:
            self._insert_task_and_attempt(
                s, "att-fresh", "task-2", "execute", "running", _iso(5)
            )

            s.recover_stale_attempts()

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

            s.recover_stale_attempts()

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

            count = s.recover_stale_attempts()
            assert count == 1

            rows = s._db.fetchall(
                "SELECT status, error_msg FROM attempts WHERE attempt_id='att-lease'"
            )
            assert rows[0][0] == "failed"
            assert "lease expired" in (rows[0][1] or "")
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

            count = s.recover_stale_attempts()
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
                count = s.recover_stale_attempts()
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

            count = s.recover_stale_attempts()
            assert count == 1  # att-tz-legacy is lease-less: live (REQ-004)

            statuses = {
                row[0]: row[1]
                for row in s._db.fetchall(
                    "SELECT attempt_id, status FROM attempts "
                    "WHERE attempt_id IN ('att-tz-legacy', 'att-tz-lease', 'att-tz-live')"
                )
            }
            assert (
                statuses["att-tz-legacy"] == "running"
            )  # lease-less stays live (REQ-004)
            assert statuses["att-tz-lease"] == "failed"
            assert statuses["att-tz-live"] == "running"
            report = s.last_recovery_report
            assert (report.recovered, report.still_live) == (1, 2)
            assert report.unparseable == 0
        finally:
            s.close()

    def test_recovery_marks_only_old_attempts(self, workflow_db) -> None:
        """recover_stale_attempts marks only lease-expired attempts as failed.

        adrrev005 REQ-004: the lease-less legacy age rule is gone, so a lease-less
        row stays running no matter how old it is.
        """
        s = self._open_store(workflow_db)
        try:
            self._insert_task_and_attempt(
                s,
                "att-1",
                "task-1",
                "execute",
                "running",
                _iso(60),
                owner_id="host-a",
                lease_expires_at=_iso(30),
            )
            self._insert_task_and_attempt(
                s, "att-2", "task-2", "execute", "running", _iso(5)
            )

            count = s.recover_stale_attempts()

            assert count == 1
            rows_1 = s._db.fetchall(
                "SELECT status FROM attempts WHERE attempt_id='att-1'"
            )
            assert rows_1[0][0] == "failed"
            rows_2 = s._db.fetchall(
                "SELECT status FROM attempts WHERE attempt_id='att-2'"
            )
            assert rows_2[0][0] == "running"
            assert s.last_recovery_report.still_live == 1
        finally:
            s.close()

    def test_recovered_attempt_has_ended_at_set(self, workflow_db) -> None:
        """A recovered stale attempt has ended_at populated."""
        s = self._open_store(workflow_db)
        try:
            self._insert_task_and_attempt(
                s,
                "att-end",
                "task-4",
                "execute",
                "running",
                _iso(60),
                owner_id="host-a",
                lease_expires_at=_iso(30),
            )

            s.recover_stale_attempts()

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
                "INSERT INTO attempts (attempt_id, task_id, stage_id, status, started_at, owner_id, lease_expires_at)"
                " VALUES (?, ?, ?, 'running', ?, ?, ?)",
                ("att-multi-1", task_id, "execute", old_ts, "host-multi", _iso(60)),
            )
            conn.execute(
                "INSERT INTO attempts (attempt_id, task_id, stage_id, status, started_at, owner_id, lease_expires_at)"
                " VALUES (?, ?, ?, 'running', ?, ?, ?)",
                ("att-multi-2", task_id, "execute", old_ts, "host-multi", _iso(60)),
            )
            conn.commit()
            conn.close()

            count = s.recover_stale_attempts()
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

            count = s.recover_stale_attempts()
            assert count == 0
        finally:
            s.close()


class TestStaleRecoveryConcurrency:
    def test_concurrent_recovery_claims_only_once(self, workflow_db: Path) -> None:
        import sqlite3
        from unittest.mock import patch

        from agent.workflow.state_store import StateStore
        from db.config import DbConfig

        # Setup: create an expired-lease attempt (adrrev005 REQ-004 removed the
        # lease-less legacy age rule: only a stamped, expired lease is recoverable).
        old_ts = _iso(7200)
        expired_lease = _iso(60)

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
            "INSERT INTO attempts (attempt_id, task_id, stage_id, status, started_at, owner_id, lease_expires_at)"
            " VALUES (?, ?, ?, 'running', ?, ?, ?)",
            (attempt_id, task_id, "execute", old_ts, "host-concurrent", expired_lease),
        )
        conn.commit()
        conn.close()

        results = []
        errors = []

        def worker():
            try:
                s = StateStore()
                count = s.recover_stale_attempts()
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
        pending1 = tool_call_state_ops.pending_tool_calls(store._db, t1.task_id)
        assert [c.idempotency_key for c in pending1] == ["key-1"]
        assert pending1[0].state == "pending"
        assert pending1[0].tool == "calculator__calculate"
        assert pending1[0].retry_class == "retryable"
        # Task isolation: the other task sees nothing (completion criterion).
        assert tool_call_state_ops.pending_tool_calls(store._db, t2.task_id) == []

    def test_record_duplicate_key_is_ignored(self, store) -> None:
        task = create_task(store._db, "sess1", 1, "1.0.0", "wf-test")
        store.record_tool_call(
            task.task_id, "key-dup", "deepresearch__search", "retryable"
        )
        store.record_tool_call(
            task.task_id, "key-dup", "deepresearch__search", "retryable"
        )
        assert len(tool_call_state_ops.pending_tool_calls(store._db, task.task_id)) == 1

    def test_finalize_moves_state_and_bumps_updated_at(self, store) -> None:
        task = create_task(store._db, "sess1", 1, "1.0.0", "wf-test")
        store.record_tool_call(
            task.task_id, "key-f", "calculator__calculate", "non_retryable"
        )
        before = tool_call_state_ops.pending_tool_calls(store._db, task.task_id)[0]
        store.finalize_tool_call("key-f", "failed")
        row = tool_call_state_ops.get_tool_call_state(store._db, "key-f")
        assert row is not None and row.state == "failed"
        assert row.updated_at >= before.updated_at
        assert tool_call_state_ops.pending_tool_calls(store._db, task.task_id) == []
        # wfaudit005 REQ-002: out-of-vocabulary state raises and writes nothing.
        with pytest.raises(ValueError, match="invalid tool_call_state.state 'done'"):
            store.finalize_tool_call("key-f", "done")
        row = tool_call_state_ops.get_tool_call_state(store._db, "key-f")
        assert row is not None and row.state == "failed"

    def test_finalize_scoped_key_leaves_other_task_row_pending(self, store) -> None:
        """wfaudit002 REQ-001/REQ-003: task-scoped keys keep per-task rows apart.

        Identical content recorded under both task-suffixed keys: finalizing
        task A's key leaves task B's row pending, and classify_stale_pending
        for A never lists B's row.
        """
        ta = create_task(store._db, "sessA", 1, "1.0.0", "wf-test")
        tb = create_task(store._db, "sessB", 2, "1.0.0", "wf-test")
        key_a = "base-key:" + ta.task_id
        key_b = "base-key:" + tb.task_id
        store.record_tool_call(ta.task_id, key_a, "calculator__calculate", "retryable")
        store.record_tool_call(tb.task_id, key_b, "calculator__calculate", "retryable")
        store.finalize_tool_call(key_a, "completed")
        assert tool_call_state_ops.pending_tool_calls(store._db, ta.task_id) == []
        assert [
            c.idempotency_key
            for c in tool_call_state_ops.pending_tool_calls(store._db, tb.task_id)
        ] == [key_b]
        # Backdate both rows; classifying A must not touch B's pending row.
        store._db.execute(
            "UPDATE tool_call_state SET created_at=?", (time.time() - 120,)
        )
        store._db.commit()
        stale = store.classify_stale_pending(ta.task_id, 60.0)
        assert [c.idempotency_key for c in stale] == []
        assert [
            c.idempotency_key
            for c in tool_call_state_ops.pending_tool_calls(store._db, tb.task_id)
        ] == [key_b]

    def test_pending_ordered_by_created_at(self, store) -> None:
        task = create_task(store._db, "sess1", 1, "1.0.0", "wf-test")
        for i in range(3):
            store.record_tool_call(
                task.task_id, f"key-{i}", "calculator__calculate", "retryable"
            )
            time.sleep(0.01)
        keys = [
            c.idempotency_key
            for c in tool_call_state_ops.pending_tool_calls(store._db, task.task_id)
        ]
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
        assert [
            c.idempotency_key
            for c in tool_call_state_ops.pending_tool_calls(store._db, task.task_id)
        ] == ["fresh"]
        # Idempotent on re-run: nothing transitions twice.
        assert store.classify_stale_pending(task.task_id, 60.0) == []
