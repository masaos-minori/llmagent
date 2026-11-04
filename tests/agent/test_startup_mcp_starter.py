"""Tests for routing drift strict mode checks."""

from unittest.mock import MagicMock, patch

import pytest
from agent.services.routing_drift import check_routing_drift
from shared.tool_registry import (
    ToolDefinition,
    _reset_registry_for_testing,
    get_registry,
)


def _make_ctx(tool_names=None):
    ctx = MagicMock()
    cfg = MagicMock()
    server = MagicMock()
    server.tool_names = tool_names or ["tool_a", "tool_b"]
    cfg.mcp.mcp_servers = {"srv1": server}
    cfg.tool.routing_drift_strict = False
    ctx.cfg = cfg
    return ctx


def setup_function():
    _reset_registry_for_testing()


# --- check_routing_drift strict mode ---


def test_routing_drift_non_strict_returns_warnings():
    _reset_registry_for_testing()
    registry = get_registry()
    registry.register(ToolDefinition("tool_a", "srv1"))
    # tool_b in config but not in registry -> drift
    ctx = _make_ctx(tool_names=["tool_a", "tool_b"])
    msgs = check_routing_drift(ctx, strict=False)
    assert len(msgs) > 0
    assert any("tool_b" in m for m in msgs)


def test_routing_drift_strict_raises():
    _reset_registry_for_testing()
    registry = get_registry()
    registry.register(ToolDefinition("tool_a", "srv1"))
    ctx = _make_ctx(tool_names=["tool_a", "tool_b"])
    with pytest.raises(RuntimeError, match="Strict mode"):
        check_routing_drift(ctx, strict=True)


def test_routing_drift_no_drift_returns_empty():
    _reset_registry_for_testing()
    registry = get_registry()
    registry.register(ToolDefinition("tool_a", "srv1"))
    ctx = _make_ctx(tool_names=["tool_a"])
    msgs = check_routing_drift(ctx, strict=True)
    assert msgs == []


def test_routing_drift_unexpected_error_propagates_when_non_strict():
    ctx = _make_ctx()
    with patch(
        "shared.tool_routing_validation.validate_routing_against_config",
        side_effect=ValueError("boom"),
    ):
        with pytest.raises(ValueError, match="boom"):
            check_routing_drift(ctx, strict=False)


def test_routing_drift_unexpected_error_propagates_when_strict():
    ctx = _make_ctx()
    with patch(
        "shared.tool_routing_validation.validate_routing_against_config",
        side_effect=ValueError("boom"),
    ):
        # An unexpected failure must not be disguised as the strict-mode drift error.
        with pytest.raises(ValueError, match="boom"):
            check_routing_drift(ctx, strict=True)


# --- post-startup health verification sends the Bearer token ---


def _auth_handler(token: str):
    import httpx

    def _handler(request: httpx.Request) -> httpx.Response:
        if request.headers.get("Authorization") == f"Bearer {token}":
            return httpx.Response(200, json={"status": "ok"})
        return httpx.Response(401, json={"error": "Unauthorized"})

    return _handler


def _starter_ctx(token: str):
    from shared.mcp_config import McpServerConfig, StartupMode, TransportType

    ctx = MagicMock()
    cfg = McpServerConfig(
        transport=TransportType.HTTP,
        url="http://localhost:9999",
        startup_mode=StartupMode.SUBPROCESS,
        cmd=["python", "server.py"],
        auth_token=token,
    )
    ctx.cfg.mcp.mcp_servers = {"srv": cfg}
    ctx.services_required.tools = MagicMock()
    ctx.services_required.lifecycle = MagicMock()
    return ctx, cfg


@pytest.mark.asyncio
async def test_verify_health_passes_with_correct_token():
    import respx
    from agent.startup_mcp_starter import McpServerStarter

    ctx, _ = _starter_ctx("s3cret")
    starter = McpServerStarter(ctx, MagicMock())
    with respx.mock as router:
        route = router.get("http://localhost:9999/health").mock(
            side_effect=_auth_handler("s3cret")
        )
        await starter.verify_health()
    assert route.call_count == 1


@pytest.mark.asyncio
async def test_verify_single_health_fails_with_wrong_token():
    import respx
    from agent.startup_mcp_starter import McpServerStarter

    ctx, cfg = _starter_ctx("wrong")
    starter = McpServerStarter(ctx, MagicMock())
    with respx.mock as router:
        router.get("http://localhost:9999/health").mock(
            side_effect=_auth_handler("s3cret")
        )
        with pytest.raises(RuntimeError, match="HTTP 401"):
            await starter._verify_single_health("srv", cfg)


@pytest.mark.asyncio
async def test_verify_single_health_degraded_but_live_does_not_raise():
    import httpx
    import respx
    from agent.startup_mcp_starter import McpServerStarter

    ctx, _ = _starter_ctx("s3cret")
    starter = McpServerStarter(ctx, MagicMock())
    with respx.mock as router:
        router.get("http://localhost:9999/health").mock(
            return_value=httpx.Response(
                503,
                json={"liveness": True},
                headers={"content-type": "application/json"},
            )
        )
        # Must not raise: degraded-but-live is treated as ready.
        await starter._verify_single_health("srv", ctx.cfg.mcp.mcp_servers["srv"])


@pytest.mark.asyncio
async def test_verify_single_health_degraded_but_live_false_raises():
    import httpx
    import respx
    from agent.startup_mcp_starter import McpServerStarter

    ctx, cfg = _starter_ctx("s3cret")
    starter = McpServerStarter(ctx, MagicMock())
    with respx.mock as router:
        router.get("http://localhost:9999/health").mock(
            return_value=httpx.Response(
                503,
                json={"liveness": False},
                headers={"content-type": "application/json"},
            )
        )
        with pytest.raises(RuntimeError, match="HTTP 503"):
            await starter._verify_single_health("srv", cfg)


