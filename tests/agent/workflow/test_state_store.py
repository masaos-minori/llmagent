#!/usr/bin/env python3
"""tests/test_state_store.py

Tests for recover_stale_attempts(): atomic per-attempt recovery and its conditional
(race-safe) transitions, against a real workflow database.
"""

from collections.abc import Iterator
from unittest.mock import MagicMock

import pytest
from agent.workflow.state_store import StateStore
from db.helper import SQLiteHelper
from db.schema_sql import build_workflow_schema_sql

_STALE = "2026-08-01T10:00:00"


@pytest.fixture
def db() -> Iterator[SQLiteHelper]:
    helper = SQLiteHelper(db_path=":memory:")
    helper.open(write_mode=True, row_factory=True)
    helper.executescript(build_workflow_schema_sql())
    yield helper
    helper.close()


def _add_task(db: SQLiteHelper, task_id: str = "t1", status: str = "running") -> None:
    db.execute(
        "INSERT INTO tasks (task_id, workflow_version, status, task_nonce)"
        " VALUES (?, '1', ?, ?)",
        (task_id, status, task_id),
    )
    db.commit()


def _add_attempt(
    db: SQLiteHelper,
    attempt_id: str,
    task_id: str = "t1",
    stage_id: str = "execute",
    number: int = 1,
    status: str = "running",
) -> None:
    db.execute(
        "INSERT INTO attempts (attempt_id, task_id, stage_id, status, started_at,"
        " attempt_number) VALUES (?, ?, ?, ?, ?, ?)",
        (attempt_id, task_id, stage_id, status, _STALE, number),
    )
    db.commit()


def _status(db: SQLiteHelper, table: str, key: str, value: str) -> str:
    rows = db.fetchall(f"SELECT status FROM {table} WHERE {key}=?", (value,))  # nosec B608 — fixed test literals
    return str(rows[0]["status"])


def _store() -> StateStore:
    return StateStore.__new__(StateStore)


def test_stale_attempt_and_its_task_are_failed_together(db: SQLiteHelper) -> None:
    _add_task(db)
    _add_attempt(db, "a1")
    assert _store().recover_stale_attempts(db) == 1
    assert _status(db, "attempts", "attempt_id", "a1") == "failed"
    assert _status(db, "tasks", "task_id", "t1") == "failed"
    kind = db.fetchall("SELECT error_kind FROM attempts WHERE attempt_id='a1'")
    assert kind[0]["error_kind"] == "stale_recovered"


def test_repeated_recovery_changes_nothing(db: SQLiteHelper) -> None:
    _add_task(db)
    _add_attempt(db, "a1")
    store = _store()
    assert store.recover_stale_attempts(db) == 1
    assert store.recover_stale_attempts(db) == 0
    assert _status(db, "tasks", "task_id", "t1") == "failed"


def test_task_stays_running_while_another_attempt_runs(db: SQLiteHelper) -> None:
    _add_task(db)
    _add_attempt(db, "a1", stage_id="plan")
    _add_attempt(db, "a2", stage_id="execute")
    store = _store()
    # Only a1 is reported stale; a2 keeps the task running.
    store.find_stale_running_attempts = lambda _db: [  # type: ignore[method-assign] — narrow the detection for this case
        {"attempt_id": "a1", "started_at": _STALE, "elapsed_sec": 60.0}
    ]
    assert store.recover_stale_attempts(db) == 1
    assert _status(db, "attempts", "attempt_id", "a1") == "failed"
    assert _status(db, "attempts", "attempt_id", "a2") == "running"
    assert _status(db, "tasks", "task_id", "t1") == "running"


def test_non_running_task_status_is_left_alone(db: SQLiteHelper) -> None:
    _add_task(db, status="halted")
    _add_attempt(db, "a1")
    assert _store().recover_stale_attempts(db) == 1
    assert _status(db, "tasks", "task_id", "t1") == "halted"


def test_lost_race_is_skipped_not_counted(db: SQLiteHelper) -> None:
    _add_task(db)
    _add_attempt(db, "a1")
    store = _store()
    # The same attempt is reported twice, as two racing recoverers would see it.
    entry = {"attempt_id": "a1", "started_at": _STALE, "elapsed_sec": 60.0}
    store.find_stale_running_attempts = lambda _db: [entry, entry]  # type: ignore[method-assign] — simulate the race
    assert store.recover_stale_attempts(db) == 1


def test_no_stale_attempts_runs_no_write(db: SQLiteHelper) -> None:
    store = _store()
    store.find_stale_running_attempts = lambda _db: []  # type: ignore[method-assign] — no stale attempt
    spy = MagicMock(wraps=db.execute)
    db.execute = spy  # type: ignore[method-assign] — assert that no statement runs
    assert store.recover_stale_attempts(db) == 0
    spy.assert_not_called()


def test_recovery_leaves_the_database_valid(db: SQLiteHelper) -> None:
    _add_task(db)
    _add_attempt(db, "a1")
    _store().recover_stale_attempts(db)
    assert db.fetchall("PRAGMA foreign_key_check") == []
