"""tests/agent/test_startup_mcp_lifecycle.py

Behavior-lock tests for agent/startup.py: StartupOrchestrator._start_servers() and
StartupOrchestrator._verify_mcp_health() (MCP server start and health checks).
"""

from __future__ import annotations

import asyncio
import subprocess
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from agent.http_lifecycle import HttpServerLifecycleManager
from agent.http_lifecycle_errors import (
    HttpStartupError,
    StartupFailure,
    TerminationOutcome,
)
from agent.shared.retry_helper import retry_once_with_delay
from agent.startup import (
    StartupInterrupted,
    StartupOrchestrator,
)
from agent.startup_mcp_starter import RETRY_DELAY_SEC
from shared.mcp_config import (
    McpServerConfig,
    StartupMode,
    TransportType,
)

# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_startup(
    mcp_servers: dict[str, McpServerConfig],
    shutdown_event: asyncio.Event | None = None,
) -> StartupOrchestrator:
    """Return a StartupOrchestrator with mocked ctx/view for _start_servers() tests."""
    ctx = MagicMock()
    ctx.cfg.mcp.mcp_servers = mcp_servers
    ctx.cfg.obs.audit_log_file = "/opt/llm/logs/audit.log"
    ctx.services_required.tools = MagicMock()
    ctx.services_required.tools.set_transport = MagicMock()
    ctx.services_required.lifecycle = AsyncMock()
    ctx.services_required.lifecycle.start_http_subprocess = AsyncMock()
    view = MagicMock()
    view.write_warning = MagicMock()
    return StartupOrchestrator(ctx, view, shutdown_event=shutdown_event)


def _http_subprocess_cfg() -> McpServerConfig:
    return McpServerConfig(
        transport=TransportType.HTTP,
        url="http://127.0.0.1:9999",
        auth_token="test-token",
        startup_mode=StartupMode.SUBPROCESS,
        cmd=["echo", "hello"],
    )


class _AsyncClientMock:
    """Minimal async context manager that mimics httpx.AsyncClient."""

    def __init__(
        self, get_return: MagicMock | None = None, timeout: float = 5.0
    ) -> None:
        self._get_return = get_return
        self.timeout = timeout

    async def __aenter__(self) -> _AsyncClientMock:
        return self

    async def __aexit__(self, *args: object, **kwargs: object) -> None:
        pass

    async def get(self, url: str, **_kw: object) -> MagicMock:
        assert self._get_return is not None
        return self._get_return


def _make_http_mock(resp_status: int) -> MagicMock:
    resp = MagicMock()
    resp.status_code = resp_status
    return resp


# ── StartupOrchestrator._start_servers ────────────────────────────────────────


