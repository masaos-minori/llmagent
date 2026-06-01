#!/usr/bin/env python3
"""pipeline_utils.py
Shared I/O utilities for the RAG ingestion pipeline.
Used by ChunkSplitter.py and RagIngester.py to eliminate code duplication.

Responsibilities:
  - JSON file reading with uniform error logging
  - Source file enumeration (rag_src_dir/*.txt, excluding chunk/ and registered/)
  - Idempotency check for already-processed files (sentinel-based)
"""

import logging
from pathlib import Path
from typing import Any

import orjson

logger = logging.getLogger(__name__)


def read_json_file(path: Path) -> dict[str, Any] | None:
    """Read and parse a JSON file. Returns None on failure, logging the error."""
    try:
        data = orjson.loads(path.read_bytes())
        return data if isinstance(data, dict) else None
    except (orjson.JSONDecodeError, OSError) as e:
        logger.error(f"failed to read {path}: {e}")
        return None


def collect_source_files(rag_src_dir: Path, target: Path | None = None) -> list[Path]:
    """Return .txt files to process from rag_src_dir.

    When target is given: validate it exists, return [target].
    Without target: glob rag_src_dir/*.txt, sorted (excludes chunk/ and registered/).
    """
    if target is not None:
        if not target.exists():
            logger.error(f"Specified file does not exist: {target}")
            return []
        return [target]
    return sorted(rag_src_dir.glob("*.txt"))


def is_already_processed(sentinel_path: Path, force: bool) -> bool:
    """Return True when the sentinel file exists and force=False (skip signal)."""
    return not force and sentinel_path.exists()
