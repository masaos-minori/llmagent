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
from agent.http_lifecycle import HttpStartupError, StartupFailure
from agent.lifecycle import LifecycleState
from agent.stdio_lifecycle import TransportHandle
from shared.mcp_config import McpServerConfig


def _http_cfg(url: str = "http://127.0.0.1:8000") -> McpServerConfig:
    return McpServerConfig("http", url, [], "")


def _http_subprocess_cfg(
    url: str = "http://127.0.0.1:8000",
    cmd: list[str] | None = None,
    timeout: int = 5,
) -> McpServerConfig:
    return McpServerConfig(
        "http",
        url,
        cmd or ["python", "srv.py"],
        "",
        startup_mode="subprocess",
        startup_timeout_sec=timeout,
    )


def _stdio_persistent() -> McpServerConfig:
    return McpServerConfig("stdio", "", ["python", "s.py"], "")


def _stdio_ondemand(cmd: list[str] | None = None) -> McpServerConfig:
    return McpServerConfig(
        "stdio", "", cmd or ["python", "s.py"], "", startup_mode="ondemand"
    )


def _stdio_ondemand_idle(
    idle_sec: int, cmd: list[str] | None = None
) -> McpServerConfig:
    return McpServerConfig(
        "stdio",
        "",
        cmd or ["python", "s.py"],
        "",
        startup_mode="ondemand",
        idle_timeout_sec=idle_sec,
    )


def _mock_tool_executor() -> MagicMock:
    ex = MagicMock()
    ex.set_transport = MagicMock()
    return ex


class TestEnsureReady:
    @pytest.mark.asyncio
    async def test_http_server_noop(self) -> None:
        configs = {"web": _http_cfg()}
        ex = _mock_tool_executor()
        mgr = _ServerLifecycleRouter(configs, ex, {})
        # Must not raise and must not attempt subprocess startup
        await mgr.ensure_ready("web")
        ex.set_transport.assert_not_called()

    @pytest.mark.asyncio
    async def test_persistent_stdio_noop(self) -> None:
        configs = {"file": _stdio_persistent()}
        ex = _mock_tool_executor()
        mgr = _ServerLifecycleRouter(configs, ex, {})
        await mgr.ensure_ready("file")
        ex.set_transport.assert_not_called()

    @pytest.mark.asyncio
    async def test_ondemand_already_alive_noop(self) -> None:
        transport = MagicMock()
        transport.is_alive.return_value = True
        configs = {"od": _stdio_ondemand()}
        ex = _mock_tool_executor()
        mgr = _ServerLifecycleRouter(configs, ex, {"od": transport})
        await mgr.ensure_ready("od")
        ex.set_transport.assert_not_called()

    @pytest.mark.asyncio
    async def test_ondemand_starts_when_not_alive(self) -> None:
        configs = {"od": _stdio_ondemand(["python", "srv.py"])}
        ex = _mock_tool_executor()
        stdio_procs: dict = {}

        with patch("agent.stdio_lifecycle.StdioTransport") as MockTransport:
            mock_t = AsyncMock()
            mock_t.is_alive.return_value = True
            MockTransport.return_value = mock_t

            mgr = _ServerLifecycleRouter(configs, ex, stdio_procs)
            await mgr.ensure_ready("od")

        MockTransport.assert_called_once_with(
            ["python", "srv.py"], server_key="od", working_dir="", env=None
        )
        mock_t.start.assert_awaited_once()
        ex.set_transport.assert_called_once_with("od", mock_t)
        assert stdio_procs["od"] is mock_t

    @pytest.mark.asyncio
    async def test_ondemand_start_failure_logs_error(self) -> None:
        configs = {"od": _stdio_ondemand(["python", "srv.py"])}
        ex = _mock_tool_executor()
        stdio_procs: dict = {}

        with patch("agent.stdio_lifecycle.StdioTransport") as MockTransport:
            mock_t = AsyncMock()
            mock_t.is_alive.return_value = False
            mock_t.start.side_effect = OSError("no such file")
            MockTransport.return_value = mock_t

            mgr = _ServerLifecycleRouter(configs, ex, stdio_procs)
            # Must not raise; logs an error
            await mgr.ensure_ready("od")

        ex.set_transport.assert_not_called()

    @pytest.mark.asyncio
    async def test_ondemand_no_cmd_logs_warning(self) -> None:
        cfg = McpServerConfig(
            "stdio", "", ["python", "s.py"], "", startup_mode="ondemand"
        )
        cfg.cmd = []  # empty cmd after construction
        configs = {"od": cfg}
        ex = _mock_tool_executor()
        mgr = _ServerLifecycleRouter(configs, ex, {})
        # Must not raise; logs a warning
        await mgr.ensure_ready("od")
        ex.set_transport.assert_not_called()

    @pytest.mark.asyncio
    async def test_unknown_server_key_noop(self) -> None:
        configs: dict[str, McpServerConfig] = {}
        ex = _mock_tool_executor()
        mgr = _ServerLifecycleRouter(configs, ex, {})
        await mgr.ensure_ready("nonexistent")
        ex.set_transport.assert_not_called()

    @pytest.mark.asyncio
    async def test_concurrent_ondemand_starts_only_once(self) -> None:
        configs = {"od": _stdio_ondemand(["python", "srv.py"])}
        ex = _mock_tool_executor()
        stdio_procs: dict = {}
        start_count = 0

        async def fake_start() -> None:
            nonlocal start_count
            await asyncio.sleep(0)  # yield to allow interleaving
            start_count += 1

        with patch("agent.stdio_lifecycle.StdioTransport") as MockTransport:
            mock_t = MagicMock()
            mock_t.is_alive = MagicMock(return_value=True)
            mock_t.start = fake_start
            MockTransport.return_value = mock_t

            mgr = _ServerLifecycleRouter(configs, ex, stdio_procs)
            # Fire three concurrent ensure_ready calls
            await asyncio.gather(
                mgr.ensure_ready("od"),
                mgr.ensure_ready("od"),
                mgr.ensure_ready("od"),
            )

        assert start_count == 1