class TestStartupOrchestratorStartServers:
    """Tests for StartupOrchestrator._start_servers()."""

    @pytest.mark.asyncio
    async def test_http_subprocess_calls_lifecycle(self) -> None:
        cfg = _http_subprocess_cfg()
        startup = _make_startup({"web": cfg})

        await startup._start_servers()

        startup._ctx.services_required.lifecycle.start_http_subprocess.assert_called_once_with(
            "web", cfg, shutdown_event=None
        )

    @pytest.mark.asyncio
    async def test_http_subprocess_failure_raises_in_production(self) -> None:
        cfg = _http_subprocess_cfg()
        startup = _make_startup({"web": cfg})
        startup._ctx.services_required.lifecycle.start_http_subprocess.side_effect = (
            RuntimeError("port busy")
        )

        with pytest.raises(RuntimeError, match=r"\[fatal\]"):
            await startup._start_servers()

    @pytest.mark.asyncio
    async def test_production_profile_raises_on_start_failure(self) -> None:
        cfg = _http_subprocess_cfg()
        startup = _make_startup({"web": cfg})
        startup._ctx.services_required.lifecycle.start_http_subprocess.side_effect = (
            RuntimeError("port busy")
        )

        with pytest.raises(RuntimeError, match=r"\[fatal\]"):
            await startup._start_servers()

    @pytest.mark.asyncio
    async def test_production_failure_message_contains_server_key(self) -> None:
        cfg = _http_subprocess_cfg()
        startup = _make_startup({"web": cfg})
        startup._ctx.services_required.lifecycle.start_http_subprocess.side_effect = (
            OSError("no such file")
        )

        with pytest.raises(OSError) as exc_info:
            await startup._start_servers()

        assert "web" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_retry_success_appends_to_spawned_subprocesses(self) -> None:
        """A retry-success (first attempt raises, retry returns a Popen) must append
        the retried proc onto self._spawned_subprocesses, not just the first-attempt
        success path."""
        cfg = _http_subprocess_cfg()
        startup = _make_startup({"web": cfg})
        retried_proc = MagicMock(spec=subprocess.Popen)
        startup._ctx.services_required.lifecycle.start_http_subprocess = AsyncMock(
            side_effect=[RuntimeError("port busy"), retried_proc]
        )

        result = await startup._start_servers()

        assert result == [retried_proc]

    @pytest.mark.asyncio
    async def test_no_process_returned_does_not_append(self) -> None:
        """start_http_subprocess() returning None (e.g. server already running)
        must not be treated as a spawned process."""
        cfg = _http_subprocess_cfg()
        startup = _make_startup({"web": cfg})
        startup._ctx.services_required.lifecycle.start_http_subprocess = AsyncMock(
            return_value=None
        )

        result = await startup._start_servers()

        assert result == []

    @pytest.mark.asyncio
    async def test_pre_set_shutdown_event_stops_before_second_server(self) -> None:
        """A shutdown_event set before _start_servers() is called must stop the
        per-server loop's pre-loop check before any further server is started."""
        cfg = _http_subprocess_cfg()
        shutdown_event = asyncio.Event()
        shutdown_event.set()
        startup = _make_startup(
            {"first": cfg, "second": cfg},
            shutdown_event=shutdown_event,
        )

        with pytest.raises(StartupInterrupted):
            await startup._start_servers()

        assert (
            startup._ctx.services_required.lifecycle.start_http_subprocess.call_count
            <= 1
        )

    @pytest.mark.asyncio
    async def test_shutdown_event_during_retry_delay_raises_promptly(self) -> None:
        """shutdown_event firing mid-retry-delay must interrupt _interruptible_sleep()
        promptly, well before RETRY_DELAY_SEC elapses."""
        cfg = _http_subprocess_cfg()
        shutdown_event = asyncio.Event()
        startup = _make_startup(
            {"web": cfg},
            shutdown_event=shutdown_event,
        )
        startup._ctx.services_required.lifecycle.start_http_subprocess.side_effect = (
            RuntimeError("port busy")
        )

        async def _fire_shutdown() -> None:
            await asyncio.sleep(0.05)
            shutdown_event.set()

        fire_task = asyncio.ensure_future(_fire_shutdown())
        start = time.monotonic()
        with pytest.raises(StartupInterrupted):
            await startup._start_servers()
        elapsed = time.monotonic() - start
        await fire_task

        assert elapsed < RETRY_DELAY_SEC / 2

    @pytest.mark.asyncio
    async def test_shutdown_event_passed_but_never_set_is_no_op(self) -> None:
        """A real, never-set shutdown_event must not change _start_servers()
        behavior relative to shutdown_event=None."""
        cfg = _http_subprocess_cfg()
        shutdown_event = asyncio.Event()
        startup = _make_startup(
            {"web": cfg},
            shutdown_event=shutdown_event,
        )

        result = await startup._start_servers()

        startup._ctx.services_required.lifecycle.start_http_subprocess.assert_called_once_with(
            "web", cfg, shutdown_event=shutdown_event
        )
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_startup_interrupted_propagates_without_retry(self) -> None:
        """REQ-002/T-001: a StartupInterrupted raised from a mocked subprocess start
        propagates out of start_servers() without invoking the retry helper."""
        cfg = _http_subprocess_cfg()
        startup = _make_startup({"web": cfg})
        startup._mcp_starter._start_http_subprocess_once = AsyncMock(
            side_effect=StartupInterrupted("shutdown requested")
        )

        with patch(
            "agent.startup_mcp_starter.retry_once_with_delay", new=AsyncMock()
        ) as retry_mock:
            with pytest.raises(StartupInterrupted, match="shutdown requested"):
                await startup._start_servers()

        retry_mock.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_genuine_runtime_error_still_retries(self) -> None:
        """REQ-005/T-002: a genuine RuntimeError from _start_http_subprocess_once()
        still triggers exactly one retry via the retry helper, and the retried proc
        is appended to the spawned list. Guards against accidentally dropping
        RuntimeError from the first-attempt tuple (which would drop retry)."""
        cfg = _http_subprocess_cfg()
        startup = _make_startup({"web": cfg})
        retried_proc = MagicMock(spec=subprocess.Popen)
        startup._ctx.services_required.lifecycle.start_http_subprocess = AsyncMock(
            side_effect=[RuntimeError("port busy"), retried_proc]
        )

        real_retry = retry_once_with_delay
        retry_calls = {"n": 0}

        async def _spy(*args, **kwargs) -> None:
            retry_calls["n"] += 1
            return await real_retry(*args, **kwargs)

        with patch("agent.startup_mcp_starter.retry_once_with_delay", new=_spy):
            result = await startup._start_servers()

        assert retry_calls["n"] == 1
        assert result == [retried_proc]

    @pytest.mark.asyncio
    async def test_unconfirmed_first_failure_raises_not_records_spawn(
        self,
    ) -> None:
        """REQ-004/T-005: a start whose first attempt fails with an exit that
        cannot be confirmed must end in a startup failure, not in a recorded
        spawn.

        Reproduces the router's two-line shape over a real
        HttpServerLifecycleManager: the first start spawns a live fake process,
        its health poll fails, and the terminator reports EXIT_UNCONFIRMED; the
        retry reuses the still-tracked process. On the pre-fix manager the reuse
        branch returns the process (a recorded spawn); the fix keeps it tracked
        and raises HttpStartupError again.
        """
        cfg = _http_subprocess_cfg()
        startup = _make_startup({"web": cfg})

        mgr = HttpServerLifecycleManager()
        fake_proc = MagicMock(spec=subprocess.Popen)
        fake_proc.poll.return_value = None
        fake_proc.pid = 4242

        async def _fake_create(
            server_key: str, server_cfg: McpServerConfig
        ) -> tuple[subprocess.Popen[bytes], object]:
            mgr._http_procs[server_key] = fake_proc
            mgr._http_pgids[server_key] = 99001
            return fake_proc, MagicMock()

        async def _fake_health(
            server_key: str,
            _server_cfg: object,
            _proc: object,
            _deadline: object,
            _shutdown_event: object,
        ) -> None:
            await mgr._raise_startup_failure_unconfirmed(
                server_key, "health poll timeout", ""
            )

        async def _start_http_subprocess(
            server_key: str,
            server_cfg: McpServerConfig,
            shutdown_event: asyncio.Event | None = None,
        ) -> object:
            await mgr.start(server_key, server_cfg, shutdown_event=shutdown_event)
            return mgr._http_procs.get(server_key)

        startup._ctx.services_required.lifecycle.start_http_subprocess = (
            _start_http_subprocess
        )

        with (
            patch.object(
                mgr._subprocess_launcher,
                "create_and_validate_proc",
                AsyncMock(side_effect=_fake_create),
            ),
            patch.object(mgr, "_health_poll_until_ready", _fake_health),
            patch.object(
                mgr._process_terminator,
                "terminate_with_timeout",
                AsyncMock(return_value=TerminationOutcome.EXIT_UNCONFIRMED),
            ),
            patch("agent.startup_mcp_starter.RETRY_DELAY_SEC", 0.05),
        ):
            with pytest.raises(HttpStartupError) as exc_info:
                await startup._start_servers()

        assert isinstance(exc_info.value.failure, StartupFailure)
        assert exc_info.value.failure.server_key == "web"
        assert startup._mcp_starter._spawned_subprocesses == []
        assert mgr._http_procs.get("web") is fake_proc
        assert mgr._failed_start_procs.get("web") is fake_proc

    @pytest.mark.asyncio
    async def test_failing_start_calls_twice_with_retry_gap(self) -> None:
        """REQ-004/T-003: a start that always fails calls start_http_subprocess
        exactly twice, the second no earlier than the patched RETRY_DELAY_SEC after
        the first. Fails on the pre-change code, which makes three attempts."""
        cfg = _http_subprocess_cfg()
        startup = _make_startup({"web": cfg})

        calls: list[float] = []

        async def _fail(*_args: object, **_kwargs: object) -> None:
            calls.append(time.monotonic())
            raise RuntimeError("port busy")

        startup._ctx.services_required.lifecycle.start_http_subprocess = AsyncMock(
            side_effect=_fail
        )

        with patch("agent.startup_mcp_starter.RETRY_DELAY_SEC", 0.05):
            with pytest.raises(RuntimeError, match=r"\[fatal\]"):
                await startup._start_servers()

        assert len(calls) == 2
        assert calls[1] - calls[0] >= 0.05


