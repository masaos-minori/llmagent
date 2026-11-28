#!/usr/bin/env python3
"""scripts/mcp_servers/mdq/mdq_models.py

Pydantic models, and domain exceptions for mdq-mcp.
"""

from __future__ import annotations

from typing import ClassVar, Literal, TypedDict

from pydantic import BaseModel, Field, ValidationInfo, field_validator
from shared.config_field_types import (
    RULE_BOOL,
    RULE_INT,
    RULE_STR_LIST,
    FieldRule,
    apply_field_rule,
)

# ──────────────────────────────────────────────────────────────────────────────
# Parsing TypedDicts
# ──────────────────────────────────────────────────────────────────────────────


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


# ──────────────────────────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────────────────────────


class MdqConfig(BaseModel):
    """Validated mdq-mcp configuration loaded from `mdq_mcp_server.toml`.

    `db_path` is deliberately excluded — it has no meaningful range/type
    constraint beyond being a string and is handled separately by the caller.

    Every key is required: no field has an implicit default, so a payload that omits
    one is a validation failure rather than a silent fallback (REQ-007).
    """

    # Declared rule per key, so the model applies the same rule the startup loader uses
    # (REQ-001). The rule runs before pydantic's own coercion, so a recognized boolean
    # token is refused instead of coerced, and the error names the field path only (AC-6).
    _CONFIG_FIELD_RULES: ClassVar[dict[str, FieldRule]] = {
        "allowed_dirs": RULE_STR_LIST,
        "include_globs": RULE_STR_LIST,
        "exclude_globs": RULE_STR_LIST,
        "max_snippet_chars": RULE_INT,
        "max_chunk_chars": RULE_INT,
        "max_file_bytes": RULE_INT,
        "search_timeout_sec": RULE_INT,
        "max_results_limit": RULE_INT,
        "max_chars_per_chunk": RULE_INT,
        "max_total_result_chars": RULE_INT,
        "max_outline_items": RULE_INT,
        "max_grep_matches": RULE_INT,
        "max_chars_per_match": RULE_INT,
        "context_before": RULE_INT,
        "context_after": RULE_INT,
        "enable_grep": RULE_BOOL,
        "max_outline_depth": RULE_INT,
        "sqlite_busy_timeout": RULE_INT,
    }

    allowed_dirs: list[str]
    include_globs: list[str]
    exclude_globs: list[str]
    max_snippet_chars: int = Field(gt=0)
    max_chunk_chars: int = Field(gt=0)
    max_file_bytes: int = Field(gt=0)
    search_timeout_sec: int = Field(gt=0)
    max_results_limit: int = Field(gt=0)
    max_chars_per_chunk: int = Field(gt=0)
    max_total_result_chars: int = Field(gt=0)
    max_outline_items: int = Field(gt=0)
    max_grep_matches: int = Field(gt=0)
    max_chars_per_match: int = Field(gt=0)
    context_before: int = Field(ge=0)
    context_after: int = Field(ge=0)
    enable_grep: bool
    max_outline_depth: int = Field(gt=0)
    sqlite_busy_timeout: int = Field(gt=0)

    @field_validator("*", mode="before")
    @classmethod
    def _apply_declared_rule(cls, value: object, info: ValidationInfo) -> object:
        """Run the declared rule for the field before any coercion.

        Emptiness is not a type violation here: an empty `allowed_dirs` is the configured
        deny-all state, so the caller decides what an empty list means.
        """
        field_name = info.field_name
        if field_name is None:
            return value
        return apply_field_rule(
            cls._CONFIG_FIELD_RULES[field_name],
            value,
            field_name,
            allow_empty=True,
        )


# ──────────────────────────────────────────────────────────────────────────────
# Request models
# ──────────────────────────────────────────────────────────────────────────────


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


# ──────────────────────────────────────────────────────────────────────────────
# Response models
# ──────────────────────────────────────────────────────────────────────────────


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
    """A single grep match result with source location, matched text, and context.

    `line_number` is the source-file line of the first stored content line, computed as
    `start_line + 1 + k` (UNK-03, decided 20261127), not a chunk-relative offset.
    """

    chunk_id: str
    source_path: str
    heading_path: str
    match_text: str
    line_number: int
    context_before_lines: list[str] = Field(default_factory=list)
    context_after_lines: list[str] = Field(default_factory=list)


class GrepDocsResponse(BaseModel):
    """Response containing a list of grep match results."""

    results: list[GrepDocMatch]


# ──────────────────────────────────────────────────────────────────────────────
# Internal result wrapper
# ──────────────────────────────────────────────────────────────────────────────


class SearchResultResult(TypedDict):
    """Search result wrapper containing query and result items."""

    query: str | None
    results: list[SearchResultItem]
    matched_count: int  # exact count of rows matching the query, no LIMIT applied
    shown_count: int  # len(results) — rows actually returned after effective_limit


