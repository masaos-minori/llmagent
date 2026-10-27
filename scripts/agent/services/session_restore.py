"""scripts/agent/services/session_restore.py

Session restore service — rebuild history and switch the active session.

Extracted from cmd_session._SessionMixin so the restore logic can be
tested independently of the REPL.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, cast

from agent.commands.mixin_base import refresh_session_correlation, reset_session_stats
from agent.services.exceptions import SessionNoMessagesError, SessionNotFoundError
from agent.services.models import SessionRestoreResult

if TYPE_CHECKING:
    from shared.types import LLMMessage

    from agent.context import AgentContext

logger = logging.getLogger(__name__)

# Identifiable signature written into tool-result rows synthesized at load
# time for assistant tool_calls that were never answered (interrupted turn).
INTERRUPTED_TOOL_CALL_MARKER = (
    "[interrupted] tool call did not complete before session termination"
)


def repair_orphan_tool_calls(
    messages: list[LLMMessage],
    session_id: int,
    *,
    boundary_index: int | None = None,
) -> tuple[list[LLMMessage], int]:
    """Pair assistant tool_calls rows with tool-result rows at load time.

    For every assistant row carrying ``tool_calls``, the immediately following
    contiguous ``role="tool"`` run answers some of the called ids; unanswered
    ids get a synthesized tool row (marker constant content) appended right
    after the run, mirroring ``tool_preparation._reject`` synthetic failures.
    Pure function over the fetched list: no DB write, so a second load
    reproduces identical output (REQ-004).

    Returns the repaired list and the number of synthesized rows that landed
    at or before ``boundary_index`` (the pre-repair snapshot count), so the
    caller can shift the undo_floor consistently (REQ-005). Logs one warning
    with the session id and total synthesized count when nonzero (REQ-003).
    """
    repaired: list[LLMMessage] = []
    synthesized_before = 0
    total_synthesized = 0
    i = 0
    n = len(messages)
    while i < n:
        msg = messages[i]
        if msg.get("role") == "assistant" and msg.get("tool_calls"):
            j = i + 1
            answered: set[str] = set()
            names: dict[str, str] = {}
            while j < n and messages[j].get("role") == "tool":
                tool_call_id = messages[j].get("tool_call_id")
                if tool_call_id is not None:
                    answered.add(tool_call_id)
                    name = messages[j].get("name")
                    if name is not None:
                        names[tool_call_id] = name
                j += 1
            repaired.append(msg)
            repaired.extend(messages[i + 1 : j])
            for tool_call in msg["tool_calls"]:
                tool_call_id = tool_call["id"]
                if tool_call_id in answered:
                    continue
                row: LLMMessage = {
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "content": INTERRUPTED_TOOL_CALL_MARKER,
                }
                name = names.get(tool_call_id)
                if name is not None:
                    row["name"] = name
                repaired.append(row)
                total_synthesized += 1
                if boundary_index is not None and j <= boundary_index:
                    synthesized_before += 1
            i = j
            continue
        repaired.append(msg)
        i += 1
    if total_synthesized:
        logger.warning(
            "Session %s repaired %d orphaned tool call(s) at load",
            session_id,
            total_synthesized,
        )
    return repaired, synthesized_before


def _boundary_to_index(
    n_snapshot: int,
    messages: list[LLMMessage],
    *,
    system_prompt_set: bool,
    insertions: int = 0,
) -> int:
    """Convert a snapshot message count into a rebuilt-history index.

    Adjusts for the single prepended system prompt that restore injects, so
    ``ctx.conv.undo_floor`` indexes the rebuilt history consistently with the
    compression path (rows 02/04). Returns 0 when the snapshot is empty.
    ``insertions`` is the number of rows synthesized by
    ``repair_orphan_tool_calls`` at or before the snapshot, added so the floor
    lands on the same turn as before repair (REQ-005).
    """
    if not n_snapshot:
        return 0
    snapshot_msgs = messages[:n_snapshot]
    system_count = sum(1 for m in snapshot_msgs if m.get("role") == "system")
    if system_prompt_set:
        return 1 + n_snapshot - system_count + insertions
    return n_snapshot + insertions


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
    # Compute the persisted boundary index BEFORE any session state is mutated
    # (REQ-001): a raised count_messages_up_to() must propagate with history,
    # session_id, and stats all left exactly as they were.
    n_snapshot: int | None = None
    if undo_floor_id:
        n_snapshot = ctx.session.count_messages_up_to(session_id, undo_floor_id)
    # Pair orphaned tool_calls rows BEFORE the boundary computation and
    # replace_history so the restored history is always well-formed (REQ-001).
    repaired, synthesized_before = repair_orphan_tool_calls(
        messages, session_id, boundary_index=n_snapshot
    )
    boundary_index: int | None = None
    if n_snapshot is not None:
        boundary_index = _boundary_to_index(
            n_snapshot,
            messages,
            system_prompt_set=bool(ctx.conv.system_prompt_content),
            insertions=synthesized_before,
        )
    if ctx.conv.system_prompt_content:
        system_msgs: list[LLMMessage] = cast(
            "list[LLMMessage]",
            [{"role": "system", "content": ctx.conv.system_prompt_content}],
        )
        non_system = [m for m in repaired if m["role"] != "system"]
        await ctx.conv.replace_history(system_msgs + non_system)
    else:
        await ctx.conv.replace_history(repaired)
    # convert the persisted boundary row ID into a rebuilt-history index
    # (rows 02/04): nothing in the compressed snapshot is undoable after load.
    if boundary_index is None:
        ctx.conv.undo_floor = 0
    else:
        live_len = len(ctx.conv.history)
        if boundary_index > live_len:
            # replace_history() dropped snapshot rows: clamp to the live history so the
            # floor can never point past its end. Conservative — /undo loses at most a
            # few extra turns, and no row below the boundary is ever exposed.
            logger.warning(
                "Session %s undo_floor clamped %d -> %d (%d row(s) dropped by validation)",
                session_id,
                boundary_index,
                live_len,
                boundary_index - live_len,
            )
            boundary_index = live_len
        ctx.conv.undo_floor = boundary_index
    ctx.session.session_id = session_id
    refresh_session_correlation(ctx)
    reset_session_stats(ctx)
    logger.info("Session %s loaded: %s messages", session_id, len(messages))
    # Note: n_messages reflects the originally fetched row count, not the
    # post-sanitization stored count; a tampered/corrupted persisted row
    # dropped by replace_history() would make this a slight overstatement.
    # Acceptable for this defense-in-depth path (see implementation notes).
    return SessionRestoreResult(session_id=session_id, n_messages=len(messages))
