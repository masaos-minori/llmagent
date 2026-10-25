"""scripts/agent/services/conversation_service.py

Conversation lifecycle operations that should not live in command handlers.

These functions encapsulate state mutations on AgentContext that were previously
done directly inside cmd_context.py command handlers.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from agent.commands.mixin_base import refresh_session_correlation, reset_session_stats
from agent.services.enums import ConversationActionType
from agent.services.models import ConversationActionResult

if TYPE_CHECKING:
    from agent.context import AgentContext

logger = logging.getLogger(__name__)


def clear_conversation(
    ctx: AgentContext, *, new_session: bool = False
) -> ConversationActionResult:
    """Reset conversation history to system prompt only and clear session stats."""
    ctx.conv.history = ctx.conv.history[:1]
    reset_session_stats(ctx)
    if new_session:
        ctx.session.start()
        refresh_session_correlation(ctx)
        ctx.session.set_title("(New Session)")
        logger.info("History cleared; new session started")
        return ConversationActionResult(
            action=ConversationActionType.CLEAR,
            message="History cleared. New session started.",
        )
    logger.info("History cleared; session stats reset")
    return ConversationActionResult(
        action=ConversationActionType.CLEAR,
        message="History cleared. Session stats reset.",
    )
