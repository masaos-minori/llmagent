"""tests/agent/test_startup_approval_recovery.py

Behavior-lock tests for agent/startup.py: StartupOrchestrator._recover_pending_approvals().
"""

from __future__ import annotations

import asyncio
import subprocess
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from agent.startup import (
    StartupInterrupted,
    StartupOrchestrator,
)
from agent.startup_mcp_starter import RETRY_DELAY_SEC
from shared.mcp_config import (
    McpServerConfig,
    SecurityProfile,
    StartupMode,
    TransportType,
)

# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_startup(
    mcp_servers: dict[str, McpServerConfig],
    security_profile: SecurityProfile = SecurityProfile.PRODUCTION,
    shutdown_event: asyncio.Event | None = None,
) -> StartupOrchestrator:
    """Return a StartupOrchestrator with mocked ctx/view for _start_servers() tests."""
    ctx = MagicMock()
    ctx.cfg.mcp.security_profile = security_profile
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
        startup = _make_startup(
            {"web": cfg}, security_profile=SecurityProfile.PRODUCTION
        )

        await startup._start_servers()

        startup._ctx.services_required.lifecycle.start_http_subprocess.assert_called_once_with(
            "web", cfg, shutdown_event=None
        )

    @pytest.mark.asyncio
    async def test_http_subprocess_failure_raises_in_production(self) -> None:
        cfg = _http_subprocess_cfg()
        startup = _make_startup(
            {"web": cfg}, security_profile=SecurityProfile.PRODUCTION
        )
        startup._ctx.services_required.lifecycle.start_http_subprocess.side_effect = (
            RuntimeError("port busy")
        )

        with pytest.raises(RuntimeError, match=r"\[fatal\]"):
            await startup._start_servers()

    @pytest.mark.asyncio
    async def test_production_profile_raises_on_start_failure(self) -> None:
        cfg = _http_subprocess_cfg()
        startup = _make_startup(
            {"web": cfg}, security_profile=SecurityProfile.PRODUCTION
        )
        startup._ctx.services_required.lifecycle.start_http_subprocess.side_effect = (
            RuntimeError("port busy")
        )

        with pytest.raises(RuntimeError, match=r"\[fatal\]"):
            await startup._start_servers()

    @pytest.mark.asyncio
    async def test_production_failure_message_contains_server_key(self) -> None:
        cfg = _http_subprocess_cfg()
        startup = _make_startup(
            {"web": cfg}, security_profile=SecurityProfile.PRODUCTION
        )
        startup._ctx.services_required.lifecycle.start_http_subprocess.side_effect = (
            OSError("no such file")
        )

        with pytest.raises(RuntimeError) as exc_info:
            await startup._start_servers()

        assert "web" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_retry_success_appends_to_spawned_subprocesses(self) -> None:
        """A retry-success (first attempt raises, retry returns a Popen) must append
        the retried proc onto self._spawned_subprocesses, not just the first-attempt
        success path."""
        cfg = _http_subprocess_cfg()
        startup = _make_startup(
            {"web": cfg}, security_profile=SecurityProfile.PRODUCTION
        )
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
        startup = _make_startup(
            {"web": cfg}, security_profile=SecurityProfile.PRODUCTION
        )
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
            security_profile=SecurityProfile.PRODUCTION,
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
            security_profile=SecurityProfile.PRODUCTION,
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
            security_profile=SecurityProfile.PRODUCTION,
            shutdown_event=shutdown_event,
        )

        result = await startup._start_servers()

        startup._ctx.services_required.lifecycle.start_http_subprocess.assert_called_once_with(
            "web", cfg, shutdown_event=shutdown_event
        )
        assert len(result) == 1


# ── StartupOrchestrator._verify_mcp_health ────────────────────────────────────


class TestStartupVerifyMcpHealth:
    """Tests for StartupOrchestrator._verify_mcp_health()."""

    @pytest.mark.asyncio
    async def test_health_check_passes_for_all_servers(self) -> None:
        cfg = _http_subprocess_cfg()
        startup = _make_startup(
            {"web": cfg}, security_profile=SecurityProfile.PRODUCTION
        )

        mock_resp = _make_http_mock(200)
        mock_client = _AsyncClientMock(get_return=mock_resp)

        with patch(
            "agent.startup_mcp_starter.httpx.AsyncClient", return_value=mock_client
        ):
            await startup._verify_mcp_health()

    @pytest.mark.asyncio
    async def test_health_check_failure_production_raises(self) -> None:
        cfg = _http_subprocess_cfg()
        startup = _make_startup(
            {"web": cfg}, security_profile=SecurityProfile.PRODUCTION
        )

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
        startup = _make_startup(
            {"web": cfg}, security_profile=SecurityProfile.PRODUCTION
        )

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
        startup = _make_startup(
            {"persistent": cfg_persistent}, security_profile=SecurityProfile.PRODUCTION
        )

        with patch("agent.startup_mcp_starter.httpx.AsyncClient") as MockClient:
            await startup._verify_mcp_health()

        MockClient.assert_not_called()

    @pytest.mark.asyncio
    async def test_tools_service_none_raises(self) -> None:
        cfg = _http_subprocess_cfg()
        ctx = MagicMock()
        ctx.cfg.mcp.security_profile = SecurityProfile.PRODUCTION
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
        ctx.cfg.mcp.security_profile = SecurityProfile.PRODUCTION
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
            security_profile=SecurityProfile.PRODUCTION,
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
