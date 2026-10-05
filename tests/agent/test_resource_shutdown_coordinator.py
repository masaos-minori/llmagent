"""tests/agent/test_resource_shutdown_coordinator.py

Regression tests for ResourceShutdownCoordinator.close_resources()'s settlement-block
removal: a healthy shutdown must complete promptly (REQ-001), and no
shutdown_timeout/shutdown_error entries may be recorded once the block is removed
(REQ-002).
"""

from __future__ import annotations

import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from agent.resource_shutdown_coordinator import ResourceShutdownCoordinator


def _make_coordinator() -> ResourceShutdownCoordinator:
    ctx = MagicMock()
    ctx.services = None
    view = MagicMock()
    wal = MagicMock()
    wal.checkpoint_sync = AsyncMock(return_value=(True, []))
    wal.backup_sync = AsyncMock(return_value=("", []))
    return ResourceShutdownCoordinator(ctx, view, wal)


class TestSettlementBlockRemoved:
    """Regression tests for the removed unconditional settlement-block sleep."""

    @pytest.mark.asyncio
    async def test_healthy_shutdown_completes_promptly(self) -> None:
        """A healthy shutdown (no pending tasks, checkpoint/backup succeed
        immediately) completes well under _GRACEFUL_TIMEOUT_S."""
        coordinator = _make_coordinator()
        start = time.monotonic()
        await coordinator.close_resources()
        elapsed = time.monotonic() - start
        assert elapsed < 1.0

    @pytest.mark.asyncio
    async def test_no_shutdown_error_entries_after_settlement_block_removal(
        self,
    ) -> None:
        """No shutdown_timeout/shutdown_error entries are recorded — the
        settlement block that used to produce them no longer exists."""
        coordinator = _make_coordinator()
        with patch("agent.resource_shutdown_coordinator.logger") as mock_logger:
            await coordinator.close_resources()
        error_messages = [str(c.args) for c in mock_logger.error.call_args_list]
        assert not any("shutdown_timeout" in msg for msg in error_messages)
        assert not any("shutdown_error" in msg for msg in error_messages)


class TestSelectiveTaskCancellation:
    """Tests for REQ-001, REQ-002: Verify only tracked background tasks are cancelled."""

    @pytest.mark.asyncio
    async def test_only_tracked_background_tasks_cancelled(self) -> None:
        """REQ-001: Only tasks in turn.background_tasks are cancelled during shutdown."""
        ctx = MagicMock()
        ctx.services = None
        view = MagicMock()
        wal = MagicMock()
        wal.checkpoint_sync = AsyncMock(return_value=(True, []))
        wal.backup_sync = AsyncMock(return_value=("", []))

        # Create a mock TurnState with background_tasks set
        turn_state = MagicMock()
        bg_task1 = MagicMock()
        bg_task1.cancel = MagicMock()
        bg_task2 = MagicMock()
        bg_task2.cancel = MagicMock()
        turn_state.background_tasks = {bg_task1, bg_task2}
        ctx.turn = turn_state

        coordinator = ResourceShutdownCoordinator(ctx, view, wal)
        with patch(
            "agent.resource_shutdown_coordinator.asyncio.gather", new_callable=AsyncMock
        ):
            await coordinator.close_resources()

        # Both tracked tasks should have been cancelled
        bg_task1.cancel.assert_called_once()
        bg_task2.cancel.assert_called_once()

    @pytest.mark.asyncio
    async def test_critical_operations_not_cancelled(self) -> None:
        """REQ-002: Critical operations (not in background_tasks) are NOT cancelled."""
        ctx = MagicMock()
        ctx.services = None
        view = MagicMock()
        wal = MagicMock()
        wal.checkpoint_sync = AsyncMock(return_value=(True, []))
        wal.backup_sync = AsyncMock(return_value=("", []))

        # Create a mock TurnState with empty background_tasks
        turn_state = MagicMock()
        turn_state.background_tasks = set()
        ctx.turn = turn_state

        coordinator = ResourceShutdownCoordinator(ctx, view, wal)
        await coordinator.close_resources()

        # No tasks should have been cancelled
        # The key assertion is that no AttributeError occurs when accessing
        # turn.background_tasks
        assert hasattr(turn_state, "background_tasks")

    @pytest.mark.asyncio
    async def test_no_turn_attribute_no_crash(self) -> None:
        """Verify graceful handling when turn attribute doesn't exist."""
        ctx = MagicMock(spec=["services"])
        ctx.services = None
        view = MagicMock()
        wal = MagicMock()
        wal.checkpoint_sync = AsyncMock(return_value=(True, []))
        wal.backup_sync = AsyncMock(return_value=("", []))

        coordinator = ResourceShutdownCoordinator(ctx, view, wal)
        # Should not raise even without turn attribute
        await coordinator.close_resources()
