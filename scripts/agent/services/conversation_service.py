"""scripts/agent/services/conversation_service.py

Conversation lifecycle operations that should not live in command handlers.

These functions encapsulate state mutations on AgentContext that were previously
done directly inside cmd_context.py command handlers.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from agent.commands.mixin_base import reset_session_stats
from agent.services.enums import ConversationActionType
from agent.services.models import ConversationActionResult

if TYPE_CHECKING:
    from agent.context import AgentContext
    from agent.services.session_transition import SessionTransitionService

logger = logging.getLogger(__name__)


async def clear_conversation(
    ctx: AgentContext,
    *,
    new_session: bool = False,
    transition_service: SessionTransitionService | None = None,
) -> ConversationActionResult:
    """Reset the in-memory conversation history and clear session stats.

    ``new_session=True`` delegates the whole switch (finalize the old session,
    start a new one, atomic commit) to the SessionTransitionService (REQ-002);
    the caller must supply it. The in-memory-only path keeps trimming history
    to the leading message and resetting stats.
    """
    if new_session:
        if transition_service is None:
            raise ValueError(
                "clear_conversation(new_session=True) requires a "
                "SessionTransitionService (REQ-002)"
            )
        await transition_service.clear_new()
        ctx.session.set_title("(New Session)")
        logger.info("History cleared; new session started")
        return ConversationActionResult(
            action=ConversationActionType.CLEAR,
            message=(
                "In-memory conversation history cleared. New session started. "
                "Persisted messages remain in session storage."
            ),
        )
    ctx.conv.history = ctx.conv.history[:1]
    reset_session_stats(ctx)
    logger.info("History cleared; session stats reset")
    return ConversationActionResult(
        action=ConversationActionType.CLEAR,
        message=(
            "In-memory conversation history cleared. Session stats reset. "
            "Persisted messages remain in session storage."
        ),
    )