class TestShutdownIdle:
    @pytest.mark.asyncio
    async def test_stops_idle_ondemand_server(self) -> None:
        transport = AsyncMock()
        transport.is_alive = MagicMock(return_value=True)  # is_alive is sync
        configs = {"od": _stdio_ondemand_idle(idle_sec=30)}
        ex = _mock_tool_executor()
        mgr = _ServerLifecycleRouter(configs, ex, {"od": transport})
        # Backdate _last_called to simulate 60s of inactivity
        mgr._last_called["od"] = mgr._last_called["od"] - 60
        await mgr.shutdown_idle()
        transport.stop.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_skips_server_within_timeout(self) -> None:
        transport = AsyncMock()
        transport.is_alive = MagicMock(return_value=True)
        configs = {"od": _stdio_ondemand_idle(idle_sec=300)}
        ex = _mock_tool_executor()
        mgr = _ServerLifecycleRouter(configs, ex, {"od": transport})
        # _last_called initialized to now(); 300s has not elapsed
        await mgr.shutdown_idle()
        transport.stop.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_skips_idle_timeout_disabled(self) -> None:
        transport = AsyncMock()
        transport.is_alive = MagicMock(return_value=True)
        configs = {"od": _stdio_ondemand_idle(idle_sec=0)}
        ex = _mock_tool_executor()
        mgr = _ServerLifecycleRouter(configs, ex, {"od": transport})
        mgr._last_called["od"] = 0.0  # simulate very old last call
        await mgr.shutdown_idle()
        transport.stop.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_skips_persistent_server(self) -> None:
        transport = AsyncMock()
        transport.is_alive = MagicMock(return_value=True)
        configs = {"p": _stdio_persistent()}
        ex = _mock_tool_executor()
        mgr = _ServerLifecycleRouter(configs, ex, {"p": transport})
        mgr._last_called["p"] = 0.0  # simulate very old last call
        await mgr.shutdown_idle()
        transport.stop.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_skips_already_dead_server(self) -> None:
        transport = AsyncMock()
        transport.is_alive = MagicMock(return_value=False)
        configs = {"od": _stdio_ondemand_idle(idle_sec=30)}
        ex = _mock_tool_executor()
        mgr = _ServerLifecycleRouter(configs, ex, {"od": transport})
        mgr._last_called["od"] = 0.0
        await mgr.shutdown_idle()
        transport.stop.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_tolerates_stop_error(self) -> None:
        transport = AsyncMock()
        transport.is_alive = MagicMock(return_value=True)
        transport.stop.side_effect = RuntimeError("crash")
        configs = {"od": _stdio_ondemand_idle(idle_sec=30)}
        ex = _mock_tool_executor()
        mgr = _ServerLifecycleRouter(configs, ex, {"od": transport})
        mgr._last_called["od"] = 0.0
        # Must not propagate
        await mgr.shutdown_idle()


