#!/usr/bin/env python3
"""
mcp/mdq/models.py
Pydantic models for Markdown Context Compression Engine MCP Server.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

# ──────────────────────────────────────────────────────────────────────────────
# Request Models
# ──────────────────────────────────────────────────────────────────────────────


class SearchDocsRequest(BaseModel):
    """Request model for search_docs tool."""

    query: str
    limit: int | None = Field(default=10)
    mode: str | None = Field(default="hybrid")
    path_prefix: str | None = Field(default=None)
    tag_filter: list[str] | None = Field(default=None)
    heading_prefix: str | None = Field(default=None)


class GetChunkRequest(BaseModel):
    """Request model for get_chunk tool."""

    chunk_id: int
    with_neighbors: bool | None = Field(default=False)


class OutlineRequest(BaseModel):
    """Request model for outline tool."""

    path: str


class IndexPathsRequest(BaseModel):
    """Request model for index_paths tool."""

    paths: list[str]


class RefreshIndexRequest(BaseModel):
    """Request model for refresh_index tool."""

    paths: list[str]


class StatsRequest(BaseModel):
    """Request model for stats tool."""

    pass


class GrepDocsRequest(BaseModel):
    """Request model for grep_docs tool."""

    pattern: str
    paths: list[str] | None = Field(default=None)


# ──────────────────────────────────────────────────────────────────────────────
# Response Models
# ──────────────────────────────────────────────────────────────────────────────


class SearchDocsHit(BaseModel):
    """Individual hit from search_docs."""

    chunk_id: int
    source_path: str
    heading_path: str
    score: float
    snippet: str
    token_count: int
    tags: list[str]


class SearchDocsResponse(BaseModel):
    """Response model for search_docs tool."""

    hits: list[SearchDocsHit]
    total_hits: int


class ChunkResponse(BaseModel):
    """Response model for get_chunk tool."""

    chunk_id: int
    source_path: str
    heading_path: str
    content: str
    token_count: int
    tags: list[str]
    chunk_order: int


class OutlineEntry(BaseModel):
    """Individual entry from outline."""

    heading_path: str
    heading_level: int
    chunk_id: int
    token_count: int


class OutlineResponse(BaseModel):
    """Response model for outline tool."""

    path: str
    title: str
    outline: list[OutlineEntry]


class IndexPathsResponse(BaseModel):
    """Response model for index_paths tool."""

    indexed_paths: list[str]
    total_docs: int


class RefreshIndexResponse(BaseModel):
    """Response model for refresh_index tool."""

    updated_paths: list[str]
    total_docs: int


class StatsResponse(BaseModel):
    """Response model for stats tool."""

    document_count: int
    chunk_count: int
    latest_update: str
    fts_size: int


class GrepDocsResponse(BaseModel):
    """Response model for grep_docs tool."""

    pattern: str
    matches: list[dict]  # TODO: Define more specific structure
    truncated: bool


# ──────────────────────────────────────────────────────────────────────────────
# Utility Functions
# ──────────────────────────────────────────────────────────────────────────────


def _get_cfg() -> dict[str, Any]:
    """Get configuration for the mdq-mcp server."""
    from shared.config_loader import get_config

    return get_config("mdq_mcp_server")


def _get_db_path() -> str:
    """Get the database path for the mdq-mcp server."""
    cfg = _get_cfg()
    return str(cfg.get("db_path", "/opt/llm/db/mdq.sqlite"))
