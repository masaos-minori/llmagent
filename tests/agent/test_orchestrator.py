"""
tests/test_orchestrator.py
Unit tests for Orchestrator: LLMTransportError handling in handle_turn() and _run_turn().
"""

from __future__ import annotations

import asyncio
import json
import logging
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from agent.context import ConversationState, TurnState
from agent.history import CompressResult, HistoryCompressionError
from agent.llm_turn_executor import LlmTurnExecutor
from agent.message_schema import ValidationResult
from agent.orchestrator import BG_FAILURE_THRESHOLD, Orchestrator
from agent.session import AgentSession
from agent.session_message_repo import SessionMessageRepository
from agent.tool_loop_guard import ToolLoopGuard
from agent.turn_persistence import ConversationPersistenceError
from agent.turn_result import TurnResult
from agent.workflow import (
    WorkflowHaltError,
    WorkflowLoadError,
    WorkflowTimeoutError,
)
from agent.workflow.models import RetryPolicy, StageDefinition, WorkflowDef
from agent.workflow.state_store import StateStore
from agent.workflow.task_ops import create_task
from agent.workflow.workflow_engine import WorkflowEngine
from db.config import DbConfig
from db.create_schema import create_workflow_schema
from db.helper import SQLiteHelper
from shared.llm_exceptions import LLMErrorKind, LLMTransportError
from shared.llm_types import LLMMessage, LLMResponse

from tests.agent.test_turn_persistence import _SCHEMA_SQL, _FakeSQLiteHelper


async def _await_raising(
    message: str, name: str = "test_bg_task"
) -> asyncio.Task[object]:
    """Create a raising task, let its body run to the raise, and return it.

    The exception is retained on the task (retrievable via ``task.exception()``)
    rather than propagated, so the caller can hand the finished task to the
    monitor without the raise escaping this helper.
    """

    async def _body() -> None:
        raise RuntimeError(message)

    task = asyncio.create_task(_body(), name=name)
    await asyncio.sleep(0)  # yield once so the body runs and raises
    return task


async def _successful(name: str = "test_bg_task") -> asyncio.Task[object]:
    """Create a task that returns normally; ``task.exception()`` is ``None``."""

    async def _body() -> int:
        return 42

    task = asyncio.create_task(_body(), name=name)
    await asyncio.sleep(0)
    return task


async def _make_cancelled(name: str) -> asyncio.Task[object]:
    """Create a cancellable task, cancel it, await it to completion, and return it."""

    async def _body() -> None:
        await asyncio.Event().wait()

    task = asyncio.create_task(_body(), name=name)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert task.cancelled()
    return task


# ── Fixtures ──────────────────────────────────────────────────────────────────


def _persistence_boundary_mock() -> MagicMock:
    """A stand-in TurnPersistence with awaitable save/replace_messages.

    Used so manager write-routing (through ``ctx.turn.persistence_boundary``) is
    exercised without a real session/DB. The orchestrator assigns this either
    directly (direct-call tests) or as ``turn_boundary()``'s return value (tests
    that drive the full ``execute_turn``).
    """
    boundary = MagicMock()
    boundary.save = AsyncMock(return_value=None)
    boundary.replace_messages = AsyncMock(return_value=None)
    return boundary


def _make_ctx() -> MagicMock:
    ctx = MagicMock()
    # cfg values accessed by handle_turn / _run_turn
    ctx.cfg.tool.max_tool_turns = 3
    ctx.cfg.llm.context_char_limit = 0
    ctx.cfg.llm.context_token_limit = 0
    ctx.cfg.llm.budget_warn_ratio = 0.8
    ctx.cfg.tool.tool_definitions = []
    ctx.cfg.tool.tool_dedup_max_repeats = 3
    ctx.cfg.tool.tool_error_retry_max = 0
    ctx.cfg.tool.tool_cycle_detect_window = 0
    ctx.cfg.tool.tool_error_max_consecutive = 3
    ctx.cfg.tool.progress_stagnation_window = 3
    ctx.cfg.tool.tool_empty_result_max_repeats = 0
    # session / turn state
    ctx.conv = ConversationState(llm_url="http://llm-test")
    ctx.stats.stat_turns = (
        1  # keep > 0 so create_task is not called in first handle_turn
    )
    ctx.stats.stat_latency = {}
    ctx.stats.stat_input_tokens = None
    ctx.stats.stat_output_tokens = None
    ctx.stats.stat_tool_errors = 0
    ctx.stats.stat_tool_calls = 0
    ctx.turn.current_turn_id = None
    ctx.session.session_id = "test-session"
    # Orchestrator creates a per-turn persistence boundary via turn_boundary();
    # expose an awaitable handle on the turn context so the write-routing callers
    # (manager.save / manager.replace_messages) resolve without a real DB. Tests
    # that drive the full execute_turn get this same handle as turn_boundary()'s
    # return value.
    ctx.turn.persistence_boundary = _persistence_boundary_mock()
    ctx.session.turn_boundary = AsyncMock(return_value=_persistence_boundary_mock())
    ctx.workflow.workflow_id = None
    # services
    hist_mgr = AsyncMock()
    hist_mgr.stat_compress_count = 0

    _no_op = CompressResult(compressed_count=0, protected_count=0, summary_added=False)

    async def _compress(h: list) -> tuple:
        return h, _no_op

    hist_mgr.compress = AsyncMock(side_effect=_compress)
    ctx.services_required.hist_mgr = hist_mgr
    llm_svc = MagicMock()
    llm_svc.stat_partial_completions = 0
    llm_svc.stat_parse_errors = 0
    llm_svc.stat_heartbeat_timeouts = 0
    llm_svc.stat_reconnects = 0
    llm_svc.stream = AsyncMock(
        return_value=LLMResponse(
            message=LLMMessage(role="assistant", content="ok"),
            finish_reason="stop",
        )
    )
    ctx.services_required.llm = llm_svc
    ctx.services_required.audit_logger = None
    ctx.services_required.memory = None
    ctx.services_required.tools = None
    return ctx


@pytest.fixture(autouse=True)
def _patch_workflow_loader():
    """Patch workflow infrastructure so Orchestrator works without filesystem access."""
    mock_task = MagicMock()
    mock_task.task_id = "test-task-id"
    mock_task.workflow_id = "test-workflow-id"

    async def _engine_run(task, plan_fn, execute_fn, verify_fn):
        await plan_fn()
        await execute_fn()
        await verify_fn()

    mock_engine_instance = MagicMock()
    mock_engine_instance.run = AsyncMock(side_effect=_engine_run)

    with (
        patch("agent.orchestrator.WorkflowLoader") as mock_loader,
        patch("agent.orchestrator.StateStore"),
        patch("agent.workflow_engine_adapter.create_task", return_value=mock_task),
        patch("agent.workflow_engine_adapter.audit_workflow_start"),
        patch(
            "agent.workflow_engine_adapter.WorkflowEngine",
            return_value=mock_engine_instance,
        ),
    ):
        _default_wdef = WorkflowDef(
            name="default",
            version="test-v1",
            stages=[
                StageDefinition(id="plan", timeout_sec=60, retryable=False),
                StageDefinition(id="execute", timeout_sec=60, retryable=True),
                StageDefinition(id="verify", timeout_sec=60, retryable=False),
            ],
            retry_policy=RetryPolicy(max_attempts=3, backoff_sec=1),
        )
        mock_loader.return_value.load.return_value = _default_wdef
        yield mock_loader


def _make_orchestrator(
    ctx: MagicMock,
    on_error: Any = None,
    pause_on_critical_failure: bool = False,
    workflow_engine: Any = None,
) -> Orchestrator:
    on_first_turn = AsyncMock()
    orch = Orchestrator(
        ctx,
        on_error=on_error,
        on_first_turn=on_first_turn,
        pause_on_critical_failure=pause_on_critical_failure,
        workflow_engine=workflow_engine,
    )
    orch._diagnostic_store = MagicMock()
    ctx.diagnostics = orch._diagnostic_store  # keep ctx.diagnostics in sync with mock
    return orch


def _make_err(
    kind: LLMErrorKind = "CONNECT_ERROR",
    partial_text: str = "",
    retryable: bool = False,
    phase: str = "in_stream",
) -> LLMTransportError:
    return LLMTransportError(
        kind=kind,
        phase=phase,  # type: ignore[arg-type]
        url="http://llm-test",
        retryable=retryable,
        partial_text=partial_text,
    )


def _wire_entry_services(ctx: MagicMock) -> MagicMock:
    """Wire memory + MDQ/RAG mode so the real _prepare_turn_input runs cleanly.

    Returns the injected memory mock so tests can assert on_user_prompt counts.
    """
    ctx.cfg.mdq_rag_mode = "rag"  # deterministic hint, bypasses classifier heuristics
    ctx.conv.system_prompt_content = ""  # no system-prompt sync noise in this test
    memory = AsyncMock()
    snippet = MagicMock()
    snippet.text = "remembered fact"
    memory.on_user_prompt = AsyncMock(return_value=[snippet])
    ctx.services_required.memory = memory
    return memory


# ── handle_turn: mandatory WorkflowEngine.run() invocation ───────────────────


class TestHandleTurnInvokesWorkflowEngine:
    @pytest.mark.asyncio
    async def test_handle_turn_calls_workflow_engine_run_once(self) -> None:
        """handle_turn() always drives execution through WorkflowEngine.run() — there is
        no fallback path that bypasses the engine. This is an explicit, dedicated assertion
        independent of the autouse _patch_workflow_loader fixture's implicit exercise of
        the same call (that fixture patches WorkflowEngine but never asserts on it).
        """
        ctx = _make_ctx()

        async def _engine_run(
            task: Any, plan_fn: Any, execute_fn: Any, verify_fn: Any
        ) -> None:
            await plan_fn()
            await execute_fn()
            await verify_fn()

        mock_engine_instance = MagicMock()
        mock_engine_instance.run = AsyncMock(side_effect=_engine_run)

        orch = _make_orchestrator(ctx, workflow_engine=mock_engine_instance)
        with patch.object(
            orch._llm_executor,
            "handle_llm_turn",
            AsyncMock(return_value=TurnResult(action="continue", answer="ok")),
        ):
            await orch.handle_turn("hello")

        mock_engine_instance.run.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_turn_returns_normally_on_genuine_workflow_timeout(
        self,
    ) -> None:
        """When WorkflowEngine.run() raises WorkflowTimeoutError, handle_turn() must return
        normally and invoke _on_error with the timeout error instance."""
        ctx = _make_ctx()
        on_error = MagicMock()

        async def _raise_timeout(task, plan_fn, execute_fn, verify_fn):
            raise WorkflowTimeoutError("stage timed out")

        mock_engine = MagicMock()
        mock_engine.run = AsyncMock(side_effect=_raise_timeout)

        orch = _make_orchestrator(ctx, on_error=on_error, workflow_engine=mock_engine)
        with (
            patch.object(
                orch._workflow_adapter,
                "init_workflow_task",
                return_value=("wf-1", MagicMock(task_id="task-1")),
            ),
            patch.object(orch._workflow_adapter, "activate_workflow"),
            patch.object(orch._workflow_adapter, "deactivate_workflow"),
            patch("agent.orchestrator.StateStore"),
        ):
            await orch.handle_turn("hello")

        assert on_error.call_count == 1
        exc_arg = on_error.call_args[0][0]
        assert isinstance(exc_arg, WorkflowTimeoutError)
        assert str(exc_arg) == "stage timed out"

    @pytest.mark.asyncio
    async def test_handle_turn_does_not_raise_on_workflow_timeout(self) -> None:
        """handle_turn() must NOT re-raise WorkflowTimeoutError — it is handled internally."""
        ctx = _make_ctx()
        orch = _make_orchestrator(ctx)

        async def _raise_timeout(task, plan_fn, execute_fn, verify_fn):
            raise WorkflowTimeoutError("stage timed out")

        mock_engine = MagicMock()
        mock_engine.run = AsyncMock(side_effect=_raise_timeout)

        with (
            patch.object(
                orch._workflow_adapter,
                "init_workflow_task",
                return_value=("wf-1", MagicMock(task_id="task-1")),
            ),
            patch.object(orch._workflow_adapter, "activate_workflow"),
            patch.object(orch._workflow_adapter, "deactivate_workflow"),
            patch("agent.orchestrator.StateStore"),
            patch(
                "agent.workflow_engine_adapter.WorkflowEngine", return_value=mock_engine
            ),
        ):
            # Should NOT raise
            await orch.handle_turn("hello")

    @pytest.mark.asyncio
    async def test_handle_turn_returns_normally_on_genuine_asyncio_wait_for_timeout(
        self, tmp_path, monkeypatch
    ) -> None:
        """When WorkflowEngine.run() raises WorkflowTimeoutError via a real asyncio.wait_for timeout,
        handle_turn() must return normally and invoke _on_error."""

        from agent.workflow.state_store import StateStore
        from agent.workflow.workflow_engine import WorkflowEngine
        from db.config import DbConfig
        from db.create_schema import create_workflow_schema

        db_path = str(tmp_path / "workflow.sqlite")
        rag_path = str(tmp_path / "rag.sqlite")
        session_path = str(tmp_path / "session.sqlite")

        # Create temp DB schema before creating StateStore
        with patch(
            "db.helper.build_db_config",
            return_value=DbConfig(
                rag_db_path=rag_path,
                session_db_path=session_path,
                workflow_db_path=db_path,
            ),
        ):
            create_workflow_schema()

        # Replace StateStore with one that uses our temp DB (bypasses autouse fixture patch)
        class TempStateStore(StateStore):
            def __init__(self) -> None:
                from db.helper import SQLiteHelper

                self._db = SQLiteHelper(db_path=db_path)
                self._db.open(write_mode=True, row_factory=True)

        # Restore real classes that were patched by autouse _patch_workflow_loader fixture
        monkeypatch.setattr("agent.orchestrator.StateStore", TempStateStore)
        monkeypatch.setattr(
            "agent.workflow_engine_adapter.WorkflowEngine", WorkflowEngine
        )
        monkeypatch.setattr("agent.workflow_engine_adapter.create_task", create_task)

        ctx = _make_ctx()
        on_error = MagicMock()
        orch = _make_orchestrator(ctx, on_error=on_error)

        async def _slow_stream(*_args: object, **_kwargs: object) -> LLMResponse:
            """Force the execute stage to genuinely exceed its 0.01s timeout below."""
            await asyncio.sleep(0.05)
            return LLMResponse(
                message=LLMMessage(role="assistant", content="ok"),
                finish_reason="stop",
            )

        ctx.services_required.llm.stream = _slow_stream

        # Set a real WorkflowDef (autouse fixture returns a mock with MagicMock values)
        stages = [
            StageDefinition(id="plan", timeout_sec=5, retryable=False),
            StageDefinition(id="execute", timeout_sec=0.01, retryable=True),
            StageDefinition(id="verify", timeout_sec=5, retryable=False),
        ]
        policy = RetryPolicy(max_attempts=1, backoff_sec=0)
        orch._workflow_def = WorkflowDef(
            name="default", version="1.0.0", stages=stages, retry_policy=policy
        )
        orch._workflow_adapter._workflow_engine._wdef = orch._workflow_def

        # Patch _activate_workflow/_deactivate_workflow to set workflow state properly
        # so _run_execute_stage has valid task_id/workflow_id for the execute stage
        def _fake_activate(ctx_obj, task):
            ctx_obj.workflow.current_task_id = task.task_id
            ctx_obj.workflow.workflow_id = task.workflow_id
            ctx_obj.workflow.current_workflow_version = orch._workflow_def.version
            ctx_obj.workflow.active = True

        def _fake_deactivate(ctx_obj):
            ctx_obj.workflow.active = False
            ctx_obj.workflow.current_task_id = None
            ctx_obj.workflow.workflow_id = None

        with (
            patch.object(
                orch._workflow_adapter, "activate_workflow", side_effect=_fake_activate
            ),
            patch.object(
                orch._workflow_adapter,
                "deactivate_workflow",
                side_effect=_fake_deactivate,
            ),
        ):
            # Should NOT raise — real WorkflowEngine will timeout after 0.01s
            await orch.handle_turn("hello")

        assert on_error.call_count == 1
        exc_arg = on_error.call_args[0][0]
        # _run_stage_with_retry() re-raises WorkflowTimeoutError immediately
        # (no retry/halt wrapping applies to timeouts specifically), so the
        # exception the adapter's halt handler receives is the timeout error
        # itself, not a WorkflowHaltError.
        assert isinstance(exc_arg, WorkflowTimeoutError)

    @pytest.mark.asyncio
    async def test_handle_turn_does_not_raise_on_real_asyncio_wait_for_timeout(
        self, tmp_path, monkeypatch
    ) -> None:
        """handle_turn() must NOT re-raise WorkflowTimeoutError — it is handled internally by the real engine."""

        from agent.workflow.state_store import StateStore
        from agent.workflow.workflow_engine import WorkflowEngine
        from db.config import DbConfig
        from db.create_schema import create_workflow_schema

        db_path = str(tmp_path / "workflow.sqlite")
        rag_path = str(tmp_path / "rag.sqlite")
        session_path = str(tmp_path / "session.sqlite")

        # Create temp DB schema before creating StateStore
        with patch(
            "db.helper.build_db_config",
            return_value=DbConfig(
                rag_db_path=rag_path,
                session_db_path=session_path,
                workflow_db_path=db_path,
            ),
        ):
            create_workflow_schema()

        # Replace StateStore with one that uses our temp DB (bypasses autouse fixture patch)
        class TempStateStore(StateStore):
            def __init__(self) -> None:
                from db.helper import SQLiteHelper

                self._db = SQLiteHelper(db_path=db_path)
                self._db.open(write_mode=True, row_factory=True)

        # Restore real classes that were patched by autouse _patch_workflow_loader fixture
        monkeypatch.setattr("agent.orchestrator.StateStore", TempStateStore)
        monkeypatch.setattr(
            "agent.workflow_engine_adapter.WorkflowEngine", WorkflowEngine
        )
        monkeypatch.setattr("agent.workflow_engine_adapter.create_task", create_task)

        ctx = _make_ctx()
        orch = _make_orchestrator(ctx)

        async def _slow_stream(*_args: object, **_kwargs: object) -> LLMResponse:
            """Force the execute stage to genuinely exceed its 0.01s timeout below."""
            await asyncio.sleep(0.05)
            return LLMResponse(
                message=LLMMessage(role="assistant", content="ok"),
                finish_reason="stop",
            )

        ctx.services_required.llm.stream = _slow_stream

        # Set a real WorkflowDef (autouse fixture returns a mock with MagicMock values)
        stages = [
            StageDefinition(id="plan", timeout_sec=5, retryable=False),
            StageDefinition(id="execute", timeout_sec=0.01, retryable=True),
            StageDefinition(id="verify", timeout_sec=5, retryable=False),
        ]
        policy = RetryPolicy(max_attempts=1, backoff_sec=0)
        orch._workflow_def = WorkflowDef(
            name="default", version="1.0.0", stages=stages, retry_policy=policy
        )
        orch._workflow_adapter._workflow_engine._wdef = orch._workflow_def

        # Patch _activate_workflow/_deactivate_workflow to set workflow state properly
        def _fake_activate(ctx_obj, task):
            ctx_obj.workflow.current_task_id = task.task_id
            ctx_obj.workflow.workflow_id = task.workflow_id
            ctx_obj.workflow.current_workflow_version = orch._workflow_def.version
            ctx_obj.workflow.active = True

        def _fake_deactivate(ctx_obj):
            ctx_obj.workflow.active = False
            ctx_obj.workflow.current_task_id = None
            ctx_obj.workflow.workflow_id = None

        with (
            patch.object(
                orch._workflow_adapter, "activate_workflow", side_effect=_fake_activate
            ),
            patch.object(
                orch._workflow_adapter,
                "deactivate_workflow",
                side_effect=_fake_deactivate,
            ),
        ):
            # Should NOT raise — real WorkflowEngine will timeout after 0.01s
            await orch.handle_turn("hello")


