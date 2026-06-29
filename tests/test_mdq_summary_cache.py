#!/usr/bin/env python3
"""Tests for MDQ summary cache for large chunks."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from mcp.mdq.models import GetChunkRequest
from mcp.mdq.service import MdqService


@pytest.fixture()
def service(tmp_path: Path) -> MdqService:
    db = tmp_path / "mdq.db"
    svc = MdqService(db_path=str(db))
    svc._allowed_dirs = [str(tmp_path)]
    return svc


class TestSummaryCacheDisabledByDefault:
    """Verify summary cache is disabled by default."""

    def test_summary_cache_disabled_by_default(self, service: MdqService) -> None:
        assert service.summary_cache_enabled is False

    def test_summary_threshold_default(self, service: MdqService) -> None:
        assert service.summary_threshold == 5000

    def test_summary_model_default(self, service: MdqService) -> None:
        assert service.summary_model == "default"


class TestSummaryCacheEnabled:
    """Verify summary cache works when enabled."""

    def test_summary_cache_table_created_when_enabled(self, tmp_path: Path) -> None:
        from mcp.mdq.service import MdqService

        svc = MdqService(db_path=str(tmp_path / "mdq.db"))
        svc._allowed_dirs = [str(tmp_path)]
        svc.summary_cache_enabled = True

        conn = svc._get_db_connection()
        try:
            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
            table_names = {row[0] for row in tables}
            assert "chunk_summaries" in table_names, "chunk_summaries table not created"
        finally:
            conn.close()

    def test_summary_cache_not_used_when_disabled(self, service: MdqService) -> None:
        """When use_summary=True but cache is disabled, raw content is returned."""

        # Create a chunk first via indexing
        db_path = Path(service.db_path)
        md_file = db_path.parent / "test_large_chunk.md"
        md_file.write_text("# Test\n\n" + "x" * 6000)

        conn = service._get_db_connection()
        try:
            doc_id = "test_doc"
            conn.execute(
                "INSERT OR REPLACE INTO documents (doc_id, source_path, mtime_ns, size_bytes, content_hash, indexed_at) VALUES (?, ?, ?, ?, ?, ?)",
                (doc_id, str(md_file), 1234567890, 6000, "hash1", 1.0),
            )
            conn.execute(
                "INSERT INTO chunks (chunk_id, doc_id, source_path, heading, heading_path, heading_level, ordinal, content, normalized_content, start_line, end_line, char_count, token_count, content_hash, tags_json, indexed_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    "test_chunk",
                    doc_id,
                    str(md_file),
                    "Test",
                    "",
                    1,
                    0,
                    "x" * 6000,
                    "x" * 6000,
                    2,
                    6003,
                    6000,
                    None,
                    "hash1",
                    "",
                    1.0,
                ),
            )
            conn.commit()
        finally:
            conn.close()

        req = GetChunkRequest(chunk_id="test_chunk", use_summary=True)
        result = asyncio.run(service.get_chunk(req))
        assert "[Summary" not in result
        assert "x" * 10000 not in result


class TestSummaryCacheWithLargeChunk:
    """Verify summary cache returns cached summary for large chunks."""

    def test_cached_summary_returned_when_available(self, tmp_path: Path) -> None:

        svc = MdqService(db_path=str(tmp_path / "mdq.db"))
        svc._allowed_dirs = [str(tmp_path)]
        svc.summary_cache_enabled = True

        # Create a chunk and its summary
        conn = svc._get_db_connection()
        try:
            doc_id = "test_doc"
            conn.execute(
                "INSERT OR REPLACE INTO documents (doc_id, source_path, mtime_ns, size_bytes, content_hash, indexed_at) VALUES (?, ?, ?, ?, ?, ?)",
                (doc_id, "/test.md", 1234567890, 6000, "hash1", 1.0),
            )
            conn.execute(
                "INSERT INTO chunks (chunk_id, doc_id, source_path, heading, heading_path, heading_level, ordinal, content, normalized_content, start_line, end_line, char_count, token_count, content_hash, tags_json, indexed_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    "test_chunk",
                    doc_id,
                    "/test.md",
                    "Test",
                    "",
                    1,
                    0,
                    "x" * 6000,
                    "x" * 6000,
                    2,
                    6003,
                    6000,
                    None,
                    "hash1",
                    "",
                    1.0,
                ),
            )
            # Insert summary
            conn.execute(
                "INSERT INTO chunk_summaries (chunk_id, summary, summary_model, content_hash, created_at) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)",
                (
                    "test_chunk",
                    "This is a cached summary of the chunk.",
                    "default",
                    "hash1",
                ),
            )
            conn.commit()
        finally:
            conn.close()

        req = GetChunkRequest(chunk_id="test_chunk", use_summary=True)
        result = asyncio.run(svc.get_chunk(req))
        assert "[Summary" in result
        assert "This is a cached summary of the chunk." in result

    def test_raw_content_returned_when_no_cached_summary(self, tmp_path: Path) -> None:
        """When use_summary=True but no cached summary exists, raw content is returned."""

        svc = MdqService(db_path=str(tmp_path / "mdq.db"))
        svc._allowed_dirs = [str(tmp_path)]
        svc.summary_cache_enabled = True

        # Create a chunk without a summary
        conn = svc._get_db_connection()
        try:
            doc_id = "test_doc"
            conn.execute(
                "INSERT OR REPLACE INTO documents (doc_id, source_path, mtime_ns, size_bytes, content_hash, indexed_at) VALUES (?, ?, ?, ?, ?, ?)",
                (doc_id, "/test.md", 1234567890, 6000, "hash1", 1.0),
            )
            conn.execute(
                "INSERT INTO chunks (chunk_id, doc_id, source_path, heading, heading_path, heading_level, ordinal, content, normalized_content, start_line, end_line, char_count, token_count, content_hash, tags_json, indexed_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    "test_chunk",
                    doc_id,
                    "/test.md",
                    "Test",
                    "",
                    1,
                    0,
                    "x" * 6000,
                    "x" * 6000,
                    2,
                    6003,
                    6000,
                    None,
                    "hash1",
                    "",
                    1.0,
                ),
            )
            conn.commit()
        finally:
            conn.close()

        req = GetChunkRequest(chunk_id="test_chunk", use_summary=True)
        result = asyncio.run(svc.get_chunk(req))
        assert "[Summary" not in result
        # Raw content should be returned (truncated to max_chars_per_chunk)
        assert "x" * 10000 not in result

    def test_content_hash_invalidation_invalidates_summary(
        self, tmp_path: Path
    ) -> None:
        """When content hash changes, cached summary is not used."""

        svc = MdqService(db_path=str(tmp_path / "mdq.db"))
        svc._allowed_dirs = [str(tmp_path)]
        svc.summary_cache_enabled = True

        # Create a chunk and its summary with old hash
        conn = svc._get_db_connection()
        try:
            doc_id = "test_doc"
            conn.execute(
                "INSERT OR REPLACE INTO documents (doc_id, source_path, mtime_ns, size_bytes, content_hash, indexed_at) VALUES (?, ?, ?, ?, ?, ?)",
                (doc_id, "/test.md", 1234567890, 6000, "hash2", 1.0),
            )
            conn.execute(
                "INSERT INTO chunks (chunk_id, doc_id, source_path, heading, heading_path, heading_level, ordinal, content, normalized_content, start_line, end_line, char_count, token_count, content_hash, tags_json, indexed_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    "test_chunk",
                    doc_id,
                    "/test.md",
                    "Test",
                    "",
                    1,
                    0,
                    "x" * 6000,
                    "x" * 6000,
                    2,
                    6003,
                    6000,
                    None,
                    "hash2",
                    "",
                    1.0,
                ),
            )
            # Insert summary with old hash (different from chunk content_hash)
            conn.execute(
                "INSERT INTO chunk_summaries (chunk_id, summary, summary_model, content_hash, created_at) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)",
                (
                    "test_chunk",
                    "This is a cached summary of the chunk.",
                    "default",
                    "hash1",  # Different from chunk's hash
                ),
            )
            conn.commit()
        finally:
            conn.close()

        req = GetChunkRequest(chunk_id="test_chunk", use_summary=True)
        result = asyncio.run(svc.get_chunk(req))
        assert "[Summary" not in result  # Stale summary not used
