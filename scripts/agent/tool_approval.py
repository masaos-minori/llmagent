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
from shared.tool_constants import GITHUB_DANGEROUS_TOOLS, GITHUB_WRITE_TOOLS

from agent.tool_audit import audit_approval
from agent.tool_enums import ApprovalDecisionType, RiskLevel
from agent.tool_exceptions import (
    ApprovalPreviewBlockingError,
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


_GITHUB_MUTATION_TOOLS: frozenset[str] = GITHUB_WRITE_TOOLS | GITHUB_DANGEROUS_TOOLS

# gitops_push_blocked guards repository-content and PR mutations.
# Issue-tracker mutations are intentionally excluded — see
# docs/05_agent_06_01_tool-execution-and-approval-execution.md.
_GITOPS_BLOCKABLE_TOOLS: frozenset[str] = _GITHUB_MUTATION_TOOLS - {
    "github_create_issue",
    "github_add_issue_comment",
}

# Tools that support the dry_run parameter for preview enrichment.
# Only these tools can safely receive dry_run=True during approval preview.
_KNOWN_DRY_RUN_CAPABLE_TOOLS: frozenset[str] = frozenset(
    [
        "write_file",
        "edit_file",
        "create_directory",
        "delete_file",
        "delete_directory",
        "move_file",
    ]
)


def _is_dry_run_capable(tool_name: str) -> bool:
    """Check whether a tool supports the dry_run parameter."""
    return tool_name in _KNOWN_DRY_RUN_CAPABLE_TOOLS


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
        or ctx.services_required.tools is None
    ):
        preview_str: str = preview
        return preview_str
    if not _is_dry_run_capable(tool_name):
        logger.warning(
            "Tool %s does not support dry_run; using static preview", tool_name
        )
        return preview
    try:
        result = await ctx.services_required.tools.execute(
            tool_name,
            {**args, "dry_run": True},
        )
        dry_text = result.output
        is_error = result.is_error
        _x_req = result.request_id
        if is_error:
            raise ApprovalPreviewBlockingError(
                f"Dry-run for {tool_name!r} returned an error: {dry_text[:200]}"
            )
        preview += f"\n    dry-run: {dry_text[:300]}"
    except ApprovalPreviewError:
        raise
    except (RuntimeError, OSError) as e:
        raise ApprovalPreviewError(
            f"Dry-run execution failed for {tool_name!r}: {e}"
        ) from e
    final_preview: str = preview
    return final_preview


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
    if ctx.cfg.approval.gitops_push_blocked and tool_name in _GITOPS_BLOCKABLE_TOOLS:
        audit_approval(
            ctx, tool_name, RiskLevel.HIGH, args, "denied_gitops_push_blocked"
        )
        emit_denied(
            f"{tool_name}: gitops_push_blocked is set; write operations are disabled"
        )
        return False

    try:
        check_preflight(ctx.cfg, tool_name, args)
    except PolicyViolationError as preflight_exc:
        audit_approval(
            ctx, tool_name, RiskLevel.HIGH, args, preflight_exc.audit_decision
        )
        emit_denied(str(preflight_exc))
        return False

    risk = classify_risk(ctx.cfg, tool_name, args)

    if risk == RiskLevel.NONE:
        audit_approval(ctx, tool_name, risk, args, ApprovalDecisionType.AUTO)
        return True

    try:
        preview = await _build_preview_with_dry_run(ctx, tool_name, args)
    except ApprovalPreviewBlockingError as e:
        if risk == RiskLevel.HIGH:
            audit_approval(ctx, tool_name, risk, args, "denied_dry_run_error")
            emit_denied(f"{tool_name}: dry-run reported an error: {e}")
            return False
        logger.warning("Dry-run preview unavailable for %r: %s", tool_name, e)
        preview = build_preview(tool_name, args)
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
    skip_in_workflow_mode: bool = False,  # When True, skip per-tool approval (workflow-level approval is active)
) -> tuple[list[dict], list[str]]:
    """Run plan-mode block and interactive approval for each tool call.

    Returns (approved_calls, denied_ids). Runs serially — approval is interactive.
    Invalid JSON arguments are treated as empty dicts; approval continues normally.
    """
    if skip_in_workflow_mode:
        logger.debug("run_approval_checks: skipping — workflow approval mode active")
        return tool_calls, []

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
            denied_ids.append(tc["id"])
            continue
        approved_calls.append(tc)
    return approved_calls, denied_ids
