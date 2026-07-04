"""tests/test_tool_constants.py
Unit tests for shared/tool_constants.py: canonical tool classification sets.
"""

from __future__ import annotations

from shared.tool_constants import (
    CICD_TOOLS,
    DELETE_TOOLS,
    GIT_READ_TOOLS,
    GIT_TOOLS,
    GIT_WRITE_TOOLS,
    GITHUB_DANGEROUS_TOOLS,
    GITHUB_READ_TOOLS,
    GITHUB_TOOLS,
    GITHUB_WRITE_TOOLS,
    MDQ_TOOLS,
    RAG_TOOLS,
    READ_TOOLS,
    SHELL_TOOLS,
    SQLITE_TOOLS,
    WEB_SEARCH_TOOLS,
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
            "rag_list_documents",
            "rag_delete_document",
        }
        assert RAG_TOOLS == expected
        assert len(RAG_TOOLS) == 4

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
            "fts_consistency_check",
            "fts_rebuild",
        }
        assert MDQ_TOOLS == expected
        assert len(MDQ_TOOLS) == 9

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
        all_tools: set[str] = set()

        for tools_set in [
            READ_TOOLS,
            WRITE_TOOLS,
            DELETE_TOOLS,
            RAG_TOOLS,
            CICD_TOOLS,
            MDQ_TOOLS,
            GIT_TOOLS,
            SHELL_TOOLS,
            SQLITE_TOOLS,
            WEB_SEARCH_TOOLS,
        ]:
            # Check for overlaps within each set (should be empty)
            overlaps = all_tools & tools_set
            assert not overlaps, f"Overlaps found: {overlaps}"

            # Add to overall set
            all_tools.update(tools_set)

        # Total should be 45 tools (all frozensets; github-mcp uses prefix routing separately)
        assert len(all_tools) == 45

    def test_all_tools_are_strings(self) -> None:
        """Ensure all items in tool sets are strings."""
        for name, tools_set in [
            ("READ_TOOLS", READ_TOOLS),
            ("WRITE_TOOLS", WRITE_TOOLS),
            ("DELETE_TOOLS", DELETE_TOOLS),
            ("RAG_TOOLS", RAG_TOOLS),
            ("CICD_TOOLS", CICD_TOOLS),
            ("MDQ_TOOLS", MDQ_TOOLS),
            ("GIT_TOOLS", GIT_TOOLS),
        ]:
            for tool_name in tools_set:
                assert isinstance(tool_name, str), (
                    f"{name} contains non-string: {tool_name}"
                )


class TestGitToolClassification:
    def test_git_tools_is_union_of_read_and_write(self) -> None:
        assert GIT_TOOLS == GIT_READ_TOOLS | GIT_WRITE_TOOLS

    def test_git_read_write_are_disjoint(self) -> None:
        assert GIT_READ_TOOLS.isdisjoint(GIT_WRITE_TOOLS)

    def test_git_read_tools_not_side_effect(self) -> None:
        from shared.tool_executor_helpers import is_side_effect

        for tool in GIT_READ_TOOLS:
            assert not is_side_effect(tool), f"{tool!r} should not be a side-effect"

    def test_git_write_tools_are_side_effect(self) -> None:
        from shared.tool_executor_helpers import is_side_effect

        for tool in GIT_WRITE_TOOLS:
            assert is_side_effect(tool), f"{tool!r} should be a side-effect"


class TestGithubToolClassification:
    def test_github_tools_is_union_of_sub_sets(self) -> None:
        assert (
            GITHUB_TOOLS
            == GITHUB_READ_TOOLS | GITHUB_WRITE_TOOLS | GITHUB_DANGEROUS_TOOLS
        )

    def test_github_sub_sets_are_pairwise_disjoint(self) -> None:
        assert GITHUB_READ_TOOLS.isdisjoint(GITHUB_WRITE_TOOLS)
        assert GITHUB_READ_TOOLS.isdisjoint(GITHUB_DANGEROUS_TOOLS)
        assert GITHUB_WRITE_TOOLS.isdisjoint(GITHUB_DANGEROUS_TOOLS)

    def test_github_read_tools_not_side_effect(self) -> None:
        from shared.tool_executor_helpers import is_side_effect

        for tool in GITHUB_READ_TOOLS:
            assert not is_side_effect(tool), f"{tool!r} should not be a side-effect"

    def test_github_write_tools_are_side_effect(self) -> None:
        from shared.tool_executor_helpers import is_side_effect

        for tool in GITHUB_WRITE_TOOLS:
            assert is_side_effect(tool), f"{tool!r} should be a side-effect"

    def test_github_dangerous_tools_are_side_effect(self) -> None:
        from shared.tool_executor_helpers import is_side_effect

        for tool in GITHUB_DANGEROUS_TOOLS:
            assert is_side_effect(tool), f"{tool!r} should be a side-effect"
