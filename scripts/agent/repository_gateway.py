"""scripts/agent/repository_gateway.py

Agent-side enforcement boundary for all repository write/delete/API-write operations.

The MCP git server independently enforces its refspec, protected-branch, and
forced-update rules regardless of Agent-side approval state (ADR-012 INV-04,
docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md); this
gateway guards the Agent-side write path only and does not take over the
server's technical safety judgments (ADR-014 INV-03).

Read-only tool calls are forwarded directly to ToolExecutor without checks.
Write/delete/API-write tool calls are gated through:
  1. Approval-grant verification (mcpdl001 REQ-006, AC-4)
  2. Policy preflight (tool_policy.check_preflight)
  3. Execution (ToolExecutor)
  4. Audit emission
"""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Any

from shared.tool_executor import ToolExecutor
from shared.transport_dto import ToolCallResult

from agent.shared.models import ApprovalGrant
from agent.tool_enums import ApprovalDecisionType, OperationType
from agent.tool_exceptions import PolicyViolationError
from agent.tool_policy import check_preflight, classify_operation_type
from agent.tool_preparation import _canonical_args_hash

if TYPE_CHECKING:
    from shared.logger import Logger

    from agent.config_dataclasses import AgentConfig
    from agent.context import AgentContext

logger = logging.getLogger(__name__)

# Grant modes a verification accepts (mcpdl001 AC-4): only the issuance
# decisions tool_approval produces. Anything else is not an approval.
_GRANT_VALID_MODES: frozenset[str] = frozenset(
    {ApprovalDecisionType.AUTO.value, ApprovalDecisionType.APPROVED.value}
)

# Consumed-grant bookkeeping size before expiry-based pruning kicks in.
_CONSUMED_GRANTS_PRUNE_THRESHOLD = 1024


def _denied_result(reason: str) -> ToolCallResult:
    """Create a ToolCallResult indicating the operation was denied by policy."""
    return ToolCallResult(
        output=reason,
        is_error=True,
        request_id="",
        server_key="",
        error_type="denied",
    )


class RepositoryGateway:
    """Agent-side enforcement boundary for all repository mutation operations.

    Wraps ToolExecutor. Write/delete/API-write tool calls are gated through
    policy checks and audit logging. Read-only tool calls are forwarded
    directly without additional checks. The MCP git server behind the executor
    enforces its own refspec, protected-branch, and forced-update rules
    independently of Agent-side approval state (ADR-012 INV-04,
    docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md).

    Precondition: this gateway does not itself prompt for interactive
    approval. Callers must route write/risky tool calls through
    tool_runner.execute_all_tool_calls() (which runs the batch-level
    _run_approval_gate()), or otherwise call
    tool_approval.run_approval_checks() themselves, before invoking
    RepositoryGateway.execute(). A non-READ call must additionally carry the
    ApprovalGrant its approval issued (mcpdl001 REQ-006, AC-4): the gateway
    verifies tool/args-hash/mode/expiry/single-use immediately before
    execution and denies any mismatch — skipping the upstream gate or the
    grant can no longer reach execution.
    """

    def __init__(
        self,
        executor: ToolExecutor,
        cfg: AgentConfig,
        audit_logger: logging.Logger | Logger | None = None,
    ) -> None:
        """Initialize the repository gateway with its executor, config, and optional audit logger."""
        self._executor = executor
        self._cfg = cfg
        self._audit_logger = audit_logger
        # Single-use enforcement (REQ-006): the grant model is immutable, so
        # consumption is tracked here as the grant's issuance fingerprint.
        self._consumed_grants: set[tuple[str, str, str, float, float]] = set()

    async def execute(
        self,
        ctx: AgentContext,
        tool_name: str,
        args: dict[str, Any],
        grant: ApprovalGrant | None = None,
    ) -> ToolCallResult:
        """Execute one tool call, enforcing write boundary policy.

        Read-only tools: direct passthrough.
        Write/delete/API-write tools: grant check → policy check → execution → audit.
        """
        op = classify_operation_type(tool_name, ctx.services_required.runtime_tools)
        if op == OperationType.READ:
            return await self._executor.execute(tool_name, args)
        return await self._gate_write(ctx, tool_name, args, op, grant)

    def _verify_grant(
        self, grant: ApprovalGrant | None, tool_name: str, args: dict[str, Any]
    ) -> str:
        """Return the denial reason for *grant*, or "" when it authorizes the call.

        Checks tool name, canonical-args hash (the same computation the
        execution context records), issuance mode, expiry, and single use.
        On success the grant is marked consumed here — the gateway is the
        single-use enforcement point (ApprovalGrant model docstring, AC-4).
        """
        if grant is None:
            return "no approval grant"
        if grant.tool != tool_name:
            return f"grant tool mismatch ({grant.tool!r} != {tool_name!r})"
        if grant.args_hash != _canonical_args_hash(args):
            return "grant args hash mismatch"
        if grant.mode not in _GRANT_VALID_MODES:
            return f"grant mode {grant.mode!r} is not an approval decision"
        now = time.time()
        if now >= grant.expires_at:
            return "grant expired"
        key = (
            grant.tool,
            grant.args_hash,
            grant.mode,
            grant.issued_at,
            grant.expires_at,
        )
        if key in self._consumed_grants:
            return "grant already used"
        if len(self._consumed_grants) > _CONSUMED_GRANTS_PRUNE_THRESHOLD:
            self._consumed_grants = {
                entry for entry in self._consumed_grants if entry[4] >= now
            }
        self._consumed_grants.add(key)
        return ""

    async def _gate_write(
        self,
        ctx: AgentContext,
        tool_name: str,
        args: dict[str, Any],
        op: OperationType,
        grant: ApprovalGrant | None = None,
    ) -> ToolCallResult:
        """Enforce grant, policy, execute, audit.

        Tool-level approval is decided earlier, before the Tool call reaches
        this gate; this method verifies the grant that approval issued and
        applies the policy preflight. It does not prompt and never re-approves.
        """
        denial = self._verify_grant(grant, tool_name, args)
        if denial:
            logger.warning("gateway.grant_denied tool=%r reason=%s", tool_name, denial)
            return _denied_result(f"Grant denied: {denial} (tool={tool_name})")

        try:
            check_preflight(
                self._cfg, tool_name, args, ctx.services_required.runtime_tools
            )
        except PolicyViolationError as exc:
            logger.warning("gateway.policy_denied tool=%r reason=%s", tool_name, exc)
            return _denied_result(f"Policy blocked: {exc}")

        result = await self._executor.execute(tool_name, args)

        if self._audit_logger is not None:
            self._audit_logger.info(
                "gateway.write tool=%r op=%s is_error=%s",
                tool_name,
                op.value,
                result.is_error,
            )
        return result
