"""tests/test_repository_gateway.py
Tests for RepositoryGateway: policy enforcement, approval bypass for reads,
audit emission, and denied results.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from agent.repository_gateway import RepositoryGateway
from agent.tool_enums import OperationType, RiskLevel
from agent.tool_exceptions import PolicyViolationError


def _make_gateway(cfg=None, executor=None, audit_logger=None):
    if cfg is None:
        cfg = MagicMock()
    if executor is None:
        executor = AsyncMock()
    return RepositoryGateway(executor=executor, cfg=cfg, audit_logger=audit_logger)


def _make_ctx():
    workflow = SimpleNamespace(approval_pending=False, workflow_id=None)
    return SimpleNamespace(
        cfg=MagicMock(),
        services=SimpleNamespace(gateway=None, tools=AsyncMock()),
        turn=SimpleNamespace(current_turn_id="turn-1"),
        workflow=workflow,
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
            return_value=OperationType.READ,
        ):
            await gw.execute(ctx, "list_directory", {"path": "/tmp"})

        executor.execute.assert_awaited_once_with("list_directory", {"path": "/tmp"})


class TestWritePolicy:
    @pytest.mark.asyncio
    async def test_write_tool_blocked_by_policy(self) -> None:
        """Write tool blocked by check_preflight raises PolicyViolationError → denied result."""
        executor = AsyncMock()
        gw = _make_gateway(executor=executor)
        ctx = _make_ctx()

        with (
            patch(
                "agent.repository_gateway.classify_operation_type",
                return_value=OperationType.WRITE,
            ),
            patch(
                "agent.repository_gateway.check_preflight",
                side_effect=PolicyViolationError("deny", "blocked"),
            ),
        ):
            result = await gw.execute(
                ctx, "write_file", {"path": "/etc/passwd", "content": "x"}
            )

        assert result.is_error is True
        assert "Policy blocked" in result.output
        executor.execute.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_write_tool_approved_and_executed(self) -> None:
        """Happy path: write tool passes policy and approval, result returned."""
        expected = MagicMock(is_error=False, output="written")
        executor = AsyncMock()
        executor.execute = AsyncMock(return_value=expected)
        gw = _make_gateway(executor=executor)
        ctx = _make_ctx()

        with (
            patch(
                "agent.repository_gateway.classify_operation_type",
                return_value=OperationType.WRITE,
            ),
            patch("agent.repository_gateway.check_preflight"),
            patch(
                "agent.repository_gateway.classify_risk", return_value=RiskLevel.NONE
            ),
        ):
            result = await gw.execute(
                ctx, "write_file", {"path": "/tmp/x.txt", "content": "ok"}
            )

        assert result is expected
        executor.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_write_tool_denied_by_user(self) -> None:
        """Write tool blocked when user denies approval."""
        executor = AsyncMock()
        gw = _make_gateway(executor=executor)
        ctx = _make_ctx()

        with (
            patch(
                "agent.repository_gateway.classify_operation_type",
                return_value=OperationType.WRITE,
            ),
            patch("agent.repository_gateway.check_preflight"),
            patch(
                "agent.repository_gateway.classify_risk", return_value=RiskLevel.HIGH
            ),
            patch(
                "agent.tool_approval.run_approval_checks",
                return_value=([], {"write_file"}),
            ),
        ):
            result = await gw.execute(
                ctx, "write_file", {"path": "/tmp/x.txt", "content": "ok"}
            )

        assert result.is_error is True
        assert "Denied" in result.output
        executor.execute.assert_not_awaited()


class TestAudit:
    @pytest.mark.asyncio
    async def test_audit_emitted_on_write(self) -> None:
        """Audit logger is called after a successful write."""
        audit = MagicMock()
        executor = AsyncMock(return_value=MagicMock(is_error=False))
        gw = _make_gateway(executor=executor, audit_logger=audit)
        ctx = _make_ctx()

        with (
            patch(
                "agent.repository_gateway.classify_operation_type",
                return_value=OperationType.WRITE,
            ),
            patch("agent.repository_gateway.check_preflight"),
            patch(
                "agent.repository_gateway.classify_risk", return_value=RiskLevel.NONE
            ),
        ):
            await gw.execute(ctx, "write_file", {"path": "/tmp/x.txt", "content": "ok"})

        audit.info.assert_called_once()
        call_args = audit.info.call_args[0]
        assert "write_file" in str(call_args)
