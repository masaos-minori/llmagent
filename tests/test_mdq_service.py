"""tests/test_mdq_service.py
Unit tests for mcp/mdq/ components: parser, indexer, search, service, models.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from tempfile import mkstemp

import pytest
from mcp.mdq.indexer import _index_directory, _index_single_file, index_paths
from mcp.mdq.models import (
    GetChunkRequest,
    GrepDocsRequest,
    IndexPathsRequest,
    MdqNotFoundError,
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
        req = GetChunkRequest(chunk_id="chunk_abc123")
        assert req.chunk_id == "chunk_abc123"
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

    def test_refresh_index_request_force_default(self) -> None:
        req = RefreshIndexRequest(paths=["/x"])
        assert req.force is False

    def test_refresh_index_request_force_true(self) -> None:
        req = RefreshIndexRequest(paths=["/x"], force=True)
        assert req.force is True


# ── parser ────────────────────────────────────────────────────────────────────


class TestParseMarkdown:
    def test_returns_sections_with_headings(
        self, service: MdqService, md_file: Path
    ) -> None:
        sections = asyncio.run(
            parse_markdown(service, ParseMarkdownRequest(path=str(md_file)))
        )
        assert len(sections) == 1
        assert sections[0]["heading"] == "Title"
        assert "Content here." in sections[0]["content"]

    def test_returns_root_for_content_before_heading(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        f = tmp_path / "root.md"
        f.write_text("Intro text.\n\n## Section\n\nBody.", encoding="utf-8")
        sections = asyncio.run(
            parse_markdown(service, ParseMarkdownRequest(path=str(f)))
        )
        headings = [s["heading"] for s in sections]
        assert "<root>" in headings
        assert "Section" in headings

    def test_raises_for_missing_file(self, service: MdqService, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError, match="not_exist.md"):
            asyncio.run(
                parse_markdown(
                    service, ParseMarkdownRequest(path=str(tmp_path / "not_exist.md"))
                )
            )


# ── indexer ───────────────────────────────────────────────────────────────────


class TestIndexer:
    def test_index_single_file_stores_in_db(
        self, service: MdqService, md_file: Path
    ) -> None:
        asyncio.run(_index_single_file(service, md_file))
        conn = service._get_db_connection()
        try:
            row = conn.execute(
                "SELECT heading, content FROM chunks WHERE source_path = ?",
                (str(md_file),),
            ).fetchone()
            assert row is not None
            assert "Title" in row["heading"]
        finally:
            conn.close()

    def test_index_directory_processes_md_files(
        self, service: MdqService, md_dir: Path
    ) -> None:
        asyncio.run(_index_directory(service, md_dir))
        conn = service._get_db_connection()
        try:
            count = conn.execute("SELECT COUNT(*) as cnt FROM chunks").fetchone()[
                "cnt"
            ]
            assert count == 2  # a.md and b.md
        finally:
            conn.close()

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
    def test_returns_results_after_indexing(
        self, service: MdqService, md_file: Path
    ) -> None:
        asyncio.run(index_paths(service, IndexPathsRequest(paths=[str(md_file)])))
        req = SearchDocsRequest(query="Content")
        result = asyncio.run(search_docs(service, req))
        assert "Content" in result
        assert "found" in result

    def test_returns_no_results_for_empty_query(self, service: MdqService) -> None:
        req = SearchDocsRequest(query="")
        result = asyncio.run(search_docs(service, req))
        assert "No results found" in result

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

    def test_get_chunk_returns_content_after_indexing(
        self, service: MdqService, md_file: Path
    ) -> None:
        asyncio.run(index_paths(service, IndexPathsRequest(paths=[str(md_file)])))
        conn = service._get_db_connection()
        try:
            row = conn.execute("SELECT chunk_id FROM chunks LIMIT 1").fetchone()
            assert row is not None
            chunk_id = row["chunk_id"]
        finally:
            conn.close()
        req = GetChunkRequest(chunk_id=chunk_id)
        result = asyncio.run(service.get_chunk(req))
        assert "Title" in result
        assert "Content here." in result

    def test_get_chunk_not_found(self, service: MdqService) -> None:
        req = GetChunkRequest(chunk_id="nonexistent_chunk_id")
        with pytest.raises(MdqNotFoundError):
            asyncio.run(service.get_chunk(req))

    def test_refresh_index_delegates_to_indexer(
        self, service: MdqService, md_file: Path
    ) -> None:
        req = RefreshIndexRequest(paths=[str(md_file)])
        result = asyncio.run(service.refresh_index(req))
        assert "Refresh complete" in result
        assert "Indexed:" in result
        assert "Skipped (unchanged):" in result
        assert "Deleted from index:" in result
        assert "Failed:" in result

    def test_stats_returns_counts_after_indexing(
        self, service: MdqService, md_dir: Path
    ) -> None:
        asyncio.run(index_paths(service, IndexPathsRequest(paths=[str(md_dir)])))
        req = StatsRequest()
        result = asyncio.run(service.stats(req))
        assert "Documents:" in result
        assert "Chunks:" in result

    def test_grep_docs_returns_matches_after_indexing(
        self, service: MdqService, md_file: Path
    ) -> None:
        asyncio.run(index_paths(service, IndexPathsRequest(paths=[str(md_file)])))
        req = GrepDocsRequest(pattern="Content")
        result = asyncio.run(service.grep_docs(req))
        assert "Chunk" in result or "Content" in result

    def test_grep_docs_no_match(self, service: MdqService) -> None:
        req = GrepDocsRequest(pattern="nonexistent_xyz")
        result = asyncio.run(service.grep_docs(req))
        assert "No matches found" in result

    def test_index_paths_delegates(self, service: MdqService, md_dir: Path) -> None:
        req = IndexPathsRequest(paths=[str(md_dir)])
        result = asyncio.run(service.index_paths(req))
        assert result == "Indexing complete"

    def test_outline_returns_headings(self, service: MdqService, md_file: Path) -> None:
        asyncio.run(index_paths(service, IndexPathsRequest(paths=[str(md_file)])))
        req = OutlineRequest(path=str(md_file))
        result = asyncio.run(service.outline(req))
        assert "Title" in result

    def test_db_path_configurable(self) -> None:
        from tempfile import mkstemp  # noqa: PLC0415

        fd, db = mkstemp(suffix=".db")
        try:
            svc = MdqService(db_path=db)
            assert svc.db_path == db
        finally:
            import os  # noqa: PLC0415

            os.close(fd)