class TestEnsureReadySubprocess:
    @pytest.mark.asyncio
    async def test_subprocess_http_already_running_noop(self) -> None:
        proc = MagicMock()
        proc.poll.return_value = None  # still alive
        cfg = _http_subprocess_cfg()
        ex = _mock_tool_executor()
        mgr = _ServerLifecycleRouter({"srv": cfg}, ex, {})
        mgr._http_mgr._http_procs["srv"] = proc
        await mgr.ensure_ready("srv")
        # verify no attempt to start a new process
        ex.set_transport.assert_not_called()

    @pytest.mark.asyncio
    async def test_subprocess_http_dead_logs_warning(self) -> None:
        proc = MagicMock()
        proc.poll.return_value = 1  # exited
        cfg = _http_subprocess_cfg()
        ex = _mock_tool_executor()
        mgr = _ServerLifecycleRouter({"srv": cfg}, ex, {})
        mgr._http_mgr._http_procs["srv"] = proc
        await mgr.ensure_ready("srv")  # must not raise


class TestStartHttpSubprocess:
    @pytest.mark.asyncio
    async def test_starts_process_and_polls_health(self) -> None:
        cfg = _http_subprocess_cfg(url="http://127.0.0.1:9999", cmd=["python", "s.py"])
        ex = _mock_tool_executor()
        mgr = _ServerLifecycleRouter({"s": cfg}, ex, {})

        mock_proc = MagicMock()
        mock_proc.poll.return_value = None
        mock_proc.stderr = None

        mock_resp = MagicMock()
        mock_resp.status_code = 200

        with (
            patch("agent.http_lifecycle.subprocess.Popen", return_value=mock_proc),
            patch("agent.http_lifecycle.httpx.AsyncClient") as MockClient,
        ):
            client_instance = AsyncMock()
            client_instance.get = AsyncMock(return_value=mock_resp)
            MockClient.return_value.__aenter__ = AsyncMock(return_value=client_instance)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            await mgr.start_http_subprocess("s", cfg)

        assert mgr._http_mgr._http_procs["s"] is mock_proc

    @pytest.mark.asyncio
    async def test_reuses_alive_proc(self) -> None:
        cfg = _http_subprocess_cfg(url="http://127.0.0.1:9999", cmd=["python", "s.py"])
        ex = _mock_tool_executor()
        mgr = _ServerLifecycleRouter({"s": cfg}, ex, {})
        existing = MagicMock()
        existing.poll.return_value = None
        mgr._http_mgr._http_procs["s"] = existing

        with patch("agent.http_lifecycle.subprocess.Popen") as mock_popen:
            await mgr.start_http_subprocess("s", cfg)
        mock_popen.assert_not_called()

    @pytest.mark.asyncio
    async def test_raises_on_early_exit(self) -> None:
        cfg = _http_subprocess_cfg(url="http://127.0.0.1:9999", cmd=["python", "s.py"])
        ex = _mock_tool_executor()
        mgr = _ServerLifecycleRouter({"s": cfg}, ex, {})

        mock_proc = MagicMock()
        mock_proc.poll.return_value = 1  # already exited
        mock_proc.stderr = None

        with (
            patch("agent.http_lifecycle.subprocess.Popen", return_value=mock_proc),
            patch("agent.http_lifecycle.httpx.AsyncClient") as MockClient,
            pytest.raises(RuntimeError, match="exited early"),
        ):
            client_instance = AsyncMock()
            mock_resp = MagicMock()
            mock_resp.status_code = 503
            client_instance.get = AsyncMock(return_value=mock_resp)
            MockClient.return_value.__aenter__ = AsyncMock(return_value=client_instance)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            await mgr.start_http_subprocess("s", cfg)

    @pytest.mark.asyncio
    async def test_raises_on_timeout(self) -> None:
        cfg = _http_subprocess_cfg(
            url="http://127.0.0.1:9999", cmd=["python", "s.py"], timeout=0
        )
        ex = _mock_tool_executor()
        mgr = _ServerLifecycleRouter({"s": cfg}, ex, {})

        mock_proc = MagicMock()
        mock_proc.poll.return_value = None
        mock_proc.stderr = None

        with (
            patch("agent.http_lifecycle.subprocess.Popen", return_value=mock_proc),
            patch("agent.http_lifecycle.httpx.AsyncClient") as MockClient,
            pytest.raises(RuntimeError, match="did not become healthy"),
        ):
            client_instance = AsyncMock()
            client_instance.get = AsyncMock(side_effect=Exception("connect refused"))
            MockClient.return_value.__aenter__ = AsyncMock(return_value=client_instance)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            await mgr.start_http_subprocess("s", cfg)

    @pytest.mark.asyncio
    async def test_merges_env_vars(self) -> None:
        cfg = _http_subprocess_cfg(url="http://127.0.0.1:9999", cmd=["python", "s.py"])
        # Override env to exercise the env-merge branch
        cfg.env = {"MY_VAR": "val"}
        ex = _mock_tool_executor()
        mgr = _ServerLifecycleRouter({"s": cfg}, ex, {})

        mock_proc = MagicMock()
        mock_proc.poll.return_value = None
        mock_proc.stderr = None
        mock_resp = MagicMock()
        mock_resp.status_code = 200

        with (
            patch(
                "agent.http_lifecycle.subprocess.Popen", return_value=mock_proc
            ) as mock_popen,
            patch("agent.http_lifecycle.httpx.AsyncClient") as MockClient,
        ):
            client_instance = AsyncMock()
            client_instance.get = AsyncMock(return_value=mock_resp)
            MockClient.return_value.__aenter__ = AsyncMock(return_value=client_instance)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            await mgr.start_http_subprocess("s", cfg)

        # Verify Popen received an env dict (not None)
        call_kwargs = mock_popen.call_args.kwargs
        assert call_kwargs["env"] is not None
        assert call_kwargs["env"].get("MY_VAR") == "val"

    @pytest.mark.asyncio
    async def test_health_poll_exception_is_logged_not_raised(self) -> None:
        cfg = _http_subprocess_cfg(
            url="http://127.0.0.1:9999", cmd=["python", "s.py"], timeout=5
        )
        ex = _mock_tool_executor()
        mgr = _ServerLifecycleRouter({"s": cfg}, ex, {})

        mock_proc = MagicMock()
        mock_proc.poll.return_value = None
        mock_proc.stderr = None
        good_resp = MagicMock()
        good_resp.status_code = 200

        call_count = 0

        async def get_side_effect(url: str) -> MagicMock:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ConnectionRefusedError("refused")
            return good_resp

        with (
            patch("agent.http_lifecycle.subprocess.Popen", return_value=mock_proc),
            patch("agent.http_lifecycle.httpx.AsyncClient") as MockClient,
            patch("agent.http_lifecycle.asyncio.sleep", AsyncMock()),
        ):
            client_instance = AsyncMock()
            client_instance.get = get_side_effect
            MockClient.return_value.__aenter__ = AsyncMock(return_value=client_instance)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            await mgr.start_http_subprocess("s", cfg)

        assert call_count == 2


