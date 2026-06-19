"""agent/tool_approval.py
Interactive tool approval flow: risk-based prompts and plan-mode blocking.

Depends on tool_policy / tool_audit / tool_result_formatter but has no
dependency on tool_runner.
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any

import orjson
from shared.json_utils import dumps as _json_dumps

from agent.tool_audit import audit_approval
from agent.tool_enums import ApprovalDecisionType, RiskLevel
from agent.tool_exceptions import (
    ApprovalPreviewError,
    PolicyViolationError,
)
from agent.tool_output import (
    emit_approval_prompt,
    emit_denied,
    emit_plan_blocked,
    emit_skipped,
)
from agent.tool_policy import check_preflight, classify_risk
from agent.tool_result_formatter import build_preview, mask_args

if TYPE_CHECKING:
    from agent.context import AgentContext

logger = logging.getLogger(__name__)


_GITHUB_WRITE_TOOLS: frozenset[str] = frozenset(
    {
        "github_push_files",
        "github_create_or_update_file",
        "github_delete_file",
        "github_merge_pull_request",
        "github_create_pull_request",
        "github_update_pull_request",
        "github_create_branch",
    }
)


async def _build_preview_with_dry_run(
    ctx: AgentContext,
    tool_name: str,
    args: dict[str, Any],
) -> str:
    """Return preview string, optionally enriched with dry-run output.

    Raises ApprovalPreviewError when dry-run execution fails, unless
    approval_dry_run_tools is not configured or tools is unavailable.
    """
    preview = build_preview(tool_name, args)
    if (
        tool_name not in ctx.cfg.approval.approval_dry_run_tools
        or ctx.services.tools is None
    ):
        return preview
    try:
        dry_text, is_error, _x_req = await ctx.services.tools.execute(
            tool_name,
            {**args, "dry_run": True},
        )
        if is_error:
            raise ApprovalPreviewError(
                f"Dry-run for {tool_name!r} returned an error: {dry_text[:200]}"
            )
        preview += f"\n  Dry-run: {dry_text[:300]}"
    except ApprovalPreviewError:
        raise
    except Exception as e:
        raise ApprovalPreviewError(
            f"Dry-run execution failed for {tool_name!r}: {e}"
        ) from e
    return preview


async def _prompt_user_approval(risk: RiskLevel) -> bool:
    """Prompt the user interactively; HIGH requires full word 'yes'."""
    if risk == RiskLevel.HIGH:
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
    Risk NONE → auto-approved.
    Risk MEDIUM/HIGH → interactive prompt (with optional dry-run preview).

    Note: dry-run preview failures downgrade to text-only preview rather
    than failing the entire approval, to avoid blocking approvals when the
    MCP server has a connection issue.
    """
    if ctx.cfg.approval.gitops_push_blocked and tool_name in _GITHUB_WRITE_TOOLS:
        msg = f"  [DENIED] {tool_name}: gitops_push_blocked is set; write operations are disabled"
        audit_approval(
            ctx, tool_name, RiskLevel.HIGH, args, "denied_gitops_push_blocked"
        )
        emit_denied(tool_name, msg)
        return False

    try:
        check_preflight(ctx.cfg, tool_name, args)
    except PolicyViolationError as preflight_exc:
        audit_approval(
            ctx, tool_name, RiskLevel.HIGH, args, preflight_exc.audit_decision
        )
        emit_denied(tool_name, str(preflight_exc))
        return False

    risk = classify_risk(ctx.cfg, tool_name, args)

    if risk == RiskLevel.NONE:
        audit_approval(ctx, tool_name, risk, args, ApprovalDecisionType.AUTO)
        return True

    try:
        preview = await _build_preview_with_dry_run(ctx, tool_name, args)
    except ApprovalPreviewError as e:
        logger.warning("Dry-run preview unavailable for %r: %s", tool_name, e)
        preview = build_preview(tool_name, args)

    emit_approval_prompt(risk, tool_name, preview)

    approved = await _prompt_user_approval(risk)
    decision = (
        ApprovalDecisionType.APPROVED if approved else ApprovalDecisionType.DENIED
    )
    audit_approval(ctx, tool_name, risk, args, decision)
    if not approved:
        emit_skipped(tool_name)
    return approved


async def run_approval_checks(
    ctx: AgentContext,
    tool_calls: list[dict],
) -> tuple[list[dict], list[str]]:
    """Run plan-mode block and interactive approval for each tool call.

    Returns (approved_calls, denied_ids). Runs serially — approval is interactive.
    Invalid JSON arguments are treated as empty dicts; approval continues normally.
    """
    approved_calls: list[dict] = []
    denied_ids: list[str] = []
    for tc in tool_calls:
        tc_name = tc["function"]["name"]
        args_str = tc["function"].get("arguments", "{}")
        try:
            args_preview: dict[str, Any] = orjson.loads(args_str)
        except orjson.JSONDecodeError:
            logger.warning(
                "run_approval_checks: invalid JSON for %r; proceeding with empty args",
                tc_name,
            )
            args_preview = {}
        masked_preview = mask_args(args_preview, ctx.cfg.tool.masked_fields)
        if ctx.conv.plan_mode and tc_name in ctx.cfg.tool.plan_blocked_tools:
            emit_plan_blocked(tc_name, _json_dumps(masked_preview))
            logger.info("Plan mode blocked tool: %s", tc_name)
            denied_ids.append(tc["id"])
            continue
        if not await check_approval(ctx, tc_name, args_preview):
            emit_denied(tc_name, _json_dumps(masked_preview))
            denied_ids.append(tc["id"])
            continue
        approved_calls.append(tc)
    return approved_calls, denied_ids
