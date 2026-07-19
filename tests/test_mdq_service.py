"""tests/test_mdq_service.py
Unit tests for mcp/mdq/ components: parser, indexer, search, service, models.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from tempfile import mkstemp
from unittest.mock import patch

import pytest
from mcp_servers.mdq.indexer import (
    _index_directory,
    _index_single_file,
    _iter_indexable_files,
    generate_chunk_id,
    index_paths,
)
from mcp_servers.mdq.mdq_models import (
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
from mcp_servers.mdq.parser import parse_markdown
from mcp_servers.mdq.search import search_docs
from mcp_servers.mdq.mdq_service import MdqService

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


# ── include_globs / exclude_globs wiring ──────────────────────────────────────


class TestIterIndexableFiles:
    def test_exclude_globs_skips_matching_files(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        """A file under a directory matching exclude_globs is not returned."""
        (tmp_path / ".git").mkdir()
        (tmp_path / ".git" / "config.md").write_text("# git config", encoding="utf-8")
        (tmp_path / "keep.md").write_text("# Keep", encoding="utf-8")

        files = _iter_indexable_files(service, tmp_path)
        names = {f.name for f in files}
        assert "keep.md" in names
        assert "config.md" not in names

    def test_exclude_globs_skips_nested_pycache(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        """__pycache__/** excludes files nested arbitrarily deep, not just at root."""
        nested = tmp_path / "src" / "__pycache__" / "inner"
        nested.mkdir(parents=True)
        (tmp_path / "src" / "keep.md").write_text("# Keep", encoding="utf-8")
        (nested / "ignored.md").write_text("# Ignored", encoding="utf-8")

        files = _iter_indexable_files(service, tmp_path)
        names = {f.name for f in files}
        assert "keep.md" in names
        assert "ignored.md" not in names

    def test_custom_include_globs_matches_non_md_files(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        """A non-.md file matching a customized include_globs is indexed."""
        service.include_globs = ["*.txt"]
        (tmp_path / "notes.txt").write_text("plain text notes", encoding="utf-8")
        (tmp_path / "ignored.md").write_text("# Ignored", encoding="utf-8")

        files = _iter_indexable_files(service, tmp_path)
        names = {f.name for f in files}
        assert "notes.txt" in names
        assert "ignored.md" not in names


class TestMaxFileCharsEnforcement:
    def test_oversized_file_is_skipped_with_warning(
        self,
        service: MdqService,
        tmp_path: Path,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """A file exceeding max_file_chars is skipped entirely, with a warning log."""
        import logging

        service.max_file_chars = 10
        big = tmp_path / "big.md"
        big.write_text("# Title\n\n" + ("X" * 100), encoding="utf-8")

        with caplog.at_level(logging.WARNING, logger="mcp_servers.mdq.indexer"):
            asyncio.run(_index_single_file(service, big))

        assert "exceeds max_file_chars" in caplog.text
        conn = service._get_db_connection()
        try:
            row = conn.execute(
                "SELECT COUNT(*) as cnt FROM documents WHERE source_path = ?",
                (str(big),),
            ).fetchone()
            assert row["cnt"] == 0
        finally:
            conn.close()

    def test_file_within_limit_is_indexed(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        service.max_file_chars = 100000
        f = tmp_path / "small.md"
        f.write_text("# Title\n\nSmall content.", encoding="utf-8")
        asyncio.run(_index_single_file(service, f))
        conn = service._get_db_connection()
        try:
            row = conn.execute(
                "SELECT COUNT(*) as cnt FROM documents WHERE source_path = ?",
                (str(f),),
            ).fetchone()
            assert row["cnt"] == 1
        finally:
            conn.close()


class TestMaxChunkCharsEnforcement:
    def test_oversized_chunk_is_truncated_and_hash_matches_stored_content(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        """A section exceeding max_chunk_chars is truncated before storage, and
        content_hash is computed from the truncated (stored) content, not the
        original."""
        import hashlib

        service.max_chunk_chars = 20
        f = tmp_path / "big_chunk.md"
        f.write_text("# Title\n\n" + ("Y" * 500), encoding="utf-8")
        asyncio.run(_index_single_file(service, f))

        conn = service._get_db_connection()
        try:
            row = conn.execute(
                "SELECT content, content_hash FROM chunks WHERE source_path = ?",
                (str(f),),
            ).fetchone()
            assert row is not None
            assert len(row["content"]) <= 20
            expected_hash = hashlib.sha256(row["content"].encode()).hexdigest()
            assert row["content_hash"] == expected_hash
        finally:
            conn.close()


# ── service construction ──────────────────────────────────────────────────────


class TestServiceConstruction:
    def test_service_has_no_audit_log_path_attribute(self, service: MdqService) -> None:
        """audit_log_path was a dead config field; MdqService must not carry it."""
        assert not hasattr(service, "audit_log_path")


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
        sections, _tags = asyncio.run(
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
        sections, _tags = asyncio.run(
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

    def test_code_fence_hash_not_treated_as_heading(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        """# inside a code fence must not create a new section."""
        f = tmp_path / "fence.md"
        f.write_text(
            "# Title\n\n```text\n# Not a heading\n```\n\nBody.", encoding="utf-8"
        )
        sections, _tags = asyncio.run(
            parse_markdown(service, ParseMarkdownRequest(path=str(f)))
        )
        headings = [s["heading"] for s in sections]
        assert "Title" in headings
        assert "Not a heading" not in headings
        assert len([s for s in sections if s["heading"] == "Title"]) == 1

    def test_frontmatter_stripped(self, service: MdqService, tmp_path: Path) -> None:
        """YAML frontmatter is skipped; first ATX heading becomes first section."""
        f = tmp_path / "frontmatter.md"
        f.write_text("---\ntitle: Test\n---\n\n# Title\n\nBody.", encoding="utf-8")
        sections, tags = asyncio.run(
            parse_markdown(service, ParseMarkdownRequest(path=str(f)))
        )
        headings = [s["heading"] for s in sections]
        assert "---" not in headings
        assert "Title" in headings
        assert len(sections) == 1
        assert tags == []

    def test_repeated_headings_have_distinct_ordinals(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        """Two ## API headings produce ordinal=1 and ordinal=2."""
        f = tmp_path / "repeated.md"
        f.write_text(
            "# Title\n\n## API\n\nFirst body.\n\n## API\n\nSecond body.",
            encoding="utf-8",
        )
        sections, _tags = asyncio.run(
            parse_markdown(service, ParseMarkdownRequest(path=str(f)))
        )
        api_sections = [s for s in sections if s["heading"] == "API"]
        assert len(api_sections) == 2
        ordinals = sorted(s["ordinal"] for s in api_sections)
        assert ordinals == [1, 2], f"Expected [1, 2], got {ordinals}"

    def test_nested_heading_path(self, service: MdqService, tmp_path: Path) -> None:
        """### C under # A / ## B produces heading_path='A > B'."""
        f = tmp_path / "nested.md"
        f.write_text("# A\n\n## B\n\n### C\n\nBody.", encoding="utf-8")
        sections, _tags = asyncio.run(
            parse_markdown(service, ParseMarkdownRequest(path=str(f)))
        )
        c_section = next(s for s in sections if s["heading"] == "C")
        assert c_section["heading_path"] == "A > B"
        assert c_section["parent_heading"] == "B"

    def test_malformed_heading_treated_as_content(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        """#NoSpace (no space after #) is treated as plain content."""
        f = tmp_path / "malformed.md"
        f.write_text("# Title\n\n#NoSpace\n\nBody.", encoding="utf-8")
        sections, _tags = asyncio.run(
            parse_markdown(service, ParseMarkdownRequest(path=str(f)))
        )
        headings = [s["heading"] for s in sections]
        assert "NoSpace" not in headings
        assert "Title" in headings

    def test_heading_level_returned_correctly(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        """Verify heading_level field equals the ATX # count."""
        f = tmp_path / "levels.md"
        f.write_text("# A\n\n## B\n\n### C\n\nBody.", encoding="utf-8")
        sections, _tags = asyncio.run(
            parse_markdown(service, ParseMarkdownRequest(path=str(f)))
        )
        levels = {s["heading"]: s["heading_level"] for s in sections}
        assert levels["A"] == 1
        assert levels["B"] == 2
        assert levels["C"] == 3

    def test_heading_with_no_content_body_omitted(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        """Heading immediately followed by next heading (no content) is omitted."""
        f = tmp_path / "empty.md"
        # No blank line between ## Empty and ## Has Content — no content lines
        f.write_text("# Title\n\n## Empty\n## Has Content\n\nBody.", encoding="utf-8")
        sections, _tags = asyncio.run(
            parse_markdown(service, ParseMarkdownRequest(path=str(f)))
        )
        headings = [s["heading"] for s in sections]
        assert "Empty" not in headings
        assert "Has Content" in headings

    def test_frontmatter_tags_list_form(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        """tags: [a, b] in frontmatter is returned as a normalized list."""
        f = tmp_path / "tags_list.md"
        f.write_text(
            "---\ntags: [alpha, beta]\n---\n\n# Title\n\nBody.", encoding="utf-8"
        )
        _sections, tags = asyncio.run(
            parse_markdown(service, ParseMarkdownRequest(path=str(f)))
        )
        assert tags == ["alpha", "beta"]

    def test_frontmatter_tags_comma_string_form(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        """tags: "a, b" (comma-separated string) is normalized to a list."""
        f = tmp_path / "tags_string.md"
        f.write_text(
            '---\ntags: "alpha, beta"\n---\n\n# Title\n\nBody.', encoding="utf-8"
        )
        _sections, tags = asyncio.run(
            parse_markdown(service, ParseMarkdownRequest(path=str(f)))
        )
        assert tags == ["alpha", "beta"]

    def test_frontmatter_no_tags_key_returns_empty(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        """Frontmatter present but with no tags key yields an empty tags list."""
        f = tmp_path / "no_tags.md"
        f.write_text("---\ntitle: Test\n---\n\n# Title\n\nBody.", encoding="utf-8")
        _sections, tags = asyncio.run(
            parse_markdown(service, ParseMarkdownRequest(path=str(f)))
        )
        assert tags == []

    def test_malformed_frontmatter_does_not_crash_indexing(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        """Invalid YAML or a non-list/non-string tags value falls back to empty tags,
        not an exception — a malformed frontmatter block must not break indexing of an
        otherwise-valid document.
        """
        f = tmp_path / "malformed_fm.md"
        f.write_text(
            "---\ntags: {not: a, list: or, string: value}\n---\n\n# Title\n\nBody.",
            encoding="utf-8",
        )
        sections, tags = asyncio.run(
            parse_markdown(service, ParseMarkdownRequest(path=str(f)))
        )
        assert tags == []
        assert len(sections) == 1
        title_section = next(s for s in sections if s["heading"] == "Title")
        assert title_section["content"] == "Body."

    def test_frontmatter_followed_by_blank_line_yields_no_spurious_root_section(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        """Frontmatter + blank line + heading (no other pre-heading content) parses
        to exactly one section — no empty `<root>` section from the trailing blank
        line left over after skipping the frontmatter block.

        Regression test for issues/20260719-142152_parser_spurious_empty_root_section_after_frontmatter.md.
        """
        f = tmp_path / "frontmatter_blank.md"
        f.write_text("---\ntags: [x]\n---\n\n# Title\n\nBody.", encoding="utf-8")
        sections, _tags = asyncio.run(
            parse_markdown(service, ParseMarkdownRequest(path=str(f)))
        )
        assert len(sections) == 1
        assert sections[0]["heading"] == "Title"


# ── indexer ───────────────────────────────────────────────────────────────────


class TestIndexer:
    def test_index_single_file_stores_in_db(
        self, service: MdqService, md_file: Path
    ) -> None:
        asyncio.run(_index_single_file(service, md_file))
        conn = service._get_db_connection()
        try:
            row = conn.execute(
                "SELECT heading, content, token_count, tags_json FROM chunks WHERE source_path = ?",
                (str(md_file),),
            ).fetchone()
            assert row is not None
            assert "Title" in row["heading"]
            assert row["token_count"] is not None and row["token_count"] > 0
            assert row["tags_json"] == "[]"
        finally:
            conn.close()

    def test_index_single_file_stores_real_tags_json(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        """A frontmatter tags list is persisted as a real JSON array in tags_json."""
        f = tmp_path / "tagged.md"
        f.write_text(
            "---\ntags: [urgent, draft]\n---\n\n# Title\n\nBody.", encoding="utf-8"
        )
        asyncio.run(_index_single_file(service, f))
        conn = service._get_db_connection()
        try:
            row = conn.execute(
                "SELECT tags_json FROM chunks WHERE source_path = ?", (str(f),)
            ).fetchone()
            assert row is not None
            assert json.loads(row["tags_json"]) == ["urgent", "draft"]
        finally:
            conn.close()

    def test_index_directory_processes_md_files(
        self, service: MdqService, md_dir: Path
    ) -> None:
        asyncio.run(_index_directory(service, md_dir))
        conn = service._get_db_connection()
        try:
            count = conn.execute("SELECT COUNT(*) as cnt FROM chunks").fetchone()["cnt"]
            assert count == 2  # a.md and b.md
        finally:
            conn.close()

    def test_index_paths_skips_nonexistent(
        self, service: MdqService, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        import logging

        req = IndexPathsRequest(paths=[str(tmp_path / "ghost.md")])
        with caplog.at_level(logging.WARNING, logger="mcp_servers.mdq.indexer"):
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
        with caplog.at_level(logging.WARNING, logger="mcp_servers.mdq.indexer"):
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
        with caplog.at_level(logging.INFO, logger="mcp_servers.mdq.search"):
            asyncio.run(search_docs(service, req))
        assert "foo bar" in caplog.text

    def test_snippet_length_respects_max_snippet_chars(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        """snippet length in results is bounded by service.max_snippet_chars."""
        from mcp_servers.mdq.search import _search_docs_structured

        service.max_snippet_chars = 10
        f = tmp_path / "long.md"
        f.write_text("# Title\n\n" + ("Keyword content " * 20), encoding="utf-8")
        asyncio.run(index_paths(service, IndexPathsRequest(paths=[str(f)])))
        result = _search_docs_structured(service, SearchDocsRequest(query="Keyword"))
        assert len(result["results"]) > 0
        for item in result["results"]:
            assert len(item.snippet) <= 10

    def test_search_docs_tag_filter_matches_real_tags(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        """search_docs(..., tag_filter=[...]) matches docs indexed with that tag only."""
        tagged = tmp_path / "tagged.md"
        tagged.write_text(
            "---\ntags: [important]\n---\n\n# Title\n\nShared keyword content.",
            encoding="utf-8",
        )
        untagged = tmp_path / "untagged.md"
        untagged.write_text("# Other\n\nShared keyword content.", encoding="utf-8")
        asyncio.run(
            index_paths(service, IndexPathsRequest(paths=[str(tagged), str(untagged)]))
        )
        req = SearchDocsRequest(query="keyword", tag_filter=["important"])
        result = asyncio.run(search_docs(service, req))
        assert "Title" in result
        assert "Other" not in result

    def test_search_docs_structured_token_count_non_null(
        self, service: MdqService, md_file: Path
    ) -> None:
        """SearchResultItem.token_count is a positive int after indexing (API response
        payload, not just the raw DB row)."""
        from mcp_servers.mdq.search import _search_docs_structured

        asyncio.run(index_paths(service, IndexPathsRequest(paths=[str(md_file)])))
        result = _search_docs_structured(service, SearchDocsRequest(query="Content"))
        assert len(result["results"]) > 0
        for item in result["results"]:
            assert item.token_count is not None
            assert item.token_count > 0

    def test_search_timeout_raises_mdq_consistency_error(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        """A search exceeding search_timeout_sec raises MdqConsistencyError."""
        import time as _time

        from mcp_servers.mdq.mdq_models import MdqConsistencyError

        f = tmp_path / "slow.md"
        f.write_text("# Title\n\nKeyword content.", encoding="utf-8")
        asyncio.run(index_paths(service, IndexPathsRequest(paths=[str(f)])))
        service.search_timeout_sec = 0.01

        def _slow_search(_service: MdqService, _req: SearchDocsRequest):
            _time.sleep(0.2)
            return {"query": _req.query, "results": [], "total": 0}

        with patch("mcp_servers.mdq.search._search_docs_structured", _slow_search):
            with pytest.raises(MdqConsistencyError, match="timed out"):
                asyncio.run(search_docs(service, SearchDocsRequest(query="Keyword")))


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

    def test_stats_includes_fts_count(self, service: MdqService, md_dir: Path) -> None:
        """stats() includes FTS row count after indexing."""
        asyncio.run(index_paths(service, IndexPathsRequest(paths=[str(md_dir)])))
        result = asyncio.run(service.stats(StatsRequest()))
        assert "FTS rows:" in result

    def test_stats_includes_stale_count(
        self, service: MdqService, md_dir: Path
    ) -> None:
        """stats() includes stale document count (0 immediately after indexing)."""
        asyncio.run(index_paths(service, IndexPathsRequest(paths=[str(md_dir)])))
        result = asyncio.run(service.stats(StatsRequest()))
        assert "Stale:" in result
        assert "Stale: 0," in result

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


# ── chunk ID stability ────────────────────────────────────────────────────────


class TestChunkIdStability:
    def test_generate_chunk_id_deterministic(self) -> None:
        """Same inputs always produce same ID."""
        a = generate_chunk_id("/docs/file.md", "A > B", 1, "abc123")
        b = generate_chunk_id("/docs/file.md", "A > B", 1, "abc123")
        assert a == b

    def test_generate_chunk_id_differs_on_content(self) -> None:
        """Different content_hash produces different ID."""
        a = generate_chunk_id("/docs/file.md", "A", 1, "hash1")
        b = generate_chunk_id("/docs/file.md", "A", 1, "hash2")
        assert a != b

    def test_generate_chunk_id_differs_on_path(self) -> None:
        """Different path produces different ID even with same heading/content."""
        a = generate_chunk_id("/docs/a.md", "A", 1, "hash1")
        b = generate_chunk_id("/docs/b.md", "A", 1, "hash1")
        assert a != b

    def test_chunk_id_stable_across_reindex(
        self, service: MdqService, md_file: Path
    ) -> None:
        """Index same file twice; chunk IDs are identical."""
        import sqlite3  # noqa: PLC0415

        asyncio.run(index_paths(service, IndexPathsRequest(paths=[str(md_file)])))
        conn = sqlite3.connect(service.db_path)
        conn.row_factory = sqlite3.Row
        ids_first = {r["chunk_id"] for r in conn.execute("SELECT chunk_id FROM chunks")}
        conn.close()

        asyncio.run(index_paths(service, IndexPathsRequest(paths=[str(md_file)])))
        conn = sqlite3.connect(service.db_path)
        conn.row_factory = sqlite3.Row
        ids_second = {
            r["chunk_id"] for r in conn.execute("SELECT chunk_id FROM chunks")
        }
        conn.close()

        assert ids_first == ids_second

    def test_chunk_id_changes_on_content_edit(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        """Editing content and re-indexing changes the chunk ID."""
        import sqlite3  # noqa: PLC0415

        f = tmp_path / "edit.md"
        f.write_text("# Title\n\nOriginal content.", encoding="utf-8")
        asyncio.run(index_paths(service, IndexPathsRequest(paths=[str(f)])))
        conn = sqlite3.connect(service.db_path)
        conn.row_factory = sqlite3.Row
        ids_before = {
            r["chunk_id"] for r in conn.execute("SELECT chunk_id FROM chunks")
        }
        conn.close()

        f.write_text("# Title\n\nEdited content.", encoding="utf-8")
        asyncio.run(index_paths(service, IndexPathsRequest(paths=[str(f)])))
        conn = sqlite3.connect(service.db_path)
        conn.row_factory = sqlite3.Row
        ids_after = {r["chunk_id"] for r in conn.execute("SELECT chunk_id FROM chunks")}
        conn.close()

        assert ids_before != ids_after

    def test_search_chunk_id_passthrough(
        self, service: MdqService, md_file: Path
    ) -> None:
        """chunk_id from search result can be passed to get_chunk without error."""
        asyncio.run(index_paths(service, IndexPathsRequest(paths=[str(md_file)])))
        search_result = asyncio.run(
            search_docs(service, SearchDocsRequest(query="Content"))
        )
        assert "Title" in search_result

        import sqlite3  # noqa: PLC0415

        conn = sqlite3.connect(service.db_path)
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT chunk_id FROM chunks LIMIT 1").fetchone()
        conn.close()
        assert row is not None

        result = asyncio.run(
            service.get_chunk(GetChunkRequest(chunk_id=row["chunk_id"]))
        )
        assert "Title" in result or "Content" in result


# ── truncation ────────────────────────────────────────────────────────────────


class TestTruncation:
    def test_search_docs_truncates_by_results_limit(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        """search_docs respects max_results_limit and includes truncation marker."""
        for i in range(5):
            f = tmp_path / f"doc{i}.md"
            f.write_text(f"# Section {i}\n\nKeyword content here.", encoding="utf-8")
        asyncio.run(index_paths(service, IndexPathsRequest(paths=[str(tmp_path)])))
        service.max_results_limit = 2
        result = asyncio.run(search_docs(service, SearchDocsRequest(query="Keyword")))
        assert "Truncated" in result
        assert "results found" in result

    def test_search_docs_truncates_by_char_limit(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        """search_docs respects max_total_result_chars and includes truncation marker."""
        for i in range(3):
            f = tmp_path / f"doc{i}.md"
            f.write_text(f"# Section {i}\n\nKeyword content here.", encoding="utf-8")
        asyncio.run(index_paths(service, IndexPathsRequest(paths=[str(tmp_path)])))
        service.max_total_result_chars = 50
        result = asyncio.run(search_docs(service, SearchDocsRequest(query="Keyword")))
        assert "Truncated" in result
        assert "chars" in result

    def test_get_chunk_truncates_large_content(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        """get_chunk truncates content exceeding max_chars_per_chunk."""
        import sqlite3  # noqa: PLC0415

        f = tmp_path / "big.md"
        f.write_text("# Big\n\n" + "X" * 2000, encoding="utf-8")
        asyncio.run(index_paths(service, IndexPathsRequest(paths=[str(f)])))
        service.max_chars_per_chunk = 100
        conn = sqlite3.connect(service.db_path)
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT chunk_id FROM chunks LIMIT 1").fetchone()
        conn.close()
        result = asyncio.run(
            service.get_chunk(GetChunkRequest(chunk_id=row["chunk_id"]))
        )
        assert "Truncated" in result
        assert "chars" in result

    def test_outline_truncates_large_heading_list(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        """outline truncates when heading count exceeds max_outline_items."""
        headings = "\n\n".join(f"## H{i}\n\nBody." for i in range(10))
        f = tmp_path / "many.md"
        f.write_text(f"# Root\n\n{headings}", encoding="utf-8")
        asyncio.run(index_paths(service, IndexPathsRequest(paths=[str(f)])))
        service.max_outline_items = 3
        result = asyncio.run(service.outline(OutlineRequest(path=str(f))))
        assert "Truncated" in result
        assert "headings found" in result

    def test_grep_docs_truncates_at_match_cap(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        """grep_docs truncates when match cap is reached."""
        for i in range(5):
            f = tmp_path / f"g{i}.md"
            f.write_text(f"# G{i}\n\nfind_me content.", encoding="utf-8")
        asyncio.run(index_paths(service, IndexPathsRequest(paths=[str(tmp_path)])))
        service.max_grep_matches = 2
        result = asyncio.run(service.grep_docs(GrepDocsRequest(pattern="find_me")))
        assert "Truncated" in result
        assert "cap of 2 matches reached" in result

    def test_request_override_bounded_by_config_cap(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        """Per-request max_outline_items cannot exceed config max_outline_items."""
        headings = "\n\n".join(f"## H{i}\n\nBody." for i in range(10))
        f = tmp_path / "bound.md"
        f.write_text(f"# Root\n\n{headings}", encoding="utf-8")
        asyncio.run(index_paths(service, IndexPathsRequest(paths=[str(f)])))
        service.max_outline_items = 3
        result = asyncio.run(
            service.outline(OutlineRequest(path=str(f), max_outline_items=100))
        )
        assert "Truncated" in result


class TestEnableGrepConfig:
    """Verify enable_grep flag controls grep_docs access."""

    def test_grep_docs_disabled_by_config(self, service: MdqService) -> None:
        """When enable_grep=False, grep_docs raises MdqValidationError."""
        from mcp_servers.mdq.mdq_models import MdqValidationError

        service.enable_grep = False
        with pytest.raises(MdqValidationError, match="disabled by configuration"):
            asyncio.run(service.grep_docs(GrepDocsRequest(pattern="test")))

    def test_grep_docs_enabled_by_default(self, service: MdqService) -> None:
        """enable_grep defaults to True — grep_docs should not raise on valid input."""
        assert service.enable_grep is True
