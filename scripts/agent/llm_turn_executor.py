#!/usr/bin/env python3
"""scripts/agent/llm_turn_executor.py

LLM streaming and result processing, extracted from Orchestrator (see
`issues/done/20260829-080923_refactor_001_orchestrator_separation.md`).
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from shared.llm_exceptions import LLMTransportError
from shared.logger import Logger

from agent.context import AgentContext
from agent.diagnostic_store import DiagnosticStore
from agent.llm_transport_errors import handle_llm_transport_error
from agent.llm_turn_runner import LLMTurnRunner
from agent.turn_result import TurnResult

logger = Logger(__name__, "/opt/llm/logs/agent.log")


class LlmTurnExecutor:
    """Executes an LLM streaming turn with wait/start/end callbacks and error handling."""

    def __init__(
        self,
        llm_runner: LLMTurnRunner,
        diagnostic_store: DiagnosticStore,
        *,
        on_turn_start: Callable[[], None] | None = None,
        on_turn_end: Callable[[], None] | None = None,
        on_error: Callable[[Exception], None] | None = None,
        on_llm_wait_start: Callable[[], Any] | None = None,
        on_llm_wait_end: Callable[[], None] | None = None,
    ) -> None:
        """Initialize with the LLM runner, diagnostic store, and optional callbacks."""
        self._llm_runner = llm_runner
        self._diagnostic_store = diagnostic_store
        self._on_turn_start = on_turn_start
        self._on_turn_end = on_turn_end
        self._on_error = on_error
        self._on_llm_wait_start = on_llm_wait_start
        self._on_llm_wait_end = on_llm_wait_end

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

    async def handle_llm_turn(self, ctx: AgentContext, llm_url: str) -> TurnResult:
        """Execute an LLM streaming turn with wait/start/end callbacks and error handling."""
        try:
            if self._on_llm_wait_start:
                await self._on_llm_wait_start()
            if self._on_turn_start:
                self._on_turn_start()
            with self._llm_runner._span_ctx("llm") as llm_span:
                llm_span.set_attribute("model_url", llm_url)
                result = await self._llm_runner.run(
                    llm_url,
                    workflow_id=ctx.workflow.workflow_id or "",
                    task_id=ctx.workflow.current_task_id or "",
                    stage_id="execute",
                    attempt_id=ctx.turn.current_turn_id or "",
                )
                logger.info("LLM response: %s", result.answer)
                if result.persist_as_assistant:
                    ctx.session.save("assistant", result.answer)
                if result.exception is not None:
                    # run() caught LLMTransportError internally; propagate callbacks
                    handle_llm_transport_error(
                        result.exception, ctx, self._diagnostic_store
                    )
                    self.call_on_llm_wait_end()
                    self.call_on_error(result.exception)
                    self.call_on_turn_end()
                else:
                    self.call_on_llm_wait_end()
                    self.call_on_turn_end()
                return result
        except LLMTransportError as e:
            # Reached when run() is mocked with side_effect=e (tests) or re-raises
            handle_llm_transport_error(e, ctx, self._diagnostic_store)
            self.call_on_llm_wait_end()
            self.call_on_error(e)
            return TurnResult(
                action="fail",
                answer="",
                error_kind=str(e),
                exception=e,
                persist_as_assistant=False,
            )
