"""tests/test_tool_constants.py
Unit tests for shared/tool_constants.py: canonical tool classification sets.
"""

from __future__ import annotations

from shared.tool_constants import (
    CICD_TOOLS,
    DELETE_TOOLS,
    GIT_TOOLS,
    MDQ_TOOLS,
    RAG_TOOLS,
    READ_TOOLS,
    WRITE_TOOLS,
)


class TestToolConstants:
    def test_read_tools(self) -> None:
        expected = {
            "list_directory",
            "list_directory_with_sizes",
            "directory_tree",
            "read_text_file",
            "read_media_file",
            "read_multiple_files",
            "search_files",
            "grep_files",
            "get_file_info",
        }
        assert READ_TOOLS == expected
        assert len(READ_TOOLS) == 9

    def test_write_tools(self) -> None:
        expected = {
            "write_file",
            "edit_file",
            "create_directory",
            "move_file",
        }
        assert WRITE_TOOLS == expected
        assert len(WRITE_TOOLS) == 4

    def test_delete_tools(self) -> None:
        expected = {
            "delete_file",
            "delete_directory",
        }
        assert DELETE_TOOLS == expected
        assert len(DELETE_TOOLS) == 2

    def test_rag_tools(self) -> None:
        expected = {
            "rag_run_pipeline",
            "rag_debug_pipeline",
        }
        assert RAG_TOOLS == expected
        assert len(RAG_TOOLS) == 2

    def test_cicd_tools(self) -> None:
        expected = {
            "trigger_workflow",
            "get_workflow_runs",
            "get_workflow_status",
            "get_workflow_logs",
        }
        assert CICD_TOOLS == expected
        assert len(CICD_TOOLS) == 4

    def test_mdq_tools(self) -> None:
        expected = {
            "search_docs",
            "get_chunk",
            "outline",
            "index_paths",
            "refresh_index",
            "stats",
            "grep_docs",
        }
        assert MDQ_TOOLS == expected
        assert len(MDQ_TOOLS) == 7

    def test_git_tools(self) -> None:
        expected = {
            "git_status",
            "git_log",
            "git_diff",
            "git_branch",
            "git_show",
            "git_add",
            "git_commit",
            "git_checkout",
            "git_pull",
            "git_push",
        }
        assert GIT_TOOLS == expected
        assert len(GIT_TOOLS) == 10

    def test_no_overlapping_tools(self) -> None:
        """Ensure no tool appears in multiple categories."""
        all_tools = set()
        
        for tools_set in [READ_TOOLS, WRITE_TOOLS, DELETE_TOOLS, RAG_TOOLS, 
                         CICD_TOOLS, MDQ_TOOLS, GIT_TOOLS]:
            # Check for overlaps within each set (should be empty)
            overlaps = all_tools & tools_set
            assert not overlaps, f"Overlaps found: {overlaps}"
            
            # Add to overall set
            all_tools.update(tools_set)
        
        # Total should be 38 tools (sum of individual sets)
        assert len(all_tools) == 38

    def test_all_tools_are_strings(self) -> None:
        """Ensure all items in tool sets are strings."""
        for name, tools_set in [
            ("READ_TOOLS", READ_TOOLS),
            ("WRITE_TOOLS", WRITE_TOOLS), 
            ("DELETE_TOOLS", DELETE_TOOLS),
            ("RAG_TOOLS", RAG_TOOLS),
            ("CICD_TOOLS", CICD_TOOLS),
            ("MDQ_TOOLS", MDQ_TOOLS),
            ("GIT_TOOLS", GIT_TOOLS)
        ]:
            for tool_name in tools_set:
                assert isinstance(tool_name, str), f"{name} contains non-string: {tool_name}"