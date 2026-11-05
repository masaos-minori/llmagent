"""tests/agent/workflow/test_session_diagnostics_wiring.py

tasks.session_id holds the chat session id, so session diagnostics, which count a
session's workflow rows by that id, see the turns the orchestrator ran.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from unittest.mock import MagicMock, patch

import orjson
import pytest
from agent.orchestrator import Orchestrator
from agent.session_persister import SessionPersister
from agent.workflow.models import RetryPolicy, StageDefinition, WorkflowDef
from agent.workflow.state_store import StateStore
from agent.workflow.task_ops import create_task
from agent.workflow.workflow_engine import WorkflowEngine
from db.config import DbConfig
from db.create_schema import create_workflow_schema

from tests.agent.test_orchestrator import _make_ctx, _make_orchestrator

_SESSION_ID = 7


def _definition() -> WorkflowDef:
    return WorkflowDef(
        name="default",
        version="1.0.0",
        stages=[
            StageDefinition(id="plan", timeout_sec=5, retryable=False),
            StageDefinition(id="execute", timeout_sec=5, retryable=False),
            StageDefinition(id="verify", timeout_sec=5, retryable=False),
        ],
        retry_policy=RetryPolicy(max_attempts=1, backoff_sec=0),
    )


@pytest.fixture
def wired(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Iterator[tuple[Orchestrator, MagicMock]]:
    """A real orchestrator, engine, and StateStore over a temporary workflow.sqlite.

    The patched database configuration stays active for the whole test, so the
    persister's own StateStore opens the same file.
    """
    cfg = DbConfig(
        rag_db_path=str(tmp_path / "rag.sqlite"),
        session_db_path=str(tmp_path / "session.sqlite"),
        workflow_db_path=str(tmp_path / "workflow.sqlite"),
    )
    with (
        patch("db.helper.build_db_config", return_value=cfg),
        patch("agent.orchestrator.WorkflowLoader") as loader,
    ):
        create_workflow_schema()
        loader.return_value.load.return_value = _definition()
        # tests/agent/test_orchestrator.py leaves MagicMock patches of these names
        # behind (its autouse patch is undone before the test's own monkeypatch), so
        # pin the real objects.
        monkeypatch.setattr("agent.orchestrator.StateStore", StateStore)
        monkeypatch.setattr(
            "agent.workflow_engine_adapter.WorkflowEngine", WorkflowEngine
        )
        monkeypatch.setattr(
            "agent.workflow_engine_adapter.create_task", create_task, raising=False
        )

        ctx = _make_ctx()
        ctx.session.session_id = _SESSION_ID
        # Without these two the summary holds mock values and is not saved.
        ctx.services = None
        ctx.stats.stat_partial_completions = 0
        orch = _make_orchestrator(ctx)

        async def _execute_stage(
            *_a: object, **_k: object
        ) -> tuple[str, str | None, bool]:
            return ("answer", None, False)

        monkeypatch.setattr(
            orch._workflow_adapter, "_run_execute_stage", _execute_stage, raising=True
        )
        monkeypatch.setattr(
            "agent.workflow_engine_adapter.audit_workflow_start", MagicMock()
        )
        monkeypatch.setattr(
            "agent.workflow_engine_adapter.audit_stage_completed", MagicMock()
        )
        try:
            yield orch, ctx
        finally:
            orch._state_store.close()


def _task_session_ids(orch: Orchestrator) -> list[str]:
    rows = orch._state_store.get_connection().fetchall("SELECT session_id FROM tasks")
    return [row["session_id"] for row in rows]


async def test_persister_sees_turn_workflow_rows(
    wired: tuple[Orchestrator, MagicMock],
) -> None:
    orch, ctx = wired
    await orch._execute_turn("hello")

    diagnostics = MagicMock()
    diagnostics.fetch.return_value = []
    await SessionPersister(ctx, diagnostics, MagicMock()).persist_session_diagnostics()

    summary = orjson.loads(diagnostics.save.call_args.kwargs["content"])
    assert summary["task_count"] == 1
    assert summary["workflow_count"] == 1


async def test_task_row_carries_chat_session_id(
    wired: tuple[Orchestrator, MagicMock],
) -> None:
    orch, _ctx = wired
    await orch._execute_turn("hello")

    assert _task_session_ids(orch) == [str(_SESSION_ID)]


async def test_turn_without_session_records_empty_session_id(
    wired: tuple[Orchestrator, MagicMock],
) -> None:
    """Documents the fallback of format_session_id for an unstarted session."""
    orch, ctx = wired
    ctx.session.session_id = None
    await orch._execute_turn("hello")

    assert _task_session_ids(orch) == [""]
