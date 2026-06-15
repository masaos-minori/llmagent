# Implementation Plan: State Store (Step 5)

## Goal

Implement `state_store.py` for CRUD operations on `workflow.sqlite` with idempotency checking via `processed_events` table.

## Scope

**In:**
- `scripts/agent/workflow/state_store.py`: Task/attempt/event/artifact CRUD, idempotency check

**Out:**
- Schema definition (handled by workflow_schema.py)
- Workflow engine logic (handled by workflow_engine.py)

## Assumptions

1. `SQLiteHelper(target="workflow")` provides the connection (from Step 1).
2. Idempotency key = `event_id` (unique per stage execution attempt).
3. All DB operations use `SQLiteHelper` context manager pattern (`with SQLiteHelper().open(...) as db:`).
4. Foreign keys enforced via `PRAGMA foreign_keys=ON` in write_mode.

## Implementation

### Target File

| File | Change Type |
|---|---|
| `scripts/agent/workflow/state_store.py` | New |

### Procedure

#### Create `scripts/agent/workflow/state_store.py`

```python
#!/usr/bin/env python3
"""workflow/state_store.py — CRUD and idempotency for workflow.sqlite."""

from __future__ import annotations

import logging
import sqlite3
from dataclasses import dataclass, field
from typing import Any

from agent.workflow.models import AttemptRecord, ArtifactRef, TaskRecord, WorkflowStage

logger = logging.getLogger(__name__)


@dataclass
class IdempotencyCheck:
    """Result of an idempotency lookup."""
    is_duplicate: bool
    artifact_ref: str | None = None


class StateStore:
    """Thread-safe CRUD operations on workflow.sqlite via SQLiteHelper."""

    def __init__(self) -> None:
        self._db_path: str | None = None  # resolved lazily

    def _open_db(self) -> sqlite3.Connection:
        """Open workflow DB connection; resolve path from DbConfig."""
        if self._db_path is None:
            from db.config import build_db_config
            self._db_path = build_db_config().workflow_db_path

        from db.helper import SQLiteHelper
        helper = SQLiteHelper(target="workflow")
        return helper.open(write_mode=True).conn  # type: ignore[return-value]

    def create_task(self, task: TaskRecord) -> None:
        """Insert a new task record. Raises if task_id already exists."""
        conn = self._open_db()
        try:
            conn.execute(
                """INSERT INTO tasks (task_id, session_id, turn_number, workflow_version, status, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    task.task_id,
                    task.session_id,
                    task.turn_number,
                    task.workflow_version,
                    task.status.value,
                    task.created_at,
                    task.updated_at,
                ),
            )
            conn.commit()
        except sqlite3.IntegrityError as e:
            conn.rollback()
            raise ValueError(f"Task {task.task_id} already exists") from e

    def update_task_status(self, task_id: str, status: str) -> None:
        """Update task status and updated_at timestamp."""
        conn = self._open_db()
        conn.execute(
            "UPDATE tasks SET status=?, updated_at=datetime('now') WHERE task_id=?",
            (status, task_id),
        )
        conn.commit()

    def create_attempt(self, attempt: AttemptRecord) -> int:
        """Insert a new attempt record; return attempt_id."""
        conn = self._open_db()
        cursor = conn.execute(
            """INSERT INTO attempts (task_id, stage, status, started_at, completed_at, error_message, attempt_number)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                attempt.task_id,
                attempt.stage.value if isinstance(attempt.stage, WorkflowStage) else attempt.stage,
                attempt.status.value if isinstance(attempt.status, AttemptRecord.__class__.__bases__[0]) else attempt.status,
                attempt.started_at,
                attempt.completed_at,
                attempt.error_message,
                attempt.attempt_number,
            ),
        )
        conn.commit()
        return cursor.lastrowid  # type: ignore[return-value]

    def complete_attempt(self, attempt_id: int, status: str, error: str | None = None) -> None:
        """Mark an attempt as completed/failed with timestamp and optional error."""
        conn = self._open_db()
        conn.execute(
            """UPDATE attempts SET status=?, completed_at=datetime('now'), error_message=?
               WHERE attempt_id=?""",
            (status, error, attempt_id),
        )
        conn.commit()

    def check_idempotency(self, event_id: str) -> IdempotencyCheck:
        """Check if event_id already processed. Returns duplicate status and artifact ref."""
        conn = self._open_db()
        row = conn.execute(
            "SELECT artifact_ref FROM processed_events WHERE event_id=?",
            (event_id,),
        ).fetchone()

        if row is not None:
            return IdempotencyCheck(is_duplicate=True, artifact_ref=row[0])
        return IdempotencyCheck(is_duplicate=False)

    def record_event(self, event_id: str, task_id: str, stage_id: str, artifact_ref: str | None = None) -> None:
        """Record a processed event with optional artifact reference."""
        conn = self._open_db()
        conn.execute(
            "INSERT INTO processed_events (event_id, task_id, stage_id, artifact_ref, processed_at) VALUES (?, ?, ?, ?, datetime('now'))",
            (event_id, task_id, stage_id, artifact_ref),
        )
        conn.commit()

    def save_artifact(self, artifact: ArtifactRef) -> None:
        """Save an artifact reference."""
        conn = self._open_db()
        conn.execute(
            "INSERT INTO artifacts (artifact_id, task_id, stage_id, uri, created_at) VALUES (?, ?, ?, ?, ?)",
            (
                artifact.artifact_id,
                artifact.task_id,
                artifact.stage_id,
                artifact.uri,
                artifact.created_at,
            ),
        )
        conn.commit()

    def get_task(self, task_id: str) -> TaskRecord | None:
        """Fetch a task by ID; returns None if not found."""
        conn = self._open_db()
        row = conn.execute(
            "SELECT task_id, session_id, turn_number, workflow_version, status, created_at, updated_at FROM tasks WHERE task_id=?",
            (task_id,),
        ).fetchone()

        if row is None:
            return None

        from agent.workflow.models import TaskStatus
        return TaskRecord(
            task_id=row[0],
            session_id=row[1],
            turn_number=row[2],
            workflow_version=row[3],
            status=TaskStatus(row[4]),
            created_at=row[5],
            updated_at=row[6],
        )

    def get_task_attempts(self, task_id: str) -> list[AttemptRecord]:
        """Fetch all attempts for a task, ordered by attempt_number."""
        conn = self._open_db()
        rows = conn.execute(
            "SELECT attempt_id, task_id, stage, status, started_at, completed_at, error_message, attempt_number FROM attempts WHERE task_id=? ORDER BY attempt_number",
            (task_id,),
        ).fetchall()

        from agent.workflow.models import AttemptStatus, WorkflowStage
        attempts: list[AttemptRecord] = []
        for row in rows:
            attempts.append(AttemptRecord(
                attempt_id=row[0],
                task_id=row[1],
                stage=WorkflowStage(row[2]),
                status=AttemptStatus(row[3]),
                started_at=row[4],
                completed_at=row[5],
                error_message=row[6],
                attempt_number=row[7],
            ))
        return attempts
```

### Details

- Lazily resolves `db_path` on first DB access (avoids circular import at module load time)
- All mutations commit immediately; transactions managed by caller if atomicity needed
- Idempotency check is a simple SELECT; record_event uses INSERT (fails on duplicate key)
- Error handling: SQLite errors propagate; IntegrityError on duplicate task_id converted to ValueError

## Validation Plan

| Check | Tool | Target |
|---|---|---|
| Type check | `uv run mypy scripts/agent/workflow/state_store.py` | 0 errors |
| Create + fetch task | `store.create_task(t); store.get_task(t.task_id)` | returns same record |
| Idempotency: new event | `check_idempotency("new-id")` | is_duplicate=False |
| Idempotency: duplicate | Record event, then check_idempotency same ID | is_duplicate=True |
| Duplicate task | Create task with same task_id twice | raises ValueError |
