#!/usr/bin/env python3
"""Tests for MDQ tool metadata consistency (routing, safety tiers, tool definitions)."""

from __future__ import annotations

from pathlib import Path

import pytest
from shared.tool_constants import MDQ_TOOLS


class TestMdqToolsCount:
    """Verify MDQ_TOOLS contains exactly 9 expected tools."""

    def test_mdq_tools_count(self) -> None:
        assert len(MDQ_TOOLS) == 9

    def test_mdq_tools_exact_names(self) -> None:
        expected = {
            "search_docs",
            "get_chunk",
            "outline",
            "index_paths",
            "refresh_index",
            "stats",
            "grep_docs",
            "fts_consistency_check",
            "fts_rebuild",
        }
        assert MDQ_TOOLS == expected


class TestMdqNoUnmappedTools:
    """Verify no MDQ tool is accidentally unmapped across config, registry, and live sources."""

    def test_mdq_tools_mapped_to_server_key(self) -> None:
        from shared.route_resolver import _SET_ROUTES

        for tool_name in MDQ_TOOLS:
            found = False
            for entry in _SET_ROUTES:
                if tool_name in entry.tool_set:
                    assert entry.server_key == "mdq", (
                        f"Tool '{tool_name}' is not mapped to 'mdq' server key, got '{entry.server_key}'"
                    )
                    found = True
                    break
            assert found, f"Tool '{tool_name}' not found in any _SET_ROUTES entry"

    def test_mdq_tools_in_registry(self) -> None:
        from shared.tool_registry import get_registry

        registry = get_registry()
        for tool_name in MDQ_TOOLS:
            server_key = registry.get_server_for_tool(tool_name)
            assert server_key == "mdq", (
                f"Tool '{tool_name}' not mapped to 'mdq' in registry, got '{server_key}'"
            )

    def test_mdq_tools_match_server_definition(self) -> None:
        from mcp.mdq.tools import _MCP_TOOLS

        server_tool_names = {t["name"] for t in _MCP_TOOLS}
        assert MDQ_TOOLS == server_tool_names, (
            f"MDQ_TOOLS mismatch with _MCP_TOOLS:\n"
            f"  Missing from _MCP_TOOLS: {MDQ_TOOLS - server_tool_names}\n"
            f"  Extra in _MCP_TOOLS: {server_tool_names - MDQ_TOOLS}"
        )


class TestMdqSafetyTiers:
    """Verify safety tiers classify MDQ tools correctly (read-only vs WRITE_DANGEROUS)."""

    def test_mdq_read_only_tools(self) -> None:
        read_only = {"search_docs", "get_chunk", "outline", "stats", "grep_docs"}
        assert MDQ_TOOLS & read_only == read_only, (
            f"Expected read-only tools not classified as READ_ONLY:\n"
            f"  {read_only - MDQ_TOOLS}"
        )

    def test_mdq_write_dangerous_tools(self) -> None:
        write_dangerous = {"index_paths", "refresh_index"}
        assert MDQ_TOOLS & write_dangerous == write_dangerous, (
            f"Expected WRITE_DANGEROUS tools not classified:\n"
            f"  {write_dangerous - MDQ_TOOLS}"
        )

    def test_mdq_safety_tiers_from_config(self) -> None:
        """Verify agent.toml has mdq entry in tool_safety_tiers."""
        import tomllib

        agent_toml_path = Path(__file__).parent.parent / "config" / "agent.toml"
        if not agent_toml_path.exists():
            pytest.skip("agent.toml not found")
        with open(agent_toml_path, "rb") as f:
            agent_config = tomllib.load(f)

        safety_tiers = agent_config.get("tool_safety_tiers", {})
        assert "mdq" in safety_tiers, "mdq not in agent.toml [tool_safety_tiers]"
        assert safety_tiers["mdq"] == "WRITE_DANGEROUS", (
            f"mdq should be WRITE_DANGEROUS, got {safety_tiers['mdq']}"
        )
