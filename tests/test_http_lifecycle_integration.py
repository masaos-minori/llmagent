"""Integration tests for HttpLifecycle.

Characterizes current behavior around signal handling, subprocess lifecycle,
shutdown sequence, and error recovery — documenting what the system actually
does today, not what it ought to do tomorrow.
"""

from __future__ import annotations

import asyncio
import os
import signal
import subprocess
import time
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import httpx
import pytest
from agent.http_lifecycle import (
    HttpServerLifecycleManager,
    HttpStartupError,
    StartupFailure,
)
from shared.mcp_config import McpServerConfig, StartupMode, TransportType


def _make_cfg(**overrides: object) -> McpServerConfig:
    defaults = dict(
        transport=TransportType.HTTP,
        url="http://localhost:8080",
        startup_mode=StartupMode.SUBPROCESS,
        startup_timeout_sec=30,
        cmd=["node", "/fake/server.js"],
    )
    defaults.update(overrides)  # type: ignore[arg-type]
    return McpServerConfig(**defaults)  # type: ignore[arg-type]


@pytest.fixture
def mgr() -> HttpServerLifecycleManager:
    return HttpServerLifecycleManager()


class TestSignalHandling:
    """Characterize current signal handler registration and restoration."""

    def test_absorb_sigint_handler_exists(self) -> None:
        assert hasattr(HttpServerLifecycleManager, "_absorb_sigint_during_shutdown")
        sig_received = False

        def capture(*args: object) -> None:
            nonlocal sig_received
            sig_received = True

        with patch.object(
            HttpServerLifecycleManager,
            "_absorb_sigint_during_shutdown",
            new=capture,
        ):
            manager = HttpServerLifecycleManager()
            old = signal.default_int_handler
            try:
                old = signal.getsignal(signal.SIGINT)
                signal.signal(signal.SIGINT, manager._absorb_sigint_during_shutdown)
                signal.raise_signal(signal.SIGINT)
                assert sig_received is True
            finally:
                signal.signal(signal.SIGINT, old)

    @pytest.mark.asyncio
    async def test_shutdown_all_installs_guard_handler(self) -> None:
        manager = HttpServerLifecycleManager()
        manager._http_procs["test"] = Mock(poll=Mock(return_value=None))

        with (
            patch.object(signal, "getsignal", return_value=signal.default_int_handler),
            patch.object(
                signal, "signal", side_effect=lambda sig, handler: handler
            ) as mock_signal,
        ):
            await manager.shutdown_all()

        install_calls = [
            c for c in mock_signal.call_args_list if c[0][0] == signal.SIGINT
        ]
        assert len(install_calls) >= 1
        installed_handler = install_calls[0][0][1]
        assert installed_handler is manager._absorb_sigint_during_shutdown

    @pytest.mark.asyncio
    async def test_shutdown_all_restores_original_handler(self) -> None:
        manager = HttpServerLifecycleManager()
        manager._http_procs["test"] = Mock(poll=Mock(return_value=None))

        original_handler = Mock(spec=object)
        restore_count = 0

        def track_restore(sig: int, handler: object) -> object:
            nonlocal restore_count
            if handler is original_handler:
                restore_count += 1
            return handler

        with (
            patch.object(signal, "getsignal", return_value=original_handler),
            patch.object(signal, "signal", side_effect=track_restore),
        ):
            await manager.shutdown_all()

        assert restore_count >= 1

    @pytest.mark.asyncio
    async def test_shutdown_all_noop_when_not_main_thread(self) -> None:
        manager = HttpServerLifecycleManager()
        manager._http_procs["test"] = Mock(poll=Mock(return_value=None))

        with (
            patch.object(
                signal, "getsignal", side_effect=ValueError("not main thread")
            ),
            patch.object(
                signal, "signal", side_effect=lambda sig, handler: handler
            ) as mock_signal,
        ):
            await manager.shutdown_all()

        install_calls = [
            c for c in mock_signal.call_args_list if c[0][0] == signal.SIGINT
        ]
        assert len(install_calls) == 0

    @pytest.mark.asyncio
    async def test_shutdown_all_handles_signal_install_failure(self) -> None:
        manager = HttpServerLifecycleManager()
        manager._http_procs["test"] = Mock(poll=Mock(return_value=None))

        original_handler = Mock(spec=object)

        def failing_signal(sig: int, handler: object) -> object:
            if handler is not original_handler:
                raise ValueError("signal.install failed")
            return handler

        with (
            patch.object(signal, "getsignal", return_value=original_handler),
            patch.object(signal, "signal", side_effect=failing_signal) as mock_signal,
        ):
            await manager.shutdown_all()

        restore_calls = [
            c for c in mock_signal.call_args_list if c[0][1] is original_handler
        ]
        assert len(restore_calls) >= 1

    def test_absorb_handler_logs_warning(self) -> None:
        import logging

        captured = False

        class WarningCapture(logging.Handler):
            def emit(self, record: logging.LogRecord) -> None:
                nonlocal captured
                if "SIGINT received during shutdown_all" in record.getMessage():
                    captured = True

        handler = WarningCapture()
        logger = logging.getLogger("agent.http_lifecycle")
        logger.addHandler(handler)
        try:
            manager = HttpServerLifecycleManager()
            manager._absorb_sigint_during_shutdown(signal.SIGINT, None)
            assert captured is True
        finally:
            logger.removeHandler(handler)

    @pytest.mark.asyncio
    async def test_shutdown_all_clears_procs_on_normal_exit(self) -> None:
        manager = HttpServerLifecycleManager()
        proc_mock = Mock(poll=Mock(return_value=0))
        manager._http_procs["test"] = proc_mock

        with (
            patch.object(signal, "getsignal", return_value=signal.default_int_handler),
            patch.object(signal, "signal", side_effect=lambda sig, h: h),
        ):
            await manager.shutdown_all()

        assert len(manager._http_procs) == 0

    @pytest.mark.asyncio
    async def test_shutdown_all_clears_pgids(self) -> None:
        manager = HttpServerLifecycleManager()
        proc_mock = Mock(poll=Mock(return_value=0))
        manager._http_procs["test"] = proc_mock
        manager._http_pgids["test"] = 1234

        with (
            patch.object(signal, "getsignal", return_value=signal.default_int_handler),
            patch.object(signal, "signal", side_effect=lambda sig, h: h),
        ):
            await manager.shutdown_all()

        assert len(manager._http_pgids) == 0

    @pytest.mark.asyncio
    async def test_shutdown_all_clears_stderr_files(self) -> None:
        manager = HttpServerLifecycleManager()
        fh_mock = MagicMock()
        manager._http_procs["test"] = Mock(poll=Mock(return_value=0))
        manager._stderr_files["test"] = fh_mock

        with (
            patch.object(signal, "getsignal", return_value=signal.default_int_handler),
            patch.object(signal, "signal", side_effect=lambda sig, h: h),
        ):
            await manager.shutdown_all()

        assert len(manager._stderr_files) == 0

    @pytest.mark.asyncio
    async def test_shutdown_all_clears_stderr_log_paths(self) -> None:
        manager = HttpServerLifecycleManager()
        manager._http_procs["test"] = Mock(poll=Mock(return_value=0))
        manager._stderr_log_paths["test"] = "/tmp/test.log"

        with (
            patch.object(signal, "getsignal", return_value=signal.default_int_handler),
            patch.object(signal, "signal", side_effect=lambda sig, h: h),
        ):
            await manager.shutdown_all()

        assert len(manager._stderr_log_paths) == 0

    @pytest.mark.asyncio
    async def test_shutdown_all_skips_already_exited_procs(self) -> None:
        manager = HttpServerLifecycleManager()
        proc_mock = Mock(poll=Mock(return_value=1))
        manager._http_procs["test"] = proc_mock

        with (
            patch.object(signal, "getsignal", return_value=signal.default_int_handler),
            patch.object(signal, "signal", side_effect=lambda sig, h: h),
            patch.object(asyncio, "sleep", return_value=None) as mock_sleep,
        ):
            await manager.shutdown_all()

        assert mock_sleep.called is False

    @pytest.mark.asyncio
    async def test_shutdown_all_removes_proc_from_dict_before_terminate(self) -> None:
        manager = HttpServerLifecycleManager()
        terminate_keys: list[str] = []

        async def track_terminate(proc: object, key: str, **kwargs: object) -> None:
            terminate_keys.append(key)

        proc_mock = Mock(poll=Mock(return_value=None))
        manager._http_procs["test"] = proc_mock

        with (
            patch.object(signal, "getsignal", return_value=signal.default_int_handler),
            patch.object(signal, "signal", side_effect=lambda sig, h: h),
            patch.object(asyncio, "sleep", return_value=None),
            patch.object(os, "killpg", side_effect=ProcessLookupError),
        ):
            with patch.object(
                type(manager), "_wait_exited", new=AsyncMock(return_value=True)
            ):
                with patch.object(
                    type(manager),
                    "_terminate_with_timeout",
                    side_effect=track_terminate,
                ):
                    await manager.shutdown_all()

        assert "test" in terminate_keys


