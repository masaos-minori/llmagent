"""tests/test_mdq_search_modes.py

Regression coverage for search_docs mode restriction and result-limit
behavior after the hybrid-search placeholder removal. Replaces the deleted
tests/test_mdq_hybrid_search.py. Also pins the genuine zero-result case measured
through the query boundary (REQ-003, AC-3): source
issues/20261119-142124_mdqmcp002_mdq-search-query-boundary.md.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from tempfile import mkstemp

import pytest
from mcp_servers.mdq.indexer import index_paths
from mcp_servers.mdq.mdq_models import IndexPathsRequest, SearchDocsRequest
from mcp_servers.mdq.mdq_service import MdqService
from mcp_servers.mdq.search import _search_docs_structured, search_docs
from pydantic import ValidationError

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
        import os

        os.close(fd)


class TestSearchModeRestriction:
    def test_default_mode_is_bm25(self) -> None:
        req = SearchDocsRequest(query="test")
        assert req.mode == "bm25"

    def test_explicit_bm25_mode_accepted(self) -> None:
        req = SearchDocsRequest(query="test", mode="bm25")
        assert req.mode == "bm25"

    def test_unsupported_mode_rejected(self) -> None:
        with pytest.raises(ValidationError):
            SearchDocsRequest(query="test", mode="hybrid")

    def test_grep_mode_rejected(self) -> None:
        """grep is a separate dedicated tool (grep_docs), not a search_docs mode."""
        with pytest.raises(ValidationError):
            SearchDocsRequest(query="test", mode="grep")


class TestMaxSearchResultsRemoved:
    def test_max_search_results_field_does_not_exist(self, service: MdqService) -> None:
        """max_search_results was a dead config duplicate; must not remain."""
        assert not hasattr(service, "max_search_results")

    def test_max_search_results_kwarg_ignored(self) -> None:
        """Passing max_search_results to SearchDocsRequest has no effect."""
        req = SearchDocsRequest(query="test", max_search_results=5)
        assert not hasattr(req, "max_search_results")


class TestResultLimitBehavior:
    def test_default_limit_from_config(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        for i in range(3):
            f = tmp_path / f"doc{i}.md"
            f.write_text(f"# Section {i}\n\nKeyword content here.", encoding="utf-8")
        asyncio.run(index_paths(service, IndexPathsRequest(paths=[str(tmp_path)])))
        text, metadata = asyncio.run(
            search_docs(service, SearchDocsRequest(query="Keyword"))
        )
        assert "Truncated" not in text
        assert "3 found" in text
        assert metadata["truncated"] is False

    def test_request_override_below_cap_is_honored(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        for i in range(5):
            f = tmp_path / f"doc{i}.md"
            f.write_text(f"# Section {i}\n\nKeyword content here.", encoding="utf-8")
        asyncio.run(index_paths(service, IndexPathsRequest(paths=[str(tmp_path)])))
        text, metadata = asyncio.run(
            search_docs(
                service, SearchDocsRequest(query="Keyword", max_results_limit=2)
            )
        )
        assert "Truncated" in text
        assert "5" in text  # matched_count
        assert "2" in text  # shown_count
        assert metadata["truncated"] is True
        assert metadata["result_count"] == 5
        assert metadata["shown_count"] == 2

    def test_request_override_above_cap_is_bounded(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        for i in range(3):
            f = tmp_path / f"doc{i}.md"
            f.write_text(f"# Section {i}\n\nKeyword content here.", encoding="utf-8")
        asyncio.run(index_paths(service, IndexPathsRequest(paths=[str(tmp_path)])))
        service.max_results_limit = 2
        text, metadata = asyncio.run(
            search_docs(
                service, SearchDocsRequest(query="Keyword", max_results_limit=100)
            )
        )
        assert "Truncated" in text
        assert "3" in text  # matched_count
        assert "2" in text  # shown_count
        assert metadata["truncated"] is True
        assert metadata["result_count"] == 3
        assert metadata["shown_count"] == 2


class TestGenuineZeroResult:
    def test_rows_outside_the_authorized_roots_report_zero_through_the_boundary(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        """Phase 1 characterization (REQ-003, AC-3): rows exist in the index while all
        of them are outside the authorized roots, so the query boundary must report a
        genuine zero. Written before the production change; it fails first because the
        count query has no authorized-source predicate today, so `matched_count` reports
        rows the caller cannot see.
        """
        for i in range(3):
            f = tmp_path / f"doc{i}.md"
            f.write_text(f"# Section {i}\n\nKeyword content here.", encoding="utf-8")
        asyncio.run(index_paths(service, IndexPathsRequest(paths=[str(tmp_path)])))

        # The allowlist is narrowed to a different root after indexing, so every indexed
        # row is present in the database but not visible.
        authorized_root = tmp_path / "authorized"
        authorized_root.mkdir()
        service._allowed_dirs = [str(authorized_root)]

        result = _search_docs_structured(service, SearchDocsRequest(query="Keyword"))
        assert result["matched_count"] == 0
        assert result["results"] == []

        text, metadata = asyncio.run(
            search_docs(service, SearchDocsRequest(query="Keyword"))
        )
        assert "No results found" in text
        assert metadata["result_count"] == 0
        assert metadata["shown_count"] == 0
        assert metadata["truncated"] is False