# ── execute-stage retry runs turn-entry preparation once (AC-1/2/3) ──────────


class TestExecuteStageRetryRunsTurnEntryOnce:
    """The execute stage may retry on failure, but turn-entry preparation runs once."""

    @pytest.mark.asyncio
    async def test_retry_runs_turn_entry_once(self, tmp_path, monkeypatch) -> None:
        """Three execute-stage retries advance turn-entry state exactly once (AC-1/2/3).

        Leaving current_turn_id empty forces the real LLM half to raise RuntimeError
        on every attempt, so the retryable execute stage retries max_attempts times.
        The witness that the boundary moved: stat_turns advances by 1, not 3.
        """
        from agent.workflow.state_store import StateStore
        from agent.workflow.workflow_engine import WorkflowEngine
        from db.config import DbConfig
        from db.create_schema import create_workflow_schema

        db_path = str(tmp_path / "retry_workflow.sqlite")
        rag_path = str(tmp_path / "retry_rag.sqlite")
        session_path = str(tmp_path / "retry_session.sqlite")

        with patch(
            "db.helper.build_db_config",
            return_value=DbConfig(
                rag_db_path=rag_path,
                session_db_path=session_path,
                workflow_db_path=db_path,
            ),
        ):
            create_workflow_schema()

        class TempStateStore(StateStore):
            def __init__(self) -> None:
                from db.helper import SQLiteHelper

                self._db = SQLiteHelper(db_path=db_path)
                self._db.open(write_mode=True, row_factory=True)

        monkeypatch.setattr("agent.orchestrator.StateStore", TempStateStore)
        monkeypatch.setattr(
            "agent.workflow_engine_adapter.WorkflowEngine", WorkflowEngine
        )
        monkeypatch.setattr("agent.workflow_engine_adapter.create_task", create_task)

        ctx = _make_ctx()
        memory = _wire_entry_services(ctx)

        # Classify-and-inject-mode runs during the prepared step; count invocations.
        classify_mock = AsyncMock()
        monkeypatch.setattr(
            "agent.workflow_engine_adapter.classify_and_inject_mode", classify_mock
        )

        # Keep current_turn_id empty so the LLM half raises RuntimeError every attempt.
        on_error = MagicMock()
        orch = _make_orchestrator(ctx, on_error=on_error)
        monkeypatch.setattr(orch._audit_emitter, "emit_turn_start", AsyncMock())

        # Clear-ephemeral is sync; wrap to count invocations.
        clear_spy = MagicMock(
            side_effect=orch._conversation_manager.clear_previous_turn_ephemeral_messages
        )
        orch._conversation_manager.clear_previous_turn_ephemeral_messages = clear_spy

        stages = [
            StageDefinition(id="plan", timeout_sec=5, retryable=False),
            StageDefinition(id="execute", timeout_sec=60, retryable=True),
            StageDefinition(id="verify", timeout_sec=5, retryable=False),
        ]
        policy = RetryPolicy(max_attempts=3, backoff_sec=0)
        orch._workflow_def = WorkflowDef(
            name="default", version="1.0.0", stages=stages, retry_policy=policy
        )
        orch._workflow_adapter._workflow_engine._wdef = orch._workflow_def

        def _fake_activate(ctx_obj, task):
            ctx_obj.workflow.current_task_id = task.task_id
            ctx_obj.workflow.workflow_id = task.workflow_id
            ctx_obj.workflow.current_workflow_version = orch._workflow_def.version
            ctx_obj.workflow.active = True

        def _fake_deactivate(ctx_obj):
            ctx_obj.workflow.active = False
            ctx_obj.workflow.current_task_id = None
            ctx_obj.workflow.workflow_id = None

        with (
            patch.object(
                orch._workflow_adapter, "activate_workflow", side_effect=_fake_activate
            ),
            patch.object(
                orch._workflow_adapter,
                "deactivate_workflow",
                side_effect=_fake_deactivate,
            ),
        ):
            start_turns = ctx.stats.stat_turns
            await orch._workflow_adapter.execute_turn("retry me", 0.0, "")

        # Entry preparation ran exactly once despite three execute-stage attempts.
        assert classify_mock.await_count == 1
        assert memory.on_user_prompt.await_count == 1
        assert clear_spy.call_count == 1
        assert ctx.stats.stat_turns == start_turns + 1

        user_msgs = [m for m in ctx.conv.history if m.get("role") == "user"]
        assert len(user_msgs) == 1
        assert user_msgs[0]["content"] == "retry me"

        # A stage halt surfaces via on_error as a WorkflowHaltError (REQ-003).
        assert on_error.call_count == 1
        assert isinstance(on_error.call_args[0][0], WorkflowHaltError)
        statuses = orch._state_store.get_connection().fetchall(
            "SELECT status FROM tasks"
        )
        assert statuses[0]["status"] == "halted"


# ── entry-work failure is not retried (AC-5) ─────────────────────────────────


class TestEntryWorkFailureIsNotRetried:
    """A turn-entry failure halts immediately: no retries, no attempts row (AC-5)."""

    @pytest.mark.asyncio
    async def test_entry_failure_not_retried(self, tmp_path, monkeypatch) -> None:
        """HistoryCompressionError from the prepared step halts without retrying."""
        from agent.workflow.state_store import StateStore
        from agent.workflow.workflow_engine import WorkflowEngine
        from db.config import DbConfig
        from db.create_schema import create_workflow_schema

        db_path = str(tmp_path / "entry_workflow.sqlite")
        rag_path = str(tmp_path / "entry_rag.sqlite")
        session_path = str(tmp_path / "entry_session.sqlite")

        with patch(
            "db.helper.build_db_config",
            return_value=DbConfig(
                rag_db_path=rag_path,
                session_db_path=session_path,
                workflow_db_path=db_path,
            ),
        ):
            create_workflow_schema()

        class TempStateStore(StateStore):
            def __init__(self) -> None:
                from db.helper import SQLiteHelper

                self._db = SQLiteHelper(db_path=db_path)
                self._db.open(write_mode=True, row_factory=True)

        monkeypatch.setattr("agent.orchestrator.StateStore", TempStateStore)
        monkeypatch.setattr(
            "agent.workflow_engine_adapter.WorkflowEngine", WorkflowEngine
        )
        monkeypatch.setattr("agent.workflow_engine_adapter.create_task", create_task)

        ctx = _make_ctx()
        _wire_entry_services(ctx)
        monkeypatch.setattr(
            "agent.workflow_engine_adapter.classify_and_inject_mode", AsyncMock()
        )

        on_error = MagicMock()
        orch = _make_orchestrator(ctx, on_error=on_error)

        async def _raise_history_error() -> None:
            raise HistoryCompressionError("context compression failed")

        orch._conversation_manager.handle_history_compression = _raise_history_error

        stages = [
            StageDefinition(id="plan", timeout_sec=5, retryable=False),
            StageDefinition(id="execute", timeout_sec=60, retryable=True),
            StageDefinition(id="verify", timeout_sec=5, retryable=False),
        ]
        policy = RetryPolicy(max_attempts=3, backoff_sec=0)
        orch._workflow_def = WorkflowDef(
            name="default", version="1.0.0", stages=stages, retry_policy=policy
        )
        orch._workflow_adapter._workflow_engine._wdef = orch._workflow_def

        with (
            patch.object(
                orch._workflow_adapter,
                "activate_workflow",
                side_effect=lambda ctx_obj, task: None,
            ),
            patch.object(
                orch._workflow_adapter,
                "deactivate_workflow",
                side_effect=lambda ctx_obj: None,
            ),
        ):
            await orch._workflow_adapter.execute_turn("boom entry", 0.0, "")

        # No retry loop touched the entry step: zero attempts rows were written.
        attempts = orch._state_store.get_connection().fetchall(
            "SELECT COUNT(*) AS n FROM attempts"
        )
        assert int(attempts[0]["n"]) == 0

        # At most one user row exists and the halt surfaced via on_error.
        user_msgs = [m for m in ctx.conv.history if m.get("role") == "user"]
        assert len(user_msgs) <= 1
        assert on_error.call_count == 1
        assert isinstance(on_error.call_args[0][0], WorkflowHaltError)
        statuses = orch._state_store.get_connection().fetchall(
            "SELECT status FROM tasks"
        )
        assert statuses[0]["status"] == "halted"


# ── entry work runs outside the execute-stage timeout (AC-4 / REQ-006) ────────


