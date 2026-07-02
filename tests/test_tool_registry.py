"""tests/test_tool_registry.py

Unit tests for shared.tool_registry — registry drift validation.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from shared.mcp_config import McpServerConfig
from shared.tool_registry import (
    ToolDefinition,
    ToolRegistry,
    get_registry,
    reset_registry,
    validate_all_routing,
    validate_routing_against_config,
    validate_routing_against_live,
)


class TestValidateRoutingDriftRegistry:
    """Tests for validate_routing_against_config drift detection."""

    def test_no_drift_when_config_matches_registry(self) -> None:
        """validate_routing_against_config returns {} when config tool_names are in the registry."""
        registry = ToolRegistry()
        registry.register(ToolDefinition(name="read_text_file", server_key="file_read"))
        registry.register(ToolDefinition(name="list_directory", server_key="file_read"))

        cfg = MagicMock(spec=McpServerConfig)
        cfg.tool_names = ["read_text_file", "list_directory"]
        server_configs = {"file_read": cfg}

        result = validate_routing_against_config(
            registry=registry, server_configs=server_configs
        )
        assert result == {}

    def test_drift_detected_when_config_has_unregistered_tool(self) -> None:
        """validate_routing_against_config returns mismatch when config lists a tool not in registry."""
        registry = ToolRegistry()
        registry.register(ToolDefinition(name="read_text_file", server_key="file_read"))

        cfg = MagicMock(spec=McpServerConfig)
        cfg.tool_names = ["read_text_file", "missing_tool"]
        server_configs = {"file_read": cfg}

        result = validate_routing_against_config(
            registry=registry, server_configs=server_configs
        )
        assert "file_read" in result
        assert any("missing_tool" in msg for msg in result["file_read"])

    def test_no_drift_when_config_tool_names_empty(self) -> None:
        """validate_routing_against_config skips servers with empty tool_names."""
        cfg = MagicMock(spec=McpServerConfig)
        cfg.tool_names = []
        server_configs = {"some_server": cfg}

        result = validate_routing_against_config(server_configs=server_configs)
        assert result == {}


class TestDuplicateOwnershipRejection:
    """Tests for duplicate tool ownership rejection."""

    def test_duplicate_raises_value_error(self) -> None:
        """Registering the same tool name twice raises ValueError."""
        registry = ToolRegistry()
        registry.register(ToolDefinition(name="tool_a", server_key="s1"))
        with pytest.raises(ValueError, match=r"already registered"):
            registry.register(ToolDefinition(name="tool_a", server_key="s2"))


class TestValidateRoutingAgainstLive:
    """Tests for validate_routing_against_live drift detection."""

    def test_no_drift_when_live_matches_registry(self) -> None:
        """Live list identical to registry → empty dict."""
        registry = ToolRegistry()
        registry.register(ToolDefinition(name="tool_a", server_key="s1"))
        drift = validate_routing_against_live(registry, {"s1": ["tool_a"]})
        assert drift == {}

    def test_owner_mismatch_detected(self) -> None:
        """Tool registered to s1 but live response comes from s2 → mismatch."""
        registry = ToolRegistry()
        registry.register(ToolDefinition(name="x", server_key="s1"))
        drift = validate_routing_against_live(registry, {"s2": ["x"]})
        assert "s2" in drift
        assert "'x' in live response but not in registry" in drift["s2"][0]

    def test_tool_in_live_not_in_registry(self) -> None:
        """Tool in live response but not in registry → mismatch."""
        reset_registry()
        registry = get_registry()
        drift = validate_routing_against_live(registry, {"rag_pipeline": ["nonexistent_tool"]})
        assert "rag_pipeline" in drift
        assert "'nonexistent_tool' in live response but not in registry" in drift["rag_pipeline"][0]

    def test_tool_in_registry_not_in_live(self) -> None:
        """Tool in registry but not in live → mismatch for all rag_pipeline tools."""
        reset_registry()
        registry = get_registry()
        drift = validate_routing_against_live(registry, {"rag_pipeline": []})
        assert "rag_pipeline" in drift
        # All 4 rag_pipeline tools should be listed as missing from live
        assert len(drift["rag_pipeline"]) == 4

    def test_returns_empty_when_live_is_none(self) -> None:
        """None input → empty dict."""
        registry = ToolRegistry()
        drift = validate_routing_against_live(registry, None)
        assert drift == {}


class TestValidateAllRouting:
    """Tests for validate_all_routing drift detection."""

    def test_merges_config_and_live_results(self) -> None:
        """Both config and live have drift for same server key → merged."""
        reset_registry()
        cfg = MagicMock(spec=McpServerConfig)
        cfg.tool_names = ["existing_tool"]  # drift: not in registry
        server_configs = {"rag_pipeline": cfg}
        live_tool_lists = {"rag_pipeline": ["nonexistent_tool"]}  # drift: in live but not registry

        result = validate_all_routing(server_configs, live_tool_lists)
        assert "rag_pipeline" in result
        # Both config drift and live drift messages present
        assert len(result["rag_pipeline"]) >= 2

    def test_empty_when_both_inputs_none(self) -> None:
        """No inputs → empty dict."""
        result = validate_all_routing()
        assert result == {}
