"""tests/agent/workflow/test_workflow_status_vocabulary.py

Status vocabulary contract tests (wfaudit005 REQ-001/REQ-002/REQ-004).

- Exact membership of the three frozensets in agent/workflow/models.py.
- Per-helper rejection: out-of-vocabulary writes raise ValueError and change
  no row (update_task_status, finish_attempt, finalize_tool_call).
- Writer consistency: the known writer literal list stays inside the
  vocabularies (static assertion list, not a runtime grep).

The DDL-vs-constants equality test lives in tests/db/test_create_schema.py.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from agent.workflow import tool_call_state_ops
from agent.workflow.attempt_ops import finish_attempt
from agent.workflow.idempotency_ops import begin_stage_if_new
from agent.workflow.models import ATTEMPT_STATUSES, TASK_STATUSES, TOOL_CALL_STATES
from agent.workflow.task_ops import create_task, get_task_by_id, update_task_status
from db.config import DbConfig
from db.create_schema import create_workflow_schema

# Known writer literals per table (re-verified at HEAD 11c20696a):
# tasks: workflow_engine writes running/halted/failed/completed; DDL default
#   pending (create_task).
# attempts: idempotency_ops INSERT running; recovery UPDATE failed
#   (state_store.py); finish_attempt completed/failed.
# tool_call_state: record_tool_call INSERT pending; tool_runner passes
#   failed/completed through the recorder facade; classify_stale_pending
#   writes interrupted via its own guarded UPDATE.
KNOWN_WRITER_STATUSES: dict[str, set[str]] = {
    "tasks": {"pending", "running", "halted", "failed", "completed"},
    "attempts": {"running", "failed", "completed"},
    "tool_call_state": {"pending", "completed", "failed", "interrupted"},
}


def _make_cfg(db_path: str) -> DbConfig:
    return DbConfig(
        rag_db_path="/tmp/opencode/wfaudit005_rag.sqlite",
        session_db_path="/tmp/opencode/wfaudit005_session.sqlite",
        workflow_db_path=db_path,
    )


@pytest.fixture()
def workflow_db(tmp_path: Path) -> Path:
    db_path = tmp_path / "workflow.sqlite"
    with patch(
        "db.helper.build_db_config",
        return_value=_make_cfg(str(db_path)),
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


class TestVocabularyMembership:
    """REQ-001: the three frozensets exist with exact membership."""

    def test_task_statuses_exact(self) -> None:
        assert TASK_STATUSES == frozenset(
            {"pending", "running", "completed", "failed", "halted"}
        )

    def test_attempt_statuses_exact(self) -> None:
        assert ATTEMPT_STATUSES == frozenset({"running", "completed", "failed"})

    def test_tool_call_states_exact(self) -> None:
        assert TOOL_CALL_STATES == frozenset(
            {"pending", "completed", "failed", "interrupted"}
        )


class TestWriterConsistency:
    """REQ-004: every known writer literal is vocabulary-valid."""

    def test_task_writer_literals_are_valid(self) -> None:
        assert KNOWN_WRITER_STATUSES["tasks"] <= TASK_STATUSES

    def test_attempt_writer_literals_are_valid(self) -> None:
        assert KNOWN_WRITER_STATUSES["attempts"] <= ATTEMPT_STATUSES

    def test_tool_call_writer_literals_are_valid(self) -> None:
        assert KNOWN_WRITER_STATUSES["tool_call_state"] <= TOOL_CALL_STATES


class TestHelperRejection:
    """REQ-002: each writer helper rejects out-of-vocabulary values, no write."""

    def test_update_task_status_rejects_and_writes_nothing(self, store) -> None:
        task = create_task(store._db, "sess1", 1, "1.0.0", "wf-test")
        update_task_status(store._db, task.task_id, "running")
        with pytest.raises(ValueError, match="invalid tasks.status 'done'"):
            update_task_status(store._db, task.task_id, "done")
        found = get_task_by_id(store._db, task.task_id)
        assert found is not None
        assert found.status == "running"

    def test_finish_attempt_rejects_and_writes_nothing(self, store) -> None:
        task = create_task(store._db, "sess1", 1, "1.0.0", "wf-test")
        attempt = begin_stage_if_new(store._db, "evt-vocab-1", task.task_id, "plan")
        assert attempt is not None
        finish_attempt(store._db, attempt.attempt_id, "completed")
        with pytest.raises(ValueError, match="invalid attempts.status 'done'"):
            finish_attempt(store._db, attempt.attempt_id, "done")
        rows = store._db.fetchall(
            "SELECT status FROM attempts WHERE attempt_id=?", (attempt.attempt_id,)
        )
        assert rows[0][0] == "completed"

    def test_finalize_tool_call_rejects_and_writes_nothing(self, store) -> None:
        task = create_task(store._db, "sess1", 1, "1.0.0", "wf-test")
        store.record_tool_call(
            task.task_id, "key-v", "calculator__calculate", "retryable"
        )
        store.finalize_tool_call("key-v", "completed")
        with pytest.raises(ValueError, match="invalid tool_call_state.state 'done'"):
            store.finalize_tool_call("key-v", "done")
        row = tool_call_state_ops.get_tool_call_state(store._db, "key-v")
        assert row is not None
        assert row.state == "completed"


class TestUpdateTaskStatusCommitFlag:
    """wfaudit007 (135741_02): commit=False defers the commit to the caller."""

    def test_commit_false_skips_commit_but_writes_in_transaction(self, store) -> None:
        task = create_task(store._db, "sess1", 1, "1.0.0", "wf-test")
        commits: list[int] = []
        real_commit = store._db.commit
        store._db.commit = lambda: (commits.append(1), real_commit())[1]
        try:
            update_task_status(store._db, task.task_id, "failed", commit=False)
        finally:
            store._db.commit = real_commit
        assert commits == []
        # Visible on the same (open) connection before any commit.
        found = get_task_by_id(store._db, task.task_id)
        assert found is not None
        assert found.status == "failed"
        store._db.commit()

    def test_default_still_commits(self, store) -> None:
        task = create_task(store._db, "sess1", 1, "1.0.0", "wf-test")
        update_task_status(store._db, task.task_id, "running")
        # A fresh connection sees the committed row.
        import sqlite3

        conn = sqlite3.connect(str(store._db._db_path))
        try:
            row = conn.execute(
                "SELECT status FROM tasks WHERE task_id=?", (task.task_id,)
            ).fetchone()
        finally:
            conn.close()
        assert row is not None
        assert row[0] == "running"

    def test_commit_false_still_rejects_out_of_vocabulary(self, store) -> None:
        task = create_task(store._db, "sess1", 1, "1.0.0", "wf-test")
        with pytest.raises(ValueError, match="invalid tasks.status 'done'"):
            update_task_status(store._db, task.task_id, "done", commit=False)
        found = get_task_by_id(store._db, task.task_id)
        assert found is not None
        assert found.status == "pending"
