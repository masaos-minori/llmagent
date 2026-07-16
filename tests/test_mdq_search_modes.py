"""tests/test_mdq_search_modes.py

Regression coverage for search_docs mode restriction and result-limit
behavior after the hybrid-search placeholder removal. Replaces the deleted
tests/test_mdq_hybrid_search.py.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from tempfile import mkstemp

import pytest
from mcp_servers.mdq.indexer import index_paths
from mcp_servers.mdq.models import IndexPathsRequest, SearchDocsRequest
from mcp_servers.mdq.search import search_docs
from mcp_servers.mdq.service import MdqService
from pydantic import ValidationError


@pytest.fixture
def service(tmp_path: Path) -> MdqService:
    """MdqService with a temp DB path and tmp_path in allowed_dirs."""
    fd, db = mkstemp(suffix=".db", dir=str(tmp_path))
    try:
        svc = MdqService(db_path=db)
        svc._allowed_dirs = [str(tmp_path)]
        return svc
    finally:
        import os  # noqa: PLC0415

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
        result = asyncio.run(search_docs(service, SearchDocsRequest(query="Keyword")))
        assert "Truncated" not in result
        assert "3 found" in result

    def test_request_override_below_cap_is_honored(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        for i in range(5):
            f = tmp_path / f"doc{i}.md"
            f.write_text(f"# Section {i}\n\nKeyword content here.", encoding="utf-8")
        asyncio.run(index_paths(service, IndexPathsRequest(paths=[str(tmp_path)])))
        result = asyncio.run(
            search_docs(
                service, SearchDocsRequest(query="Keyword", max_results_limit=2)
            )
        )
        assert "Truncated" in result
        assert "5 found" in result

    def test_request_override_above_cap_is_bounded(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        for i in range(3):
            f = tmp_path / f"doc{i}.md"
            f.write_text(f"# Section {i}\n\nKeyword content here.", encoding="utf-8")
        asyncio.run(index_paths(service, IndexPathsRequest(paths=[str(tmp_path)])))
        service.max_results_limit = 2
        result = asyncio.run(
            search_docs(
                service, SearchDocsRequest(query="Keyword", max_results_limit=100)
            )
        )
        assert "Truncated" in result