class TestRestart:
    @pytest.mark.asyncio
    async def test_restart_non_subprocess_mode_warns(self) -> None:
        cfg = _http_cfg()  # no startup_mode="subprocess"
        ex = _mock_tool_executor()
        mgr = _ServerLifecycleRouter({"srv": cfg}, ex, {})
        # Must log warning and return without raising
        await mgr.restart("srv")

    @pytest.mark.asyncio
    async def test_restart_unknown_key_warns(self) -> None:
        ex = _mock_tool_executor()
        mgr = _ServerLifecycleRouter({}, ex, {})
        await mgr.restart("nonexistent")  # must not raise

    @pytest.mark.asyncio
    async def test_restart_terminates_running_proc(self) -> None:
        cfg = _http_subprocess_cfg(url="http://127.0.0.1:9998", cmd=["python", "s.py"])
        ex = _mock_tool_executor()
        mgr = _ServerLifecycleRouter({"srv": cfg}, ex, {})

        proc = MagicMock()
        proc.poll.return_value = None  # running
        mgr._http_mgr._http_procs["srv"] = proc

        good_resp = MagicMock()
        good_resp.status_code = 200

        new_proc = MagicMock()
        new_proc.poll.return_value = None
        new_proc.stderr = None

        with (
            patch("agent.http_lifecycle.subprocess.Popen", return_value=new_proc),
            patch("agent.http_lifecycle.httpx.AsyncClient") as MockClient,
            patch(
                "agent.http_lifecycle.asyncio.wait_for",
                AsyncMock(return_value=None),
            ),
        ):
            client_instance = AsyncMock()
            client_instance.get = AsyncMock(return_value=good_resp)
            MockClient.return_value.__aenter__ = AsyncMock(return_value=client_instance)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            await mgr.restart("srv")

        # Stale proc must have been removed before start; new proc registered
        proc.terminate.assert_called_once()
        assert mgr._http_mgr._http_procs.get("srv") is new_proc

    @pytest.mark.asyncio
    async def test_restart_no_existing_proc_still_starts(self) -> None:
        cfg = _http_subprocess_cfg(url="http://127.0.0.1:9997", cmd=["python", "s.py"])
        ex = _mock_tool_executor()
        mgr = _ServerLifecycleRouter({"srv": cfg}, ex, {})
        # No proc in _http_procs — restart must still call start_http_subprocess

        good_resp = MagicMock()
        good_resp.status_code = 200

        new_proc = MagicMock()
        new_proc.poll.return_value = None
        new_proc.stderr = None

        with (
            patch("agent.http_lifecycle.subprocess.Popen", return_value=new_proc),
            patch("agent.http_lifecycle.httpx.AsyncClient") as MockClient,
        ):
            client_instance = AsyncMock()
            client_instance.get = AsyncMock(return_value=good_resp)
            MockClient.return_value.__aenter__ = AsyncMock(return_value=client_instance)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            await mgr.restart("srv")

        assert mgr._http_mgr._http_procs.get("srv") is new_proc

    @pytest.mark.asyncio
    async def test_restart_force_kills_on_terminate_timeout(self) -> None:
        cfg = _http_subprocess_cfg(url="http://127.0.0.1:9996", cmd=["python", "s.py"])
        ex = _mock_tool_executor()
        mgr = _ServerLifecycleRouter({"srv": cfg}, ex, {})

        proc = MagicMock()
        proc.poll.return_value = None
        mgr._http_mgr._http_procs["srv"] = proc

        good_resp = MagicMock()
        good_resp.status_code = 200
        new_proc = MagicMock()
        new_proc.poll.return_value = None
        new_proc.stderr = None

        async def fake_wait_for(coro: object, timeout: float) -> None:
            raise TimeoutError

        with (
            patch("agent.http_lifecycle.subprocess.Popen", return_value=new_proc),
            patch("agent.http_lifecycle.httpx.AsyncClient") as MockClient,
            patch("agent.http_lifecycle.asyncio.wait_for", fake_wait_for),
        ):
            client_instance = AsyncMock()
            client_instance.get = AsyncMock(return_value=good_resp)
            MockClient.return_value.__aenter__ = AsyncMock(return_value=client_instance)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            await mgr.restart("srv")

        proc.kill.assert_called_once()


