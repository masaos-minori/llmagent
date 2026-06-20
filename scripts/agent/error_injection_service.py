"""agent/error_injection_service.py
Stores mid-turn LLMTransportError diagnostics in the diagnostic channel
and tool-result store; does not modify conversation history.

This is a production path called by llm_turn_runner.py, not a test utility.
Do not add test-specific error injection to this class.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import orjson
from shared.tool_executor import format_transport_error

if TYPE_CHECKING:
    from shared.llm_client import LLMTransportError

    from agent.context import AgentContext

logger = logging.getLogger(__name__)


class ErrorInjectionService:
    """Service for handling synthetic error injection in agent turns."""

    def __init__(self, ctx: AgentContext) -> None:
        self._ctx = ctx

    def inject_mid_turn_error(self, e: LLMTransportError, turn: int) -> str:
        """Store mid-turn LLM error in diagnostic and tool-result channels; return summary."""
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
        if ctx.diagnostics is not None:
            ctx.diagnostics.save(
                ctx.session.session_id,
                "mid_turn_error",
                orjson.dumps(
                    {
                        "error_type": type(e).__name__,
                        "detail": err.detail,
                        "turn": turn,
                        "timestamp": datetime.now(UTC).isoformat(),
                    }
                ).decode(),
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
