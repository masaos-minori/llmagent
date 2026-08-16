"""scripts/agent/tool_runner.py

Tool execution orchestration: single call dispatch, DAG/serial ordering,
result collection and history injection.

Public entry point: execute_all_tool_calls().
"""

from __future__ import annotations

import asyncio
import logging
import sqlite3
import time
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from shared.json_utils import (
    dumps as _json_dumps,
)
from shared.json_utils import (
    now_iso_raw,
)
from shared.tool_executor_helpers import tool_hash_key
from shared.tool_spec import ToolSpec
from shared.types import LLMMessage

from agent.tool_audit import audit_tool_exec, write_round_exec
from agent.tool_exceptions import ToolExecutorUnavailableError
from agent.tool_output import emit_tool_call, emit_tool_result
from agent.tool_preparation import PreparedToolCall, prepare_tool_calls
from agent.tool_result_formatter import (
    mask_args,
    turn_limit_hint,
)
from agent.tool_scheduler import ExecutionPlan, build_execution_groups

_serialization_stats: dict[str, int] = {
    "total_events": 0,
    "total_tools_affected": 0,
    "tools_affected_last_round": 0,
}


def get_serialization_stats() -> dict[str, int]:
    """Return current serialization statistics."""
    return dict(_serialization_stats)


def _estimate_parallel_time(tool_timings: dict[str, float]) -> float:
    """Estimate parallel execution time as the sum of per-tool times (conservative lower bound)."""
    if not tool_timings:
        return 0.0
    return sum(tool_timings.values())


def _compute_serial_overhead(actual_ms: float, estimated_parallel_ms: float) -> float:
    """Compute ratio of actual serial time to estimated parallel time."""
    if estimated_parallel_ms <= 0:
        return 1.0
    return round(actual_ms / estimated_parallel_ms, 2)


if TYPE_CHECKING:
    from agent.context import AgentContext

logger = logging.getLogger(__name__)

# Display threshold: results longer than this are shown as line/char counts
_TOOL_RESULT_MAX_CHARS = 500


async def _run_group_calls(
    group: list[PreparedToolCall],
    serialize: bool,
    ctx: AgentContext,
    turn: int,
) -> list[Any]:
    """Execute one group of tool calls, sequentially when serialize=True, gathered otherwise."""
    if serialize:
        results: list[Any] = []
        for pc in group:
            results.append(await execute_one_tool_call(ctx, pc, turn))
        return results
    return list(
        await asyncio.gather(*(execute_one_tool_call(ctx, pc, turn) for pc in group))
    )


async def execute_one_tool_call(
    ctx: AgentContext,
    pc: PreparedToolCall,
    turn: int,
) -> tuple[str, str, dict, str, bool, str]:
    """Execute and truncate one already-prepared tool call.

    Returns (tc_id, name, args, full_text, is_error, llm_text).
    Raises ToolExecutorUnavailableError when ctx.services_required.tools is None.
    Argument parsing and validation already happened in the preparation phase
    (agent.tool_preparation.prepare_tool_calls) before this function is ever called.
    """
    if ctx.services_required.tools is None:
        raise ToolExecutorUnavailableError(
            "Tool executor is not available (ctx.services_required.tools is None)"
        )
    name = pc.name
    args = pc.args

    if ctx.services_required.gateway is not None:
        result = await ctx.services_required.gateway.execute(ctx, name, args)
    else:
        result = await ctx.services_required.tools.execute(name, args)
    text, is_error, x_request_id = result.output, result.is_error, result.request_id
    audit_tool_exec(
        ctx, name, args, is_error, x_request_id, result.error_type, source=result.source
    )

    if (
        result.is_error
        and result.error_type == "transport"
        and ctx.diagnostics is not None
    ):
        ctx.diagnostics.save_transport_failure(
            session_id=getattr(ctx.session, "session_id", None),
            tool_name=name,
            server_key=result.server_key or "",
            error_msg=result.output[:500],
        )

    llm_text = (
        text[: ctx.cfg.tool.tool_result_max_llm_chars] + "\n... (truncated)"
        if len(text) > ctx.cfg.tool.tool_result_max_llm_chars
        else text
    )

    return pc.call_id, name, args, text, is_error, llm_text


async def _collect_tool_result_msgs(
    ctx: AgentContext,
    results: list[tuple[str, str, dict, str, bool, str]],
    turn: int,
    out_failed_keys: set[str] | None,
) -> list[tuple[str, str | None, list[dict] | None, str | None]]:
    """Log, display, persist, and append tool results to history.

    Returns tool_msgs for session.save_many(). Applies per-turn char limit.
    Raises sqlite3.Error when tool result persistence fails.
    """
    tool_msgs: list[tuple[str, str | None, list[dict] | None, str | None]] = []
    turn_chars = 0
    for tc_id, name, args, text, is_error, llm_text in results:
        _update_stats_for_result(ctx, name, args, is_error, out_failed_keys)
        masked = mask_args(args, ctx.cfg.tool.masked_fields)
        _log_and_emit_tool_call(turn + 1, name, masked)
        _emit_tool_result(text, name)

        llm_text = _apply_turn_char_limit(
            llm_text,
            turn_chars,
            limit=ctx.cfg.tool.tool_results_turn_max_chars,
        )
        turn_chars += len(llm_text)
        await ctx.conv.append_message(
            {"role": "tool", "tool_call_id": tc_id, "content": llm_text}
        )
        tool_msgs.append(("tool", llm_text, None, tc_id))
    return tool_msgs


