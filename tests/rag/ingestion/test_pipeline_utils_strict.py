"""
tests/rag/ingestion/test_pipeline_utils_strict.py

Unit tests for the strict TypedDict/reader pairs added to
scripts/rag/ingestion/pipeline_utils.py (Phase 1).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from rag.exceptions import ChunkFormatError
from rag.ingestion.pipeline_utils import (
    read_chunk_json,
    read_crawl_json,
)

# --- Helper fixtures ---


def _make_tmp_file(tmp_path: Path, data: dict[str, Any]) -> Path:
    """Write *data* as JSON to a temp file and return its path."""
    p = tmp_path / "payload.json"
    p.write_text(json.dumps(data))
    return p


CRAWL_PAYLOAD: dict[str, Any] = {
    "url": "https://example.com/page",
    "content": "some text",
    "title": "Page Title",
    "lang": "en",
    "code_blocks": ["print('hello')"],
    "etag": "abc123",
    "last_modified": "2024-01-01T00:00:00Z",
    "fetched_at": "2024-01-01T00:00:00Z",
}

CHUNK_PAYLOAD: dict[str, Any] = {
    "url": "https://example.com/page",
    "content": "chunked text",
    "title": "Chunk Title",
    "lang": "en",
    "code_blocks": [],
    "etag": "xyz789",
    "last_modified": "2024-01-01T00:00:00Z",
    "normalized_content": "normalized text",
    "chunk_index": 0,
    "source_file": "",
    "chunk_type": "text",
    "chunking_strategy": "text",
    "fetched_at": "2024-01-01T00:00:00Z",
}

# --- read_crawl_json tests ---


class TestReadCrawlJson:
    def test_success_case(self, tmp_path: Path) -> None:
        result = read_crawl_json(_make_tmp_file(tmp_path, CRAWL_PAYLOAD))
        assert result.url == CRAWL_PAYLOAD["url"]
        assert result.content == CRAWL_PAYLOAD["content"]
        assert result.title == CRAWL_PAYLOAD["title"]
        assert result.lang == CRAWL_PAYLOAD["lang"]
        assert result.code_blocks == CRAWL_PAYLOAD["code_blocks"]
        assert result.etag == CRAWL_PAYLOAD["etag"]
        assert result.last_modified == CRAWL_PAYLOAD["last_modified"]

    def test_missing_key_raises(self, tmp_path: Path) -> None:
        data = dict(CRAWL_PAYLOAD)
        del data["title"]
        with pytest.raises(ChunkFormatError, match="Missing keys"):
            read_crawl_json(_make_tmp_file(tmp_path, data))

    def test_non_dict_json_raises(self, tmp_path: Path) -> None:
        p = tmp_path / "arr.json"
        p.write_text("[1, 2, 3]")
        with pytest.raises(ChunkFormatError, match="Expected JSON object"):
            read_crawl_json(p)

    def test_invalid_json_raises(self, tmp_path: Path) -> None:
        p = tmp_path / "bad.json"
        p.write_text("{invalid json}")
        with pytest.raises(ChunkFormatError, match="JSON parse error"):
            read_crawl_json(p)

    def test_missing_file_raises(self, tmp_path: Path) -> None:
        with pytest.raises(ChunkFormatError, match="Failed to read"):
            read_crawl_json(tmp_path / "nonexistent.json")

    def test_empty_content_requires_code_blocks(self, tmp_path: Path) -> None:
        data = dict(CRAWL_PAYLOAD)
        data["content"] = ""
        data["code_blocks"] = []
        with pytest.raises(ChunkFormatError, match="empty 'content' requires"):
            read_crawl_json(_make_tmp_file(tmp_path, data))

    def test_empty_content_with_code_blocks_ok(self, tmp_path: Path) -> None:
        data = dict(CRAWL_PAYLOAD)
        data["content"] = ""
        data["code_blocks"] = ["code"]
        result = read_crawl_json(_make_tmp_file(tmp_path, data))
        assert result.content == ""

    def test_null_etag_accepted(self, tmp_path: Path) -> None:
        data = dict(CRAWL_PAYLOAD)
        data["etag"] = None
        result = read_crawl_json(_make_tmp_file(tmp_path, data))
        assert result.etag is None

    def test_null_last_modified_accepted(self, tmp_path: Path) -> None:
        data = dict(CRAWL_PAYLOAD)
        data["last_modified"] = None
        result = read_crawl_json(_make_tmp_file(tmp_path, data))
        assert result.last_modified is None

    def test_wrong_type_for_string_field_raises(self, tmp_path: Path) -> None:
        data = dict(CRAWL_PAYLOAD)
        data["lang"] = 123
        with pytest.raises(ChunkFormatError, match="missing or invalid"):
            read_crawl_json(_make_tmp_file(tmp_path, data))

    def test_bool_rejected_as_int(self, tmp_path: Path) -> None:
        # bool check happens before int check — should reject bool
        data = dict(CRAWL_PAYLOAD)
        data["chunk_index"] = True
        # Note: crawl doesn't have chunk_index, so this won't trigger
        # This test is for read_chunk_json below


# --- read_chunk_json tests ---


class TestReadChunkJson:
    def test_success_case(self, tmp_path: Path) -> None:
        from rag.models_data import ChunkDocument

        result = read_chunk_json(_make_tmp_file(tmp_path, CHUNK_PAYLOAD))
        assert isinstance(result, ChunkDocument)
        assert result.url == CHUNK_PAYLOAD["url"]
        assert result.content == CHUNK_PAYLOAD["content"]
        assert result.title == CHUNK_PAYLOAD["title"]
        assert result.lang == CHUNK_PAYLOAD["lang"]
        assert result.code_blocks == CHUNK_PAYLOAD["code_blocks"]
        assert result.etag == CHUNK_PAYLOAD["etag"]
        assert result.last_modified == CHUNK_PAYLOAD["last_modified"]
        assert result.normalized_content == CHUNK_PAYLOAD["normalized_content"]
        assert result.chunk_index == CHUNK_PAYLOAD["chunk_index"]
        assert result.source_file == CHUNK_PAYLOAD["source_file"]
        assert result.chunk_type == CHUNK_PAYLOAD["chunk_type"]

    def test_missing_key_raises(self, tmp_path: Path) -> None:
        data = dict(CHUNK_PAYLOAD)
        del data["chunk_type"]
        with pytest.raises(ChunkFormatError, match="Missing keys"):
            read_chunk_json(_make_tmp_file(tmp_path, data))

    def test_extra_key_raises(self, tmp_path: Path) -> None:
        data = dict(CHUNK_PAYLOAD)
        data["unknown_field"] = "bad"
        with pytest.raises(ChunkFormatError, match="Unknown keys"):
            read_chunk_json(_make_tmp_file(tmp_path, data))

    def test_non_dict_json_raises(self, tmp_path: Path) -> None:
        p = tmp_path / "arr.json"
        p.write_text("[1, 2, 3]")
        with pytest.raises(ChunkFormatError, match="Expected JSON object"):
            read_chunk_json(p)

    def test_invalid_json_raises(self, tmp_path: Path) -> None:
        p = tmp_path / "bad.json"
        p.write_text("{invalid json}")
        with pytest.raises(ChunkFormatError, match="JSON parse error"):
            read_chunk_json(p)

    def test_missing_file_raises(self, tmp_path: Path) -> None:
        with pytest.raises(ChunkFormatError, match="Failed to read"):
            read_chunk_json(tmp_path / "nonexistent.json")

    def test_null_etag_accepted(self, tmp_path: Path) -> None:
        data = dict(CHUNK_PAYLOAD)
        data["etag"] = None
        result = read_chunk_json(_make_tmp_file(tmp_path, data))
        assert result.etag is None

    def test_null_normalized_content_accepted(self, tmp_path: Path) -> None:
        data = dict(CHUNK_PAYLOAD)
        data["normalized_content"] = None
        result = read_chunk_json(_make_tmp_file(tmp_path, data))
        assert result.normalized_content is None

    def test_bool_rejected_as_int(self, tmp_path: Path) -> None:
        data = dict(CHUNK_PAYLOAD)
        data["chunk_index"] = True
        with pytest.raises(ChunkFormatError, match="must not be bool"):
            read_chunk_json(_make_tmp_file(tmp_path, data))

    def test_negative_chunk_index_raises(self, tmp_path: Path) -> None:
        data = dict(CHUNK_PAYLOAD)
        data["chunk_index"] = -1
        with pytest.raises(ChunkFormatError, match="must be non-negative"):
            read_chunk_json(_make_tmp_file(tmp_path, data))

    def test_list_element_non_str_raises(self, tmp_path: Path) -> None:
        data = dict(CHUNK_PAYLOAD)
        data["code_blocks"] = [123]
        with pytest.raises(ChunkFormatError, match="contains non-str element"):
            read_chunk_json(_make_tmp_file(tmp_path, data))

    def test_title_defaults_to_empty_when_none(self, tmp_path: Path) -> None:
        data = dict(CHUNK_PAYLOAD)
        data["title"] = None
        result = read_chunk_json(_make_tmp_file(tmp_path, data))
        assert result.title == ""
