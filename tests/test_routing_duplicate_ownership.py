"""Tests for duplicate tool ownership detection in build_discovery_map and check_routing_drift_vs_live."""

from unittest.mock import MagicMock, patch

import pytest
from shared.route_resolver import build_discovery_map

# --- build_discovery_map unit tests ---


def test_no_duplicates():
    server_tool_lists = {
        "srv1": [{"name": "tool_a"}],
        "srv2": [{"name": "tool_b"}],
    }
    route_map, duplicates = build_discovery_map(server_tool_lists)
    assert route_map == {"tool_a": "srv1", "tool_b": "srv2"}
    assert duplicates == {}


def test_duplicate_tool_detected():
    server_tool_lists = {
        "srv1": [{"name": "tool_a"}],
        "srv2": [{"name": "tool_a"}],
    }
    route_map, duplicates = build_discovery_map(server_tool_lists)
    assert "tool_a" in duplicates
    assert sorted(duplicates["tool_a"]) == ["srv1", "srv2"]


def test_duplicate_route_map_uses_first_server():
    server_tool_lists = {
        "srv1": [{"name": "tool_a"}],
        "srv2": [{"name": "tool_a"}],
    }
    route_map, _ = build_discovery_map(server_tool_lists)
    assert route_map["tool_a"] == "srv1"


def test_empty_input():
    route_map, duplicates = build_discovery_map({})
    assert route_map == {}
    assert duplicates == {}


def test_invalid_tool_entry_skipped():
    server_tool_lists = {
        "srv1": [{"name": ""}, {"name": "tool_a"}],
    }
    route_map, duplicates = build_discovery_map(server_tool_lists)
    assert "tool_a" in route_map
    assert "" not in route_map


def test_three_servers_same_tool():
    server_tool_lists = {
        "srv1": [{"name": "tool_a"}],
        "srv2": [{"name": "tool_a"}],
        "srv3": [{"name": "tool_a"}],
    }
    _, duplicates = build_discovery_map(server_tool_lists)
    assert sorted(duplicates["tool_a"]) == ["srv1", "srv2", "srv3"]


# --- check_routing_drift_vs_live integration tests ---


@pytest.mark.asyncio
async def test_check_routing_drift_duplicate_in_warnings():
    from agent.repl_health import check_routing_drift_vs_live
    from shared.tool_registry import (
        ToolDefinition,
        _reset_registry_for_testing,
        get_registry,
    )

    _reset_registry_for_testing()
    get_registry().register(ToolDefinition("tool_a", "srv1"))

    per_server = {"srv1": ["tool_a"], "srv2": ["tool_a"]}

    with patch(
        "agent.repl_health._collect_server_tool_names_per_server",
        return_value=(per_server, []),
    ):
        result = await check_routing_drift_vs_live(MagicMock(), strict=False)

    assert any("tool_a" in w.message for w in result.warnings)


@pytest.mark.asyncio
async def test_check_routing_drift_duplicate_strict_raises():
    from agent.repl_health import check_routing_drift_vs_live
    from shared.tool_registry import (
        ToolDefinition,
        _reset_registry_for_testing,
        get_registry,
    )

    _reset_registry_for_testing()
    get_registry().register(ToolDefinition("tool_a", "srv1"))

    per_server = {"srv1": ["tool_a"], "srv2": ["tool_a"]}

    with patch(
        "agent.repl_health._collect_server_tool_names_per_server",
        return_value=(per_server, []),
    ):
        with pytest.raises(RuntimeError, match="Strict mode.*duplicate"):
            await check_routing_drift_vs_live(MagicMock(), strict=True)


@pytest.mark.asyncio
async def test_check_routing_drift_no_duplicate_no_warning():
    from agent.repl_health import check_routing_drift_vs_live
    from shared.tool_registry import (
        ToolDefinition,
        _reset_registry_for_testing,
        get_registry,
    )

    _reset_registry_for_testing()
    get_registry().register(ToolDefinition("tool_a", "srv1"))

    per_server = {"srv1": ["tool_a"], "srv2": ["tool_b"]}

    with patch(
        "agent.repl_health._collect_server_tool_names_per_server",
        return_value=(per_server, []),
    ):
        result = await check_routing_drift_vs_live(MagicMock(), strict=False)

    assert not any("duplicate" in (w.message or "").lower() for w in result.warnings)
