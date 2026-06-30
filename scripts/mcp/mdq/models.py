#!/usr/bin/env python3
"""mcp/mdq/models.py
Pydantic models, and domain exceptions for mdq-mcp.
"""

from __future__ import annotations

from typing import TypedDict

from pydantic import BaseModel


class ParsedSection(TypedDict):
    heading: str
    heading_level: int
    heading_path: str
    content: str
    start_line: int
    end_line: int
    ordinal: int
    parent_heading: str | None


class ChunkRecord(TypedDict):
    chunk_id: str
    doc_id: str
    source_path: str
    heading: str
    heading_path: str
    heading_level: int
    ordinal: int
    content: str
    normalized_content: str
    start_line: int
    end_line: int
    char_count: int
    token_count: int | None
    content_hash: str
    tags_json: str | None
    indexed_at: float | None


class ChunkSummary(TypedDict):
    chunk_id: str
    summary: str
    summary_model: str
    content_hash: str
    created_at: str


class ParsedSectionRequest(TypedDict):
    path: str


# ──────────────────────────────────────────────────────────────────────────────
# Domain exceptions
# ──────────────────────────────────────────────────────────────────────────────


class MdqServiceError(RuntimeError):
    """Raised on mdq service failures (index not ready, I/O error, etc.)."""


class MdqValidationError(MdqServiceError):
    """Validation errors: invalid input, bad regex, etc."""


class MdqAuthorizationError(MdqServiceError):
    """Authorization errors: unauthorized path access."""


class MdqNotFoundError(MdqServiceError):
    """Not found errors: file not found, chunk not found."""


class MdqIndexNotReadyError(MdqServiceError):
    """Index not ready errors: index missing, stale."""


class MdqDatabaseError(MdqServiceError):
    """Database errors: DB unavailable, migration failed."""


class MdqConsistencyError(MdqServiceError):
    """Consistency errors: FTS mismatch, data corruption."""


class ParseMarkdownRequest(BaseModel):
    path: str


class SearchDocsRequest(BaseModel):
    query: str
    limit: int | None = 10
    mode: str | None = "bm25"
    path_prefix: str | None = None
    tag_filter: list[str] | None = None
    heading_prefix: str | None = None
    max_results_limit: int | None = None
    max_total_result_chars: int | None = None


class GetChunkRequest(BaseModel):
    chunk_id: str
    with_neighbors: bool | None = False
    max_chars_per_chunk: int | None = None
    use_summary: bool = False


class OutlineRequest(BaseModel):
    path: str
    max_depth: int | None = 6
    max_outline_items: int | None = 500


class IndexPathsRequest(BaseModel):
    paths: list[str]


class RefreshIndexRequest(BaseModel):
    paths: list[str]
    force: bool = False


class StatsRequest(BaseModel):
    pass


class GrepDocsRequest(BaseModel):
    pattern: str
    paths: list[str] | None = None
    max_grep_matches: int | None = 200
    max_chars_per_match: int | None = 500
    context_before: int | None = 2
    context_after: int | None = 2


class SearchResultItem(BaseModel):
    chunk_id: str
    source_path: str
    heading: str
    heading_path: str
    score: float
    start_line: int
    end_line: int
    token_count: int | None
    snippet: str


class SearchDocsResponse(BaseModel):
    results: list[SearchResultItem]


class GetChunkResponse(BaseModel):
    chunk: str
    headings: list[str]


class GetChunkSummaryResponse(BaseModel):
    chunk_id: str
    summary: str
    summary_model: str
    content_hash: str
    created_at: str
    headings: list[str]


class OutlineHeading(BaseModel):
    heading: str
    level: int
    heading_path: str
    chunk_id: str
    start_line: int
    end_line: int


class OutlineResponse(BaseModel):
    headings: list[OutlineHeading]
    stale_warning: str | None = None


class IndexPathsResponse(BaseModel):
    message: str


class RefreshIndexResponse(BaseModel):
    indexed_count: int
    skipped_count: int
    deleted_count: int
    failed_count: int
    elapsed_seconds: float


class IndexMetadata(BaseModel):
    pass


class StatsResponse(BaseModel):
    document_count: int
    chunk_count: int
    index_metadata: IndexMetadata


class GrepDocMatch(BaseModel):
    chunk_id: str
    source_path: str
    heading_path: str
    match_text: str
    line_number: int


class GrepDocsResponse(BaseModel):
    results: list[GrepDocMatch]


class SearchResultResult(TypedDict):
    query: str | None
    results: list[SearchResultItem]
    total: int


class FtsConsistencyCheckRequest(BaseModel):
    pass


class FtsConsistencyCheckResponse(BaseModel):
    consistent: bool
    chunks_count: int
    chunks_fts_count: int


class FtsRebuildRequest(BaseModel):
    pass


class EmbeddingResult(TypedDict):
    chunk_id: str
    embedding_score: float
    rank: int
