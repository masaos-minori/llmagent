#!/usr/bin/env python3
"""scripts/agent/llm_turn_executor.py

LLM streaming and result processing: turn execution, callback invocation,
result handling.

Extracted from orchestrator.py (_process_turn).
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from shared.llm_exceptions import LLMTransportError

from agent.llm_turn_runner import LLMTurnRunner
from agent.tool_loop_guard import ToolLoopGuard
from agent.turn_result import TurnResult

if TYPE_CHECKING:
    from agent.context import AgentContext
    from agent.diagnostic_store import DiagnosticStore

class LlmTurnExecutor:
    """Executes an LLM turn: streaming + inner tool-call loop.

    Responsibilities:
      - Run the LLM turn via LLMTurnRunner
      - Process TurnResult (answer, error_kind, is_partial)
      - Invoke callbacks on turn completion
    """

    def __init__(
        self,
        ctx: AgentContext,
        *,
        diagnostic_store: DiagnosticStore | None = None,
        tracer: Any = None,
        on_turn_start: Callable[[], None] | None = None,
        on_turn_end: Callable[[], None] | None = None,
        on_error: Callable[[Exception], None] | None = None,
        on_llm_wait_start: Callable[[], Any] | None = None,
        on_llm_wait_end: Callable[[], None] | None = None,
    ) -> None:
        """Initialize the LLM turn executor."""
        self._ctx = ctx
        self._diagnostic_store = diagnostic_store
        self._tracer = tracer
        self._on_turn_start = on_turn_start
        self._on_turn_end = on_turn_end
        self._on_error = on_error
        self._on_llm_wait_start = on_llm_wait_start
        self._on_llm_wait_end = on_llm_wait_end

    # ── Backward-compatible helper methods ────────────────────────────────────

    def call_on_llm_wait_end(self) -> None:
        """Invoke on_llm_wait_end if configured."""
        if self._on_llm_wait_end:
            self._on_llm_wait_end()

    def call_on_turn_end(self) -> None:
        """Invoke on_turn_end if configured."""
        if self._on_turn_end:
            self._on_turn_end()

    def call_on_error(self, exc: Exception) -> None:
        """Invoke on_error with exc if configured."""
        if self._on_error:
            self._on_error(exc)

    async def handle_llm_turn(
        self,
        llm_url: str,
        *,
        workflow_id: str = "",
        task_id: str = "",
        stage_id: str = "",
        attempt_id: str = "",
    ) -> TurnResult:
        """Execute one LLM turn and return the result."""
        guard = ToolLoopGuard(self._ctx)
        runner = LLMTurnRunner(
            self._ctx,
            guard,
            tracer=self._tracer,
        )
        return await runner.run(
            llm_url,
            workflow_id=workflow_id,
            task_id=task_id,
            stage_id=stage_id,
            attempt_id=attempt_id,
        )

    def process_turn_result(
        self,
        result: TurnResult,
    ) -> tuple[str, str | None, bool]:
        """Process a TurnResult and return (answer, error_kind, is_partial)."""
        answer = result.answer
        error_kind = None
        is_partial = False

        if result.action != "continue":
            error_kind = result.error_kind or result.reason or result.action
            if (
                isinstance(result.exception, LLMTransportError)
                and result.exception.partial_text
            ):
                is_partial = True

        return answer, error_kind, is_partial
