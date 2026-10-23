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
    call_order = {tc["id"]: i for i, tc in enumerate(tool_calls)}
    results = [*state.collected.values(), *state.prep_failures]
    results.sort(key=lambda r: call_order.get(r[0], 0))
    tool_msgs = await collect(ctx, results, turn, out_failed_keys)
    denied_history, denied_msgs = build_denied_messages(state.denied_ids)
    answered = {*(r[0] for r in state.prep_failures), *state.denied_ids}
    pair_history, pair_msgs = pair_round_results(
        state.declared_ids, answered, state.collected, reason
    )
    await ctx.conv.extend_messages([*denied_history, *pair_history])
    tool_msgs.extend([*denied_msgs, *pair_msgs])
    ctx.session.save_many(tool_msgs)
