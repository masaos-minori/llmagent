"""scripts/agent/services/undo_service.py

Undo service — rolls back the last user+assistant turn.

Extracted from cmd_context._ContextMixin so the rollback logic can be
tested independently of the REPL.

Parity contract (REQ-007): memory history is trimmed to exactly the rows the
DB deletes. The DB delete runs first; the remaining memory tail is matched
against the deleted rows and trimmed by identity. When the match is ambiguous
(orphan DB rows absent from memory) the remaining conversation is reloaded
from the DB so memory and DB converge (REQ-003).
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, cast

from agent.services.models import UndoResult

if TYPE_CHECKING:
    from shared.types import LLMMessage

    from agent.context import AgentContext
    from agent.services.models import DeletedRow

logger = logging.getLogger(__name__)


def _match_deleted_tail(
    history: list[LLMMessage], deleted_rows: list[DeletedRow]
) -> int | None:
    """Return the cut index whose tail equals *deleted_rows*, else None.

    Walks the memory tail backwards, matching deleted_rows in reverse by
    (role, tool_call_id, content) with content optional when the DB row is
    NULL. Memory-only _memory_injected/_ephemeral artifacts are tolerated
    (skipped). Returns the index at which the matched suffix begins (after
    stripping any trailing artifacts), or None when the deleted rows do not
    form a contiguous matchable tail (ambiguous -> caller reloads, REQ-003).
    """
    if not deleted_rows:
        return None
    j = len(deleted_rows) - 1
    i = len(history) - 1
    while j >= 0 and i >= 0:
        msg = history[i]
        if msg.get("_memory_injected") or msg.get("_ephemeral"):
            i -= 1  # tolerate a memory-only artifact in the walk-back
            continue
        dr = deleted_rows[j]
        if msg.get("role") != dr.role:
            return None
        if msg.get("tool_call_id") != dr.tool_call_id:
            return None
        if dr.content is not None and msg.get("content") != dr.content:
            return None
        j -= 1
        i -= 1
    if j < 0:
        cut = i + 1
        while cut > 0 and (
            history[cut - 1].get("_memory_injected")
            or history[cut - 1].get("_ephemeral")
        ):
            cut -= 1
        return cut
    return None


def undo_last_turn(ctx: AgentContext) -> UndoResult:
    """Roll back the last user+assistant turn, gated by the compression boundary.

    Searches the last user message at history index >= ctx.conv.undo_floor,
    deletes from the DB before trimming history, and returns a blocked
    UndoResult (block_reason set) when nothing is undoable. On success trims
    history to exactly the deleted rows (restoring memory/DB parity),
    decrements stat_turns, and returns a success UndoResult.
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
    deleted_rows = ctx.session.undo_last_turn()  # DB first (row 03); list[DeletedRow]
    if not deleted_rows:  # blocked by the DB boundary
        return _undo_blocked()
    cut = _match_deleted_tail(ctx.conv.history, deleted_rows)
    if cut is None:
        # Ambiguous match (e.g. orphan DB rows absent from memory): reload the
        # remaining conversation from the DB and log the decision (REQ-003).
        # deleted_rows is non-empty, so the DB delete succeeded and session_id is set.
        remaining, _found, _floor = ctx.session.fetch_messages(
            cast(int, ctx.session.session_id)
        )
        ctx.conv.history = remaining
        logger.warning(
            "Undo: ambiguous match for %d deleted row(s) (%s); reloaded memory "
            "from DB to restore parity",
            len(deleted_rows),
            ", ".join(str(r.message_id) for r in deleted_rows),
        )
        return UndoResult(n_removed=len(deleted_rows), deleted_rows=deleted_rows)
    ctx.conv.history = ctx.conv.history[:cut]
    ctx.stats.stat_turns = max(0, ctx.stats.stat_turns - 1)
    logger.info(
        "Undo: removed %d messages (ids %s); memory trimmed to parity",
        len(deleted_rows),
        ", ".join(str(r.message_id) for r in deleted_rows),
    )
    return UndoResult(n_removed=len(deleted_rows), deleted_rows=deleted_rows)


def _undo_blocked() -> UndoResult:
    """Return a blocked UndoResult for the compression-boundary gate."""
    return UndoResult(
        n_removed=0,
        block_reason="Nothing to undo: at or before the compression boundary.",
    )
