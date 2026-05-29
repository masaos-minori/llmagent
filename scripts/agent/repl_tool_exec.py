"""
Tool call execution helpers for AgentREPL.

Standalone async functions taking AgentContext as first argument.
Extracted from agent/repl.py to allow targeted loading when modifying
tool approval or execution logic.
"""

import asyncio
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any

import orjson
from rag.llm import summarize_tool_result
from shared.logger import Logger
from shared.tool_constants import DELETE_TOOLS, WRITE_TOOLS
from shared.tool_executor import is_side_effect, tool_call_key

from agent.commands.registry import mask_args
from agent.context import AgentContext

if TYPE_CHECKING:
    from agent.config import AgentConfig

logger = Logger(__name__, "/opt/llm/logs/agent.log")

# Tool result display threshold: results longer than this are summarised on screen
_TOOL_RESULT_MAX_CHARS = 500

# Hint appended to history when a tool result is dropped due to the per-turn limit
_TURN_LIMIT_HINT = (
    "[Result omitted: per-turn tool result limit reached."
    " Use /tool show <id> to retrieve the full output.]"
)


_EXEC_TOOLS: frozenset[str] = frozenset({"shell_run"})
_API_WRITE_TOOLS: frozenset[str] = frozenset(
    {
        "github_push_files",
        "github_create_or_update_file",
        "github_delete_file",
        "github_merge_pull_request",
        "github_create_branch",
        "github_create_pull_request",
        "github_update_pull_request",
        "github_create_issue",
        "github_add_issue_comment",
    }
)

# GitHub tools that perform write operations; used by repo allowlist enforcement
_GITHUB_WRITE_TOOLS: frozenset[str] = _API_WRITE_TOOLS

# Maps tool_safety_tiers tier → default approval risk level
_TIER_TO_RISK: dict[str, str] = {
    "READ_ONLY": "none",
    "WRITE_SAFE": "none",
    "WRITE_DANGEROUS": "medium",
    "ADMIN": "high",
}


def _classify_operation_type(tool_name: str) -> str:
    """Return operation type for a tool: write | delete | execute | api_write | read."""
    if tool_name in WRITE_TOOLS:
        return "write"
    if tool_name in DELETE_TOOLS:
        return "delete"
    if tool_name in _EXEC_TOOLS:
        return "execute"
    if tool_name in _API_WRITE_TOOLS:
        return "api_write"
    return "read"


def _classify_risk(cfg: "AgentConfig", tool_name: str, args: dict) -> str:
    """Return the risk level for a tool call: 'none' | 'medium' | 'high'.

    Classification order:
      1. Look up tool_name in cfg.approval_risk_rules (priority).
      2. Tier fallback: cfg.tool_safety_tiers → _TIER_TO_RISK (absent → WRITE_DANGEROUS).
      3. delete_directory + recursive=True → escalate to 'high'.
      4. shell_run: downgrade to 'none' when command matches a safe prefix.
      5. File path escalation: any path arg in a protected dir → 'high'.
      6. GitHub branch escalation: target branch in high_risk_branches → 'high'.
    """
    base = cfg.approval_risk_rules.get(tool_name)
    if base is None:
        # Tier fallback: tools absent from approval_risk_rules use tier default.
        # Unknown tools fall back to WRITE_DANGEROUS (Fail-Safe).
        tier = cfg.tool_safety_tiers.get(tool_name, "WRITE_DANGEROUS")
        base = _TIER_TO_RISK[tier]
    if base == "none":
        return "none"
    # delete_directory + recursive=True is always high risk regardless of base level
    if tool_name == "delete_directory" and args.get("recursive"):
        return "high"
    # shell_run: safe-prefix commands bypass the high-risk default
    if tool_name == "shell_run":
        cmd = str(args.get("command", ""))
        if any(cmd.startswith(p) for p in cfg.approval_shell_safe_prefixes):
            return "none"
        return "high"
    path_keys = cfg.approval_resource_keys.get("path_keys", [])
    # Escalate to 'high' when the target path is in a protected directory
    if base != "high":
        for key in path_keys:
            val = str(args.get(key) or "")
            if val and any(val.startswith(p) for p in cfg.approval_protected_paths):
                return "high"
    # Escalate GitHub write ops to 'high' when targeting a protected branch
    if tool_name.startswith("github_") and base != "high":
        branch_keys = cfg.approval_resource_keys.get("branch_keys", [])
        for key in branch_keys:
            val = str(args.get(key) or "")
            if val and val in cfg.approval_high_risk_branches:
                return "high"
    return base


def _check_allowed_root(cfg: "AgentConfig", tool_name: str, args: dict) -> bool:
    """Return False when any path argument violates cfg.allowed_root.

    Uses Path.resolve() to prevent directory traversal via symlinks or relative paths.
    An empty cfg.allowed_root disables the check.
    """
    if not cfg.allowed_root:
        return True
    root = Path(cfg.allowed_root).resolve()
    path_keys = cfg.approval_resource_keys.get("path_keys", [])
    for key in path_keys:
        val = str(args.get(key) or "")
        if val:
            try:
                resolved = Path(val).resolve()
            except (ValueError, OSError):
                return False  # Unresolvable path → deny
            if not resolved.is_relative_to(root):
                return False
    return True


def _check_allowed_repo(cfg: "AgentConfig", tool_name: str, args: dict) -> bool:
    """Return False when the target GitHub repo is not in the allowlist (Fail-Closed).

    Non-write GitHub tools and non-GitHub tools are always allowed.
    When approval_github_allowed_repos is empty, all write ops are denied.
    """
    if tool_name not in _GITHUB_WRITE_TOOLS:
        return True
    allowed = cfg.approval_github_allowed_repos
    # Fail-Closed: empty allowlist = deny all write operations
    if not allowed:
        return False
    owner = str(args.get("owner", ""))
    repo = str(args.get("repo", ""))
    return f"{owner}/{repo}" in allowed


