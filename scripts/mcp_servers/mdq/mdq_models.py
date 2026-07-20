#!/usr/bin/env python3
"""mcp_servers/mdq/models.py

Pydantic models, and domain exceptions for mdq-mcp.
"""

from __future__ import annotations

from typing import Literal, TypedDict

from pydantic import BaseModel, Field


class ParsedSection(TypedDict):
    """Parsed markdown section with heading hierarchy and content."""

    heading: str
    heading_level: int
    heading_path: str
    content: str
    start_line: int
    end_line: int
    ordinal: int
    parent_heading: str | None


class ChunkRecord(TypedDict):
    """Chunk record containing document metadata and content hash."""

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


class ParsedSectionRequest(TypedDict):
    """Request to parse a markdown file into sections."""

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


class MdqConfig(BaseModel):
    """Validated mdq-mcp configuration loaded from `mdq_mcp_server.toml`.

    `db_path` is deliberately excluded — it has no meaningful range/type
    constraint beyond being a string and is handled separately by the caller.
    """

    allowed_dirs: list[str] = []
    include_globs: list[str] = ["*.md"]
    exclude_globs: list[str] = [".git/**", "__pycache__/**"]
    max_snippet_chars: int = Field(default=500, gt=0)
    max_chunk_chars: int = Field(default=10000, gt=0)
    max_file_chars: int = Field(default=100000, gt=0)
    search_timeout_sec: int = Field(default=30, gt=0)
    max_results_limit: int = Field(default=100, gt=0)
    max_chars_per_chunk: int = Field(default=10000, gt=0)
    max_total_result_chars: int = Field(default=100000, gt=0)
    max_outline_items: int = Field(default=500, gt=0)
    max_grep_matches: int = Field(default=200, gt=0)
    max_chars_per_match: int = Field(default=500, gt=0)
    context_before: int = Field(default=2, ge=0)
    context_after: int = Field(default=2, ge=0)
    enable_grep: bool = True
    max_outline_depth: int = Field(default=6, gt=0)
    sqlite_busy_timeout: int = Field(default=5000, gt=0)


class ParseMarkdownRequest(BaseModel):
    """Pydantic model for parsing a markdown file into sections."""

    path: str


class SearchDocsRequest(BaseModel):
    """Pydantic model for searching documents via BM25."""

    query: str
    limit: int | None = 10
    mode: Literal["bm25"] | None = "bm25"
    path_prefix: str | None = None
    tag_filter: list[str] | None = None
    heading_prefix: str | None = None
    max_results_limit: int | None = None
    max_total_result_chars: int | None = None


class GetChunkRequest(BaseModel):
    """Pydantic model for retrieving a single chunk by ID."""

    chunk_id: str
    with_neighbors: bool | None = False
    max_chars_per_chunk: int | None = None


class OutlineRequest(BaseModel):
    """Pydantic model for generating an outline from a markdown file."""

    path: str
    max_depth: int | None = 6
    max_outline_items: int | None = 500


class IndexPathsRequest(BaseModel):
    """Pydantic model for indexing specified paths."""

    paths: list[str]


class RefreshIndexRequest(BaseModel):
    """Pydantic model for refreshing the index for specified paths."""

    paths: list[str]
    force: bool = False


class StatsRequest(BaseModel):
    """Pydantic model for requesting index statistics (no parameters)."""

    pass


class GrepDocsRequest(BaseModel):
    """Pydantic model for grep-style text search across indexed documents."""

    pattern: str
    paths: list[str] | None = None
    max_grep_matches: int | None = 200
    max_chars_per_match: int | None = 500
    context_before: int | None = 2
    context_after: int | None = 2


class SearchResultItem(BaseModel):
    """A single search result item with score and snippet."""

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
    """Response containing a list of search results."""

    results: list[SearchResultItem]


class GetChunkResponse(BaseModel):
    """Response containing a chunk string and its heading hierarchy."""

    chunk: str
    headings: list[str]


class OutlineHeading(BaseModel):
    """A single heading entry in an outline response."""

    heading: str
    level: int
    heading_path: str
    chunk_id: str
    start_line: int
    end_line: int


class OutlineResponse(BaseModel):
    """Response containing document outline headings and optional staleness warning."""

    headings: list[OutlineHeading]
    stale_warning: str | None = None


class IndexPathsResponse(BaseModel):
    """Response confirming index paths were processed."""

    message: str


class RefreshIndexResponse(BaseModel):
    """Response containing refresh operation counts and elapsed time."""

    indexed_count: int
    skipped_count: int
    deleted_count: int
    failed_count: int
    elapsed_seconds: float


class IndexMetadata(BaseModel):
    """Placeholder for future index metadata fields."""

    pass


class StatsResponse(BaseModel):
    """Response containing index statistics including document/chunk counts and metadata."""

    document_count: int
    chunk_count: int
    index_metadata: IndexMetadata


class GrepDocMatch(BaseModel):
    """A single grep match result with source location and matched text."""

    chunk_id: str
    source_path: str
    heading_path: str
    match_text: str
    line_number: int


class GrepDocsResponse(BaseModel):
    """Response containing a list of grep match results."""

    results: list[GrepDocMatch]


class SearchResultResult(TypedDict):
    """Search result wrapper containing query and result items."""

    query: str | None
    results: list[SearchResultItem]
    matched_count: int  # exact count of rows matching the query, no LIMIT applied
    shown_count: int  # len(results) — rows actually returned after effective_limit


def is_stale(mtime_ns: int, indexed_at: float) -> bool:
    """True if the file's on-disk mtime (ns) is newer than the last indexed_at (s, time.time())."""
    return mtime_ns > int(indexed_at * 1e9)


STALE_SQL_CONDITION: str = "mtime_ns > CAST(indexed_at * 1e9 AS INTEGER)"


class SearchDocsMetadata(TypedDict):
    """Structured audit metadata produced by search_docs(), consumed by mdq_server.py."""

    query_preview: str
    result_count: int  # exact match count before truncation
    shown_count: int  # results actually included in the formatted text
    truncated: bool
    total_count: int  # kept distinct from result_count per requirement wording
    duration_ms: float


class IndexPathsMetadata(TypedDict):
    """Structured audit metadata produced by index_paths(), consumed by mdq_server.py."""

    input_path_count: int
    indexed_count: int
    skipped_count: int
    failed_count: int
    duration_ms: float


class GrepDocsMetadata(TypedDict):
    """Structured audit metadata produced by grep_docs(), consumed by mdq_server.py."""

    pattern_preview: str
    path_filter_count: int
    match_count: int
    truncated: bool
    grep_enabled: bool
