"""scripts/agent/tool_approval.py

Interactive tool approval flow: risk-based prompts and plan-mode blocking.

Depends on tool_policy / tool_audit / tool_result_formatter but has no
dependency on tool_runner.
"""

from __future__ import annotations

import logging
import time
from dataclasses import replace
from typing import TYPE_CHECKING, Any

from shared.json_utils import dumps as _json_dumps
from shared.tool_constants import GITHUB_DANGEROUS_TOOLS, GITHUB_WRITE_TOOLS

from agent.shared.models import ApprovalGrant
from agent.stdin_reader import get_stdin_reader
from agent.tool_audit import audit_approval
from agent.tool_enums import ApprovalDecisionType, OperationType, RiskLevel
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
from agent.tool_policy import (
    check_preflight,
    classify_operation_type,
    classify_risk,
    is_plan_mode_blocked,
)
from agent.tool_preparation import PreparedToolCall, _canonical_args_hash
from agent.tool_result_formatter import build_preview, mask_args

if TYPE_CHECKING:
    from agent.context import AgentContext

logger = logging.getLogger(__name__)

# Grant expiry horizon (mcpdl001 REQ-006): fixed module constant until the
# mcpdl003 config decision (Plan Assumption, UNK-01). Grants are single-use;
# the gateway (tool_repository_gateway) enforces the horizon at execution.
_GRANT_TTL_SECONDS = 300.0


_GITHUB_MUTATION_TOOLS: frozenset[str] = GITHUB_WRITE_TOOLS | GITHUB_DANGEROUS_TOOLS

# gitops_push_blocked guards repository-content and PR mutations.
# Issue-tracker mutations are intentionally excluded — see
# docs/23_agent/agent_06_02_tool-execution-and-approval-approval.md and
# docs/23_agent/agent_06_04_tool-execution-and-approval-canonical.md.
_GITOPS_BLOCKABLE_TOOLS: frozenset[str] = _GITHUB_MUTATION_TOOLS - {
    "github_create_issue",
    "github_add_issue_comment",
}

