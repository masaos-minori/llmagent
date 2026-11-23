"""scripts/agent/services/session_restore.py

Session restore builder — rebuild the history of a stored session off to the side.

The live context is never written here; the transition service commits the result.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, cast

from agent.history import is_conversation_summary
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
    reproduces identical output.

    Returns the repaired list and the number of synthesized rows that landed
    at or before ``boundary_index`` (the pre-repair snapshot count), so the
    caller can shift the undo_floor consistently. Logs one warning
    with the session id and total synthesized count when nonzero.
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
    lands on the same turn as before repair.
    """
    if not n_snapshot:
        return 0
    snapshot_msgs = messages[:n_snapshot]
    # The restored canonical summary row is re-inserted by restore_session, so it
    # counts as present in the rebuilt history instead of a dropped system row.
    system_count = sum(
        1
        for m in snapshot_msgs
        if m.get("role") == "system" and not is_conversation_summary(m)
    )
    if system_prompt_set:
        return 1 + n_snapshot - system_count + insertions
    return n_snapshot + insertions


def _restored_summary_msgs(
    repaired: list[LLMMessage], session_id: int
) -> list[LLMMessage]:
    """Return the canonical summary row to re-insert after the prompt, or [].

    Keeps the last summary-shaped row (the most recent compression) and warns
    once when older extra summary rows are dropped (Plan: single-summary rule).
    The row is rebuilt with only ``role``/``content`` so it carries no stored
    markers (untrusted-restore).
    """
    summary_rows = [m for m in repaired if is_conversation_summary(m)]
    if len(summary_rows) > 1:
        logger.warning(
            "Session %s dropped %d extra summary row(s); kept the most recent",
            session_id,
            len(summary_rows) - 1,
        )
    return (
        [{"role": "system", "content": summary_rows[-1]["content"]}]
        if summary_rows
        else []
    )


@dataclass(frozen=True)
class RestoredSessionState:
    """State rebuilt from a stored session, ready to be committed atomically.

    Built off to the side: producing it never touches the live context.
    """

    result: SessionRestoreResult
    history: tuple[LLMMessage, ...]
    undo_floor: int


async def _validated_history(candidate: list[LLMMessage]) -> list[LLMMessage]:
    """Run ``candidate`` through the untrusted-restore validation on a scratch state."""
    from agent.context import ConversationState  # lazy import: avoids an import cycle

    scratch = ConversationState()
    await scratch.replace_history(candidate)
    return list(scratch.history)


def _clamp_boundary(boundary_index: int, live_len: int, session_id: int) -> int:
    """Clamp the undo floor into the rebuilt history, warning when rows were dropped."""
    if boundary_index <= live_len:
        return boundary_index
    # replace_history() dropped snapshot rows: clamp to the live history so the
    # floor can never point past its end. Conservative: /undo loses at most a few
    # extra turns, and no row below the boundary is ever exposed.
    logger.warning(
        "Session %s undo_floor clamped %d -> %d (%d row(s) dropped by validation)",
        session_id,
        boundary_index,
        live_len,
        boundary_index - live_len,
    )
    return live_len


async def restore_session(ctx: AgentContext, session_id: int) -> RestoredSessionState:
    """Build the restored state of a stored session without mutating ``ctx``.

    The caller (``SessionTransitionService``) commits the returned state. Reads
    only: the live history, undo floor, session id, correlation id and statistics
    are never written here.

    Raises SessionNotFoundError when the session does not exist.
    Raises SessionNoMessagesError when the session exists but has no messages.
    """
    messages, session_found, undo_floor_id = ctx.session.fetch_messages(session_id)
    if not session_found:
        raise SessionNotFoundError(f"Session {session_id} not found.")
    if not messages:
        raise SessionNoMessagesError(f"Session {session_id} has no messages.")
    # Compute the persisted boundary index first: a raised count_messages_up_to()
    # must propagate before anything is built.
    n_snapshot: int | None = None
    if undo_floor_id:
        n_snapshot = ctx.session.count_messages_up_to(session_id, undo_floor_id)
    # Pair orphaned tool_calls rows BEFORE the boundary computation so the restored
    # history is always well-formed.
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
    candidate: list[LLMMessage] = repaired
    if ctx.conv.system_prompt_content:
        system_msgs: list[LLMMessage] = cast(
            "list[LLMMessage]",
            [{"role": "system", "content": ctx.conv.system_prompt_content}],
        )
        non_system = [m for m in repaired if m["role"] != "system"]
        candidate = (
            system_msgs + _restored_summary_msgs(repaired, session_id) + non_system
        )
    history = await _validated_history(candidate)
    # convert the persisted boundary row ID into a rebuilt-history index: nothing
    # in the compressed snapshot is undoable after load.
    undo_floor = (
        0
        if boundary_index is None
        else _clamp_boundary(boundary_index, len(history), session_id)
    )
    logger.info("Session %s loaded: %s messages", session_id, len(messages))
    result = SessionRestoreResult(
        session_id=session_id,
        n_messages=len(messages),
        fetched=len(messages),
        synthesized=len(repaired) - len(messages),
        dropped=len(candidate) - len(history),
        restored=len(history),
    )
    return RestoredSessionState(
        result=result, history=tuple(history), undo_floor=undo_floor
    )
