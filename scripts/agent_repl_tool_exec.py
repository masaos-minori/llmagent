"""
Tool call execution helpers for AgentREPL.

Standalone async functions taking AgentContext as first argument.
Extracted from agent_repl.py to allow targeted loading when modifying
tool approval or execution logic.
"""

import asyncio
import time
from typing import TYPE_CHECKING, Any

import orjson
from agent_commands import mask_args
from agent_context import AgentContext
from logger import Logger
from rag_llm import summarize_tool_result
from tool_executor import is_side_effect, tool_call_key

if TYPE_CHECKING:
    from agent_config import AgentConfig

logger = Logger(__name__, "/opt/llm/logs/agent.log")

# Tool result display threshold: results longer than this are summarised on screen
_TOOL_RESULT_MAX_CHARS = 500

# Hint appended to history when a tool result is dropped due to the per-turn limit
_TURN_LIMIT_HINT = (
    "[Result omitted: per-turn tool result limit reached."
    " Use /tool show <id> to retrieve the full output.]"
)


# Arg keys that may contain a file-system path; used for path escalation.
_PREVIEW_PATH_KEYS: frozenset[str] = frozenset(
    {"path", "file_path", "directory_path", "source", "destination"}
)
# Arg keys that may contain a GitHub branch name; used for branch escalation.
_GITHUB_BRANCH_KEYS: frozenset[str] = frozenset({"branch", "base", "head"})


def _classify_risk(cfg: "AgentConfig", tool_name: str, args: dict) -> str:
    """Return the risk level for a tool call: 'none' | 'medium' | 'high'.

    Classification order:
      1. Look up tool_name in cfg.approval_risk_rules (absent → 'none').
      2. shell_run: downgrade to 'none' when command matches a safe prefix.
      3. File path escalation: any path arg in a protected dir → 'high'.
      4. GitHub branch escalation: target branch in high_risk_branches → 'high'.
    """
    base = cfg.approval_risk_rules.get(tool_name, "none")
    if base == "none":
        return "none"
    # shell_run: safe-prefix commands bypass the high-risk default
    if tool_name == "shell_run":
        cmd = str(args.get("command", ""))
        if any(cmd.startswith(p) for p in cfg.approval_shell_safe_prefixes):
            return "none"
        return "high"
    # Escalate to 'high' when the target path is in a protected directory
    if base != "high":
        for key in _PREVIEW_PATH_KEYS:
            val = str(args.get(key) or "")
            if val and any(val.startswith(p) for p in cfg.approval_protected_paths):
                return "high"
    # Escalate GitHub write ops to 'high' when targeting a protected branch
    if tool_name.startswith("github_") and base != "high":
        for key in _GITHUB_BRANCH_KEYS:
            val = str(args.get(key) or "")
            if val and val in cfg.approval_high_risk_branches:
                return "high"
    return base


def _build_preview(tool_name: str, args: dict) -> str:
    """Build a human-readable operation preview shown before approval prompts."""
    if tool_name in ("write_file", "edit_file"):
        path = args.get("path") or args.get("file_path", "?")
        content = str(args.get("content") or args.get("new_content") or "")[:200]
        return f"{path}\n    content: {content!r}"
    if tool_name in ("delete_file", "delete_directory"):
        return str(args.get("path") or args.get("directory_path", "?"))
    if tool_name == "create_directory":
        return str(args.get("path") or args.get("directory_path", "?"))
    if tool_name == "move_file":
        return f"{args.get('source', '?')} → {args.get('destination', '?')}"
    if tool_name == "shell_run":
        return str(args.get("command", "?"))
    if tool_name.startswith("github_"):
        owner = str(args.get("owner", ""))
        repo = str(args.get("repo", ""))
        repo_str = f"{owner}/{repo}" if owner and repo else owner or repo or "?"
        extra = {k: v for k, v in args.items() if k not in ("owner", "repo")}
        extra_str = orjson.dumps(extra, option=orjson.OPT_SORT_KEYS).decode()[:200]
        return f"{repo_str} {extra_str}"
    raw: str = orjson.dumps(args, option=orjson.OPT_SORT_KEYS).decode()
    return raw[:300]


def _audit_approval(
    ctx: AgentContext, tool_name: str, risk: str, args: dict, decision: str
) -> None:
    """Write a structured tool_approval event to the audit log."""
    if ctx.services.audit_logger is None:
        return
    ctx.services.audit_logger.info(
        orjson.dumps(
            {
                "event": "tool_approval",
                "task_id": ctx.current_turn_id,
                "tool": tool_name,
                "risk": risk,
                "decision": decision,
                "args_preview": mask_args(args, ctx.cfg.masked_fields),
                "ts": time.time(),
            }
        ).decode()
    )


