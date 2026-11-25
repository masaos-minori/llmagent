"""tests/test_tool_constants.py
Unit tests for shared/tool_constants.py: reference-data tool-name sets and
cross-source drift detection.
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
    RAG_READ_TOOLS,
    RAG_TOOLS,
    RAG_WRITE_TOOLS,
    READ_TOOLS,
    RETRYABLE_TOOLS,
    SHELL_TOOLS,
    WEB_SEARCH_TOOLS,
    WRITE_TOOLS,
    get_all_mcp_tool_names,
)
from shared.tool_metadata import retry_policy_is_retryable


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

    def test_no_github_tool_is_retryable(self) -> None:
        assert GITHUB_TOOLS.isdisjoint(RETRYABLE_TOOLS)


class TestRagToolClassification:
    def test_rag_tools_is_union_of_read_and_write(self) -> None:
        assert RAG_TOOLS == RAG_READ_TOOLS | RAG_WRITE_TOOLS

    def test_rag_read_write_are_disjoint(self) -> None:
        assert RAG_READ_TOOLS.isdisjoint(RAG_WRITE_TOOLS)


class TestRetryClassDriftConsistency:
    """Cross-source drift detection: RETRYABLE_TOOLS is reference data, not the
    retry-classification owner (the declared `retry_policy` field is the
    authority, mcpdl003 REQ-005). This test compares the reference data against
    the retry_policy declarations in the ten TOOL_LIST modules and reports any
    drift between the two. Parsed directly (no dispatcher globals) so the two
    source artifacts are compared independently.
    """

    _TOOL_LIST_MODULES = (
        "mcp_servers.cicd.cicd_tools",
        "mcp_servers.file.delete_tools",
        "mcp_servers.file.read_tools",
        "mcp_servers.file.write_tools",
        "mcp_servers.git.git_tools",
        "mcp_servers.github.github_tools",
        "mcp_servers.mdq.mdq_tools",
        "mcp_servers.rag_pipeline.rag_pipeline_tools",
        "mcp_servers.shell.shell_tools",
        "mcp_servers.web_search.web_search_tools",
    )

    def _declared_policies(self) -> dict[str, str]:
        from importlib import import_module

        policies: dict[str, str] = {}
        for name in self._TOOL_LIST_MODULES:
            for entry in getattr(import_module(name), "TOOL_LIST", ()):
                policies[str(entry["name"])] = str(entry["retry_policy"])
        return policies

    def test_retryable_reference_equals_declared_retryable(self) -> None:
        declared = {
            name
            for name, policy in self._declared_policies().items()
            if retry_policy_is_retryable(policy)
        }
        assert declared == set(RETRYABLE_TOOLS)

    def test_every_declaration_is_a_known_tool_name(self) -> None:
        unknown = set(self._declared_policies()) - set(get_all_mcp_tool_names())
        assert not unknown, f"unknown retry_policy declarations: {unknown}"

    def test_declared_non_retryable_outside_retryable_tools(self) -> None:
        contradicted = {
            name
            for name, policy in self._declared_policies().items()
            if not retry_policy_is_retryable(policy) and name in RETRYABLE_TOOLS
        }
        assert not contradicted, f"contradicted names: {contradicted}"
