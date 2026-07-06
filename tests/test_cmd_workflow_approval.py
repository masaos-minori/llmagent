"""tests/test_cmd_workflow_approval.py
Fail-closed multi-pending and UUID-targeted approval tests for _WorkflowMixin.
"""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from agent.workflow.approval_ops import find_approval_by_id, request_approval
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
def workflow_db(tmp_path: Path) -> str:
    db_path = str(tmp_path / "workflow.sqlite")
    with patch("db.helper.build_db_config", return_value=_make_cfg(db_path)):
        create_workflow_schema()
    return db_path


@pytest.fixture()
def store(workflow_db: str):
    from agent.workflow.state_store import StateStore

    with patch("db.helper.build_db_config", return_value=_make_cfg(workflow_db)):
        s = StateStore()
    yield s
    s.close()


def _make_mixin(workflow_db: str, audit_logger=None):
    """Return a _WorkflowMixin instance wired to the temp DB."""
    from agent.commands.cmd_workflow import _WorkflowMixin

    services = SimpleNamespace(audit_logger=audit_logger)
    session = SimpleNamespace(session_id="test-session-1")
    turn = SimpleNamespace(pending_approval_id=None, pending_approval_task_id=None)
    workflow = SimpleNamespace(approval_pending=False)
    ctx = SimpleNamespace(
        turn=turn,
        workflow=workflow,
        session=session,
        services_required=services,
    )

    messages: list[str] = []
    errors: list[str] = []
    out = SimpleNamespace(
        write=lambda msg: messages.append(msg),
        write_validation_error=lambda msg: errors.append(msg),
    )

    class _Concrete(_WorkflowMixin):
        pass

    mixin = _Concrete.__new__(_Concrete)
    mixin._ctx = ctx
    mixin._out = out
    return mixin, ctx, messages, errors


def _create_pending(db, workflow_id: str | None = None):
    """Create a task + pending approval; return (task, approval)."""
    task = create_task(db, None, None, "1.0.0", workflow_id=workflow_id)
    update_task_status(db, task.task_id, "pending_approval")
    approval = request_approval(db, task_id=task.task_id)
    return task, approval


# ── _parse_approval_arg ───────────────────────────────────────────────────────


def test_parse_approval_arg_uuid() -> None:
    from agent.commands.cmd_workflow import _parse_approval_arg

    uid = "12345678-1234-1234-1234-123456789abc"
    approval_id, reason = _parse_approval_arg(f"{uid} some reason")
    assert approval_id == uid
    assert reason == "some reason"


def test_parse_approval_arg_no_uuid() -> None:
    from agent.commands.cmd_workflow import _parse_approval_arg

    approval_id, reason = _parse_approval_arg("my reason text")
    assert approval_id is None
    assert reason == "my reason text"


def test_parse_approval_arg_empty() -> None:
    from agent.commands.cmd_workflow import _parse_approval_arg

    approval_id, reason = _parse_approval_arg("")
    assert approval_id is None
    assert reason is None


# ── approve: zero pending ─────────────────────────────────────────────────────


def test_approve_no_pending(workflow_db: str) -> None:
    mixin, _ctx, _messages, errors = _make_mixin(workflow_db)
    with patch("db.helper.build_db_config", return_value=_make_cfg(workflow_db)):
        mixin._cmd_approve("")
    assert errors
    assert "No pending approval" in errors[0]


# ── approve: one pending, no ID ───────────────────────────────────────────────


def test_approve_single_pending_no_id(store, workflow_db: str) -> None:
    _task, approval = _create_pending(store._db)
    store.close()

    mixin, ctx, messages, errors = _make_mixin(workflow_db)
    with patch("db.helper.build_db_config", return_value=_make_cfg(workflow_db)):
        mixin._cmd_approve("")

    assert not errors
    assert any(approval.approval_id in m for m in messages)
    assert ctx.workflow.approval_pending is False

    with patch("db.helper.build_db_config", return_value=_make_cfg(workflow_db)):
        from agent.workflow.state_store import StateStore

        s = StateStore()
        row = find_approval_by_id(s._db, approval.approval_id)
        s.close()
    assert row is not None
    assert row.status == "approved"


