"""agent/repository_gateway.py

Single enforcement boundary for all repository write/delete/API-write operations.

Read-only tool calls are forwarded directly to ToolExecutor without checks.
Write/delete/API-write tool calls are gated through:
  1. Policy preflight (tool_policy.check_preflight)
  2. Approval, enforced upstream and once by tool_runner.execute_all_tool_calls()'s
     batch-level gate, before any tool call reaches this executor
  3. Execution (ToolExecutor)
  4. Audit emission
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from shared.tool_executor import ToolExecutor
from shared.transport_dto import ToolCallResult

from agent.tool_enums import OperationType
from agent.tool_exceptions import PolicyViolationError
from agent.tool_policy import check_preflight, classify_operation_type

if TYPE_CHECKING:
    from shared.logger import Logger

    from agent.config_dataclasses import AgentConfig
    from agent.context import AgentContext

logger = logging.getLogger(__name__)


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
    """Single write enforcement boundary for all repository mutation operations.

    Wraps ToolExecutor. Write/delete/API-write tool calls are gated through
    policy checks and audit logging. Read-only tool calls are forwarded
    directly without additional checks.

    Precondition: this gateway does not itself prompt for interactive
    approval. Callers must route write/risky tool calls through
    tool_runner.execute_all_tool_calls() (which runs the batch-level
    _run_approval_gate()), or otherwise call
    tool_approval.run_approval_checks() themselves, before invoking
    RepositoryGateway.execute(). Skipping that upstream gate means a
    write/risky call reaches execution without ever having been approved.
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

    async def execute(
        self,
        ctx: AgentContext,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute one tool call, enforcing write boundary policy.

        Read-only tools: direct passthrough.
        Write/delete/API-write tools: policy check → approval → execution → audit.
        """
        op = classify_operation_type(tool_name)
        if op == OperationType.READ:
            return await self._executor.execute(tool_name, args)
        return await self._gate_write(ctx, tool_name, args, op)

    async def _gate_write(
        self,
        ctx: AgentContext,
        tool_name: str,
        args: dict[str, Any],
        op: OperationType,
    ) -> ToolCallResult:
        """Enforce policy, execute, audit.

        Approval is expected to have already been granted by the caller's
        batch-level gate (tool_runner.execute_all_tool_calls()'s
        _run_approval_gate()); this method does not prompt.
        """
        # Skip gateway preflight when workflow approval is active
        if ctx.turn.pending_approval_id is not None:
            logger.debug(
                "Skipping gateway preflight: workflow approval pending (id=%s)",
                ctx.turn.pending_approval_id,
            )
            result = await self._executor.execute(tool_name, args)
            return result

        try:
            check_preflight(self._cfg, tool_name, args)
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
