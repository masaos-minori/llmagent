#!/usr/bin/env python3
"""pipeline_utils.py
Shared I/O utilities for the RAG ingestion pipeline.
"""

import logging
from pathlib import Path

import orjson

from rag.exceptions import ChunkFormatError
from rag.models_data import ChunkDocument
from rag.models_result import SkipInfo

logger = logging.getLogger(__name__)


def read_json_file(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    try:
        raw = path.read_bytes()
    except OSError as e:
        raise FileNotFoundError(f"Cannot read {path}: {e}") from e
    try:
        data = orjson.loads(raw)
    except orjson.JSONDecodeError as e:
        raise ChunkFormatError(f"JSON parse error in {path}: {e}") from e
    if not isinstance(data, dict):
        raise ChunkFormatError(
            f"Expected JSON object in {path}, got {type(data).__name__}"
        )
    url = data.get("url")
    content = data.get("content")
    if not isinstance(url, str) or not url:
        raise ChunkFormatError(f"Missing or invalid 'url' in {path}")
    if not isinstance(content, str) or not content:
        raise ChunkFormatError(f"Missing or invalid 'content' in {path}")
    title_raw = data.get("title")
    title = title_raw if isinstance(title_raw, str) else ""
    lang_raw = data.get("lang")
    lang = lang_raw if isinstance(lang_raw, str) else "en"
    code_blocks_raw = data.get("code_blocks")
    code_blocks = list(code_blocks_raw) if isinstance(code_blocks_raw, list) else []
    return ChunkDocument(
        url=url, title=title, lang=lang, content=content, code_blocks=code_blocks
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