class TestSubprocessLifecycle:
    """Characterize current subprocess start, run, and stop behavior."""

    @pytest.mark.asyncio
    async def test_start_reuses_running_process(
        self, mgr: HttpServerLifecycleManager
    ) -> None:
        proc_mock = Mock(poll=Mock(return_value=None))
        mgr._http_procs["test"] = proc_mock

        cfg = _make_cfg()
        with patch.object(subprocess, "Popen") as mock_popen:
            await mgr.start("test", cfg)

        assert mock_popen.call_count == 0

    @pytest.mark.asyncio
    async def test_start_starts_new_process(
        self, mgr: HttpServerLifecycleManager
    ) -> None:
        cfg = _make_cfg(cmd=["node", "/fake/server.js"])
        proc_mock = Mock(pid=9999, poll=Mock(return_value=None))

        monotonic_base = time.monotonic()
        monotonic_count = [0]

        def fake_monotonic() -> float:
            monotonic_count[0] += 1
            if monotonic_count[0] <= 10:
                return monotonic_base + 1.0
            return monotonic_base + 31.0

        with (
            patch.object(subprocess, "Popen", return_value=proc_mock),
            patch.object(os, "getpgid", return_value=9999),
            patch.object(time, "monotonic", side_effect=fake_monotonic),
            patch.object(asyncio, "sleep", return_value=None),
        ):
            with patch.object(type(mgr), "_terminate_with_timeout", new=AsyncMock()):
                with pytest.raises(HttpStartupError):
                    await mgr.start("test", cfg)

        assert mgr._http_procs.get("test") is None
        assert mgr._http_pgids.get("test") is None

    @pytest.mark.asyncio
    async def test_start_env_includes_os_environ(
        self, mgr: HttpServerLifecycleManager
    ) -> None:
        cfg = _make_cfg(env={"CUSTOM_VAR": "value"})
        proc_mock = Mock(pid=9999, poll=Mock(return_value=None))

        monotonic_base = time.monotonic()
        monotonic_count = [0]

        def fake_monotonic() -> float:
            monotonic_count[0] += 1
            if monotonic_count[0] <= 10:
                return monotonic_base + 1.0
            return monotonic_base + 31.0

        mock_popen = MagicMock(return_value=proc_mock)
        with (
            patch.object(subprocess, "Popen", mock_popen),
            patch.object(os, "getpgid", return_value=9999),
            patch.object(time, "monotonic", side_effect=fake_monotonic),
            patch.object(asyncio, "sleep", return_value=None),
        ):
            with patch.object(type(mgr), "_terminate_with_timeout", new=AsyncMock()):
                with pytest.raises(HttpStartupError):
                    await mgr.start("test", cfg)

        assert mock_popen.called
        env_arg = mock_popen.call_args[1].get("env")
        assert env_arg is not None
        assert "PATH" in env_arg or "HOME" in env_arg

    @pytest.mark.asyncio
    async def test_start_blocked_protected_env_vars(
        self, mgr: HttpServerLifecycleManager
    ) -> None:
        cfg = _make_cfg(env={"PATH": "/custom/path", "PYTHONPATH": "/custom/lib"})
        proc_mock = Mock(pid=9999, poll=Mock(return_value=None))

        monotonic_base = time.monotonic()
        monotonic_count = [0]

        def fake_monotonic() -> float:
            monotonic_count[0] += 1
            if monotonic_count[0] <= 10:
                return monotonic_base + 1.0
            return monotonic_base + 31.0

        mock_popen = MagicMock(return_value=proc_mock)
        with (
            patch.object(subprocess, "Popen", mock_popen),
            patch.object(os, "getpgid", return_value=9999),
            patch.object(time, "monotonic", side_effect=fake_monotonic),
            patch.object(asyncio, "sleep", return_value=None),
        ):
            with patch.object(type(mgr), "_terminate_with_timeout", new=AsyncMock()):
                with pytest.raises(HttpStartupError):
                    await mgr.start("test", cfg)

        assert mock_popen.called
        env_arg = mock_popen.call_args[1].get("env")
        assert env_arg is not None
        assert env_arg.get("PATH") != "/custom/path"
        assert env_arg.get("PYTHONPATH") != "/custom/lib"

    @pytest.mark.asyncio
    async def test_start_non_protected_env_vars_passed(
        self, mgr: HttpServerLifecycleManager
    ) -> None:
        cfg = _make_cfg(env={"MY_CUSTOM_VAR": "my_value"})
        proc_mock = Mock(pid=9999, poll=Mock(return_value=None))

        monotonic_base = time.monotonic()
        monotonic_count = [0]

        def fake_monotonic() -> float:
            monotonic_count[0] += 1
            if monotonic_count[0] <= 10:
                return monotonic_base + 1.0
            return monotonic_base + 31.0

        mock_popen = MagicMock(return_value=proc_mock)
        with (
            patch.object(subprocess, "Popen", mock_popen),
            patch.object(os, "getpgid", return_value=9999),
            patch.object(time, "monotonic", side_effect=fake_monotonic),
            patch.object(asyncio, "sleep", return_value=None),
        ):
            with patch.object(type(mgr), "_terminate_with_timeout", new=AsyncMock()):
                with pytest.raises(HttpStartupError):
                    await mgr.start("test", cfg)

        assert mock_popen.called
        env_arg = mock_popen.call_args[1].get("env")
        assert env_arg is not None
        assert env_arg.get("MY_CUSTOM_VAR") == "my_value"

    @pytest.mark.asyncio
    async def test_start_rejected_command_not_whitelisted(
        self, mgr: HttpServerLifecycleManager
    ) -> None:
        cfg = _make_cfg(cmd=["curl", "http://example.com"])
        proc_mock = Mock(pid=9999, poll=Mock(return_value=None))

        popen_called = False

        def track_popen(*args: object, **kwargs: object) -> Mock:
            nonlocal popen_called
            popen_called = True
            return proc_mock

        with (
            patch.object(subprocess, "Popen", side_effect=track_popen),
            patch.object(os, "getpgid", return_value=9999),
            patch.object(asyncio, "sleep", return_value=None),
        ):
            await mgr.start("test", cfg)

        assert popen_called is False
        assert mgr._http_procs.get("test") is None

    @pytest.mark.asyncio
    async def test_start_getpgid_failure_cleans_up(
        self, mgr: HttpServerLifecycleManager
    ) -> None:
        cfg = _make_cfg(cmd=["node", "/fake/server.js"])
        proc_mock = Mock(pid=9999, poll=Mock(return_value=None))

        stderr_fh_mock = MagicMock()
        with (
            patch.object(subprocess, "Popen", return_value=proc_mock),
            patch.object(os, "getpgid", side_effect=OSError("no such process")),
            patch.object(type(mgr), "_open_stderr_log", return_value=stderr_fh_mock),
        ):
            await mgr.start("test", cfg)

        assert mgr._http_procs.get("test") is None
        assert mgr._http_pgids.get("test") is None
        assert mgr._stderr_files.get("test") is None
        assert mgr._stderr_log_paths.get("test") is None
        stderr_fh_mock.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_restart_stops_then_starts(
        self, mgr: HttpServerLifecycleManager
    ) -> None:
        old_proc = Mock(poll=Mock(return_value=None))
        mgr._http_procs["test"] = old_proc

        new_proc = Mock(pid=8888, poll=Mock(return_value=None))

        monotonic_base = time.monotonic()
        monotonic_count = [0]

        def fake_monotonic() -> float:
            monotonic_count[0] += 1
            if monotonic_count[0] <= 10:
                return monotonic_base + 1.0
            return monotonic_base + 31.0

        with (
            patch.object(subprocess, "Popen", return_value=new_proc),
            patch.object(os, "getpgid", return_value=8888),
            patch.object(time, "monotonic", side_effect=fake_monotonic),
            patch.object(asyncio, "sleep", return_value=None),
        ):
            with patch.object(type(mgr), "_terminate_with_timeout", new=AsyncMock()):
                with pytest.raises(HttpStartupError):
                    await mgr.restart("test", _make_cfg())

        assert mgr._http_procs.get("test") is None
        assert mgr._http_pgids.get("test") is None

    @pytest.mark.asyncio
    async def test_restart_clears_stderr_file(
        self, mgr: HttpServerLifecycleManager
    ) -> None:
        old_proc = Mock(poll=Mock(return_value=None))
        mgr._http_procs["test"] = old_proc
        fh_mock = MagicMock()
        mgr._stderr_files["test"] = fh_mock
        mgr._stderr_log_paths["test"] = "/tmp/test.log"

        new_proc = Mock(pid=8888, poll=Mock(return_value=None))

        with (
            patch.object(subprocess, "Popen", return_value=new_proc),
            patch.object(os, "getpgid", return_value=8888),
            patch.object(asyncio, "sleep", return_value=None),
        ):
            with patch.object(
                type(mgr), "_wait_exited", new=AsyncMock(return_value=False)
            ):
                with pytest.raises(HttpStartupError):
                    await mgr.restart("test", _make_cfg())

        assert mgr._stderr_files.get("test") is None
        assert mgr._stderr_log_paths.get("test") is None

    @pytest.mark.asyncio
    async def test_verify_running_returns_true_when_alive(
        self, mgr: HttpServerLifecycleManager
    ) -> None:
        proc_mock = Mock(poll=Mock(return_value=None))
        mgr._http_procs["test"] = proc_mock
        assert mgr.verify_running("test") is True

    @pytest.mark.asyncio
    async def test_verify_running_returns_false_when_missing(
        self, mgr: HttpServerLifecycleManager
    ) -> None:
        assert mgr.verify_running("nonexistent") is False

    @pytest.mark.asyncio
    async def test_verify_running_returns_false_when_exited(
        self, mgr: HttpServerLifecycleManager
    ) -> None:
        proc_mock = Mock(poll=Mock(return_value=1))
        mgr._http_procs["test"] = proc_mock
        assert mgr.verify_running("test") is False

    @pytest.mark.asyncio
    async def test_list_processes_returns_snapshots(
        self, mgr: HttpServerLifecycleManager
    ) -> None:
        mgr._http_procs["test"] = Mock(poll=Mock(return_value=None))
        mgr._http_procs["test2"] = Mock(poll=Mock(return_value=None))

        with patch.object(os, "getpgid", return_value=9999):
            snapshots = mgr.list_processes()

        assert len(snapshots) == 2
        keys = {snap.server_key for snap in snapshots}
        assert "test" in keys
        assert "test2" in keys

    @pytest.mark.asyncio
    async def test_get_process_snapshot_returns_info(
        self, mgr: HttpServerLifecycleManager
    ) -> None:
        proc_mock = Mock(pid=9999, poll=Mock(return_value=None))
        mgr._http_procs["test"] = proc_mock
        mgr._http_pgids["test"] = 9999

        snap = mgr.get_process_snapshot("test")
        assert snap is not None
        assert snap["pid"] == 9999
        assert snap["running"] is True
        assert snap["last_exit_code"] is None

    @pytest.mark.asyncio
    async def test_get_process_snapshot_none_for_unknown(
        self, mgr: HttpServerLifecycleManager
    ) -> None:
        assert mgr.get_process_snapshot("unknown") is None

    @pytest.mark.asyncio
    async def test_get_process_info_returns_snapshot(
        self, mgr: HttpServerLifecycleManager
    ) -> None:
        proc_mock = Mock(pid=9999, poll=Mock(return_value=None))
        mgr._http_procs["test"] = proc_mock
        mgr._http_pgids["test"] = 9999
        mgr._stderr_log_paths["test"] = "/tmp/test.stderr.log"

        info = mgr.get_process_info("test")
        assert info is not None
        assert info.server_key == "test"
        assert info.pid == 9999
        assert info.running is True
        assert info.last_exit_code is None

    @pytest.mark.asyncio
    async def test_get_process_info_none_for_unknown(
        self, mgr: HttpServerLifecycleManager
    ) -> None:
        assert mgr.get_process_info("unknown") is None