class TestShutdownAll:
    @pytest.mark.asyncio
    async def test_stops_all_running_transports(self) -> None:
        t1 = AsyncMock()
        t2 = AsyncMock()
        configs: dict[str, McpServerConfig] = {}
        ex = _mock_tool_executor()
        mgr = _ServerLifecycleRouter(configs, ex, {"a": t1, "b": t2})
        await mgr.shutdown_all()
        t1.stop.assert_awaited_once()
        t2.stop.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_shutdown_terminates_http_procs(self) -> None:
        proc = MagicMock()
        proc.poll.return_value = None  # running
        configs: dict[str, McpServerConfig] = {}
        ex = _mock_tool_executor()
        mgr = _ServerLifecycleRouter(configs, ex, {})
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
        mgr = _ServerLifecycleRouter(configs, ex, {})
        mgr._http_mgr._http_procs["srv"] = proc
        await mgr.shutdown_all()
        proc.terminate.assert_not_called()

    @pytest.mark.asyncio
    async def test_shutdown_tolerates_stop_errors(self) -> None:
        t1 = AsyncMock()
        t1.stop.side_effect = RuntimeError("crash")
        configs: dict[str, McpServerConfig] = {}
        ex = _mock_tool_executor()
        mgr = _ServerLifecycleRouter(configs, ex, {"a": t1})
        # Must not propagate the exception
        await mgr.shutdown_all()

    @pytest.mark.asyncio
    async def test_shutdown_tolerates_http_terminate_errors(self) -> None:
        proc = MagicMock()
        proc.poll.return_value = None
        proc.terminate.side_effect = OSError("cannot terminate")
        configs: dict[str, McpServerConfig] = {}
        ex = _mock_tool_executor()
        mgr = _ServerLifecycleRouter(configs, ex, {})
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
        "stdio",
        "",
        _echo_cmd(),
        "",
        startup_mode="ondemand",
        working_dir=working_dir,
    )


