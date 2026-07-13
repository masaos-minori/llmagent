#!/usr/bin/env python3
"""pipeline_utils.py
Shared I/O utilities for the RAG ingestion pipeline.
"""

from pathlib import Path
from typing import NotRequired, TypedDict, cast

import orjson
from rag.exceptions import ChunkFormatError
from rag.models_data import ChunkDocument
from rag.models_result import SkipInfo
from shared.logger import Logger

logger = Logger(__name__, "/opt/llm/logs/pipeline.log")


class ChunkJsonRaw(TypedDict):
    """Typed dict for raw chunk/crawl JSON payload fields."""

    url: str
    content: str
    title: NotRequired[str]
    lang: NotRequired[str]
    code_blocks: NotRequired[list[str]]
    etag: NotRequired[str | None]
    last_modified: NotRequired[str | None]
    fetched_at: NotRequired[str | None]
    chunking_strategy: NotRequired[str]
    normalized_content: NotRequired[str | None]
    chunk_index: NotRequired[int]
    source_file: NotRequired[str]
    chunk_type: NotRequired[str]
    artifact_type: NotRequired[
        str
    ]  # ingestion-pipeline metadata only; not persisted to DB
    schema_version: NotRequired[str]
    created_by: NotRequired[str]


def _read_chunk_json_raw(path: Path) -> ChunkJsonRaw | None:
    """Read and parse a chunk JSON file as a raw dict; returns None on any failure."""
    try:
        raw = path.read_bytes()
    except OSError as e:
        logger.warning("skip chunk %s: %s", path.name, e)
        return None
    try:
        data = orjson.loads(raw)
    except orjson.JSONDecodeError as e:
        logger.warning("skip chunk %s: JSON parse error: %s", path.name, e)
        return None
    if not isinstance(data, dict):
        logger.warning(
            "skip chunk %s: expected JSON object, got %s",
            path.name,
            type(data).__name__,
        )
        return None
    url = data.get("url")
    content = data.get("content")
    if not isinstance(url, str) or not url:
        logger.warning("skip chunk %s: missing or invalid 'url'", path.name)
        return None
    if not isinstance(content, str) or not content:
        logger.warning("skip chunk %s: missing or invalid 'content'", path.name)
        return None
    return cast(ChunkJsonRaw, data)


def read_json_file(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def _get_str(data: ChunkJsonRaw, key: str) -> str | None:
    """Get a string value from data."""
    val = data.get(key)
    return val if isinstance(val, str) else None


def _get_list(data: ChunkJsonRaw, key: str) -> list[str] | None:
    """Get a list value from data."""
    val = data.get(key)
    return list(val) if isinstance(val, list) else None


def _get_str_with_default(data: ChunkJsonRaw, key: str, default: str) -> str:
    """Get a string value with default fallback."""
    val = data.get(key)
    return val if isinstance(val, str) else default


def _get_int_with_default(data: ChunkJsonRaw, key: str, default: int) -> int:
    """Get an integer value with default fallback."""
    val = data.get(key)
    if val is None:
        return default
    try:
        return int(val)  # type: ignore[call-overload, no-any-return]
    except (ValueError, TypeError):
        return default


def collect_source_files(
    rag_src_dir: Path, target: Path | None = None
) -> tuple[list[Path], list[SkipInfo]]:
    """Return (files_to_process, skipped) from rag_src_dir."""
    if target is not None:
        if not target.exists():
            return [], [SkipInfo(path=str(target), reason="file not found")]
        return [target], []
    files = sorted(rag_src_dir.glob("*.json"))
    return files, []


def is_already_processed(sentinel_path: Path, force: bool) -> bool:
    """Return True when the sentinel file exists and force=False (skip signal)."""
    return not force and sentinel_path.exists()
