"""scripts/agent/commands/session_title.py — Session title generation logic."""

from __future__ import annotations

import logging

from agent.commands.output_port import OutputPort
from agent.context import AgentContext
from agent.conversation_state_manager import get_captured_session_target
from agent.services.exceptions import SessionTitleGenerationError
from agent.services.session_title import SessionTitleService
from agent.session import SESSION_TITLE_DISPLAY_MAX_CHARS

logger = logging.getLogger(__name__)

SESSION_TITLE_TRUNCATE_AT = SESSION_TITLE_DISPLAY_MAX_CHARS - 3


class SessionTitleGen:
    """Handles session title generation (LLM-based with fallback)."""

    def __init__(self, ctx: AgentContext, out: OutputPort) -> None:
        """Initialize the session title generator with context and output port."""
        self._ctx = ctx
        self._out = out

    async def generate(self, first_input: str) -> None:
        """Generate and persist a session title via LLM (background task).

        REQ-004: pending state and the fallback write are bound to the session
        target captured when the task was created, so a stale task cannot flip
        state on a newer session.
        """
        target = get_captured_session_target()
        pending_sid = target.session_id if target is not None else None
        self._ctx.session.set_title_pending(True, session_id=pending_sid)
        try:
            await SessionTitleService().generate(self._ctx, first_input)
        except SessionTitleGenerationError as e:
            # AC-2: class name only — the raw reason can echo user input.
            logger.warning(
                "Session title generation failed (error=%s), using fallback",
                type(e).__name__,
            )
            clean_input = first_input.strip() if first_input else ""
            if not clean_input:
                fallback_title = "(New Session)"
            elif len(clean_input) > SESSION_TITLE_DISPLAY_MAX_CHARS:
                fallback_title = clean_input[:SESSION_TITLE_TRUNCATE_AT] + "..."
            else:
                fallback_title = clean_input
            try:
                self._ctx.session.set_title(fallback_title, target=target)
            except Exception as db_err:  # noqa: BLE001
                logger.error(
                    "Session title fallback set_title failed: %s (session_id=%s)",
                    type(db_err).__name__,
                    self._ctx.session.session_id,
                )
            else:
                if self._ctx.services_required.audit_logger is not None:
                    # REQ-005: ids and class name only — no fallback text, no
                    # raw reason (AC-2).
                    sid = (
                        target.session_id
                        if target is not None
                        else self._ctx.session.session_id
                    )
                    gen = (
                        target.generation
                        if target is not None
                        else self._ctx.session.generation
                    )
                    self._ctx.services_required.audit_logger.warning(
                        "session_title_fallback session_id=%s generation=%s error=%s",
                        sid,
                        gen,
                        type(e).__name__,
                    )
        finally:
            self._ctx.session.set_title_pending(False, session_id=pending_sid)
