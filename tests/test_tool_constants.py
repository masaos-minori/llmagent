"""tests/test_tool_constants.py
Unit tests for shared/tool_constants.py: canonical tool classification sets.
"""

from __future__ import annotations

from shared.tool_constants import (
    CICD_TOOLS,
    CICD_WRITE_TOOLS,
    DELETE_TOOLS,
    GIT_READ_TOOLS,
    GIT_TOOLS,
    GIT_WRITE_TOOLS,
    GITHUB_DANGEROUS_TOOLS,
    GITHUB_READ_TOOLS,
    GITHUB_TOOLS,
    GITHUB_WRITE_TOOLS,
    MDQ_TOOLS,
    MDQ_WRITE_TOOLS,
    RAG_READ_TOOLS,
    RAG_TOOLS,
    RAG_WRITE_TOOLS,
    READ_TOOLS,
    SHELL_TOOLS,
    WEB_SEARCH_TOOLS,
    WRITE_TOOLS,
)


class TestToolConstants:
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
            WEB_SEARCH_TOOLS,
        ]:
            # Check for overlaps within each set (should be empty)
            overlaps = all_tools & tools_set
            assert not overlaps, f"Overlaps found: {overlaps}"

            # Add to overall set
            all_tools.update(tools_set)

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


class TestCicdToolClassification:
    def test_cicd_write_tools_are_side_effect(self) -> None:
        from shared.tool_executor_helpers import is_side_effect

        for tool in CICD_WRITE_TOOLS:
            assert is_side_effect(tool), f"{tool!r} should be a side-effect"


class TestRagToolClassification:
    def test_rag_tools_is_union_of_read_and_write(self) -> None:
        assert RAG_TOOLS == RAG_READ_TOOLS | RAG_WRITE_TOOLS

    def test_rag_read_write_are_disjoint(self) -> None:
        assert RAG_READ_TOOLS.isdisjoint(RAG_WRITE_TOOLS)

    def test_rag_read_tools_not_side_effect(self) -> None:
        from shared.tool_executor_helpers import is_side_effect

        for tool in RAG_READ_TOOLS:
            assert not is_side_effect(tool), f"{tool!r} should not be a side-effect"

    def test_rag_write_tools_are_side_effect(self) -> None:
        from shared.tool_executor_helpers import is_side_effect

        for tool in RAG_WRITE_TOOLS:
            assert is_side_effect(tool), f"{tool!r} should be a side-effect"


class TestMdqToolClassification:
    def test_mdq_write_tools_are_side_effect(self) -> None:
        from shared.tool_executor_helpers import is_side_effect

        for tool in MDQ_WRITE_TOOLS:
            assert is_side_effect(tool), f"{tool!r} should be a side-effect"
