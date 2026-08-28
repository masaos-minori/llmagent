#!/usr/bin/env python3
"""scripts/rag/ingestion/pipeline_utils.py

Shared I/O utilities for the RAG ingestion pipeline.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, NotRequired, TypedDict, cast

import orjson
from rag.exceptions import ChunkFormatError
from rag.models_data import ChunkDocument
from rag.models_result import SkipInfo
from shared.logger import Logger

logger = Logger(__name__, "/opt/llm/logs/pipeline.log")

# --- Strict TypedDicts for crawl/chunk payloads (Phase 1) ---


class CrawlJsonPayload(TypedDict):
    """Strict TypedDict for crawl JSON payload — all keys mandatory."""

    url: str
    content: str
    title: str | None
    lang: str
    code_blocks: list[str]
    etag: str | None
    last_modified: str | None
    fetched_at: str


class ChunkJsonPayload(TypedDict):
    """Strict TypedDict for chunk JSON payload — all keys mandatory."""

    url: str
    content: str
    title: str | None
    lang: str
    code_blocks: list[str]
    etag: str | None
    last_modified: str | None
    normalized_content: str | None
    chunk_index: int
    source_file: str
    chunk_type: str
    fetched_at: str


def _validate_str(data: dict[str, Any], key: str, label: str) -> str:
    """Validate that *key* maps to a non-empty string; raise ChunkFormatError otherwise."""
    val = data.get(key)
    if not isinstance(val, str) or not val:
        raise ChunkFormatError(f"{label}: missing or invalid '{key}'")
    return val


def _validate_str_or_empty(data: dict[str, Any], key: str, label: str) -> str:
    """Validate that *key* maps to a string (may be empty); reject None/wrong type."""
    val = data.get(key)
    if not isinstance(val, str):
        raise ChunkFormatError(f"{label}: missing or invalid '{key}'")
    return val


def _validate_nullable_str(data: dict[str, Any], key: str, label: str) -> str | None:
    """Validate that *key* maps to str | None (may be absent); raise ChunkFormatError on wrong type."""
    val = data.get(key)
    if val is not None and not isinstance(val, str):
        raise ChunkFormatError(
            f"{label}: '{key}' must be str or null, got {type(val).__name__}"
        )
    return val


def _validate_list_of_str(data: dict[str, Any], key: str, label: str) -> list[str]:
    """Validate that *key* maps to a list[str]; raise ChunkFormatError otherwise."""
    val = data.get(key)
    if not isinstance(val, list):
        raise ChunkFormatError(f"{label}: '{key}' must be list[str]")
    for item in val:
        if not isinstance(item, str):
            raise ChunkFormatError(f"{label}: '{key}' contains non-str element")
    return val


def _validate_int_non_negative(data: dict[str, Any], key: str, label: str) -> int:
    """Validate that *key* maps to a non-negative int; reject bool before int."""
    val = data.get(key)
    if isinstance(val, bool):
        raise ChunkFormatError(f"{label}: '{key}' must not be bool")
    if not isinstance(val, int) or val < 0:
        raise ChunkFormatError(f"{label}: '{key}' must be non-negative int")
    return val


def read_crawl_json(path: Path) -> ChunkDocument:
    """Read and validate a crawl JSON file; return a ChunkDocument.

    Raises ChunkFormatError on any validation failure.
    """
    try:
        raw = path.read_bytes()
    except OSError as e:
        raise ChunkFormatError(f"Failed to read crawl file: {path}: {e}") from e
    try:
        data = orjson.loads(raw)
    except orjson.JSONDecodeError as e:
        raise ChunkFormatError(f"JSON parse error in crawl file {path}: {e}") from e
    if not isinstance(data, dict):
        raise ChunkFormatError(
            f"Expected JSON object in crawl file {path}, got {type(data).__name__}"
        )
    # Exact key-set check
    required_keys = {
        "url",
        "content",
        "title",
        "lang",
        "code_blocks",
        "etag",
        "last_modified",
        "fetched_at",
    }
    actual_keys = set(data.keys())
    missing = required_keys - actual_keys
    if missing:
        raise ChunkFormatError(f"Missing keys in crawl payload: {sorted(missing)}")
    # Per-field validation
    url = _validate_str(data, "url", "crawl")
    content = _validate_str_or_empty(data, "content", "crawl")
    title = _validate_nullable_str(data, "title", "crawl")
    lang = _validate_str(data, "lang", "crawl")
    code_blocks = _validate_list_of_str(data, "code_blocks", "crawl")
    etag = _validate_nullable_str(data, "etag", "crawl")
    last_modified = _validate_nullable_str(data, "last_modified", "crawl")
    fetched_at = _validate_str(data, "fetched_at", "crawl")
    # Cross-field rule: empty content requires non-empty code_blocks
    if not content and not code_blocks:
        raise ChunkFormatError(
            "crawl: empty 'content' requires non-empty 'code_blocks'"
        )
    return ChunkDocument(
        url=url,
        title=title or "",
        lang=lang,
        content=content,
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy="text",
        normalized_content=None,
        chunk_index=0,
        source_file="",
        chunk_type="",
        fetched_at=fetched_at,
    )


def read_chunk_json(path: Path) -> ChunkDocument:
    """Read and validate a chunk JSON file; return ChunkDocument.

    Raises ChunkFormatError on any validation failure.
    """
    try:
        raw = path.read_bytes()
    except OSError as e:
        raise ChunkFormatError(f"Failed to read chunk file: {path}: {e}") from e
    try:
        data = orjson.loads(raw)
    except orjson.JSONDecodeError as e:
        raise ChunkFormatError(f"JSON parse error in chunk file {path}: {e}") from e
    if not isinstance(data, dict):
        raise ChunkFormatError(
            f"Expected JSON object in chunk file {path}, got {type(data).__name__}"
        )
    # Exact key-set check
    required_keys = {
        "url",
        "content",
        "title",
        "lang",
        "code_blocks",
        "etag",
        "last_modified",
        "normalized_content",
        "chunk_index",
        "source_file",
        "chunk_type",
        "chunking_strategy",
        "fetched_at",
    }
    actual_keys = set(data.keys())
    missing = required_keys - actual_keys
    if missing:
        raise ChunkFormatError(f"Missing keys in chunk payload: {sorted(missing)}")
    extra = (
        actual_keys - required_keys - {"schema_version", "artifact_type", "created_by"}
    )
    if extra:
        raise ChunkFormatError(f"Unknown keys in chunk payload: {sorted(extra)}")
    # Per-field validation
    url = _validate_str(data, "url", "chunk")
    content = _validate_str(data, "content", "chunk")
    title = _validate_nullable_str(data, "title", "chunk")
    lang = _validate_str(data, "lang", "chunk")
    code_blocks = _validate_list_of_str(data, "code_blocks", "chunk")
    etag = _validate_nullable_str(data, "etag", "chunk")
    last_modified = _validate_nullable_str(data, "last_modified", "chunk")
    normalized_content = _validate_nullable_str(data, "normalized_content", "chunk")
    chunk_index = _validate_int_non_negative(data, "chunk_index", "chunk")
    source_file = _validate_str_or_empty(data, "source_file", "chunk")
    chunk_type = _validate_str_or_empty(data, "chunk_type", "chunk")
    chunking_strategy = _validate_str(data, "chunking_strategy", "chunk")
    fetched_at = _validate_str(data, "fetched_at", "chunk")
    return ChunkDocument(
        url=url,
        title=title or "",
        lang=lang,
        content=content,
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
        fetched_at=fetched_at,
    )


class ChunkJsonRaw(TypedDict):
    """Typed dict for raw chunk/crawl JSON payload fields."""

    url: str
    content: str
    title: NotRequired[str]
    lang: NotRequired[str]
    code_blocks: NotRequired[list[str]]
    etag: NotRequired[str | None]
    last_modified: NotRequired[str | None]
    fetched_at: str
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
    fetched_at = _get_str(data, "fetched_at")
    if fetched_at is None:
        raise ChunkFormatError("chunk: missing or invalid 'fetched_at'")
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
        fetched_at=fetched_at,
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
