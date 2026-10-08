"""Tests for routing drift strict mode checks."""

from unittest.mock import MagicMock

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
