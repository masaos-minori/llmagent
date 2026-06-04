"""agent/tool_runner.py
Tool execution orchestration: single call dispatch, DAG/serial ordering,
result collection and history injection.

Extracted from repl_tool_exec.py. Public entry point: execute_all_tool_calls().
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any

import orjson
from rag.llm import summarize_tool_result
from shared.tool_constants import WRITE_TOOLS
from shared.tool_executor import is_side_effect, tool_call_key

from agent.tool_approval import run_approval_checks
from agent.tool_audit import audit_tool_exec
from agent.tool_result_formatter import (
    TURN_LIMIT_HINT,
    is_summarized,
    mask_args,
)

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
    """
    assert ctx.services.tools is not None
    func = tc["function"]
    name = func["name"]
    args_str = func.get("arguments", "{}")
    try:
        args = orjson.loads(args_str)
    except orjson.JSONDecodeError:
        logger.warning(f"Invalid JSON in tool arguments for {name!r}: {args_str!r}")
        args = {}

    text, is_error, x_request_id = await ctx.services.tools.execute(name, args)
    audit_tool_exec(ctx, name, args, is_error, x_request_id)

    if (
        ctx.cfg.tool.use_tool_summarize
        and not is_error
        and len(text) > ctx.cfg.tool.tool_summarize_threshold
        and ctx.services.http is not None
    ):
        llm_text = await summarize_tool_result(text, name, args, ctx.services.http)
        logger.info(
            f"Tool result {name} summarized: {len(text)} → {len(llm_text)} chars",
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
        logger.info(f"Tool call (turn {turn + 1}): {name}({masked})")
        print(f"  [tool] {name}({orjson.dumps(masked).decode()})")
        n_lines = len(text.splitlines())
        if len(text) > _TOOL_RESULT_MAX_CHARS:
            logger.info(f"Tool result {name} (full): {text}")
            display = f"{n_lines} lines / {len(text)} chars (truncated)"
            print(f"  [tool] {name} → {display}")
        else:
            print(f"  [tool] {name} → {text}")
        summarized = is_summarized(ctx.cfg, text, llm_text, is_error)
        result_id = ctx.tool_result_store.store(
            session_id=ctx.session.session_id,
            turn=turn,
            tool_name=name,
            args_json=orjson.dumps(args).decode(),
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
                f"Per-turn tool result limit reached: {turn_chars} chars"
                f" > {limit}; result replaced with hint (id={result_id})",
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
    """Run approved calls in DAG order: writes first, then the rest."""
    writes = [tc for tc in approved_calls if tc["function"]["name"] in WRITE_TOOLS]
    rest = [tc for tc in approved_calls if tc["function"]["name"] not in WRITE_TOOLS]
    results: list[Any] = []
    if writes:
        logger.info(
            "DAG: executing write group first"
            f" ({[tc['function']['name'] for tc in writes]})",
        )
        results.extend(
            await asyncio.gather(
                *(execute_one_tool_call(ctx, tc, turn) for tc in writes)
            ),
        )
    if rest:
        results.extend(
            await asyncio.gather(
                *(execute_one_tool_call(ctx, tc, turn) for tc in rest)
            ),
        )
    return results


async def _execute_standard(
    ctx: AgentContext,
    approved_calls: list[dict],
    turn: int,
) -> list[Any]:
    """Run approved calls in parallel, or serially when side effects are detected."""
    has_side_effect = any(
        is_side_effect(tc["function"]["name"]) for tc in approved_calls
    )
    use_serial = ctx.cfg.tool.serial_tool_calls or has_side_effect
    if use_serial:
        if has_side_effect and not ctx.cfg.tool.serial_tool_calls:
            logger.info(
                "Side-effect tool detected; downgrading to serial execution"
                f" ({[tc['function']['name'] for tc in approved_calls]})",
            )
        results: list[Any] = []
        for tc in approved_calls:
            results.append(await execute_one_tool_call(ctx, tc, turn))
        return results
    return list(
        await asyncio.gather(
            *(execute_one_tool_call(ctx, tc, turn) for tc in approved_calls),
        ),
    )


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
    for denied_id in denied_ids:
        ctx.conv.history.append(
            {
                "role": "tool",
                "tool_call_id": denied_id,
                "content": "Tool execution denied by user.",
            },
        )
        tool_msgs.append(("tool", "Tool execution denied by user.", None, denied_id))
    ctx.session.save_many(tool_msgs)
