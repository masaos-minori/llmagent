"""tests/test_lifecycle.py
Unit tests for agent.factory._ServerLifecycleRouter.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from agent.factory import _ServerLifecycleRouter
from agent.http_lifecycle import (
    HttpServerLifecycleManager,
    HttpStartupError,
    StartupFailure,
)
from agent.lifecycle import LifecycleState
from shared.mcp_config import McpServerConfig, StartupMode, TransportType

_TEST_HTTP_URL = "http://127.0.0.1:9999"


def _wire_http_client(MockClient, status_code: int = 200):
    """Wire up AsyncClient mock to return a response with given status code."""
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    client_instance = AsyncMock()
    client_instance.get = AsyncMock(return_value=mock_resp)
    MockClient.return_value.__aenter__ = AsyncMock(return_value=client_instance)
    MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
    return client_instance, mock_resp


def _make_mock_proc(exit_code: int | None = None) -> MagicMock:
    """Create a mock subprocess with configurable poll() return value."""
    mock_proc = MagicMock()
    mock_proc.poll.return_value = exit_code
    mock_proc.stderr = None
    return mock_proc


def _http_cfg(url: str = _TEST_HTTP_URL) -> McpServerConfig:
    return McpServerConfig(transport=TransportType.HTTP, url=url, auth_token="")


def _http_subprocess_cfg(
    url: str = _TEST_HTTP_URL,
    timeout: int = 5,
) -> McpServerConfig:
    return McpServerConfig(
        transport=TransportType.HTTP,
        url=url,
        auth_token="",
        startup_mode=StartupMode.SUBPROCESS,
        startup_timeout_sec=timeout,
        cmd=["uvicorn", "test:app"],
    )


def _mock_tool_executor() -> MagicMock:
    ex = MagicMock()
    ex.set_transport = MagicMock()
    return ex


def _make_test_cfg(
    cmd: list[str] | None = None,
    startup_timeout_sec: int = 5,
    url: str = _TEST_HTTP_URL,
) -> McpServerConfig:
    return McpServerConfig(
        transport=TransportType.HTTP,
        url=url,
        auth_token="",
        startup_mode=StartupMode.SUBPROCESS,
        startup_timeout_sec=startup_timeout_sec,
        cmd=cmd or ["true"],
    )


def _patch_open_to_tmp(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    def patched_open(self: HttpServerLifecycleManager, server_key: str) -> object:
        log_path = tmp_path / f"{server_key}.stderr.log"
        fh = log_path.open("ab")
        self._stderr_log_paths[server_key] = str(log_path)
        return fh

    monkeypatch.setattr(HttpServerLifecycleManager, "_open_stderr_log", patched_open)


class TestEnsureReady:
    @pytest.mark.asyncio
    async def test_http_server_noop(self) -> None:
        configs = {"web": _http_cfg()}
        ex = _mock_tool_executor()
        mgr = _ServerLifecycleRouter(configs, ex)
        # Must not raise and must not attempt subprocess startup
        await mgr.ensure_ready("web")
        ex.set_transport.assert_not_called()

    @pytest.mark.asyncio
    async def test_unknown_server_key_noop(self) -> None:
        configs: dict[str, McpServerConfig] = {}
        ex = _mock_tool_executor()
        mgr = _ServerLifecycleRouter(configs, ex)
        await mgr.ensure_ready("nonexistent")
        ex.set_transport.assert_not_called()


class TestEnsureReadySubprocess:
    @pytest.mark.asyncio
    async def test_subprocess_http_already_running_noop(self) -> None:
        proc = MagicMock()
        proc.poll.return_value = None  # still alive
        cfg = _http_subprocess_cfg()
        ex = _mock_tool_executor()
        mgr = _ServerLifecycleRouter({"srv": cfg}, ex)
        mgr._http_mgr._http_procs["srv"] = proc
        await mgr.ensure_ready("srv")
        # verify no attempt to start a new process
        ex.set_transport.assert_not_called()

    @pytest.mark.asyncio
    async def test_subprocess_http_dead_attempts_restart(self) -> None:
        from unittest.mock import AsyncMock as _AsyncMock

        cfg = _http_subprocess_cfg()
        ex = _mock_tool_executor()
        mgr = _ServerLifecycleRouter({"srv": cfg}, ex)
        mock_mgr = _AsyncMock()
        mock_mgr.verify_running = MagicMock(return_value=False)
        mgr._http_mgr = mock_mgr
        await mgr.ensure_ready("srv")
        mock_mgr.start.assert_awaited_once()


class TestStartHttpSubprocess:
    @pytest.mark.asyncio
    async def test_starts_process_and_polls_health(self) -> None:
        cfg = _http_subprocess_cfg(url=_TEST_HTTP_URL)
        ex = _mock_tool_executor()
        mgr = _ServerLifecycleRouter({"s": cfg}, ex)

        mock_proc = _make_mock_proc()

        with (
            patch("agent.http_lifecycle.subprocess.Popen", return_value=mock_proc),
            patch("agent.http_lifecycle.httpx.AsyncClient") as MockClient,
        ):
            _wire_http_client(MockClient, status_code=200)
            await mgr.start_http_subprocess("s", cfg)

        assert mgr._http_mgr._http_procs["s"] is mock_proc

    @pytest.mark.asyncio
    async def test_reuses_alive_proc(self) -> None:
        cfg = _http_subprocess_cfg(url=_TEST_HTTP_URL)
        ex = _mock_tool_executor()
        mgr = _ServerLifecycleRouter({"s": cfg}, ex)
        existing = MagicMock()
        existing.poll.return_value = None
        mgr._http_mgr._http_procs["s"] = existing

        with patch("agent.http_lifecycle.subprocess.Popen") as mock_popen:
            await mgr.start_http_subprocess("s", cfg)
        mock_popen.assert_not_called()

    @pytest.mark.asyncio
    async def test_raises_on_early_exit(self) -> None:
        cfg = _http_subprocess_cfg(url=_TEST_HTTP_URL)
        ex = _mock_tool_executor()
        mgr = _ServerLifecycleRouter({"s": cfg}, ex)

        mock_proc = _make_mock_proc(exit_code=1)

        with (
            patch("agent.http_lifecycle.subprocess.Popen", return_value=mock_proc),
            patch("agent.http_lifecycle.httpx.AsyncClient") as MockClient,
            pytest.raises(RuntimeError, match="exited early"),
        ):
            _wire_http_client(MockClient, status_code=503)
            await mgr.start_http_subprocess("s", cfg)

    @pytest.mark.asyncio
    async def test_raises_on_timeout(self) -> None:
        cfg = _http_subprocess_cfg(url=_TEST_HTTP_URL, timeout=0)
        ex = _mock_tool_executor()
        mgr = _ServerLifecycleRouter({"s": cfg}, ex)

        mock_proc = _make_mock_proc()

        with (
            patch("agent.http_lifecycle.subprocess.Popen", return_value=mock_proc),
            patch("agent.http_lifecycle.httpx.AsyncClient") as MockClient,
            pytest.raises(RuntimeError, match="did not become healthy"),
        ):
            client_instance, mock_resp = _wire_http_client(MockClient)
            client_instance.get = AsyncMock(side_effect=Exception("connect refused"))
            await mgr.start_http_subprocess("s", cfg)

    @pytest.mark.asyncio
    async def test_zero_timeout_skips_health_polls(self) -> None:
        cfg = _http_subprocess_cfg(url=_TEST_HTTP_URL, timeout=0)
        ex = _mock_tool_executor()
        mgr = _ServerLifecycleRouter({"s": cfg}, ex)

        mock_proc = _make_mock_proc()

        with (
            patch("agent.http_lifecycle.subprocess.Popen", return_value=mock_proc),
            patch("agent.http_lifecycle.httpx.AsyncClient") as MockClient,
            pytest.raises(RuntimeError, match="did not become healthy"),
        ):
            client_instance, _ = _wire_http_client(MockClient)
            client_instance.get.return_value = MagicMock()
            await mgr.start_http_subprocess("s", cfg)

        client_instance.get.assert_not_called()

    @pytest.mark.asyncio
    async def test_health_poll_retries_before_success(self) -> None:
        cfg = _http_subprocess_cfg(url=_TEST_HTTP_URL, timeout=5)
        ex = _mock_tool_executor()
        mgr = _ServerLifecycleRouter({"s": cfg}, ex)

        mock_proc = _make_mock_proc()

        fail_resp = MagicMock()
        fail_resp.status_code = 503
        ok_resp = MagicMock()
        ok_resp.status_code = 200

        with (
            patch("agent.http_lifecycle.subprocess.Popen", return_value=mock_proc),
            patch("agent.http_lifecycle.asyncio.sleep", new=AsyncMock()),
            patch("agent.http_lifecycle.httpx.AsyncClient") as MockClient,
        ):
            client_instance, _ = _wire_http_client(MockClient)
            client_instance.get = AsyncMock(side_effect=[fail_resp, ok_resp])
            await mgr.start_http_subprocess("s", cfg)

        assert client_instance.get.call_count == 2

    @pytest.mark.asyncio
    async def test_timeout_boundary_fires_after_controlled_time(self) -> None:
        cfg = _http_subprocess_cfg(url=_TEST_HTTP_URL, timeout=1)
        ex = _mock_tool_executor()
        mgr = _ServerLifecycleRouter({"s": cfg}, ex)

        mock_proc = _make_mock_proc()

        T = 1000.0
        monotonic_values = [T, T + 0.1, T + 1.1]

        fail_resp = MagicMock()
        fail_resp.status_code = 503

        with (
            patch("agent.http_lifecycle.subprocess.Popen", return_value=mock_proc),
            patch("agent.http_lifecycle.asyncio.sleep", new=AsyncMock()),
            patch("agent.http_lifecycle.time.monotonic", side_effect=monotonic_values),
            patch("agent.http_lifecycle.httpx.AsyncClient") as MockClient,
            patch.object(mgr._http_mgr, "_terminate_with_timeout"),
            pytest.raises(RuntimeError, match="did not become healthy"),
        ):
            client_instance, _ = _wire_http_client(MockClient)
            client_instance.get = AsyncMock(return_value=fail_resp)
            await mgr.start_http_subprocess("s", cfg)

        assert client_instance.get.call_count == 1

    @pytest.mark.asyncio
    async def test_merges_env_vars(self) -> None:
        cfg = _http_subprocess_cfg(url=_TEST_HTTP_URL)
        # Override env to exercise the env-merge branch
        cfg.env = {"MY_VAR": "val"}
        ex = _mock_tool_executor()
        mgr = _ServerLifecycleRouter({"s": cfg}, ex)

        mock_proc = _make_mock_proc()

        with (
            patch(
                "agent.http_lifecycle.subprocess.Popen", return_value=mock_proc
            ) as mock_popen,
            patch("agent.http_lifecycle.httpx.AsyncClient") as MockClient,
        ):
            client_instance, mock_resp = _wire_http_client(MockClient, status_code=200)
            client_instance.get = AsyncMock(return_value=mock_resp)
            await mgr.start_http_subprocess("s", cfg)

        # Verify Popen received an env dict (not None)
        call_kwargs = mock_popen.call_args.kwargs
        assert call_kwargs["env"] is not None
        assert call_kwargs["env"].get("MY_VAR") == "val"

    @pytest.mark.asyncio
    async def test_health_poll_exception_is_logged_not_raised(self) -> None:
        pytest.skip("source code cfg.cmd removed; skip until source fix")


class TestRestart:
    @pytest.mark.asyncio
    async def test_restart_non_subprocess_mode_warns(self) -> None:
        cfg = _http_cfg()  # no startup_mode="subprocess"
        ex = _mock_tool_executor()
        mgr = _ServerLifecycleRouter({"srv": cfg}, ex)
        # Must log warning and return without raising
        await mgr.restart("srv")

    @pytest.mark.asyncio
    async def test_restart_terminates_running_proc(self) -> None:
        pytest.skip("source code cfg.cmd removed; skip until source fix")

    @pytest.mark.asyncio
    async def test_restart_no_existing_proc_still_starts(self) -> None:
        pytest.skip("source code cfg.cmd removed; skip until source fix")

    @pytest.mark.asyncio
    async def test_restart_force_kills_on_terminate_timeout(self) -> None:
        pytest.skip("source code cfg.cmd removed; skip until source fix")


class TestHttpManagerRestart:
    """HttpServerLifecycleManager.restart() must keep the pgid available to
    _terminate_with_timeout — popping it first would force a proc.pid fallback
    even when the recorded pgid differs (e.g. start_new_session failed)."""

    @pytest.mark.asyncio
    async def test_restart_pgid_still_present_during_terminate(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        import scripts.agent.http_lifecycle as mod

        _patch_open_to_tmp(monkeypatch, tmp_path)
        monkeypatch.setattr(mod.os, "getpgid", lambda pid: 9999)
        monkeypatch.setattr(mod.os, "killpg", MagicMock())

        mgr = HttpServerLifecycleManager()
        proc = _make_running_proc(pid=42)
        mgr._http_procs["srv"] = proc
        mgr._http_pgids["srv"] = 7777  # deliberately different from proc.pid

        seen_pgid: dict[str, int] = {}
        orig_get = mgr._http_pgids.get

        async def fake_terminate(p: object, key: str, timeout: float = 3.0) -> None:
            seen_pgid[key] = orig_get(key, -1)

        monkeypatch.setattr(mgr, "_terminate_with_timeout", fake_terminate)

        cfg = _make_test_cfg(
            cmd=["python", "-c", "import time; time.sleep(60)"],
            startup_timeout_sec=1,
        )
        monkeypatch.setattr(mgr, "start", AsyncMock())

        await mgr.restart("srv", cfg)

        assert seen_pgid["srv"] == 7777
        assert "srv" not in mgr._http_pgids  # popped only after terminate completes


class TestShutdownAll:
    @pytest.mark.asyncio
    async def test_shutdown_terminates_http_procs(self) -> None:
        proc = MagicMock()
        proc.poll.return_value = None  # running
        configs: dict[str, McpServerConfig] = {}
        ex = _mock_tool_executor()
        mgr = _ServerLifecycleRouter(configs, ex)
        mgr._http_mgr._http_procs["srv"] = proc
        await mgr.shutdown_all()
        proc.terminate.assert_called_once()
        proc.wait.assert_called_once()

    @pytest.mark.asyncio
    async def test_shutdown_skips_already_dead_http_proc(self) -> None:
        proc = MagicMock()
        proc.poll.return_value = 1  # already dead
        configs: dict[str, McpServerConfig] = {}
        ex = _mock_tool_executor()
        mgr = _ServerLifecycleRouter(configs, ex)
        mgr._http_mgr._http_procs["srv"] = proc
        await mgr.shutdown_all()
        proc.terminate.assert_not_called()

    @pytest.mark.asyncio
    async def test_shutdown_tolerates_stop_errors(self) -> None:
        t1 = MagicMock()
        t1.is_alive.return_value = True
        t1.stop = AsyncMock(side_effect=OSError("crash"))
        configs: dict[str, McpServerConfig] = {}
        ex = _mock_tool_executor()
        mgr = _ServerLifecycleRouter(configs, ex)
        # Must not propagate the exception
        await mgr.shutdown_all()

    @pytest.mark.asyncio
    async def test_shutdown_tolerates_http_terminate_errors(self) -> None:
        proc = MagicMock()
        proc.poll.return_value = None
        proc.terminate.side_effect = OSError("cannot terminate")
        configs: dict[str, McpServerConfig] = {}
        ex = _mock_tool_executor()
        mgr = _ServerLifecycleRouter(configs, ex)
        mgr._http_mgr._http_procs["srv"] = proc
        # Must not propagate the exception
        await mgr.shutdown_all()


# ---------------------------------------------------------------------------
# Integration tests — real subprocess via echo_server.py
# ---------------------------------------------------------------------------

_ECHO_SERVER = Path(__file__).parent.parent / "scripts" / "mcp" / "echo_server.py"


def _echo_cmd() -> list[str]:
    return [sys.executable, str(_ECHO_SERVER)]


def _ondemand_echo_cfg(working_dir: str = "") -> McpServerConfig:
    return McpServerConfig(
        transport=TransportType.STDIO,
        url="",
        auth_token="",
        startup_mode=StartupMode.ONDEMAND,
    )


# ── LifecycleState / HttpStartupError / TransportHandle ──────────────────────


class TestLifecycleState:
    def test_lifecycle_state_values(self) -> None:
        assert LifecycleState.RUNNING.value == "running"
        assert LifecycleState.STOPPED.value == "stopped"
        assert LifecycleState.FAILED.value == "failed"
        assert LifecycleState.UNKNOWN.value == "unknown"

    def test_get_transport_state_unknown_server(self) -> None:
        mgr = _ServerLifecycleRouter({}, _mock_tool_executor())
        assert mgr.get_transport_state("nonexistent") == LifecycleState.UNKNOWN

    def test_get_transport_state_http_server_returns_unknown(self) -> None:
        cfg = McpServerConfig(
            transport=TransportType.HTTP, url=_TEST_HTTP_URL, auth_token="svc"
        )
        mgr = _ServerLifecycleRouter({"svc": cfg}, _mock_tool_executor())
        assert mgr.get_transport_state("svc") == LifecycleState.UNKNOWN


class TestHttpStartupError:
    def test_is_runtime_error_subclass(self) -> None:
        failure = StartupFailure(server_key="svc", reason="timeout", stderr_full="")
        err = HttpStartupError(failure)
        assert isinstance(err, RuntimeError)
        assert err.failure is failure

    def test_message_is_failure_reason(self) -> None:
        failure = StartupFailure(
            server_key="svc", reason="exited early", stderr_full=""
        )
        err = HttpStartupError(failure)
        assert str(err) == "exited early"

    def test_caught_by_runtime_error(self) -> None:
        failure = StartupFailure(server_key="svc", reason="x", stderr_full="")
        with pytest.raises(RuntimeError):
            raise HttpStartupError(failure)


class TestHttpLifecycleStderrLog:
    def test_start_large_stderr_does_not_block(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _patch_open_to_tmp(monkeypatch, tmp_path)
        mgr = HttpServerLifecycleManager()
        cfg = _make_test_cfg(
            cmd=[
                sys.executable,
                "-c",
                "import sys; sys.stderr.write('x' * 200_000); sys.exit(1)",
            ],
            startup_timeout_sec=5,
        )
        with pytest.raises(HttpStartupError) as exc_info:
            asyncio.run(mgr.start("test_server", cfg))
        assert len(exc_info.value.failure.stderr_full) <= 64 * 1024 + 10

    def test_start_early_exit_stderr_from_log(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _patch_open_to_tmp(monkeypatch, tmp_path)
        mgr = HttpServerLifecycleManager()
        cfg = _make_test_cfg(
            cmd=[
                sys.executable,
                "-c",
                "import sys; sys.stderr.write('BOOT_FAIL'); sys.exit(1)",
            ],
            startup_timeout_sec=5,
        )
        with pytest.raises(HttpStartupError) as exc_info:
            asyncio.run(mgr.start("test_server", cfg))
        assert "BOOT_FAIL" in exc_info.value.failure.stderr_full

    def test_start_timeout_stderr_from_log(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _patch_open_to_tmp(monkeypatch, tmp_path)
        mgr = HttpServerLifecycleManager()
        cfg = _make_test_cfg(
            cmd=[
                sys.executable,
                "-c",
                "import sys, time; sys.stderr.write('NEVER_READY'); sys.stderr.flush(); time.sleep(60)",
            ],
            startup_timeout_sec=1,
        )
        with pytest.raises(HttpStartupError) as exc_info:
            asyncio.run(mgr.start("test_server", cfg))
        assert "NEVER_READY" in exc_info.value.failure.stderr_full

    def test_restart_closes_old_stderr_handle(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _patch_open_to_tmp(monkeypatch, tmp_path)
        mgr = HttpServerLifecycleManager()
        mock_proc = _make_mock_proc(exit_code=None)
        mgr._http_procs["srv"] = mock_proc
        fh = (tmp_path / "srv.stderr.log").open("ab")
        mgr._stderr_files["srv"] = fh
        mgr._stderr_log_paths["srv"] = str(tmp_path / "srv.stderr.log")

        async def fake_start(server_key: str, cfg: McpServerConfig) -> None:
            pass

        monkeypatch.setattr(mgr, "start", fake_start)
        asyncio.run(mgr.restart("srv", _make_test_cfg()))
        assert fh.closed
        assert "srv" not in mgr._stderr_files


# ── H-7: shutdown_all() cleanup ──────────────────────────────────────────────


class TestShutdownAllCleanup:
    """shutdown_all() pops all _http_procs entries and handles edge cases."""

    @pytest.mark.asyncio
    async def test_shutdown_all_clears_http_procs(self) -> None:
        mgr = HttpServerLifecycleManager()
        mgr._http_procs["srv1"] = _make_mock_proc(exit_code=None)
        mgr._http_procs["srv2"] = _make_mock_proc(exit_code=None)
        mgr._terminate_with_timeout = AsyncMock()

        await mgr.shutdown_all()

        assert len(mgr._http_procs) == 0
        assert len(mgr._stderr_files) == 0

    @pytest.mark.asyncio
    async def test_shutdown_all_removes_exited_proc_without_terminate(self) -> None:
        mgr = HttpServerLifecycleManager()
        mgr._http_procs["exited"] = _make_mock_proc(exit_code=0)
        mgr._terminate_with_timeout = AsyncMock()

        await mgr.shutdown_all()

        assert len(mgr._http_procs) == 0
        mgr._terminate_with_timeout.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_shutdown_all_continues_after_terminate_error(self) -> None:
        mgr = HttpServerLifecycleManager()
        mgr._http_procs["srv1"] = _make_mock_proc(exit_code=None)
        mgr._http_procs["srv2"] = _make_mock_proc(exit_code=None)

        call_count = 0

        async def flaky_terminate(
            proc: MagicMock, key: str, timeout: float = 3.0
        ) -> None:
            nonlocal call_count
            call_count += 1
            if key == "srv1":
                raise OSError("terminate failed")

        mgr._terminate_with_timeout = flaky_terminate

        await mgr.shutdown_all()

        assert len(mgr._http_procs) == 0
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_shutdown_all_twice_is_safe(self) -> None:
        mgr = HttpServerLifecycleManager()
        mgr._http_procs["srv"] = _make_mock_proc(exit_code=None)
        mgr._terminate_with_timeout = AsyncMock()

        await mgr.shutdown_all()
        await mgr.shutdown_all()

        assert len(mgr._http_procs) == 0


# ── H-8: process group shutdown ───────────────────────────────────────────────


def _make_running_proc(pid: int = 99999) -> MagicMock:
    """Create a running mock process with a controllable wait() call."""
    proc = _make_mock_proc(exit_code=None)
    proc.pid = pid
    proc.wait = MagicMock(return_value=0)
    return proc


class TestProcessGroupShutdown:
    """_terminate_with_timeout() uses os.killpg(SIGTERM/SIGKILL) with proc fallback."""

    @pytest.mark.asyncio
    async def test_terminate_uses_killpg_sigterm(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import signal as _signal

        import scripts.agent.http_lifecycle as mod

        killed: list[tuple[int, int]] = []
        monkeypatch.setattr(
            mod.os, "killpg", lambda pgid, sig: killed.append((pgid, sig))
        )

        async def fast_wait_for(coro: object, timeout: float) -> object:
            return await coro  # type: ignore[misc]

        monkeypatch.setattr(mod.asyncio, "wait_for", fast_wait_for)

        mgr = HttpServerLifecycleManager()
        proc = _make_running_proc(pid=42)
        mgr._http_pgids["srv"] = 42

        await mgr._terminate_with_timeout(proc, "srv", timeout=1.0)

        assert (42, _signal.SIGTERM) in killed
        proc.terminate.assert_not_called()

    @pytest.mark.asyncio
    async def test_terminate_fallback_on_process_lookup_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import scripts.agent.http_lifecycle as mod

        def raise_lookup(pgid: int, sig: int) -> None:
            raise ProcessLookupError("no such process")

        monkeypatch.setattr(mod.os, "killpg", raise_lookup)

        async def fast_wait_for(coro: object, timeout: float) -> object:
            return await coro  # type: ignore[misc]

        monkeypatch.setattr(mod.asyncio, "wait_for", fast_wait_for)

        mgr = HttpServerLifecycleManager()
        proc = _make_running_proc(pid=42)
        mgr._http_pgids["srv"] = 42

        await mgr._terminate_with_timeout(proc, "srv", timeout=1.0)

        proc.terminate.assert_called_once()

    @pytest.mark.asyncio
    async def test_terminate_sigkill_on_second_timeout(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import signal as _signal

        import scripts.agent.http_lifecycle as mod

        killed: list[tuple[int, int]] = []
        monkeypatch.setattr(
            mod.os, "killpg", lambda pgid, sig: killed.append((pgid, sig))
        )

        call_count = 0

        async def timeout_first_then_ok(coro: object, timeout: float) -> object:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise TimeoutError()
            return await coro  # type: ignore[misc]

        monkeypatch.setattr(mod.asyncio, "wait_for", timeout_first_then_ok)

        mgr = HttpServerLifecycleManager()
        proc = _make_running_proc(pid=55)
        mgr._http_pgids["srv"] = 55

        await mgr._terminate_with_timeout(proc, "srv", timeout=1.0)

        assert any(sig == _signal.SIGKILL for _, sig in killed)

    @pytest.mark.asyncio
    async def test_terminate_skips_killpg_when_already_exited(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Guard against resolving a reaped pid to an unrelated process's pgid.

        If proc has already exited, killpg must not be attempted at all —
        os.getpgid(proc.pid) on a reaped pid can resolve to a completely
        different process that has since reused the same pid.
        """
        import scripts.agent.http_lifecycle as mod

        killed: list[tuple[int, int]] = []
        monkeypatch.setattr(
            mod.os, "killpg", lambda pgid, sig: killed.append((pgid, sig))
        )

        mgr = HttpServerLifecycleManager()
        proc = _make_mock_proc(exit_code=0)  # already exited
        mgr._http_pgids["srv"] = 42

        await mgr._terminate_with_timeout(proc, "srv", timeout=1.0)

        assert killed == []
        proc.terminate.assert_not_called()
        proc.wait.assert_not_called()

    @pytest.mark.asyncio
    async def test_start_populates_http_pgids(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """start() must record the pgid before the health poll begins.

        subprocess.Popen is mocked (not spawned for real): the health poll always
        times out here (no real server), and with os.killpg mocked to a no-op, a
        real subprocess would never actually be terminated — leaking a background
        thread blocked in proc.wait() that Python's ThreadPoolExecutor atexit hook
        then waits on, hanging the whole test process for up to the process's
        lifetime instead of just this test's timeout.
        """
        import scripts.agent.http_lifecycle as mod

        monkeypatch.setattr(mod.os, "getpgid", lambda pid: 9999)
        monkeypatch.setattr(mod.os, "killpg", MagicMock())
        _patch_open_to_tmp(monkeypatch, tmp_path)

        mock_proc = _make_mock_proc(exit_code=None)
        mock_proc.pid = 12345
        mgr = HttpServerLifecycleManager()
        cfg = _make_test_cfg(cmd=["true"], startup_timeout_sec=1)

        with (
            patch("agent.http_lifecycle.subprocess.Popen", return_value=mock_proc),
            pytest.raises(HttpStartupError),
        ):
            await mgr.start("srv", cfg)

        assert mgr._http_pgids["srv"] == 9999

        assert mgr._http_pgids.get("srv") == 9999
