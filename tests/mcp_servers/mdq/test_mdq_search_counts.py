"""tests/test_mdq_search_counts.py

Coverage for the matched_count/shown_count split replacing the old `total`
field: the structured result must report an exact matched count independent
of any limit, the shown count must reflect what was actually returned, and
search_docs()'s rendered text must never claim an exact "found" total when
rows were actually dropped by a limit.
"""

from __future__ import annotations

import asyncio
import os
import re
from pathlib import Path
from tempfile import mkstemp

import pytest
from mcp_servers.mdq.indexer import index_paths
from mcp_servers.mdq.mdq_models import IndexPathsRequest, SearchDocsRequest
from mcp_servers.mdq.mdq_service import MdqService
from mcp_servers.mdq.search import _search_docs_structured, search_docs


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


def _index_n_docs(service: MdqService, tmp_path: Path, n: int, keyword: str) -> None:
    for i in range(n):
        f = tmp_path / f"doc{i}.md"
        f.write_text(f"# Section {i}\n\n{keyword} content here.", encoding="utf-8")
    asyncio.run(index_paths(service, IndexPathsRequest(paths=[str(tmp_path)])))


class TestMatchedShownCounts:
    def test_matched_count_is_exact_regardless_of_limit(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        _index_n_docs(service, tmp_path, 5, "Keyword")
        result = _search_docs_structured(
            service, SearchDocsRequest(query="Keyword", limit=2)
        )
        assert result["matched_count"] == 5
        assert result["shown_count"] == 2

    def test_header_wording_when_nothing_truncated(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        _index_n_docs(service, tmp_path, 3, "Keyword")
        text, _metadata = asyncio.run(
            search_docs(service, SearchDocsRequest(query="Keyword"))
        )
        assert "3" in text
        assert "Truncated" not in text

    def test_header_wording_when_results_truncated(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        _index_n_docs(service, tmp_path, 5, "Keyword")
        text, _metadata = asyncio.run(
            search_docs(service, SearchDocsRequest(query="Keyword", limit=2))
        )
        # Both the matched count (5) and shown count (2) must be
        # discoverable in the text — the header/trailer must not present a
        # single ambiguous number that conflates the two.
        assert "5" in text
        assert "2" in text
        assert "Truncated" in text

    def test_truncation_message_consistency(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        """Whatever counts appear before the [Truncated ...] trailer must
        match whatever counts appear inside it — no cross-referencing
        inconsistency between the header and the trailer."""
        _index_n_docs(service, tmp_path, 5, "Keyword")
        text, _metadata = asyncio.run(
            search_docs(service, SearchDocsRequest(query="Keyword", limit=2))
        )
        assert "Truncated" in text
        header, _, trailer = text.partition("[Truncated")
        header_numbers = set(re.findall(r"\d+", header))
        trailer_numbers = set(re.findall(r"\d+", trailer))
        # The exact matched count (5) must appear consistently in both the
        # header and the truncation trailer.
        assert "5" in header_numbers
        assert "5" in trailer_numbers
