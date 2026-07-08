"""db/models.py
Typed DTOs for db-layer operation results.

Defined here (not in agent/services/models.py) so that db-layer code can import
them without violating the agent→db import-linter contract.
agent/services/models.py re-exports these for agent-layer callers.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WalCheckpointCounts:
    """Result of a WAL checkpoint (busy, log_size=pages_in_wal, pages_checkpointed)."""

    busy: int
    log_size: int
    pages_checkpointed: int


@dataclass(frozen=True)
class PurgeCounts:
    """Result of a session retention purge (age_deleted, count_deleted)."""

    age_deleted: int
    count_deleted: int


@dataclass(frozen=True)
class DbHealthMetrics:
    """DB health metrics returned by SQLiteHelper.health_check()."""

    journal_mode: str
    integrity: str
    page_count: int
    page_size: int
    freelist_count: int
    db_size_bytes: int


@dataclass(frozen=True)
class DocumentRow:
    """One row from the documents table (doc_list query result)."""

    doc_id: int
    url: str
    title: str | None
    lang: str
    fetched_at: str


@dataclass(frozen=True)
class SessionRow:
    """One row from the sessions table (session_list query result)."""

    session_id: int
    created_at: str
    title: str | None


@dataclass(frozen=True)
class MessageRow:
    """One row from the messages table (message_list query result)."""

    role: str
    content: str
    tool_calls: str | None
    tool_call_id: str | None = None


@dataclass(frozen=True)
class RagConsistencyReport:
    """Counts from chunks, chunks_fts, and chunks_vec for consistency verification."""

    chunks: int
    fts: int
    vec: int
    orphan_vec_count: int
    fts_gap: int  # chunks - fts; positive = missing FTS entries
    fts_orphan_count: int  # fts - chunks; positive = extra FTS entries (data loss risk)
    embed_failed: int = 0  # embedding failures during ingestion
    issues: tuple[str, ...] = ()  # human-readable consistency issues
    # Affected identifiers (up to 10 each; None when not applicable)
    affected_chunk_ids: tuple[int, ...] | None = None  # chunk_ids missing from FTS
    affected_doc_ids: tuple[int, ...] | None = (
        None  # doc_ids for chunks missing from FTS
    )
    affected_orphan_chunk_ids: tuple[int, ...] | None = (
        None  # chunk_ids in vec but not chunks
    )
    affected_orphan_urls: tuple[str, ...] | None = (
        None  # URLs of docs with orphan vec rows
    )


@dataclass(frozen=True)
class RecoveryResult:
    """Structured result of a corruption recovery attempt."""

    success: bool
    action: str
    detail: str | None = None
    dry_run: bool = False
