"""tests/test_tool_registry_counts.py
Verify that tool registry counts match documented values and config sources.
"""

from __future__ import annotations


class TestRegistryRagPipelineCounts:
    """Intentional drift guard: asserts the fixed tool count for the rag_pipeline server.

    A failing test here means a tool was added to or removed from this server's
    registration — review the change and update the expected count deliberately;
    do not treat this as incidental test flakiness.
    """

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