class TestEntryWorkOutsideStageTimeout:
    """Turn-entry preparation is not bounded by the execute stage's timeout."""

    @pytest.mark.asyncio
    async def test_entry_longer_than_stage_timeout_still_completes(
        self, tmp_path, monkeypatch
    ) -> None:
        """Entry work exceeding the stage timeout completes the turn (no timeout)."""
        from agent.workflow.state_store import StateStore
        from agent.workflow.workflow_engine import WorkflowEngine
        from db.config import DbConfig
        from db.create_schema import create_workflow_schema

        db_path = str(tmp_path / "timeout_workflow.sqlite")
        rag_path = str(tmp_path / "timeout_rag.sqlite")
        session_path = str(tmp_path / "timeout_session.sqlite")

        with patch(
            "db.helper.build_db_config",
            return_value=DbConfig(
                rag_db_path=rag_path,
                session_db_path=session_path,
                workflow_db_path=db_path,
            ),
        ):
            create_workflow_schema()

        class TempStateStore(StateStore):
            def __init__(self) -> None:
                from db.helper import SQLiteHelper

                self._db = SQLiteHelper(db_path=db_path)
                self._db.open(write_mode=True, row_factory=True)

        monkeypatch.setattr("agent.orchestrator.StateStore", TempStateStore)
        monkeypatch.setattr(
            "agent.workflow_engine_adapter.WorkflowEngine", WorkflowEngine
        )
        monkeypatch.setattr("agent.workflow_engine_adapter.create_task", create_task)

        ctx = _make_ctx()
        _wire_entry_services(ctx)
        monkeypatch.setattr(
            "agent.workflow_engine_adapter.classify_and_inject_mode", AsyncMock()
        )
        # execute_turn() does not call emit_turn_start(); set the attempt id so the
        # real LLM half has a non-empty workflow context.
        ctx.turn.current_turn_id = "turn-test"

        orch = _make_orchestrator(ctx)

        async def _slow_compress() -> None:
            # Entry work takes longer than the execute stage timeout below.
            await asyncio.sleep(0.3)

        orch._conversation_manager.handle_history_compression = _slow_compress

        async def _instant_stream(*_args: object, **_kwargs: object) -> LLMResponse:
            return LLMResponse(
                message=LLMMessage(role="assistant", content="ok"),
                finish_reason="stop",
            )

        ctx.services_required.llm.stream = _instant_stream

        stages = [
            StageDefinition(id="plan", timeout_sec=5, retryable=False),
            StageDefinition(id="execute", timeout_sec=0.1, retryable=True),
            StageDefinition(id="verify", timeout_sec=5, retryable=False),
        ]
        policy = RetryPolicy(max_attempts=3, backoff_sec=0)
        orch._workflow_def = WorkflowDef(
            name="default", version="1.0.0", stages=stages, retry_policy=policy
        )
        orch._workflow_adapter._workflow_engine._wdef = orch._workflow_def

        def _fake_activate(ctx_obj, task):
            ctx_obj.workflow.current_task_id = task.task_id
            ctx_obj.workflow.workflow_id = task.workflow_id
            ctx_obj.workflow.current_workflow_version = orch._workflow_def.version
            ctx_obj.workflow.active = True

        def _fake_deactivate(ctx_obj):
            ctx_obj.workflow.active = False
            ctx_obj.workflow.current_task_id = None
            ctx_obj.workflow.workflow_id = None

        with (
            patch.object(
                orch._workflow_adapter, "activate_workflow", side_effect=_fake_activate
            ),
            patch.object(
                orch._workflow_adapter,
                "deactivate_workflow",
                side_effect=_fake_deactivate,
            ),
        ):
            # Turn-entry completion must not raise even though entry (0.3s) >
            # execute-stage timeout (0.1s): entry work is outside the stage timeout.
            await orch._workflow_adapter.execute_turn("slow entry", 0.0, "")

        statuses = orch._state_store.get_connection().fetchall(
            "SELECT status FROM tasks"
        )
        assert statuses[0]["status"] == "completed"

    @pytest.mark.asyncio
    async def test_llm_stage_still_bounded_by_timeout(
        self, tmp_path, monkeypatch
    ) -> None:
        """A slow LLM stage still raises WorkflowTimeoutError inside the engine."""
        from agent.workflow.state_store import StateStore
        from agent.workflow.workflow_engine import WorkflowEngine
        from db.config import DbConfig
        from db.create_schema import create_workflow_schema

        db_path = str(tmp_path / "llm_timeout_workflow.sqlite")
        rag_path = str(tmp_path / "llm_timeout_rag.sqlite")
        session_path = str(tmp_path / "llm_timeout_session.sqlite")

        with patch(
            "db.helper.build_db_config",
            return_value=DbConfig(
                rag_db_path=rag_path,
                session_db_path=session_path,
                workflow_db_path=db_path,
            ),
        ):
            create_workflow_schema()

        class TempStateStore(StateStore):
            def __init__(self) -> None:
                from db.helper import SQLiteHelper

                self._db = SQLiteHelper(db_path=db_path)
                self._db.open(write_mode=True, row_factory=True)

        monkeypatch.setattr("agent.orchestrator.StateStore", TempStateStore)
        monkeypatch.setattr(
            "agent.workflow_engine_adapter.WorkflowEngine", WorkflowEngine
        )
        monkeypatch.setattr("agent.workflow_engine_adapter.create_task", create_task)

        ctx = _make_ctx()
        _wire_entry_services(ctx)
        monkeypatch.setattr(
            "agent.workflow_engine_adapter.classify_and_inject_mode", AsyncMock()
        )
        ctx.turn.current_turn_id = "turn-test"

        async def _slow_stream(*_args: object, **_kwargs: object) -> LLMResponse:
            await asyncio.sleep(0.3)
            return LLMResponse(
                message=LLMMessage(role="assistant", content="ok"),
                finish_reason="stop",
            )

        ctx.services_required.llm.stream = _slow_stream

        on_error = MagicMock()
        orch = _make_orchestrator(ctx, on_error=on_error)
        stages = [
            StageDefinition(id="plan", timeout_sec=5, retryable=False),
            StageDefinition(id="execute", timeout_sec=0.1, retryable=True),
            StageDefinition(id="verify", timeout_sec=5, retryable=False),
        ]
        policy = RetryPolicy(max_attempts=3, backoff_sec=0)
        orch._workflow_def = WorkflowDef(
            name="default", version="1.0.0", stages=stages, retry_policy=policy
        )
        orch._workflow_adapter._workflow_engine._wdef = orch._workflow_def

        def _fake_activate(ctx_obj, task):
            ctx_obj.workflow.current_task_id = task.task_id
            ctx_obj.workflow.workflow_id = task.workflow_id
            ctx_obj.workflow.current_workflow_version = orch._workflow_def.version
            ctx_obj.workflow.active = True

        def _fake_deactivate(ctx_obj):
            ctx_obj.workflow.active = False
            ctx_obj.workflow.current_task_id = None
            ctx_obj.workflow.workflow_id = None

        with (
            patch.object(
                orch._workflow_adapter, "activate_workflow", side_effect=_fake_activate
            ),
            patch.object(
                orch._workflow_adapter,
                "deactivate_workflow",
                side_effect=_fake_deactivate,
            ),
        ):
            # execute_turn handles the timeout internally and returns normally.
            await orch._workflow_adapter.execute_turn("slow llm", 0.0, "")

        assert on_error.call_count == 1
        assert isinstance(on_error.call_args[0][0], WorkflowTimeoutError)


class TestHandleTurnLLMTransportError:
    @pytest.mark.asyncio
    async def test_partial_completion_not_in_conversation_history(self) -> None:
        ctx = _make_ctx()
        orch = _make_orchestrator(ctx)
        err = _make_err(kind="PREMATURE_EOF", partial_text="partial answer")

        ctx.services_required.llm.stream = AsyncMock(side_effect=err)
        await orch.handle_turn("hello")

        incomplete = [
            m for m in ctx.conv.history if "[INCOMPLETE" in m.get("content", "")
        ]
        assert len(incomplete) == 0, (
            "Incomplete output must not pollute conversation history"
        )

    @pytest.mark.asyncio
    async def test_partial_completion_saved_to_diagnostic_channel(self) -> None:
        ctx = _make_ctx()
        orch = _make_orchestrator(ctx)
        err = _make_err(kind="PREMATURE_EOF", partial_text="partial answer")

        ctx.services_required.llm.stream = AsyncMock(side_effect=err)
        await orch.handle_turn("hello")

        orch._diagnostic_store.save.assert_called_once()
        # DiagnosticStore.save(session_id, kind, content)
        saved_content = orch._diagnostic_store.save.call_args[0][2]
        assert "partial answer" in saved_content
        assert "[INCOMPLETE: PREMATURE_EOF]" in saved_content

    @pytest.mark.asyncio
    async def test_partial_completion_increments_stat(self) -> None:
        ctx = _make_ctx()
        orch = _make_orchestrator(ctx)
        err = _make_err(kind="PREMATURE_EOF", partial_text="some output")

        ctx.services_required.llm.stream = AsyncMock(side_effect=err)
        await orch.handle_turn("hello")

        assert ctx.services_required.llm.stat_partial_completions == 1

    @pytest.mark.asyncio
    async def test_prestream_error_stores_diagnostic_not_pop(self) -> None:
        """Pre-stream errors store a diagnostic entry; user message stays in history."""
        ctx = _make_ctx()
        orch = _make_orchestrator(ctx)
        err = _make_err(kind="CONNECT_ERROR", partial_text="")

        ctx.services_required.llm.stream = AsyncMock(side_effect=err)
        await orch.handle_turn("hello")

        user_msgs = [m for m in ctx.conv.history if m.get("role") == "user"]
        assert len(user_msgs) == 1
        orch._diagnostic_store.save.assert_called()

    @pytest.mark.asyncio
    async def test_on_error_called_for_partial_completion(self) -> None:
        ctx = _make_ctx()
        on_error = MagicMock()
        orch = _make_orchestrator(ctx, on_error=on_error)
        err = _make_err(kind="PREMATURE_EOF", partial_text="partial")

        ctx.services_required.llm.stream = AsyncMock(side_effect=err)
        await orch.handle_turn("hello")

        on_error.assert_called_once_with(err)

    @pytest.mark.asyncio
    async def test_on_error_called_for_prestream_failure(self) -> None:
        ctx = _make_ctx()
        on_error = MagicMock()
        orch = _make_orchestrator(ctx, on_error=on_error)
        err = _make_err(kind="CONNECT_ERROR", partial_text="")

        ctx.services_required.llm.stream = AsyncMock(side_effect=err)
        await orch.handle_turn("hello")

        on_error.assert_called_once_with(err)

    @pytest.mark.asyncio
    async def test_audit_logger_turn_end_written_on_success(self) -> None:
        ctx = _make_ctx()
        ctx.services_required.audit_logger = MagicMock()
        orch = _make_orchestrator(ctx)

        with patch.object(
            orch._llm_executor,
            "handle_llm_turn",
            AsyncMock(return_value=TurnResult(action="continue", answer="answer")),
        ):
            await orch.handle_turn("hello")

        assert ctx.services_required.audit_logger.info.called

    @pytest.mark.asyncio
    async def test_audit_logger_turn_end_written_on_partial_error(self) -> None:
        ctx = _make_ctx()
        ctx.services_required.audit_logger = MagicMock()
        orch = _make_orchestrator(ctx)
        err = _make_err(kind="PREMATURE_EOF", partial_text="partial")

        ctx.services_required.llm.stream = AsyncMock(side_effect=err)
        await orch.handle_turn("hello")

        assert ctx.services_required.audit_logger.info.called

    @pytest.mark.asyncio
    async def test_turn_end_event_has_partial_completion_true_on_partial_error(
        self,
    ) -> None:
        """turn_end audit event must have partial_completion=True when LLM transport error has partial_text."""
        ctx = _make_ctx()
        ctx.services_required.audit_logger = MagicMock()
        orch = _make_orchestrator(ctx)
        err = _make_err(kind="PREMATURE_EOF", partial_text="partial")

        ctx.services_required.llm.stream = AsyncMock(side_effect=err)
        await orch.handle_turn("hello")

        assert ctx.services_required.audit_logger.info.called
        event = ctx.services_required.audit_logger.info.call_args[0][0]
        import json

        event_dict = json.loads(event)
        assert event_dict["partial_completion"] is True

    @pytest.mark.asyncio
    async def test_turn_end_event_has_partial_completion_false_on_non_partial_error(
        self,
    ) -> None:
        """turn_end audit event must have partial_completion=False when LLM transport error has no partial_text."""
        ctx = _make_ctx()
        ctx.services_required.audit_logger = MagicMock()
        orch = _make_orchestrator(ctx)
        err = _make_err(kind="HTTP_500", partial_text="")

        ctx.services_required.llm.stream = AsyncMock(side_effect=err)
        await orch.handle_turn("hello")

        assert ctx.services_required.audit_logger.info.called
        event = ctx.services_required.audit_logger.info.call_args[0][0]
        import json

        event_dict = json.loads(event)
        assert event_dict["partial_completion"] is False

    @pytest.mark.asyncio
    async def test_read_timeout_with_partial_increments_stat(self) -> None:
        ctx = _make_ctx()
        orch = _make_orchestrator(ctx)
        err = _make_err(kind="READ_TIMEOUT", partial_text="chunk text")

        ctx.services_required.llm.stream = AsyncMock(side_effect=err)
        await orch.handle_turn("hello")

        assert ctx.services_required.llm.stat_partial_completions == 1
        call_args = orch._diagnostic_store.save.call_args_list
        assert any("llm_transport_error" in str(a) for a in call_args)

    @pytest.mark.asyncio
    async def test_http_retryable_prestream_saves_mid_turn_diagnostic(self) -> None:
        ctx = _make_ctx()
        orch = _make_orchestrator(ctx)
        err = _make_err(kind="HTTP_STATUS_RETRYABLE", retryable=True, partial_text="")

        ctx.services_required.llm.stream = AsyncMock(side_effect=err)
        await orch.handle_turn("hello")

        assert ctx.services_required.llm.stat_partial_completions == 0
        call_args = orch._diagnostic_store.save.call_args_list
        assert any("mid_turn_error" in str(a) for a in call_args)

    @pytest.mark.asyncio
    async def test_http_fatal_with_status_code_saves_diagnostic(self) -> None:
        ctx = _make_ctx()
        orch = _make_orchestrator(ctx)
        err = LLMTransportError(
            kind="HTTP_STATUS_FATAL",
            phase="pre_stream",
            url="http://llm-test",
            status_code=503,
            partial_text="",
        )

        ctx.services_required.llm.stream = AsyncMock(side_effect=err)
        await orch.handle_turn("hello")

        assert ctx.services_required.llm.stat_partial_completions == 0
        orch._diagnostic_store.save.assert_called()

    @pytest.mark.asyncio
    async def test_malformed_sse_with_partial_saves_llm_transport_diagnostic(
        self,
    ) -> None:
        ctx = _make_ctx()
        orch = _make_orchestrator(ctx)
        err = _make_err(kind="MALFORMED_SSE_FRAME", partial_text="partial frame")

        ctx.services_required.llm.stream = AsyncMock(side_effect=err)
        await orch.handle_turn("hello")

        assert ctx.services_required.llm.stat_partial_completions == 1
        saved_content = orch._diagnostic_store.save.call_args[0][2]
        assert "[INCOMPLETE: MALFORMED_SSE_FRAME]" in saved_content

    @pytest.mark.asyncio
    async def test_prestream_error_not_saved_as_assistant_message(self) -> None:
        """Pre-stream LLM transport errors must not be saved as assistant messages."""
        ctx = _make_ctx()
        orch = _make_orchestrator(ctx)
        err = _make_err(kind="CONNECT_ERROR", partial_text="")

        ctx.services_required.llm.stream = AsyncMock(side_effect=err)
        await orch.handle_turn("hello")

        # session.save should NOT be called with "assistant" role for transport errors
        assistant_saves = [
            call
            for call in ctx.session.save.call_args_list
            if call[0][0] == "assistant"
        ]
        assert len(assistant_saves) == 0, (
            "Transport error summary must not be saved as assistant message"
        )

    @pytest.mark.asyncio
    async def test_partial_completion_not_saved_as_assistant_message(self) -> None:
        """Partial completion LLM errors must not be saved as assistant messages."""
        ctx = _make_ctx()
        orch = _make_orchestrator(ctx)
        err = _make_err(kind="PREMATURE_EOF", partial_text="partial answer")

        ctx.services_required.llm.stream = AsyncMock(side_effect=err)
        await orch.handle_turn("hello")

        # session.save should NOT be called with "assistant" role for partial completions
        assistant_saves = [
            call
            for call in ctx.session.save.call_args_list
            if call[0][0] == "assistant"
        ]
        assert len(assistant_saves) == 0, (
            "Partial completion must not be saved as assistant message"
        )

    @pytest.mark.asyncio
    async def test_success_still_saved_as_assistant_message(self) -> None:
        """Successful LLM responses should still be saved as assistant messages."""
        ctx = _make_ctx()
        orch = _make_orchestrator(ctx)

        with patch.object(
            orch._llm_executor,
            "handle_llm_turn",
            AsyncMock(return_value=TurnResult(action="continue", answer="hello")),
        ):
            await orch.handle_turn("hello")

        # SEQ-09: the final-answer persist routes through the turn boundary, not
        # a standalone ctx.session.save (AC-001). The boundary also persists the
        # user row first; assert the assistant row is among its saves.
        assistant_calls = [
            c
            for c in ctx.turn.persistence_boundary.save.call_args_list
            if c.args == ("assistant", "hello")
        ]
        assert len(assistant_calls) == 1

    @pytest.mark.asyncio
    async def test_turn_end_partial_completion_true_on_partial_error(self) -> None:
        """partial_completion=True when LLM transport error has partial text."""
        ctx = _make_ctx()
        orch = _make_orchestrator(ctx)
        err = _make_err(kind="PREMATURE_EOF", partial_text="partial text here")

        captured: list[str] = []
        ctx.services_required.audit_logger = MagicMock()
        ctx.services_required.audit_logger.info = lambda s: captured.append(s)

        ctx.services_required.llm.stream = AsyncMock(side_effect=err)
        await orch.handle_turn("test message")

        turn_end_events = [json.loads(s) for s in captured if "turn_end" in s]
        assert turn_end_events, "No turn_end event captured"
        assert turn_end_events[0]["partial_completion"] is True

    @pytest.mark.asyncio
    async def test_turn_end_partial_completion_false_on_full_error(self) -> None:
        """partial_completion=False when LLM transport error has no partial text."""
        ctx = _make_ctx()
        orch = _make_orchestrator(ctx)
        err = _make_err(kind="CONNECT_ERROR", partial_text="")

        captured: list[str] = []
        ctx.services_required.audit_logger = MagicMock()
        ctx.services_required.audit_logger.info = lambda s: captured.append(s)

        ctx.services_required.llm.stream = AsyncMock(side_effect=err)
        await orch.handle_turn("test message")

        turn_end_events = [json.loads(s) for s in captured if "turn_end" in s]
        assert turn_end_events, "No turn_end event captured"
        assert turn_end_events[0]["partial_completion"] is False

    @pytest.mark.asyncio
    async def test_fetch_messages_excludes_transport_diagnostics(self) -> None:
        """Transport errors must not be saved to the messages table."""
        ctx = _make_ctx()
        orch = _make_orchestrator(ctx)
        err = _make_err(kind="CONNECT_ERROR", partial_text="")

        ctx.services_required.llm.stream = AsyncMock(side_effect=err)
        await orch.handle_turn("test message")

        assistant_saves = [
            call
            for call in ctx.session.save.call_args_list
            if call[0][0] == "assistant"
        ]
        assert len(assistant_saves) == 0, (
            "Transport error must not write to messages table"
        )


