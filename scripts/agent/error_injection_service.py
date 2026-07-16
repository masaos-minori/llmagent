"""agent/error_injection_service.py

Stores mid-turn LLMTransportError diagnostics in the diagnostic channel only;
does not write to any store and does not modify conversation history.

This is a production path called by llm_turn_runner.py, not a test utility.
Do not add test-specific error injection to this class.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from shared.json_utils import dumps, now_iso_raw
from shared.tool_executor_helpers import format_transport_error

if TYPE_CHECKING:
    from shared.llm_exceptions import LLMTransportError

    from agent.context import AgentContext

logger = logging.getLogger(__name__)


class ErrorInjectionService:
    """Service for handling synthetic error injection in agent turns."""

    def __init__(self, ctx: AgentContext) -> None:
        self._ctx = ctx

    def inject_mid_turn_error(self, e: LLMTransportError, turn: int) -> str:
        """Store mid-turn LLM error in the diagnostic channel; return summary."""
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
                dumps(
                    {
                        "error_type": type(e).__name__,
                        "detail": err.detail,
                        "turn": turn,
                        "timestamp": now_iso_raw(),
                    }
                ),
            )
        logger.warning(
            "LLM transport error during tool continuation (turn=%s): %s",
            turn,
            e.kind,
        )
        return str(err.summary)
