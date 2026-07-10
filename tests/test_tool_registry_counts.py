"""tests/test_tool_registry_counts.py
Verify that tool registry counts match documented values and config sources.
"""

from __future__ import annotations


class TestRegistryRagPipelineCounts:
    def test_registry_rag_pipeline_tool_count(self) -> None:
        """rag_pipeline server has exactly 4 tools registered."""
        from shared.tool_registry import _reset_registry_for_testing, get_registry

        _reset_registry_for_testing()
        registry = get_registry()
        rag_tools = registry.get_tool_names("rag_pipeline")
        assert len(rag_tools) == 4, f"Expected 4 rag_pipeline tools, got {rag_tools}"

    def test_rag_tools_all_in_registry(self) -> None:
        """Each name in RAG_TOOLS maps to server_key 'rag_pipeline'."""
        from shared.tool_constants import RAG_TOOLS
        from shared.tool_registry import _reset_registry_for_testing, get_registry

        _reset_registry_for_testing()
        registry = get_registry()
        for tool_name in RAG_TOOLS:
            key = registry.get_server_for_tool(tool_name)
            assert key == "rag_pipeline", (
                f"Expected {tool_name!r} -> 'rag_pipeline', got {key!r}"
            )

    def test_rag_list_documents_registered(self) -> None:
        """rag_list_documents is registered to rag_pipeline."""
        from shared.tool_registry import _reset_registry_for_testing, get_registry

        _reset_registry_for_testing()
        registry = get_registry()
        assert registry.get_server_for_tool("rag_list_documents") == "rag_pipeline"

    def test_rag_delete_document_registered(self) -> None:
        """rag_delete_document is registered to rag_pipeline."""
        from shared.tool_registry import _reset_registry_for_testing, get_registry

        _reset_registry_for_testing()
        registry = get_registry()
        assert registry.get_server_for_tool("rag_delete_document") == "rag_pipeline"


class TestRegistryTotalCounts:
    def test_registry_total_tool_count(self) -> None:
        """Registry has exactly 65 tools (all GitHub MCP tools registered explicitly)."""
        from shared.tool_registry import _reset_registry_for_testing, get_registry

        _reset_registry_for_testing()
        registry = get_registry()
        all_tools = registry.get_all_tool_names()
        assert len(all_tools) == 65, (
            f"Expected 65 total registry tools, got {len(all_tools)}"
        )

    def test_github_tools_count(self) -> None:
        """Registry has exactly 21 GitHub MCP tools."""
        from shared.tool_registry import get_registry

        registry = get_registry()
        github_tools = registry.get_tool_names("github")
        assert len(github_tools) == 21, (
            f"Expected 21 GitHub tools, got {len(github_tools)}"
        )

    def test_mcp_tools_module_count(self) -> None:
        """TOOL_LIST list in mcp_servers.rag_pipeline.tools has exactly 4 tools."""
        from mcp_servers.rag_pipeline.tools import TOOL_LIST

        assert len(TOOL_LIST) == 4, (
            f"Expected 4 TOOL_LIST entries, got {len(TOOL_LIST)}"
        )