def _update_stats_for_result(
    ctx: AgentContext,
    name: str,
    args: dict,
    is_error: bool,
    out_failed_keys: set[str] | None,
) -> None:
    """Update stats and failed keys for a single tool result."""
    ctx.stats.stat_tool_calls += 1
    if is_error:
        ctx.stats.stat_tool_errors += 1
        if out_failed_keys is not None:
            out_failed_keys.add(tool_hash_key(name, args))


def _log_and_emit_tool_call(turn: int, name: str, masked: dict) -> None:
    """Log and emit a tool call event."""
    logger.info("Tool call (turn %s): %s(%s)", turn, name, masked)
    emit_tool_call(name, _json_dumps(masked))


def _emit_tool_result(text: str, name: str) -> None:
    """Emit tool result with truncation display if needed."""
    if len(text) > _TOOL_RESULT_MAX_CHARS:
        n_lines = len(text.splitlines())
        logger.info("Tool result %s (full): %s", name, text)
        emit_tool_result(name, f"{n_lines} lines / {len(text)} chars (truncated)")
    else:
        emit_tool_result(name, text)


def _apply_turn_char_limit(
    llm_text: str,
    turn_chars: int,
    limit: int,
) -> str:
    """Apply per-turn char limit; return hint if exceeded."""
    if limit > 0 and (turn_chars + len(llm_text)) > limit:
        omitted_chars = len(llm_text)
        omitted_lines = len(llm_text.splitlines())
        logger.info(
            "Per-turn tool result limit reached: %s chars > %s; result replaced with hint",
            turn_chars + omitted_chars,
            limit,
        )
        return turn_limit_hint(omitted_chars, omitted_lines, limit)
    return llm_text


async def _execute_with_dag(
    ctx: AgentContext,
    approved_calls: list[PreparedToolCall],
    turn: int,
    force_serial: bool = False,
) -> list[Any]:
    """Run approved calls through the single DAG execution plan.

    Delegates to build_execution_groups(), the sole scheduling engine — passing
    force_serial through as a planner input (rather than selecting between two
    execution engines) is what lets ctx.cfg.tool.serial_tool_calls still force
    fully serial execution without a second code path. Scheduling metadata
    comes entirely from each PreparedToolCall.spec (already resolved via
    RuntimeToolRegistry.tool_spec_for_call() during the preparation phase) —
    this function performs no registry lookups of its own.
    """
    call_specs: dict[str, ToolSpec] = {pc.call_id: pc.spec for pc in approved_calls}
    pc_by_id: dict[str, PreparedToolCall] = {pc.call_id: pc for pc in approved_calls}

    round_id = str(uuid4())
    t0 = time.perf_counter()
    plan: ExecutionPlan = build_execution_groups(
        [pc.original_call for pc in approved_calls],
        call_specs,
        force_serial=force_serial,
    )
    if logger.isEnabledFor(logging.DEBUG):
        for _pc in approved_calls:
            _m = _pc.spec
            if _m.requires_serial:
                _bucket = "serial_barrier"
            elif _m.resource_scopes or _m.is_write:
                _scopes = _m.resource_scopes or ("global:write",)
                _bucket = f"resource_scope:{','.join(_scopes)}"
            else:
                _bucket = "parallel"
            logger.debug("DAG_BUCKET: %s → %s", _pc.name, _bucket)
    serialization_events = plan.serialization_events
    if serialization_events:
        total_affected = sum(e.tools_count for e in serialization_events)
        _serialization_stats["total_events"] += len(serialization_events)
        _serialization_stats["total_tools_affected"] += total_affected
        _serialization_stats["tools_affected_last_round"] = total_affected
        logger.info(
            "Serialization impact: %d tools grouped serially (normally would run in parallel)",
            total_affected,
        )
    else:
        _serialization_stats["tools_affected_last_round"] = 0

    call_order = {pc.call_id: i for i, pc in enumerate(approved_calls)}
    results: list[Any] = []
    for batch in plan.batches:
        is_concurrent = len(batch.groups) > 1
        logger.debug(
            "ROUND_EXEC: running %d group(s) %s",
            len(batch.groups),
            "concurrently" if is_concurrent else "sequentially",
        )
        pc_groups = [
            [pc_by_id[spec.call_id] for spec in group.calls] for group in batch.groups
        ]
        batch_results = await asyncio.gather(
            *(
                _run_group_calls(pcs, group.sequential, ctx, turn)
                for pcs, group in zip(pc_groups, batch.groups)
            )
        )
        results.extend(r for group_res in batch_results for r in group_res)
    results.sort(key=lambda r: call_order.get(r[0], 0))
    elapsed_ms = (time.perf_counter() - t0) * 1000
    ts = now_iso_raw()
    for se in serialization_events:
        round_event: dict[str, Any] = {
            "trigger_tool": se.trigger_tool,
            "affected_tools": [],
            "affected_count": se.tools_count,
            "mode": "serial",
            "serial_reason": se.reason,
            "resource_scopes": list(se.resource_scopes),
            "is_write": se.is_write,
            "requires_serial": se.requires_serial,
            "scheduling_decision": se.scheduling_decision,
            "elapsed_ms": round(elapsed_ms, 1),
            "timestamp": ts,
        }
        ctx.stats.stat_serialization_events.append(round_event)
        ctx.stats.stat_serialization_total_overhead_ms += elapsed_ms
        if ctx.diagnostics is not None:
            ctx.diagnostics.save_serialization_event(
                session_id=ctx.session.session_id,
                round_id=round_id,
                trigger_tool=se.trigger_tool,
                affected_count=se.tools_count,
                mode="serial",
                elapsed_ms=elapsed_ms,
                reason=se.reason,
            )
    is_concurrent_round = any(len(batch.groups) > 1 for batch in plan.batches)
    scheduling_mode = "dag_concurrent" if is_concurrent_round else "dag_sequential"
    write_round_exec(
        ctx,
        round_id=round_id,
        tool_count=len(approved_calls),
        mode="parallel",
        has_side_effect=bool(serialization_events),
        trigger_tool=serialization_events[0].trigger_tool
        if serialization_events
        else None,
        elapsed_ms=elapsed_ms,
        affected_tools=[pc.name for pc in approved_calls],
        serial_reason=serialization_events[0].reason if serialization_events else None,
        scheduling_mode=scheduling_mode,
    )
    return results


