"""tests/test_mdq_search_limits.py

Coverage for the effective SQL-layer result limit:
`effective_limit = min(request limit, service.max_results_limit)`, applied
directly to the SQL `LIMIT` clause so a large request `limit` cannot bypass
the config cap by having the database return an unbounded row set before
Python-side truncation.
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from tempfile import mkstemp

import pytest
from mcp_servers.mdq.indexer import index_paths
from mcp_servers.mdq.mdq_models import IndexPathsRequest, SearchDocsRequest
from mcp_servers.mdq.mdq_service import MdqService
from mcp_servers.mdq.search import _search_docs_structured

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


def _index_n_docs(service: MdqService, tmp_path: Path, n: int, keyword: str) -> None:
    for i in range(n):
        f = tmp_path / f"doc{i}.md"
        f.write_text(f"# Section {i}\n\n{keyword} content here.", encoding="utf-8")
    asyncio.run(index_paths(service, IndexPathsRequest(paths=[str(tmp_path)])))


class TestEffectiveLimit:
    def test_default_limit_from_config(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        """No explicit limit — default limit=10, all 3 docs fit under both
        the default limit and the config cap."""
        _index_n_docs(service, tmp_path, 3, "Alpha")
        result = _search_docs_structured(service, SearchDocsRequest(query="Alpha"))
        assert len(result["results"]) == 3
        assert result["shown_count"] == 3

    def test_explicit_limit_below_cap_is_honored(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        """A request limit smaller than service.max_results_limit is what
        actually reaches the SQL LIMIT."""
        _index_n_docs(service, tmp_path, 5, "Bravo")
        result = _search_docs_structured(
            service, SearchDocsRequest(query="Bravo", limit=3)
        )
        assert len(result["results"]) == 3
        assert result["shown_count"] == 3

    def test_explicit_limit_above_cap_is_bounded_at_sql_layer(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        """The key regression assertion: a huge request limit must be
        bounded at the SQL layer by service.max_results_limit — the fetch
        itself (not just later Python-side slicing) must never exceed the
        config cap."""
        _index_n_docs(service, tmp_path, 5, "Charlie")
        service.max_results_limit = 2
        result = _search_docs_structured(
            service, SearchDocsRequest(query="Charlie", limit=10000)
        )
        assert len(result["results"]) == 2
        assert result["shown_count"] == 2
        # matched_count remains the exact, unbounded match count.
        assert result["matched_count"] == 5

    def test_unauthorized_row_cannot_take_a_limit_slot(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        """Phase 1 characterization (REQ-002, AC-1): an unauthorized row that ranks
        above an authorized row must not fill a `LIMIT` slot. Written before the
        production change in the release unit; it fails first because the SQL `LIMIT`
        runs before authorization today, so the unauthorized row takes the slot and the
        authorized result is missing.
        """
        authorized_root = tmp_path / "authorized"
        unauthorized_root = tmp_path / "unauthorized"
        authorized_root.mkdir()
        unauthorized_root.mkdir()
        # bm25 ranks the unauthorized doc first by term frequency, so the ranking does
        # not depend on insertion order.
        (unauthorized_root / "unauthorized.md").write_text(
            "# Unauthorized\n\nUniform Uniform Uniform.", encoding="utf-8"
        )
        (authorized_root / "authorized.md").write_text(
            "# Authorized\n\nUniform content here.", encoding="utf-8"
        )
        asyncio.run(index_paths(service, IndexPathsRequest(paths=[str(tmp_path)])))

        # The allowlist is narrowed after indexing, so the unauthorized row is present
        # in the database but not visible.
        service._allowed_dirs = [str(authorized_root)]
        result = _search_docs_structured(
            service, SearchDocsRequest(query="Uniform", limit=1)
        )

        assert len(result["results"]) == 1
        assert result["results"][0].source_path.startswith(
            str(authorized_root.resolve())
        )
