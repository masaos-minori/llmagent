from unittest.mock import AsyncMock, MagicMock

import pytest

from scripts.agent.http_lifecycle_shutdown_coordinator import ShutdownCoordinator


class TestShutdownCoordinatorFailureScenarios:
    """Tests for REQ-003, REQ-004: Verify tracking entry handling on shutdown failure."""

    @pytest.mark.asyncio
    async def test_tracking_entry_persists_on_termination_failure(self):
        """REQ-004: Tracking entry persists when termination fails."""
        coordinator = ShutdownCoordinator()
        server_key = "test-server-key"

        # Setup mock manager
        mock_manager = MagicMock()
        mock_manager.process_terminator = MagicMock()
        mock_manager.process_terminator.terminate_with_timeout = AsyncMock(
            side_effect=OSError("Connection refused")
        )
        mock_manager.cleanup_server_key = MagicMock()
        mock_manager.remove_process_entry = MagicMock()
        mock_proc = MagicMock()
        mock_proc.poll.return_value = None  # Process still running
        mock_manager.iter_processes = MagicMock(return_value=[(server_key, mock_proc)])
        mock_manager.clear_all_health_checks = MagicMock()

        # Exception is caught and logged, not re-raised
        await coordinator.shutdown_all(mock_manager)

        # Verify cleanup_server_key was NOT called
        mock_manager.cleanup_server_key.assert_not_called()

    @pytest.mark.asyncio
    async def test_tracking_entry_removed_on_success(self):
        """REQ-001: Tracking entry is removed after confirmed termination."""
        coordinator = ShutdownCoordinator()
        server_key = "test-server-key"

        # Setup mock manager
        mock_manager = MagicMock()
        mock_manager.process_terminator = MagicMock()
        mock_manager.process_terminator.terminate_with_timeout = AsyncMock(
            return_value=None
        )
        mock_manager.cleanup_server_key = MagicMock()
        mock_manager.remove_process_entry = MagicMock()
        mock_proc = MagicMock()
        mock_proc.poll.return_value = None  # Process still running
        mock_manager.iter_processes = MagicMock(return_value=[(server_key, mock_proc)])
        mock_manager.clear_all_health_checks = MagicMock()

        # Attempt shutdown
        await coordinator.shutdown_all(mock_manager)

        # Verify cleanup_server_key WAS called
        mock_manager.cleanup_server_key.assert_called_once_with(server_key)
