"""tests/test_rag_tools_consistency.py
Consistency tests for RAG MCP tools across schema, discovery, and registry.
"""

import pytest
from shared.route_resolver import ToolRouteResolver
from shared.tool_constants import RAG_TOOLS
from shared.tool_registry import ToolRegistry


class TestRagToolsInRegistry:
    """Verify RAG MCP tools are registered in ToolRegistry."""

    def _get_rag_tools_in_registry(self) -> set[str]:
        resolver = ToolRouteResolver(
            server_configs={},
            discovery_map=None,
            strict_mode=False,
        )
        return set(resolver._registry.get_all_tool_names())

    def test_rag_run_pipeline_registered(self) -> None:
        tools = self._get_rag_tools_in_registry()
        assert "rag_run_pipeline" in tools

    def test_rag_debug_pipeline_registered(self) -> None:
        tools = self._get_rag_tools_in_registry()
        assert "rag_debug_pipeline" in tools

    def test_rag_list_documents_registered(self) -> None:
        tools = self._get_rag_tools_in_registry()
        assert "rag_list_documents" in tools

    def test_rag_delete_document_registered(self) -> None:
        tools = self._get_rag_tools_in_registry()
        assert "rag_delete_document" in tools

    def test_all_rag_tools_registered(self) -> None:
        """Every tool in RAG_TOOLS must be in the registry."""
        tools = self._get_rag_tools_in_registry()
        for tool_name in RAG_TOOLS:
            assert tool_name in tools, f"RAG tool {tool_name!r} not in ToolRegistry"

    def test_rag_tools_resolve_without_fallback(self) -> None:
        """RAG tools must resolve via registry, not static fallback."""
        resolver = ToolRouteResolver(
            server_configs={},
            discovery_map=None,
            strict_mode=False,
        )
        for tool_name in RAG_TOOLS:
            server_key = resolver.resolve(tool_name)
            assert server_key == "rag_pipeline", (
                f"RAG tool {tool_name!r} resolved to {server_key!r}, expected 'rag_pipeline'"
            )

    def test_rag_tools_not_in_other_set(self) -> None:
        """RAG tools must not be in READ_TOOLS, WRITE_TOOLS, or DELETE_TOOLS."""
        from shared.tool_constants import READ_TOOLS, WRITE_TOOLS, DELETE_TOOLS

        for tool_name in RAG_TOOLS:
            assert tool_name not in READ_TOOLS, f"{tool_name!r} should not be in READ_TOOLS"
            assert tool_name not in WRITE_TOOLS, f"{tool_name!r} should not be in WRITE_TOOLS"
            assert tool_name not in DELETE_TOOLS, f"{tool_name!r} should not be in DELETE_TOOLS"
