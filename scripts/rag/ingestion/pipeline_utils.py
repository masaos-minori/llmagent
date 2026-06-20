#!/usr/bin/env python3
"""pipeline_utils.py
Shared I/O utilities for the RAG ingestion pipeline.
"""

from pathlib import Path
from typing import Any

import orjson
from rag.exceptions import ChunkFormatError
from rag.models_data import ChunkDocument
from rag.models_result import SkipInfo
from shared.logger import Logger

logger = Logger(__name__, "/opt/llm/logs/pipeline.log")


def _read_chunk_json_raw(path: Path) -> dict[str, Any] | None:
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
    return data


def read_json_file(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title_raw = data.get("title")
    title = title_raw if isinstance(title_raw, str) else ""
    lang_raw = data.get("lang")
    lang = lang_raw if isinstance(lang_raw, str) else "en"
    code_blocks_raw = data.get("code_blocks")
    code_blocks = list(code_blocks_raw) if isinstance(code_blocks_raw, list) else []
    etag = data.get("etag") if isinstance(data.get("etag"), str) else None
    last_modified = (
        data.get("last_modified")
        if isinstance(data.get("last_modified"), str)
        else None
    )
    chunking_strategy = (
        data.get("chunking_strategy", "text")
        if isinstance(data.get("chunking_strategy"), str)
        else "text"
    )
    nc_raw = data.get("normalized_content")
    normalized_content = nc_raw if isinstance(nc_raw, str) else None
    try:
        chunk_index = int(data.get("chunk_index", 0))
    except (ValueError, TypeError):
        chunk_index = 0
    source_file = data.get("source_file", "") or ""
    chunk_type = data.get("chunk_type", "") or ""
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


def collect_source_files(
    rag_src_dir: Path, target: Path | None = None
) -> tuple[list[Path], list[SkipInfo]]:
    """Return (files_to_process, skipped) from rag_src_dir."""
    if target is not None:
        if not target.exists():
            return [], [SkipInfo(path=str(target), reason="file not found")]
        return [target], []
    files = sorted(rag_src_dir.glob("*.txt"))
    return files, []


def is_already_processed(sentinel_path: Path, force: bool) -> bool:
    """Return True when the sentinel file exists and force=False (skip signal)."""
    return not force and sentinel_path.exists()