class TestTurnEndBracket:
    """Witnesses the Orchestrator ``_execute_turn`` bracket: exactly one ``turn_end``
    on every exit path, turn-relative ``elapsed_ms``, and completed teardown
    (REQ-001, REQ-002, REQ-004)."""

    @staticmethod
    def _install_audit_capture(ctx: Any) -> list[str]:
        captured: list[str] = []
        ctx.services_required.audit_logger = MagicMock()
        ctx.services_required.audit_logger.info = lambda s: captured.append(s)  # noqa: E731
        return captured

    @staticmethod
    def _turn_end_events(captured: list[str]) -> list[dict]:
        return [json.loads(s) for s in captured if "turn_end" in s]

    @pytest.mark.asyncio
    async def test_success_emits_single_turn_end_with_turn_relative_elapsed(
        self,
    ) -> None:
        # Case A: success. One turn_end; fields populated; elapsed is turn-relative.
        ctx = _make_ctx()
        orch = _make_orchestrator(ctx)
        captured = self._install_audit_capture(ctx)

        with patch.object(
            orch._llm_executor,
            "handle_llm_turn",
            AsyncMock(return_value=TurnResult(action="continue", answer="ok")),
        ):
            await orch.handle_turn("hello")

        events = self._turn_end_events(captured)
        assert len(events) == 1, f"expected one turn_end, got {len(events)}"
        ev = events[0]
        assert ev["error_kind"] is None
        assert ev["partial_completion"] is False
        assert ev["task_id"], "task_id must be set during the turn"
        assert ev["workflow_id"], "workflow_id must be set at init"
        assert 0 <= ev["elapsed_ms"] < 5000, "elapsed_ms must be turn-relative"
        assert ctx.workflow.active is False, "workflow must be deactivated at teardown"

    @pytest.mark.asyncio
    async def test_soft_partial_error_emits_single_turn_end_with_fields(self) -> None:
        # Case C: soft LLM transport error with partial text.
        ctx = _make_ctx()
        orch = _make_orchestrator(ctx)
        err = _make_err(kind="PREMATURE_EOF", partial_text="partial text here")
        captured = self._install_audit_capture(ctx)

        ctx.services_required.llm.stream = AsyncMock(side_effect=err)
        await orch.handle_turn("test message")

        events = self._turn_end_events(captured)
        assert len(events) == 1
        ev = events[0]
        assert ev["error_kind"] == "PREMATURE_EOF"
        assert ev["partial_completion"] is True
        assert ctx.workflow.active is False

    @pytest.mark.asyncio
    async def test_halt_emits_single_turn_end_and_invokes_on_error(self) -> None:
        # Case halt: WorkflowHaltError surfaces via on_error; one turn_end emitted.
        ctx = _make_ctx()
        on_error = MagicMock()
        orch = _make_orchestrator(ctx, on_error=on_error)
        captured = self._install_audit_capture(ctx)

        engine = orch._workflow_adapter._workflow_engine

        async def _raise_halt(task, plan_fn, execute_fn, verify_fn) -> None:
            raise WorkflowHaltError("stage halted")

        engine.run = AsyncMock(side_effect=_raise_halt)
        await orch.handle_turn("hello")

        events = self._turn_end_events(captured)
        assert len(events) == 1
        assert events[0]["error_kind"] is None
        on_error.assert_called_once()
        assert isinstance(on_error.call_args[0][0], WorkflowHaltError)
        assert ctx.workflow.active is False

    @pytest.mark.asyncio
    async def test_escaping_exception_emits_single_turn_end_then_reraises(
        self,
    ) -> None:
        # Case G: a non-halt exception escapes; one turn_end with the class name.
        ctx = _make_ctx()
        orch = _make_orchestrator(ctx)
        captured = self._install_audit_capture(ctx)

        engine = orch._workflow_adapter._workflow_engine

        async def _raise_runtime(task, plan_fn, execute_fn, verify_fn) -> None:
            raise RuntimeError("boom")

        engine.run = AsyncMock(side_effect=_raise_runtime)

        with pytest.raises(RuntimeError):
            await orch.handle_turn("hello")

        events = self._turn_end_events(captured)
        assert len(events) == 1
        assert events[0]["error_kind"] == "RuntimeError"
        assert ctx.turn.current_turn_id is None, "turn id cleared at teardown"
        assert ctx.workflow.active is False

    @pytest.mark.asyncio
    async def test_cancelled_emits_single_turn_end_and_clears_turn_id(self) -> None:
        # Case E: CancelledError at a stage boundary; one turn_end, turn id cleared.
        ctx = _make_ctx()
        orch = _make_orchestrator(ctx)
        captured = self._install_audit_capture(ctx)

        engine = orch._workflow_adapter._workflow_engine

        async def _raise_cancel(task, plan_fn, execute_fn, verify_fn) -> None:
            raise asyncio.CancelledError()

        engine.run = AsyncMock(side_effect=_raise_cancel)

        with pytest.raises(asyncio.CancelledError):
            await orch.handle_turn("hello")

        events = self._turn_end_events(captured)
        assert len(events) == 1
        assert events[0]["error_kind"] == "CancelledError"
        assert ctx.turn.current_turn_id is None
        assert ctx.workflow.active is False

    @pytest.mark.asyncio
    async def test_failure_before_activate_emits_single_turn_end(self) -> None:
        # Failure raised before activation completes: one turn_end, teardown ran.
        ctx = _make_ctx()
        orch = _make_orchestrator(ctx)
        captured = self._install_audit_capture(ctx)

        def _raise_activate(*args: Any, **kwargs: Any) -> None:
            raise RuntimeError("activate failed")

        with patch.object(
            orch._workflow_adapter, "_activate_workflow", side_effect=_raise_activate
        ):
            with pytest.raises(RuntimeError):
                await orch.handle_turn("hello")

        events = self._turn_end_events(captured)
        assert len(events) == 1
        assert events[0]["error_kind"] == "RuntimeError"
        assert ctx.workflow.active is False


# ── _handle_llm_turn: optional wait/turn callbacks ───────────────────────────


class TestHandleLlmTurnOptionalCallbacks:
    """Characterization tests for _handle_llm_turn's optional callback invocations.

    These callbacks (on_llm_wait_start/end, on_turn_start/end) previously had no
    test coverage at all — none of the existing tests configure them.
    """

    @pytest.mark.asyncio
    async def test_wait_and_turn_callbacks_invoked_on_success(self) -> None:
        ctx = _make_ctx()
        on_turn_start = MagicMock()
        on_turn_end = MagicMock()
        on_llm_wait_start = AsyncMock()
        on_llm_wait_end = MagicMock()
        orch = Orchestrator(
            ctx,
            on_turn_start=on_turn_start,
            on_turn_end=on_turn_end,
            on_llm_wait_start=on_llm_wait_start,
            on_llm_wait_end=on_llm_wait_end,
        )
        orch._diagnostic_store = MagicMock()
        ctx.diagnostics = orch._diagnostic_store

        mock_runner = AsyncMock()
        mock_runner.run.return_value = TurnResult(action="continue", answer="ok")
        with patch("agent.llm_turn_executor.LLMTurnRunner", return_value=mock_runner):
            await orch.handle_turn("hello")

        on_llm_wait_start.assert_called_once()
        on_turn_start.assert_called_once()
        on_llm_wait_end.assert_called_once()
        on_turn_end.assert_called_once()

    @pytest.mark.asyncio
    async def test_wait_end_error_and_turn_end_invoked_when_run_returns_exception(
        self,
    ) -> None:
        """Covers the in-try `result.exception is not None` branch (run() caught the
        error internally and returned it on the TurnResult), distinct from the
        `except LLMTransportError` branch exercised by other tests in this file.
        """
        ctx = _make_ctx()
        on_error = MagicMock()
        on_turn_end = MagicMock()
        on_llm_wait_end = MagicMock()
        err = _make_err(kind="CONNECT_ERROR", partial_text="")
        orch = Orchestrator(
            ctx,
            on_error=on_error,
            on_turn_end=on_turn_end,
            on_llm_wait_end=on_llm_wait_end,
        )
        orch._diagnostic_store = MagicMock()
        ctx.diagnostics = orch._diagnostic_store

        mock_runner = AsyncMock()
        mock_runner.run.return_value = TurnResult(
            action="fail",
            answer="",
            exception=err,
            persist_as_assistant=False,
        )
        with patch("agent.llm_turn_executor.LLMTurnRunner", return_value=mock_runner):
            await orch.handle_turn("hello")

        on_error.assert_called_once_with(err)
        on_llm_wait_end.assert_called_once()
        on_turn_end.assert_called_once()

    @pytest.mark.asyncio
    async def test_wait_end_invoked_in_except_branch(self) -> None:
        """Covers the `except LLMTransportError` branch's on_llm_wait_end call,
        reached when run() itself raises (rather than returning a TurnResult
        with exception set)."""
        ctx = _make_ctx()
        on_llm_wait_end = MagicMock()
        err = _make_err(kind="CONNECT_ERROR", partial_text="")
        orch = Orchestrator(ctx, on_llm_wait_end=on_llm_wait_end)
        orch._diagnostic_store = MagicMock()
        ctx.diagnostics = orch._diagnostic_store

        ctx.services_required.llm.stream = AsyncMock(side_effect=err)
        await orch.handle_turn("hello")

        on_llm_wait_end.assert_called_once()


# ── _run_turn: tool-continuation LLMTransportError ───────────────────────────


class TestRunTurnLLMTransportError:
    @pytest.mark.asyncio
    async def test_transport_error_on_tool_continuation_stores_in_diagnostic(
        self,
    ) -> None:
        """Tool-continuation LLM errors go to diagnostic channel; history not modified."""
        ctx = _make_ctx()
        orch = _make_orchestrator(ctx)

        tool_calls = [
            {"id": "tc1", "function": {"name": "test_tool", "arguments": "{}"}}
        ]
        first_response = LLMResponse(
            message=LLMMessage(
                role="assistant",
                content=None,
                tool_calls=tool_calls,
            ),
            finish_reason="tool_calls",
        )
        err = _make_err(kind="CONNECT_ERROR", partial_text="")
        call_count = 0

        async def _mock_stream(*_args: object, **_kwargs: object) -> LLMResponse:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return first_response
            raise err

        ctx.services_required.llm.stream = _mock_stream

        with patch("agent.llm_turn_runner.execute_all_tool_calls", AsyncMock()):
            result = await orch._llm_executor.handle_llm_turn(
                "http://llm-test",
                workflow_id="wf-test",
                task_id="task-test",
                stage_id="execute",
                attempt_id="att-test",
            )

        assert "CONNECT_ERROR" in result.answer
        synthetic = [
            m for m in ctx.conv.history if m.get("name") == "llm_transport_error"
        ]
        assert len(synthetic) == 0
        ctx.diagnostics.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_transport_error_on_first_turn_stores_in_diagnostic(self) -> None:
        """First-turn LLM errors go to diagnostic channel; no synthetic history entry."""
        ctx = _make_ctx()
        orch = _make_orchestrator(ctx)
        err = _make_err(kind="CONNECT_ERROR", partial_text="")

        async def _mock_stream(*_args: object, **_kwargs: object) -> dict:
            raise err

        ctx.services_required.llm.stream = _mock_stream

        result = await orch._llm_executor.handle_llm_turn(
            "http://llm-test",
            workflow_id="wf-test",
            task_id="task-test",
            stage_id="execute",
            attempt_id="att-test",
        )
        assert "CONNECT_ERROR" in result.answer
        synthetic = [
            m for m in ctx.conv.history if m.get("name") == "llm_transport_error"
        ]
        assert len(synthetic) == 0
        ctx.diagnostics.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_tool_continuation_fail_stores_in_diagnostic(self) -> None:
        """Tool-continuation LLM errors are stored in diagnostic channel only."""
        ctx = _make_ctx()
        orch = _make_orchestrator(ctx)

        tool_calls = [
            {"id": "tc1", "function": {"name": "test_tool", "arguments": "{}"}}
        ]
        first_response = LLMResponse(
            message=LLMMessage(
                role="assistant",
                content=None,
                tool_calls=tool_calls,
            ),
            finish_reason="tool_calls",
        )
        err = _make_err(kind="HEARTBEAT_TIMEOUT", partial_text="")
        call_count = 0

        async def _mock_stream(*_args: object, **_kwargs: object) -> LLMResponse:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return first_response
            raise err

        ctx.services_required.llm.stream = _mock_stream

        with patch("agent.llm_turn_runner.execute_all_tool_calls", AsyncMock()):
            result = await orch._llm_executor.handle_llm_turn(
                "http://llm-test",
                workflow_id="wf-test",
                task_id="task-test",
                stage_id="execute",
                attempt_id="att-test",
            )

        assert result.action == "fail"
        assert "HEARTBEAT_TIMEOUT" in result.answer
        ctx.diagnostics.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_read_timeout_on_first_turn_stores_in_diagnostic(self) -> None:
        ctx = _make_ctx()
        orch = _make_orchestrator(ctx)
        err = _make_err(kind="READ_TIMEOUT", partial_text="")

        async def _mock_stream(*_args: object, **_kwargs: object) -> dict:
            raise err

        ctx.services_required.llm.stream = _mock_stream

        result = await orch._llm_executor.handle_llm_turn(
            "http://llm-test",
            workflow_id="wf-test",
            task_id="task-test",
            stage_id="execute",
            attempt_id="att-test",
        )
        assert "READ_TIMEOUT" in result.answer
        ctx.diagnostics.save.assert_called_once()


# ── _run_turn: normal completion (is_done=True) ──────────────────────────────