def _is_summarized(
    cfg: "AgentConfig", text: str, llm_text: str, is_error: bool
) -> bool:
    """Return True when llm_text represents a summarized (not truncated) form of text."""
    if not cfg.use_tool_summarize or is_error:
        return False
    if len(text) <= cfg.tool_summarize_threshold:
        return False
    if llm_text == text:
        return False
    truncated = text[: cfg.tool_result_max_llm_chars] + "\n... (truncated)"
    return llm_text != truncated


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
    masked = mask_args(args, ctx.cfg.masked_fields)
    path_keys = set(ctx.cfg.approval_resource_keys.get("path_keys", []))
    branch_keys = set(ctx.cfg.approval_resource_keys.get("branch_keys", []))
    resource_scope = {k: v for k, v in masked.items() if k in path_keys | branch_keys}
    ctx.services.audit_logger.info(
        orjson.dumps(
            {
                "event": "tool_approval",
                "task_id": ctx.current_turn_id,
                "tool": tool_name,
                "operation_type": _classify_operation_type(tool_name),
                "resource_scope": resource_scope,
                "risk": risk,
                "decision": decision,
                "args_preview": masked,
                "ts": time.time(),
            }
        ).decode()
    )


async def check_approval(ctx: AgentContext, tool_name: str, args: dict) -> bool:
    """Determine whether a tool call may proceed based on risk classification.

    Returns True when the call is approved, False when denied.
    Pre-flight checks (immediate deny without prompt):
      1. ALLOWED_ROOT: path argument outside cfg.allowed_root.
      2. GitHub repo allowlist: repo not in cfg.approval_github_allowed_repos (Fail-Closed).
    Risk levels (after pre-flight):
      'none'   — auto-approved; no prompt shown.
      'medium' — preview + y/N prompt.
      'high'   — preview + 'yes' (full word) required.
    When tool_name is in cfg.approval_dry_run_tools, a dry_run execution is
    attempted before the prompt and its output is appended to the preview.
    """
    # Pre-flight: ALLOWED_ROOT root jail — immediate deny, no prompt
    if not _check_allowed_root(ctx.cfg, tool_name, args):
        _audit_approval(ctx, tool_name, "high", args, "denied_root_jail")
        print(
            f"  [DENIED] {tool_name}: path outside allowed_root"
            f" ({ctx.cfg.allowed_root!r})"
        )
        return False
    # Pre-flight: GitHub repo allowlist (Fail-Closed) — immediate deny, no prompt
    if not _check_allowed_repo(ctx.cfg, tool_name, args):
        _audit_approval(ctx, tool_name, "high", args, "denied_repo_allowlist")
        print(f"  [DENIED] {tool_name}: repo not in approval_github_allowed_repos")
        return False
    risk = _classify_risk(ctx.cfg, tool_name, args)
    if risk == "none":
        _audit_approval(ctx, tool_name, risk, args, "auto")
        return True
    preview = _build_preview(tool_name, args)
    # Attempt dry_run for supported tools to enrich the preview
    if tool_name in ctx.cfg.approval_dry_run_tools and ctx.services.tools is not None:
        try:
            dry_text, _ = await ctx.services.tools.execute(
                tool_name, {**args, "dry_run": True}
            )
            preview += f"\n  Dry-run: {dry_text[:300]}"
        except Exception:
            pass
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


async def _run_approval_checks(
    ctx: AgentContext, tool_calls: list[dict]
) -> tuple[list[dict], list[str]]:
    """Run plan-mode block and interactive approval for each tool call.

    Returns (approved_calls, denied_ids). Must run serially — approval is interactive.
    """
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
    return approved_calls, denied_ids


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
        ctx.stat_tool_calls += 1
        if is_error:
            ctx.stat_tool_errors += 1
            # Record error key for retry suppression in agent/orchestrator.py.
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
        summarized = _is_summarized(ctx.cfg, text, llm_text, is_error)
        result_id = ctx.tool_result_store.store(
            session_id=ctx.session.session_id,
            turn=turn,
            tool_name=name,
            args_json=orjson.dumps(args).decode(),
            full_text=text,
            summary=llm_text if summarized else None,
            is_error=is_error,
        )
        limit = ctx.cfg.tool_results_turn_max_chars
        turn_chars += len(llm_text)
        if limit > 0 and turn_chars > limit:
            id_hint = f" (id={result_id})" if result_id is not None else ""
            llm_text = _TURN_LIMIT_HINT.replace("]", f"{id_hint}]")
            logger.info(
                f"Per-turn tool result limit reached: {turn_chars} chars"
                f" > {limit}; result replaced with hint (id={result_id})"
            )
        ctx.history.append({"role": "tool", "tool_call_id": tc_id, "content": llm_text})
        tool_msgs.append(("tool", llm_text, None, tc_id))
    return tool_msgs


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
    approved_calls, denied_ids = await _run_approval_checks(ctx, tool_calls)

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

    # Persist all tool result messages in one DB transaction (one connection open).
    # Collecting here avoids N individual save() calls each with their own
    # load_extension + PRAGMA overhead.
    tool_msgs = _collect_tool_result_msgs(ctx, results, turn, out_failed_keys)
    # Add skipped results so the LLM knows these tool calls were denied.
    for denied_id in denied_ids:
        ctx.history.append(
            {
                "role": "tool",
                "tool_call_id": denied_id,
                "content": "Tool execution denied by user.",
            }
        )
        tool_msgs.append(("tool", "Tool execution denied by user.", None, denied_id))
    ctx.session.save_many(tool_msgs)
