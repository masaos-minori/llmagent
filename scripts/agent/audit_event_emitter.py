#!/usr/bin/env python3
"""scripts/agent/audit_event_emitter.py

Audit event construction for turn-end logging, extracted from Orchestrator
(see `issues/done/20260829-080923_refactor_001_orchestrator_separation.md`).
"""

from __future__ import annotations

from typing import Any

from agent.context import AgentContext


def _format_session_id(session_id: int | None) -> str:
    """Format session_id for audit logs, returning empty string when None."""
    return str(session_id) if session_id is not None else ""


class AuditEventEmitter:
    """Builds the turn_end audit log event dict from context and LLM stats."""

    def build_turn_end_metadata(self, ctx: AgentContext) -> dict[str, str]:
        """Build turn_end metadata (task_id, workflow_id, session_id)."""
        return {
            "task_id": ctx.turn.current_turn_id or "",
            "workflow_id": ctx.workflow.workflow_id or "",
            "session_id": _format_session_id(ctx.session.session_id),
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
        ctx: AgentContext,
        elapsed_ms: float,
        error_kind: str | None,
        task_id: str | None,
        is_partial: bool = False,
    ) -> dict[str, int | float | str | None]:
        """Build turn_end audit log event dict."""
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