class TestRunTurnNormalCompletion:
    @pytest.mark.asyncio
    async def test_run_turn_returns_content_on_stop(self) -> None:
        # finish_reason="stop" → is_done=True → _finalize_answer() → content を返す
        ctx = _make_ctx()
        orch = _make_orchestrator(ctx)

        stop_response = LLMResponse(
            message=LLMMessage(
                role="assistant",
                content="hello world",
                tool_calls=None,
            ),
            finish_reason="stop",
        )

        async def _mock_stream(*_args: object, **_kwargs: object) -> LLMResponse:
            return stop_response

        ctx.services_required.llm.stream = _mock_stream

        result = await orch._llm_executor.handle_llm_turn(
            "http://llm-test",
            workflow_id="wf-test",
            task_id="task-test",
            stage_id="execute",
            attempt_id="att-test",
        )

        assert result.answer == "hello world"
        assistant_msgs = [m for m in ctx.conv.history if m.get("role") == "assistant"]
        assert len(assistant_msgs) == 1

    @pytest.mark.asyncio
    async def test_run_turn_returns_empty_string_on_none_content(self) -> None:
        # content が None の場合は空文字列を返す
        ctx = _make_ctx()
        orch = _make_orchestrator(ctx)

        stop_response = LLMResponse(
            message=LLMMessage(
                role="assistant",
                content=None,
                tool_calls=None,
            ),
            finish_reason="stop",
        )

        async def _mock_stream(*_args: object, **_kwargs: object) -> LLMResponse:
            return stop_response

        ctx.services_required.llm.stream = _mock_stream

        result = await orch._llm_executor.handle_llm_turn(
            "http://llm-test",
            workflow_id="wf-test",
            task_id="task-test",
            stage_id="execute",
            attempt_id="att-test",
        )

        assert result.answer == ""


# ── Orchestrator helper unit tests ────────────────────────────────────────────


class TestToolLoopGuardHelpers:
    """Tests for ToolLoopGuard public API (previously tested via Orchestrator delegates)."""

    def test_update_consecutive_errors_increments_when_all_fail(self) -> None:
        result = ToolLoopGuard.update_errors(0, 3, 3)
        assert result == 1

    def test_update_consecutive_errors_maintains_on_partial_failure(self) -> None:
        result = ToolLoopGuard.update_errors(2, 1, 3)
        assert result == 2

    def test_update_consecutive_errors_resets_when_no_errors(self) -> None:
        result = ToolLoopGuard.update_errors(2, 0, 3)
        assert result == 0

    def test_check_consecutive_error_limit_below_max_returns_none(self) -> None:
        ctx = _make_ctx()
        ctx.cfg.tool.tool_error_max_consecutive = 3
        assert ToolLoopGuard(ctx).check_error_limit(2) is None

    def test_check_consecutive_error_limit_at_max_returns_message(self) -> None:
        ctx = _make_ctx()
        ctx.cfg.tool.tool_error_max_consecutive = 3
        result = ToolLoopGuard(ctx).check_error_limit(3)
        assert result is not None
        assert "consecutive" in result

    def test_check_consecutive_error_limit_disabled_returns_none(self) -> None:
        ctx = _make_ctx()
        ctx.cfg.tool.tool_error_max_consecutive = 0
        assert ToolLoopGuard(ctx).check_error_limit(999) is None

    def test_check_all_tool_guards_returns_none_when_no_guards_hit(self) -> None:
        ctx = _make_ctx()
        ctx.cfg.tool.tool_dedup_max_repeats = 3
        ctx.cfg.tool.tool_cycle_detect_window = 0
        ctx.cfg.tool.tool_error_retry_max = 0
        msg = MagicMock()
        msg.__getitem__ = lambda self, k: [] if k == "tool_calls" else None
        msg.get = lambda k, d=None: [] if k == "tool_calls" else d
        result = ToolLoopGuard(ctx).check_all({}, [], [], set(), msg)
        assert result is None

    def test_check_all_tool_guards_returns_on_cycle_guard_hit(self) -> None:
        ctx = _make_ctx()
        ctx.cfg.tool.tool_dedup_max_repeats = 10
        ctx.cfg.tool.tool_cycle_detect_window = 1  # detect after 1 repeat
        ctx.cfg.tool.tool_error_retry_max = 0
        tool_calls = [{"function": {"name": "my_tool", "arguments": "{}"}}]
        msg: dict = {"role": "assistant", "content": None, "tool_calls": tool_calls}

        fingerprints: list[str] = []
        result1 = ToolLoopGuard(ctx).check_all({}, fingerprints, [], set(), msg)
        assert result1 is None
        assert len(fingerprints) == 1

        # Second call with the same message → cycle guard fires
        result2 = ToolLoopGuard(ctx).check_all({}, fingerprints, [], set(), msg)
        assert result2 is not None
        assert "cycle" in result2.lower() or "cyclic" in result2.lower()

    def test_check_all_tool_guards_returns_on_dedup_guard_hit(self) -> None:
        ctx = _make_ctx()
        ctx.cfg.tool.tool_dedup_max_repeats = 1  # fire on first repeat
        ctx.cfg.tool.tool_cycle_detect_window = 0
        ctx.cfg.tool.tool_error_retry_max = 0
        import hashlib

        tool_calls = [{"function": {"name": "my_tool", "arguments": "{}"}}]
        msg: dict = {"role": "assistant", "content": None, "tool_calls": tool_calls}

        key = hashlib.md5(b"my_tool:{}", usedforsecurity=False).hexdigest()
        seen: dict[str, int] = {key: 1}

        result = ToolLoopGuard(ctx).check_all(seen, [], [], set(), msg)
        assert result is not None
        assert "repeated" in result.lower() or "duplicate" in result.lower()


# ── no approval stage ─────────────────────────────────────────────────────────


class TestNoApprovalStage:
    """The workflow has no approval stage: turns complete without operator action."""

    @pytest.mark.asyncio
    async def test_consecutive_turns_complete_without_operator_action(self) -> None:
        on_error = MagicMock()
        ctx = _make_ctx()
        orch = _make_orchestrator(ctx, on_error=on_error)
        process = AsyncMock(return_value=("ok", None, False))

        with patch.object(orch._workflow_adapter, "_run_execute_stage", new=process):
            await orch.handle_turn("write a file")
            await orch.handle_turn("write another file")

        # Both turns reached the turn processor: nothing blocked the second one.
        assert process.await_count == 2
        for call in on_error.call_args_list:
            assert "approval" not in str(call[0][0]).lower()


# ── allowed_tools override ────────────────────────────────────────────────────


class TestAllowedToolsOverride:
    def test_allowed_tools_stored_on_init(self) -> None:
        ctx = _make_ctx()
        orch = Orchestrator(ctx, allowed_tools=["read_text_file"])
        assert orch._allowed_tools == ["read_text_file"]

    def test_allowed_tools_none_by_default(self) -> None:
        ctx = _make_ctx()
        orch = _make_orchestrator(ctx)
        assert orch._allowed_tools is None

    @pytest.mark.asyncio
    async def test_allowed_tools_override_applied_during_turn(self) -> None:
        """ctx.cfg.tool.allowed_tools is overridden to the instance list during the execute stage."""
        ctx = _make_ctx()
        ctx.cfg.tool.allowed_tools = []
        captured: list[list[str]] = []

        async def _capture_allowed(*_: object, **__: object) -> None:
            captured.append(list(ctx.cfg.tool.allowed_tools))

        orch = Orchestrator(ctx, allowed_tools=["search_web"])
        with patch.object(
            orch._conversation_manager,
            "handle_memory_injection",
            side_effect=_capture_allowed,
        ):
            with patch.object(
                orch._llm_executor,
                "handle_llm_turn",
                AsyncMock(return_value=TurnResult(action="continue", answer="ok")),
            ):
                await orch.handle_turn("test")

        assert captured == [["search_web"]]

    @pytest.mark.asyncio
    async def test_original_allowed_tools_restored_after_turn(self) -> None:
        """ctx.cfg.tool.allowed_tools is restored to its original value after the turn."""
        ctx = _make_ctx()
        ctx.cfg.tool.allowed_tools = ["write_file"]
        orch = Orchestrator(ctx, allowed_tools=["search_web"])
        with patch.object(
            orch._conversation_manager, "handle_memory_injection", AsyncMock()
        ):
            with patch.object(
                orch._llm_executor,
                "handle_llm_turn",
                AsyncMock(return_value=TurnResult(action="continue", answer="ok")),
            ):
                await orch.handle_turn("test")
        assert ctx.cfg.tool.allowed_tools == ["write_file"]

    @pytest.mark.asyncio
    async def test_allowed_tools_none_leaves_config_unchanged(self) -> None:
        """When allowed_tools=None, ctx.cfg.tool.allowed_tools is not touched."""
        ctx = _make_ctx()
        ctx.cfg.tool.allowed_tools = ["read_text_file"]
        orch = _make_orchestrator(ctx)  # no allowed_tools override
        with patch.object(
            orch._conversation_manager, "handle_memory_injection", AsyncMock()
        ):
            with patch.object(
                orch._llm_executor,
                "handle_llm_turn",
                AsyncMock(return_value=TurnResult(action="continue", answer="ok")),
            ):
                await orch.handle_turn("test")
        assert ctx.cfg.tool.allowed_tools == ["read_text_file"]

    @pytest.mark.asyncio
    async def test_original_config_restored_even_on_error(self) -> None:
        """ctx.cfg.tool.allowed_tools is restored, and the halt is observable via
        on_error, when the workflow engine halts the turn after retries are
        exhausted."""
        ctx = _make_ctx()
        ctx.cfg.tool.allowed_tools = []
        on_error = MagicMock()
        orch = Orchestrator(ctx, allowed_tools=["search_web"], on_error=on_error)
        orch._diagnostic_store = MagicMock()

        async def _raise(*_: object, **__: object) -> None:
            raise RuntimeError("unexpected error")

        with patch.object(
            orch._conversation_manager, "handle_memory_injection", side_effect=_raise
        ):
            await orch.handle_turn("test")

        assert ctx.cfg.tool.allowed_tools == []
        assert ctx.workflow.active is False
        on_error.assert_called_once()
        (halt_exc,), _ = on_error.call_args
        assert isinstance(halt_exc, WorkflowHaltError)
        assert isinstance(halt_exc.__cause__, RuntimeError)


class TestHandleHistoryCompressionPersist:
    """Tests for _handle_history_compression persist behavior."""

    @pytest.mark.asyncio
    async def test_compress_persists_when_compressed(self) -> None:
        ctx = _make_ctx()
        ctx.services_required.hist_mgr.compress = AsyncMock(
            return_value=(
                [
                    {"role": "system", "content": "[Conversation summary]"},
                    {"role": "user", "content": "new"},
                ],
                CompressResult(
                    compressed_count=2, protected_count=0, summary_added=True
                ),
            )
        )
        orch = Orchestrator(ctx)
        await orch._conversation_manager.handle_history_compression()
        ctx.turn.persistence_boundary.replace_messages.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_compress_no_persist_when_noop(self) -> None:
        ctx = _make_ctx()
        ctx.services_required.hist_mgr.compress = AsyncMock(
            return_value=(
                [{"role": "user", "content": "unchanged"}],
                CompressResult(
                    compressed_count=0, protected_count=0, summary_added=False
                ),
            )
        )
        orch = Orchestrator(ctx)
        await orch._conversation_manager.handle_history_compression()
        ctx.turn.persistence_boundary.replace_messages.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_compress_persists_on_fallback_truncation(self) -> None:
        ctx = _make_ctx()
        ctx.services_required.hist_mgr.compress = AsyncMock(
            return_value=(
                [{"role": "user", "content": "remaining"}],
                CompressResult(
                    compressed_count=3,
                    protected_count=0,
                    summary_added=False,
                    is_fallback=True,
                ),
            )
        )
        orch = Orchestrator(ctx)
        await orch._conversation_manager.handle_history_compression()
        ctx.turn.persistence_boundary.replace_messages.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_compress_passes_full_history_to_replace_messages(
        self,
    ) -> None:
        """replace_messages() receives full history; ephemeral/memory-injected filtering
        is handled by _clear_previous_turn_ephemeral_messages() before every turn."""
        ctx = _make_ctx()
        kept = {"role": "user", "content": "hello"}
        ephemeral_msg = {"role": "system", "content": "hint", "_ephemeral": True}
        memory_injected_msg = {
            "role": "system",
            "content": "mem",
            "_memory_injected": True,
        }
        ctx.services_required.hist_mgr.compress = AsyncMock(
            return_value=(
                [kept, ephemeral_msg, memory_injected_msg],
                CompressResult(
                    compressed_count=1, protected_count=0, summary_added=False
                ),
            )
        )
        orch = Orchestrator(ctx)
        await orch._conversation_manager.handle_history_compression()
        saved = ctx.turn.persistence_boundary.replace_messages.call_args[0][0]
        assert len(saved) == 3
        assert saved[0] == kept
        assert saved[1] == ephemeral_msg
        assert saved[2] == memory_injected_msg


class TestInitWorkflowTaskResumeReuse:
    """Tests for Orchestrator._init_workflow_task() resume/reuse behavior."""

    def test_resume_reuses_existing_task_not_creates_duplicate(self) -> None:
        """Resuming a workflow task must call get_task_by_id(), not create_task()."""
        from unittest.mock import MagicMock, patch

        existing_task = MagicMock()
        existing_task.task_id = "existing-task-id"
        existing_task.workflow_id = "existing-wf-id"

        ctx = _make_ctx()

        with (
            patch(
                "agent.workflow_engine_adapter.get_task_by_id",
                return_value=existing_task,
            ),
            patch("agent.workflow_engine_adapter.create_task") as mock_create,
            patch("agent.orchestrator.StateStore"),
            patch("agent.workflow_engine_adapter.audit_workflow_start"),
        ):
            orch = Orchestrator(ctx)
            orch._workflow_def = MagicMock(version="test-v1")
            workflow_id, task = orch._workflow_adapter._init_workflow_task(
                ctx, "test-session", existing_task_id="existing-task-id"
            )
            assert workflow_id == "existing-wf-id"
            assert task.task_id == "existing-task-id"
            mock_create.assert_not_called()

    def test_resume_does_not_call_audit_workflow_start_for_existing_task(self) -> None:
        """When resuming an existing task, audit_workflow_start should NOT be called again."""
        from unittest.mock import MagicMock, patch

        existing_task = MagicMock()
        existing_task.task_id = "existing-task-id"
        existing_task.workflow_id = "existing-wf-id"

        ctx = _make_ctx()

        with (
            patch(
                "agent.workflow_engine_adapter.get_task_by_id",
                return_value=existing_task,
            ),
            patch("agent.workflow_engine_adapter.create_task"),
            patch("agent.orchestrator.StateStore"),
            patch("agent.workflow_engine_adapter.audit_workflow_start") as mock_audit,
        ):
            orch = Orchestrator(ctx)
            orch._workflow_def = MagicMock(version="test-v1")
            orch._workflow_adapter._init_workflow_task(
                ctx, "test-session", existing_task_id="existing-task-id"
            )
            mock_audit.assert_not_called()

    def test_resume_rejects_halted_task(self) -> None:
        """A task whose persisted status is 'halted' must not be silently resumed."""
        from unittest.mock import MagicMock, patch

        halted_task = MagicMock()
        halted_task.task_id = "halted-task-id"
        halted_task.workflow_id = "halted-wf-id"
        halted_task.status = "halted"

        ctx = _make_ctx()

        with (
            patch(
                "agent.workflow_engine_adapter.get_task_by_id", return_value=halted_task
            ),
            patch("agent.workflow_engine_adapter.create_task") as mock_create,
            patch("agent.orchestrator.StateStore"),
            patch("agent.workflow_engine_adapter.audit_workflow_start"),
        ):
            orch = Orchestrator(ctx)
            orch._workflow_def = MagicMock(version="test-v1")
            with pytest.raises(RuntimeError, match="halted"):
                orch._workflow_adapter._init_workflow_task(
                    ctx, "test-session", existing_task_id="halted-task-id"
                )
            mock_create.assert_not_called()


