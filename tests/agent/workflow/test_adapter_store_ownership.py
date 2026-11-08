"""tests/agent/workflow/test_adapter_store_ownership.py

The adapter must never close a store it was injected with. ``execute_turn`` closes
only the store its own ``_init_workflow_task`` created; an injected store survives
the turn (wfaudit006 REQ-001/REQ-002), and the store-less local-init path still
commits and closes its own store cleanly (REQ-002).
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from agent.orchestrator import Orchestrator
from agent.workflow.models import RetryPolicy, StageDefinition, WorkflowDef
from agent.workflow.state_store import StateStore
from agent.workflow.task_ops import create_task
from agent.workflow.workflow_engine import WorkflowEngine
from db.config import DbConfig
from db.create_schema import create_workflow_schema

from tests.agent.test_orchestrator import _make_ctx, _make_orchestrator


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
def ownership(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Iterator[Orchestrator]:
    """A real orchestrator and adapter over a temporary workflow.sqlite.

    Mirrors the wiring in ``test_session_diagnostics_wiring``: the database
    configuration is patched so every ``StateStore`` opens the same temp file, and
    the execute stage plus audit entry points are stubbed so a full turn runs.
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
        monkeypatch.setattr("agent.orchestrator.StateStore", StateStore)
        monkeypatch.setattr(
            "agent.workflow_engine_adapter.WorkflowEngine", WorkflowEngine
        )
        monkeypatch.setattr(
            "agent.workflow_engine_adapter.create_task", create_task, raising=False
        )

        ctx = _make_ctx()
        ctx.session.session_id = "ownership-session"
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
            yield orch
        finally:
            orch._state_store.close()


class TestAdapterStoreOwnership:
    @pytest.mark.asyncio
    async def test_storeless_init_keeps_injected_store_usable(
        self, ownership: Orchestrator
    ) -> None:
        """Historical sequence: a store-less init precedes a turn; the injected
        store must stay open after the turn (use-after-close regression, REQ-001)."""
        orch = ownership
        adapter = orch._workflow_adapter
        injected = orch._state_store

        # Store-less init: the adapter creates and closes its own store, leaving
        # nothing to close the injected store during the following turn.
        adapter._init_workflow_task(orch._ctx, "ownership-session")

        await orch._execute_turn("hello")

        # The injected store survived the turn and still serves queries.
        assert injected.get_connection().conn is not None
        rows = injected.get_connection().fetchall("SELECT task_id FROM tasks")
        assert len(rows) >= 1

    def test_storeless_init_still_closes_its_own_store(
        self, ownership: Orchestrator
    ) -> None:
        """REQ-002 pin: the store-less init commits and closes its own store
        cleanly, and the injected store remains usable."""
        orch = ownership
        adapter = orch._workflow_adapter
        injected = orch._state_store

        _, task = adapter._init_workflow_task(orch._ctx, "ownership-session")

        # The locally-created store committed its task before closing; a fresh
        # connection reads it back.
        fresh = StateStore()
        try:
            row = fresh.get_task_by_id(task.task_id)
            assert row is not None
            assert row.task_id == task.task_id
        finally:
            fresh.close()

        # The store-less init did not touch the injected store.
        assert injected.get_connection().conn is not None
