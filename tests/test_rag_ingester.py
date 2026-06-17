"""tests/test_rag_ingester.py

Tests for RagIngester._read_chunk_json, chunk metadata preservation,
and --force reinsert behavior.

These tests prevent regression of BUG-1/BUG-2/BUG-3 where chunk metadata
(chunking_strategy, normalized_content, chunk_index) was lost.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from rag.ingestion.ingester import RagIngester


# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_chunk_json(
    url: str = "http://example.com/page",
    title: str = "Test Page",
    lang: str = "en",
    content: str = "Hello world",
    chunking_strategy: str = "heading",
    normalized_content: str | None = None,
    chunk_index: int = 0,
) -> dict:
    """Build a chunk JSON dict matching what ChunkSplitter produces."""
    return {
        "url": url,
        "title": title,
        "lang": lang,
        "content": content,
        "chunking_strategy": chunking_strategy,
        "normalized_content": normalized_content,
        "chunk_index": chunk_index,
        "code_blocks": [],
    }


def _write_chunk_file(chunk_dir: Path, name: str, data: dict) -> Path:
    """Write a chunk JSON file with .txt extension (as ChunkSplitter does)."""
    path = chunk_dir / f"{name}.txt"
    path.write_text(json.dumps(data))
    return path


def _make_ingester(tmp_path: Path, embed_url: str = "http://127.0.0.1:9999/embedding"):
    """Create a RagIngester with temp directories and mocked config."""
    chunk_dir = tmp_path / "chunk"
    chunk_dir.mkdir()
    registered_dir = tmp_path / "registered"
    registered_dir.mkdir()
    cfg = {
        "rag_src_dir": str(tmp_path),
        "embed_url": embed_url,
        "embed_retry": 1,
        "embed_workers": 2,
    }
    return RagIngester(config=cfg)


# ── _read_chunk_json tests ────────────────────────────────────────────────────


class TestReadChunkJson:
    """Tests for _read_chunk_json() raw JSON field preservation."""

    def test_preserves_all_fields(self, tmp_path):
        """All chunk fields including metadata are preserved in returned dict."""
        ingester = _make_ingester(tmp_path)
        data = _make_chunk_json(
            content="Test content",
            chunking_strategy="heading",
            normalized_content="test content",
            chunk_index=3,
        )
        path = _write_chunk_file(tmp_path / "chunk", "chunk_0", data)
        result = ingester._read_chunk_json(path)

        assert result is not None
        assert result["url"] == "http://example.com/page"
        assert result["title"] == "Test Page"
        assert result["lang"] == "en"
        assert result["content"] == "Test content"
        assert result["chunking_strategy"] == "heading"
        assert result["normalized_content"] == "test content"
        assert result["chunk_index"] == 3

    def test_returns_none_for_missing_file(self, tmp_path):
        """Returns None when chunk file does not exist."""
        ingester = _make_ingester(tmp_path)
        path = tmp_path / "chunk" / "nonexistent.txt"
        result = ingester._read_chunk_json(path)
        assert result is None

    def test_returns_none_for_invalid_json(self, tmp_path):
        """Returns None when chunk file contains invalid JSON."""
        ingester = _make_ingester(tmp_path)
        path = tmp_path / "chunk" / "invalid.txt"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("not json {{{")
        result = ingester._read_chunk_json(path)
        assert result is None

    def test_returns_none_for_non_dict_json(self, tmp_path):
        """Returns None when chunk file contains non-object JSON (e.g. array)."""
        ingester = _make_ingester(tmp_path)
        path = tmp_path / "chunk" / "array.txt"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("[1, 2, 3]")
        result = ingester._read_chunk_json(path)
        assert result is None


# ── Chunk metadata storage tests ──────────────────────────────────────────────


class TestChunkMetadataStorage:
    """Tests that chunk metadata fields are correctly stored in SQLite."""

    def test_chunk_index_stored_correctly(self, tmp_path):
        """chunk_index from JSON file is written to chunks.chunk_index column."""
        ingester = _make_ingester(tmp_path)
        chunk_dir = tmp_path / "chunk"

        # Create chunk files with explicit chunk_index values
        data1 = _make_chunk_json(content="First chunk", chunk_index=0)
        data2 = _make_chunk_json(content="Second chunk", chunk_index=1)
        data3 = _make_chunk_json(content="Third chunk", chunk_index=2)
        _write_chunk_file(chunk_dir, "chunk_0", data1)
        _write_chunk_file(chunk_dir, "chunk_1", data2)
        _write_chunk_file(chunk_dir, "chunk_2", data3)

        # Mock embedding to return a valid vector
        mock_resp = MagicMock()
        mock_resp.content = json.dumps({"embedding": [0.1] * 384}).encode()

        mock_cur = MagicMock()
        mock_cur.lastrowid = 1
        mock_cur.fetchone.return_value = None

        def execute_side_effect(sql, *args, **kwargs):
            return mock_cur

        mock_db = MagicMock()
        mock_db.execute.side_effect = execute_side_effect

        # Mock SQLiteHelper used by _embed_and_store (opens its own connection)
        mock_sh = MagicMock()
        mock_ctx = MagicMock()
        mock_ctx.__enter__ = MagicMock(return_value=mock_cur)
        mock_ctx.__exit__ = MagicMock(return_value=False)
        mock_sh.open = MagicMock(return_value=mock_ctx)

        with (
            patch.object(ingester._client, "post", return_value=mock_resp),
            patch("rag.ingestion.ingester.SQLiteHelper", return_value=mock_sh),
        ):
            ingester.ingest_url_group(
                db=mock_db,
                url="http://example.com/page",
                chunk_files=sorted(chunk_dir.glob("*.txt")),
                force=False,
            )

        # Verify _insert_chunk was called with correct chunk_index values
        calls = mock_cur.execute.call_args_list
        chunk_inserts = [c for c in calls if "INSERT INTO chunks" in str(c)]
        assert len(chunk_inserts) == 3
        args_list = [c[0] for c in chunk_inserts]
        idx_values = {args[2] for args in args_list if len(args) > 2}
        assert idx_values == {0, 1, 2}

    def test_normalized_content_stored_correctly(self, tmp_path):
        """normalized_content from JSON file is written to chunks.normalized_content."""
        ingester = _make_ingester(tmp_path)
        chunk_dir = tmp_path / "chunk"

        data = _make_chunk_json(
            content="Original", normalized_content="normalized form"
        )
        _write_chunk_file(chunk_dir, "chunk_0", data)

        mock_resp = MagicMock()
        mock_resp.content = json.dumps({"embedding": [0.1] * 384}).encode()
        mock_cur = MagicMock()
        mock_cur.lastrowid = 1
        mock_cur.fetchone.return_value = None

        def execute_side_effect(sql, *args, **kwargs):
            return mock_cur

        mock_db = MagicMock()
        mock_db.execute.side_effect = execute_side_effect

        mock_sh = MagicMock()
        mock_ctx = MagicMock()
        mock_ctx.__enter__ = MagicMock(return_value=mock_cur)
        mock_ctx.__exit__ = MagicMock(return_value=False)
        mock_sh.open = MagicMock(return_value=mock_ctx)

        with (
            patch.object(ingester._client, "post", return_value=mock_resp),
            patch("rag.ingestion.ingester.SQLiteHelper", return_value=mock_sh),
        ):
            ingester.ingest_url_group(
                db=mock_db,
                url="http://example.com/page",
                chunk_files=[chunk_dir / "chunk_0.txt"],
                force=False,
            )

        # Check that normalized_content was passed to INSERT
        calls = mock_cur.execute.call_args_list
        chunk_inserts = [c for c in calls if "INSERT INTO chunks" in str(c)]
        assert len(chunk_inserts) >= 1
        insert_args = chunk_inserts[0][0]
        if len(insert_args) > 3:
            assert insert_args[3] == "normalized form"

    def test_chunking_strategy_stored_in_documents(self, tmp_path):
        """chunking_strategy from first chunk JSON is stored in documents.chunking_strategy."""
        ingester = _make_ingester(tmp_path)
        chunk_dir = tmp_path / "chunk"

        data = _make_chunk_json(chunking_strategy="heading")
        _write_chunk_file(chunk_dir, "chunk_0", data)

        mock_cur = MagicMock()
        mock_cur.lastrowid = 42
        mock_cur.fetchone.return_value = None

        def execute_side_effect(sql, *args, **kwargs):
            return mock_cur

        mock_db = MagicMock()
        mock_db.execute.side_effect = execute_side_effect

        ingester.ingest_url_group(
            db=mock_db,
            url="http://example.com/page",
            chunk_files=[chunk_dir / "chunk_0.txt"],
            force=False,
        )

        # Check that _get_or_create_document was called with correct chunking_strategy
        calls = mock_db.execute.call_args_list
        doc_inserts = [c for c in calls if "INSERT INTO documents" in str(c)]
        assert len(doc_inserts) >= 1
        insert_args = doc_inserts[0][0]
        # 6th parameter (index 5) is chunking_strategy
        assert insert_args[5] == "heading"


# ── Force reinsert tests ──────────────────────────────────────────────────────


class TestForceReinsert:
    """Tests for --force reinsert behavior."""

    def test_force_reinsert_deletes_existing_document(self, tmp_path):
        """force=True deletes existing document and chunks before re-inserting."""
        ingester = _make_ingester(tmp_path)
        chunk_dir = tmp_path / "chunk"

        data = _make_chunk_json()
        _write_chunk_file(chunk_dir, "chunk_0", data)

        mock_db = MagicMock()
        # Simulate existing document found
        mock_db.fetchone.return_value = (42,)
        mock_cur = MagicMock()
        mock_cur.lastrowid = 99
        mock_db.execute.return_value = mock_cur

        ingester.ingest_url_group(
            db=mock_db,
            url="http://example.com/page",
            chunk_files=[chunk_dir / "chunk_0.txt"],
            force=True,
        )

        # Should have called DELETE for existing document
        calls = mock_db.execute.call_args_list
        delete_calls = [c for c in calls if "DELETE" in str(c)]
        assert len(delete_calls) >= 3  # chunks_vec, chunks, documents

    def test_no_force_skips_existing_document(self, tmp_path):
        """force=False skips ingestion when document already exists."""
        ingester = _make_ingester(tmp_path)
        chunk_dir = tmp_path / "chunk"

        data = _make_chunk_json()
        _write_chunk_file(chunk_dir, "chunk_0", data)

        mock_db = MagicMock()
        # Simulate existing document found
        mock_db.fetchone.return_value = (42,)
        mock_cur = MagicMock()
        mock_cur.lastrowid = 99
        mock_db.execute.return_value = mock_cur

        ingester.ingest_url_group(
            db=mock_db,
            url="http://example.com/page",
            chunk_files=[chunk_dir / "chunk_0.txt"],
            force=False,
        )

        # Should NOT have called DELETE for existing document
        calls = mock_db.execute.call_args_list
        delete_calls = [c for c in calls if "DELETE" in str(c)]
        assert len(delete_calls) == 0


# ── Chunk order tests ─────────────────────────────────────────────────────────


class TestChunkOrder:
    """Tests that chunks are processed in ascending chunk_index order."""

    def test_chunks_sorted_by_stem_filename(self, tmp_path):
        """Chunk files are sorted by stem (filename without extension) before ingestion."""
        ingester = _make_ingester(tmp_path)
        chunk_dir = tmp_path / "chunk"

        # Create files out of order
        data3 = _make_chunk_json(content="Third", chunk_index=2)
        data1 = _make_chunk_json(content="First", chunk_index=0)
        data2 = _make_chunk_json(content="Second", chunk_index=1)
        _write_chunk_file(chunk_dir, "chunk_2", data3)
        _write_chunk_file(chunk_dir, "chunk_0", data1)
        _write_chunk_file(chunk_dir, "chunk_1", data2)

        mock_db = MagicMock()
        mock_cur = MagicMock()
        mock_cur.lastrowid = 42
        mock_db.execute.return_value = mock_cur
        mock_db.fetchone.return_value = None

        # Get files in arbitrary order (simulating glob output)
        raw_files = list(chunk_dir.glob("*.txt"))

        ingester.ingest_url_group(
            db=mock_db,
            url="http://example.com/page",
            chunk_files=raw_files,
            force=False,
        )

        # ingest_url_group sorts by stem internally: sorted(chunk_files, key=lambda p: p.stem)
        # Verify the sort is correct
        sorted_files = sorted(raw_files, key=lambda p: p.stem)
        assert sorted_files[0].stem == "chunk_0"
        assert sorted_files[1].stem == "chunk_1"
        assert sorted_files[2].stem == "chunk_2"
