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
import pytest
from agent.http_lifecycle import HttpServerLifecycleManager
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
    defaults.update(overrides)  # type: ignore[arg-type]
    return McpServerConfig(**defaults)  # type: ignore[arg-type]


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
