"""Regression tests for workflow adapter production guards (wfaudit013).

Two tests (REQ-002), both fail on HEAD and pass after
20261108-201045_01 lands: one for each typed guard error.

Built against the current adapter surface (post wfaudit008): the adapter exposes
``execute_turn`` / ``deactivate_workflow`` plus private helpers, and is constructed
with injected mocks. Both tests drive ``execute_turn`` directly; no real store or
engine is required.
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from agent.turn_result import TurnResult
from agent.workflow_engine_adapter import (
    TurnBoundaryMissingError,
    WorkflowEngineAdapter,
    WorkflowEngineWiringError,
    WorkflowHaltError,
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


@pytest.mark.asyncio
async def test_cancelled_after_engine_started_writes_halted() -> None:
    """REQ-005/AC-3 regression: a ``asyncio.CancelledError`` surfaced once
    ``engine.run`` has started must still produce the adapter's single owned
    status write (``"halted"``). The ``exit_reason`` state machine must not
    silently drop this write when turn-entry preparation and the engine run are
    extracted into helpers."""
    task_record = MagicMock()
    task_record.task_id = "task-cancel"

    store = MagicMock()
    store.create_task.return_value = task_record

    engine = MagicMock()
    engine.version = "1.0.0"

    async def _run(
        task: object, plan_fn: object, execute_fn: object, verify_fn: object
    ) -> None:
        # A cancellation surfaces only after the engine has started.
        raise asyncio.CancelledError()

    engine.run = AsyncMock(side_effect=_run)

    llm_executor = MagicMock()
    llm_executor.handle_llm_turn = AsyncMock()

    conversation_manager = MagicMock()
    conversation_manager.clear_previous_turn_ephemeral_messages = MagicMock()
    conversation_manager.handle_memory_injection = AsyncMock()
    conversation_manager.append_user_message = AsyncMock()
    conversation_manager.handle_history_compression = AsyncMock()

    ctx = _make_ctx()

    adapter = WorkflowEngineAdapter(
        ctx,
        state_store=store,
        workflow_engine=engine,
        conversation_manager=conversation_manager,
        llm_executor=llm_executor,
    )

    with (
        patch(
            "agent.workflow_engine_adapter.classify_and_inject_mode",
            new=AsyncMock(),
        ),
    ):
        with pytest.raises(asyncio.CancelledError):
            await adapter.execute_turn("hello", 0.0, "s-cancel")

    # The cancelled exit is the one path the adapter owns: it must still write
    # "halted" for the task, never silently dropped by the state machine.
    store.update_task_status.assert_called_once_with("task-cancel", "halted")


@pytest.mark.asyncio
async def test_post_engine_run_exception_still_records_status() -> None:
    """REQ-005/AC-3 regression: a fresh, unhandled exception raised after
    ``engine.run`` has started must leave the engine's terminal status write
    intact and propagate. The collapsed ``exit_reason`` state machine must not
    drop or duplicate that write when the run is extracted into
    ``_run_turn_entry``."""
    task_record = MagicMock()
    task_record.task_id = "task-fresh"

    store = MagicMock()
    store.create_task.return_value = task_record

    engine = MagicMock()
    engine.version = "1.0.0"

    async def _run(
        task: object, plan_fn: object, execute_fn: object, verify_fn: object
    ) -> None:
        # The engine records its terminal status, then fails with a fresh
        # exception type the adapter does not otherwise handle.
        store.update_task_status(task.task_id, "completed")
        raise RuntimeError("engine stage aborted")

    engine.run = AsyncMock(side_effect=_run)

    llm_executor = MagicMock()
    llm_executor.handle_llm_turn = AsyncMock()

    conversation_manager = MagicMock()
    conversation_manager.clear_previous_turn_ephemeral_messages = MagicMock()
    conversation_manager.handle_memory_injection = AsyncMock()
    conversation_manager.append_user_message = AsyncMock()
    conversation_manager.handle_history_compression = AsyncMock()

    ctx = _make_ctx()

    adapter = WorkflowEngineAdapter(
        ctx,
        state_store=store,
        workflow_engine=engine,
        conversation_manager=conversation_manager,
        llm_executor=llm_executor,
    )

    with (
        patch(
            "agent.workflow_engine_adapter.classify_and_inject_mode",
            new=AsyncMock(),
        ),
    ):
        with pytest.raises(RuntimeError):
            await adapter.execute_turn("hello", 0.0, "s-fresh")

    # The engine's terminal write survives; the adapter adds nothing for a
    # post-run exception whose status the engine already recorded.
    store.update_task_status.assert_called_once_with("task-fresh", "completed")


@pytest.mark.asyncio
async def test_prepared_halt_re_raises() -> None:
    """A ``WorkflowHaltError`` raised during turn-entry preparation must propagate
    through ``_run_turn_entry``'s passthrough route unchanged, not be wrapped as a
    new halt (covers the halt re-raise extracted into ``_run_turn_entry``)."""
    task_record = MagicMock()
    task_record.task_id = "task-prep-halt"

    store = MagicMock()
    store.create_task.return_value = task_record

    engine = MagicMock()
    engine.version = "1.0.0"

    async def _raise_halt(line: str) -> None:
        raise WorkflowHaltError("turn-entry halted")

    conversation_manager = MagicMock()
    conversation_manager.clear_previous_turn_ephemeral_messages = MagicMock()
    conversation_manager.handle_memory_injection = AsyncMock(side_effect=_raise_halt)
    conversation_manager.append_user_message = AsyncMock()
    conversation_manager.handle_history_compression = AsyncMock()

    ctx = _make_ctx()

    adapter = WorkflowEngineAdapter(
        ctx,
        state_store=store,
        workflow_engine=engine,
        conversation_manager=conversation_manager,
        llm_executor=MagicMock(),
    )

    with (
        patch(
            "agent.workflow_engine_adapter.classify_and_inject_mode",
            new=AsyncMock(),
        ),
    ):
        answer, error_kind, is_partial = await adapter.execute_turn(
            "hello", 0.0, "s-prep-halt"
        )

    # The halt re-raises through the passthrough route (line 224) and is routed by
    # execute_turn's outer handler, which records error_kind "workflow_halted".
    assert error_kind == "workflow_halted"
    # The engine already owns the status write for this halt; the adapter writes
    # nothing here.
    store.update_task_status.assert_not_called()


@pytest.mark.asyncio
async def test_side_effect_attempt_is_terminal() -> None:
    """AC-6: a failed attempt that already attempted a side effect is terminal
    regardless of retry_on. ``_run_execute_attempt`` routes it as a
    ``WorkflowHaltError`` even though the per-attempt reset cleared the flag at
    attempt start."""
    task_record = MagicMock()
    task_record.task_id = "task-ac6"

    store = MagicMock()
    store.create_task.return_value = task_record

    engine = MagicMock()
    engine.version = "1.0.0"

    async def _fake_stage(
        _self: object,
        ctx: object,
        _workflow_id: object,
        _session_id: object,
        _task_id: object,
        _turn_started_at: object,
    ) -> tuple[str, str | None, bool]:
        # A side effect was attempted mid-attempt (the per-attempt reset above
        # cleared it), so the terminal guard below must treat this as terminal.
        ctx.turn.attempt_side_effect = True
        raise RuntimeError("side effect attempted, then failed")

    llm_executor = MagicMock()
    llm_executor.handle_llm_turn = AsyncMock()

    conversation_manager = MagicMock()
    conversation_manager.clear_previous_turn_ephemeral_messages = MagicMock()
    conversation_manager.handle_memory_injection = AsyncMock()
    conversation_manager.append_user_message = AsyncMock()
    conversation_manager.handle_history_compression = AsyncMock()

    ctx = _make_ctx()

    adapter = WorkflowEngineAdapter(
        ctx,
        state_store=store,
        workflow_engine=engine,
        conversation_manager=conversation_manager,
        llm_executor=llm_executor,
    )

    with (
        patch.object(WorkflowEngineAdapter, "_run_execute_stage", _fake_stage),
    ):

        async def _run(
            task: object, plan_fn: object, execute_fn: object, verify_fn: object
        ) -> None:
            await plan_fn()
            await execute_fn()
            await verify_fn()

        engine.run = AsyncMock(side_effect=_run)

        with (
            patch(
                "agent.workflow_engine_adapter.classify_and_inject_mode",
                new=AsyncMock(),
            ),
        ):
            _, error_kind, _ = await adapter.execute_turn("hello", 0.0, "s-ac6")

    # The AC-6 terminal guard converts the failed, side-effecting attempt into a
    # halt routed through execute_turn's handler, recorded as "workflow_halted".
    assert error_kind == "workflow_halted"
    # The engine already owns the status write for this halt; the adapter writes
    # nothing here.
    store.update_task_status.assert_not_called()
