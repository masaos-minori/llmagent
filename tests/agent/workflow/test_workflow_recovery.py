"""tests/agent/workflow/test_workflow_recovery.py

Crash, restart, and resume regression tests against a real workflow database: a crash
leaves nothing that suppresses a re-run, recovery is repeatable, and only a pending or
failed task can be resumed.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from agent.workflow.errors import TaskTransitionError
from agent.workflow.idempotency_ops import begin_stage_if_new, is_stage_completed
from agent.workflow.state_store import StateStore
from agent.workflow.task_ops import assert_resumable, create_task, get_task_by_id
from db.helper import SQLiteHelper
from db.schema_sql import build_workflow_schema_sql

_OLD = "2026-08-01T10:00:00"


@pytest.fixture
def db() -> Iterator[SQLiteHelper]:
    helper = SQLiteHelper(db_path=":memory:")
    helper.open(write_mode=True, row_factory=True)
    helper.executescript(build_workflow_schema_sql())
    yield helper
    helper.close()


def _age_running_attempts(db: SQLiteHelper) -> None:
    db.execute("UPDATE attempts SET started_at=? WHERE status='running'", (_OLD,))
    db.commit()


def _recover(db: SQLiteHelper) -> int:
    return StateStore.__new__(StateStore).recover_stale_attempts(db)


def test_crash_after_the_attempt_row_does_not_suppress_the_rerun(
    db: SQLiteHelper,
) -> None:
    task = create_task(db, "s", 1, "1", "wf")
    db.execute("UPDATE tasks SET status='running' WHERE task_id=?", (task.task_id,))
    db.commit()
    crashed = begin_stage_if_new(db, task.task_id, "plan")
    assert crashed is not None  # the process dies here: no finish, no ledger row
    assert not is_stage_completed(db, task.task_id, "plan")

    _age_running_attempts(db)
    assert _recover(db) == 1
    assert get_task_by_id(db, task.task_id).status == "failed"

    rerun = begin_stage_if_new(db, task.task_id, "plan")
    assert rerun is not None
    assert rerun.attempt_number == 2


def test_repeated_restart_and_recovery_is_stable(db: SQLiteHelper) -> None:
    task = create_task(db, "s", 1, "1", "wf")
    db.execute("UPDATE tasks SET status='running' WHERE task_id=?", (task.task_id,))
    db.commit()
    begin_stage_if_new(db, task.task_id, "execute")
    _age_running_attempts(db)
    results = [_recover(db), _recover(db), _recover(db)]
    assert results == [1, 0, 0]
    rows = db.fetchall("SELECT status FROM attempts WHERE task_id=?", (task.task_id,))
    assert [r["status"] for r in rows] == ["failed"]


def test_side_effect_before_the_finish_is_retried_with_a_new_number(
    db: SQLiteHelper,
) -> None:
    task = create_task(db, "s", 1, "1", "wf")
    db.execute("UPDATE tasks SET status='running' WHERE task_id=?", (task.task_id,))
    db.commit()
    first = begin_stage_if_new(db, task.task_id, "execute")
    assert first is not None  # the side effect ran, then the process died
    _age_running_attempts(db)
    _recover(db)
    second = begin_stage_if_new(db, task.task_id, "execute")
    assert second is not None
    assert (first.attempt_number, second.attempt_number) == (1, 2)


@pytest.mark.parametrize("status", ["running", "completed", "halted"])
def test_resume_is_rejected_for_a_task_that_cannot_resume(
    db: SQLiteHelper, status: str
) -> None:
    task = create_task(db, "s", 1, "1", "wf")
    db.execute("UPDATE tasks SET status=? WHERE task_id=?", (status, task.task_id))
    db.commit()
    fetched = get_task_by_id(db, task.task_id)
    assert fetched is not None
    with pytest.raises(TaskTransitionError, match=status):
        assert_resumable(fetched)


@pytest.mark.parametrize("status", ["pending", "failed"])
def test_resume_is_allowed_for_pending_and_failed_tasks(
    db: SQLiteHelper, status: str
) -> None:
    task = create_task(db, "s", 1, "1", "wf")
    db.execute("UPDATE tasks SET status=? WHERE task_id=?", (status, task.task_id))
    db.commit()
    fetched = get_task_by_id(db, task.task_id)
    assert fetched is not None
    assert_resumable(fetched)
