"""Regression tests for getpgid-failure handling in HttpServerLifecycleManager.

Verifies REQ-001 / REQ-002: tracking entries are removed only after confirmed
process exit, and a failed termination logs the process PID for manual
intervention without dropping the tracking entry.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import agent.http_lifecycle as hl_module
import agent.http_lifecycle_subprocess_launcher as launcher_module
import httpx
import pytest
from agent.http_lifecycle import HttpServerLifecycleManager
from agent.http_lifecycle_command_validator import CommandValidator
from agent.http_lifecycle_errors import (
    HttpStartupError,
    RestartBlockedError,
    StartupCode,
    StartupFailure,
    TerminationOutcome,
)
from agent.http_lifecycle_process_record import ManagedProcessRecord
from agent.lifecycle import LifecycleState
from agent.shutdown_budget import ShutdownBudget
from shared.mcp_config import McpServerConfig, StartupMode, TransportType

pytestmark = pytest.mark.contract


def _make_record(
    proc: object,
    pgid: int | None = None,
    state: LifecycleState = LifecycleState.RUNNING,
) -> ManagedProcessRecord:
    """Build a minimal ownership record for tests that seed the registry."""
    return ManagedProcessRecord(  # type: ignore[arg-type] — test helper passes Mock process objects
        process=proc,
        pid=getattr(proc, "pid", 0),
        pgid=pgid,
        stderr_log=None,
        state=state,
    )


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


@pytest.fixture(autouse=True)
def _permissive_spawn_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    """Opt into the documented permissive mode for these spawn-behavior tests.

    Strict confinement is the production default (cliplc006 REQ-004), and these cases
    characterize process-group, cleanup, and shutdown behavior through a fixture binary
    that lives on PATH rather than in the trusted directory. Confinement itself is
    covered in tests/agent/test_http_lifecycle_command_validator.py.
    """
    monkeypatch.setenv("LLMAGENT_COMMAND_MODE", "permissive")


@pytest.fixture
def mgr() -> HttpServerLifecycleManager:
    return HttpServerLifecycleManager()


def _assert_default_termination_window(terminator: AsyncMock) -> None:
    """Assert a terminate call used the module default window and carried no budget.

    The startup-failure and restart paths own their own bound (they are not part of a
    shutdown sequence), so what pins them is that no budget reached the call.
    """
    call = terminator.call_args
    assert call is not None, "expected terminate_with_timeout() to be called"
    assert call.kwargs["timeout"] == hl_module.TERMINATE_TIMEOUT_SEC
    assert call.kwargs.get("budget") is None


class TestGetPgidFailureTracking:
    """REQ-001 / REQ-002: tracking-entry behavior when getpgid fails."""

    @pytest.mark.asyncio
    async def test_tracking_removed_after_confirmed_exit(
        self, mgr: HttpServerLifecycleManager
    ) -> None:
        """A confirmed exit logs no failure and releases every tracking entry."""
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
                AsyncMock(return_value=TerminationOutcome.EXITED),
            ) as term,
            patch.object(launcher_module, "logger") as mock_logger,
        ):
            with pytest.raises(OSError, match="no such process"):
                await mgr.start("test", cfg)

        # Successful termination -> no termination-failure error logged.
        assert mock_logger.error.call_count == 0
        # The startup-failure path owns its own bound: default window, no budget.
        _assert_default_termination_window(term)
        # Resource cleanup completed (stderr handle closed once).
        stderr_fh_mock.close.assert_called_once()
        # The confirmed exit released the ownership record (REQ-002).
        assert mgr._records.get("test") is None

    @pytest.mark.asyncio
    async def test_unconfirmed_exit_is_logged_with_pid_and_the_record_is_retained(
        self, mgr: HttpServerLifecycleManager
    ) -> None:
        """REQ-002: an unconfirmed exit retains the record and names the pid."""
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
                AsyncMock(return_value=TerminationOutcome.EXIT_UNCONFIRMED),
            ) as term,
            patch.object(launcher_module, "logger") as mock_logger,
        ):
            with pytest.raises(OSError, match="no such process"):
                await mgr.start("test", cfg)

        logged = [str(call) for call in mock_logger.error.call_args_list]
        assert len(logged) == 1
        assert "9999" in logged[0] and "exit_unconfirmed" in logged[0]
        _assert_default_termination_window(term)
        # No pgid to probe: the exit cannot be observed, so the record stays
        # retained (pgid None, the honest state) for shutdown_all() to name.
        record = mgr._records["test"]
        assert record.last_outcome is TerminationOutcome.EXIT_UNCONFIRMED
        assert record.pgid is None
        assert record.state is LifecycleState.EXIT_UNCONFIRMED
        stderr_fh_mock.close.assert_called_once()

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
            ) as term,
            patch.object(launcher_module, "logger") as mock_logger,
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
            _assert_default_termination_window(term)


class TestShutdownAllBudgetForwarding:
    """REQ-010: the manager forwards the budget it is handed to the terminate call."""

    @pytest.mark.asyncio
    async def test_supplied_budget_reaches_the_terminate_call(
        self, mgr: HttpServerLifecycleManager
    ) -> None:
        """Both the clamped window and the budget itself are on the call arguments."""
        budget = ShutdownBudget(total_seconds=15.0)
        budget.arm()
        proc = Mock(pid=9999, poll=Mock(return_value=None))
        term = AsyncMock(return_value=TerminationOutcome.EXITED)

        mgr._records["test"] = _make_record(proc)
        with patch.object(mgr._process_terminator, "terminate_with_timeout", term):
            unconfirmed = await mgr.shutdown_all(budget=budget)

        call = term.call_args
        assert call is not None
        # The 30 s coordinator window cannot be used up by a 15 s budget.
        assert call.kwargs["timeout"] == pytest.approx(15.0, abs=0.5)
        assert call.kwargs["budget"] is budget
        assert unconfirmed == []


class TestStartupFailureCleanupCharacterization:
    """Characterization tests for stderr cleanup on the startup failure paths."""

    @pytest.mark.asyncio
    @pytest.mark.characterization
    async def test_command_validation_failure_closes_stderr_and_raises(
        self, mgr: HttpServerLifecycleManager
    ) -> None:
        """A rejection by the real validator releases the handle (REQ-008).

        The validator is not mocked: HttpStartupError is what the production path
        actually raises, and it is a RuntimeError, not a ValueError.
        """
        cfg = _make_cfg(cmd=["nonexistent_cmd_xyz_12345", "/fake/server.js"])
        stderr_fh = MagicMock()

        with (
            patch.object(mgr._stderr_log_manager, "open_log", return_value=stderr_fh),
            patch.object(mgr, "_command_validator", CommandValidator()),
            patch.object(subprocess, "Popen") as mock_popen,
        ):
            with pytest.raises(HttpStartupError, match="not found in PATH"):
                await mgr.start("test", cfg)

        stderr_fh.close.assert_called_once()
        assert "test" not in mgr._stderr_files
        mock_popen.assert_not_called()

    @pytest.mark.asyncio
    @pytest.mark.characterization
    async def test_validator_value_error_still_releases_stderr_handle(
        self, mgr: HttpServerLifecycleManager
    ) -> None:
        """The other raise shape stays covered: a ValueError is converted and cleaned."""
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
    @pytest.mark.characterization
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
    @pytest.mark.characterization
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
                AsyncMock(return_value=TerminationOutcome.EXITED),
            ) as term,
            patch.object(launcher_module, "logger") as mock_logger,
        ):
            with pytest.raises(OSError, match="no such process"):
                await mgr.start("test", cfg)

        logged = [call for call in mock_logger.info.call_args_list if call.args]
        exit_code_logs = [
            call for call in logged if "terminated with exit code" in str(call.args[0])
        ]
        assert exit_code_logs, "expected an exit-code info log"
        assert exit_code_logs[0].args[3] == 1
        _assert_default_termination_window(term)
        assert mgr._records.get("test") is None
        stderr_fh.close.assert_called_once()


class TestSubprocessSpawnCharacterization:
    """Characterization tests for the spawn/validate step of subprocess startup."""

    @pytest.mark.asyncio
    @pytest.mark.characterization
    async def test_empty_command_raises_before_spawn(
        self, mgr: HttpServerLifecycleManager
    ) -> None:
        """An empty cmd is a startup failure raised before command validation or Popen.

        The stderr handle opened for the attempt is closed and its tracking entry is
        dropped on this path, matching the other failure branches.
        """
        cfg = _make_cfg(cmd=[""])
        stderr_fh = MagicMock()

        with (
            patch.object(mgr._stderr_log_manager, "open_log", return_value=stderr_fh),
            patch.object(mgr._command_validator, "validate") as mock_validate,
            patch.object(subprocess, "Popen") as mock_popen,
        ):
            with pytest.raises(HttpStartupError) as exc_info:
                await mgr.start("test", cfg)

        assert exc_info.value.failure.reason == "Empty command configuration"
        assert exc_info.value.failure.server_key == "test"
        mock_validate.assert_not_called()
        mock_popen.assert_not_called()
        stderr_fh.close.assert_called_once()
        assert "test" not in mgr._stderr_files
        assert "test" not in mgr._records

    @pytest.mark.asyncio
    @pytest.mark.characterization
    async def test_popen_options_cannot_be_overridden(
        self, mgr: HttpServerLifecycleManager, tmp_path
    ) -> None:
        """REQ-002 (AC-2) and REQ-003 (AC-1): no config value reaches the Popen
        kwargs, and argv[0] is the path the validator returned."""
        exe = tmp_path / "mcp_node"
        exe.write_text("#!/bin/sh\nexit 0\n")
        exe.chmod(0o755)
        st = os.stat(exe)
        cfg = _make_cfg(
            startup_timeout_sec=0,
            cmd=["node", "/fake/server.js"],
            env={"HOME": "/tmp/evil-home"},
            credential_env=("GITHUB_TOKEN",),
        )
        # The config parser rejects a denylisted `env` key (row 1); injecting it here is
        # the defense-in-depth case where such a value still reaches the launcher.
        cfg.env["PYTHONPATH"] = "/tmp/evil"
        proc_mock = Mock(pid=4242, poll=Mock(return_value=None))
        stderr_fh = MagicMock()
        validate = MagicMock(return_value=(str(exe), (st.st_dev, st.st_ino)))

        with (
            patch.object(mgr._stderr_log_manager, "open_log", return_value=stderr_fh),
            patch.object(mgr._command_validator, "validate", validate),
            patch.object(subprocess, "Popen", return_value=proc_mock) as mock_popen,
            patch.object(os, "getpgid", return_value=4242),
        ):
            await mgr.start("test", cfg)

        call = mock_popen.call_args
        assert call is not None
        assert call.args[0][0] == str(exe)
        assert call.args[0][1] == "/fake/server.js"
        kwargs = call.kwargs
        assert set(kwargs) == {"start_new_session", "stdout", "stderr", "env"}
        assert kwargs["start_new_session"] is True
        assert kwargs["stdout"] is subprocess.DEVNULL
        assert kwargs["stderr"] is stderr_fh
        for forbidden in ("shell", "preexec_fn", "cwd", "close_fds"):
            assert forbidden not in kwargs
        assert kwargs["env"]["HOME"] != "/tmp/evil-home"
        assert "PYTHONPATH" not in kwargs["env"]
        record = mgr._records["test"]
        assert record.process is proc_mock
        assert record.pgid == 4242

    @pytest.mark.asyncio
    @pytest.mark.characterization
    async def test_changed_identity_between_validation_and_spawn_aborts(
        self, mgr: HttpServerLifecycleManager, tmp_path
    ) -> None:
        """REQ-003 (AC-1): a file identity that no longer matches aborts the start."""
        exe = tmp_path / "mcp_node"
        exe.write_text("#!/bin/sh\nexit 0\n")
        exe.chmod(0o755)
        cfg = _make_cfg(startup_timeout_sec=0, cmd=["node", "/fake/server.js"])
        stderr_fh = MagicMock()
        # An identity that cannot match the file on disk: the re-check must abort.
        validate = MagicMock(return_value=(str(exe), (0, 0)))

        with (
            patch.object(mgr._stderr_log_manager, "open_log", return_value=stderr_fh),
            patch.object(mgr._command_validator, "validate", validate),
            patch.object(subprocess, "Popen") as mock_popen,
        ):
            with pytest.raises(HttpStartupError) as exc_info:
                await mgr.start("test", cfg)

        reason = exc_info.value.failure.reason
        assert "test" in reason
        assert str(exe) in reason
        mock_popen.assert_not_called()
        stderr_fh.close.assert_called_once()
        assert "test" not in mgr._stderr_files


class TestHealthAndRestartTrackingCharacterization:
    """Characterization tests for health-check timestamps and restart cleanup."""

    @pytest.mark.asyncio
    @pytest.mark.characterization
    async def test_verify_running_async_stamps_time_on_http_error(
        self, mgr: HttpServerLifecycleManager
    ) -> None:
        cfg = _make_cfg()
        mgr._records["test"] = _make_record(Mock(pid=1, poll=Mock(return_value=None)))

        with patch.object(
            hl_module.HealthChecker,
            "verify_running_async",
            AsyncMock(side_effect=httpx.ConnectError("boom")),
        ):
            assert await mgr.verify_running_async("test", cfg) is False

        assert "test" in mgr._last_health_check

    @pytest.mark.asyncio
    @pytest.mark.characterization
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


class TestRestartRefusal:
    """REQ-005 / REQ-011: restart over a live process whose exit is not confirmed
    raises RestartBlockedError and starts no second process on the same port."""

    @pytest.mark.asyncio
    async def test_unconfirmed_exit_blocks_restart_and_starts_nothing(
        self, mgr: HttpServerLifecycleManager
    ) -> None:
        """AC-2: no start() call after an unconfirmed outcome (port-conflict prevention)."""
        cfg = _make_cfg()
        proc_mock = Mock(pid=9999, poll=Mock(return_value=None))
        mgr._records["test"] = _make_record(proc_mock)
        term = AsyncMock(return_value=TerminationOutcome.EXIT_UNCONFIRMED)
        start = AsyncMock()

        with (
            patch.object(mgr._process_terminator, "terminate_with_timeout", term),
            patch.object(mgr, "start", start),
        ):
            with pytest.raises(RestartBlockedError, match="not confirmed"):
                await mgr.restart("test", cfg)

        start.assert_not_awaited()
        # The record stays retained so status surfaces still name the live process.
        record = mgr._records["test"]
        assert record.state is LifecycleState.EXIT_UNCONFIRMED
        assert record.last_outcome is TerminationOutcome.EXIT_UNCONFIRMED

    @pytest.mark.asyncio
    async def test_confirmed_exit_releases_record_and_restarts(
        self, mgr: HttpServerLifecycleManager
    ) -> None:
        """Ownership rule in the restart path: release only on a confirmed exit."""
        cfg = _make_cfg()
        proc_mock = Mock(pid=9999, poll=Mock(return_value=None))
        mgr._records["test"] = _make_record(proc_mock)
        term = AsyncMock(return_value=TerminationOutcome.EXITED)
        start = AsyncMock()

        with (
            patch.object(mgr._process_terminator, "terminate_with_timeout", term),
            patch.object(mgr, "start", start),
        ):
            await mgr.restart("test", cfg)

        start.assert_awaited_once_with("test", cfg)
        assert "test" not in mgr._records


class TestSnapshotLogicalIdentifier:
    """REQ-007 (AC-4): the public snapshot carries a logical identifier, not the log path."""

    def _seed(self, mgr: HttpServerLifecycleManager, path: str) -> dict | None:
        mgr._stderr_log_manager._log_paths["test"] = path
        mgr._records["test"] = _make_record(
            Mock(pid=1234, poll=Mock(return_value=None))
        )
        return mgr.get_process_snapshot("test")

    def test_snapshot_value_is_the_logical_identifier(self) -> None:
        mgr = HttpServerLifecycleManager()
        root = os.path.join(tempfile.gettempdir(), "mcp_server_logs")
        path = os.path.join(root, "test", "stderr.log")
        snap = self._seed(mgr, path)
        assert snap is not None
        assert snap["stderr_log"] == "test/stderr.log"

    def test_snapshot_value_has_no_absolute_path(self) -> None:
        mgr = HttpServerLifecycleManager()
        snap = self._seed(mgr, "/opt/llm/logs/test.stderr.log")
        assert snap is not None
        assert not snap["stderr_log"].startswith("/")
        assert snap["stderr_log"] == "test.stderr.log"

    def test_empty_path_still_yields_empty_string(self) -> None:
        mgr = HttpServerLifecycleManager()
        snap = self._seed(mgr, "")
        assert snap is not None
        assert snap["stderr_log"] == ""

    def test_writer_and_tail_reader_keep_the_real_path(self) -> None:
        mgr = HttpServerLifecycleManager()
        root = os.path.join(tempfile.gettempdir(), "mcp_server_logs")
        path = os.path.join(root, "test", "stderr.log")
        self._seed(mgr, path)
        assert mgr._stderr_log_manager.get_log_path("test") == path


class TestErrorRenderingCharacterization:
    """REQ-002 (AC-1): the rendered error is the code plus a redacted summary."""

    @pytest.mark.characterization
    def test_reason_with_the_log_directory_renders_without_an_absolute_path(
        self,
    ) -> None:
        root = os.path.join(tempfile.gettempdir(), "mcp_server_logs")
        failure = StartupFailure(
            server_key="test",
            code=StartupCode.GENERAL,
            reason=f"binary not found while reading {root}/test/stderr.log",
            stderr_full="",
        )
        rendered = str(HttpStartupError(failure))
        assert (
            rendered == "test: general: binary not found while reading test/stderr.log"
        )
        assert not any(token.startswith("/") for token in rendered.split())

    @pytest.mark.characterization
    def test_existing_match_assertions_still_hold_under_the_new_rendering(self) -> None:
        # The match strings at lines 244 and 265 are substrings of the reason, so they
        # keep matching; the full rendered form is pinned here for the same failures.
        failure = StartupFailure(
            server_key="test",
            code=StartupCode.GENERAL,
            reason="nonexistent_cmd_xyz_12345 not found in PATH",
            stderr_full="",
        )
        assert str(HttpStartupError(failure)) == (
            "test: general: nonexistent_cmd_xyz_12345 not found in PATH"
        )
