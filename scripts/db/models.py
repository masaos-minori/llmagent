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
class ToolResultRow:
    """One row from the tool_results table.

    Full schema for get(); partial for list_recent (session_id/turn/args_masked/
    full_text/created_at default to None/0/"").
    """

    id: int
    tool_name: str
    is_error: bool
    summary: str | None = None
    session_id: int | None = None
    turn: int = 0
    args_masked: str = ""
    full_text: str = ""
    created_at: str = ""


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
    lang: str | None
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
