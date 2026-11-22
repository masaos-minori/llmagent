"""scripts/agent/tool_approval.py

Interactive tool approval flow: risk-based prompts and plan-mode blocking.

Depends on tool_policy / tool_audit / tool_result_formatter but has no
dependency on tool_runner.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Any

from shared.json_utils import dumps as _json_dumps
from shared.tool_constants import GITHUB_DANGEROUS_TOOLS, GITHUB_WRITE_TOOLS

from agent.repl_input_controller import (
    InputBusyError,
    InputOutcome,
    InputRequest,
    PromptKind,
    get_input_controller,
)
from agent.secrets_masker import _mask_secrets
from agent.shared.models import ApprovalGrant
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
# No-op contract: a producer's server must perform zero write/delete/network/
# database side effects under dry_run=True — the pre-preview runs the tool
# before the user approves. The capability is now the declared
# ``preview_capability`` field (agentcfg003 REQ-009); the local tool-name set
# and the approval_dry_run_tools config map no longer exist.
def _declared_dry_run_capable(ctx: AgentContext, tool_name: str) -> bool:
    """Return True when the registered tool declares ``preview_capability="dry_run"``.

    No-op contract: a producer declares the capability only when its server
    performs zero write/delete/network/database side effects under dry_run=True —
    the pre-preview runs the tool before the user approves. A tool with no
    declaration, including an unregistered tool, fails closed and gets the
    static preview (agentcfg003 REQ-004, REQ-009).
    """
    registry = ctx.services_required.runtime_tools
    if registry is None:
        return False
    try:
        tool = registry.get(tool_name)
    except KeyError:
        return False
    return tool.preview_capability == "dry_run"


_DRY_RUN_TEXT_LIMIT = 300
_DRY_RUN_ERROR_LIMIT = 200


@dataclass(frozen=True)
class PreviewResult:
    """An approval preview with its provenance.

    ``required`` is True for HIGH risk: a failed required preview denies. The
    ``fallback_reason`` is set only when the static preview replaced a failed dry run.
    """

    text: str
    source: str
    required: bool
    fallback_reason: str = ""


def _static_preview(ctx: AgentContext, tool_name: str, args: dict[str, Any]) -> str:
    """Build the static preview from masked arguments (redaction before truncation)."""
    return build_preview(tool_name, mask_args(args, ctx.cfg.tool.masked_fields))


async def _build_preview_with_dry_run(
    ctx: AgentContext,
    tool_name: str,
    args: dict[str, Any],
    required: bool = False,
) -> PreviewResult:
    """Return the preview, optionally enriched with masked dry-run output.

    Raises ApprovalPreviewError when dry-run execution fails, unless the tool
    declares no dry_run capability or tools is unavailable. Dry-run output and error
    text pass the shared masker before they are truncated; exception text never
    reaches the message, only its masked form reaches the log.
    """
    preview = _static_preview(ctx, tool_name, args)
    if ctx.services_required.tools is None:
        return PreviewResult(preview, "static", required)
    if not _declared_dry_run_capable(ctx, tool_name):
        logger.warning(
            "Tool %s does not declare dry_run preview capability; using static preview",
            tool_name,
        )
        return PreviewResult(preview, "static", required)
    try:
        result = await ctx.services_required.tools.execute(
            tool_name,
            {**args, "dry_run": True},
        )
    except (RuntimeError, OSError) as e:
        logger.warning(
            "Dry-run execution failed for %r: %s", tool_name, _mask_secrets(str(e))
        )
        raise ApprovalPreviewError(
            f"Dry-run execution failed for {tool_name!r}"
        ) from None
    if result.is_error:
        logger.warning(
            "Dry-run for %r returned an error: %s",
            tool_name,
            _mask_secrets(str(result.output))[:_DRY_RUN_ERROR_LIMIT],
        )
        raise ApprovalPreviewBlockingError(
            f"Dry-run for {tool_name!r} returned an error"
        )
    dry_text = _mask_secrets(str(result.output))[:_DRY_RUN_TEXT_LIMIT]
    return PreviewResult(f"{preview}\n    dry-run: {dry_text}", "dry_run", required)


async def _approval_read(request: InputRequest) -> str:
    """Read one approval answer through the input controller, bound to ``request``.

    Returns the answer text only for a completed request; a timed-out, cancelled,
    EOF, or shutdown outcome, or a refusal because stdin is busy, returns "" (deny).
    """
    try:
        result = await get_input_controller().submit(request)
    except InputBusyError:
        logger.warning("Approval refused: an earlier stdin read is unresolved")
        return ""
    return result.text if result.outcome is InputOutcome.COMPLETED else ""


async def _prompt_user_approval(
    risk: RiskLevel, request: InputRequest | None = None
) -> bool:
    """Prompt the user interactively; HIGH requires full word 'yes'."""
    bound = request if request is not None else _approval_request(risk, "")
    answer = (await _approval_read(bound)).strip().lower()
    return answer == ("yes" if risk == RiskLevel.HIGH else "y")


def _approval_request(risk: RiskLevel, operation_id: str) -> InputRequest:
    """Create the immutable request that carries one approval prompt."""
    prompt = "  Execute? [yes/no]: " if risk == RiskLevel.HIGH else "  Execute? [y/N]: "
    return InputRequest(
        PromptKind.TOOL_APPROVAL, prompt, operation_id=operation_id, destructive=True
    )


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

    Preview failures: HIGH risk fails closed (denied) on any dry-run failure; MEDIUM
    falls back to the static preview only while ``approval_medium_preview_fallback``
    allows it. Previews are built from masked arguments.
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

    required = risk == RiskLevel.HIGH
    try:
        preview = await _build_preview_with_dry_run(ctx, tool_name, args, required)
    except ApprovalPreviewError as e:
        blocking = isinstance(e, ApprovalPreviewBlockingError)
        reason = "dry_run_error" if blocking else "dry_run_failed"
        fallback_allowed = ctx.cfg.approval.approval_medium_preview_fallback
        if required or not fallback_allowed:
            audit_approval(
                ctx,
                tool_name,
                risk,
                args,
                "denied_dry_run_error" if blocking else "denied_preview_failed",
                idempotency_key=idempotency_key,
                fallback_reason=reason,
            )
            emit_denied(f"{tool_name}: approval preview unavailable ({reason})")
            return False
        logger.warning("Dry-run preview unavailable for %r: %s", tool_name, reason)
        preview = PreviewResult(
            _static_preview(ctx, tool_name, args), "static", False, reason
        )

    request = _approval_request(risk, idempotency_key)
    emit_approval_prompt(
        risk,
        tool_name,
        preview.text,
        request_id=request.request_id,
        preview_source=preview.source,
    )

    approved = await _prompt_user_approval(risk, request)
    decision = (
        ApprovalDecisionType.APPROVED if approved else ApprovalDecisionType.DENIED
    )
    audit_approval(
        ctx,
        tool_name,
        risk,
        args,
        decision,
        idempotency_key=idempotency_key,
        request_id=request.request_id,
        preview_source=preview.source,
        fallback_reason=preview.fallback_reason,
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
        if ctx.conv.plan_mode and is_plan_mode_blocked(
            ctx.cfg, tc_name, ctx.services_required.runtime_tools
        ):
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
