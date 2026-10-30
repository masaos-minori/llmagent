"""tests/agent/workflow/test_workflow_task_transitions.py
Unit tests for the validated task transition API in agent/workflow/task_ops.py.
"""

from __future__ import annotations

import threading
from pathlib import Path
from unittest.mock import patch

import pytest
from agent.workflow.errors import TaskNotFoundError, TaskTransitionError
from agent.workflow.models import TaskRecord
from agent.workflow.task_ops import (
    assert_resumable,
    claim_task,
    create_task,
    get_task_by_id,
    get_task_count,
    get_workflow_count,
    transition_task,
)
from db.config import DbConfig
from db.create_schema import create_workflow_schema
from db.helper import SQLiteHelper


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


def _status(store, task_id: str) -> str:
    found = get_task_by_id(store._db, task_id)
    assert found is not None
    return found.status


class TestTransitionTask:
    def test_allowed_transition_updates_status(self, store) -> None:
        task = create_task(store._db, "s", 1, "1.0.0", "wf")
        transition_task(store._db, task.task_id, "running")
        assert _status(store, task.task_id) == "running"

    def test_disallowed_transition_raises_and_keeps_status(self, store) -> None:
        task = create_task(store._db, "s", 1, "1.0.0", "wf")
        with pytest.raises(TaskTransitionError, match="pending"):
            transition_task(store._db, task.task_id, "completed")
        assert _status(store, task.task_id) == "pending"

    def test_unknown_status_raises(self, store) -> None:
        task = create_task(store._db, "s", 1, "1.0.0", "wf")
        with pytest.raises(TaskTransitionError):
            transition_task(store._db, task.task_id, "bogus")

    def test_unknown_task_raises_not_found(self, store) -> None:
        with pytest.raises(TaskNotFoundError):
            transition_task(store._db, "missing", "running")

    def test_expected_mismatch_raises(self, store) -> None:
        task = create_task(store._db, "s", 1, "1.0.0", "wf")
        with pytest.raises(TaskTransitionError):
            transition_task(store._db, task.task_id, "running", expected="failed")

    def test_halted_is_terminal(self, store) -> None:
        task = create_task(store._db, "s", 1, "1.0.0", "wf")
        transition_task(store._db, task.task_id, "halted")
        with pytest.raises(TaskTransitionError, match="halted"):
            transition_task(store._db, task.task_id, "running")


class TestClaimTask:
    @pytest.mark.parametrize("status", ["pending", "failed"])
    def test_claimable_statuses(self, store, status: str) -> None:
        task = create_task(store._db, "s", 1, "1.0.0", "wf")
        if status == "failed":
            transition_task(store._db, task.task_id, "running")
            transition_task(store._db, task.task_id, "failed")
        claim_task(store._db, task.task_id)
        assert _status(store, task.task_id) == "running"

    @pytest.mark.parametrize("status", ["running", "completed", "halted"])
    def test_rejected_statuses(self, store, status: str) -> None:
        task = create_task(store._db, "s", 1, "1.0.0", "wf")
        if status == "halted":
            transition_task(store._db, task.task_id, "halted")
        else:
            transition_task(store._db, task.task_id, "running")
            if status == "completed":
                transition_task(store._db, task.task_id, "completed")
        with pytest.raises(TaskTransitionError, match=status):
            claim_task(store._db, task.task_id)
        assert _status(store, task.task_id) == status

    def test_two_connections_one_winner(self, store, workflow_db: Path) -> None:
        task = create_task(store._db, "s", 1, "1.0.0", "wf")
        results: list[str] = []

        def _claim() -> None:
            with patch(
                "db.helper.build_db_config", return_value=_make_cfg(str(workflow_db))
            ):
                db = SQLiteHelper(target="workflow")
                db.open(write_mode=True, row_factory=True)
            try:
                claim_task(db, task.task_id)
                results.append("won")
            except TaskTransitionError:
                results.append("lost")
            finally:
                db.close()

        threads = [threading.Thread(target=_claim) for _ in range(2)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert sorted(results) == ["lost", "won"]


class TestAssertResumable:
    def _record(self, status: str) -> TaskRecord:
        return TaskRecord(
            task_id="t1",
            session_id="s",
            turn_number=1,
            workflow_version="1.0.0",
            status=status,
            task_nonce="k",
            created_at="2026-01-01T00:00:00+00:00",
            updated_at="2026-01-01T00:00:00+00:00",
        )

    @pytest.mark.parametrize("status", ["pending", "failed"])
    def test_accepts_claimable(self, status: str) -> None:
        assert_resumable(self._record(status))

    @pytest.mark.parametrize("status", ["running", "completed", "halted"])
    def test_rejects_others_naming_status(self, status: str) -> None:
        with pytest.raises(TaskTransitionError, match=status):
            assert_resumable(self._record(status))


class TestTaskCounts:
    def test_counts_by_session(self, store) -> None:
        create_task(store._db, "a", 1, "1.0.0", "wf-1")
        create_task(store._db, "a", 2, "1.0.0", "wf-1")
        create_task(store._db, "a", 3, "1.0.0", "wf-2")
        create_task(store._db, "b", 1, "1.0.0", "wf-1")
        assert get_task_count(store._db, "a") == 3
        assert get_workflow_count(store._db, "a") == 2
        assert get_task_count(store._db, "none") == 0