# Tools that support the dry_run parameter for preview enrichment.
# No-op contract: a member's server must perform zero write/delete/network/
# database side effects under dry_run=True. Do not add a member here unless it meets
# that guarantee — the pre-preview runs the tool before the user approves.
_KNOWN_DRY_RUN_CAPABLE_TOOLS: frozenset[str] = frozenset(
    [
        "write_file",
        "edit_file",
        "create_directory",
        "delete_file",
        "delete_directory",
        "move_file",
        "github_create_or_update_file",
        "github_push_files",
        "github_delete_file",
        "github_create_issue",
        "github_add_issue_comment",
        "github_create_pull_request",
        "github_update_pull_request",
        "github_merge_pull_request",
        "github_create_branch",
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
        return preview
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
    return preview


async def _approval_read(prompt: str) -> str:
    """Read one approval answer on the shared daemon reader thread."""
    return await get_stdin_reader().read(prompt=prompt)


async def _prompt_user_approval(risk: RiskLevel) -> bool:
    """Prompt the user interactively; HIGH requires full word 'yes'."""
    if risk == RiskLevel.HIGH:
        answer = (await _approval_read("  Execute? [yes/no]: ")).strip().lower()
        return answer == "yes"
    answer = (await _approval_read("  Execute? [y/N]: ")).strip().lower()
    return answer == "y"


async def check_approval(
    ctx: AgentContext,
    tool_name: str,
    args: dict[str, Any],
    idempotency_key: str = "",
) -> bool:
    """Return True when the tool call may proceed.

    Pre-flight deny → False immediately.
    Risk NONE → auto-approved.
    Risk MEDIUM/HIGH → interactive prompt (with optional dry-run preview).

    ``idempotency_key`` (the logical call id) is stamped onto every approval
    audit event (mcpdl001 REQ-008, AC-2).

    Note: dry-run preview failures downgrade to text-only preview rather
    than failing the entire approval, to avoid blocking approvals when the
    MCP server has a connection issue.
    """
    if ctx.cfg.approval.gitops_push_blocked and tool_name in _GITOPS_BLOCKABLE_TOOLS:
        audit_approval(
            ctx,
            tool_name,
            RiskLevel.HIGH,
            args,
            "denied_gitops_push_blocked",
            idempotency_key=idempotency_key,
        )
        emit_denied(
            f"{tool_name}: gitops_push_blocked is set; write operations are disabled"
        )
        return False

    try:
        check_preflight(ctx.cfg, tool_name, args, ctx.services_required.runtime_tools)
    except PolicyViolationError as preflight_exc:
        audit_approval(
            ctx,
            tool_name,
            RiskLevel.HIGH,
            args,
            preflight_exc.audit_decision,
            idempotency_key=idempotency_key,
        )
        emit_denied(str(preflight_exc))
        return False

    risk = classify_risk(ctx.cfg, tool_name, args, ctx.services_required.runtime_tools)

    if risk == RiskLevel.NONE:
        audit_approval(
            ctx,
            tool_name,
            risk,
            args,
            ApprovalDecisionType.AUTO,
            idempotency_key=idempotency_key,
        )
        return True

    try:
        preview = await _build_preview_with_dry_run(ctx, tool_name, args)
    except ApprovalPreviewBlockingError as e:
        if risk == RiskLevel.HIGH:
            audit_approval(
                ctx,
                tool_name,
                risk,
                args,
                "denied_dry_run_error",
                idempotency_key=idempotency_key,
            )
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
    audit_approval(
        ctx, tool_name, risk, args, decision, idempotency_key=idempotency_key
    )
    if not approved:
        emit_skipped(tool_name)
    return approved


def _issue_grant(
    pc: PreparedToolCall, decision: ApprovalDecisionType
) -> PreparedToolCall:
    """Return a copy of *pc* carrying a fresh ApprovalGrant (REQ-006, AC-4).

    `args_hash` reuses the preparation phase's canonical-JSON hash function —
    the exact value `ToolExecutionContext.args_hash` carries — so the gateway
    comparison (row 3) holds for any args payload.
    """
    now = time.time()
    grant = ApprovalGrant(
        tool=pc.name,
        args_hash=_canonical_args_hash(pc.args),
        mode=decision.value,
        issued_at=now,
        expires_at=now + _GRANT_TTL_SECONDS,
    )
    return replace(pc, grant=grant)


async def run_approval_checks(
    ctx: AgentContext,
    prepared_calls: list[PreparedToolCall],
) -> tuple[list[PreparedToolCall], list[str]]:
    """Run plan-mode block and interactive approval for each prepared tool call.

    Returns (approved_calls, denied_ids). Runs serially — approval is interactive.
    `args` is already parsed and validated by the preparation phase
    (agent.tool_preparation.prepare_tool_calls) before this function is ever called.

    Every approved non-READ call is returned grant-bound (mcpdl001 REQ-006):
    READ calls need no grant downstream and stay grant-less; denied calls
    never carry one.
    """
    approved_calls: list[PreparedToolCall] = []
    denied_ids: list[str] = []
    for pc in prepared_calls:
        tc_name = pc.name
        args_preview = pc.args
        masked_preview = mask_args(args_preview, ctx.cfg.tool.masked_fields)
        call_id = pc.context.call_id if pc.context else ""
        if ctx.conv.plan_mode and is_plan_mode_blocked(ctx.cfg, tc_name):
            emit_plan_blocked(tc_name, _json_dumps(masked_preview))
            logger.info("Plan mode blocked tool: %s", tc_name)
            denied_ids.append(pc.call_id)
            continue
        if not await check_approval(
            ctx, tc_name, args_preview, idempotency_key=call_id
        ):
            denied_ids.append(pc.call_id)
            continue
        op = classify_operation_type(tc_name, ctx.services_required.runtime_tools)
        if op == OperationType.READ:
            approved_calls.append(pc)
            continue
        risk = classify_risk(
            ctx.cfg, tc_name, args_preview, ctx.services_required.runtime_tools
        )
        decision = (
            ApprovalDecisionType.AUTO
            if risk == RiskLevel.NONE
            else ApprovalDecisionType.APPROVED
        )
        approved_calls.append(_issue_grant(pc, decision))
    return approved_calls, denied_ids
