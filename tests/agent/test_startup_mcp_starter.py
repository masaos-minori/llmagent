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