# ── StartupOrchestrator._verify_mcp_health ────────────────────────────────────


class TestStartupVerifyMcpHealth:
    """Tests for StartupOrchestrator._verify_mcp_health()."""

    @pytest.mark.asyncio
    async def test_health_check_passes_for_all_servers(self) -> None:
        cfg = _http_subprocess_cfg()
        startup = _make_startup({"web": cfg})

        mock_resp = _make_http_mock(200)
        mock_client = _AsyncClientMock(get_return=mock_resp)

        with patch(
            "agent.startup_mcp_starter.httpx.AsyncClient", return_value=mock_client
        ):
            await startup._verify_mcp_health()

    @pytest.mark.asyncio
    async def test_health_check_failure_production_raises(self) -> None:
        cfg = _http_subprocess_cfg()
        startup = _make_startup({"web": cfg})

        mock_resp_fail = _make_http_mock(503)

        with patch(
            "agent.startup_mcp_starter.httpx.AsyncClient",
            return_value=_AsyncClientMock(get_return=mock_resp_fail),
        ):
            with pytest.raises(RuntimeError, match=r"\[fatal\]"):
                await startup._verify_mcp_health()

    @pytest.mark.asyncio
    async def test_health_check_passes_after_retry(self) -> None:
        cfg = _http_subprocess_cfg()
        startup = _make_startup({"web": cfg})

        mock_resp_fail = _make_http_mock(503)
        mock_resp_ok = _make_http_mock(200)

        call_count = [0]

        def client_factory(*_args, **_kwargs: object) -> _AsyncClientMock:
            call_count[0] += 1
            if call_count[0] == 1:
                return _AsyncClientMock(get_return=mock_resp_fail)
            return _AsyncClientMock(get_return=mock_resp_ok)

        with patch(
            "agent.startup_mcp_starter.httpx.AsyncClient", side_effect=client_factory
        ):
            await startup._verify_mcp_health()

        startup._view.write_warning.assert_not_called()

    @pytest.mark.asyncio
    async def test_skips_non_subprocess_servers(self) -> None:
        cfg_persistent = McpServerConfig(
            transport=TransportType.HTTP,
            url="http://127.0.0.1:8888",
            startup_mode=StartupMode.PERSISTENT,
            cmd=["echo", "persistent"],
            auth_token="test-token",
        )
        startup = _make_startup({"persistent": cfg_persistent})

        with patch("agent.startup_mcp_starter.httpx.AsyncClient") as MockClient:
            await startup._verify_mcp_health()

        MockClient.assert_not_called()

    @pytest.mark.asyncio
    async def test_tools_service_none_raises(self) -> None:
        cfg = _http_subprocess_cfg()
        ctx = MagicMock()
        ctx.cfg.mcp.mcp_servers = {"web": cfg}
        ctx.services_required.tools = None
        ctx.services_required.lifecycle = AsyncMock()
        view = MagicMock()
        startup = StartupOrchestrator(ctx, view)

        with pytest.raises(RuntimeError, match="tools service not initialized"):
            await startup._verify_mcp_health()

    @pytest.mark.asyncio
    async def test_lifecycle_service_none_raises(self) -> None:
        cfg = _http_subprocess_cfg()
        ctx = MagicMock()
        ctx.cfg.mcp.mcp_servers = {"web": cfg}
        ctx.services_required.tools = MagicMock()
        ctx.services_required.lifecycle = None
        view = MagicMock()
        startup = StartupOrchestrator(ctx, view)

        with pytest.raises(RuntimeError, match="lifecycle service not initialized"):
            await startup._verify_mcp_health()

    @pytest.mark.asyncio
    async def test_shutdown_event_during_health_retry_delay_raises_promptly(
        self,
    ) -> None:
        """shutdown_event firing mid-health-retry-delay must interrupt
        _interruptible_sleep() promptly, mirroring the _start_servers() retry-delay
        interruption behavior."""
        cfg = _http_subprocess_cfg()
        shutdown_event = asyncio.Event()
        startup = _make_startup(
            {"web": cfg},
            shutdown_event=shutdown_event,
        )
        mock_resp_fail = _make_http_mock(503)

        async def _fire_shutdown() -> None:
            await asyncio.sleep(0.05)
            shutdown_event.set()

        fire_task = asyncio.ensure_future(_fire_shutdown())
        start = time.monotonic()
        with patch(
            "agent.startup_mcp_starter.httpx.AsyncClient",
            return_value=_AsyncClientMock(get_return=mock_resp_fail),
        ):
            with pytest.raises(StartupInterrupted):
                await startup._verify_mcp_health()
        elapsed = time.monotonic() - start
        await fire_task

        assert elapsed < RETRY_DELAY_SEC / 2

    @pytest.mark.asyncio
    async def test_failing_health_calls_twice_with_retry_gap(self) -> None:
        """REQ-004/T-004: a health probe that always fails runs its GET exactly
        twice, the second no earlier than the patched RETRY_DELAY_SEC after the
        first. Fails on the pre-change code, which makes three attempts."""
        cfg = _http_subprocess_cfg()
        startup = _make_startup({"web": cfg})

        mock_fail = _make_http_mock(503)
        calls: list[float] = []

        def _client_factory(*_args: object, **_kwargs: object) -> _AsyncClientMock:
            calls.append(time.monotonic())
            return _AsyncClientMock(get_return=mock_fail)

        with (
            patch("agent.startup_mcp_starter.RETRY_DELAY_SEC", 0.05),
            patch(
                "agent.startup_mcp_starter.httpx.AsyncClient",
                side_effect=_client_factory,
            ),
        ):
            with pytest.raises(RuntimeError, match=r"\[fatal\]"):
                await startup._verify_mcp_health()

        assert len(calls) == 2
        assert calls[1] - calls[0] >= 0.05
