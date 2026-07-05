# Implementation: tests/test_workflow_stage_persistence.py — Workflow stage persistence tests

## Goal

Verify that `error_kind`, `error_detail`, `workflow_id`, and `attempt_number` are persisted correctly after stage failures and artifact creation.

## Scope

**In**: Integration tests using in-memory SQLite via `SQLiteHelper(":memory:")`. Tests for `finish_attempt()`, `record_artifact()`, `begin_stage_if_new()`.

**Out**: Source file changes.

## Assumptions

1. `schema_sql.py` and ops files are updated first.
2. Tests use an in-memory DB initialized with the new schema.
3. Helper `make_db()` fixture creates in-memory DB and runs schema creation.
4. `TaskRecord` can be instantiated for test purposes.

## Implementation

### Target file
`tests/test_workflow_stage_persistence.py`

### Procedure
Write pytest tests for each new field, covering both fresh DB and migration scenarios.

### Method

```python
import pytest
import sqlite3
from scripts.db.helper import SQLiteHelper
from scripts.db.schema_sql import create_workflow_schema
from scripts.agent.workflow.attempt_ops import finish_attempt, begin_attempt
from scripts.agent.workflow.artifact_ops import record_artifact
from scripts.agent.workflow.idempotency_ops import begin_stage_if_new
import uuid


@pytest.fixture
def db():
    conn = sqlite3.connect(":memory:")
    helper = SQLiteHelper.__new__(SQLiteHelper)
    helper._conn = conn
    create_workflow_schema(conn)
    return helper


def _insert_task(db, workflow_id: str = "wf-test-1") -> str:
    task_id = str(uuid.uuid4())
    db.execute(
        "INSERT INTO tasks (task_id, workflow_id, status, created_at) VALUES (?, ?, 'running', '2026-01-01T00:00:00Z')",
        (task_id, workflow_id),
    )
    db.commit()
    return task_id


# --- error_kind and error_detail in attempts ---

def test_finish_attempt_persists_error_kind(db):
    task_id = _insert_task(db)
    attempt_id = str(uuid.uuid4())
    db.execute(
        "INSERT INTO attempts (attempt_id, task_id, stage_id, status, started_at) VALUES (?, ?, 'stage1', 'running', '2026-01-01T00:00:00Z')",
        (attempt_id, task_id),
    )
    db.commit()
    finish_attempt(db, attempt_id, "failed", error_msg="timed out", error_kind="timeout", error_detail="TimeoutError()")
    row = db.execute("SELECT error_kind, error_detail FROM attempts WHERE attempt_id=?", (attempt_id,)).fetchone()
    assert row[0] == "timeout"
    assert row[1] == "TimeoutError()"


def test_finish_attempt_null_error_kind_by_default(db):
    task_id = _insert_task(db)
    attempt_id = str(uuid.uuid4())
    db.execute(
        "INSERT INTO attempts (attempt_id, task_id, stage_id, status, started_at) VALUES (?, ?, 'stage1', 'running', '2026-01-01T00:00:00Z')",
        (attempt_id, task_id),
    )
    db.commit()
    finish_attempt(db, attempt_id, "completed")
    row = db.execute("SELECT error_kind, error_detail FROM attempts WHERE attempt_id=?", (attempt_id,)).fetchone()
    assert row[0] is None
    assert row[1] is None


def test_finish_attempt_exception_kind(db):
    task_id = _insert_task(db)
    attempt_id = str(uuid.uuid4())
    db.execute(
        "INSERT INTO attempts (attempt_id, task_id, stage_id, status, started_at) VALUES (?, ?, 'stage1', 'running', '2026-01-01T00:00:00Z')",
        (attempt_id, task_id),
    )
    db.commit()
    finish_attempt(db, attempt_id, "failed", error_kind="exception", error_detail="ValueError('bad state')")
    row = db.execute("SELECT error_kind FROM attempts WHERE attempt_id=?", (attempt_id,)).fetchone()
    assert row[0] == "exception"


# --- workflow_id and attempt_number in artifacts ---

def test_record_artifact_with_workflow_id_and_attempt(db):
    task_id = _insert_task(db, workflow_id="wf-art-test")
    ref = record_artifact(db, task_id, "stage1", "file:///out.txt", workflow_id="wf-art-test", attempt_number=2)
    row = db.execute(
        "SELECT workflow_id, attempt_number FROM artifacts WHERE artifact_id=?", (ref.artifact_id,)
    ).fetchone()
    assert row[0] == "wf-art-test"
    assert row[1] == 2


def test_record_artifact_null_fields_by_default(db):
    task_id = _insert_task(db)
    ref = record_artifact(db, task_id, "stage1", "file:///out.txt")
    row = db.execute(
        "SELECT workflow_id, attempt_number FROM artifacts WHERE artifact_id=?", (ref.artifact_id,)
    ).fetchone()
    assert row[0] is None
    assert row[1] is None


# --- workflow_id in processed_events ---

def test_begin_stage_if_new_persists_workflow_id(db):
    task_id = _insert_task(db, workflow_id="wf-idp-test")
    event_id = str(uuid.uuid4())
    result = begin_stage_if_new(db, event_id, task_id, "stage1", workflow_id="wf-idp-test")
    assert result is not None
    row = db.execute(
        "SELECT workflow_id FROM processed_events WHERE event_id=?", (event_id,)
    ).fetchone()
    assert row[0] == "wf-idp-test"


def test_begin_stage_if_new_idempotent(db):
    task_id = _insert_task(db)
    event_id = str(uuid.uuid4())
    first = begin_stage_if_new(db, event_id, task_id, "stage1")
    second = begin_stage_if_new(db, event_id, task_id, "stage1")
    assert first is not None
    assert second is None  # idempotent: returns None on duplicate


# --- Migration scenario ---

def test_migration_adds_columns_to_existing_db():
    conn = sqlite3.connect(":memory:")
    # Create old schema without new columns
    conn.execute(
        "CREATE TABLE attempts (attempt_id TEXT PRIMARY KEY, task_id TEXT, stage_id TEXT, status TEXT, started_at TEXT, ended_at TEXT, error_msg TEXT)"
    )
    conn.execute(
        "CREATE TABLE artifacts (artifact_id TEXT PRIMARY KEY, task_id TEXT, stage_id TEXT, uri TEXT, created_at TEXT)"
    )
    conn.execute(
        "CREATE TABLE processed_events (event_id TEXT PRIMARY KEY, task_id TEXT, stage_id TEXT, recorded_at TEXT)"
    )
    conn.commit()
    # Run migrations
    from scripts.db.schema_sql import apply_workflow_migrations
    apply_workflow_migrations(conn)
    # Check new columns exist
    cols_attempts = {row[1] for row in conn.execute("PRAGMA table_info(attempts)").fetchall()}
    cols_artifacts = {row[1] for row in conn.execute("PRAGMA table_info(artifacts)").fetchall()}
    cols_events = {row[1] for row in conn.execute("PRAGMA table_info(processed_events)").fetchall()}
    assert "error_kind" in cols_attempts
    assert "error_detail" in cols_attempts
    assert "workflow_id" in cols_artifacts
    assert "attempt_number" in cols_artifacts
    assert "workflow_id" in cols_events


def test_migration_idempotent():
    conn = sqlite3.connect(":memory:")
    from scripts.db.schema_sql import create_workflow_schema, apply_workflow_migrations
    create_workflow_schema(conn)  # creates with new columns
    apply_workflow_migrations(conn)  # should not fail when columns already exist
```

## Validation plan

- `uv run pytest tests/test_workflow_stage_persistence.py -v` — all pass.
- `ruff check tests/test_workflow_stage_persistence.py` — 0 errors.