@pytest.mark.asyncio
async def test_verify_single_health_non_503_non_200_raises():
    import httpx
    import respx
    from agent.startup_mcp_starter import McpServerStarter

    ctx, cfg = _starter_ctx("s3cret")
    starter = McpServerStarter(ctx, MagicMock())
    with respx.mock as router:
        router.get("http://localhost:9999/health").mock(
            return_value=httpx.Response(401, json={"error": "Unauthorized"})
        )
        with pytest.raises(RuntimeError, match="HTTP 401"):
            await starter._verify_single_health("srv", cfg)


# --- startup retry reaches the subprocess layer a second time (real router) ---


def _real_router_ctx(failures):
    """Build a real ``McpServerStarter`` around a real router with only the subprocess layer faked.

    *failures* is a list of exceptions; the fake HTTP manager's ``start`` raises them in order
    for the first ``len(failures)`` calls and records a single fake ``Popen`` afterwards.
    Returns ``(ctx, router, fake_http_mgr, proc)``.
    """
    import subprocess
    from unittest.mock import AsyncMock, MagicMock

    from agent.lifecycle_router import _ServerLifecycleRouter
    from shared.mcp_config import McpServerConfig, StartupMode, TransportType

    cfg = McpServerConfig(
        transport=TransportType.HTTP,
        url="http://localhost:9999",
        auth_token="test-token",
        startup_mode=StartupMode.SUBPROCESS,
        cmd=["python", "server.py"],
    )
    router = _ServerLifecycleRouter({"srv": cfg}, MagicMock())
    fake_http_mgr = AsyncMock()
    fake_http_mgr._http_procs = {}
    proc = MagicMock(spec=subprocess.Popen)
    fake_http_mgr._http_procs["srv"] = proc
    router._subprocess_mgr._http_mgr = fake_http_mgr

    state = {"n": 0}

    async def _start(server_key, config, shutdown_event=None):
        state["n"] += 1
        if state["n"] <= len(failures):
            raise failures[state["n"] - 1]
        fake_http_mgr._http_procs[server_key] = proc
        return None

    fake_http_mgr.start = AsyncMock(side_effect=_start)

    ctx = MagicMock()
    ctx.services_required.tools = MagicMock()
    ctx.services_required.lifecycle = router
    ctx.cfg.mcp.mcp_servers = {"srv": cfg}
    return ctx, router, fake_http_mgr, proc


class TestStartupRetryWithRealRouter:
    """Integration-style: real router + real starter, only the subprocess layer faked."""

    @pytest.mark.asyncio
    async def test_first_failure_then_success_launches_second_attempt(self) -> None:
        from agent.http_lifecycle_errors import HttpStartupError, StartupFailure
        from agent.lifecycle import LifecycleState
        from agent.startup_mcp_starter import McpServerStarter

        ctx, router, fake_http_mgr, proc = _real_router_ctx(
            [HttpStartupError(StartupFailure("srv", "port busy", ""))]
        )
        with patch("agent.startup_mcp_starter.RETRY_DELAY_SEC", 0.0):
            started = await McpServerStarter(ctx, MagicMock()).start_servers()

        assert started == [proc]
        assert fake_http_mgr.start.await_count == 2
        assert router.get_transport_state("srv") == LifecycleState.RUNNING
        assert "srv" not in router._failed_starts

    @pytest.mark.asyncio
    async def test_two_failures_abort_with_named_error_and_visible_first_failure(
        self,
    ) -> None:
        from agent.http_lifecycle_errors import HttpStartupError, StartupFailure
        from agent.startup_mcp_starter import McpServerStarter

        # Three failures: the start entry makes three subprocess-layer calls
        # (initial attempt + retry helper's execute-and-retry); the retry helper
        # swallows its first attempt and only aborts on its second.
        ctx, router, fake_http_mgr, _proc = _real_router_ctx(
            [
                HttpStartupError(StartupFailure("srv", "first reason", "")),
                HttpStartupError(StartupFailure("srv", "second reason", "")),
                HttpStartupError(StartupFailure("srv", "third reason", "")),
            ]
        )
        with (
            patch("agent.startup_mcp_starter.RETRY_DELAY_SEC", 0.0),
            patch("agent.startup_mcp_starter.logger") as patched_logger,
        ):
            with pytest.raises(HttpStartupError) as excinfo:
                await McpServerStarter(ctx, MagicMock()).start_servers()

        text = str(excinfo.value)
        assert "srv" in text
        assert "third reason" in text
        assert fake_http_mgr.start.await_count == 3
        assert isinstance(excinfo.value.__cause__, HttpStartupError)
        warning_calls = [c for c in patched_logger.warning.call_args_list if c.args]
        assert warning_calls, "first failure must be logged at WARNING"
        first_call = warning_calls[0]
        assert "First attempt failed" in first_call.args[0]
        joined = " ".join(str(a) for a in first_call.args)
        assert "srv" in joined
        assert "first reason" in joined

    @pytest.mark.asyncio
    async def test_shutdown_suppressed_start_raises_startup_interrupted(self) -> None:
        from unittest.mock import AsyncMock

        from agent.startup import StartupInterrupted
        from agent.startup_mcp_starter import McpServerStarter

        ctx, router, fake_http_mgr, _proc = _real_router_ctx([])
        fake_http_mgr.shutdown_all = AsyncMock(return_value=[])
        await router.shutdown_all()

        with pytest.raises(StartupInterrupted):
            await McpServerStarter(ctx, MagicMock()).start_servers()

        fake_http_mgr.start.assert_not_called()
