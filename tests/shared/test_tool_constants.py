"""tests/test_tool_constants.py
Unit tests for shared/tool_constants.py: reference-data tool-name sets and
cross-source drift detection.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

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


class TestRagToolClassification:
    def test_rag_tools_is_union_of_read_and_write(self) -> None:
        assert RAG_TOOLS == RAG_READ_TOOLS | RAG_WRITE_TOOLS

    def test_rag_read_write_are_disjoint(self) -> None:
        assert RAG_READ_TOOLS.isdisjoint(RAG_WRITE_TOOLS)


class TestRetryClassDriftConsistency:
    """Cross-source drift detection: RETRYABLE_TOOLS is reference data, not the
    retry-classification owner (the declared `retry_policy` field is the
    authority). This test compares the reference data against the declarations
    in config/mcp_dedup.toml [retry_class] and reports any drift between the
    two. Parsed with tomllib directly (not load_dedup_config) so the two source
    artifacts are compared independently of the loader gate.
    """

    _CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "mcp_dedup.toml"

    def _retry_class_map(self) -> dict[str, str]:
        data = tomllib.loads(self._CONFIG_PATH.read_text(encoding="utf-8"))
        return data["retry_class"]

    def test_retryable_keys_equal_retryable_tools(self) -> None:
        retry_keys = {k for k, v in self._retry_class_map().items() if v == "retryable"}
        assert retry_keys == set(RETRYABLE_TOOLS)

    def test_every_key_is_a_known_tool_name(self) -> None:
        unknown = set(self._retry_class_map()) - set(get_all_mcp_tool_names())
        assert not unknown, f"unknown [retry_class] keys: {unknown}"

    def test_non_retryable_keys_outside_retryable_tools(self) -> None:
        contradicted = {
            k
            for k, v in self._retry_class_map().items()
            if v == "non_retryable" and k in RETRYABLE_TOOLS
        }
        assert not contradicted, f"contradicted keys: {contradicted}"
