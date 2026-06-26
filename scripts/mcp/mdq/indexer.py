#!/usr/bin/env python3
"""mcp/mdq/indexer.py
Indexing logic for Markdown files — writes to SQLite sections table.
"""

from __future__ import annotations

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
        conn.execute("DELETE FROM sections WHERE file_path = ?", (str(path),))

        for section in sections:
            conn.execute(
                "INSERT INTO sections (file_path, heading, content, file_mtime) VALUES (?, ?, ?, ?)",
                (
                    str(path),
                    section["heading"],
                    section["content"],
                    path.stat().st_mtime,
                ),
            )

        conn.commit()
    except sqlite3.Error as e:
        logger.error("Failed to write sections for %s: %s", path, e)
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
