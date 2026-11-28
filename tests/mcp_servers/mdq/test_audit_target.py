"""tests/mcp_servers/mdq/test_audit_target.py

Characterization tests for `extract_audit_target`
(scripts/mcp_servers/mdq/audit_target.py) after the REQ-006 redaction change.

The target is a redacted value, not the raw argument:

- query, regex, and opaque chunk identifiers are hashed with `hash_query_value()`;
- a path inside an authorized root is the root-relative identifier, and a path outside
  one is the hash form, so no absolute path and no configured root name is persisted;
- the 80-character truncation is gone, since a hashed or relative value cannot leak a
  prefix of a customer path.

Roots are supplied by the caller (the service's authorized roots), so each test passes
them explicitly rather than reading configuration.
"""

from __future__ import annotations

from mcp_servers.audit import hash_query_value, path_identifier
from mcp_servers.mdq.audit_target import extract_audit_target

ROOT = "/opt/llm/docs"


class TestSearchDocs:
    def test_query_only(self) -> None:
        query = "hello"
        assert extract_audit_target("search_docs", {"query": query}, [ROOT]) == (
            hash_query_value(query)
        )

    def test_query_with_path_prefix(self) -> None:
        query = "hello"
        result = extract_audit_target(
            "search_docs", {"query": query, "path_prefix": ROOT + "/sub/"}, [ROOT]
        )
        # The prefix is normalized textually, so the persisted form is the root-relative
        # identifier without its trailing separator.
        assert result == f"{hash_query_value(query)} + sub"

    def test_path_prefix_outside_the_root_is_hashed(self) -> None:
        prefix = "customer-name/"
        result = extract_audit_target(
            "search_docs", {"query": "hello", "path_prefix": prefix}, [ROOT]
        )
        assert (
            result
            == f"{hash_query_value('hello')} + {hash_query_value('customer-name')}"
        )
        assert "customer-name" not in result

    def test_missing_query_defaults_to_empty(self) -> None:
        assert extract_audit_target("search_docs", {}, [ROOT]) == ""

    def test_no_root_keeps_the_target_hashed(self) -> None:
        # Fail closed: without an authorized root nothing comparable to the raw value is emitted.
        result = extract_audit_target("search_docs", {"query": "hello"}, [])
        assert len(result) == 16


class TestGetChunk:
    def test_returns_hashed_chunk_id(self) -> None:
        chunk_id = "abc123"
        assert extract_audit_target("get_chunk", {"chunk_id": chunk_id}, [ROOT]) == (
            hash_query_value(chunk_id)
        )

    def test_long_chunk_id_is_hashed_not_truncated(self) -> None:
        long_id = "x" * 200
        result = extract_audit_target("get_chunk", {"chunk_id": long_id}, [ROOT])
        assert result == hash_query_value(long_id)
        assert len(result) == 16, (
            "a truncated prefix would still leak the beginning of the value"
        )

    def test_missing_chunk_id_defaults_to_empty_hash(self) -> None:
        assert extract_audit_target("get_chunk", {}, [ROOT]) == ""

    def test_same_chunk_id_hashes_equally_across_calls(self) -> None:
        assert extract_audit_target("get_chunk", {"chunk_id": "abc123"}, [ROOT]) == (
            extract_audit_target("get_chunk", {"chunk_id": "abc123"}, [ROOT])
        )


class TestOutline:
    def test_path_inside_a_root_is_root_relative(self) -> None:
        assert (
            extract_audit_target("outline", {"path": f"{ROOT}/a/b.md"}, [ROOT])
            == "a/b.md"
        )

    def test_path_outside_a_root_is_hashed(self) -> None:
        outside = "/etc/passwd"
        result = extract_audit_target("outline", {"path": outside}, [ROOT])
        assert result == hash_query_value(outside)
        assert "passwd" not in result

    def test_long_path_is_not_truncated(self) -> None:
        long_path = f"{ROOT}/" + "y" * 200 + ".md"
        result = extract_audit_target("outline", {"path": long_path}, [ROOT])
        assert result == "y" * 200 + ".md"
        assert ROOT not in result

    def test_missing_path_defaults_to_empty_hash(self) -> None:
        assert extract_audit_target("outline", {}, [ROOT]) == ""


class TestIndexPathsAndRefreshIndex:
    def test_index_paths_returns_the_first_path_relative_to_its_root(self) -> None:
        paths = [f"{ROOT}/a.md", f"{ROOT}/b.md"]
        assert extract_audit_target("index_paths", {"paths": paths}, [ROOT]) == "a.md"

    def test_refresh_index_returns_the_first_path_relative_to_its_root(self) -> None:
        paths = [f"{ROOT}/c.md", f"{ROOT}/d.md"]
        assert extract_audit_target("refresh_index", {"paths": paths}, [ROOT]) == "c.md"

    def test_first_path_outside_a_root_is_hashed(self) -> None:
        path = "/srv/customer-name/report.md"
        result = extract_audit_target("index_paths", {"paths": [path]}, [ROOT])
        assert result == path_identifier(path, [ROOT])
        assert "customer-name" not in result

    def test_empty_paths_list_returns_empty(self) -> None:
        assert extract_audit_target("index_paths", {"paths": []}, [ROOT]) == ""

    def test_missing_paths_defaults_to_empty(self) -> None:
        assert extract_audit_target("refresh_index", {}, [ROOT]) == ""

    def test_long_path_is_not_truncated(self) -> None:
        long_path = "z" * 200
        result = extract_audit_target("index_paths", {"paths": [long_path]}, [ROOT])
        assert result == path_identifier(long_path, [ROOT])
        assert len(result) == 16


class TestGrepDocs:
    def test_returns_hashed_pattern(self) -> None:
        pattern = "TODO"
        assert extract_audit_target("grep_docs", {"pattern": pattern}, [ROOT]) == (
            hash_query_value(pattern)
        )

    def test_long_pattern_is_hashed_not_truncated(self) -> None:
        long_pattern = "p" * 200
        result = extract_audit_target("grep_docs", {"pattern": long_pattern}, [ROOT])
        assert result == hash_query_value(long_pattern)
        assert len(result) == 16

    def test_missing_pattern_defaults_to_empty_hash(self) -> None:
        assert extract_audit_target("grep_docs", {}, [ROOT]) == ""

    def test_regex_with_a_customer_name_does_not_appear_in_the_target(self) -> None:
        pattern = "customer-name.*secret"
        result = extract_audit_target("grep_docs", {"pattern": pattern}, [ROOT])
        assert "customer-name" not in result
        assert "secret" not in result


class TestStats:
    def test_returns_fixed_label(self) -> None:
        assert extract_audit_target("stats", {}, [ROOT]) == "mdq-mcp"

    def test_ignores_args(self) -> None:
        assert (
            extract_audit_target("stats", {"anything": "ignored"}, [ROOT]) == "mdq-mcp"
        )


class TestUnknownToolName:
    def test_unknown_tool_returns_empty_string(self) -> None:
        assert extract_audit_target("not_a_real_tool", {"query": "hello"}, [ROOT]) == ""

    def test_empty_tool_name_returns_empty_string(self) -> None:
        assert extract_audit_target("", {}, [ROOT]) == ""