class TestEnsureReadyIntegration:
    """Integration tests: _ServerLifecycleRouter with real echo subprocess."""

    @pytest.mark.asyncio
    async def test_ondemand_start_on_first_call(self) -> None:
        configs = {"echo": _ondemand_echo_cfg()}
        stdio_procs: dict = {}
        ex = _mock_tool_executor()
        mgr = _ServerLifecycleRouter(configs, ex, stdio_procs)

        await mgr.ensure_ready("echo")

        assert "echo" in stdio_procs
        assert stdio_procs["echo"].is_alive()
        await mgr.shutdown_all()

    @pytest.mark.asyncio
    async def test_ondemand_no_double_start(self) -> None:
        configs = {"echo": _ondemand_echo_cfg()}
        stdio_procs: dict = {}
        ex = _mock_tool_executor()
        mgr = _ServerLifecycleRouter(configs, ex, stdio_procs)

        await mgr.ensure_ready("echo")
        first_transport = stdio_procs["echo"]
        first_pid = first_transport._proc.pid if first_transport._proc else None

        await mgr.ensure_ready("echo")
        second_transport = stdio_procs["echo"]
        second_pid = second_transport._proc.pid if second_transport._proc else None

        assert first_pid is not None
        assert first_pid == second_pid
        await mgr.shutdown_all()

    @pytest.mark.asyncio
    async def test_ondemand_working_dir_passed(self, tmp_path: Path) -> None:
        from shared.tool_executor import StdioTransport

        transport = StdioTransport(
            _echo_cmd(), server_key="echo", working_dir=str(tmp_path)
        )
        try:
            await transport.start()
            assert transport.is_alive()
            result, is_error, _ = await transport.call("cwd_query", {})
            assert not is_error
            assert Path(result).resolve() == tmp_path.resolve()
        finally:
            await transport.stop()


