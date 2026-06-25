# scripts/agent/repository_gateway.py — new file: RepositoryGateway

**Plan:** `plans/20260625-094121_plan.md` (req #63)
**Target:** `scripts/agent/repository_gateway.py` (new file)

## File to create

```python
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

from shared.tool_executor import ToolCallResult, ToolExecutor

from agent.tool_policy import (
    OperationType,
    PolicyViolationError,
    RiskLevel,
    check_preflight,
    classify_operation_type,
    classify_risk,
)

if TYPE_CHECKING:
    from agent.config_dataclasses import AgentConfig
    from agent.context import AgentContext

logger = logging.getLogger(__name__)


def _denied_result(reason: str) -> ToolCallResult:
    return ToolCallResult(output=reason, is_error=True, server_key="", error_type="denied")


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
        audit_logger: logging.Logger | None = None,
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

            approved_calls, denied_ids = await run_approval_checks(
                ctx, [type("_TC", (), {"name": tool_name, "input": args})()]
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
```

## Notes

- `_denied_result()` returns a `ToolCallResult` with `is_error=True` and `error_type="denied"`.
  Verify `ToolCallResult` constructor accepts `error_type` keyword arg (check `shared/tool_executor.py`).
- The `run_approval_checks` import is lazy (`PLC0415`) to avoid circular imports at module load time.
- The per-tool approval check differs from the current batch approval in `execute_all_tool_calls()`.
  The `_TC` adapter creates a minimal tool-call-like object matching what `run_approval_checks` expects.
  Verify the exact type/protocol that `run_approval_checks` accepts and update accordingly.

## Validation

```
ruff check scripts/agent/repository_gateway.py
mypy scripts/agent/repository_gateway.py
uv run pytest tests/test_repository_gateway.py -v
```