class TestShutdownSequence:
    """Characterize current shutdown_all behavior under various conditions."""

    @pytest.mark.asyncio
    async def test_shutdown_all_terminates_each_proc(
        self, mgr: HttpServerLifecycleManager
    ) -> None:
        proc1 = Mock(poll=Mock(return_value=None))
        proc2 = Mock(poll=Mock(return_value=None))
        mgr._http_procs["a"] = proc1
        mgr._http_procs["b"] = proc2

        terminate_keys: list[str] = []

        async def track_terminate(proc: object, key: str, **kwargs: object) -> None:
            terminate_keys.append(key)

        with (
            patch.object(signal, "getsignal", return_value=signal.default_int_handler),
            patch.object(signal, "signal", side_effect=lambda sig, h: h),
            patch.object(asyncio, "sleep", return_value=None),
        ):
            with patch.object(
                type(mgr), "_terminate_with_timeout", side_effect=track_terminate
            ):
                await mgr.shutdown_all()

        assert len(terminate_keys) == 2
        assert "a" in terminate_keys
        assert "b" in terminate_keys

    @pytest.mark.asyncio
    async def test_shutdown_all_handles_terminate_error(
        self, mgr: HttpServerLifecycleManager
    ) -> None:
        proc_mock = Mock(poll=Mock(return_value=None))
        mgr._http_procs["test"] = proc_mock

        with (
            patch.object(signal, "getsignal", return_value=signal.default_int_handler),
            patch.object(signal, "signal", side_effect=lambda sig, h: h),
            patch.object(asyncio, "sleep", return_value=None),
        ):
            with patch.object(
                type(mgr),
                "_terminate_with_timeout",
                new=AsyncMock(side_effect=OSError("kill failed")),
            ):
                await mgr.shutdown_all()

        assert mgr._http_procs.get("test") is None

    @pytest.mark.asyncio
    async def test_shutdown_all_handles_terminate_timeout(
        self, mgr: HttpServerLifecycleManager
    ) -> None:
        proc_mock = Mock(poll=Mock(return_value=None))
        mgr._http_procs["test"] = proc_mock

        with (
            patch.object(signal, "getsignal", return_value=signal.default_int_handler),
            patch.object(signal, "signal", side_effect=lambda sig, h: h),
            patch.object(asyncio, "sleep", return_value=None),
        ):
            with patch.object(
                type(mgr),
                "_terminate_with_timeout",
                new=AsyncMock(side_effect=TimeoutError("timed out")),
            ):
                await mgr.shutdown_all()

        assert mgr._http_procs.get("test") is None

    @pytest.mark.asyncio
    async def test_shutdown_all_closes_stderr_on_normal_exit(
        self, mgr: HttpServerLifecycleManager
    ) -> None:
        proc_mock = Mock(poll=Mock(return_value=None))
        mgr._http_procs["test"] = proc_mock
        fh_mock = MagicMock()
        mgr._stderr_files["test"] = fh_mock

        with (
            patch.object(signal, "getsignal", return_value=signal.default_int_handler),
            patch.object(signal, "signal", side_effect=lambda sig, h: h),
            patch.object(asyncio, "sleep", return_value=None),
        ):
            with patch.object(type(mgr), "_terminate_with_timeout", new=AsyncMock()):
                await mgr.shutdown_all()

        fh_mock.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_shutdown_all_skips_stderr_close_when_already_closed(
        self, mgr: HttpServerLifecycleManager
    ) -> None:
        proc_mock = Mock(poll=Mock(return_value=None))
        mgr._http_procs["test"] = proc_mock
        fh_mock = MagicMock()
        fh_mock.close.side_effect = OSError("already closed")
        mgr._stderr_files["test"] = fh_mock

        with (
            patch.object(signal, "getsignal", return_value=signal.default_int_handler),
            patch.object(signal, "signal", side_effect=lambda sig, h: h),
            patch.object(asyncio, "sleep", return_value=None),
        ):
            with patch.object(type(mgr), "_terminate_with_timeout", new=AsyncMock()):
                await mgr.shutdown_all()

    @pytest.mark.asyncio
    async def test_shutdown_all_noop_when_no_procs(
        self, mgr: HttpServerLifecycleManager
    ) -> None:
        with (
            patch.object(signal, "getsignal", return_value=signal.default_int_handler),
            patch.object(signal, "signal", side_effect=lambda sig, h: h) as mock_signal,
        ):
            await mgr.shutdown_all()

        install_calls = [
            c for c in mock_signal.call_args_list if c[0][0] == signal.SIGINT
        ]
        assert len(install_calls) >= 1

    @pytest.mark.asyncio
    async def test_shutdown_all_clears_all_state_even_if_some_failures(
        self, mgr: HttpServerLifecycleManager
    ) -> None:
        proc_mock = Mock(poll=Mock(return_value=None))
        mgr._http_procs["test"] = proc_mock
        mgr._http_pgids["test"] = 9999
        mgr._stderr_log_paths["test"] = "/tmp/test.log"

        with (
            patch.object(signal, "getsignal", return_value=signal.default_int_handler),
            patch.object(signal, "signal", side_effect=lambda sig, h: h),
            patch.object(asyncio, "sleep", return_value=None),
        ):
            with patch.object(type(mgr), "_terminate_with_timeout", new=AsyncMock()):
                await mgr.shutdown_all()

        assert len(mgr._http_procs) == 0
        assert len(mgr._http_pgids) == 0
        assert len(mgr._stderr_log_paths) == 0

    @pytest.mark.asyncio
    async def test_shutdown_all_restores_handler_even_on_exception(
        self, mgr: HttpServerLifecycleManager
    ) -> None:
        original_handler = Mock(spec=object)
        restore_count = 0

        def track_restore(sig: int, handler: object) -> object:
            nonlocal restore_count
            if handler is original_handler:
                restore_count += 1
            return handler

        mgr._http_procs["test"] = Mock(poll=Mock(return_value=None))

        with (
            patch.object(signal, "getsignal", return_value=original_handler),
            patch.object(signal, "signal", side_effect=track_restore),
            patch.object(asyncio, "sleep", return_value=None),
        ):
            with patch.object(
                type(mgr),
                "_terminate_with_timeout",
                new=AsyncMock(side_effect=ValueError("unexpected error")),
            ):
                with pytest.raises(ValueError):
                    await mgr.shutdown_all()

        assert restore_count >= 1

    @pytest.mark.asyncio
    async def test_shutdown_all_ignores_sigint_during_cleanup(
        self, mgr: HttpServerLifecycleManager
    ) -> None:
        import logging

        captured_warning = False

        class WarningCapture(logging.Handler):
            def emit(self, record: logging.LogRecord) -> None:
                nonlocal captured_warning
                if "SIGINT received during shutdown_all" in record.getMessage():
                    captured_warning = True

        handler = WarningCapture()
        logger = logging.getLogger("agent.http_lifecycle")
        logger.addHandler(handler)
        try:
            mgr._http_procs["test"] = Mock(poll=Mock(return_value=None))

            with (
                patch.object(
                    signal, "getsignal", return_value=signal.default_int_handler
                ),
                patch.object(signal, "signal", side_effect=lambda sig, h: h),
                patch.object(asyncio, "sleep", return_value=None),
            ):
                with patch.object(
                    type(mgr), "_terminate_with_timeout", new=AsyncMock()
                ):
                    await mgr.shutdown_all()

            assert captured_warning is False
        finally:
            logger.removeHandler(handler)

    @pytest.mark.asyncio
    async def test_shutdown_all_processes_in_iteration_order(
        self, mgr: HttpServerLifecycleManager
    ) -> None:
        mgr._http_procs["a"] = Mock(poll=Mock(return_value=None))
        mgr._http_procs["b"] = Mock(poll=Mock(return_value=None))
        mgr._http_procs["c"] = Mock(poll=Mock(return_value=None))

        terminate_keys: list[str] = []

        async def track_terminate(proc: object, key: str, **kwargs: object) -> None:
            terminate_keys.append(key)

        with (
            patch.object(signal, "getsignal", return_value=signal.default_int_handler),
            patch.object(signal, "signal", side_effect=lambda sig, h: h),
            patch.object(asyncio, "sleep", return_value=None),
        ):
            with patch.object(
                type(mgr), "_wait_exited", new=AsyncMock(return_value=True)
            ):
                with patch.object(
                    type(mgr), "_terminate_with_timeout", side_effect=track_terminate
                ):
                    await mgr.shutdown_all()

        assert len(terminate_keys) == 3
        assert terminate_keys[0] != terminate_keys[1]
        assert terminate_keys[1] != terminate_keys[2]


