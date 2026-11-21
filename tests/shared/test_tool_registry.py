"""tests/test_tool_registry.py

Unit tests for shared.tool_registry — registry drift validation.
"""

from __future__ import annotations

import pytest
from shared.tool_registry import (
    ToolDefinition,
    ToolRegistry,
    _reset_registry_for_testing,
    get_registry,
)
from shared.tool_routing_validation import (
    validate_routing_against_live,
)


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
        assert "is registered to server 's1'" in drift["s2"][0]

    def test_tool_in_live_not_in_registry(self) -> None:
        """Tool in live response but not in registry → mismatch."""
        _reset_registry_for_testing()
        registry = get_registry()
        drift = validate_routing_against_live(
            registry, {"rag_pipeline": ["nonexistent_tool"]}
        )
        assert "rag_pipeline" in drift
        assert "is unknown (not registered to any server)" in drift["rag_pipeline"][0]

    def test_tool_in_registry_not_in_live(self) -> None:
        """Tool in registry but not in live → mismatch for all rag_pipeline tools."""
        _reset_registry_for_testing()
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


class TestStartupValidationStrictMode:
    """Tests for the four strict-mode drift conditions checked at startup.

    These tests verify the behavior of validate_routing_against_live() for each
    condition that must be detected.
    """

    def test_live_returns_tool_not_in_registry(self) -> None:
        """Condition 1: live response includes a tool not in the registry.

        validate_routing_against_live() must return a non-empty drift dict.
        """
        registry = ToolRegistry()
        registry.register(ToolDefinition(name="tool_a", server_key="server_x"))
        # live response includes extra_tool not registered anywhere
        drift = validate_routing_against_live(
            registry, {"server_x": ["tool_a", "extra_tool"]}
        )
        assert "server_x" in drift
        assert any("extra_tool" in msg for msg in drift["server_x"])

    def test_live_tool_unknown_message_contains_unknown_keyword(self) -> None:
        """Unknown tool message must contain 'unknown' keyword."""
        registry = ToolRegistry()
        registry.register(ToolDefinition(name="tool_a", server_key="server_x"))
        drift = validate_routing_against_live(
            registry, {"server_x": ["tool_a", "totally_unknown_tool"]}
        )
        assert "server_x" in drift
        assert any(
            "unknown" in msg and "totally_unknown_tool" in msg
            for msg in drift["server_x"]
        )

    def test_live_omits_registry_tool_for_server(self) -> None:
        """Condition 2: registry owns a tool for a server, but live response omits it.

        validate_routing_against_live() must detect the missing tool.
        """
        registry = ToolRegistry()
        registry.register(ToolDefinition(name="tool_a", server_key="server_x"))
        registry.register(ToolDefinition(name="tool_b", server_key="server_x"))
        # live response for server_x is missing tool_b
        drift = validate_routing_against_live(registry, {"server_x": ["tool_a"]})
        assert "server_x" in drift
        assert any("tool_b" in msg for msg in drift["server_x"])

    def test_live_returns_tool_under_wrong_server(self) -> None:
        """Condition 3: registry maps tool_x to server_a, but live returns it under server_b.

        validate_routing_against_live() must report a mismatch for server_b
        (tool present in live but not registered to server_b) and for server_a
        (tool registered to server_a but absent from its live response).
        """
        registry = ToolRegistry()
        registry.register(ToolDefinition(name="tool_x", server_key="server_a"))
        # server_a live response is empty (omits tool_x)
        # server_b live response includes tool_x (wrong server)
        drift = validate_routing_against_live(
            registry,
            {"server_a": [], "server_b": ["tool_x"]},
        )
        # server_b: tool_x in live but not in registry for server_b
        assert "server_b" in drift
        assert any("tool_x" in msg for msg in drift["server_b"])
        # server_a: tool_x in registry but not in live
        assert "server_a" in drift
        assert any("tool_x" in msg for msg in drift["server_a"])

    def test_live_tool_wrong_owner_message_names_owner(self) -> None:
        """Wrong-owner tool message must contain the actual registry owner."""
        registry = ToolRegistry()
        registry.register(ToolDefinition(name="tool_x", server_key="server_a"))
        drift = validate_routing_against_live(
            registry,
            {"server_a": [], "server_b": ["tool_x"]},
        )
        assert "server_b" in drift
        assert any("server_a" in msg and "tool_x" in msg for msg in drift["server_b"])


class TestAllToolConstantsFrozensetsRegistered:
    def test_all_tool_constants_frozensets_are_registered(self) -> None:
        """Every tool named in every tool_constants.py frozenset is in the registry.

        Complements the fixed-count tests in tests/test_tool_registry_counts.py: two independent
        additions/removals could cancel out a count check numerically without this membership
        check catching the actual drift.
        """
        from shared.tool_constants import (
            CICD_TOOLS,
            DELETE_TOOLS,
            GIT_TOOLS,
            GITHUB_TOOLS,
            MDQ_TOOLS,
            RAG_TOOLS,
            READ_TOOLS,
            SHELL_TOOLS,
            WEB_SEARCH_TOOLS,
            WRITE_TOOLS,
        )

        registry = get_registry()
        all_expected = (
            CICD_TOOLS
            | DELETE_TOOLS
            | GIT_TOOLS
            | GITHUB_TOOLS
            | MDQ_TOOLS
            | RAG_TOOLS
            | READ_TOOLS
            | SHELL_TOOLS
            | WEB_SEARCH_TOOLS
            | WRITE_TOOLS
        )
        assert all_expected <= registry.get_all_tool_names()


class TestGetToolNamesOrdering:
    def test_get_tool_names_returns_sorted_order(self) -> None:
        registry = ToolRegistry()
        registry.register(ToolDefinition(name="zebra", server_key="s1"))
        registry.register(ToolDefinition(name="apple", server_key="s1"))
        registry.register(ToolDefinition(name="mango", server_key="s1"))
        assert registry.get_tool_names("s1") == ["apple", "mango", "zebra"]
