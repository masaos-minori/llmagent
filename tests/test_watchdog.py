"""tests/test_watchdog.py

Unit tests for watchdog restart gating logic and early-exit fix.

Requires Steps 4 (probe helper), 5 (watchdog check), and 6 (loop fix) to be applied.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from agent.repl_health import _watchdog_check_http, watchdog_loop
from agent.shared.health_models import McpHealthProbeResult


def _make_ctx(*, watchdog_interval: float = 30.0) -> MagicMock:
    """Build a minimal AgentContext mock."""
    ctx = MagicMock()
    ctx.cfg.mcp.mcp_watchdog_interval = watchdog_interval
    ctx.cfg.mcp.mcp_watchdog_max_restarts = 3
    ctx.cfg.mcp.mcp_servers = {}
    ctx.services_required.http = AsyncMock()
    ctx.services_required.lifecycle = AsyncMock()
    ctx.services_required.lifecycle.restart = AsyncMock()
    ctx.services_required.health_registry = None
    ctx.services_required.lifecycle.shutdown_idle = AsyncMock()
    return ctx


def _make_srv_cfg(
    *, url: str = "http://localhost:8000", startup_mode: str = "subprocess"
) -> MagicMock:
    srv_cfg = MagicMock()
    srv_cfg.url = url
    srv_cfg.startup_mode = startup_mode
    srv_cfg.transport = "http"
    return srv_cfg


# ── _watchdog_check_http() ────────────────────────────────────────────────────


class TestWatchdogCheckHttp:
    @pytest.mark.asyncio
    async def test_restart_called_when_503_and_restart_recommended(self) -> None:
        """HTTP 503 + restart_recommended=True triggers lifecycle.restart()."""
        ctx = _make_ctx()
        srv_cfg = _make_srv_cfg()
        restart_counts: dict[str, int] = {}

        probe_result = McpHealthProbeResult(
            reachable=True,
            status_code=503,
            restart_recommended=True,
            operator_action_required=False,
            body={"status": "degraded", "ready": False, "restart_recommended": True},
        )
        with patch(
            "agent.repl_health._probe_mcp_health_detail",
            new=AsyncMock(return_value=probe_result),
        ):
            await _watchdog_check_http(
                ctx, "test-server", srv_cfg, restart_counts, max_restarts=3
            )

        ctx.services_required.lifecycle.restart.assert_called_once_with("test-server")

    @pytest.mark.asyncio
    async def test_restart_not_called_when_503_and_restart_not_recommended(
        self,
    ) -> None:
        """HTTP 503 + restart_recommended=False: lifecycle.restart() must NOT be called."""
        ctx = _make_ctx()
        srv_cfg = _make_srv_cfg()
        restart_counts: dict[str, int] = {}

        probe_result = McpHealthProbeResult(
            reachable=True,
            status_code=503,
            restart_recommended=False,
            operator_action_required=True,
            body={
                "status": "degraded",
                "ready": False,
                "restart_recommended": False,
                "operator_action_required": True,
            },
        )
        with patch(
            "agent.repl_health._probe_mcp_health_detail",
            new=AsyncMock(return_value=probe_result),
        ):
            await _watchdog_check_http(
                ctx, "test-server", srv_cfg, restart_counts, max_restarts=3
            )

        ctx.services_required.lifecycle.restart.assert_not_called()

    @pytest.mark.asyncio
    async def test_restart_not_called_when_200_and_ready_false_in_body(self) -> None:
        """HTTP 200 with ready=False in body and restart_recommended=False: no restart."""
        ctx = _make_ctx()
        srv_cfg = _make_srv_cfg()
        restart_counts: dict[str, int] = {}

        probe_result = McpHealthProbeResult(
            reachable=True,
            status_code=200,
            restart_recommended=False,
            operator_action_required=False,
            body={"status": "ok", "ready": False, "restart_recommended": False},
        )
        with patch(
            "agent.repl_health._probe_mcp_health_detail",
            new=AsyncMock(return_value=probe_result),
        ):
            await _watchdog_check_http(
                ctx, "test-server", srv_cfg, restart_counts, max_restarts=3
            )

        ctx.services_required.lifecycle.restart.assert_not_called()


# ── watchdog_loop() ───────────────────────────────────────────────────────────


class TestWatchdogLoop:
    @pytest.mark.asyncio
    async def test_disabled_interval_returns_immediately_without_sleeping(self) -> None:
        """watchdog_loop() with interval=0 returns without sleeping."""
        ctx = _make_ctx(watchdog_interval=0)

        with patch("agent.repl_health.asyncio.sleep", new=AsyncMock()) as mock_sleep:
            await watchdog_loop(ctx)

        mock_sleep.assert_not_called()