class TestEphemeralMessageLifecycle:
    """Regression coverage for requires/20260716_15_require.md /
    plans/20260717-001758_plan.md: _ephemeral (mode-classification hint) and
    _memory_injected (memory snippet) system messages must reach the LLM call
    for the turn they were created in, and be cleared before the *next*
    turn's LLM call -- not stripped by _sync_system_prompt() before the same
    turn's LLM call ever runs.
    """

    def _wire_memory_and_mode(self, ctx: MagicMock) -> None:
        ctx.cfg.mdq_rag_mode = (
            "rag"  # deterministic hint, bypasses classifier heuristics
        )
        ctx.conv.system_prompt_content = ""  # no system-prompt sync noise in this test
        memory = AsyncMock()
        snippet = MagicMock()
        snippet.text = "remembered fact"
        memory.on_user_prompt = AsyncMock(return_value=[snippet])
        ctx.services_required.memory = memory
        # LLMTurnRunner.run() requires non-empty workflow context.
        ctx.workflow.workflow_id = "wf-test"
        ctx.workflow.current_task_id = "task-test"
        ctx.turn.current_turn_id = "turn-test"

    @pytest.mark.asyncio
    async def test_ephemeral_and_memory_injected_present_in_same_turn_payload(
        self,
    ) -> None:
        ctx = _make_ctx()
        self._wire_memory_and_mode(ctx)
        orch = _make_orchestrator(ctx)

        seen_payloads: list[list[dict]] = []

        async def _mock_stream(
            _url: str, history: list, _tool_defs: list
        ) -> LLMResponse:
            seen_payloads.append(list(history))
            return LLMResponse(
                message={"role": "assistant", "content": "ok"}, finish_reason="stop"
            )

        ctx.services_required.llm.stream = _mock_stream

        adapter = orch._workflow_adapter
        await adapter._prepare_turn_input("what headings are here?", ctx)
        _answer, error_kind, _is_partial = await adapter._run_execute_stage(
            ctx,
            ctx.workflow.workflow_id,
            ctx.session.session_id,
            ctx.workflow.current_task_id,
            0.0,
        )

        assert error_kind is None
        assert len(seen_payloads) == 1
        payload = seen_payloads[0]
        ephemeral_msgs = [m for m in payload if m.get("_ephemeral")]
        memory_msgs = [m for m in payload if m.get("_memory_injected")]
        assert len(ephemeral_msgs) == 1
        assert len(memory_msgs) == 1
        assert "remembered fact" in memory_msgs[0]["content"]

    @pytest.mark.asyncio
    async def test_ephemeral_and_memory_injected_not_duplicated_across_turns(
        self,
    ) -> None:
        """Turn 2 gets its own fresh ephemeral/memory-injected messages (the
        memory/mode mocks fire every turn) -- the invariant under test is
        that turn 1's leftovers are cleared first, so turn 2's payload has
        exactly one of each (no accumulation), not turn 1's plus turn 2's.
        """
        ctx = _make_ctx()
        self._wire_memory_and_mode(ctx)
        orch = _make_orchestrator(ctx)

        seen_payloads: list[list[dict]] = []

        async def _mock_stream(
            _url: str, history: list, _tool_defs: list
        ) -> LLMResponse:
            seen_payloads.append(list(history))
            return LLMResponse(
                message={"role": "assistant", "content": "ok"}, finish_reason="stop"
            )

        ctx.services_required.llm.stream = _mock_stream

        adapter = orch._workflow_adapter
        await adapter._prepare_turn_input("what headings are here?", ctx)
        _answer, error_kind, _is_partial = await adapter._run_execute_stage(
            ctx,
            ctx.workflow.workflow_id,
            ctx.session.session_id,
            ctx.workflow.current_task_id,
            0.0,
        )
        await adapter._prepare_turn_input("second turn", ctx)
        _answer, error_kind, _is_partial = await adapter._run_execute_stage(
            ctx,
            ctx.workflow.workflow_id,
            ctx.session.session_id,
            ctx.workflow.current_task_id,
            0.0,
        )

        assert len(seen_payloads) == 2
        second_payload = seen_payloads[1]
        assert sum(1 for m in second_payload if m.get("_ephemeral")) == 1
        assert sum(1 for m in second_payload if m.get("_memory_injected")) == 1


class TestClearPreviousTurnEphemeralMessages:
    """Direct unit coverage for Orchestrator._clear_previous_turn_ephemeral_messages()."""

    def test_removes_ephemeral_and_memory_injected_messages(
        self,
    ) -> None:
        ctx = _make_ctx()
        ctx.conv.history = [
            {"role": "system", "content": "kept"},
            {"role": "system", "content": "eph", "_ephemeral": True},
            {"role": "system", "content": "mem", "_memory_injected": True},
        ]
        orch = _make_orchestrator(ctx)
        orch._conversation_manager.clear_previous_turn_ephemeral_messages()
        assert ctx.conv.history == [{"role": "system", "content": "kept"}]

    def test_non_ephemeral_messages_preserved(self) -> None:
        """Non-ephemeral user/assistant/system messages must survive unchanged."""
        ctx = _make_ctx()
        ctx.conv.history = [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "hi there"},
        ]
        orch = _make_orchestrator(ctx)
        orch._conversation_manager.clear_previous_turn_ephemeral_messages()
        assert len(ctx.conv.history) == 3
        assert ctx.conv.history[0] == {"role": "system", "content": "You are helpful."}
        assert ctx.conv.history[1] == {"role": "user", "content": "hello"}
        assert ctx.conv.history[2] == {"role": "assistant", "content": "hi there"}

    def test_empty_history_is_noop(self) -> None:
        """An empty conversation history must remain empty after clearing."""
        ctx = _make_ctx()
        ctx.conv.history = []
        orch = _make_orchestrator(ctx)
        orch._conversation_manager.clear_previous_turn_ephemeral_messages()
        assert ctx.conv.history == []

    def test_mixed_ephemeral_and_non_ephemeral_in_same_message_removed(self) -> None:
        """A message carrying both an ephemeral key AND a non-ephemeral role
        value must be removed — ephemeral key takes priority regardless of role."""
        ctx = _make_ctx()
        ctx.conv.history = [
            {"role": "user", "content": "eph-user", "_ephemeral": True},
            {"role": "assistant", "content": "eph-assist", "_memory_injected": True},
            {"role": "system", "content": "kept"},
        ]
        orch = _make_orchestrator(ctx)
        orch._conversation_manager.clear_previous_turn_ephemeral_messages()
        assert ctx.conv.history == [{"role": "system", "content": "kept"}]


class TestHistoryConstructionRoutedThroughAppendMessage:
    """Regression coverage for plans/20260726-093008_plan.md: the three
    history-construction call sites in orchestrator.py --
    _handle_memory_injection(), _append_user_message(), and
    _sync_system_prompt()'s insert branch -- route through
    ConversationState.append_message() / message_schema.validate_message()
    instead of raw ctx.conv.history.append()/.insert() calls, and produce the
    same message content as before for well-formed input.
    """

    @pytest.mark.asyncio
    async def test_handle_memory_injection_appends_unchanged_via_append_message(
        self,
    ) -> None:
        ctx = _make_ctx()
        memory = AsyncMock()
        snippet = MagicMock()
        snippet.text = "remembered fact"
        memory.on_user_prompt = AsyncMock(return_value=[snippet])
        ctx.services_required.memory = memory
        orch = _make_orchestrator(ctx)

        await orch._conversation_manager.handle_memory_injection(
            "what headings are here?"
        )

        assert len(ctx.conv.history) == 1
        msg = ctx.conv.history[0]
        assert msg["role"] == "system"
        assert msg["_memory_injected"] is True
        assert "remembered fact" in msg["content"]

    @pytest.mark.asyncio
    async def test_append_user_message_appends_unchanged_via_append_message(
        self,
    ) -> None:
        ctx = _make_ctx()
        ctx.conv.system_prompt_content = ""  # skip system-prompt sync noise
        orch = _make_orchestrator(ctx)

        await orch._conversation_manager.append_user_message("hello there")

        assert ctx.conv.history == [{"role": "user", "content": "hello there"}]

    def test_sync_system_prompt_insert_branch_inserts_unchanged(self) -> None:
        ctx = _make_ctx()
        ctx.conv.system_prompt_content = "You are a helpful assistant."
        ctx.conv.history = [{"role": "user", "content": "hi"}]
        orch = _make_orchestrator(ctx)

        orch._conversation_manager.sync_system_prompt()

        assert ctx.conv.history[0] == {
            "role": "system",
            "content": "You are a helpful assistant.",
        }
        assert ctx.conv.history[1] == {"role": "user", "content": "hi"}

    def test_sync_system_prompt_insert_branch_drops_message_on_validation_failure(
        self,
    ) -> None:
        """If validate_message() ever rejects the constructed system message,
        _sync_system_prompt() must log and skip the insert rather than
        inserting an unvalidated message."""
        ctx = _make_ctx()
        ctx.conv.system_prompt_content = "You are a helpful assistant."
        ctx.conv.history = [{"role": "user", "content": "hi"}]
        orch = _make_orchestrator(ctx)

        with patch(
            "agent.conversation_state_manager.validate_message",
            return_value=ValidationResult(False, "forced failure"),
        ):
            orch._conversation_manager.sync_system_prompt()

        assert ctx.conv.history == [{"role": "user", "content": "hi"}]


class TestDiscardAndLogConsecutiveFailures:
    """Locks in BG_FAILURE_THRESHOLD's log-level-only effect and the
    reset-on-success / reset-on-cancellation behavior of
    BgTaskMonitor.on_task_done's terminal-state handling."""

    @pytest.mark.asyncio
    async def test_four_consecutive_failures_each_log_via_warning(self) -> None:
        ctx = _make_ctx()
        ctx.turn = TurnState()
        orch = _make_orchestrator(ctx)

        with (
            patch("agent.bg_task_monitor.logger.warning") as mock_warning,
            patch("agent.bg_task_monitor.logger.error") as mock_error,
        ):
            for _ in range(4):
                task = await _await_raising("boom")
                orch._bg_task_monitor.on_task_done(task)

        assert orch._bg_task_monitor.get_consecutive_failures("test_bg_task") == 4
        # Only the first failure logs a warning; 2nd-4th are silent until threshold
        assert mock_warning.call_count == 1
        mock_error.assert_not_called()

    @pytest.mark.asyncio
    async def test_fifth_consecutive_failure_logs_via_error(self) -> None:
        ctx = _make_ctx()
        ctx.turn = TurnState()
        orch = _make_orchestrator(ctx)

        with (
            patch("agent.bg_task_monitor.logger.warning") as mock_warning,
            patch("agent.bg_task_monitor.logger.error") as mock_error,
        ):
            for _ in range(BG_FAILURE_THRESHOLD - 1):
                task = await _await_raising("boom")
                orch._bg_task_monitor.on_task_done(task)
            # 2nd-(N-1)th failures are silent (no logging)
            assert mock_warning.call_count == 1
            assert mock_error.call_count == 0
            task = await _await_raising("boom")
            orch._bg_task_monitor.on_task_done(task)

        assert (
            orch._bg_task_monitor.get_consecutive_failures("test_bg_task")
            == BG_FAILURE_THRESHOLD
        )
        # Only the first failure logged a warning; threshold failure logs error
        assert mock_warning.call_count == 1
        mock_error.assert_called_once()

    @pytest.mark.asyncio
    async def test_success_after_failures_resets_counter_to_zero(self) -> None:
        ctx = _make_ctx()
        ctx.turn = TurnState()
        orch = _make_orchestrator(ctx)

        for _ in range(3):
            task = await _await_raising("boom")
            orch._bg_task_monitor.on_task_done(task)
        assert orch._bg_task_monitor.get_consecutive_failures("test_bg_task") == 3

        success = await _successful()
        orch._bg_task_monitor.on_task_done(success)

        assert orch._bg_task_monitor.get_consecutive_failures("test_bg_task") == 0

    @pytest.mark.asyncio
    async def test_cancelled_error_after_failures_resets_counter_and_logs_nothing(
        self,
    ) -> None:
        ctx = _make_ctx()
        ctx.turn = TurnState()
        orch = _make_orchestrator(ctx)

        for _ in range(3):
            task = await _await_raising("boom")
            orch._bg_task_monitor.on_task_done(task)
        assert orch._bg_task_monitor.get_consecutive_failures("test_bg_task") == 3

        with (
            patch("agent.bg_task_monitor.logger.warning") as mock_warning,
            patch("agent.bg_task_monitor.logger.error") as mock_error,
        ):
            cancelled = await _make_cancelled("test_bg_task")
            orch._bg_task_monitor.on_task_done(cancelled)

        assert orch._bg_task_monitor.get_consecutive_failures("test_bg_task") == 0
        mock_warning.assert_not_called()
        mock_error.assert_not_called()

    @pytest.mark.asyncio
    async def test_threshold_reached_notifies_exactly_once_with_task_name(self) -> None:
        """_notify_bg_failure_threshold() must fire exactly once, at the failure
        that makes the counter == BG_FAILURE_THRESHOLD, and the notification
        message must include the task name."""
        on_error = MagicMock()
        ctx = _make_ctx()
        ctx.turn = TurnState()
        orch = _make_orchestrator(ctx, on_error=on_error)

        # First failure calls _on_error (not _notify_bg_failure_threshold) — skip it
        task = await _await_raising("boom", name="my_bg_task")
        orch._bg_task_monitor.on_task_done(task)
        assert on_error.call_count == 1
        on_error.reset_mock()

        # 2nd-(N-1)th failures are silent (no logging, no notifications)
        for _ in range(BG_FAILURE_THRESHOLD - 2):
            task = await _await_raising("boom", name="my_bg_task")
            orch._bg_task_monitor.on_task_done(task)

        # Nth failure (threshold) triggers _notify_bg_failure_threshold which calls _on_error
        task = await _await_raising("boom", name="my_bg_task")
        orch._bg_task_monitor.on_task_done(task)
        assert (
            orch._bg_task_monitor.get_consecutive_failures("my_bg_task")
            == BG_FAILURE_THRESHOLD
        )
        on_error.assert_called_once()
        err = on_error.call_args[0][0]
        assert "my_bg_task" in str(err)
        assert str(BG_FAILURE_THRESHOLD) in str(err)

        # A (N+1)th consecutive failure must not notify again (only == threshold, not >=).
        on_error.reset_mock()
        task = await _await_raising("boom", name="my_bg_task")
        orch._bg_task_monitor.on_task_done(task)
        on_error.assert_not_called()

    @pytest.mark.asyncio
    async def test_threshold_notification_falls_back_to_critical_log_on_error_raising(
        self,
    ) -> None:
        """If _on_error itself raises inside the threshold branch, the exception
        must be caught and logged via logger.critical, never propagated out of
        BgTaskMonitor.on_task_done()."""
        on_error = MagicMock(side_effect=RuntimeError("notification channel down"))
        ctx = _make_ctx()
        ctx.turn = TurnState()
        orch = _make_orchestrator(ctx, on_error=on_error)

        # First failure also calls _on_error — it will raise too (logged as ERROR)
        task = await _await_raising("boom", name="my_bg_task")
        orch._bg_task_monitor.on_task_done(task)

        with patch("agent.bg_task_monitor.logger.critical") as mock_critical:
            # 2nd-(N-1)th failures are silent
            for _ in range(BG_FAILURE_THRESHOLD - 2):
                task = await _await_raising("boom", name="my_bg_task")
                orch._bg_task_monitor.on_task_done(task)
            # Nth failure triggers _notify_bg_failure_threshold which calls _on_error
            task = await _await_raising("boom", name="my_bg_task")
            orch._bg_task_monitor.on_task_done(task)

        assert (
            orch._bg_task_monitor.get_consecutive_failures("my_bg_task")
            == BG_FAILURE_THRESHOLD
        )
        mock_critical.assert_called_once()
        assert "my_bg_task" in str(mock_critical.call_args)

    @pytest.mark.asyncio
    async def test_threshold_reached_with_pause_enabled_sets_pause_state(self) -> None:
        """When pause_on_critical_failure=True, reaching the threshold marks the
        offending task type as paused in _bg_pause_state."""
        ctx = _make_ctx()
        ctx.turn = TurnState()
        orch = _make_orchestrator(ctx, pause_on_critical_failure=True)

        # First failure does NOT set pause state (only calls _on_error)
        task = await _await_raising("boom", name="my_bg_task")
        orch._bg_task_monitor.on_task_done(task)
        assert orch._bg_task_monitor.bg_pause_state == {}

        # 2nd-(N-1)th failures are silent
        for _ in range(BG_FAILURE_THRESHOLD - 2):
            task = await _await_raising("boom", name="my_bg_task")
            orch._bg_task_monitor.on_task_done(task)

        # Nth failure triggers _notify_bg_failure_threshold which sets pause state
        task = await _await_raising("boom", name="my_bg_task")
        orch._bg_task_monitor.on_task_done(task)

        assert orch._bg_task_monitor.bg_pause_state == {"my_bg_task": True}

    @pytest.mark.asyncio
    async def test_threshold_reached_with_pause_disabled_leaves_pause_state_empty(
        self,
    ) -> None:
        """Default (pause_on_critical_failure=False) must not populate
        _bg_pause_state even after the threshold is reached."""
        ctx = _make_ctx()
        ctx.turn = TurnState()
        orch = _make_orchestrator(ctx)

        for _ in range(5):
            task = await _await_raising("boom", name="my_bg_task")
            orch._bg_task_monitor.on_task_done(task)

        assert orch._bg_task_monitor.bg_pause_state == {}


