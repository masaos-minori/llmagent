"""agent/error_injection_service.py
Converts a mid-turn LLMTransportError into a synthetic tool-result message
injected into conversation history, allowing the LLM to recover gracefully.

This is a production path called by llm_turn_runner.py, not a test utility.
Do not add test-specific error injection to this class.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from shared.tool_executor import format_transport_error

if TYPE_CHECKING:
    from shared.llm_client import LLMTransportError

    from agent.context import AgentContext

import logging

logger = logging.getLogger(__name__)


class ErrorInjectionService:
    """Service for handling synthetic error injection in agent turns."""

    def __init__(self, ctx: AgentContext) -> None:
        self._ctx = ctx

    def inject_mid_turn_error(self, e: LLMTransportError, turn: int) -> str:
        """Inject a synthetic tool-error message for a mid-turn LLM failure."""
        ctx = self._ctx
        err = format_transport_error(
            source="llm",
            phase=e.phase,
            kind=e.kind,
            url=e.url,
            status_code=e.status_code,
            retryable=e.retryable,
            partial=bool(e.partial_text),
        )
        ctx.conv.history.append(
            {
                "role": "tool",
                "content": err.detail,
                "name": "llm_transport_error",
                "tool_call_id": f"synthetic_{uuid.uuid4().hex[:8]}",
            },
        )
        ctx.tool_result_store.store(
            session_id=ctx.session.session_id,
            turn=turn,
            tool_name="llm_transport_error",
            args_masked="{}",
            full_text=err.detail,
            summary=err.summary,
            is_error=True,
        )
        logger.warning(
            "LLM transport error during tool continuation (turn=%s): %s",
            turn,
            e.kind,
        )
        return err.summary
