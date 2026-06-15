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
def workflow_db(tmp_path: Path) -> str:
    db_path = str(tmp_path / "workflow.sqlite")
    init_schema(db_path)
    return db_path


@pytest.fixture()
def store(workflow_db: str):
    from agent.workflow.state_store import StateStore

    with patch("db.helper.build_db_config", return_value=_make_cfg(workflow_db)):
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
