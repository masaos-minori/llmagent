"""agent/services/undo_service.py

Undo service — rolls back the last user+assistant turn.

Extracted from cmd_context._ContextMixin so the rollback logic can be
tested independently of the REPL.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from agent.services.exceptions import NothingToUndoError
from agent.services.models import UndoResult

if TYPE_CHECKING:
    from agent.context import AgentContext

logger = logging.getLogger(__name__)


def undo_last_turn(ctx: AgentContext) -> UndoResult:
    """Roll back the last user+assistant turn from history and DB.

    Strips preceding memory injection markers (_memory_injected=True),
    trims ctx.conv.history, decrements stat_turns, and calls session.undo_last_turn().
    Raises NothingToUndoError when no user message is found in history.
    """
    last_user_idx = next(
        (
            i
            for i in range(len(ctx.conv.history) - 1, -1, -1)
            if ctx.conv.history[i]["role"] == "user"
        ),
        None,
    )
    if last_user_idx is None:
        raise NothingToUndoError("Nothing to undo.")
    # Walk backwards from just before the user message to strip injected memory blocks.
    cut_idx = last_user_idx
    while cut_idx > 0 and ctx.conv.history[cut_idx - 1].get("_memory_injected"):
        cut_idx -= 1
    removed = len(ctx.conv.history) - cut_idx
    removed_messages = ctx.conv.history[cut_idx:]
    ctx.conv.history = ctx.conv.history[:cut_idx]
    ctx.stats.stat_turns = max(0, ctx.stats.stat_turns - 1)
    ctx.session.undo_last_turn()
    logger.info("Undo: removed %s messages from history", removed)
    warning: str | None = None
    if any(
        m.get("content", "").startswith("[Conversation summary]")
        for m in removed_messages
    ):
        warning = "/undo is targeting a compressed session summary; previous messages may not be recoverable."
        logger.warning(warning)
    return UndoResult(n_removed=removed, warning=warning)
