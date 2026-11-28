"""tests/mcp_servers/mdq/test_search.py

Query-boundary characterization tests for scripts/mcp_servers/mdq/search.py: the
authorized-source predicate applied before `COUNT`, ranking, and `LIMIT`, exact path
and tag semantics, cause-based error classification, and the hashed query identifier.
The pre-refactor coverage gaps in `_build_search_where`'s `path_prefix` /
`heading_prefix` filters and `_search_docs_structured`'s exception-handling branches
are kept as behavior locks. Source:
issues/20261119-142124_mdqmcp002_mdq-search-query-boundary.md.

Updated 20261128 for REQ-003: the generic `OperationalError` branch no longer swallows a
malformed FTS5 query into a successful zero-result response; the behavior change is
intentional, so the assertion moved from "swallowed" to "classified as validation error".
"""

from __future__ import annotations

import asyncio
import logging
import os
import sqlite3
from pathlib import Path
from tempfile import mkstemp

import pytest
from mcp_servers.audit import hash_query_value
from mcp_servers.mdq.indexer import index_paths
from mcp_servers.mdq.mdq_error_codes import code_for_exception
from mcp_servers.mdq.mdq_models import (
    IndexPathsRequest,
    MdqAuthorizationError,
    MdqConsistencyError,
    MdqValidationError,
    SearchDocsRequest,
)
from mcp_servers.mdq.mdq_service import MdqService
from mcp_servers.mdq.search import (
    _search_docs_structured,
    classify_sqlite_error,
    search_docs,
)

from tests.mcp_servers.mdq._startup import make_startup


@pytest.fixture
def service(tmp_path: Path) -> MdqService:
    """MdqService with a temp DB path and tmp_path in allowed_dirs."""
    fd, db = mkstemp(suffix=".db", dir=str(tmp_path))
    try:
        svc = MdqService(make_startup(db))
        svc._allowed_dirs = [str(tmp_path)]
        return svc
    finally:
        os.close(fd)