class TestHandleTurnPauseGuard:
    """Locks in the handle_turn() early-return guard added for the opt-in
    pause-on-critical-failure feature."""

    @pytest.mark.asyncio
    async def test_handle_turn_blocked_when_task_type_paused(self) -> None:
        on_error = MagicMock()
        ctx = _make_ctx()
        orch = _make_orchestrator(
            ctx, on_error=on_error, pause_on_critical_failure=True
        )
        orch._bg_task_monitor.bg_pause_state["my_bg_task"] = True

        await orch.handle_turn("do something")

        on_error.assert_called_once()
        err = on_error.call_args[0][0]
        assert isinstance(err, RuntimeError)
        assert "my_bg_task" in str(err)
        # LLM/workflow engine must not be invoked
        ctx.services_required.llm.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_turn_not_blocked_when_no_task_type_paused(self) -> None:
        on_error = MagicMock()
        ctx = _make_ctx()
        orch = _make_orchestrator(
            ctx, on_error=on_error, pause_on_critical_failure=True
        )
        orch._bg_task_monitor.bg_pause_state["my_bg_task"] = False

        with patch.object(
            orch._workflow_adapter,
            "_run_execute_stage",
            new=AsyncMock(return_value=("ok", None, False)),
        ):
            await orch.handle_turn("do something")

        for call in on_error.call_args_list:
            err = call[0][0]
            assert "paused due to repeated failures" not in str(err)


# ── _handle_workflow_engine: status preservation ──────────────────────────────


class TestHandleWorkflowEngineStatusPreservation:
    """Tests that _handle_workflow_engine does NOT overwrite terminal statuses
    already persisted by WorkflowEngine.run() when an exception occurs."""

    @pytest.mark.asyncio
    async def test_preserves_halted_status_via_halt_error(self) -> None:
        """When WorkflowEngine.run() raises WorkflowHaltError after persisting 'halted',
        the finally block must NOT overwrite it."""
        ctx = _make_ctx()
        orch = _make_orchestrator(ctx)

        mock_store = MagicMock()
        mock_store.update_task_status = MagicMock()
        mock_store.close = MagicMock()

        async def _raise_halt(task, plan_fn, execute_fn, verify_fn):
            mock_store.update_task_status("task-1", "halted")
            raise WorkflowHaltError("halted")

        mock_engine = MagicMock()
        mock_engine.run = AsyncMock(side_effect=_raise_halt)

        with (
            patch.object(
                orch._workflow_adapter,
                "init_workflow_task",
                return_value=("wf-1", MagicMock(task_id="task-1")),
            ),
            patch.object(orch._workflow_adapter, "activate_workflow"),
            patch.object(orch._workflow_adapter, "deactivate_workflow"),
            patch("agent.orchestrator.StateStore", return_value=mock_store),
            patch(
                "agent.workflow_engine_adapter.WorkflowEngine", return_value=mock_engine
            ),
        ):
            await orch._workflow_adapter.execute_turn("test line", time.time(), "")

        # The finally block should NOT have overwritten halted
        calls = [
            c
            for c in mock_store.update_task_status.call_args_list
            if c[0][1] != "halted"
        ]
        assert len(calls) == 0, (
            f"Unexpected status writes: {mock_store.update_task_status.call_args_list}"
        )

    @pytest.mark.asyncio
    async def test_preserves_halted_status_via_timeout_error(self) -> None:
        """When WorkflowEngine.run() raises WorkflowTimeoutError after persisting 'halted',
        the finally block must NOT overwrite it."""
        ctx = _make_ctx()
        orch = _make_orchestrator(ctx)

        mock_store = MagicMock()
        mock_store.update_task_status = MagicMock()
        mock_store.close = MagicMock()

        async def _raise_timeout(task, plan_fn, execute_fn, verify_fn):
            mock_store.update_task_status("task-1", "halted")
            raise WorkflowTimeoutError("timeout")

        mock_engine = MagicMock()
        mock_engine.run = AsyncMock(side_effect=_raise_timeout)

        with (
            patch.object(
                orch._workflow_adapter,
                "init_workflow_task",
                return_value=("wf-1", MagicMock(task_id="task-1")),
            ),
            patch.object(orch._workflow_adapter, "activate_workflow"),
            patch.object(orch._workflow_adapter, "deactivate_workflow"),
            patch("agent.orchestrator.StateStore", return_value=mock_store),
            patch(
                "agent.workflow_engine_adapter.WorkflowEngine", return_value=mock_engine
            ),
        ):
            await orch._workflow_adapter.execute_turn("test line", time.time(), "")

        # The finally block should NOT have overwritten halted
        calls = [
            c
            for c in mock_store.update_task_status.call_args_list
            if c[0][1] != "halted"
        ]
        assert len(calls) == 0, (
            f"Unexpected status writes: {mock_store.update_task_status.call_args_list}"
        )

    @pytest.mark.asyncio
    async def test_writes_completed_on_normal_success(
        self, tmp_path, monkeypatch
    ) -> None:
        """The engine is the sole writer of 'completed': a clean turn writes it exactly once."""

        async def execute_stage(
            *_a: object, **_k: object
        ) -> tuple[str, str | None, bool]:
            return ("answer", None, False)

        with _status_harness(
            tmp_path, monkeypatch=monkeypatch, execute_stage=execute_stage
        ) as (orch, store):
            await orch._workflow_adapter.execute_turn("hello", time.time(), "sess-1")

        assert store.calls == ["running", "completed"]
        assert store.task_status() == "completed"

    @pytest.mark.asyncio
    async def test_writes_failed_on_execute_failure(self) -> None:
        """Execute-stage failure (error_kind set) should still write 'failed'."""
        ctx = _make_ctx()
        orch = _make_orchestrator(ctx)

        mock_store = MagicMock()
        mock_store.update_task_status = MagicMock()
        mock_store.close = MagicMock()

        async def _execute_fail(task, plan_fn, execute_fn, verify_fn):
            await plan_fn()
            await execute_fn()
            await verify_fn()

        mock_engine = MagicMock()
        mock_engine.run = AsyncMock(side_effect=_execute_fail)

        with (
            patch.object(
                orch._workflow_adapter,
                "_init_workflow_task",
                return_value=("wf-1", MagicMock(task_id="task-1")),
            ),
            patch.object(orch._workflow_adapter, "_activate_workflow"),
            patch.object(orch._workflow_adapter, "_deactivate_workflow"),
            patch.object(
                orch._workflow_adapter,
                "_run_execute_stage",
                new=AsyncMock(return_value=("ok", "execute", False)),
            ),
            patch("agent.orchestrator.StateStore", return_value=mock_store),
            patch(
                "agent.workflow_engine_adapter.WorkflowEngine", return_value=mock_engine
            ),
        ):
            orch._state_store = mock_store
            orch._workflow_adapter._state_store = mock_store
            await orch._workflow_adapter.execute_turn("test line", time.time(), "")

        # The finally block should have written 'failed' because error_kind is set
        mock_store.update_task_status.assert_called_with("task-1", "failed")


class TestErrorKindPropagation:
    """Tests for error_kind derivation from TurnResult."""

    @pytest.mark.asyncio
    async def test_error_kind_derived_from_reason_on_guard_fail(self) -> None:
        """When guard triggers final-answer fallback that fails, error_kind uses result.reason."""
        ctx = _make_ctx()
        captured_events: list[str] = []
        ctx.services_required.audit_logger = MagicMock()
        ctx.services_required.audit_logger.info = lambda s: captured_events.append(s)
        orch = _make_orchestrator(ctx)

        tool_calls = [{"id": "c1"}]
        tool_response = LLMResponse(
            message={"role": "assistant", "content": "", "tool_calls": tool_calls},
            finish_reason="tool_calls",
        )
        final_response = LLMResponse(
            message={"role": "assistant", "content": "", "tool_calls": [{"id": "c2"}]},
            finish_reason="tool_calls",
        )

        with (
            patch(
                "agent.llm_turn_runner.LLMTurnRunner._stream_llm",
                AsyncMock(return_value=tool_response),
            ),
            patch(
                "agent.llm_turn_runner.LLMTurnRunner._stream_llm_final_answer",
                AsyncMock(return_value=final_response),
            ),
            patch.object(ToolLoopGuard, "check_all", return_value="Blocked by guard"),
        ):
            await orch.handle_turn("hello")

        assert len(captured_events) > 0
        event_dict = json.loads(captured_events[-1])
        assert event_dict["error_kind"] is not None
        assert "tool_loop_guard" in event_dict["error_kind"]

    @pytest.mark.asyncio
    async def test_error_kind_uses_action_when_no_reason(self) -> None:
        """When result.reason is empty, error_kind falls back to result.action."""
        ctx = _make_ctx()
        orch = _make_orchestrator(ctx)

        stop_response = LLMResponse(
            message=LLMMessage(role="assistant", content="ok", tool_calls=None),
            finish_reason="stop",
        )

        async def _mock_stream(*_args: object, **_kwargs: object) -> LLMResponse:
            return stop_response

        ctx.services_required.llm.stream = _mock_stream

        result = await orch._llm_executor.handle_llm_turn(
            "http://llm-test",
            workflow_id="wf-test",
            task_id="task-test",
            stage_id="execute",
            attempt_id="att-test",
        )

        assert result.action == "continue"
        assert result.answer == "ok"

    @pytest.mark.asyncio
    async def test_error_kind_propagates_through_handle_turn_on_transport_error(
        self,
    ) -> None:
        """LLMTransportError during handle_turn must propagate error_kind to audit logger."""
        ctx = _make_ctx()
        captured_events: list[str] = []
        ctx.services_required.audit_logger = MagicMock()
        ctx.services_required.audit_logger.info = lambda s: captured_events.append(s)
        orch = _make_orchestrator(ctx)

        err = _make_err(kind="CONNECT_ERROR", partial_text="")

        ctx.services_required.llm.stream = AsyncMock(side_effect=err)
        await orch.handle_turn("hello")

        assert len(captured_events) > 0
        event_dict = json.loads(captured_events[-1])
        assert event_dict["error_kind"].startswith("CONNECT_ERROR")


# ── Workflow load failure is fatal (ADR-001 Decision 4, ADR-004 INV-03) ───────


class TestWorkflowLoadFailureIsFatal:
    """A workflow definition that cannot be loaded stops Orchestrator
    construction; there is no fallback mode."""

    @pytest.mark.parametrize(
        "load_error",
        [
            WorkflowLoadError("invalid JSON: unexpected token"),
            FileNotFoundError("default.json is missing"),
        ],
    )
    def test_construction_raises_runtime_error_with_path_and_cause(
        self, load_error: Exception
    ) -> None:
        with patch("agent.orchestrator.WorkflowLoader") as loader_cls:
            loader_cls.return_value.load.side_effect = load_error
            with pytest.raises(RuntimeError) as excinfo:
                Orchestrator(_make_ctx())

        message = str(excinfo.value)
        assert "default.json" in message
        assert str(load_error) in message
        assert excinfo.value.__cause__ is load_error

    def test_no_workflow_engine_is_built_when_loading_fails(self) -> None:
        with (
            patch("agent.orchestrator.WorkflowLoader") as loader_cls,
            patch("agent.orchestrator.WorkflowEngine") as engine_cls,
        ):
            loader_cls.return_value.load.side_effect = WorkflowLoadError("bad")
            with pytest.raises(RuntimeError):
                Orchestrator(_make_ctx())

        engine_cls.assert_not_called()

    def test_startup_surfaces_the_construction_error(self) -> None:
        """The startup component initializer does not swallow the failure, so a
        broken workflow definition aborts startup like a failed preflight."""
        from agent.startup_component_init import ComponentInitializer

        initializer = ComponentInitializer(_make_ctx(), MagicMock())
        initializer._cmds = MagicMock()
        with (
            patch("agent.startup_component_init.init_tracer", return_value=None),
            patch("agent.orchestrator.WorkflowLoader") as loader_cls,
        ):
            loader_cls.return_value.load.side_effect = WorkflowLoadError("bad json")
            with pytest.raises(
                RuntimeError, match="Workflow definition failed to load"
            ):
                initializer._init_orchestrator()


class TestWorkflowStatus:
    """workflow_status() reports a loaded definition even between turns."""

    def test_enabled_when_idle_after_construction(self) -> None:
        ctx = _make_ctx()
        ctx.workflow.active = False
        orch = _make_orchestrator(ctx)

        assert orch.workflow_status() == {"tracking": "enabled"}

    def test_running_while_a_workflow_task_is_active(self) -> None:
        ctx = _make_ctx()
        ctx.workflow.active = True
        orch = _make_orchestrator(ctx)

        assert orch.workflow_status() == {"tracking": "running"}


# ── INV-02: centralized LlmTurnExecutor creation (ADR-014) ───────────────────


class TestSingleLlmTurnExecutorOwnership:
    """INV-02 regression (ADR-014): the Orchestrator centralizes LlmTurnExecutor
    creation — exactly one shared instance, held by no other component."""

    def test_orchestrator_creates_single_shared_llm_turn_executor(self) -> None:
        """The Orchestrator constructs a single LlmTurnExecutor and the workflow
        adapter shares that same instance rather than building its own."""
        ctx = _make_ctx()
        orch = _make_orchestrator(ctx)

        assert orch._llm_executor is not None
        assert isinstance(orch._llm_executor, LlmTurnExecutor)
        # Passed by reference to the adapter — no second instance is created.
        assert orch._workflow_adapter._llm_executor is orch._llm_executor


