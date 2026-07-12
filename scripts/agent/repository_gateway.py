"""agent/repository_gateway.py
Single enforcement boundary for all repository write/delete/API-write operations.

Read-only tool calls are forwarded directly to ToolExecutor without checks.
Write/delete/API-write tool calls are gated through:
  1. Policy preflight (tool_policy.check_preflight)
  2. Approval prompt (tool_approval.run_approval_checks per call)
  3. Execution (ToolExecutor)
  4. Audit emission
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from agent.tool_enums import OperationType, RiskLevel
from agent.tool_exceptions import PolicyViolationError
from agent.tool_policy import check_preflight, classify_operation_type, classify_risk
from shared.json_utils import dumps as json_dumps
from shared.tool_executor import ToolExecutor
from shared.transport_dto import ToolCallResult

if TYPE_CHECKING:
    from agent.config_dataclasses import AgentConfig
    from agent.context import AgentContext
    from shared.logger import Logger

logger = logging.getLogger(__name__)


def _denied_result(reason: str) -> ToolCallResult:
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
    policy checks, approval prompts, and audit logging. Read-only tool calls
    are forwarded directly without additional checks.
    """

    def __init__(
        self,
        executor: ToolExecutor,
        cfg: AgentConfig,
        audit_logger: logging.Logger | Logger | None = None,
    ) -> None:
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
        """Enforce policy, prompt for approval, execute, audit."""
        try:
            check_preflight(self._cfg, tool_name, args)
        except PolicyViolationError as exc:
            logger.warning("gateway.policy_denied tool=%r reason=%s", tool_name, exc)
            return _denied_result(f"Policy blocked: {exc}")

        risk = classify_risk(self._cfg, tool_name, args)
        if risk != RiskLevel.NONE:
            from agent.tool_approval import run_approval_checks  # noqa: PLC0415

            tool_call_dict = {
                "id": f"gateway_{tool_name}",
                "function": {
                    "name": tool_name,
                    "arguments": json_dumps(args),
                },
            }
            approved_calls, denied_ids = await run_approval_checks(
                ctx,
                [tool_call_dict],
            )
            if tool_name in denied_ids or not approved_calls:
                logger.info("gateway.approval_denied tool=%r", tool_name)
                return _denied_result("Denied by user")

        result = await self._executor.execute(tool_name, args)

        if self._audit_logger is not None:
            self._audit_logger.info(
                "gateway.write tool=%r op=%s is_error=%s",
                tool_name,
                op.value,
                result.is_error,
            )
        return result