class TestPathPrefixFilter:
    def test_path_prefix_narrows_results_to_matching_directory(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        dir_a = tmp_path / "dir_a"
        dir_b = tmp_path / "dir_b"
        dir_a.mkdir()
        dir_b.mkdir()
        (dir_a / "doc.md").write_text(
            "# Title A\n\nSharedKeyword content.", encoding="utf-8"
        )
        (dir_b / "doc.md").write_text(
            "# Title B\n\nSharedKeyword content.", encoding="utf-8"
        )
        asyncio.run(
            index_paths(service, IndexPathsRequest(paths=[str(dir_a), str(dir_b)]))
        )

        result = _search_docs_structured(
            service,
            SearchDocsRequest(query="SharedKeyword", path_prefix=str(dir_a)),
        )

        assert len(result["results"]) == 1
        assert result["results"][0].source_path.startswith(str(dir_a))

    def test_no_path_prefix_returns_all_matches(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        dir_a = tmp_path / "dir_a2"
        dir_b = tmp_path / "dir_b2"
        dir_a.mkdir()
        dir_b.mkdir()
        (dir_a / "doc.md").write_text(
            "# Title A\n\nOtherKeyword content.", encoding="utf-8"
        )
        (dir_b / "doc.md").write_text(
            "# Title B\n\nOtherKeyword content.", encoding="utf-8"
        )
        asyncio.run(
            index_paths(service, IndexPathsRequest(paths=[str(dir_a), str(dir_b)]))
        )

        result = _search_docs_structured(
            service, SearchDocsRequest(query="OtherKeyword")
        )

        assert len(result["results"]) == 2


class TestHeadingPrefixFilter:
    def test_heading_prefix_narrows_results_to_matching_heading(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        # heading_path stores only the *ancestor* chain (see parser.py), so a
        # bare top-level "# Heading" has an empty heading_path — nest a child
        # heading under each top-level section to get a distinguishing,
        # non-empty heading_path to filter on.
        f = tmp_path / "headings.md"
        f.write_text(
            "# Alpha Section\n\n## Detail\n\nMatchKeyword in alpha.\n\n"
            "# Beta Section\n\n## Detail\n\nMatchKeyword in beta.\n",
            encoding="utf-8",
        )
        asyncio.run(index_paths(service, IndexPathsRequest(paths=[str(f)])))

        result = _search_docs_structured(
            service,
            SearchDocsRequest(query="MatchKeyword", heading_prefix="Alpha"),
        )

        assert len(result["results"]) == 1
        assert result["results"][0].heading_path.startswith("Alpha")


class TestPathAndTagFilterSemantics:
    def test_wildcard_characters_in_path_prefix_do_not_broaden_scope(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        """`%` and `_` are data in a path filter, not wildcards (REQ-001): a row in a
        sibling directory that only matches the prefix pattern must stay outside the scope."""
        literal = tmp_path / "wild%card"
        pattern_match = tmp_path / "wildXcard"
        literal.mkdir()
        pattern_match.mkdir()
        (literal / "a.md").write_text(
            "# Literal\n\nWildcardProbe content.", encoding="utf-8"
        )
        (pattern_match / "b.md").write_text(
            "# PatternMatch\n\nWildcardProbe content.", encoding="utf-8"
        )
        asyncio.run(index_paths(service, IndexPathsRequest(paths=[str(tmp_path)])))

        result = _search_docs_structured(
            service, SearchDocsRequest(query="WildcardProbe", path_prefix=str(literal))
        )

        assert result["matched_count"] == 1
        assert len(result["results"]) == 1
        assert result["results"][0].source_path.startswith(str(literal))

    def test_path_prefix_outside_the_allowlist_is_refused_before_the_query(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        """A path filter is authorized before the query is built, not applied afterwards."""
        root = tmp_path / "root"
        root.mkdir()
        service._allowed_dirs = [str(root)]

        # `tmp_path` is the parent of the authorized root, so it is outside the allowlist.
        with pytest.raises(MdqAuthorizationError):
            _search_docs_structured(
                service, SearchDocsRequest(query="Keyword", path_prefix=str(tmp_path))
            )

    def test_tag_filter_matches_exact_values_only(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        """A similar tag value must not match: `json_each()` compares whole values."""
        exact = tmp_path / "exact.md"
        similar = tmp_path / "similar.md"
        exact.write_text(
            "---\ntags: [important]\n---\n\n# Exact\n\nTagProbe content.",
            encoding="utf-8",
        )
        similar.write_text(
            "---\ntags: [importantly]\n---\n\n# Similar\n\nTagProbe content.",
            encoding="utf-8",
        )
        asyncio.run(index_paths(service, IndexPathsRequest(paths=[str(tmp_path)])))

        result = _search_docs_structured(
            service, SearchDocsRequest(query="TagProbe", tag_filter=["important"])
        )

        assert result["matched_count"] == 1
        assert len(result["results"]) == 1
        assert result["results"][0].heading == "Exact"


class TestClassificationByCause:
    """A SQLite failure resolves to a code from the closed vocabulary by cause (REQ-003)."""

    def _error_connection(
        self, service: MdqService, monkeypatch: pytest.MonkeyPatch, error: sqlite3.Error
    ) -> None:
        """Route the search statement through a connection that raises `error`.

        Pragmas still run on the real connection, so the error surfaces on the query itself,
        which is what the classification branch sees.
        """

        class _ErrorConnection(sqlite3.Connection):
            def execute(self, sql: str, parameters: object = ()) -> sqlite3.Cursor:
                if not sql.strip().upper().startswith("PRAGMA"):
                    raise error
                return super().execute(sql, parameters)

        conn = _ErrorConnection(service.db_path)
        monkeypatch.setattr(sqlite3, "connect", lambda *args, **kwargs: conn)

    def test_malformed_fts_syntax_is_a_validation_error(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        """Behavior change recorded 20261128: a malformed FTS5 MATCH query (an
        unterminated quote) is reported as a validation error instead of being swallowed
        into a successful zero-result response."""
        f = tmp_path / "doc.md"
        f.write_text("# Title\n\nContent.", encoding="utf-8")
        asyncio.run(index_paths(service, IndexPathsRequest(paths=[str(f)])))

        with pytest.raises(MdqValidationError) as exc_info:
            _search_docs_structured(service, SearchDocsRequest(query='"unterminated'))

        assert code_for_exception(exc_info.value) == "validation_error"
        assert '"unterminated' not in str(exc_info.value)

    def test_busy_or_locked_is_a_retryable_consistency_error(self) -> None:
        domain, retryable = classify_sqlite_error(
            sqlite3.OperationalError("database is locked"), interrupted=False
        )
        assert isinstance(domain, MdqConsistencyError)
        assert code_for_exception(domain) == "consistency_error"
        assert retryable is True

    def test_missing_table_or_corruption_is_not_retryable(self) -> None:
        for detail in ("no such table: chunks_fts", "database disk image is corrupted"):
            domain, retryable = classify_sqlite_error(
                sqlite3.OperationalError(detail), interrupted=False
            )
            assert code_for_exception(domain) == "consistency_error"
            assert retryable is False

    def test_interruption_resolves_to_the_timeout_code(self) -> None:
        """`timeout` has no MDQ exception class, so the search path reports the interruption
        as a domain exception whose cause is the interruption; the reported code is `timeout`."""
        cause, retryable = classify_sqlite_error(
            sqlite3.OperationalError("interrupted"), interrupted=True
        )
        assert isinstance(cause, TimeoutError)
        assert retryable is True
        try:
            raise MdqConsistencyError("Search timed out") from cause
        except MdqConsistencyError as exc:
            assert code_for_exception(exc) == "timeout"

    def test_non_operational_sqlite_error_raises_consistency_error(
        self, service: MdqService, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A sqlite3.Error subclass that is not an OperationalError (e.g.
        DatabaseError) is classified as a consistency error, not swallowed."""
        self._error_connection(
            service,
            monkeypatch,
            sqlite3.DatabaseError("simulated non-operational sqlite error"),
        )

        with pytest.raises(MdqConsistencyError) as exc_info:
            _search_docs_structured(service, SearchDocsRequest(query="test"))

        assert code_for_exception(exc_info.value) == "consistency_error"
        assert "simulated" not in str(exc_info.value)


class TestHashedQueryIdentifier:
    def test_response_text_and_persistent_log_line_carry_no_raw_query(
        self,
        service: MdqService,
        tmp_path: Path,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """AC-5: the caller sees the hashed identifier, and so does the persistent log line."""
        query = "SecretProbeValue"
        (tmp_path / "doc.md").write_text(
            "# Title\n\nSecretProbeValue content.", encoding="utf-8"
        )
        asyncio.run(index_paths(service, IndexPathsRequest(paths=[str(tmp_path)])))

        with caplog.at_level(logging.INFO, logger="mcp_servers.mdq.search"):
            text, metadata = asyncio.run(
                search_docs(service, SearchDocsRequest(query=query))
            )

        identifier = hash_query_value(query)
        assert metadata["query_preview"] == identifier
        # The header echoes the query as the search term; the result lines are document
        # content, which may legitimately contain the same word.
        header = text.splitlines()[0]
        assert identifier in header
        assert query not in header
        assert query not in metadata["query_preview"]
        assert identifier in caplog.text
        assert query not in caplog.text
