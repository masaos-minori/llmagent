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
from agent.services.session_transition import SessionTransitionService

if TYPE_CHECKING:
    from agent.context import AgentContext

logger = logging.getLogger(__name__)


async def clear_conversation(
    ctx: AgentContext, *, new_session: bool = False
) -> ConversationActionResult:
    """Reset in-memory conversation history to the system prompt and clear stats.

    Persisted messages and long-term Memory are not touched. ``new_session``
    switches through ``SessionTransitionService``: the old session is finalized
    first, and a failed switch leaves the old session intact (the error
    propagates; ``SessionTransitionRefusedError`` when a turn is running).
    """
    if new_session:
        await SessionTransitionService.for_context(ctx).clear_new()
        ctx.session.set_title("(New Session)")
        logger.info("History cleared; new session started")
        return ConversationActionResult(
            action=ConversationActionType.CLEAR,
            message=(
                "In-memory conversation history cleared. New session started; "
                "the previous session was finalized and its saved messages remain "
                "in the database (/session load restores them)."
            ),
        )
    ctx.conv.history = ctx.conv.history[:1]
    reset_session_stats(ctx)
    logger.info("History cleared; session stats reset")
    return ConversationActionResult(
        action=ConversationActionType.CLEAR,
        message=(
            "In-memory conversation history cleared and session stats reset. "
            "Saved messages and long-term Memory are unchanged "
            "(/session load restores the saved messages)."
        ),
    )
