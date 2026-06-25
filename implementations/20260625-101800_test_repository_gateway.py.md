# tests/test_repository_gateway.py — new file: gateway policy/approval/audit tests

**Plan:** `plans/20260625-094121_plan.md` (req #63)
**Target:** `tests/test_repository_gateway.py` (new file)

## File to create

```python
"""tests/test_repository_gateway.py
Tests for RepositoryGateway: policy enforcement, approval bypass for reads,
audit emission, and denied results.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agent.repository_gateway import RepositoryGateway


def _make_gateway(cfg=None, executor=None, audit_logger=None):
    if cfg is None:
        cfg = MagicMock()
    if executor is None:
        executor = AsyncMock()
    return RepositoryGateway(executor=executor, cfg=cfg, audit_logger=audit_logger)


def _make_ctx():
    return SimpleNamespace(
        cfg=MagicMock(),
        services=SimpleNamespace(gateway=None, tools=AsyncMock()),
        turn=SimpleNamespace(current_turn_id="turn-1"),
    )


class TestReadBypass:
    @pytest.mark.asyncio
    async def test_read_tool_bypasses_policy(self) -> None:
        """Read-only tools skip policy check and approval."""
        executor = AsyncMock(return_value=MagicMock(is_error=False))
        gw = _make_gateway(executor=executor)
        ctx = _make_ctx()

        with patch(
            "agent.repository_gateway.classify_operation_type",
            return_value=MagicMock(value="read"),
        ) as mock_classify:
            from agent.tool_policy import OperationType
            mock_classify.return_value = OperationType.READ
            await gw.execute(ctx, "list_directory", {"path": "/tmp"})

        executor.execute.assert_awaited_once_with("list_directory", {"path": "/tmp"})


class TestWritePolicy:
    @pytest.mark.asyncio
    async def test_write_tool_blocked_by_policy(self) -> None:
        """Write tool blocked by check_preflight raises PolicyViolationError → denied result."""
        from agent.tool_policy import OperationType, PolicyViolationError

        executor = AsyncMock()
        gw = _make_gateway(executor=executor)
        ctx = _make_ctx()

        with (
            patch("agent.repository_gateway.classify_operation_type", return_value=OperationType.WRITE),
            patch("agent.repository_gateway.check_preflight", side_effect=PolicyViolationError("blocked")),
        ):
            result = await gw.execute(ctx, "write_file", {"path": "/etc/passwd", "content": "x"})

        assert result.is_error is True
        assert "Policy blocked" in result.output
        executor.execute.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_write_tool_approved_and_executed(self) -> None:
        """Happy path: write tool passes policy and approval, result returned."""
        from agent.tool_policy import OperationType, RiskLevel

        expected = MagicMock(is_error=False, output="written")
        executor = AsyncMock(return_value=expected)
        gw = _make_gateway(executor=executor)
        ctx = _make_ctx()

        with (
            patch("agent.repository_gateway.classify_operation_type", return_value=OperationType.WRITE),
            patch("agent.repository_gateway.check_preflight"),
            patch("agent.repository_gateway.classify_risk", return_value=RiskLevel.NONE),
        ):
            result = await gw.execute(ctx, "write_file", {"path": "/tmp/x.txt", "content": "ok"})

        assert result is expected
        executor.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_write_tool_denied_by_user(self) -> None:
        """Write tool blocked when user denies approval."""
        from agent.tool_policy import OperationType, RiskLevel

        executor = AsyncMock()
        gw = _make_gateway(executor=executor)
        ctx = _make_ctx()

        mock_tool_call = MagicMock()
        mock_tool_call.name = "write_file"

        with (
            patch("agent.repository_gateway.classify_operation_type", return_value=OperationType.WRITE),
            patch("agent.repository_gateway.check_preflight"),
            patch("agent.repository_gateway.classify_risk", return_value=RiskLevel.HIGH),
            patch("agent.tool_approval.run_approval_checks", return_value=([], {"write_file"})),
        ):
            result = await gw.execute(ctx, "write_file", {"path": "/tmp/x.txt", "content": "ok"})

        assert result.is_error is True
        assert "Denied" in result.output
        executor.execute.assert_not_awaited()


class TestAudit:
    @pytest.mark.asyncio
    async def test_audit_emitted_on_write(self) -> None:
        """Audit logger is called after a successful write."""
        from agent.tool_policy import OperationType, RiskLevel

        audit = MagicMock()
        executor = AsyncMock(return_value=MagicMock(is_error=False))
        gw = _make_gateway(executor=executor, audit_logger=audit)
        ctx = _make_ctx()

        with (
            patch("agent.repository_gateway.classify_operation_type", return_value=OperationType.WRITE),
            patch("agent.repository_gateway.check_preflight"),
            patch("agent.repository_gateway.classify_risk", return_value=RiskLevel.NONE),
        ):
            await gw.execute(ctx, "write_file", {"path": "/tmp/x.txt", "content": "ok"})

        audit.info.assert_called_once()
        call_args = audit.info.call_args[0]
        assert "write_file" in str(call_args)
```

## Validation

```
uv run pytest tests/test_repository_gateway.py -v
```
