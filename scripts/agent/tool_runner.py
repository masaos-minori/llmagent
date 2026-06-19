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
from rag.llm import summarize_tool_result
from shared.json_utils import dumps as _json_dumps
from shared.tool_constants import DELETE_TOOLS, WRITE_TOOLS
from shared.tool_executor import is_side_effect, tool_call_key
from shared.tool_spec import ToolSpec

from agent.tool_approval import run_approval_checks
from agent.tool_audit import audit_tool_exec, write_round_exec
from agent.tool_exceptions import ToolArgumentsDecodeError, ToolExecutorUnavailableError
from agent.tool_output import emit_tool_call, emit_tool_result
from agent.tool_result_formatter import (
    TURN_LIMIT_HINT,
    is_summarized,
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


if TYPE_CHECKING:
    from agent.context import AgentContext

logger = logging.getLogger(__name__)

# Display threshold: results longer than this are shown as line/char counts
_TOOL_RESULT_MAX_CHARS = 500


async def execute_one_tool_call(
    ctx: AgentContext,
    tc: dict,
    turn: int,
) -> tuple[str, str, dict, str, bool, str]:
    """Parse, execute, and optionally summarize one tool_call dict.

    Returns (tc_id, name, args, full_text, is_error, llm_text).
    Raises ToolExecutorUnavailableError when ctx.services.tools is None.
    Raises ToolArgumentsDecodeError when arguments JSON is malformed.
    """
    if ctx.services.tools is None:
        raise ToolExecutorUnavailableError(
            "Tool executor is not available (ctx.services.tools is None)"
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

    result = await ctx.services.tools.execute(name, args)
    text, is_error, x_request_id = result.output, result.is_error, result.request_id
    audit_tool_exec(ctx, name, args, is_error, x_request_id, result.error_type)

    if (
        ctx.cfg.tool.use_tool_summarize
        and not is_error
        and len(text) > ctx.cfg.tool.tool_summarize_threshold
        and ctx.services.http is not None
    ):
        llm_text = await summarize_tool_result(text, name, args, ctx.services.http)
        logger.info(
            "Tool result %s summarized: %s → %s chars",
            name,
            len(text),
            len(llm_text),
        )
    else:
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
) -> list[tuple[str, str, list[dict] | None, str | None]]:
    """Log, display, persist, and append tool results to history.

    Returns tool_msgs for session.save_many(). Applies per-turn char limit.
    Raises sqlite3.Error when tool result persistence fails.
    """
    tool_msgs: list[tuple[str, str, list[dict] | None, str | None]] = []
    turn_chars = 0
    for tc_id, name, args, text, is_error, llm_text in results:
        ctx.stats.stat_tool_calls += 1
        if is_error:
            ctx.stats.stat_tool_errors += 1
            if out_failed_keys is not None:
                out_failed_keys.add(tool_call_key(name, args))
        masked = mask_args(args, ctx.cfg.tool.masked_fields)
        logger.info("Tool call (turn %s): %s(%s)", turn + 1, name, masked)
        emit_tool_call(name, _json_dumps(masked))
        if len(text) > _TOOL_RESULT_MAX_CHARS:
            n_lines = len(text.splitlines())
            logger.info("Tool result %s (full): %s", name, text)
            display = f"{n_lines} lines / {len(text)} chars (truncated)"
            emit_tool_result(name, display)
        else:
            emit_tool_result(name, text)
        summarized = is_summarized(ctx.cfg, text, llm_text, is_error)
        result_id = ctx.tool_result_store.store(
            session_id=ctx.session.session_id,
            turn=turn,
            tool_name=name,
            args_masked=_json_dumps(masked),
            full_text=text,
            summary=llm_text if summarized else None,
            is_error=is_error,
        )
        limit = ctx.cfg.tool.tool_results_turn_max_chars
        turn_chars += len(llm_text)
        if limit > 0 and turn_chars > limit:
            id_hint = f" (id={result_id})" if result_id is not None else ""
            llm_text = TURN_LIMIT_HINT.replace("]", f"{id_hint}]")
            logger.info(
                "Per-turn tool result limit reached: %s chars > %s;"
                " result replaced with hint (id=%s)",
                turn_chars,
                limit,
                result_id,
            )
        ctx.conv.history.append(
            {"role": "tool", "tool_call_id": tc_id, "content": llm_text}
        )
        tool_msgs.append(("tool", llm_text, None, tc_id))
    return tool_msgs


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
    tool_meta: dict[str, ToolSpec] = {}
    for td in tool_definitions:
        fn = td.get("function", {})
        name = fn.get("name", "")
        if name:
            tool_meta[name] = ToolSpec(
                call_id="",
                name=name,
                resource_scope=fn.get("resource_scope", ""),
                requires_serial=fn.get("requires_serial", False),
                is_write=name in WRITE_TOOLS or name in DELETE_TOOLS,
            )

    groups, metadata = build_execution_groups(approved_calls, tool_meta)
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
    results: list[Any] = []
    for group in groups:
        group_results = await asyncio.gather(
            *(execute_one_tool_call(ctx, tc, turn) for tc in group)
        )
        results.extend(group_results)
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
    if use_serial:
        if has_side_effect and not ctx.cfg.tool.serial_tool_calls:
            logger.info(
                "Side-effect tool detected; downgrading to serial execution (%s)",
                [tc["function"]["name"] for tc in approved_calls],
            )
        if use_serial and has_side_effect:
            ctx.services.serialization_events += 1
            ctx.services.serialization_tools_affected += len(approved_calls)
        results: list[Any] = []
        for tc in approved_calls:
            results.append(await execute_one_tool_call(ctx, tc, turn))
    else:
        results = list(
            await asyncio.gather(
                *(execute_one_tool_call(ctx, tc, turn) for tc in approved_calls),
            ),
        )
    elapsed_ms = (time.perf_counter() - t0) * 1000
    write_round_exec(
        ctx,
        round_id=round_id,
        tool_count=len(approved_calls),
        mode=mode,
        has_side_effect=has_side_effect,
        trigger_tool=trigger_tool,
        elapsed_ms=elapsed_ms,
    )
    return results


async def execute_all_tool_calls(
    ctx: AgentContext,
    tool_calls: list[dict],
    turn: int,
    out_failed_keys: set[str] | None = None,
) -> None:
    """Execute all tool calls then append results in original order.

    Parallel by default; downgrades to serial on side-effect detection.
    DAG mode (write-before-read) activated by ctx.cfg.tool.use_tool_dag.
    """
    approved_calls, denied_ids = await run_approval_checks(ctx, tool_calls)

    if ctx.cfg.tool.use_tool_dag and not ctx.cfg.tool.serial_tool_calls:
        results = await _execute_with_dag(ctx, approved_calls, turn)
    else:
        results = await _execute_standard(ctx, approved_calls, turn)

    tool_msgs = _collect_tool_result_msgs(ctx, results, turn, out_failed_keys)
    denied_history, denied_msgs = _build_denied_messages(denied_ids)
    ctx.conv.history.extend(denied_history)  # type: ignore[arg-type]
    tool_msgs.extend(denied_msgs)
    ctx.session.save_many(tool_msgs)


def _build_denied_messages(
    denied_ids: list[str],
) -> tuple[list[dict], list[tuple[str, str, None, str]]]:
    """Build history entries and tool_msgs for denied tool calls."""
    denied_text = "Tool execution denied by user."
    history_entries: list[dict] = []
    messages: list[tuple[str, str, None, str]] = []
    for denied_id in denied_ids:
        history_entries.append(
            {
                "role": "tool",
                "tool_call_id": denied_id,
                "content": denied_text,
            },
        )
        messages.append(("tool", denied_text, None, denied_id))
    return history_entries, messages


# Expose sqlite3 in module scope so callers can catch the right exception type.
_sqlite3_error = sqlite3.Error
