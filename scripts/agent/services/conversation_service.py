"""agent/services/conversation_service.py

Conversation lifecycle operations that should not live in command handlers.

These functions encapsulate state mutations on AgentContext that were previously
done directly inside cmd_context.py command handlers.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from agent.commands.mixin_base import reset_session_stats
from agent.services.enums import ConversationActionType
from agent.services.exceptions import ConversationStateError
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


def switch_system_prompt(ctx: AgentContext, name: str) -> ConversationActionResult:
    """Switch the active system prompt to a named preset.

    Raises ConversationStateError if the preset name is not found.
    """
    prompts = ctx.cfg.tool.system_prompts
    if name not in prompts:
        available = ", ".join(prompts.keys())
        raise ConversationStateError(f"Unknown preset {name!r}. Available: {available}")
    ctx.conv.system_prompt_name = name
    ctx.conv.system_prompt_content = prompts[name]
    if ctx.conv.history and ctx.conv.history[0]["role"] == "system":
        ctx.conv.history[0]["content"] = ctx.conv.system_prompt_content
    elif ctx.conv.system_prompt_content:
        ctx.conv.history.insert(
            0, {"role": "system", "content": ctx.conv.system_prompt_content}
        )
    logger.info("System prompt switched to %r", name)
    return ConversationActionResult(
        action=ConversationActionType.SWITCH_PROMPT,
        message=f"System prompt: {name}",
    )
