#!/usr/bin/env python3
"""db_store.py
Abstract store Protocol definitions and SQLite-backed implementations
for the RAG pipeline.

Three storage boundaries:
  VectorStore        — embedding CRUD over chunks_vec (sqlite-vec)
  DocumentStore      — document + chunk metadata CRUD over documents + chunks
  SessionStore       — conversation session + message CRUD over sessions + messages
  MemoryDeleteStore  — atomic cross-table deletion for memories tables

Protocol pattern (structural subtyping): the existing RagRepository in
rag_repository.py already provides the same operations and will conform to
these Protocols without modification.  Future non-SQLite backends need only
implement the Protocol methods to become drop-in replacements.

Embedding helpers:
  get_embedding_dims()    — return configured dimension count (default 384)
  get_embedding_bytes()   — return expected float32 BLOB byte size
  validate_embedding_blob(blob) — raises TypeError/ValueError on wrong size
"""

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from db.config import build_db_config
from db.helper import SQLiteHelper
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
    """CRUD interface for vector embeddings (chunks_vec table)."""

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
    """CRUD interface for documents and chunks."""

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
        normalized: str | None,
    ) -> int:
        """Insert a chunk row; return chunk_id."""
        ...

    def chunk_count(self) -> int:
        """Return the total number of chunks."""
        ...


@runtime_checkable
class SessionStore(Protocol):
    """CRUD interface for conversation sessions and messages."""

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
    ) -> None:
        """Append a message to the session."""
        ...

    def message_list(self, session_id: int) -> list[MessageRow]:
        """Return all messages for session_id in insertion order."""
        ...


# ── SQLite-backed implementations ─────────────────────────────────────────────


class SQLiteVectorStore:
    """SQLite-backed VectorStore using the sqlite-vec chunks_vec virtual table."""

    def __init__(self, db: SQLiteHelper) -> None:
        self._db = db

    def vec_insert(self, chunk_id: int, embedding: bytes) -> None:
        validate_embedding_blob(embedding)
        self._db.execute(
            "INSERT INTO chunks_vec (chunk_id, embedding) VALUES (?, ?)",
            (chunk_id, embedding),
        )

    def vec_search(self, embedding: bytes, k: int) -> list[tuple[int, float]]:
        validate_embedding_blob(embedding)
        rows = self._db.fetchall(
            "SELECT chunk_id, distance FROM chunks_vec"
            " WHERE embedding MATCH ? ORDER BY distance LIMIT ?",
            (embedding, k),
        )
        return [(int(row[0]), float(row[1])) for row in rows]

    def vec_delete(self, chunk_id: int) -> None:
        self._db.execute("DELETE FROM chunks_vec WHERE chunk_id = ?", (chunk_id,))

    def vec_count(self) -> int:
        rows = self._db.fetchall("SELECT count(*) FROM chunks_vec")
        return int(rows[0][0]) if rows else 0


class SQLiteDocumentStore:
    """SQLite-backed DocumentStore over the documents + chunks tables."""

    def __init__(self, db: SQLiteHelper) -> None:
        self._db = db

    def doc_upsert(
        self,
        url: str,
        title: str | None,
        lang: str,
        etag: str | None,
        last_modified: str | None,
    ) -> int:
        cur = self._db.execute(
            "INSERT INTO documents (url, title, lang, etag, last_modified)"
            " VALUES (?, ?, ?, ?, ?)"
            " ON CONFLICT(url) DO UPDATE SET"
            "  title = excluded.title,"
            "  lang = excluded.lang,"
            "  etag = excluded.etag,"
            "  last_modified = excluded.last_modified,"
            "  fetched_at = strftime('%Y-%m-%dT%H:%M:%SZ', 'now')",
            (url, title, lang, etag, last_modified),
        )
        if cur.lastrowid is None:
            raise RuntimeError(
                "doc_insert: INSERT ... ON CONFLICT did not produce a lastrowid"
            )
        return int(cur.lastrowid)

    def doc_get(self, url: str) -> DocumentRow | None:
        rows = self._db.fetchall(
            "SELECT doc_id, url, title, lang, fetched_at FROM documents WHERE url = ?",
            (url,),
        )
        if not rows:
            return None
        r = rows[0]
        return DocumentRow(
            doc_id=int(r[0]),
            url=str(r[1]),
            title=r[2],
            lang=r[3],
            fetched_at=str(r[4]) if r[4] is not None else "",
        )

    def doc_list(self, lang: str | None, limit: int) -> list[DocumentRow]:
        if lang:
            rows = self._db.fetchall(
                "SELECT doc_id, url, title, lang, fetched_at FROM documents"
                " WHERE lang = ? ORDER BY fetched_at DESC LIMIT ?",
                (lang, limit),
            )
        else:
            rows = self._db.fetchall(
                "SELECT doc_id, url, title, lang, fetched_at FROM documents"
                " ORDER BY fetched_at DESC LIMIT ?",
                (limit,),
            )
        return [
            DocumentRow(
                doc_id=int(r[0]),
                url=str(r[1]),
                title=r[2],
                lang=r[3],
                fetched_at=str(r[4]) if r[4] is not None else "",
            )
            for r in rows
        ]

    def doc_delete(self, url: str) -> bool:
        row = self._db.fetchall("SELECT doc_id FROM documents WHERE url = ?", (url,))
        if not row:
            return False
        doc_id = int(row[0][0])
        self._db.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))
        return True

    def chunk_insert(
        self,
        doc_id: int,
        index: int,
        content: str,
        normalized: str | None,
    ) -> int:
        cur = self._db.execute(
            "INSERT INTO chunks (doc_id, chunk_index, content, normalized_content)"
            " VALUES (?, ?, ?, ?)",
            (doc_id, index, content, normalized),
        )
        if cur.lastrowid is None:
            raise RuntimeError("chunk_insert: INSERT did not produce a lastrowid")
        return int(cur.lastrowid)

    def chunk_count(self) -> int:
        rows = self._db.fetchall("SELECT count(*) FROM chunks")
        return int(rows[0][0]) if rows else 0


