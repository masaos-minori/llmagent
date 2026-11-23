"""tests/agent/workflow/test_no_workflow_bypass.py

ADR-001 INV-02: no call path reaches the tool-execution and LLM-turn chain except
through the Workflow Engine. A scan of scripts/ finds call sites of the chain symbols
only at the allowlisted sites, and the adapter reaches them only inside the engine run.

Scope is the Plan's proposed allowlist (UNK-01); an amendment changes the data here only.
"""

from __future__ import annotations

import ast
import time
from pathlib import Path
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock

import pytest
from agent.turn_result import TurnResult
from agent.workflow.workflow_engine import WorkflowStageFailure
from agent.workflow_engine_adapter import WorkflowEngineAdapter

from tests.agent.test_orchestrator import _make_ctx

_SCRIPTS = Path(__file__).resolve().parents[3] / "scripts"

# The only places allowed to reach the chain (Plan UNK-01, proposed scope).
ALLOWLIST: dict[str, set[str]] = {
    "handle_llm_turn": {"agent/workflow_engine_adapter.py"},
    "LLMTurnRunner": {"agent/llm_turn_executor.py"},
    "execute_all_tool_calls": {"agent/llm_turn_runner.py"},
}


def _scan() -> dict[str, list[str]]:
    """Call sites of the chain symbols, as scripts/-relative paths with line numbers."""
    found: dict[str, list[str]] = {symbol: [] for symbol in ALLOWLIST}
    for path in sorted(_SCRIPTS.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            name = (
                func.attr
                if isinstance(func, ast.Attribute)
                else (func.id if isinstance(func, ast.Name) else None)
            )
            if name in found:
                found[name].append(f"{path.relative_to(_SCRIPTS)}:{node.lineno}")
    return found


class _RecordingEngine:
    """A workflow engine that records whether its callbacks ran inside its own run."""

    def __init__(self, *, fail_before_callback: bool = False) -> None:
        self.version = "1.0.0-test"
        self.active = False
        self.run_started = False
        self.call_seen_inside_run = False
        self._fail_before_callback = fail_before_callback

    async def run(self, task: Any, *callbacks: Any) -> None:
        self.run_started = True
        self.active = True
        try:
            if self._fail_before_callback:
                raise WorkflowStageFailure("engine halted before the callback")
            for callback in callbacks:
                await callback()
        finally:
            self.active = False

    def build_turn_control_message(self, task_id: str) -> str:
        return ""


class _FakeConversationManager:
    """Sync and async call shapes the adapter expects from the conversation manager."""

    def clear_previous_turn_ephemeral_messages(self) -> None:
        return None

    async def handle_memory_injection(self, line: str) -> None:
        return None

    async def append_user_message(self, line: str) -> None:
        return None

    async def handle_history_compression(self) -> None:
        return None


def _record_call(engine: Any) -> TurnResult:
    """Record whether the engine run was active when the LLM turn was reached."""
    engine.call_seen_inside_run = engine.active
    return TurnResult(action="continue", answer="ok")


def _adapter_with_engine(*, engine: Any) -> WorkflowEngineAdapter:
    """Build an adapter over injected mocks whose LLM turn records engine state."""
    executor = MagicMock()
    executor.handle_llm_turn = AsyncMock(
        side_effect=lambda *args, **kwargs: _record_call(engine)
    )
    return WorkflowEngineAdapter(
        _make_ctx(),
        state_store=MagicMock(),
        workflow_engine=engine,
        conversation_manager=cast(Any, _FakeConversationManager()),
        llm_executor=executor,
    )


class TestNoCallPathOutsideTheEngine:
    @pytest.mark.repo_scan
    def test_chain_symbols_are_called_only_at_the_allowlisted_sites(self) -> None:
        found = _scan()
        for symbol, allowed in ALLOWLIST.items():
            sites = found[symbol]
            assert sites, f"{symbol}: no call site found, the scan is vacuous"
            offenders = [site for site in sites if site.split(":")[0] not in allowed]
            assert not offenders, (
                f"{symbol}: call sites outside the allowlist: {offenders}"
            )

    @pytest.mark.asyncio
    async def test_the_adapter_reaches_the_chain_only_inside_the_engine_run(
        self,
    ) -> None:
        """The adapter's only path to the LLM turn is the callback the engine invokes."""
        engine = _RecordingEngine()
        adapter = _adapter_with_engine(engine=engine)
        await adapter.execute_turn("hello", time.time(), "session-1")

        assert engine.run_started, "the adapter did not run the engine"
        assert engine.call_seen_inside_run is True, (
            "the LLM turn was reached outside the engine run"
        )

    @pytest.mark.asyncio
    async def test_the_chain_is_not_reached_when_the_engine_does_not_call_back(
        self,
    ) -> None:
        engine = _RecordingEngine(fail_before_callback=True)
        adapter = _adapter_with_engine(engine=engine)
        await adapter.execute_turn("hello", time.time(), "session-1")

        assert engine.run_started
        assert engine.call_seen_inside_run is False, (
            "the LLM turn was reached without the engine running the stage callback"
        )
