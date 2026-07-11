"""tests/test_approval_ops.py
Unit tests for agent/workflow/approval_ops.py.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from agent.workflow.approval_ops import (
    find_approval_by_id,
    find_latest_pending_approval,
    find_pending_approval_by_session,
    get_latest_approval,
    request_approval,
    resolve_approval,
)
from agent.workflow.task_ops import create_task, update_task_status
from db.config import DbConfig
from db.create_schema import create_workflow_schema


def _make_cfg(db_path: str) -> DbConfig:
    return DbConfig(
        rag_db_path="/opt/llm/db/rag.sqlite",
        session_db_path="/opt/llm/db/session.sqlite",
        workflow_db_path=db_path,
    )


@pytest.fixture()
def workflow_db(tmp_path: Path) -> Path:
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


def _make_task(db, session_id: str = "sess-1", workflow_id: str = "wf-test-1"):
    task = create_task(db, session_id, 1, "1.0.0", workflow_id)
    update_task_status(db, task.task_id, "pending_approval")
    return task


class TestRequestApproval:
    def test_request_approval_persists_workflow_id(self, store) -> None:
        task = _make_task(store._db)
        approval = request_approval(
            store._db, task_id=task.task_id, workflow_id="wf-stored-1"
        )
        rows = store._db.fetchall(
            "SELECT workflow_id FROM approvals WHERE approval_id=?",
            (approval.approval_id,),
        )
        assert rows and rows[0]["workflow_id"] == "wf-stored-1"

    def test_request_approval_returns_record_with_workflow_id(self, store) -> None:
        task = _make_task(store._db)
        approval = request_approval(
            store._db, task_id=task.task_id, workflow_id="wf-nonempty-1"
        )
        assert approval.workflow_id == "wf-nonempty-1"

    def test_request_approval_defaults_empty_workflow_id(self, store) -> None:
        task = _make_task(store._db)
        approval = request_approval(store._db, task_id=task.task_id)
        assert approval.workflow_id == ""

    def test_request_approval_status_is_pending(self, store) -> None:
        task = _make_task(store._db)
        approval = request_approval(
            store._db, task_id=task.task_id, workflow_id="wf-test-1"
        )
        assert approval.status == "pending"


class TestFindApprovalById:
    def test_find_approval_by_id_populates_workflow_id(self, store) -> None:
        task = _make_task(store._db)
        request_approval(store._db, task_id=task.task_id, workflow_id="wf-find-1")
        pending = get_latest_approval(store._db, task.task_id)
        assert pending is not None
        found = find_approval_by_id(store._db, pending.approval_id)
        assert found is not None
        assert found.workflow_id == "wf-find-1"

    def test_find_approval_by_id_returns_none_for_unknown(self, store) -> None:
        result = find_approval_by_id(store._db, "00000000-0000-0000-0000-000000000000")
        assert result is None


class TestGetPendingApproval:
    def test_get_latest_approval_returns_workflow_id(self, store) -> None:
        task = _make_task(store._db)
        request_approval(store._db, task_id=task.task_id, workflow_id="wf-get-1")
        found = get_latest_approval(store._db, task.task_id)
        assert found is not None
        assert found.workflow_id == "wf-get-1"

    def test_get_latest_approval_returns_none_when_absent(self, store) -> None:
        task = _make_task(store._db)
        assert get_latest_approval(store._db, task.task_id) is None


class TestResolveApproval:
    def test_resolve_approval_sets_status_approved(self, store) -> None:
        task = _make_task(store._db)
        approval = request_approval(
            store._db, task_id=task.task_id, workflow_id="wf-test-1"
        )
        resolve_approval(store._db, approval.approval_id, "approved")
        found = find_approval_by_id(store._db, approval.approval_id)
        assert found is not None and found.status == "approved"

    def test_resolve_approval_sets_status_rejected_with_reason(self, store) -> None:
        task = _make_task(store._db)
        approval = request_approval(
            store._db, task_id=task.task_id, workflow_id="wf-test-1"
        )
        resolve_approval(store._db, approval.approval_id, "rejected", "too risky")
        found = find_approval_by_id(store._db, approval.approval_id)
        assert found is not None and found.status == "rejected"
        assert found.reason == "too risky"


class TestFindLatestPendingApproval:
    def test_returns_task_id_and_approval(self, store) -> None:
        task = _make_task(store._db)
        request_approval(store._db, task_id=task.task_id, workflow_id="wf-test-1")
        result = find_latest_pending_approval(store._db)
        assert result is not None
        task_id, approval = result
        assert task_id == task.task_id
        assert approval.status == "pending"

    def test_returns_none_when_none_pending(self, store) -> None:
        assert find_latest_pending_approval(store._db) is None


class TestFindPendingApprovalBySession:
    def test_returns_approval_for_session(self, store) -> None:
        task = create_task(store._db, "session-abc", 1, "1.0.0", "wf-test-1")
        update_task_status(store._db, task.task_id, "pending_approval")
        request_approval(store._db, task_id=task.task_id, workflow_id="wf-test-1")
        result = find_pending_approval_by_session(store._db, "session-abc")
        assert result is not None
        task_id, approval = result
        assert task_id == task.task_id

    def test_returns_none_for_unrelated_session(self, store) -> None:
        task = create_task(store._db, "session-abc", 1, "1.0.0", "wf-test-1")
        update_task_status(store._db, task.task_id, "pending_approval")
        request_approval(store._db, task_id=task.task_id, workflow_id="wf-test-1")
        assert find_pending_approval_by_session(store._db, "session-other") is None
