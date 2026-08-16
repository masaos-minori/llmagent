"""tests/mcp_servers/mdq/test_audit_target.py

Characterization tests for `extract_audit_target`
(scripts/mcp_servers/mdq/audit_target.py).

Locks the current mapping of MDQ tool name + args to the human-readable
audit-log "target" string, including the 80-char truncation behavior and
the empty-string fallbacks, ahead of a structural (no-behavior-change)
refactor of the module. Added because pre-refactor coverage on
audit_target.py was 79% (missing: get_chunk, stats, and the unknown-tool
default branch) — below the 80% behavior-lock threshold for this
refactor cycle.
"""

from __future__ import annotations

from mcp_servers.mdq.audit_target import extract_audit_target


class TestSearchDocs:
    def test_query_only(self) -> None:
        assert extract_audit_target("search_docs", {"query": "hello"}) == "hello"

    def test_query_with_path_prefix(self) -> None:
        result = extract_audit_target(
            "search_docs", {"query": "hello", "path_prefix": "docs/"}
        )
        assert result == "hello + docs/"

    def test_missing_query_defaults_to_empty(self) -> None:
        assert extract_audit_target("search_docs", {}) == ""


class TestGetChunk:
    def test_returns_chunk_id(self) -> None:
        assert extract_audit_target("get_chunk", {"chunk_id": "abc123"}) == "abc123"

    def test_truncates_to_80_chars(self) -> None:
        long_id = "x" * 200
        result = extract_audit_target("get_chunk", {"chunk_id": long_id})
        assert result == "x" * 80
        assert len(result) == 80

    def test_missing_chunk_id_defaults_to_empty(self) -> None:
        assert extract_audit_target("get_chunk", {}) == ""


class TestOutline:
    def test_returns_path(self) -> None:
        assert extract_audit_target("outline", {"path": "a/b.md"}) == "a/b.md"

    def test_truncates_to_80_chars(self) -> None:
        long_path = "y" * 200
        result = extract_audit_target("outline", {"path": long_path})
        assert result == "y" * 80


class TestIndexPathsAndRefreshIndex:
    def test_index_paths_returns_first_path(self) -> None:
        result = extract_audit_target("index_paths", {"paths": ["/a.md", "/b.md"]})
        assert result == "/a.md"

    def test_refresh_index_returns_first_path(self) -> None:
        result = extract_audit_target("refresh_index", {"paths": ["/c.md", "/d.md"]})
        assert result == "/c.md"

    def test_empty_paths_list_returns_empty(self) -> None:
        assert extract_audit_target("index_paths", {"paths": []}) == ""

    def test_missing_paths_defaults_to_empty(self) -> None:
        assert extract_audit_target("refresh_index", {}) == ""

    def test_first_path_truncated_to_80_chars(self) -> None:
        long_path = "z" * 200
        result = extract_audit_target("index_paths", {"paths": [long_path]})
        assert result == "z" * 80


class TestGrepDocs:
    def test_returns_pattern(self) -> None:
        assert extract_audit_target("grep_docs", {"pattern": "TODO"}) == "TODO"

    def test_truncates_to_80_chars(self) -> None:
        long_pattern = "p" * 200
        result = extract_audit_target("grep_docs", {"pattern": long_pattern})
        assert result == "p" * 80

    def test_missing_pattern_defaults_to_empty(self) -> None:
        assert extract_audit_target("grep_docs", {}) == ""


class TestStats:
    def test_returns_fixed_label(self) -> None:
        assert extract_audit_target("stats", {}) == "mdq-mcp"

    def test_ignores_args(self) -> None:
        assert extract_audit_target("stats", {"anything": "ignored"}) == "mdq-mcp"


class TestUnknownToolName:
    def test_unknown_tool_returns_empty_string(self) -> None:
        assert extract_audit_target("not_a_real_tool", {"query": "hello"}) == ""

    def test_empty_tool_name_returns_empty_string(self) -> None:
        assert extract_audit_target("", {}) == ""
