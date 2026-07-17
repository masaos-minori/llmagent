"""agent/tool_runner.py

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

import orjson
from shared.json_utils import (
    dumps as _json_dumps,
)
from shared.json_utils import (
    now_iso_raw,
)
from shared.tool_constants import SHELL_TOOLS
from shared.tool_executor_helpers import is_side_effect, tool_hash_key
from shared.tool_spec import ToolSpec
from shared.types import LLMMessage

from agent.tool_audit import audit_tool_exec, write_round_exec
from agent.tool_exceptions import ToolArgumentsDecodeError, ToolExecutorUnavailableError
from agent.tool_output import emit_tool_call, emit_tool_result
from agent.tool_result_formatter import (
    TURN_LIMIT_HINT,
    mask_args,
)
from agent.tool_scheduler import build_execution_groups

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


def _build_tool_meta(
    tool_definitions: list[dict],
) -> dict[str, ToolSpec]:
    """Build tool metadata map from tool_definitions for DAG execution."""
    tool_meta: dict[str, ToolSpec] = {}
    for td in tool_definitions:
        fn = td.get("function", {})
        name = fn.get("name", "")
        if name:
            _is_write = is_side_effect(name)
            _requires_serial = fn.get("requires_serial", False) or name in SHELL_TOOLS
            _default_scope = name if _is_write else ""
            tool_meta[name] = ToolSpec(
                call_id="",
                name=name,
                resource_scope=fn.get("resource_scope", _default_scope),
                requires_serial=_requires_serial,
                is_write=fn.get("is_write", _is_write),
            )
    return tool_meta


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
    group: list[dict],
    serialize: bool,
    ctx: AgentContext,
    turn: int,
) -> list[Any]:
    """Execute one group of tool calls, sequentially when serialize=True, gathered otherwise."""
    if serialize:
        results: list[Any] = []
        for tc in group:
            results.append(await execute_one_tool_call(ctx, tc, turn))
        return results
    return list(
        await asyncio.gather(*(execute_one_tool_call(ctx, tc, turn) for tc in group))
    )


async def execute_one_tool_call(
    ctx: AgentContext,
    tc: dict,
    turn: int,
) -> tuple[str, str, dict, str, bool, str]:
    """Parse, execute, and truncate one tool_call dict.

    Returns (tc_id, name, args, full_text, is_error, llm_text).
    Raises ToolExecutorUnavailableError when ctx.services_required.tools is None.
    Raises ToolArgumentsDecodeError when arguments JSON is malformed.
    """
    if ctx.services_required.tools is None:
        raise ToolExecutorUnavailableError(
            "Tool executor is not available (ctx.services_required.tools is None)"
        )
    func = tc["function"]
    name = func["name"]
    args_str = func.get("arguments", "{}")
    try:
        args = orjson.loads(args_str)
    except orjson.JSONDecodeError as e:
        raise ToolArgumentsDecodeError(
            f"Invalid JSON in tool arguments for {name!r}: {args_str!r}"
        ) from e

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

    return tc["id"], name, args, text, is_error, llm_text


def _collect_tool_result_msgs(
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
        ctx.conv.history.append(
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
        logger.info(
            "Per-turn tool result limit reached: %s chars > %s; result replaced with hint",
            turn_chars + len(llm_text),
            limit,
        )
        hint: str = TURN_LIMIT_HINT
        return hint
    return llm_text


async def _execute_with_dag(
    ctx: AgentContext,
    approved_calls: list[dict],
    turn: int,
) -> list[Any]:
    """Run approved calls using resource-scoped dependency groups.

    Delegates to build_execution_groups which handles write-first ordering
    for tools without resource_scope metadata.
    """
    tool_definitions = ctx.cfg.tool.tool_definitions
    tool_meta = _build_tool_meta(tool_definitions)

    round_id = str(uuid4())
    t0 = time.perf_counter()
    _groups, metadata = build_execution_groups(approved_calls, tool_meta)
    if logger.isEnabledFor(logging.DEBUG):
        for _tc in approved_calls:
            _n = _tc["function"]["name"]
            _m = tool_meta.get(_n)
            if _m is not None and _m.requires_serial:
                _bucket = "serial_barrier"
            elif _m is not None and _m.is_write and _m.resource_scope:
                _bucket = f"resource_scope:{_m.resource_scope}"
            elif _m is not None and _m.is_write:
                _bucket = "write_first"
            else:
                _bucket = "parallel"
            logger.debug("DAG_BUCKET: %s → %s", _n, _bucket)
    serialization_events = metadata.serialization_events
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

    call_order = {tc["id"]: i for i, tc in enumerate(approved_calls)}
    results: list[Any] = []
    for batch in metadata.concurrent_groups:
        is_concurrent = len(batch.groups) > 1
        logger.debug(
            "ROUND_EXEC: running %d group(s) %s",
            len(batch.groups),
            "concurrently" if is_concurrent else "sequentially",
        )
        batch_results = await asyncio.gather(
            *(
                _run_group_calls(group, serialize, ctx, turn)
                for group, serialize in zip(batch.groups, batch.serialize_flags)
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
            "resource_scope": se.resource_scope,
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
    is_concurrent_round = any(
        len(batch.groups) > 1 for batch in metadata.concurrent_groups
    )
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
        affected_tools=[tc["function"]["name"] for tc in approved_calls],
        serial_reason=serialization_events[0].reason if serialization_events else None,
        scheduling_mode=scheduling_mode,
    )
    return results


async def _execute_standard(
    ctx: AgentContext,
    approved_calls: list[dict],
    turn: int,
) -> list[Any]:
    """Run approved calls in parallel, or serially when side effects are detected."""
    round_id = str(uuid4())
    t0 = time.perf_counter()
    has_side_effect = False
    trigger_tool: str | None = None
    for tc in approved_calls:
        if is_side_effect(tc["function"]["name"]):
            has_side_effect = True
            trigger_tool = tc["function"]["name"]
            break
    use_serial = ctx.cfg.tool.serial_tool_calls or has_side_effect
    mode = "serial" if use_serial else "parallel"
    tool_timings: dict[str, float] = {}
    if use_serial:
        if has_side_effect and not ctx.cfg.tool.serial_tool_calls:
            logger.info(
                "Side-effect tool detected; downgrading to serial execution (%s)",
                [tc["function"]["name"] for tc in approved_calls],
            )
        if use_serial and has_side_effect:
            ctx.services_required.serialization_events += 1
            ctx.services_required.serialization_tools_affected += len(approved_calls)
        results: list[Any] = []
        for tc in approved_calls:
            t_tool = time.perf_counter()
            results.append(await execute_one_tool_call(ctx, tc, turn))
            tool_timings[tc["function"]["name"]] = (time.perf_counter() - t_tool) * 1000
    else:
        results = list(
            await asyncio.gather(
                *(execute_one_tool_call(ctx, tc, turn) for tc in approved_calls),
            ),
        )
    elapsed_ms = (time.perf_counter() - t0) * 1000
    estimated_parallel_ms: float | None = None
    if use_serial and has_side_effect:
        estimated_parallel_ms = _estimate_parallel_time(tool_timings)
        serial_overhead = _compute_serial_overhead(elapsed_ms, estimated_parallel_ms)
        round_event: dict[str, Any] = {
            "trigger_tool": trigger_tool,
            "affected_tools": [tc["function"]["name"] for tc in approved_calls],
            "affected_count": len(approved_calls),
            "mode": "serial",
            "serial_reason": "side_effect",
            "elapsed_ms": round(elapsed_ms, 1),
            "estimated_parallel_ms": round(estimated_parallel_ms, 1),
            "serial_overhead": serial_overhead,
            "timestamp": now_iso_raw(),
        }
        ctx.stats.stat_serialization_events.append(round_event)
        ctx.stats.stat_serialization_total_overhead_ms += (
            elapsed_ms - estimated_parallel_ms
        )
        if ctx.diagnostics is not None and trigger_tool:
            ctx.diagnostics.save_serialization_event(
                session_id=ctx.session.session_id,
                round_id=round_id,
                trigger_tool=trigger_tool,
                affected_count=len(approved_calls),
                mode="serial",
                elapsed_ms=elapsed_ms,
                reason="side_effect",
            )
    write_round_exec(
        ctx,
        round_id=round_id,
        tool_count=len(approved_calls),
        mode=mode,
        has_side_effect=has_side_effect,
        trigger_tool=trigger_tool,
        elapsed_ms=elapsed_ms,
        affected_tools=[tc["function"]["name"] for tc in approved_calls],
        serial_reason="side_effect" if has_side_effect else None,
        estimated_parallel_ms=estimated_parallel_ms,
    )
    return results


async def execute_all_tool_calls(
    ctx: AgentContext,
    tool_calls: list[dict],
    turn: int,
    out_failed_keys: set[str] | None = None,
) -> None:
    """Execute all tool calls then append results in original order.

    DAG-scheduled (resource-scoped parallelism) by default; downgrades to
    fully serial execution when ctx.cfg.tool.serial_tool_calls is set.
    Approval checks are enforced before execution — denied tool calls are
    returned as tool messages with a denial reason.
    """
    if not tool_calls:
        ctx.session.save_many([])
        return

    # Enforce approval checks before any execution
    approved_calls, denied_ids = await _run_approval_gate(ctx, tool_calls)

    if approved_calls:
        if not ctx.cfg.tool.serial_tool_calls:
            results = await _execute_with_dag(ctx, approved_calls, turn)
        else:
            results = await _execute_standard(ctx, approved_calls, turn)
    else:
        results = []

    tool_msgs = _collect_tool_result_msgs(ctx, results, turn, out_failed_keys)
    denied_history, denied_msgs = _build_denied_messages(denied_ids)
    ctx.conv.history.extend(denied_history)
    tool_msgs.extend(denied_msgs)
    ctx.session.save_many(tool_msgs)


async def _run_approval_gate(
    ctx: AgentContext,
    tool_calls: list[dict],
) -> tuple[list[dict], list[str]]:
    """Run approval checks and return (approved_calls, denied_ids).

    When the workflow definition sets require_approval=true, workflow-level approval
    gates are inserted between execute and verify stages. In this case, per-tool
    approval is skipped during the execute stage to avoid double-prompting.
    """
    from agent.tool_approval import run_approval_checks  # noqa: PLC0415

    result: tuple[list[dict[Any, Any]], list[str]] = await run_approval_checks(
        ctx, tool_calls
    )
    return result


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
