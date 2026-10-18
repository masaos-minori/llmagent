"""Regression tests for getpgid-failure handling in HttpServerLifecycleManager.

Verifies REQ-001 / REQ-002: tracking entries are removed only after confirmed
process exit, and a failed termination logs the process PID for manual
intervention without dropping the tracking entry.
"""

from __future__ import annotations

import os
import subprocess
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import agent.http_lifecycle as hl_module
import httpx
import pytest
from agent.http_lifecycle import HttpServerLifecycleManager
from agent.http_lifecycle_errors import HttpStartupError
from shared.mcp_config import McpServerConfig, StartupMode, TransportType


def _make_cfg(**overrides: object) -> McpServerConfig:
    defaults = dict(
        transport=TransportType.HTTP,
        url="http://localhost:8080",
        startup_mode=StartupMode.SUBPROCESS,
        startup_timeout_sec=30,
        cmd=["node", "/fake/server.js"],
        auth_token="test-token",
    )
    defaults.update(overrides)  # type: ignore[arg-type] — test helper merges arbitrary override kwargs into a typed dict; mypy cannot narrow the value types
    return McpServerConfig(**defaults)  # type: ignore[arg-type] — test helper merges arbitrary override kwargs into a typed dict; mypy cannot narrow the value types


@pytest.fixture
def mgr() -> HttpServerLifecycleManager:
    return HttpServerLifecycleManager()


class TestGetPgidFailureTracking:
    """REQ-001 / REQ-002: tracking-entry behavior when getpgid fails."""

    @pytest.mark.asyncio
    async def test_tracking_removed_after_confirmed_exit(
        self, mgr: HttpServerLifecycleManager
    ) -> None:
        """REQ-001: tracking entries removed only after confirmed process exit."""
        cfg = _make_cfg()
        proc_mock = Mock(pid=9999, poll=Mock(return_value=None))
        stderr_fh_mock = MagicMock()

        with (
            patch.object(subprocess, "Popen", return_value=proc_mock),
            patch.object(os, "getpgid", side_effect=OSError("no such process")),
            patch.object(
                mgr._stderr_log_manager, "open_log", return_value=stderr_fh_mock
            ),
            patch.object(
                mgr._process_terminator,
                "terminate_with_timeout",
                AsyncMock(return_value=True),
            ),
            patch.object(hl_module, "logger") as mock_logger,
        ):
            with pytest.raises(OSError, match="no such process"):
                await mgr.start("test", cfg)

        # Successful termination -> no termination-failure error logged.
        assert mock_logger.error.call_count == 0
        # Resource cleanup completed (stderr handle closed once).
        stderr_fh_mock.close.assert_called_once()
        # Tracking entries were not retained (removed in the success path).
        assert mgr._http_procs.get("test") is None
        assert mgr._http_pgids.get("test") is None

    @pytest.mark.asyncio
    async def test_pid_logged_on_termination_failure(
        self, mgr: HttpServerLifecycleManager
    ) -> None:
        """REQ-002: PID is logged when termination fails after getpgid failure."""
        cfg = _make_cfg()
        proc_mock = Mock(pid=9999, poll=Mock(return_value=None))
        stderr_fh_mock = MagicMock()

        with (
            patch.object(subprocess, "Popen", return_value=proc_mock),
            patch.object(os, "getpgid", side_effect=OSError("no such process")),
            patch.object(
                mgr._stderr_log_manager, "open_log", return_value=stderr_fh_mock
            ),
            patch.object(
                mgr._process_terminator,
                "terminate_with_timeout",
                AsyncMock(side_effect=RuntimeError("kill failed")),
            ),
            patch.object(hl_module, "logger") as mock_logger,
        ):
            caught: BaseException | None = None
            try:
                await mgr.start("test", cfg)
            except BaseException as exc:  # noqa: BLE001 -- any propagation proves the entry was kept, not swallowed
                caught = exc

            assert caught is not None, "expected an exception to propagate"
            # Termination-failure error must include the process PID.
            logged = [str(call) for call in mock_logger.error.call_args_list]
            assert logged, "expected a termination-failure error log"
            assert "9999" in logged[0]


