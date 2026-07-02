"""session_title.py — Session title generation logic."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from agent.commands.mixin_base import MixinBase

from agent.services.exceptions import SessionTitleGenerationError
from agent.services.session_title import SessionTitleService

logger = logging.getLogger(__name__)

SESSION_TITLE_MAX_CHARS = 32
SESSION_TITLE_TRUNCATE_AT = SESSION_TITLE_MAX_CHARS - 3


class SessionTitleGen:
    """Handles session title generation (LLM-based with fallback)."""

    def __init__(self, ctx: Any, out: Any) -> None:
        self._ctx = ctx
        self._out = out

    async def generate(self, first_input: str) -> None:
        """Generate and persist a session title via LLM (background task)."""
        self._ctx.session.set_title_pending(True)
        try:
            await SessionTitleService().generate(self._ctx, first_input)
        except SessionTitleGenerationError as e:
            logger.warning("Session title generation failed, using fallback: %s", e)
            clean_input = first_input.strip() if first_input else ""
            if not clean_input:
                fallback_title = "(New Session)"
            elif len(clean_input) > SESSION_TITLE_MAX_CHARS:
                fallback_title = clean_input[:SESSION_TITLE_TRUNCATE_AT] + "..."
            else:
                fallback_title = clean_input
            try:
                self._ctx.session.set_title(fallback_title)
            except Exception as db_err:  # noqa: BLE001
                logger.error(
                    "Session title fallback set_title failed: %s (session_id=%s)",
                    db_err,
                    self._ctx.session.session_id,
                )
            else:
                if self._ctx.services_required.audit_logger is not None:
                    self._ctx.services_required.audit_logger.warning(
                        "session_title_fallback session_id=%s fallback=%r reason=%s",
                        self._ctx.session.session_id,
                        fallback_title,
                        e,
                    )
        finally:
            self._ctx.session.set_title_pending(False)
