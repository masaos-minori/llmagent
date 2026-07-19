"""Tests for duplicate tool ownership detection in build_discovery_map."""

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
