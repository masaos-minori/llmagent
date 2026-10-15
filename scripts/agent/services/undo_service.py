"""scripts/agent/services/undo_service.py

Undo service — rolls back the last user+assistant turn.

Extracted from cmd_context._ContextMixin so the rollback logic can be
tested independently of the REPL.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from agent.services.models import UndoResult

if TYPE_CHECKING:
    from agent.context import AgentContext

logger = logging.getLogger(__name__)


def undo_last_turn(ctx: AgentContext) -> UndoResult:
    """Roll back the last user+assistant turn, gated by the compression boundary.

    Searches the last user message at history index >= ctx.conv.undo_floor,
    deletes from the DB before trimming history, and returns a blocked
    UndoResult (block_reason set) when nothing is undoable. On success trims
    history, decrements stat_turns, and returns a success UndoResult.
    """
    last_user_idx = next(
        (
            i
            for i in range(len(ctx.conv.history) - 1, ctx.conv.undo_floor - 1, -1)
            if ctx.conv.history[i]["role"] == "user"
        ),
        None,
    )
    if last_user_idx is None:
        return _undo_blocked()
    # Walk backwards from just before the user message to strip turn-scoped
    # artifacts (injected memory blocks and ephemeral mode hints).
    cut_idx = last_user_idx
    while cut_idx > 0 and (
        ctx.conv.history[cut_idx - 1].get("_memory_injected")
        or ctx.conv.history[cut_idx - 1].get("_ephemeral")
    ):
        cut_idx -= 1
    removed = ctx.session.undo_last_turn()  # DB first (row 03)
    if removed == 0:  # blocked by the DB boundary
        return _undo_blocked()
    # trim history AFTER the DB delete succeeds
    ctx.conv.history = ctx.conv.history[:cut_idx]
    ctx.stats.stat_turns = max(0, ctx.stats.stat_turns - 1)
    logger.info("Undo: removed %s messages from history", cut_idx)
    return UndoResult(n_removed=removed)


def _undo_blocked() -> UndoResult:
    """Return a blocked UndoResult for the compression-boundary gate."""
    return UndoResult(
        n_removed=0,
        block_reason="Nothing to undo: at or before the compression boundary.",
    )
