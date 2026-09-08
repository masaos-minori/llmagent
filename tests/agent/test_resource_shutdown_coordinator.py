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
