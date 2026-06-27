#!/usr/bin/env python3
"""mcp/mdq/indexer.py
Indexing logic for Markdown files — writes to SQLite documents/chunks tables.
"""

from __future__ import annotations

import hashlib
import logging
import sqlite3
from pathlib import Path
from typing import TYPE_CHECKING

from mcp.mdq.auth import authorize_path
from mcp.mdq.models import IndexPathsRequest, ParseMarkdownRequest
from mcp.mdq.parser import parse_markdown

if TYPE_CHECKING:
    from mcp.mdq.service import MdqService

logger = logging.getLogger(__name__)


async def _index_single_file(service: MdqService, path: Path) -> None:
    """Index a single Markdown file into the service DB."""
    logger.info("Indexing file: %s", path)

    try:
        sections = await parse_markdown(service, ParseMarkdownRequest(path=str(path)))
    except FileNotFoundError as e:
        logger.error("Failed to parse %s: %s", path, e)
        return

    if not sections:
        logger.info("No sections found in %s", path)
        return

    conn = service._get_db_connection()
    try:
        doc_id = hashlib.sha256(str(path).encode()).hexdigest()
        now = path.stat().st_mtime_ns

        # Delete old chunks for this document
        conn.execute("DELETE FROM chunks WHERE doc_id = ?", (doc_id,))

        for section in sections:
            content_hash = hashlib.sha256(section["content"].encode()).hexdigest()
            normalized_content = " ".join(section["content"].split())
            char_count = len(section["content"])

            # Upsert document
            conn.execute(
                "INSERT OR REPLACE INTO documents (doc_id, source_path, mtime_ns, size_bytes, content_hash, indexed_at) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    doc_id,
                    str(path),
                    now,
                    path.stat().st_size,
                    content_hash,
                    path.stat().st_mtime,
                ),
            )

            # Insert chunk with new schema
            conn.execute(
                "INSERT INTO chunks (chunk_id, doc_id, source_path, heading, heading_path, heading_level, ordinal, content, normalized_content, start_line, end_line, char_count, token_count, content_hash, tags_json, indexed_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    hashlib.sha256(
                        f"{doc_id}:{section['heading']}:{section['start_line']}".encode()
                    ).hexdigest(),
                    doc_id,
                    str(path),
                    section["heading"],
                    section.get("heading_path", ""),
                    section.get("heading_level", 0),
                    section.get("ordinal", 0),
                    section["content"],
                    normalized_content,
                    section["start_line"],
                    section["end_line"],
                    char_count,
                    None,
                    content_hash,
                    "",
                    path.stat().st_mtime,
                ),
            )

        conn.commit()
    except sqlite3.Error as e:
        logger.error("Failed to write chunks for %s: %s", path, e)
    finally:
        conn.close()


async def _index_directory(service: MdqService, path: Path) -> None:
    """Recursively index all Markdown files under a directory."""
    for child in sorted(path.rglob("*.md")):
        if child.is_file():
            await _index_single_file(service, child)


async def index_paths(service: MdqService, req: IndexPathsRequest) -> str:
    """Index a set of paths into the in-process SQLite DB."""
    logger.info("Indexing paths: %s", req.paths)
    for path_str in req.paths:
        p = Path(path_str)
        if not p.exists():
            logger.warning("Path does not exist: %s", path_str)
            continue
        if not authorize_path(p, service.allowed_dirs):
            logger.warning("Path denied: %s (outside allowed dirs)", path_str)
            continue
        if p.is_file() and p.suffix == ".md":
            await _index_single_file(service, p)
        elif p.is_dir():
            await _index_directory(service, p)
        else:
            logger.warning("Skipping non-Markdown path: %s", path_str)
    return "Indexing complete"
