"""scripts/agent/tool_round_completion.py — completion step of one tool round: every declared tool_call id is answered.

RoundState is the round's own record of what exists; complete_round() writes
the real results, the denials, and one synthesized row per declared id that
still has no answer, through the existing history and single save_many() path.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from agent.tool_enums import ToolCallStopReason
from agent.tool_result_pairing import build_denied_messages, pair_round_results

if TYPE_CHECKING:
    from agent.context import AgentContext


@dataclass
class RoundState:
    """What one round has produced so far, keyed by tool_call_id where it matters."""

    declared_ids: list[str]
    collected: dict[str, tuple] = field(default_factory=dict)
    prep_failures: list[Any] = field(default_factory=list)
    denied_ids: list[str] = field(default_factory=list)


def _merge_in_declared_order(
    tool_calls: list[dict],
    results: list[tuple],
) -> list[tuple]:
    """Merge collected results and preparation failures into declared batch order.

    Each entry of `tool_calls` consumes, in order, the earliest not-yet-consumed
    result whose `tool_call_id` equals the entry's id; an absent or empty id is
    treated as `""`. Results consumed by no entry are appended last, in their
    original relative order. Ids are never indexed strictly.
    """
    remaining = list(results)
    merged: list[tuple] = []
    for tc in tool_calls:
        tc_id = tc.get("id") or ""
        for i, r in enumerate(remaining):
            if r[0] == tc_id:
                merged.append(r)
                del remaining[i]
                break
    merged.extend(remaining)
    return merged


async def complete_round(
    ctx: AgentContext,
    state: RoundState,
    tool_calls: list[dict],
    turn: int,
    out_failed_keys: set[str] | None,
    reason: ToolCallStopReason,
    collect: Callable[
        ..., Awaitable[list[tuple[str, str | None, list | None, str | None]]]
    ],
) -> None:
    """Persist every row the round owes and answer each unanswered declared id.

    Synthesized rows bypass stats, out_failed_keys and the empty-result guard:
    only real results go through *collect*. Rows keep the original batch order.
    """
    results = _merge_in_declared_order(
        tool_calls, [*state.collected.values(), *state.prep_failures]
    )
    tool_msgs = await collect(ctx, results, turn, out_failed_keys)
    denied_history, denied_msgs = build_denied_messages(state.denied_ids)
    answered = {*(r[0] for r in state.prep_failures), *state.denied_ids}
    pair_history, pair_msgs = pair_round_results(
        state.declared_ids, answered, state.collected, reason
    )
    await ctx.conv.extend_messages([*denied_history, *pair_history])
    tool_msgs.extend([*denied_msgs, *pair_msgs])
    # Persist the round's tool-result rows through the turn's atomic boundary
    # (SEQ-08) in one begin_immediate transaction instead of a standalone
    # save_many commit; a mid-round failure is then compensated atomically with
    # every other turn write (AC-001, AC-005).
    boundary = ctx.turn.persistence_boundary
    assert boundary is not None, "persistence boundary not set for this turn"  # noqa: B101 — boundary required inside a turn; None means writes bypass the atomic boundary
    await boundary.save_phase_grouped(tool_msgs)