async def execute_all_tool_calls(
    ctx: AgentContext,
    tool_calls: list[dict],
    turn: int,
    out_failed_keys: set[str] | None = None,
) -> None:
    """Execute all tool calls then append results in original order.

    Always DAG-scheduled via _execute_with_dag() — the single execution path.
    ctx.cfg.tool.serial_tool_calls feeds force_serial into the planner (one
    sequential phase per call) rather than selecting a separate execution
    engine. Every raw tool call is prepared (parsed, resolved against
    RuntimeToolRegistry, and argument-validated) before approval — a call
    that fails preparation never reaches the approval gate, DAG planning, or
    execution. Approval checks are enforced before execution — denied tool
    calls are returned as tool messages with a denial reason.
    """
    if not tool_calls:
        ctx.session.save_many([])
        return

    # Fail-closed preparation phase: parse/resolve/validate before approval.
    prepared, prep_failures = prepare_tool_calls(ctx, tool_calls)

    # Enforce approval checks before any execution
    approved_calls, denied_ids = await _run_approval_gate(ctx, prepared)

    if approved_calls:
        results = await _execute_with_dag(
            ctx, approved_calls, turn, force_serial=ctx.cfg.tool.serial_tool_calls
        )
    else:
        results = []

    # Merge preparation failures back into original batch order alongside
    # successful execution results (denied calls are handled separately below).
    call_order = {tc["id"]: i for i, tc in enumerate(tool_calls)}
    results = list(results) + list(prep_failures)
    results.sort(key=lambda r: call_order.get(r[0], 0))

    tool_msgs = await _collect_tool_result_msgs(ctx, results, turn, out_failed_keys)
    denied_history, denied_msgs = _build_denied_messages(denied_ids)
    await ctx.conv.extend_messages(denied_history)
    tool_msgs.extend(denied_msgs)
    ctx.session.save_many(tool_msgs)


async def _run_approval_gate(
    ctx: AgentContext,
    prepared: list[PreparedToolCall],
) -> tuple[list[PreparedToolCall], list[str]]:
    """Run approval checks and return (approved_calls, denied_ids).

    This is the sole per-tool-call approval gate for the batch: every prepared
    tool call in `prepared` is checked here, exactly once, before any of it
    reaches execution. Calls that pass (`approved_calls`) proceed straight
    to execution — including through `RepositoryGateway` for write/delete/
    API-write tools — without any further approval check performed anywhere
    downstream.
    """
    from agent.tool_approval import run_approval_checks

    return await run_approval_checks(ctx, prepared)


def _build_denied_messages(
    denied_ids: list[str],
) -> tuple[list[LLMMessage], list[tuple[str, str, None, str]]]:
    """Build history entries and tool_msgs for denied tool calls."""
    denied_text = "Tool execution denied by user."
    history_entries: list[LLMMessage] = []
    messages: list[tuple[str, str, None, str]] = []
    for denied_id in denied_ids:
        history_entries.append(
            LLMMessage(
                role="tool",
                tool_call_id=denied_id,
                content=denied_text,
            ),
        )
        messages.append(("tool", denied_text, None, denied_id))
    return history_entries, messages


# Expose sqlite3 in module scope so callers can catch the right exception type.
_sqlite3_error = sqlite3.Error
