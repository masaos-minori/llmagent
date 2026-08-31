#!/usr/bin/env python3
"""scripts/agent/audit_event_emitter.py

Audit event construction and emission for turn lifecycle events.

Extracted from orchestrator.py (_format_session_id, _build_turn_end_event,
_build_turn_end_metadata, _build_turn_end_llm_stats, _handle_turn_start).
"""

from __future__ import annotations

import time
import uuid
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from shared.json_utils import dumps as _json_dumps

if TYPE_CHECKING:
    from agent.context import AgentContext
    from agent.diagnostic_store import DiagnosticStore

# ── Public helpers ──────────────────────────────────────────────────────────────


def format_session_id(session_id: int | None) -> str:
    """Format session_id for audit logs, returning empty string when None."""
    return str(session_id) if session_id is not None else ""


# Backward-compatible alias for existing callers that import _format_session_id
_format_session_id = format_session_id

# ── AuditEventEmitter class ────────────────────────────────────────────────────


class AuditEventEmitter:
    """Constructs and emits audit events for turn lifecycle boundaries.

    Responsibilities:
      - Build turn_end event dicts with elapsed_ms, token stats, error_kind
      - Emit turn_start events to audit_logger
      - Format session IDs consistently across audit events
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
        on_first_turn: Callable[[str], Any] | None = None,
        on_llm_wait_start: Callable[[], Any] | None = None,
        on_llm_wait_end: Callable[[], None] | None = None,
    ) -> None:
        """Initialize the audit event emitter."""
        self._ctx = ctx
        self._diagnostic_store = diagnostic_store
        self._tracer = tracer
        self._on_turn_start = on_turn_start
        self._on_turn_end = on_turn_end
        self._on_error = on_error
        self._on_first_turn = on_first_turn
        self._on_llm_wait_start = on_llm_wait_start
        self._on_llm_wait_end = on_llm_wait_end

    @staticmethod
    def format_session_id(session_id: int | None) -> str:
        """Format session_id for audit logs, returning empty string when None."""
        return str(session_id) if session_id is not None else ""

    async def emit_turn_start(self) -> None:
        """Emit a turn_start audit event."""
        ctx = self._ctx
        if ctx.services_required.audit_logger is not None:
            ctx.turn.current_turn_id = str(uuid.uuid4())
            session_id = self.format_session_id(ctx.session.session_id) or "none"
            ctx.services_required.audit_logger.info(
                _json_dumps(
                    {
                        "event": "turn_start",
                        "task_id": ctx.turn.current_turn_id,
                        "worker_id": session_id,
                        "event_id": str(uuid.uuid4()),
                        "ts": time.time(),
                    },
                ),
            )

    def build_turn_end_metadata(self, ctx: AgentContext) -> dict[str, str]:
        """Build turn_end metadata (task_id, workflow_id, session_id)."""
        return {
            "task_id": ctx.turn.current_turn_id or "",
            "workflow_id": ctx.workflow.workflow_id or "",
            "session_id": self.format_session_id(ctx.session.session_id),
        }

    def build_turn_end_llm_stats(self, llm: Any) -> dict[str, int]:
        """Build turn_end LLM stats fields."""
        return {
            "parse_error_count": getattr(llm, "stat_parse_errors", 0),
            "heartbeat_timeout_count": getattr(llm, "stat_heartbeat_timeouts", 0),
            "reconnect_count": getattr(llm, "stat_reconnects", 0),
        }

    def build_turn_end_event(
        self,
        elapsed_ms: float,
        error_kind: str | None,
        task_id: str | None,
        is_partial: bool = False,
    ) -> dict[str, int | float | str | None]:
        """Build turn_end audit log event dict."""
        ctx = self._ctx
        return {
            "event": "turn_end",
            **self.build_turn_end_metadata(ctx),
            "elapsed_ms": elapsed_ms,
            "input_tokens": ctx.stats.stat_input_tokens,
            "output_tokens": ctx.stats.stat_output_tokens,
            **self.build_turn_end_llm_stats(ctx.services_required.llm),
            "partial_completion": is_partial,
            "error_kind": error_kind,
        }

    async def emit_turn_end(
        self,
        line: str,
        answer: str,
        turn_started_at: float,
        error_kind: str | None,
        is_partial: bool = False,
    ) -> None:
        """Emit a turn_end audit event and clear the current turn ID."""
        ctx = self._ctx
        elapsed_ms = round((time.perf_counter() - turn_started_at) * 1000, 1)
        if ctx.services_required.audit_logger is not None:
            event = self.build_turn_end_event(
                elapsed_ms, error_kind, ctx.turn.current_turn_id, is_partial
            )
            ctx.services_required.audit_logger.info(_json_dumps(event))
        ctx.turn.current_turn_id = None
