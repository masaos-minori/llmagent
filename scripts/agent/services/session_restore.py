"""scripts/agent/services/session_restore.py

Session restore service — rebuild history and switch the active session.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, cast

from agent.context import ConversationState
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
    """State built by :func:`restore_session`, waiting to be committed.

    The transition service (session_transition) applies these fields to the
    context atomically; ``restore_session`` itself never mutates the context
    (REQ-002). ``history`` is already validated through the untrusted-restore
    pipeline, so the commit can assign it directly.
    """

    history: list[LLMMessage]
    undo_floor: int
    result: SessionRestoreResult


async def restore_session(ctx: AgentContext, session_id: int) -> RestoredSessionState:
    """Build the restored session state without mutating the context.

    Validates and rebuilds the history, computes the undo floor, and reports
    the fetched, synthesized, dropped, and restored counts (REQ-009). History,
    undo_floor, session id, correlation, and stats are left untouched here;
    the transition service performs the commit (REQ-002).

    Raises SessionNotFoundError when the session does not exist.
    Raises SessionNoMessagesError when the session exists but has no messages.
    """
    messages, session_found, undo_floor_id = ctx.session.fetch_messages(session_id)
    if not session_found:
        raise SessionNotFoundError(f"Session {session_id} not found.")
    if not messages:
        raise SessionNoMessagesError(f"Session {session_id} has no messages.")
    # Compute the persisted boundary index BEFORE any session state is mutated
    # a raised count_messages_up_to() must propagate with history,
    # session_id, and stats all left exactly as they were.
    n_snapshot: int | None = None
    if undo_floor_id:
        n_snapshot = ctx.session.count_messages_up_to(session_id, undo_floor_id)
    # Pair orphaned tool_calls rows BEFORE the boundary computation and
    # history validation so the restored history is always well-formed.
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
        candidate = (
            system_msgs + _restored_summary_msgs(repaired, session_id) + non_system
        )
        injected = 1  # the canonical prompt row is not a fetched DB row
    else:
        candidate = repaired
        injected = 0
    # Validate through a throwaway ConversationState: same untrusted-restore
    # pipeline as replace_history(), but the live context history is untouched.
    scratch = ConversationState(system_prompt_content=ctx.conv.system_prompt_content)
    await scratch.replace_history(candidate)
    history = scratch.history
    # convert the persisted boundary row ID into a rebuilt-history index
    # (rows 02/04): nothing in the compressed snapshot is undoable after load.
    if boundary_index is None:
        undo_floor = 0
    else:
        live_len = len(history)
        if boundary_index > live_len:
            # validation dropped snapshot rows: clamp to the built history so the
            # floor can never point past its end. Conservative — /undo loses at
            # most a few extra turns, and no row below the boundary is ever exposed.
            logger.warning(
                "Session %s undo_floor clamped %d -> %d (%d row(s) dropped by validation)",
                session_id,
                boundary_index,
                live_len,
                boundary_index - live_len,
            )
            boundary_index = live_len
        undo_floor = boundary_index
    fetched = len(messages)
    synthesized = len(repaired) - fetched
    # dropped covers both rebuild filters (stray system and extra summary rows)
    # and rows removed by validation.
    dropped = (len(repaired) - (len(candidate) - injected)) + (
        len(candidate) - len(history)
    )
    restored = len(history)
    logger.info(
        "Session %s restore built: %d fetched, %d synthesized, %d dropped, %d restored",
        session_id,
        fetched,
        synthesized,
        dropped,
        restored,
    )
    result = SessionRestoreResult(
        session_id=session_id,
        n_messages=fetched,
        fetched=fetched,
        synthesized=synthesized,
        dropped=dropped,
        restored=restored,
    )
    return RestoredSessionState(history=history, undo_floor=undo_floor, result=result)
