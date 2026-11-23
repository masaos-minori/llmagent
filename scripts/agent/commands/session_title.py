"""scripts/agent/commands/session_title.py — Session title generation logic."""

from __future__ import annotations

import logging

from agent.bg_task_monitor import current_task_target
from agent.commands.output_port import OutputPort
from agent.context import AgentContext
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

    @staticmethod
    def _fallback_title(first_input: str) -> str:
        """Return the fallback title: the (truncated) first input or a placeholder."""
        clean_input = first_input.strip() if first_input else ""
        if not clean_input:
            return "(New Session)"
        if len(clean_input) > SESSION_TITLE_DISPLAY_MAX_CHARS:
            return clean_input[:SESSION_TITLE_TRUNCATE_AT] + "..."
        return clean_input

    async def generate(self, first_input: str) -> None:
        """Generate and persist a session title via LLM (background task).

        Every write goes to the session target captured when the task was created
        (``current_task_target``), falling back to the live session when the task
        was not created through the first-turn path. Neither logs nor audit carry
        title text or raw failure reasons.
        """
        session = self._ctx.session
        target = current_task_target() or session.capture_target()
        session.set_title_pending(True, target.session_id)
        try:
            await SessionTitleService().generate(self._ctx, first_input)
        except SessionTitleGenerationError as e:
            error_class = type(e.__cause__ or e).__name__
            logger.warning(
                "Session title generation failed, using fallback: "
                "session=%s generation=%s error=%s",
                target.session_id,
                target.generation,
                error_class,
            )
            fallback_title = self._fallback_title(first_input)
            try:
                persisted = session.set_title(fallback_title, target=target)
            except Exception as db_err:  # noqa: BLE001 — a failed fallback write must not escape the background task
                logger.error(
                    "Session title fallback set_title failed: %s (session=%s)",
                    type(db_err).__name__,
                    target.session_id,
                )
            else:
                if persisted is False:
                    logger.info(
                        "Session title fallback discarded: session %s generation %s "
                        "is not current",
                        target.session_id,
                        target.generation,
                    )
                elif self._ctx.services_required.audit_logger is not None:
                    self._ctx.services_required.audit_logger.warning(
                        "session_title_fallback session_id=%s generation=%s error=%s",
                        target.session_id,
                        target.generation,
                        error_class,
                    )
        finally:
            session.set_title_pending(False, target.session_id)
