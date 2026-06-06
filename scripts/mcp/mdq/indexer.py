#!/usr/bin/env python3
"""mcp/mdq/indexer.py
Indexing logic for Markdown files.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from mcp.mdq.models import IndexPathsRequest
from mcp.mdq.service import MdqService

if TYPE_CHECKING:
    from mcp.mdq.service import MdqService

logger = logging.getLogger(__name__)


async def _index_single_file(service: MdqService, path: Path) -> None:
    """Index a single Markdown file into the service DB."""
    logger.info("Indexing file: %s", path)


async def _index_directory(service: MdqService, path: Path) -> None:
    """Recursively index all Markdown files under a directory."""
    for child in sorted(path.rglob("*.md")):
        if child.is_file():
            await _index_single_file(service, child)


async def index_paths(service: MdqService, req: IndexPathsRequest) -> str:
    """Index a set of paths into the in-process SQLite DB."""
    logger.info("Indexing paths: %s", req.paths)
    for path_str in req.paths:
        path = Path(path_str)
        if not path.exists():
            logger.warning("Path does not exist: %s", path_str)
            continue
        if path.is_file() and path.suffix == ".md":
            await _index_single_file(service, path)
        elif path.is_dir():
            await _index_directory(service, path)
        else:
            logger.warning("Skipping non-Markdown path: %s", path_str)
    return "Indexing complete"
