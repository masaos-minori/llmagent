#!/usr/bin/env python3
"""db/store_protocols.py
Public storage-layer contracts for the RAG pipeline and session/memory layers.

Protocol → SQLite implementation mapping (all in db/store_impl.py):
  VectorStore        → SQLiteVectorStore
  DocumentStore      → SQLiteDocumentStore
  SessionStore       → SQLiteSessionStore
  MemoryDeleteStore  → SQLiteMemoryDeleteStore

Embedding helpers (used by implementations and callers):
  get_embedding_dims()     — return configured dimension count (default 384)
  get_embedding_bytes()    — return expected float32 BLOB byte size
  validate_embedding_blob(blob) — raises TypeError/ValueError on wrong size

Stable import surface: use db/store.py for all imports.
"""

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from db.config import build_db_config
from db.models import DocumentRow, MessageRow, SessionRow


def get_embedding_dims() -> int:
    """Return embedding dimensions from DbConfig; raises on config error."""
    return build_db_config().embedding_dims


def get_embedding_bytes() -> int:
    """Return expected float32 BLOB size in bytes."""
    return get_embedding_dims() * 4


def validate_embedding_blob(blob: bytes) -> None:
    """Raise TypeError/ValueError if blob is not a valid float32 embedding BLOB."""
    if not isinstance(blob, bytes):
        raise TypeError(f"Embedding must be bytes, got {type(blob).__name__}")
    expected_bytes = get_embedding_bytes()
    expected_dims = get_embedding_dims()
    if len(blob) != expected_bytes:
        raise ValueError(
            f"Embedding BLOB must be {expected_bytes} bytes"
            f" ({expected_dims} float32 dims), got {len(blob)}",
        )


# ── Protocol definitions ───────────────────────────────────────────────────────


@runtime_checkable
class VectorStore(Protocol):
    """CRUD interface for vector embeddings (chunks_vec table).

    Implementation: SQLiteVectorStore (db/store_impl.py)
    """

    def vec_insert(self, chunk_id: int, embedding: bytes) -> None:
        """Insert a float32 BLOB embedding for chunk_id."""
        ...

    def vec_search(self, embedding: bytes, k: int) -> list[tuple[int, float]]:
        """Return up to k (chunk_id, distance) pairs nearest to embedding."""
        ...

    def vec_delete(self, chunk_id: int) -> None:
        """Delete the embedding for chunk_id; no-op if not present."""
        ...

    def vec_count(self) -> int:
        """Return the total number of stored embeddings."""
        ...


@runtime_checkable
class DocumentStore(Protocol):
    """CRUD interface for documents and chunks.

    Implementation: SQLiteDocumentStore (db/store_impl.py)
    """

    def doc_upsert(
        self,
        url: str,
        title: str | None,
        lang: str,
        etag: str | None,
        last_modified: str | None,
    ) -> int:
        """Insert or update a document record; return doc_id."""
        ...

    def doc_get(self, url: str) -> DocumentRow | None:
        """Return the document row for url, or None if not found."""
        ...

    def doc_list(self, lang: str | None, limit: int) -> list[DocumentRow]:
        """Return up to limit document rows, optionally filtered by lang."""
        ...

    def doc_delete(self, url: str) -> bool:
        """Delete document and its cascaded chunks; return True when found."""
        ...

    def chunk_insert(
        self,
        doc_id: int,
        index: int,
        content: str,
        normalized: str | None = None,
        chunk_type: str = "",
        source_file: str = "",
    ) -> int:
        """Insert one chunk row; return the new chunk_id.

        Args:
            doc_id: FK to the parent document row.
            index: Zero-based position of this chunk within the document.
            content: Raw chunk text.
            normalized: Pre-normalized text for FTS and vector indexing, or None.
            chunk_type: Content type label (e.g. "text", "code"). Defaults to "".
            source_file: Path to the originating source file. Defaults to "".

        Returns:
            The rowid of the newly inserted chunk row.

        Note:
            Field set matches RagIngester._insert_chunk() INSERT in rag/ingester.py.
        """
        ...

    def chunk_count(self) -> int:
        """Return the total number of chunks."""
        ...


@runtime_checkable
class SessionStore(Protocol):
    """CRUD interface for conversation sessions and messages.

    Implementation: SQLiteSessionStore (db/store_impl.py)
    """

    def session_create(self) -> int:
        """Create a new session row; return session_id."""
        ...

    def session_list(self, limit: int) -> list[SessionRow]:
        """Return up to limit most-recent session rows (desc by created_at)."""
        ...

    def session_rename(self, session_id: int, title: str) -> None:
        """Set the title of an existing session."""
        ...

    def session_delete(self, session_id: int) -> None:
        """Delete a session; ON DELETE CASCADE removes its messages."""
        ...

    def message_save(
        self,
        session_id: int,
        role: str,
        content: str,
        tool_calls: str | None,
        tool_call_id: str | None = None,
    ) -> None:
        """Append a message to the session."""
        ...

    def message_list(self, session_id: int) -> list[MessageRow]:
        """Return all messages for session_id in insertion order."""
        ...


# ── Memory deletion store ──────────────────────────────────────────────────────


@dataclass(frozen=True)
class MemoryDeleteResult:
    """Result of an atomic cross-table memory deletion operation."""

    deleted: int


@runtime_checkable
class MemoryDeleteStore(Protocol):
    """Atomic cross-table deletion for memories / memories_fts / memories_vec.

    Implementation: SQLiteMemoryDeleteStore (db/store_impl.py)
    """

    def delete_memories_before(self, older_than_days: int) -> MemoryDeleteResult:
        """Delete memories older than older_than_days; return deletion summary."""
        ...