# ── approve: multiple pending, no ID → fail closed ───────────────────────────


def test_approve_multiple_pending_no_id(store, workflow_db: str) -> None:
    _create_pending(store._db)
    _create_pending(store._db)
    store.close()

    mixin, _ctx, _messages, errors = _make_mixin(workflow_db)
    with patch("db.helper.build_db_config", return_value=_make_cfg(workflow_db)):
        mixin._cmd_approve("")

    assert errors
    assert "2 pending approvals" in errors[0]


# ── approve: multiple pending, explicit ID ────────────────────────────────────


def test_approve_multiple_pending_with_id(store, workflow_db: str) -> None:
    _task1, approval1 = _create_pending(store._db)
    _task2, approval2 = _create_pending(store._db)
    store.close()

    mixin, _ctx, messages, errors = _make_mixin(workflow_db)
    with patch("db.helper.build_db_config", return_value=_make_cfg(workflow_db)):
        mixin._cmd_approve(f"{approval2.approval_id} my reason")

    assert not errors
    assert any(approval2.approval_id in m for m in messages)

    with patch("db.helper.build_db_config", return_value=_make_cfg(workflow_db)):
        from agent.workflow.state_store import StateStore

        s = StateStore()
        row1 = find_approval_by_id(s._db, approval1.approval_id)
        row2 = find_approval_by_id(s._db, approval2.approval_id)
        s.close()
    assert row1 is not None and row1.status == "pending"
    assert row2 is not None and row2.status == "approved"


# ── reject: task halted ───────────────────────────────────────────────────────


def test_reject_halts_task(store, workflow_db: str) -> None:
    task, approval = _create_pending(store._db)
    store.close()

    mixin, ctx, messages, errors = _make_mixin(workflow_db)
    with patch("db.helper.build_db_config", return_value=_make_cfg(workflow_db)):
        mixin._cmd_reject("")

    assert not errors
    assert any(approval.approval_id in m for m in messages)
    assert ctx.workflow.approval_pending is False

    with patch("db.helper.build_db_config", return_value=_make_cfg(workflow_db)):
        from agent.workflow.state_store import StateStore

        s = StateStore()
        row = find_approval_by_id(s._db, approval.approval_id)
        task_row = s.get_task_by_id(task.task_id)
        s.close()
    assert row is not None and row.status == "rejected"
    assert task_row is not None and task_row.status == "halted"


# ── reject: multiple pending, no ID → fail closed ─────────────────────────────


def test_reject_multiple_pending_no_id(store, workflow_db: str) -> None:
    _create_pending(store._db)
    _create_pending(store._db)
    store.close()

    mixin, _ctx, _messages, errors = _make_mixin(workflow_db)
    with patch("db.helper.build_db_config", return_value=_make_cfg(workflow_db)):
        mixin._cmd_reject("")

    assert errors
    assert "2 pending approvals" in errors[0]


# ── audit event ───────────────────────────────────────────────────────────────


def test_approve_emits_audit_event(store, workflow_db: str) -> None:
    task, approval = _create_pending(store._db, workflow_id="wf-123")
    store.close()

    class _MockAudit:
        last_event: dict = {}

        def info(self, msg: str) -> None:
            self.last_event = json.loads(msg)

    mock_audit = _MockAudit()
    mixin, _ctx, _messages, errors = _make_mixin(workflow_db, audit_logger=mock_audit)
    with patch("db.helper.build_db_config", return_value=_make_cfg(workflow_db)):
        mixin._cmd_approve("approved for testing")

    assert not errors
    evt = mock_audit.last_event
    assert evt["approval_id"] == approval.approval_id
    assert evt["task_id"] == task.task_id
    assert evt["workflow_id"] == "wf-123"
    assert evt["decision"] == "approved"
    assert evt["reason"] == "approved for testing"
