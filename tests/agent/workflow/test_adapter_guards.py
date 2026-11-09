"""Regression tests for workflow adapter production guards (wfaudit013).

Two tests (REQ-002), both fail on HEAD and pass after
20261108-201045_01 lands: one for each typed guard error.

Built against the current adapter surface (post wfaudit008): the adapter exposes
``execute_turn`` / ``deactivate_workflow`` plus private helpers, and is constructed
with injected mocks. Both tests drive ``execute_turn`` directly; no real store or
engine is required.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from agent.turn_result import TurnResult
from agent.workflow_engine_adapter import (
    TurnBoundaryMissingError,
    WorkflowEngineAdapter,
    WorkflowEngineWiringError,
)

from tests.agent.test_orchestrator import _make_ctx


def _adapter_with_engine(*, workflow_engine: object) -> WorkflowEngineAdapter:
    """Build an adapter over injected mocks (no real store/engine needed)."""
    return WorkflowEngineAdapter(
        _make_ctx(),
        state_store=MagicMock(),
        workflow_engine=workflow_engine,
        conversation_manager=MagicMock(),
        llm_executor=MagicMock(),
    )


@pytest.mark.asyncio
async def test_missing_engine_raises_wiring_error() -> None:
    """REQ-002 pin: a ``None`` injected engine raises before any engine field is
    dereferenced (the guard must precede ``_init_workflow_task`` /
    ``_activate_workflow``, which touch ``engine.version``)."""
    adapter = _adapter_with_engine(workflow_engine=None)

    with pytest.raises(WorkflowEngineWiringError):
        await adapter.execute_turn("line", 0.0, "s-wiring")


@pytest.mark.asyncio
async def test_missing_boundary_raises_protocol_error() -> None:
    """REQ-002 pin: a persist-as-assistant turn with no persistence boundary raises
    ``TurnBoundaryMissingError`` and never reaches ``audit_stage_completed``."""
    task_record = MagicMock()
    task_record.task_id = "task-guard"

    store = MagicMock()
    store.create_task.return_value = task_record

    engine = MagicMock()
    engine.version = "1.0.0"
    engine.build_turn_control_message.return_value = "ctrl"

    async def _run(
        task: object, plan_fn: object, execute_fn: object, verify_fn: object
    ) -> None:
        await plan_fn()
        await execute_fn()
        await verify_fn()

    engine.run = AsyncMock(side_effect=_run)

    llm_executor = MagicMock()
    llm_executor.handle_llm_turn = AsyncMock(
        return_value=TurnResult(
            action="continue", answer="hi", persist_as_assistant=True
        )
    )

    conversation_manager = MagicMock()
    conversation_manager.clear_previous_turn_ephemeral_messages = MagicMock()
    conversation_manager.handle_memory_injection = AsyncMock()
    conversation_manager.append_user_message = AsyncMock()
    conversation_manager.handle_history_compression = AsyncMock()

    ctx = _make_ctx()
    ctx.turn.persistence_boundary = None

    adapter = WorkflowEngineAdapter(
        ctx,
        state_store=store,
        workflow_engine=engine,
        conversation_manager=conversation_manager,
        llm_executor=llm_executor,
    )

    audit = AsyncMock()
    with (
        patch(
            "agent.workflow_engine_adapter.classify_and_inject_mode",
            new=AsyncMock(),
        ),
        patch("agent.workflow_engine_adapter.audit_stage_completed", new=audit),
    ):
        with pytest.raises(TurnBoundaryMissingError):
            await adapter.execute_turn("hello", 0.0, "s-boundary")

    assert audit.await_count == 0
