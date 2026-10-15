"""scripts/agent/services/session_restore.py

Session restore service — rebuild history and switch the active session.

Extracted from cmd_session._SessionMixin so the restore logic can be
tested independently of the REPL.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, cast

from agent.commands.mixin_base import reset_session_stats
from agent.services.exceptions import SessionNoMessagesError, SessionNotFoundError
from agent.services.models import SessionRestoreResult

if TYPE_CHECKING:
    from shared.types import LLMMessage

    from agent.context import AgentContext

logger = logging.getLogger(__name__)


def _boundary_to_index(
    n_snapshot: int,
    messages: list[LLMMessage],
    *,
    system_prompt_set: bool,
) -> int:
    """Convert a snapshot message count into a rebuilt-history index.

    Adjusts for the single prepended system prompt that restore injects, so
    ``ctx.conv.undo_floor`` indexes the rebuilt history consistently with the
    compression path (rows 02/04). Returns 0 when the snapshot is empty.
    """
    if not n_snapshot:
        return 0
    snapshot_msgs = messages[:n_snapshot]
    system_count = sum(1 for m in snapshot_msgs if m.get("role") == "system")
    if system_prompt_set:
        return 1 + n_snapshot - system_count
    return n_snapshot


async def restore_session(ctx: AgentContext, session_id: int) -> SessionRestoreResult:
    """Restore session: rebuild history, switch session ID, reset stats.

    Raises SessionNotFoundError when the session does not exist.
    Raises SessionNoMessagesError when the session exists but has no messages.
    """
    messages, session_found, undo_floor_id = ctx.session.fetch_messages(session_id)
    if not session_found:
        raise SessionNotFoundError(f"Session {session_id} not found.")
    if not messages:
        raise SessionNoMessagesError(f"Session {session_id} has no messages.")
    if ctx.conv.system_prompt_content:
        system_msgs: list[LLMMessage] = cast(
            "list[LLMMessage]",
            [{"role": "system", "content": ctx.conv.system_prompt_content}],
        )
        non_system = [m for m in messages if m["role"] != "system"]
        await ctx.conv.replace_history(system_msgs + non_system)
    else:
        await ctx.conv.replace_history(messages)
    ctx.session.session_id = session_id
    reset_session_stats(ctx)
    # convert the persisted boundary row ID into a rebuilt-history index
    # (rows 02/04): nothing in the compressed snapshot is undoable after load.
    if undo_floor_id:
        n_snapshot = ctx.session.count_messages_up_to(session_id, undo_floor_id)
        ctx.conv.undo_floor = _boundary_to_index(
            n_snapshot,
            messages,
            system_prompt_set=bool(ctx.conv.system_prompt_content),
        )
    else:
        ctx.conv.undo_floor = 0
    logger.info("Session %s loaded: %s messages", session_id, len(messages))
    # Note: n_messages reflects the originally fetched row count, not the
    # post-sanitization stored count; a tampered/corrupted persisted row
    # dropped by replace_history() would make this a slight overstatement.
    # Acceptable for this defense-in-depth path (see implementation notes).
    return SessionRestoreResult(session_id=session_id, n_messages=len(messages))
