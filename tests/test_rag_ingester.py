"""tests/test_rag_ingester.py
Unit tests for rag/ingestion/ingester.py _read_chunk_json() field preservation.

Covers BUG-1 (chunking_strategy), BUG-2 (normalized_content), BUG-3 (chunk_index).
"""

from __future__ import annotations

from pathlib import Path

import orjson
from rag.ingestion.ingester import RagIngester


def _make_ingester() -> RagIngester:
    """Construct RagIngester with minimal config (no real embed/DB needed)."""
    return RagIngester(
        config={
            "rag_src_dir": "/tmp/rag-src",
            "embed_url": "http://localhost:8003/embedding",
            "embed_retry": "1",
        }
    )


def _write_chunk(tmp_path: Path, data: dict) -> Path:
    path = tmp_path / "chunk_001.txt"
    path.write_bytes(orjson.dumps(data))
    return path


class TestReadChunkJsonFieldPreservation:
    """BUG-1/2/3: _read_chunk_json must return all JSON fields, not just ChunkDocument fields."""

    def test_chunking_strategy_preserved(self, tmp_path: Path) -> None:
        """BUG-1: chunking_strategy must not be silently dropped."""
        path = _write_chunk(
            tmp_path,
            {
                "url": "https://example.com/doc",
                "content": "text content",
                "chunking_strategy": "heading",
            },
        )
        ingester = _make_ingester()
        data = ingester._read_chunk_json(path)
        assert data is not None
        assert data["chunking_strategy"] == "heading"

    def test_normalized_content_preserved(self, tmp_path: Path) -> None:
        """BUG-2: normalized_content must survive the JSON read (not hardcoded to None)."""
        path = _write_chunk(
            tmp_path,
            {
                "url": "https://example.com/doc",
                "content": "original text",
                "normalized_content": "normalized form",
            },
        )
        ingester = _make_ingester()
        data = ingester._read_chunk_json(path)
        assert data is not None
        assert data["normalized_content"] == "normalized form"

    def test_chunk_index_preserved(self, tmp_path: Path) -> None:
        """BUG-3: chunk_index must be read from JSON, not hardcoded to 0."""
        path = _write_chunk(
            tmp_path,
            {
                "url": "https://example.com/doc",
                "content": "text",
                "chunk_index": 5,
            },
        )
        ingester = _make_ingester()
        data = ingester._read_chunk_json(path)
        assert data is not None
        assert data["chunk_index"] == 5

    def test_all_extra_fields_preserved(self, tmp_path: Path) -> None:
        """All JSON fields beyond the old ChunkDocument fields are preserved."""
        payload = {
            "url": "https://example.com/doc",
            "content": "text",
            "title": "Title",
            "lang": "ja",
            "chunking_strategy": "heading",
            "normalized_content": "normalized",
            "chunk_index": 3,
            "etag": "abc123",
            "last_modified": "Wed, 01 Jan 2025 00:00:00 GMT",
        }
        path = _write_chunk(tmp_path, payload)
        ingester = _make_ingester()
        data = ingester._read_chunk_json(path)
        assert data is not None
        for key, value in payload.items():
            assert data[key] == value


class TestReadChunkJsonErrorHandling:
    """_read_chunk_json must return None on invalid input without raising."""

    def test_missing_file_returns_none(self, tmp_path: Path) -> None:
        ingester = _make_ingester()
        result = ingester._read_chunk_json(tmp_path / "nonexistent.txt")
        assert result is None

    def test_invalid_json_returns_none(self, tmp_path: Path) -> None:
        path = tmp_path / "bad.txt"
        path.write_bytes(b"not json {")
        ingester = _make_ingester()
        result = ingester._read_chunk_json(path)
        assert result is None

    def test_missing_url_returns_none(self, tmp_path: Path) -> None:
        path = _write_chunk(tmp_path, {"content": "text"})
        ingester = _make_ingester()
        result = ingester._read_chunk_json(path)
        assert result is None

    def test_missing_content_returns_none(self, tmp_path: Path) -> None:
        path = _write_chunk(tmp_path, {"url": "https://example.com/doc"})
        ingester = _make_ingester()
        result = ingester._read_chunk_json(path)
        assert result is None

    def test_non_object_json_returns_none(self, tmp_path: Path) -> None:
        path = tmp_path / "array.txt"
        path.write_bytes(orjson.dumps([1, 2, 3]))
        ingester = _make_ingester()
        result = ingester._read_chunk_json(path)
        assert result is None
