#!/usr/bin/env python3
"""mcp/mdq/service.py
Service layer for Markdown Context Compression Engine MCP Server.
"""

from __future__ import annotations

import logging
from pathlib import Path

import orjson
from fastapi import HTTPException

from mcp.mdq.indexer import Indexer
from mcp.mdq.models import (
    ChunkResponse,
    GetChunkRequest,
    GrepDocsRequest,
    GrepDocsResponse,
    IndexPathsRequest,
    IndexPathsResponse,
    OutlineEntry,
    OutlineRequest,
    OutlineResponse,
    RefreshIndexRequest,
    RefreshIndexResponse,
    SearchDocsHit,
    SearchDocsRequest,
    SearchDocsResponse,
    StatsRequest,
    StatsResponse,
)
from mcp.mdq.parser import parse_markdown_file
from mcp.mdq.search import search_chunks

logger = logging.getLogger(__name__)


def _dump(obj: object) -> str:
    """Serialize obj to an indented JSON string; return type is str, not bytes."""
    result: str = orjson.dumps(obj, option=orjson.OPT_INDENT_2).decode()
    return result


class MdqService:
    """Service class for Markdown Context Compression Engine."""

    def __init__(self) -> None:
        self._indexer = Indexer()
        self._db_path = self._indexer.db_path

    async def search_docs(self, request: SearchDocsRequest) -> str:
        """Search for Markdown documents matching the query."""
        try:
            hits = search_chunks(
                query=request.query,
                limit=request.limit,
                mode=request.mode,
                path_prefix=request.path_prefix,
                tag_filter=request.tag_filter,
                heading_prefix=request.heading_prefix,
            )
            response = SearchDocsResponse(
                hits=[SearchDocsHit(**hit) for hit in hits],
                total_hits=len(hits),
            )
            return _dump(response)
        except Exception as e:
            logger.error(f"Error in search_docs: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Search error: {e}")

    async def get_chunk(self, request: GetChunkRequest) -> str:
        """Get a specific chunk by ID."""
        try:
            chunk = self._indexer.get_chunk(request.chunk_id)
            if not chunk:
                raise HTTPException(status_code=404, detail="Chunk not found")

            response = ChunkResponse(
                chunk_id=chunk["chunk_id"],
                source_path=chunk["source_path"],
                heading_path=chunk["heading_path"],
                content=chunk["content"],
                token_count=chunk["token_count"],
                tags=chunk["tags"],
                chunk_order=chunk["chunk_order"],
            )
            return _dump(response)
        except Exception as e:
            logger.error(f"Error in get_chunk: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Get chunk error: {e}")

    async def outline(self, request: OutlineRequest) -> str:
        """Get the outline of a Markdown file."""
        try:
            if not Path(request.path).exists():
                raise HTTPException(status_code=404, detail="File not found")

            # Parse the file to get the outline
            outline_data = parse_markdown_file(request.path)

            response = OutlineResponse(
                path=request.path,
                title=outline_data.get("title", ""),
                outline=[
                    OutlineEntry(
                        heading_path=entry["heading_path"],
                        heading_level=entry["heading_level"],
                        chunk_id=entry["chunk_id"],
                        token_count=entry["token_count"],
                    )
                    for entry in outline_data.get("outline", [])
                ],
            )
            return _dump(response)
        except Exception as e:
            logger.error(f"Error in outline: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Outline error: {e}")

    async def index_paths(self, request: IndexPathsRequest) -> str:
        """Index a set of paths."""
        try:
            indexed_paths = self._indexer.index_paths(request.paths)
            response = IndexPathsResponse(
                indexed_paths=indexed_paths,
                total_docs=len(indexed_paths),
            )
            return _dump(response)
        except Exception as e:
            logger.error(f"Error in index_paths: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Index paths error: {e}")

    async def refresh_index(self, request: RefreshIndexRequest) -> str:
        """Refresh the index for a set of paths."""
        try:
            updated_paths = self._indexer.refresh_paths(request.paths)
            response = RefreshIndexResponse(
                updated_paths=updated_paths,
                total_docs=len(updated_paths),
            )
            return _dump(response)
        except Exception as e:
            logger.error(f"Error in refresh_index: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Refresh index error: {e}")

    async def stats(self, request: StatsRequest) -> str:
        """Get statistics about the index."""
        try:
            stats = self._indexer.get_stats()
            response = StatsResponse(
                document_count=stats["document_count"],
                chunk_count=stats["chunk_count"],
                latest_update=stats["latest_update"],
                fts_size=stats["fts_size"],
            )
            return _dump(response)
        except Exception as e:
            logger.error(f"Error in stats: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Stats error: {e}")

    async def grep_docs(self, request: GrepDocsRequest) -> str:
        """Search documents with a regex pattern."""
        try:
            matches = self._indexer.grep_chunks(request.pattern, request.paths)
            response = GrepDocsResponse(
                pattern=request.pattern,
                matches=matches,
                truncated=False,
            )
            return _dump(response)
        except Exception as e:
            logger.error(f"Error in grep_docs: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Grep docs error: {e}")
