"""tests/mcp_servers/mdq/test_search.py

Characterization tests for scripts/mcp_servers/mdq/search.py closing the
pre-refactor coverage gaps in `_build_search_where`'s `path_prefix` /
`heading_prefix` filters and `_search_docs_structured`'s exception-handling
branches (generic FTS5 OperationalError swallowed vs. non-OperationalError
sqlite3.Error re-raised as MdqConsistencyError). Written as a Phase 2
behavior-lock step before an extract-only refactor of `search.py`; do not
weaken these assertions when the implementation is refactored.
"""

from __future__ import annotations

import asyncio
import logging
import os
import sqlite3
from pathlib import Path
from tempfile import mkstemp

import pytest
from mcp_servers.mdq.indexer import index_paths
from mcp_servers.mdq.mdq_models import (
    IndexPathsRequest,
    MdqConsistencyError,
    SearchDocsRequest,
)
from mcp_servers.mdq.mdq_service import MdqService
from mcp_servers.mdq.search import _search_docs_structured


@pytest.fixture
def service(tmp_path: Path) -> MdqService:
    """MdqService with a temp DB path and tmp_path in allowed_dirs."""
    fd, db = mkstemp(suffix=".db", dir=str(tmp_path))
    try:
        svc = MdqService(db_path=db)
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


class TestGenericOperationalErrorFallback:
    def test_non_corruption_operational_error_returns_empty_results_without_raising(
        self,
        service: MdqService,
        tmp_path: Path,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """A malformed FTS5 MATCH query (e.g. an unterminated quote) raises a
        generic sqlite3.OperationalError that does not mention "no such
        table" or "corrupt" — this must be swallowed (logged, empty results)
        rather than propagated, unlike the index-corruption case."""
        f = tmp_path / "doc.md"
        f.write_text("# Title\n\nContent.", encoding="utf-8")
        asyncio.run(index_paths(service, IndexPathsRequest(paths=[str(f)])))

        with caplog.at_level(logging.WARNING, logger="mcp_servers.mdq.search"):
            result = _search_docs_structured(
                service, SearchDocsRequest(query='"unterminated')
            )

        assert result["results"] == []
        assert result["matched_count"] == 0
        assert "MDQ FTS5 search failed" in caplog.text


class TestGenericSqliteErrorRaises:
    def test_non_operational_sqlite_error_raises_consistency_error(
        self, service: MdqService, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A sqlite3.Error subclass that is not an OperationalError (e.g.
        DatabaseError) must be re-raised as MdqConsistencyError, not
        swallowed like the generic-OperationalError fallback case."""

        class _RaisingConnection:
            def execute(self, *args: object, **kwargs: object) -> None:
                raise sqlite3.DatabaseError("simulated non-operational sqlite error")

            def close(self) -> None:
                return None

        monkeypatch.setattr(service, "_get_db_connection", lambda: _RaisingConnection())

        with pytest.raises(MdqConsistencyError):
            _search_docs_structured(service, SearchDocsRequest(query="test"))