async def check_approval(ctx: AgentContext, tool_name: str, args: dict) -> bool:
    """Determine whether a tool call may proceed based on risk classification.

    Returns True when the call is approved, False when denied.
    Risk levels:
      'none'   — auto-approved; no prompt shown.
      'medium' — preview + y/N prompt.
      'high'   — preview + 'yes' (full word) required.
    """
    risk = _classify_risk(ctx.cfg, tool_name, args)
    if risk == "none":
        _audit_approval(ctx, tool_name, risk, args, "auto")
        return True
    preview = _build_preview(tool_name, args)
    print(f"\n[{risk} risk] {tool_name}")
    print(f"  Preview: {preview}")
    if risk == "high":
        answer = (
            (await asyncio.to_thread(input, "  Execute? [yes/no]: ")).strip().lower()
        )
        approved = answer == "yes"
    else:
        answer = (await asyncio.to_thread(input, "  Execute? [y/N]: ")).strip().lower()
        approved = answer == "y"
    decision = "approved" if approved else "denied"
    _audit_approval(ctx, tool_name, risk, args, decision)
    if not approved:
        print(f"  Skipped: {tool_name}")
    return approved


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
        args = orjson.loads(args_str)
    except orjson.JSONDecodeError:
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
    ctx: AgentContext,
    tool_calls: list[dict],
    turn: int,
    out_failed_keys: set[str] | None = None,
) -> None:
    """Execute all tool calls then append results in original order.

    When ctx.cfg.serial_tool_calls is False (default), calls run in parallel
    via asyncio.gather() unless an approved call has side effects (write/delete/shell),
    in which case execution is automatically downgraded to serial.
    Logging, display, and history.append are always done sequentially.
    Error keys are added to out_failed_keys (if provided) for retry suppression.
    """
    # Pre-flight checks: plan_mode block first, then interactive approval.
    # Both must run serially regardless of serial_tool_calls setting.
    approved_calls: list[dict] = []
    denied_ids: list[str] = []
    for tc in tool_calls:
        tc_name = tc["function"]["name"]
        args_preview: Any
        try:
            args_preview = orjson.loads(tc["function"].get("arguments", "{}"))
        except orjson.JSONDecodeError:
            args_preview = tc["function"].get("arguments", "{}")
        masked_preview = mask_args(args_preview, ctx.cfg.masked_fields)
        # Block destructive tools automatically when plan_mode is active
        if ctx.plan_mode and tc_name in ctx.cfg.plan_blocked_tools:
            print(f"  [plan mode] Blocked: {tc_name}")
            print(f"  args: {orjson.dumps(masked_preview).decode()}")
            logger.info(f"Plan mode blocked tool: {tc_name}")
            denied_ids.append(tc["id"])
            continue
        if not await check_approval(ctx, tc_name, args_preview):
            print(f"  args: {orjson.dumps(masked_preview).decode()}")
            denied_ids.append(tc["id"])
            continue
        approved_calls.append(tc)

    # Auto-downgrade to serial if any approved call has side effects (write/delete/shell).
    has_side_effect = any(
        is_side_effect(tc["function"]["name"]) for tc in approved_calls
    )
    use_serial = ctx.cfg.serial_tool_calls or has_side_effect
    if use_serial:
        if has_side_effect and not ctx.cfg.serial_tool_calls:
            logger.info(
                "Side-effect tool detected; downgrading to serial execution"
                f" ({[tc['function']['name'] for tc in approved_calls]})"
            )
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
            # Record error key for retry suppression in orchestrator.py.
            # Uses tool_call_key() to guarantee the same hash as the lookup side.
            if out_failed_keys is not None:
                out_failed_keys.add(tool_call_key(name, args))
        masked = mask_args(args, ctx.cfg.masked_fields)
        logger.info(f"Tool call (turn {turn + 1}): {name}({masked})")
        print(f"  [tool] {name}({orjson.dumps(masked).decode()})")
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
            args_json=orjson.dumps(args).decode(),
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
    # Persist all tool result messages in one DB transaction (one connection open).
    # Collecting here avoids N individual save() calls each with their own
    # load_extension + PRAGMA overhead.
    tool_msgs: list[tuple[str, str, list[dict] | None, str | None]] = [
        ("tool", llm_text, None, tc_id)
        for tc_id, _name, _args, _text, _is_error, llm_text in results
    ]
    tool_msgs += [
        ("tool", "Tool execution denied by user.", None, denied_id)
        for denied_id in denied_ids
    ]
    ctx.session.save_many(tool_msgs)
