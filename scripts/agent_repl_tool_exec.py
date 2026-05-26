"""
Tool call execution helpers for AgentREPL.

Standalone async functions taking AgentContext as first argument.
Extracted from agent_repl.py to allow targeted loading when modifying
tool approval or execution logic.
"""

import asyncio
import json
from typing import Any

from agent_commands import mask_args
from agent_context import AgentContext
from logger import Logger
from rag_llm import summarize_tool_result

logger = Logger(__name__, "/opt/llm/logs/agent.log")

# Tool result display threshold: results longer than this are summarised on screen
_TOOL_RESULT_MAX_CHARS = 500

# Hint appended to history when a tool result is dropped due to the per-turn limit
_TURN_LIMIT_HINT = (
    "[Result omitted: per-turn tool result limit reached."
    " Use /tool show <id> to retrieve the full output.]"
)


async def check_approval(ctx: AgentContext, tool_name: str) -> bool:
    """Prompt y/N confirmation if tool_name is in require_approval_tools.

    Returns True when the tool may proceed, False when the user denies.
    Tools not listed in require_approval_tools always return True.
    """
    if tool_name not in ctx.cfg.require_approval_tools:
        return True
    # Approval required: display the tool name and wait for input
    print(f"\n[approval required] {tool_name}")
    answer = (await asyncio.to_thread(input, "  Execute? [y/N]: ")).strip().lower()
    return answer == "y"


async def execute_one_tool_call(
    ctx: AgentContext, tc: dict, turn: int
) -> tuple[str, str, dict, str, bool, str]:
    """Parse, execute, and optionally summarise one tool_call dict.

    Performs JSON argument parsing, MCP dispatch via ToolExecutor, and
    optionally calls summarize_tool_result() when use_tool_summarize is
    enabled and the result exceeds tool_summarize_threshold chars.

    Returns (tc_id, name, args, full_text, is_error, llm_text) where:
      - full_text  : raw tool output (stored for /tool show)
      - llm_text   : text injected into LLM history (may be summarized/truncated)
    """
    assert ctx.services.tools is not None
    func = tc["function"]
    name = func["name"]
    args_str = func.get("arguments", "{}")
    try:
        args = json.loads(args_str)
    except json.JSONDecodeError:
        logger.warning(f"Invalid JSON in tool arguments for {name!r}: {args_str!r}")
        args = {}

    text, is_error = await ctx.services.tools.execute(name, args)

    # Decide LLM context text: summarize if enabled and above threshold
    if (
        ctx.cfg.use_tool_summarize
        and not is_error
        and len(text) > ctx.cfg.tool_summarize_threshold
        and ctx.services.http is not None
    ):
        llm_text = await summarize_tool_result(text, name, args, ctx.services.http)
        logger.info(
            f"Tool result {name} summarized: {len(text)} → {len(llm_text)} chars"
        )
    else:
        llm_text = (
            text[: ctx.cfg.tool_result_max_llm_chars] + "\n... (truncated)"
            if len(text) > ctx.cfg.tool_result_max_llm_chars
            else text
        )

    # Tag full_text with summarized flag via tuple; store separately in caller
    return tc["id"], name, args, text, is_error, llm_text


async def execute_all_tool_calls(
    ctx: AgentContext, tool_calls: list[dict], turn: int
) -> None:
    """Execute all tool calls then append results in original order.

    When ctx.cfg.serial_tool_calls is False (default), calls run in parallel
    via asyncio.gather(). When True, calls run sequentially to preserve
    ordering for dependent operations (e.g. write-then-read the same file).
    Logging, display, and history.append are always done sequentially.
    """
    # Pre-flight checks: plan_mode block first, then interactive approval.
    # Both must run serially regardless of serial_tool_calls setting.
    approved_calls: list[dict] = []
    denied_ids: list[str] = []
    for tc in tool_calls:
        tc_name = tc["function"]["name"]
        args_preview: Any
        try:
            args_preview = json.loads(tc["function"].get("arguments", "{}"))
        except json.JSONDecodeError:
            args_preview = tc["function"].get("arguments", "{}")
        masked_preview = mask_args(args_preview, ctx.cfg.masked_fields)
        # Block destructive tools automatically when plan_mode is active
        if ctx.plan_mode and tc_name in ctx.cfg.plan_blocked_tools:
            print(f"  [plan mode] Blocked: {tc_name}")
            print(f"  args: {json.dumps(masked_preview, ensure_ascii=False)}")
            logger.info(f"Plan mode blocked tool: {tc_name}")
            denied_ids.append(tc["id"])
            continue
        if not await check_approval(ctx, tc_name):
            print(f"  Skipped: {tc_name}")
            print(f"  args: {json.dumps(masked_preview, ensure_ascii=False)}")
            denied_ids.append(tc["id"])
            continue
        approved_calls.append(tc)

    if ctx.cfg.serial_tool_calls:
        results = []
        for tc in approved_calls:
            results.append(await execute_one_tool_call(ctx, tc, turn))
    else:
        results = list(
            await asyncio.gather(
                *(execute_one_tool_call(ctx, tc, turn) for tc in approved_calls)
            )
        )

    turn_chars = 0  # cumulative llm_text chars injected into history this turn
    for tc_id, name, args, text, is_error, llm_text in results:
        ctx.stat_tool_calls += 1
        if is_error:
            ctx.stat_tool_errors += 1
        masked = mask_args(args, ctx.cfg.masked_fields)
        logger.info(f"Tool call (turn {turn + 1}): {name}({masked})")
        print(f"  [tool] {name}({json.dumps(masked, ensure_ascii=False)})")
        n_lines = len(text.splitlines())
        if len(text) > _TOOL_RESULT_MAX_CHARS:
            logger.info(f"Tool result {name} (full): {text}")
            display = f"{n_lines} lines / {len(text)} chars (truncated)"
            print(f"  [tool] {name} → {display}")
        else:
            print(f"  [tool] {name} → {text}")
        # Determine whether this result was summarized for storage tagging
        summarized = (
            ctx.cfg.use_tool_summarize
            and not is_error
            and len(text) > ctx.cfg.tool_summarize_threshold
            and llm_text != text
            and not (
                len(text) > ctx.cfg.tool_result_max_llm_chars
                and llm_text
                == text[: ctx.cfg.tool_result_max_llm_chars] + "\n... (truncated)"
            )
        )
        # Persist full text to DB store; id enables /tool show retrieval
        result_id = ctx.tool_result_store.store(
            session_id=ctx.session.session_id,
            turn=turn,
            tool_name=name,
            args_json=json.dumps(args, ensure_ascii=False),
            full_text=text,
            summary=llm_text if summarized else None,
            is_error=is_error,
        )
        # Apply per-turn total limit after persisting so full text is always stored
        limit = ctx.cfg.tool_results_turn_max_chars
        turn_chars += len(llm_text)
        if limit > 0 and turn_chars > limit:
            id_hint = f" (id={result_id})" if result_id is not None else ""
            llm_text = _TURN_LIMIT_HINT.replace("]", f"{id_hint}]")
            logger.info(
                f"Per-turn tool result limit reached: {turn_chars} chars"
                f" > {limit}; result replaced with hint (id={result_id})"
            )
        ctx.history.append(
            {
                "role": "tool",
                "tool_call_id": tc_id,
                "content": llm_text,
            }
        )
    # Add skipped results so the LLM knows these tool calls were denied.
    for denied_id in denied_ids:
        ctx.history.append(
            {
                "role": "tool",
                "tool_call_id": denied_id,
                "content": "Tool execution denied by user.",
            }
        )
