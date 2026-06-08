"""tests/test_mdq_service.py
Unit tests for mcp/mdq/ components: parser, indexer, search, service, models.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import patch

import pytest
from mcp.mdq.indexer import _index_directory, _index_single_file, index_paths
from mcp.mdq.models import (
    GetChunkRequest,
    GrepDocsRequest,
    IndexPathsRequest,
    OutlineRequest,
    ParseMarkdownRequest,
    RefreshIndexRequest,
    SearchDocsRequest,
    StatsRequest,
)
from mcp.mdq.parser import parse_markdown
from mcp.mdq.search import search_docs
from mcp.mdq.service import MdqService

# ── fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def service() -> MdqService:
    """MdqService with DB init patched out."""
    with patch.object(MdqService, "_init_db", return_value=None):
        return MdqService()


@pytest.fixture
def md_file(tmp_path: Path) -> Path:
    """A temporary Markdown file."""
    f = tmp_path / "test.md"
    f.write_text("# Title\n\nContent here.", encoding="utf-8")
    return f


@pytest.fixture
def md_dir(tmp_path: Path) -> Path:
    """A temporary directory with two Markdown files."""
    d = tmp_path / "docs"
    d.mkdir()
    (d / "a.md").write_text("# A\n\nAlpha.", encoding="utf-8")
    (d / "b.md").write_text("# B\n\nBeta.", encoding="utf-8")
    (d / "ignore.txt").write_text("not markdown", encoding="utf-8")
    return d


# ── models ────────────────────────────────────────────────────────────────────


class TestModels:
    def test_search_docs_request_defaults(self) -> None:
        req = SearchDocsRequest(query="hello")
        assert req.query == "hello"
        assert req.limit == 10
        assert req.mode == "bm25"
        assert req.path_prefix is None
        assert req.tag_filter is None

    def test_get_chunk_request_defaults(self) -> None:
        req = GetChunkRequest(chunk_id=42)
        assert req.chunk_id == 42
        assert req.with_neighbors is False

    def test_index_paths_request(self) -> None:
        req = IndexPathsRequest(paths=["/a", "/b"])
        assert req.paths == ["/a", "/b"]

    def test_grep_docs_request(self) -> None:
        req = GrepDocsRequest(pattern=r"\bfoo\b")
        assert req.pattern == r"\bfoo\b"
        assert req.paths is None

    def test_stats_request_empty(self) -> None:
        req = StatsRequest()
        assert req is not None

    def test_outline_request(self) -> None:
        req = OutlineRequest(path="/tmp/doc.md")
        assert req.path == "/tmp/doc.md"

    def test_refresh_index_request(self) -> None:
        req = RefreshIndexRequest(paths=["/x"])
        assert req.paths == ["/x"]


# ── parser ────────────────────────────────────────────────────────────────────


class TestParseMarkdown:
    def test_returns_file_content(self, service: MdqService, md_file: Path) -> None:
        result = asyncio.run(
            parse_markdown(service, ParseMarkdownRequest(path=str(md_file)))
        )
        assert "# Title" in result
        assert "Content here." in result

    def test_raises_for_missing_file(self, service: MdqService, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError, match="not_exist.md"):
            asyncio.run(
                parse_markdown(
                    service, ParseMarkdownRequest(path=str(tmp_path / "not_exist.md"))
                )
            )


# ── indexer ───────────────────────────────────────────────────────────────────


class TestIndexer:
    def test_index_single_file_logs(
        self, service: MdqService, md_file: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        import logging

        with caplog.at_level(logging.INFO, logger="mcp.mdq.indexer"):
            asyncio.run(_index_single_file(service, md_file))
        assert str(md_file) in caplog.text

    def test_index_directory_processes_md_files(
        self, service: MdqService, md_dir: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        import logging

        with caplog.at_level(logging.INFO, logger="mcp.mdq.indexer"):
            asyncio.run(_index_directory(service, md_dir))
        assert "a.md" in caplog.text
        assert "b.md" in caplog.text
        assert "ignore.txt" not in caplog.text

    def test_index_paths_skips_nonexistent(
        self, service: MdqService, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        import logging

        req = IndexPathsRequest(paths=[str(tmp_path / "ghost.md")])
        with caplog.at_level(logging.WARNING, logger="mcp.mdq.indexer"):
            result = asyncio.run(index_paths(service, req))
        assert result == "Indexing complete"
        assert "does not exist" in caplog.text

    def test_index_paths_skips_non_md_file(
        self, service: MdqService, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        import logging

        txt = tmp_path / "file.txt"
        txt.write_text("hello")
        req = IndexPathsRequest(paths=[str(txt)])
        with caplog.at_level(logging.WARNING, logger="mcp.mdq.indexer"):
            result = asyncio.run(index_paths(service, req))
        assert result == "Indexing complete"
        assert "Skipping" in caplog.text

    def test_index_paths_md_file_returns_complete(
        self, service: MdqService, md_file: Path
    ) -> None:
        req = IndexPathsRequest(paths=[str(md_file)])
        result = asyncio.run(index_paths(service, req))
        assert result == "Indexing complete"

    def test_index_paths_directory_returns_complete(
        self, service: MdqService, md_dir: Path
    ) -> None:
        req = IndexPathsRequest(paths=[str(md_dir)])
        result = asyncio.run(index_paths(service, req))
        assert result == "Indexing complete"


# ── search ────────────────────────────────────────────────────────────────────


class TestSearchDocs:
    def test_returns_placeholder_with_query(self, service: MdqService) -> None:
        req = SearchDocsRequest(query="python")
        result = asyncio.run(search_docs(service, req))
        assert "python" in result

    def test_logs_query(
        self, service: MdqService, caplog: pytest.LogCaptureFixture
    ) -> None:
        import logging

        req = SearchDocsRequest(query="foo bar")
        with caplog.at_level(logging.INFO, logger="mcp.mdq.search"):
            asyncio.run(search_docs(service, req))
        assert "foo bar" in caplog.text


# ── service ───────────────────────────────────────────────────────────────────


class TestMdqService:
    def test_search_docs_delegates(self, service: MdqService) -> None:
        req = SearchDocsRequest(query="test")
        result = asyncio.run(service.search_docs(req))
        assert "test" in result

    def test_get_chunk_placeholder(self, service: MdqService) -> None:
        req = GetChunkRequest(chunk_id=7)
        result = asyncio.run(service.get_chunk(req))
        assert "7" in result

    def test_refresh_index_placeholder(self, service: MdqService) -> None:
        req = RefreshIndexRequest(paths=[])
        result = asyncio.run(service.refresh_index(req))
        assert result == "Index refreshed"

    def test_stats_placeholder(self, service: MdqService) -> None:
        req = StatsRequest()
        result = asyncio.run(service.stats(req))
        assert result == "Stats retrieved"

    def test_grep_docs_placeholder(self, service: MdqService) -> None:
        req = GrepDocsRequest(pattern=r"\bword\b")
        result = asyncio.run(service.grep_docs(req))
        assert r"\bword\b" in result

    def test_index_paths_delegates(self, service: MdqService, md_dir: Path) -> None:
        req = IndexPathsRequest(paths=[str(md_dir)])
        result = asyncio.run(service.index_paths(req))
        assert result == "Indexing complete"

    def test_outline_delegates_to_parser(
        self, service: MdqService, md_file: Path
    ) -> None:
        req = OutlineRequest(path=str(md_file))
        result = asyncio.run(service.outline(req))
        assert "# Title" in result

    def test_db_path_default(self, service: MdqService) -> None:
        assert service.db_path == "/opt/llm/db/mdq.db"