class TestStartupFailureCleanupCharacterization:
    """Characterization tests for stderr cleanup on the startup failure paths."""

    @pytest.mark.asyncio
    async def test_command_validation_failure_closes_stderr_and_raises(
        self, mgr: HttpServerLifecycleManager
    ) -> None:
        cfg = _make_cfg()
        stderr_fh = MagicMock()
        validate = MagicMock(side_effect=ValueError("command not allowed"))

        with (
            patch.object(mgr._stderr_log_manager, "open_log", return_value=stderr_fh),
            patch.object(mgr._command_validator, "validate", validate),
            patch.object(subprocess, "Popen") as mock_popen,
        ):
            with pytest.raises(HttpStartupError, match="command not allowed"):
                await mgr.start("test", cfg)

        stderr_fh.close.assert_called_once()
        assert "test" not in mgr._stderr_files
        mock_popen.assert_not_called()

    @pytest.mark.asyncio
    async def test_popen_failure_closes_stderr_and_reraises(
        self, mgr: HttpServerLifecycleManager
    ) -> None:
        cfg = _make_cfg()
        stderr_fh = MagicMock()

        with (
            patch.object(mgr._stderr_log_manager, "open_log", return_value=stderr_fh),
            patch.object(
                subprocess, "Popen", side_effect=FileNotFoundError("no binary")
            ),
        ):
            with pytest.raises(FileNotFoundError, match="no binary"):
                await mgr.start("test", cfg)

        stderr_fh.close.assert_called_once()
        assert "test" not in mgr._stderr_files

    @pytest.mark.asyncio
    async def test_nonzero_exit_code_is_logged_after_getpgid_failure(
        self, mgr: HttpServerLifecycleManager
    ) -> None:
        cfg = _make_cfg()
        proc_mock = Mock(pid=9999, poll=Mock(return_value=1))
        stderr_fh = MagicMock()

        with (
            patch.object(subprocess, "Popen", return_value=proc_mock),
            patch.object(os, "getpgid", side_effect=OSError("no such process")),
            patch.object(mgr._stderr_log_manager, "open_log", return_value=stderr_fh),
            patch.object(
                mgr._process_terminator,
                "terminate_with_timeout",
                AsyncMock(return_value=True),
            ),
            patch.object(hl_module, "logger") as mock_logger,
        ):
            with pytest.raises(OSError, match="no such process"):
                await mgr.start("test", cfg)

        logged = [call for call in mock_logger.info.call_args_list if call.args]
        exit_code_logs = [
            call for call in logged if "terminated with exit code" in str(call.args[0])
        ]
        assert exit_code_logs, "expected an exit-code info log"
        assert exit_code_logs[0].args[3] == 1
        assert mgr._http_procs.get("test") is None
        assert mgr._http_pgids.get("test") is None
        stderr_fh.close.assert_called_once()


class TestHealthAndRestartTrackingCharacterization:
    """Characterization tests for health-check timestamps and restart cleanup."""

    @pytest.mark.asyncio
    async def test_verify_running_async_stamps_time_on_http_error(
        self, mgr: HttpServerLifecycleManager
    ) -> None:
        cfg = _make_cfg()
        mgr._http_procs["test"] = Mock(pid=1, poll=Mock(return_value=None))

        with patch.object(
            hl_module.HealthChecker,
            "verify_running_async",
            AsyncMock(side_effect=httpx.ConnectError("boom")),
        ):
            assert await mgr.verify_running_async("test", cfg) is False

        assert "test" in mgr._last_health_check

    @pytest.mark.asyncio
    async def test_restart_tolerates_stderr_close_error(
        self, mgr: HttpServerLifecycleManager
    ) -> None:
        cfg = _make_cfg()
        stderr_fh = MagicMock()
        stderr_fh.close.side_effect = OSError("close failed")
        mgr._stderr_files["test"] = stderr_fh
        mgr._stderr_log_manager._log_paths["test"] = "/tmp/opencode/test.log"
        mgr._last_health_check["test"] = 1.0

        with patch.object(mgr, "start", AsyncMock()) as start:
            await mgr.restart("test", cfg)

        start.assert_awaited_once_with("test", cfg)
        assert "test" not in mgr._stderr_files
        assert "test" not in mgr._last_health_check
        assert mgr._stderr_log_manager.get_log_path("test") is None
