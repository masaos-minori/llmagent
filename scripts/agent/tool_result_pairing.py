"""scripts/agent/tool_result_pairing.py — pure pairing of a round's declared tool_call ids with results.

Pure logic that pairs a tool round's declared tool_call ids with results.

A round answers every id its assistant message declared. An id that has no
result when the round ends (the round raised, or a guard stopped it) gets one
synthesized tool row stating that the call was not executed. No I/O.
"""

from __future__ import annotations

from collections.abc import Collection, Iterable, Mapping
from typing import Any

from shared.types import LLMMessage

from agent.tool_enums import ToolCallStopReason

_STOP_TEXT: dict[ToolCallStopReason, str] = {
    ToolCallStopReason.GUARD_STOP: (
        "Tool call not executed: the round was stopped by a loop guard."
    ),
    ToolCallStopReason.ROUND_NOT_COMPLETED: (
        "Tool call not executed: the tool round did not complete."
    ),
}


def pair_round_results(
    declared: Iterable[str],
    answered: Collection[str],
    collected: Mapping[str, Any],
    stop_reason: ToolCallStopReason,
) -> tuple[list[LLMMessage], list[tuple[str, str, None, str]]]:
    """Return (history entries, tool rows) for declared ids that have no result.

    An id is answered when it is in *answered* (preparation failures, denials) or
    a key of *collected* (executed calls). The output keeps declared order and
    holds one entry per missing id, matching the shape of denied-call messages.
    """
    text = _STOP_TEXT[stop_reason]
    history: list[LLMMessage] = []
    rows: list[tuple[str, str, None, str]] = []
    seen: set[str] = set()
    for call_id in declared:
        if call_id in answered or call_id in collected or call_id in seen:
            continue
        seen.add(call_id)
        history.append(LLMMessage(role="tool", tool_call_id=call_id, content=text))
        rows.append(("tool", text, None, call_id))
    return history, rows


def build_denied_messages(
    denied_ids: Iterable[str],
) -> tuple[list[LLMMessage], list[tuple[str, str, None, str]]]:
    """Build history entries and tool_msgs for denied tool calls."""
    denied_text = "Tool execution denied by user."
    history_entries: list[LLMMessage] = []
    messages: list[tuple[str, str, None, str]] = []
    for denied_id in denied_ids:
        history_entries.append(
            LLMMessage(role="tool", tool_call_id=denied_id, content=denied_text)
        )
        messages.append(("tool", denied_text, None, denied_id))
    return history_entries, messages
