"""tests/agent/workflow/test_workflow_concurrency.py

Two-connection tests: a task claim has one winner and attempt numbering never collides.
"""

from __future__ import annotations

import sqlite3
import threading
from collections.abc import Callable
from pathlib import Path

import pytest
from agent.workflow.errors import StageAlreadyRunningError, TaskTransitionError
from agent.workflow.idempotency_ops import begin_stage_if_new
from agent.workflow.task_ops import claim_task, create_task
from db.helper import SQLiteHelper
from db.schema_sql import build_workflow_schema_sql


@pytest.fixture
def db_path(tmp_path: Path) -> str:
    path = str(tmp_path / "workflow.sqlite")
    conn = sqlite3.connect(path)
    conn.executescript(build_workflow_schema_sql())
    conn.close()
    return path


def _open(path: str) -> SQLiteHelper:
    helper = SQLiteHelper(db_path=path, check_same_thread=False)
    helper.open(write_mode=True, row_factory=True)
    return helper


def _race(path: str, work: Callable[[SQLiteHelper], object]) -> list[object]:
    """Run `work` on two connections at once; return each outcome (value or error)."""
    barrier = threading.Barrier(2)
    outcomes: list[object] = [None, None]

    def run(index: int) -> None:
        helper = _open(path)
        try:
            barrier.wait()
            outcomes[index] = work(helper)
        except (TaskTransitionError, StageAlreadyRunningError) as exc:
            outcomes[index] = exc
        finally:
            helper.close()

    threads = [threading.Thread(target=run, args=(i,)) for i in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    return outcomes


def test_two_connections_claim_a_task_with_one_winner(db_path: str) -> None:
    helper = _open(db_path)
    task = create_task(helper, "s", 1, "1", "wf")
    helper.close()

    def work(db: SQLiteHelper) -> object:
        claim_task(db, task.task_id)
        return "claimed"

    outcomes = _race(db_path, work)
    assert sorted(type(o).__name__ for o in outcomes) == ["TaskTransitionError", "str"]


def test_two_connections_never_share_an_attempt_number(db_path: str) -> None:
    helper = _open(db_path)
    task = create_task(helper, "s", 1, "1", "wf")
    helper.close()

    def work(db: SQLiteHelper) -> object:
        record = begin_stage_if_new(db, task.task_id, "execute")
        return None if record is None else record.attempt_number

    outcomes = _race(db_path, work)
    # One start wins with number 1; the other sees the running attempt and is refused.
    assert 1 in outcomes
    assert sum(isinstance(o, StageAlreadyRunningError) for o in outcomes) == 1
    check = _open(db_path)
    rows = check.fetchall("SELECT attempt_number FROM attempts")
    check.close()
    assert [r["attempt_number"] for r in rows] == [1]
