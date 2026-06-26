#!/usr/bin/env python3
"""mcp/mdq/models.py
Pydantic models, and domain exceptions for mdq-mcp.
"""

from __future__ import annotations

from typing import TypedDict

from pydantic import BaseModel


class ParsedSection(TypedDict):
    heading: str
    content: str


class ParsedSectionRequest(TypedDict):
    path: str


# ──────────────────────────────────────────────────────────────────────────────
# Domain exceptions
# ──────────────────────────────────────────────────────────────────────────────


class MdqServiceError(RuntimeError):
    """Raised on mdq service failures (index not ready, I/O error, etc.)."""


class ParseMarkdownRequest(BaseModel):
    path: str


class SearchDocsRequest(BaseModel):
    query: str
    limit: int | None = 10
    mode: str | None = "bm25"
    path_prefix: str | None = None
    tag_filter: list[str] | None = None
    heading_prefix: str | None = None


class GetChunkRequest(BaseModel):
    chunk_id: int
    with_neighbors: bool | None = False


class OutlineRequest(BaseModel):
    path: str


class IndexPathsRequest(BaseModel):
    paths: list[str]


class RefreshIndexRequest(BaseModel):
    paths: list[str]


class StatsRequest(BaseModel):
    pass


class GrepDocsRequest(BaseModel):
    pattern: str
    paths: list[str] | None = None


class SearchResultItem(BaseModel):
    file_path: str
    heading: str
    content: str


class SearchDocsResponse(BaseModel):
    results: list[SearchResultItem]


class GetChunkResponse(BaseModel):
    chunk: str
    headings: list[str]


class OutlineResponse(BaseModel):
    headings: list[str]


class IndexPathsResponse(BaseModel):
    message: str


class RefreshIndexResponse(BaseModel):
    message: str


class IndexMetadata(BaseModel):
    pass


class StatsResponse(BaseModel):
    document_count: int
    chunk_count: int
    index_metadata: IndexMetadata


class GrepDocMatch(BaseModel):
    chunk_id: int
    heading: str
    content: str


class GrepDocsResponse(BaseModel):
    results: list[GrepDocMatch]


class SearchResultResult(TypedDict):
    query: str | None
    results: list[SearchResultItem]
    total: int