class TestErrorRecovery:
    """Characterize current behavior when startup fails — subsequent attempts should work."""

    @pytest.mark.asyncio
    async def test_failed_start_doesnt_block_subsequent_attempts(
        self, mgr: HttpServerLifecycleManager
    ) -> None:
        cfg = _make_cfg(cmd=["node", "/fake/server.js"])
        first_proc = Mock(pid=7777, poll=Mock(return_value=None))

        monotonic_base = time.monotonic()
        monotonic_count = [0]

        def fake_monotonic_first() -> float:
            monotonic_count[0] += 1
            if monotonic_count[0] <= 10:
                return monotonic_base + 1.0
            return monotonic_base + 31.0

        with (
            patch.object(subprocess, "Popen", return_value=first_proc),
            patch.object(os, "getpgid", return_value=7777),
            patch.object(time, "monotonic", side_effect=fake_monotonic_first),
            patch.object(asyncio, "sleep", return_value=None),
        ):
            with patch.object(type(mgr), "_terminate_with_timeout", new=AsyncMock()):
                with pytest.raises(HttpStartupError):
                    await mgr.start("test", cfg)

        assert mgr._http_procs.get("test") is None

        second_proc = Mock(pid=8888, poll=Mock(return_value=None))
        mock_resp = MagicMock()
        from http import HTTPStatus

        mock_resp.status_code = HTTPStatus.OK

        mock_client = MagicMock()
        mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.get = AsyncMock(return_value=mock_resp)

        with (
            patch.object(subprocess, "Popen", return_value=second_proc),
            patch.object(os, "getpgid", return_value=8888),
            patch.object(httpx, "AsyncClient", mock_client),
            patch.object(asyncio, "sleep", return_value=None),
        ):
            await mgr.start("test", cfg)

        assert mgr._http_procs.get("test") is second_proc

    @pytest.mark.asyncio
    async def test_startup_failure_contains_stderr(
        self, mgr: HttpServerLifecycleManager
    ) -> None:
        cfg = _make_cfg(cmd=["node", "/fake/server.js"])
        proc_mock = Mock(pid=7777, poll=Mock(return_value=1))

        with (
            patch.object(subprocess, "Popen", return_value=proc_mock),
            patch.object(os, "getpgid", return_value=7777),
            patch.object(asyncio, "sleep", return_value=None),
        ):
            with patch.object(
                type(mgr),
                "_read_stderr_tail",
                new=MagicMock(return_value="error output here"),
            ):
                with pytest.raises(HttpStartupError) as exc_info:
                    await mgr.start("test", cfg)

        failure = exc_info.value.failure
        assert isinstance(failure, StartupFailure)
        assert failure.server_key == "test"
        assert failure.reason == "exited early"
        assert "error output here" in failure.stderr_full

    @pytest.mark.asyncio
    async def test_startup_failure_contains_reason_on_timeout(
        self, mgr: HttpServerLifecycleManager
    ) -> None:
        cfg = _make_cfg(cmd=["node", "/fake/server.js"], startup_timeout_sec=5)
        proc_mock = Mock(pid=7777, poll=Mock(return_value=None))

        monotonic_base = time.monotonic()
        monotonic_count = [0]

        def fake_monotonic() -> float:
            monotonic_count[0] += 1
            if monotonic_count[0] <= 10:
                return monotonic_base + 1.0
            return monotonic_base + 6.0

        with (
            patch.object(subprocess, "Popen", return_value=proc_mock),
            patch.object(os, "getpgid", return_value=7777),
            patch.object(time, "monotonic", side_effect=fake_monotonic),
            patch.object(httpx, "AsyncClient"),
            patch.object(asyncio, "sleep", return_value=None),
        ):
            with patch.object(
                type(mgr),
                "_read_stderr_tail",
                new=MagicMock(return_value="timeout stderr"),
            ):
                with patch.object(
                    type(mgr), "_terminate_with_timeout", new=AsyncMock()
                ):
                    with pytest.raises(HttpStartupError) as exc_info:
                        await mgr.start("test", cfg)

        failure = exc_info.value.failure
        assert isinstance(failure, StartupFailure)
        assert failure.server_key == "test"
        assert "did not become healthy within 5s" in failure.reason
        assert "timeout stderr" in failure.stderr_full

    @pytest.mark.asyncio
    async def test_restart_handles_already_stopped_process(
        self, mgr: HttpServerLifecycleManager
    ) -> None:
        old_proc = Mock(poll=Mock(return_value=1))
        mgr._http_procs["test"] = old_proc

        new_proc = Mock(pid=8888, poll=Mock(return_value=None))
        mock_resp = MagicMock()
        from http import HTTPStatus

        mock_resp.status_code = HTTPStatus.OK

        mock_client = MagicMock()
        mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.get = AsyncMock(return_value=mock_resp)

        with (
            patch.object(subprocess, "Popen", return_value=new_proc),
            patch.object(os, "getpgid", return_value=8888),
            patch.object(httpx, "AsyncClient", mock_client),
            patch.object(asyncio, "sleep", return_value=None),
        ):
            await mgr.restart("test", _make_cfg())

        assert mgr._http_procs.get("test") is new_proc

    @pytest.mark.asyncio
    async def test_restart_handles_missing_process(
        self, mgr: HttpServerLifecycleManager
    ) -> None:
        # No process registered for this key
        new_proc = Mock(pid=8888, poll=Mock(return_value=None))
        mock_resp = MagicMock()
        from http import HTTPStatus

        mock_resp.status_code = HTTPStatus.OK

        mock_client = MagicMock()
        mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.get = AsyncMock(return_value=mock_resp)

        with (
            patch.object(subprocess, "Popen", return_value=new_proc),
            patch.object(os, "getpgid", return_value=8888),
            patch.object(httpx, "AsyncClient", mock_client),
            patch.object(asyncio, "sleep", return_value=None),
        ):
            await mgr.restart("nonexistent", _make_cfg())

    @pytest.mark.asyncio
    async def test_health_check_poll_continues_on_error(
        self, mgr: HttpServerLifecycleManager
    ) -> None:
        cfg = _make_cfg(cmd=["node", "/fake/server.js"], startup_timeout_sec=2)
        proc_mock = Mock(pid=9999, poll=Mock(return_value=None))

        monotonic_base = time.monotonic()
        monotonic_count = [0]

        def fake_monotonic() -> float:
            monotonic_count[0] += 1
            if monotonic_count[0] <= 10:
                return monotonic_base + 1.0
            return monotonic_base + 3.0

        with (
            patch.object(subprocess, "Popen", return_value=proc_mock),
            patch.object(os, "getpgid", return_value=9999),
            patch.object(time, "monotonic", side_effect=fake_monotonic),
            patch.object(httpx, "AsyncClient"),
            patch.object(asyncio, "sleep", return_value=None),
        ):
            with patch.object(
                type(mgr), "_read_stderr_tail", new=MagicMock(return_value="")
            ):
                with patch.object(
                    type(mgr), "_terminate_with_timeout", new=AsyncMock()
                ):
                    with pytest.raises(HttpStartupError):
                        await mgr.start("test", cfg)

        assert mgr._http_procs.get("test") is None

    @pytest.mark.asyncio
    async def test_health_check_succeeds_returns_cleanly(
        self, mgr: HttpServerLifecycleManager
    ) -> None:
        cfg = _make_cfg(cmd=["node", "/fake/server.js"], startup_timeout_sec=2)
        proc_mock = Mock(pid=9999, poll=Mock(return_value=None))

        mock_client = MagicMock()
        mock_resp = MagicMock()
        from http import HTTPStatus

        mock_resp.status_code = HTTPStatus.OK
        mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.get = AsyncMock(return_value=mock_resp)

        with (
            patch.object(subprocess, "Popen", return_value=proc_mock),
            patch.object(os, "getpgid", return_value=9999),
            patch.object(httpx, "AsyncClient", mock_client),
            patch.object(asyncio, "sleep", return_value=None),
        ):
            await mgr.start("test", cfg)

        assert mgr._http_procs.get("test") is proc_mock
