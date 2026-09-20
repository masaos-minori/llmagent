"""Tests for ShutdownCoordinator.shutdown_all()."""

import time
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest
from agent.http_lifecycle_shutdown_coordinator import ShutdownCoordinator


class TestShutdownCoordinatorShutdownAll:
    """Tests for ShutdownCoordinator.shutdown_all()."""

    @pytest.fixture
    def mock_manager(self):
        mgr = Mock()
        mgr._http_procs = {}
        mgr._http_pgids = {}
        mgr._stderr_files = {}
        mgr._stderr_log_manager = Mock()
        mgr._last_health_check = {}
        mgr._process_terminator = AsyncMock()
        mgr.process_terminator = mgr._process_terminator
        mgr.cleanup_server_key = Mock()
        mgr.remove_process_entry = Mock()
        mgr.clear_all_health_checks = Mock()
        
        def iter_processes():
            yield from mgr._http_procs.items()
        
        mgr.iter_processes = iter_processes
        return mgr

    @pytest.fixture
    def mock_proc(self):
        proc = Mock()
        proc.poll.return_value = None  # still running
        proc.pid = 1234
        return proc

    @pytest.fixture
    def mock_stderr_fh(self):
        fh = MagicMock()
        fh.close = MagicMock()
        return fh

    async def test_shutdown_all_clears_internal_state(
        self, mock_manager, mock_proc, mock_stderr_fh
    ):
        mock_manager._http_procs["server1"] = mock_proc
        mock_manager._http_pgids["server1"] = 1234
        mock_manager._stderr_files["server1"] = mock_stderr_fh
        mock_manager._last_health_check["server1"] = time.monotonic()

        coord = ShutdownCoordinator()
        await coord.shutdown_all(mock_manager)

        mock_manager.remove_process_entry.assert_called_once_with("server1")
        mock_manager.cleanup_server_key.assert_called_once_with("server1")
        mock_manager.clear_all_health_checks.assert_called_once()

    async def test_shutdown_all_uses_caller_supplied_terminator(
        self, mock_manager, mock_proc
    ):
        mock_manager._http_procs["server1"] = mock_proc
        custom_terminator = AsyncMock()

        coord = ShutdownCoordinator()
        await coord.shutdown_all(mock_manager, terminator=custom_terminator)

        custom_terminator.terminate_with_timeout.assert_called_once_with(
            mock_proc, "server1", timeout=30.0
        )

    async def test_shutdown_all_closes_stderr_file_handles(
        self, mock_manager, mock_proc, mock_stderr_fh
    ):
        mock_manager._http_procs["server1"] = mock_proc
        mock_manager._stderr_files["server1"] = mock_stderr_fh

        coord = ShutdownCoordinator()
        await coord.shutdown_all(mock_manager)

        mock_manager.remove_process_entry.assert_called_once_with("server1")
        mock_manager.cleanup_server_key.assert_called_once_with("server1")

    async def test_shutdown_all_skips_already_exited_processes(self, mock_manager):
        exited_proc = Mock()
        exited_proc.poll.return_value = 1  # already exited
        mock_manager._http_procs["server1"] = exited_proc

        coord = ShutdownCoordinator()
        await coord.shutdown_all(mock_manager)

        # Should not call terminate_with_timeout for an already-exited process
        mock_manager._process_terminator.terminate_with_timeout.assert_not_called()