class SQLiteSessionStore:
    """SQLite-backed SessionStore over the sessions + messages tables."""

    def __init__(self, db: SQLiteHelper) -> None:
        self._db = db

    def session_create(self) -> int:
        cur = self._db.execute("INSERT INTO sessions (title) VALUES (NULL)")
        if cur.lastrowid is None:
            raise RuntimeError("session_create: INSERT did not produce a lastrowid")
        return int(cur.lastrowid)

    def session_list(self, limit: int) -> list[SessionRow]:
        rows = self._db.fetchall(
            "SELECT session_id, created_at, title FROM sessions"
            " ORDER BY created_at DESC LIMIT ?",
            (limit,),
        )
        return [
            SessionRow(
                session_id=int(r[0]),
                created_at=str(r[1]) if r[1] is not None else "",
                title=r[2],
            )
            for r in rows
        ]

    def session_rename(self, session_id: int, title: str) -> None:
        self._db.execute(
            "UPDATE sessions SET title = ? WHERE session_id = ?",
            (title, session_id),
        )

    def session_delete(self, session_id: int) -> None:
        self._db.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))

    def message_save(
        self,
        session_id: int,
        role: str,
        content: str,
        tool_calls: str | None,
    ) -> None:
        self._db.execute(
            "INSERT INTO messages (session_id, role, content, tool_calls)"
            " VALUES (?, ?, ?, ?)",
            (session_id, role, content, tool_calls),
        )

    def message_list(self, session_id: int) -> list[MessageRow]:
        rows = self._db.fetchall(
            "SELECT role, content, tool_calls FROM messages"
            " WHERE session_id = ? ORDER BY message_id",
            (session_id,),
        )
        return [
            MessageRow(
                role=str(r[0]),
                content=str(r[1]) if r[1] is not None else "",
                tool_calls=r[2],
            )
            for r in rows
        ]


# ── Memory deletion store ──────────────────────────────────────────────────────


@dataclass(frozen=True)
class MemoryDeleteResult:
    """Result of an atomic cross-table memory deletion operation."""

    deleted: int


@runtime_checkable
class MemoryDeleteStore(Protocol):
    """Atomic cross-table deletion for memories / memories_fts / memories_vec."""

    def delete_memories_before(self, older_than_days: int) -> MemoryDeleteResult:
        """Delete memories older than older_than_days; return deletion summary."""
        ...


class SQLiteMemoryDeleteStore:
    """SQLite-backed MemoryDeleteStore; all deletions are atomic."""

    def __init__(self, db: SQLiteHelper) -> None:
        self._db = db

    def delete_memories_before(self, older_than_days: int) -> MemoryDeleteResult:
        rows = self._db.fetchall(
            "SELECT memory_id FROM memories WHERE created_at < datetime('now', ?)",
            (f"-{older_than_days} days",),
        )
        if not rows:
            return MemoryDeleteResult(deleted=0)

        mids = [row[0] for row in rows]
        placeholders = ",".join("?" * len(mids))
        cur = self._db.execute(
            f"DELETE FROM memories WHERE memory_id IN ({placeholders})",  # nosec B608 — mids are UUIDs from DB; placeholders use ?
            tuple(mids),
        )
        deleted = cur.rowcount
        for mid in mids:
            self._db.execute("DELETE FROM memories_fts WHERE memory_id=?", (mid,))
        for mid in mids:
            self._db.execute("DELETE FROM memories_vec WHERE memory_id=?", (mid,))

        self._db.commit()
        return MemoryDeleteResult(deleted=deleted)
