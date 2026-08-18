"""Tests for routing drift strict mode and safety tier checks."""

from unittest.mock import MagicMock

import pytest
from shared.tool_registry import (
    ToolDefinition,
    ToolRegistry,
    _reset_registry_for_testing,
    get_registry,
)
from shared.tool_routing_validation import check_tool_safety_tiers


def _make_ctx(tool_names=None, safety_tiers=None):
    ctx = MagicMock()
    cfg = MagicMock()
    server = MagicMock()
    server.tool_names = tool_names or ["tool_a", "tool_b"]
    cfg.mcp.mcp_servers = {"srv1": server}
    cfg.tool.routing_drift_strict = False
    cfg.approval.tool_safety_tiers = safety_tiers or {}
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
    from agent.repl_health import check_routing_drift

    ctx = _make_ctx(tool_names=["tool_a", "tool_b"])
    msgs = check_routing_drift(ctx, strict=False)
    assert len(msgs) > 0
    assert any("tool_b" in m for m in msgs)


def test_routing_drift_strict_raises():
    _reset_registry_for_testing()
    registry = get_registry()
    registry.register(ToolDefinition("tool_a", "srv1"))
    from agent.repl_health import check_routing_drift

    ctx = _make_ctx(tool_names=["tool_a", "tool_b"])
    with pytest.raises(RuntimeError, match="Strict mode"):
        check_routing_drift(ctx, strict=True)


def test_routing_drift_no_drift_returns_empty():
    _reset_registry_for_testing()
    registry = get_registry()
    registry.register(ToolDefinition("tool_a", "srv1"))
    from agent.repl_health import check_routing_drift

    ctx = _make_ctx(tool_names=["tool_a"])
    msgs = check_routing_drift(ctx, strict=True)
    assert msgs == []


# --- check_tool_safety_tiers ---


def test_safety_tiers_missing_tools_reported():
    registry = ToolRegistry()
    registry.register(ToolDefinition("tool_a", "srv1"))
    registry.register(ToolDefinition("tool_b", "srv1"))
    msgs = check_tool_safety_tiers(
        registry=registry, tool_safety_tiers={"tool_a": "READ_ONLY"}
    )
    assert len(msgs) == 1
    assert "tool_b" in msgs[0]


def test_safety_tiers_all_present_returns_empty():
    registry = ToolRegistry()
    registry.register(ToolDefinition("tool_a", "srv1"))
    msgs = check_tool_safety_tiers(
        registry=registry, tool_safety_tiers={"tool_a": "READ_ONLY"}
    )
    assert msgs == []


def test_safety_tiers_empty_config_skips_check():
    registry = ToolRegistry()
    registry.register(ToolDefinition("tool_a", "srv1"))
    msgs = check_tool_safety_tiers(registry=registry, tool_safety_tiers={})
    assert msgs == []


# --- check_routing_safety_tiers integration ---


def test_check_routing_safety_tiers_context():
    from agent.repl_health import check_routing_safety_tiers

    ctx = _make_ctx(safety_tiers={})  # empty = no check
    msgs = check_routing_safety_tiers(ctx)
    assert msgs == []
