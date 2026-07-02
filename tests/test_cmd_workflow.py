"""tests/test_cmd_workflow.py
Tests for _WorkflowMixin._cmd_approve() and _cmd_reject().
Exercises the cross-session recovery scenario (ctx cache empty, DB has pending approval).
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest
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


def _make_mixin(workflow_db: str):
    """Return a _WorkflowMixin instance wired to the temp DB."""
    from agent.commands.cmd_workflow import _WorkflowMixin

    # Minimal ctx stubs
    turn = SimpleNamespace(pending_approval_id=None)
    workflow = SimpleNamespace(approval_pending=False)
    ctx = SimpleNamespace(turn=turn, workflow=workflow)

    # Capture output calls
    messages: list[str] = []
    errors: list[str] = []
    out = SimpleNamespace(
        write=lambda msg: messages.append(msg),
        write_validation_error=lambda msg: errors.append(msg),
    )

    class _ConcreteWorkflowMixin(_WorkflowMixin):
        pass

    mixin = _ConcreteWorkflowMixin.__new__(_ConcreteWorkflowMixin)
    mixin._ctx = ctx
    mixin._out = out
    return mixin, ctx, messages, errors, workflow_db


class TestApprove:
    def test_approve_resolves_via_db_when_ctx_cache_empty(
        self, store, workflow_db
    ) -> None:
        """Simulates restart: ctx.turn.pending_approval_id=None but DB has a pending approval."""
        task = store.create_task("session-old", 1, "1.0.0")
        store.update_task_status(task.task_id, "pending_approval")
        approval = store.request_approval(task_id=task.task_id, stage_id="plan")
        store.close()

        mixin, ctx, messages, errors, _ = _make_mixin(workflow_db)
        assert ctx.turn.pending_approval_id is None

        with patch("db.helper.build_db_config", return_value=_make_cfg(workflow_db)):
            mixin._cmd_approve("")

        assert not errors
        assert any(approval.approval_id in m for m in messages)
        assert ctx.turn.pending_approval_id is None  # cleared
        assert ctx.workflow.approval_pending is False

    def test_approve_writes_error_when_no_pending(self, workflow_db) -> None:
        """No pending approval in DB — write_validation_error is called."""
        mixin, _ctx, _messages, errors, _ = _make_mixin(workflow_db)

        with patch("db.helper.build_db_config", return_value=_make_cfg(workflow_db)):
            mixin._cmd_approve("")

        assert errors
        assert "No pending approval" in errors[0]


class TestReject:
    def test_reject_resolves_via_db_when_ctx_cache_empty(
        self, store, workflow_db
    ) -> None:
        """Simulates restart: ctx.turn.pending_approval_id=None but DB has a pending approval."""
        task = store.create_task("session-old", 2, "1.0.0")
        store.update_task_status(task.task_id, "pending_approval")
        approval = store.request_approval(task_id=task.task_id, stage_id="execute")
        store.close()

        mixin, ctx, messages, errors, _ = _make_mixin(workflow_db)

        with patch("db.helper.build_db_config", return_value=_make_cfg(workflow_db)):
            mixin._cmd_reject("too risky")

        assert not errors
        assert any(approval.approval_id in m for m in messages)
        assert ctx.workflow.approval_pending is False

    def test_reject_marks_task_as_halted(self, store, workflow_db) -> None:
        """Reject immediately marks the task as halted."""
        task = store.create_task("session-old", 3, "1.0.0")
        store.update_task_status(task.task_id, "pending_approval")
        store.request_approval(task_id=task.task_id, stage_id="execute")
        store.close()

        mixin, ctx, messages, errors, _ = _make_mixin(workflow_db)

        with patch("db.helper.build_db_config", return_value=_make_cfg(workflow_db)):
            mixin._cmd_reject("too risky")

        assert not errors
        # Verify task is halted in DB
        with patch("db.helper.build_db_config", return_value=_make_cfg(workflow_db)):
            from agent.workflow.state_store import StateStore

            s = StateStore()
            task_record = s.get_task_by_id(task.task_id)
            assert task_record.status == "halted"
            s.close()

    def test_approve_sets_pending_approval_task_id(self, store, workflow_db) -> None:
        """Approve sets pending_approval_task_id for auto-resume."""
        task = store.create_task("session-old", 4, "1.0.0")
        store.update_task_status(task.task_id, "pending_approval")
        store.request_approval(task_id=task.task_id, stage_id="execute")
        store.close()

        mixin, ctx, messages, errors, _ = _make_mixin(workflow_db)

        with patch("db.helper.build_db_config", return_value=_make_cfg(workflow_db)):
            mixin._cmd_approve("")

        assert not errors
        assert ctx.turn.pending_approval_task_id == task.task_id
