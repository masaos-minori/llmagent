"""agent/tool_approval.py
Interactive tool approval flow: risk-based prompts and plan-mode blocking.

Extracted from repl_tool_exec.py. Depends on tool_policy / tool_audit /
tool_result_formatter but has no dependency on tool_runner.
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any, TypedDict

import orjson

from agent.tool_audit import audit_approval
from agent.tool_policy import classify_risk, preflight_deny_reason
from agent.tool_result_formatter import build_preview, mask_args

if TYPE_CHECKING:
    from agent.config import ApprovalConfig
    from agent.context import AgentContext

logger = logging.getLogger(__name__)


class ApprovalDecision(TypedDict, total=False):
    """Structured result of a single tool approval evaluation."""

    tool_name: str
    risk_level: str  # "none" | "medium" | "high"
    decision: str  # "approved" | "denied" | "dry_run" | "preview_only"
    escalation_reason: str  # why the risk was escalated (or "" if no escalation)
    preview: str  # dry_run result text (or "")


def _escalate_by_args(
    tool_name: str,
    args: dict[str, Any],
    cfg: ApprovalConfig,
) -> tuple[str, str] | None:
    """Return (escalated_risk_level, reason) if arg content warrants escalation.

    Returns None when no escalation is needed.
    Checks:
    - Recursive deletion (delete_directory with recursive=True or non-empty dir)
    - Force/overwrite flags
    - Dangerous shell command prefixes (already partially covered by approval_shell_safe_prefixes)
    """
    # Check recursive delete escalation
    if tool_name == "delete_directory" and args.get("recursive"):
        return "high", "recursive directory deletion requested"

    # Check for dangerous explicit flags
    for flag in ("force", "overwrite", "clobber"):
        if args.get(flag) is True:
            return "high", f"dangerous flag {flag}=True in args"

    # Check path escalation (extends existing approval_protected_paths logic)
    resource_keys = cfg.approval_resource_keys
    path_keys = resource_keys.get("path_keys", [])
    for key in path_keys:
        path = str(args.get(key, ""))
        if path and any(path.startswith(p) for p in cfg.approval_protected_paths):
            return "high", f"path {path!r} is in a protected directory"

    return None


async def _build_preview_with_dry_run(
    ctx: AgentContext,
    tool_name: str,
    args: dict[str, Any],
) -> str:
    """Return preview string, optionally enriched with dry-run output."""
    preview = build_preview(tool_name, args)
    if (
        tool_name not in ctx.cfg.approval.approval_dry_run_tools
        or ctx.services.tools is None
    ):
        return preview
    try:
        dry_text, _, _x_req = await ctx.services.tools.execute(
            tool_name,
            {**args, "dry_run": True},
        )
        preview += f"\n  Dry-run: {dry_text[:300]}"
    except Exception:
        pass
    return preview


async def _prompt_user_approval(risk: str) -> bool:
    """Prompt the user interactively; 'high' requires full word 'yes'."""
    if risk == "high":
        answer = (
            (await asyncio.to_thread(input, "  Execute? [yes/no]: ")).strip().lower()
        )
        return answer == "yes"
    answer = (await asyncio.to_thread(input, "  Execute? [y/N]: ")).strip().lower()
    return answer == "y"


async def check_approval(
    ctx: AgentContext,
    tool_name: str,
    args: dict[str, Any],
) -> bool:
    """Return True when the tool call may proceed.

    Pre-flight deny → False immediately.
    Risk 'none' → auto-approved.
    Risk 'medium'/'high' → interactive prompt (with optional dry-run preview).
    """
    deny = preflight_deny_reason(ctx.cfg, tool_name, args)
    if deny is not None:
        audit_decision, message = deny
        audit_approval(ctx, tool_name, "high", args, audit_decision)
        print(message)
        return False

    # Check for argument-based risk escalation
    escalated = _escalate_by_args(tool_name, args, ctx.cfg.approval)
    if escalated is not None:
        escalated_risk, reason = escalated
        # Use the escalated risk level
        risk = escalated_risk
    else:
        risk = classify_risk(ctx.cfg, tool_name, args)

    if risk == "none":
        audit_approval(ctx, tool_name, risk, args, "auto")
        return True

    preview = await _build_preview_with_dry_run(ctx, tool_name, args)
    print(f"\n[{risk} risk] {tool_name}")
    print(f"  Preview: {preview}")

    approved = await _prompt_user_approval(risk)
    decision = "approved" if approved else "denied"
    audit_approval(ctx, tool_name, risk, args, decision)
    if not approved:
        print(f"  Skipped: {tool_name}")
    return approved


async def run_approval_checks(
    ctx: AgentContext,
    tool_calls: list[dict],
) -> tuple[list[dict], list[str]]:
    """Run plan-mode block and interactive approval for each tool call.

    Returns (approved_calls, denied_ids). Runs serially — approval is interactive.
    """
    approved_calls: list[dict] = []
    denied_ids: list[str] = []
    for tc in tool_calls:
        tc_name = tc["function"]["name"]
        args_preview: dict[str, Any]
        try:
            args_preview = orjson.loads(tc["function"].get("arguments", "{}"))
        except orjson.JSONDecodeError:
            args_preview = {}
        masked_preview = mask_args(args_preview, ctx.cfg.tool.masked_fields)
        if ctx.conv.plan_mode and tc_name in ctx.cfg.tool.plan_blocked_tools:
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
