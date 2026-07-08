"""llm_transport_errors.py — LLM transport error handling for Orchestrator."""

from __future__ import annotations

from datetime import UTC, datetime

import orjson
from shared.llm_client import LLMTransportError
from shared.logger import Logger

from agent.context import AgentContext
from agent.diagnostic_store import DiagnosticStore

logger = Logger(__name__, "/opt/llm/logs/agent.log")


def handle_llm_transport_error(
    e: LLMTransportError,
    ctx: AgentContext,
    diagnostic_store: DiagnosticStore,
) -> bool:
    """Handle LLM transport error: partial or non-partial."""
    if e.partial_text:
        handle_partial_completion(e, ctx, diagnostic_store)
        return True
    handle_non_partial_error(e, ctx, diagnostic_store)
    return False


def handle_partial_completion(
    e: LLMTransportError,
    ctx: AgentContext,
    diagnostic_store: DiagnosticStore,
) -> None:
    """Save partial text to diagnostic channel only."""
    incomplete_msg = f"{e.partial_text}\n[INCOMPLETE: {e.kind}]"
    diagnostic_store.save(ctx.session.session_id, "llm_transport_error", incomplete_msg)
    diagnostic_store.save_partial_completion(
        session_id=ctx.session.session_id,
        turn=ctx.stats.stat_turns,
        reason=e.kind,
        content_length=len(e.partial_text),
    )
    ctx.services_required.llm.stat_partial_completions += 1
    logger.warning("Partial LLM completion saved: %s", e.kind)


def handle_non_partial_error(
    e: LLMTransportError,
    ctx: AgentContext,
    diagnostic_store: DiagnosticStore,
) -> None:
    """Save non-partial error to diagnostic channel and log."""
    diagnostic_store.save(
        ctx.session.session_id,
        "mid_turn_error",
        orjson.dumps(
            {
                "action": "pre_stream_error",
                "reason": "llm_transport_error_non_partial",
                "error_kind": e.kind,
                "timestamp": datetime.now(UTC).isoformat(),
            }
        ).decode(),
    )
    logger.error(
        "LLM transport error (pre-stream): %s status=%s",
        e.kind,
        e.status_code,
    )