# Closed vocabulary for the per-file processing result (REQ-001, REQ-007). A value outside
# one of these sets is a construction error, so no caller can report an outcome the audit
# surface does not recognize.
FILE_OUTCOME_STATUSES: frozenset[str] = frozenset(
    {
        "indexed",
        "skipped_unchanged",
        "skipped_size_limit",
        "skipped_no_content",
        "failed",
    }
)

FILE_OUTCOME_REASON_CODES: frozenset[str] = frozenset(
    {
        "unchanged",
        "size_limit",
        "no_content",
        "file_disappeared",
        "write_failure",
        "invalid_frontmatter",
    }
)


class FileOutcome(BaseModel):
    """Per-file processing result: what happened to one file, and why.

    `path` is the root-relative POSIX path, never an absolute path, so the record stays
    inside the audit rule that persistent output carries no absolute path.
    """

    path: str
    status: str
    reason_code: str | None = None
    warning_codes: list[str] = Field(default_factory=list)
    warning_count: int = 0
    char_count: int = 0  # decoded characters, kept distinct from the byte gate

    @field_validator("status")
    @classmethod
    def _status_is_known(cls, value: str) -> str:
        if value not in FILE_OUTCOME_STATUSES:
            raise ValueError(f"status {value!r} is outside the closed status set")
        return value

    @field_validator("reason_code")
    @classmethod
    def _reason_code_is_known(cls, value: str | None) -> str | None:
        if value is not None and value not in FILE_OUTCOME_REASON_CODES:
            raise ValueError(
                f"reason code {value!r} is outside the closed reason-code set"
            )
        return value

    @field_validator("warning_codes")
    @classmethod
    def _warning_codes_are_known(cls, values: list[str]) -> list[str]:
        for code in values:
            if code not in FILE_OUTCOME_REASON_CODES:
                raise ValueError(
                    f"warning code {code!r} is outside the closed reason-code set"
                )
        return values


# ──────────────────────────────────────────────────────────────────────────────
# Outcome text (REQ-003)
# ──────────────────────────────────────────────────────────────────────────────

# The two texts an index or refresh run reports. Success is reported only when the run
# finished the work it discovered; anything short of that reports `partial_success`. An
# all-failed run reports neither: its callers raise MdqServiceError.
SUCCESS_TEXT = "Indexing complete"
PARTIAL_SUCCESS_TEXT = "partial_success"


def outcome_text(
    *,
    committed_files: int,
    discovered_files: int,
    skipped_files: int,
    failed_files: int,
    skipped_paths: int,
    failed_paths: int,
    unchanged_files: int = 0,
) -> str:
    """Render the outcome text from counters, not from the absence of an exception.

    Full success means no file or path failed and everything left over was unchanged: an
    unchanged file is completed refresh work, so it does not make a run partial. A path
    skipped before any file was read (nonexistent, non-Markdown) breaks it.
    """
    full_success = (
        committed_files == discovered_files - unchanged_files
        and skipped_files == unchanged_files
        and failed_files == 0
        and failed_paths == 0
        and skipped_paths == unchanged_files
    )
    return SUCCESS_TEXT if full_success else PARTIAL_SUCCESS_TEXT


# ──────────────────────────────────────────────────────────────────────────────
# Staleness helpers
# ──────────────────────────────────────────────────────────────────────────────


def is_stale(mtime_ns: int, indexed_at: float) -> bool:
    """True if the file's on-disk mtime (ns) is newer than the last indexed_at (s, time.time())."""
    return mtime_ns > int(indexed_at * 1e9)


STALE_SQL_CONDITION: str = "mtime_ns > CAST(indexed_at * 1e9 AS INTEGER)"


# ──────────────────────────────────────────────────────────────────────────────
# Audit metadata TypedDicts (consumed by mdq_server.py)
# ──────────────────────────────────────────────────────────────────────────────


class SearchDocsMetadata(TypedDict):
    """Structured audit metadata produced by search_docs(), consumed by mdq_server.py.

    `query_preview` carries the hashed identifier produced by
    `mcp_servers.audit.hash_query_value`; no raw query text, and no prefix of it,
    is reachable from this metadata (AC-5).
    """

    query_preview: str  # hashed identifier; the raw query value is not stored here
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
    discovered_file_count: int
    committed_file_count: int
    skipped_file_count: int
    failed_file_count: int
    duration_ms: float


class GrepDocsMetadata(TypedDict):
    """Structured audit metadata produced by grep_docs(), consumed by mdq_server.py."""

    pattern_preview: str
    path_filter_count: int
    match_count: int
    truncated: bool
    grep_enabled: bool