class TestShutdownIdleIntegration:
    """Idle-timeout integration test against real echo subprocess."""

    @pytest.mark.asyncio
    async def test_idle_stop_after_timeout(self) -> None:
        from shared.tool_executor import StdioTransport

        transport = StdioTransport(_echo_cmd(), server_key="echo")
        await transport.start()
        assert transport.is_alive()

        configs = {"echo": _stdio_ondemand_idle(idle_sec=30)}
        ex = _mock_tool_executor()
        mgr = _ServerLifecycleRouter(configs, ex, {"echo": transport})
        mgr._last_called["echo"] = mgr._last_called["echo"] - 60

        await mgr.shutdown_idle()
        assert not transport.is_alive()

    @pytest.mark.asyncio
    async def test_non_ondemand_not_idle_stopped(self) -> None:
        from shared.tool_executor import StdioTransport

        transport = StdioTransport(_echo_cmd(), server_key="echo")
        await transport.start()
        assert transport.is_alive()

        configs = {"echo": McpServerConfig("stdio", "", _echo_cmd(), "")}
        ex = _mock_tool_executor()
        mgr = _ServerLifecycleRouter(configs, ex, {"echo": transport})
        mgr._last_called["echo"] = 0.0

        await mgr.shutdown_idle()
        assert transport.is_alive()
        await transport.stop()


# ── LifecycleState / HttpStartupError / TransportHandle ──────────────────────


class TestLifecycleState:
    def test_lifecycle_state_values(self) -> None:
        assert LifecycleState.RUNNING.value == "running"
        assert LifecycleState.STOPPED.value == "stopped"
        assert LifecycleState.FAILED.value == "failed"
        assert LifecycleState.UNKNOWN.value == "unknown"

    def test_get_transport_state_unknown_server(self) -> None:
        mgr = _ServerLifecycleRouter({}, _mock_tool_executor(), {})
        assert mgr.get_transport_state("nonexistent") == LifecycleState.UNKNOWN

    def test_get_transport_state_http_server_returns_unknown(self) -> None:
        cfg = McpServerConfig("http", "http://127.0.0.1:8000", [], "svc")
        mgr = _ServerLifecycleRouter({"svc": cfg}, _mock_tool_executor(), {})
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


class TestTransportHandle:
    def test_default_last_error_is_none(self) -> None:
        from unittest.mock import MagicMock

        from shared.tool_executor import StdioTransport

        transport = MagicMock(spec=StdioTransport)
        handle = TransportHandle(transport=transport, state=LifecycleState.RUNNING)
        assert handle.last_error is None

    def test_stores_state_and_transport(self) -> None:
        handle = TransportHandle(transport=None, state=LifecycleState.STOPPED)
        assert handle.state == LifecycleState.STOPPED
        assert handle.transport is None

    def test_last_error_can_be_set(self) -> None:
        handle = TransportHandle(
            transport=None, state=LifecycleState.FAILED, last_error="timeout"
        )
        assert handle.last_error == "timeout"
