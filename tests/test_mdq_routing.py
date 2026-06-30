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

    def test_mdq_production_tools_count(self) -> None:
        """_MCP_TOOLS should have exactly 7 production-status tools."""
        from mcp.mdq.tools import _MCP_TOOLS

        production_tools = [t for t in _MCP_TOOLS if t.get("status") == "production"]
        assert len(production_tools) == 7, (
            f"Expected 7 production tools, got {len(production_tools)}: "
            f"{[t['name'] for t in production_tools]}"
        )

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
        from shared.tool_registry import get_registry

        registry = get_registry()
        for tool_name in MDQ_TOOLS:
            server_key = registry.get_server_for_tool(tool_name)
            assert server_key == "mdq", (
                f"Tool '{tool_name}' is not mapped to 'mdq' server key, got '{server_key}'"
            )

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

    def test_write_tools_contains_expected(self) -> None:
        """_WRITE_TOOLS frozenset should contain only index_paths and refresh_index."""
        from mcp.mdq.tools import _WRITE_TOOLS

        assert _WRITE_TOOLS == frozenset({"index_paths", "refresh_index"}), (
            f"_WRITE_TOOLS should be {{index_paths, refresh_index}}, got {_WRITE_TOOLS}"
        )

    def test_read_only_not_in_write_tools(self) -> None:
        """Read-only tools must not appear in _WRITE_TOOLS."""
        from mcp.mdq.tools import _WRITE_TOOLS

        read_only = {"search_docs", "get_chunk", "outline", "stats", "grep_docs"}
        overlap = read_only & _WRITE_TOOLS
        assert not overlap, f"Read-only tools found in _WRITE_TOOLS: {overlap}"

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


class TestMdqMCPServerConformance:
    """Verify MdqMCPServer conforms to MCPServer base class contract."""

    def test_server_key_class_attribute(self) -> None:
        from mcp.mdq.server import MdqMCPServer

        assert hasattr(MdqMCPServer, "server_key"), (
            "MdqMCPServer missing server_key class attribute"
        )
        assert MdqMCPServer.server_key == "mdq", (
            f"MdqMCPServer.server_key should be 'mdq', got '{MdqMCPServer.server_key}'"
        )

    def test_http_host_class_attribute(self) -> None:
        from mcp.mdq.server import MdqMCPServer

        assert hasattr(MdqMCPServer, "http_host"), (
            "MdqMCPServer missing http_host class attribute"
        )
        assert MdqMCPServer.http_host == "127.0.0.1", (
            f"MdqMCPServer.http_host should be '127.0.0.1', got '{MdqMCPServer.http_host}'"
        )

    def test_list_tools_with_server_key(self) -> None:
        from mcp.mdq.server import MdqMCPServer

        server = MdqMCPServer()
        tools = server.list_tools_with_server_key()
        for tool in tools:
            assert tool.get("server_key") == "mdq", (
                f"Tool '{tool['name']}' missing server_key='mdq', got '{tool.get('server_key')}'"
            )

    def test_dispatch_method_exists(self) -> None:
        from mcp.mdq.server import MdqMCPServer

        server = MdqMCPServer()
        assert hasattr(server, "dispatch"), "MdqMCPServer missing dispatch method"
        assert callable(server.dispatch), "MdqMCPServer.dispatch is not callable"

    def test_health_method_returns_standard_shape(self) -> None:
        from mcp.mdq.server import MdqMCPServer

        server = MdqMCPServer()
        health, status_code = server.health()
        assert isinstance(health, dict), "health() should return a dict"
        assert "status" in health, "health() missing 'status' key"
        assert "ready" in health, "health() missing 'ready' key"
        assert "dependencies" in health, "health() missing 'dependencies' key"
        assert "details" in health, "health() missing 'details' key"
        assert isinstance(health["ready"], bool), "health()['ready'] should be bool"
        assert status_code == 200, (
            f"Expected HTTP 200 for healthy server, got {status_code}"
        )

    def test_list_tools_returns_tool_names(self) -> None:
        from mcp.mdq.server import MdqMCPServer

        server = MdqMCPServer()
        tool_names = server.list_tools()
        assert isinstance(tool_names, list), "list_tools() should return a list"
        for name in tool_names:
            assert isinstance(name, str), f"Tool name should be str, got {type(name)}"


class TestMdqV1ToolsEndpoint:
    """Verify GET /v1/tools HTTP endpoint returns expected tool definitions."""

    def test_v1_tools_returns_all_tools(self) -> None:
        """GET /v1/tools should return all 9 MDQ tools."""
        from fastapi.testclient import TestClient
        from mcp.mdq.server import app

        client = TestClient(app)
        response = client.get("/v1/tools")
        assert response.status_code == 200
        body = response.json()
        assert "tools" in body
        assert len(body["tools"]) == 9

    def test_v1_tools_names_match_mdq_tools(self) -> None:
        """Tool names in GET /v1/tools must match MDQ_TOOLS."""
        from fastapi.testclient import TestClient
        from mcp.mdq.server import app

        client = TestClient(app)
        response = client.get("/v1/tools")
        assert response.status_code == 200
        tool_names = {t["name"] for t in response.json()["tools"]}
        assert tool_names == MDQ_TOOLS, (
            f"Missing: {MDQ_TOOLS - tool_names}, Extra: {tool_names - MDQ_TOOLS}"
        )

    def test_v1_tools_includes_server_key(self) -> None:
        """Each tool in GET /v1/tools must include server_key='mdq'."""
        from fastapi.testclient import TestClient
        from mcp.mdq.server import app

        client = TestClient(app)
        response = client.get("/v1/tools")
        assert response.status_code == 200
        for tool in response.json()["tools"]:
            assert tool.get("server_key") == "mdq", (
                f"Tool '{tool['name']}' missing server_key='mdq'"
            )
