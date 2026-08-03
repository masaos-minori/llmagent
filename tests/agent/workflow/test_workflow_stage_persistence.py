"""tests/test_workflow_stage_persistence.py
Tests for workflow stage persistence: error_kind, error_detail, workflow_id, attempt_number.
"""

from __future__ import annotations

import sqlite3
import uuid

import pytest
from agent.workflow.artifact_ops import record_artifact
from agent.workflow.attempt_ops import finish_attempt, start_attempt
from agent.workflow.idempotency_ops import begin_stage_if_new
from db.helper import SQLiteHelper
from db.schema_sql import apply_workflow_migrations, build_workflow_schema_sql


@pytest.fixture
def db():
    helper = SQLiteHelper(db_path=":memory:")
    helper.open(write_mode=True)
    helper.executescript(build_workflow_schema_sql())
    yield helper
    helper.close()


def _insert_task(db: SQLiteHelper, workflow_id: str = "wf-test-1") -> str:
    task_id = str(uuid.uuid4())
    db.execute(
        "INSERT INTO tasks (task_id, workflow_id, workflow_version, status, idempotency_key)"
        " VALUES (?, ?, '1.0.0', 'running', ?)",
        (task_id, workflow_id, task_id),
    )
    db.commit()
    return task_id


# --- error_kind and error_detail in attempts ---


def test_finish_attempt_persists_error_kind(db: SQLiteHelper) -> None:
    task_id = _insert_task(db)
    rec = start_attempt(db, task_id, "stage1")
    finish_attempt(
        db,
        rec.attempt_id,
        "failed",
        error_msg="timed out",
        error_kind="timeout",
        error_detail="TimeoutError()",
    )
    row = db.execute(
        "SELECT error_kind, error_detail FROM attempts WHERE attempt_id=?",
        (rec.attempt_id,),
    ).fetchone()
    assert row[0] == "timeout"
    assert row[1] == "TimeoutError()"


def test_finish_attempt_null_error_kind_by_default(db: SQLiteHelper) -> None:
    task_id = _insert_task(db)
    rec = start_attempt(db, task_id, "stage1")
    finish_attempt(db, rec.attempt_id, "completed")
    row = db.execute(
        "SELECT error_kind, error_detail FROM attempts WHERE attempt_id=?",
        (rec.attempt_id,),
    ).fetchone()
    assert row[0] is None
    assert row[1] is None


def test_finish_attempt_exception_kind(db: SQLiteHelper) -> None:
    task_id = _insert_task(db)
    rec = start_attempt(db, task_id, "stage1")
    finish_attempt(
        db,
        rec.attempt_id,
        "failed",
        error_kind="exception",
        error_detail="ValueError('bad state')",
    )
    row = db.execute(
        "SELECT error_kind FROM attempts WHERE attempt_id=?", (rec.attempt_id,)
    ).fetchone()
    assert row[0] == "exception"


# --- workflow_id and attempt_number in artifacts ---


def test_record_artifact_with_workflow_id_and_attempt(db: SQLiteHelper) -> None:
    task_id = _insert_task(db, workflow_id="wf-art-test")
    ref = record_artifact(
        db,
        task_id,
        "stage1",
        "file:///out.txt",
        workflow_id="wf-art-test",
        attempt_number=2,
    )
    row = db.execute(
        "SELECT workflow_id, attempt_number FROM artifacts WHERE artifact_id=?",
        (ref.artifact_id,),
    ).fetchone()
    assert row[0] == "wf-art-test"
    assert row[1] == 2


def test_record_artifact_null_fields_by_default(db: SQLiteHelper) -> None:
    task_id = _insert_task(db)
    ref = record_artifact(db, task_id, "stage1", "file:///out.txt")
    row = db.execute(
        "SELECT workflow_id, attempt_number FROM artifacts WHERE artifact_id=?",
        (ref.artifact_id,),
    ).fetchone()
    assert row[0] is None
    assert row[1] is None


# --- workflow_id in processed_events ---


def test_begin_stage_if_new_persists_workflow_id(db: SQLiteHelper) -> None:
    task_id = _insert_task(db, workflow_id="wf-idp-test")
    event_id = str(uuid.uuid4())
    result = begin_stage_if_new(
        db, event_id, task_id, "stage1", workflow_id="wf-idp-test"
    )
    assert result is not None
    row = db.execute(
        "SELECT workflow_id FROM processed_events WHERE event_id=?", (event_id,)
    ).fetchone()
    assert row[0] == "wf-idp-test"


def test_begin_stage_if_new_idempotent(db: SQLiteHelper) -> None:
    task_id = _insert_task(db)
    event_id = str(uuid.uuid4())
    first = begin_stage_if_new(db, event_id, task_id, "stage1")
    second = begin_stage_if_new(db, event_id, task_id, "stage1")
    assert first is not None
    assert second is None


# --- Migration scenario ---


def test_migration_adds_columns_to_existing_db() -> None:
    conn = sqlite3.connect(":memory:")
    conn.execute(
        "CREATE TABLE attempts (attempt_id TEXT PRIMARY KEY, task_id TEXT, stage_id TEXT,"
        " status TEXT, started_at TEXT, ended_at TEXT, error_msg TEXT)"
    )
    conn.execute(
        "CREATE TABLE artifacts (artifact_id TEXT PRIMARY KEY, task_id TEXT, stage_id TEXT, uri TEXT, created_at TEXT)"
    )
    conn.execute(
        "CREATE TABLE processed_events (event_id TEXT PRIMARY KEY, task_id TEXT, stage_id TEXT, recorded_at TEXT)"
    )
    conn.commit()
    apply_workflow_migrations(conn)
    cols_attempts = {
        row[1] for row in conn.execute("PRAGMA table_info(attempts)").fetchall()
    }
    cols_artifacts = {
        row[1] for row in conn.execute("PRAGMA table_info(artifacts)").fetchall()
    }
    cols_events = {
        row[1] for row in conn.execute("PRAGMA table_info(processed_events)").fetchall()
    }
    assert "error_kind" in cols_attempts
    assert "error_detail" in cols_attempts
    assert "workflow_id" in cols_artifacts
    assert "attempt_number" in cols_artifacts
    assert "workflow_id" in cols_events


def test_migration_idempotent() -> None:
    conn = sqlite3.connect(":memory:")
    conn.executescript(build_workflow_schema_sql())
    apply_workflow_migrations(conn)  # should not raise when columns already exist