# ── Task status per turn outcome (real WorkflowEngine + real StateStore) ──────


class _ProbeStateStore(StateStore):
    """StateStore on a temp workflow.sqlite that records every update_task_status call."""

    def __init__(self, db_path: str) -> None:
        self._db = SQLiteHelper(db_path=db_path)
        self._db.open(write_mode=True, row_factory=True)
        self.calls: list[str] = []

    def update_task_status(self, task_id: str, status: str) -> None:
        self.calls.append(status)
        super().update_task_status(task_id, status)

    def task_status(self) -> str | None:
        rows = self._db.fetchall("SELECT status FROM tasks")
        return rows[0]["status"] if rows else None

    def attempt_rows(self) -> list[tuple[str, str, str | None]]:
        rows = self._db.fetchall("SELECT stage_id, status, error_kind FROM attempts")
        return [(r["stage_id"], r["status"], r["error_kind"]) for r in rows]


@contextmanager
def _status_harness(
    tmp_path: Path,
    *,
    monkeypatch: pytest.MonkeyPatch,
    execute_stage: Any,
    on_error: Any = None,
    max_attempts: int = 1,
    execute_timeout_sec: float = 5,
    execute_retryable: bool = True,
    store_cls: type[_ProbeStateStore] = _ProbeStateStore,
):
    """Real WorkflowEngine + real StateStore + real adapter on a temp workflow.sqlite.

    Restores the classes the autouse ``_patch_workflow_loader`` fixture patched, points the
    single shared StateStore at a temp DB, installs a real WorkflowDef, and drives the execute
    stage through a controlled ``_run_execute_stage`` replacement so no LLM service is required.
    """
    db_path = str(tmp_path / "workflow.sqlite")
    rag_path = str(tmp_path / "rag.sqlite")
    session_path = str(tmp_path / "session.sqlite")

    with patch(
        "db.helper.build_db_config",
        return_value=DbConfig(
            rag_db_path=rag_path,
            session_db_path=session_path,
            workflow_db_path=db_path,
        ),
    ):
        create_workflow_schema()

    store = store_cls(db_path)

    # Restore the real classes BEFORE constructing the orchestrator so it builds the real
    # WorkflowEngine and routes its single shared StateStore at our temp DB (factory form so
    # StateStore() returns our pre-built probe store rather than opening a second connection).
    monkeypatch.setattr("agent.orchestrator.StateStore", lambda: store)
    monkeypatch.setattr("agent.workflow_engine_adapter.WorkflowEngine", WorkflowEngine)
    monkeypatch.setattr("agent.workflow_engine_adapter.create_task", create_task)

    ctx = _make_ctx()
    orch = _make_orchestrator(ctx, on_error=on_error)

    stages = [
        StageDefinition(id="plan", timeout_sec=5, retryable=False),
        StageDefinition(
            id="execute", timeout_sec=execute_timeout_sec, retryable=execute_retryable
        ),
        StageDefinition(id="verify", timeout_sec=5, retryable=False),
    ]
    policy = RetryPolicy(max_attempts=max_attempts, backoff_sec=0)
    wdef = WorkflowDef(
        name="default", version="1.0.0", stages=stages, retry_policy=policy
    )
    orch._workflow_def = wdef
    orch._workflow_adapter._workflow_engine._wdef = wdef

    # Drive the execute stage without the LLM stack.
    monkeypatch.setattr(
        orch._workflow_adapter, "_run_execute_stage", execute_stage, raising=True
    )
    monkeypatch.setattr(
        "agent.workflow_engine_adapter.audit_workflow_start", MagicMock()
    )
    monkeypatch.setattr(
        "agent.workflow_engine_adapter.audit_stage_completed", MagicMock()
    )

    yield orch, store


class TestTaskStatusPerTurnOutcome:
    """Pins tasks.status for every exit path of WorkflowEngineAdapter.execute_turn against a
    real WorkflowEngine and a real StateStore on a temporary workflow.sqlite."""

    @pytest.mark.asyncio
    async def test_success_writes_completed_exactly_once(
        self, tmp_path, monkeypatch
    ) -> None:
        """Case A: a clean turn has the engine write running then completed exactly once."""

        async def execute_stage(
            *_a: object, **_k: object
        ) -> tuple[str, str | None, bool]:
            return ("answer", None, False)

        with _status_harness(
            tmp_path, monkeypatch=monkeypatch, execute_stage=execute_stage
        ) as (orch, store):
            await orch._workflow_adapter.execute_turn("hello", time.time(), "sess-1")

        assert store.task_status() == "completed"
        assert store.calls == ["running", "completed"]

    @pytest.mark.asyncio
    async def test_execute_stage_exception_marks_failed(
        self, tmp_path, monkeypatch
    ) -> None:
        """Case B: a non-retryable execute-stage failure has the engine write failed.

        The adapter's verify_fn is a no-op, so the adapter-visible "engine wrote failed" path is
        reproduced here with a non-retryable execute-stage exception (the identical adapter-visible
        outcome a verify-stage failure would produce).
        """

        async def execute_stage(*_a: object, **_k: object) -> object:
            raise RuntimeError("stage failure")

        with _status_harness(
            tmp_path,
            monkeypatch=monkeypatch,
            execute_stage=execute_stage,
            execute_retryable=False,
        ) as (orch, store):
            with pytest.raises(RuntimeError):
                await orch._workflow_adapter.execute_turn(
                    "hello", time.time(), "sess-1"
                )

        assert store.task_status() == "failed"
        assert store.calls == ["running", "failed"]
        assert ("execute", "failed", "exception") in store.attempt_rows()

    @pytest.mark.asyncio
    async def test_soft_turn_error_downgrades_to_failed(
        self, tmp_path, monkeypatch
    ) -> None:
        """Case C: a partial answer with an error_kind ends failed (adapter writes it)."""

        async def execute_stage(
            *_a: object, **_k: object
        ) -> tuple[str, str | None, bool]:
            return ("partial", "CONNECT_ERROR", True)

        with _status_harness(
            tmp_path, monkeypatch=monkeypatch, execute_stage=execute_stage
        ) as (orch, store):
            _, error_kind, is_partial = await orch._workflow_adapter.execute_turn(
                "hello", time.time(), "sess-1"
            )

        assert is_partial is True
        assert error_kind == "CONNECT_ERROR"
        assert store.task_status() == "failed"
        assert store.calls[-1] == "failed"

    @pytest.mark.asyncio
    async def test_execute_retry_exhaustion_halts(self, tmp_path, monkeypatch) -> None:
        """Case D: a retryable execute stage that fails past max_attempts ends halted."""

        async def execute_stage(*_a: object, **_k: object) -> object:
            raise RuntimeError("always fails")

        with _status_harness(
            tmp_path,
            monkeypatch=monkeypatch,
            execute_stage=execute_stage,
            max_attempts=2,
        ) as (orch, store):
            await orch._workflow_adapter.execute_turn("hello", time.time(), "sess-1")

        assert store.task_status() == "halted"
        assert store.calls == ["running", "halted"]
        assert store.attempt_rows().count(("execute", "failed", "exception")) == 2

    @pytest.mark.asyncio
    async def test_execute_stage_timeout_halts(self, tmp_path, monkeypatch) -> None:
        """Case F: an execute stage that exceeds its timeout ends halted with a timeout attempt."""

        async def execute_stage(*_a: object, **_k: object) -> object:
            await asyncio.sleep(0.2)
            return ("", None, False)

        with _status_harness(
            tmp_path,
            monkeypatch=monkeypatch,
            execute_stage=execute_stage,
            execute_timeout_sec=0.01,
        ) as (orch, store):
            await orch._workflow_adapter.execute_turn("hello", time.time(), "sess-1")

        assert store.task_status() == "halted"
        assert ("execute", "failed", "timeout") in store.attempt_rows()

    @pytest.mark.asyncio
    async def test_cancellation_records_halted_and_propagates(
        self, tmp_path, monkeypatch
    ) -> None:
        """Case E: cancelling a running turn records halted, propagates CancelledError, and
        leaves the execute attempt row open (closing it is out of scope)."""

        async def execute_stage(*_a: object, **_k: object) -> object:
            while True:
                await asyncio.sleep(0.01)

        with _status_harness(
            tmp_path, monkeypatch=monkeypatch, execute_stage=execute_stage
        ) as (orch, store):
            runner = asyncio.create_task(
                orch._workflow_adapter.execute_turn("hello", time.time(), "sess-1")
            )
            await asyncio.sleep(0.05)
            runner.cancel()
            with pytest.raises(asyncio.CancelledError):
                await runner

        assert store.task_status() == "halted"
        assert any(
            stage == "execute" and status == "running"
            for stage, status, _ in store.attempt_rows()
        )

    @pytest.mark.asyncio
    async def test_failure_before_engine_start_keeps_pending(
        self, tmp_path, monkeypatch
    ) -> None:
        """Case H: a failure inside task creation before the engine starts keeps pending."""

        async def execute_stage(
            *_a: object, **_k: object
        ) -> tuple[str, str | None, bool]:
            return ("", None, False)

        with _status_harness(
            tmp_path, monkeypatch=monkeypatch, execute_stage=execute_stage
        ) as (orch, store):
            monkeypatch.setattr(
                "agent.workflow_engine_adapter.audit_workflow_start",
                MagicMock(side_effect=RuntimeError("audit start failed")),
            )
            with pytest.raises(RuntimeError):
                await orch._workflow_adapter.execute_turn(
                    "hello", time.time(), "sess-1"
                )

        assert store.task_status() == "pending"
        assert store.calls == []

    @pytest.mark.asyncio
    async def test_status_write_failure_logs_error_without_on_error(
        self, tmp_path, monkeypatch, caplog
    ) -> None:
        """Log case: a failing status write is logged at ERROR, returns normally, skips on_error."""

        class _FailingStatusStore(_ProbeStateStore):
            def update_task_status(self, task_id: str, status: str) -> None:
                if status == "failed":
                    raise RuntimeError("db down")
                super().update_task_status(task_id, status)

        async def execute_stage(
            *_a: object, **_k: object
        ) -> tuple[str, str | None, bool]:
            return ("partial", "CONNECT_ERROR", True)

        with _status_harness(
            tmp_path,
            monkeypatch=monkeypatch,
            execute_stage=execute_stage,
            store_cls=_FailingStatusStore,
        ) as (orch, store):
            with caplog.at_level(logging.ERROR, logger="agent.workflow_engine_adapter"):
                await orch._workflow_adapter.execute_turn(
                    "hello", time.time(), "sess-1"
                )

            rows = store._db.fetchall("SELECT task_id FROM tasks")
            task_id = rows[0]["task_id"]
            assert any(
                "failed" in rec.getMessage() and task_id in rec.getMessage()
                for rec in caplog.records
            )

        assert store.task_status() == "completed"


# ── Turn-persistence boundary wiring (REQ-001, REQ-004, REQ-007) ───────────────


class TestTurnPersistenceBoundaryWiring:
    @pytest.mark.asyncio
    async def test_boundary_created_once_and_exposed_on_success(self) -> None:
        """A successful turn creates exactly one boundary via turn_boundary() and exposes
        it on ``ctx.turn.persistence_boundary`` so the write-routing callers can reach it
        without a threaded parameter (AC-001)."""
        ctx = _make_ctx()
        sentinel = object()
        ctx.session.turn_boundary = AsyncMock(return_value=sentinel)
        orch = _make_orchestrator(ctx)
        orch._workflow_adapter.execute_turn = AsyncMock(return_value=("", None, False))

        await orch._execute_turn("hello")

        ctx.session.turn_boundary.assert_awaited_once_with(ctx.conv)
        assert ctx.turn.persistence_boundary is sentinel

    @pytest.mark.asyncio
    async def test_persistence_failure_sets_distinct_error_kind_and_reraises(
        self,
    ) -> None:
        """A ``ConversationPersistenceError`` from the turn sets ``error_kind='persistence'``,
        leaves ``is_partial`` False (nothing was persisted), and re-raises so the REPL can
        surface it distinctly instead of swallowing it under the generic handler (REQ-007)."""
        ctx = _make_ctx()
        ctx.session.turn_boundary = AsyncMock(return_value=object())
        orch = _make_orchestrator(ctx)
        orch._workflow_adapter.execute_turn = AsyncMock(
            side_effect=ConversationPersistenceError(
                "history rolled back", cause=sqlite3.Error("boom")
            )
        )
        emit_end = AsyncMock()
        orch._audit_emitter.emit_turn_end = emit_end

        with pytest.raises(ConversationPersistenceError):
            await orch._execute_turn("hello")

        emit_end.assert_awaited_once()
        call_args = emit_end.call_args[0]
        assert call_args[3] == "persistence"  # error_kind
        assert call_args[4] is False  # is_partial

    @pytest.mark.asyncio
    async def test_real_boundary_compensates_and_restores_through_orchestrator(
        self,
    ) -> None:
        """End-to-end: a real boundary owns the turn. A mid-turn write failure makes the
        boundary compensate (delete only the failed turn's rows; prior-turn rows survive)
        and restore history to its turn-start snapshot, and the orchestrator re-raises the
        single ``ConversationPersistenceError`` (AC-002, AC-004)."""
        conn = sqlite3.connect(":memory:")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.executescript(_SCHEMA_SQL)
        conn.execute("INSERT INTO sessions (session_id) VALUES (1)")
        conn.execute(
            "INSERT INTO messages (session_id, role, content) "
            "VALUES (1, 'user', 'prior-1')"
        )
        conn.commit()

        state: dict[str, int] = {"fail_next": 0}

        def _make(target: str = "session") -> _FakeSQLiteHelper:
            fake = _FakeSQLiteHelper(conn)
            fake._state = state
            return fake

        with (
            patch("agent.session.SQLiteHelper", side_effect=_make),
            patch("agent.session_message_repo.SQLiteHelper", side_effect=_make),
        ):
            session = AgentSession()
            session.session_id = 1
            session._message_repo = SessionMessageRepository(1)

            conv = ConversationState()
            conv.history = [{"role": "user", "content": "prior-1"}]

            ctx = _make_ctx()
            ctx.session = session
            ctx.conv = conv
            ctx.turn = TurnState()

            orch = _make_orchestrator(ctx)

            async def _failing_execute_turn(line: str, started_at: float, _answer: str):
                boundary = ctx.turn.persistence_boundary
                await boundary.save("user", "turn-row")  # phase 1 commits (id 2)
                state["fail_next"] = 1
                await boundary.save_phase_grouped(
                    [("assistant", "answer", None, None)]
                )  # phase 2 fails

            orch._workflow_adapter.execute_turn = AsyncMock(
                side_effect=_failing_execute_turn
            )

            with pytest.raises(ConversationPersistenceError):
                await orch._execute_turn("hello")

            # AC-002: prior-turn row survives; zero of the failed turn's rows remain.
            rows = [
                (mid, role, content)
                for mid, role, content in conn.execute(
                    "SELECT message_id, role, content FROM messages ORDER BY message_id"
                ).fetchall()
            ]
            assert rows == [(1, "user", "prior-1")]

            # AC-004: memory restored element-wise to the turn-start snapshot.
            assert conv.history == [{"role": "user", "content": "prior-1"}]
