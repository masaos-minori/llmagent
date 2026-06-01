#!/usr/bin/env python3
"""db_store.py
Abstract store Protocol definitions and SQLite-backed implementations
for the RAG pipeline.

Three storage boundaries:
  VectorStore   — embedding CRUD over chunks_vec (sqlite-vec)
  DocumentStore — document + chunk metadata CRUD over documents + chunks
  SessionStore  — conversation session + message CRUD over sessions + messages

Protocol pattern (structural subtyping): the existing RagRepository in
rag_repository.py already provides the same operations and will conform to
these Protocols without modification.  Future non-SQLite backends need only
implement the Protocol methods to become drop-in replacements.

Embedding constants:
  EMBEDDING_DIMS  — expected embedding dimensionality (384 for all-MiniLM-L6-v2)
  EMBEDDING_BYTES — expected float32 BLOB size in bytes (384 * 4 = 1536)
  validate_embedding_blob(blob) — raises ValueError on wrong size
"""

from typing import Any, Protocol, runtime_checkable

from db.helper import SQLiteHelper

EMBEDDING_DIMS: int = 384
EMBEDDING_BYTES: int = EMBEDDING_DIMS * 4  # float32 → 4 bytes per dimension


def validate_embedding_blob(blob: bytes) -> None:
    """Raise ValueError if blob is not a valid 384-dim float32 embedding BLOB."""
    if not isinstance(blob, bytes):
        raise TypeError(f"Embedding must be bytes, got {type(blob).__name__}")
    if len(blob) != EMBEDDING_BYTES:
        raise ValueError(
            f"Embedding BLOB must be {EMBEDDING_BYTES} bytes"
            f" ({EMBEDDING_DIMS} float32 dims), got {len(blob)}",
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

    def doc_get(self, url: str) -> dict[str, Any] | None:
        """Return the document row for url, or None if not found."""
        ...

    def doc_list(self, lang: str | None, limit: int) -> list[dict[str, Any]]:
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

    def session_list(self, limit: int) -> list[dict[str, Any]]:
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

    def message_list(self, session_id: int) -> list[dict[str, Any]]:
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
        row = self._db.fetchall("SELECT doc_id FROM documents WHERE url = ?", (url,))
        if row:
            doc_id = int(row[0][0])
            self._db.execute(
                "UPDATE documents SET title=?, lang=?, etag=?, last_modified=?"
                " WHERE doc_id=?",
                (title, lang, etag, last_modified, doc_id),
            )
            return doc_id
        cur = self._db.execute(
            "INSERT INTO documents (url, title, lang, etag, last_modified)"
            " VALUES (?, ?, ?, ?, ?)",
            (url, title, lang, etag, last_modified),
        )
        assert cur.lastrowid is not None  # INSERT always sets lastrowid on success
        return int(cur.lastrowid)

    def doc_get(self, url: str) -> dict[str, Any] | None:
        rows = self._db.fetchall(
            "SELECT doc_id, url, title, lang, fetched_at, etag, last_modified"
            " FROM documents WHERE url = ?",
            (url,),
        )
        if not rows:
            return None
        r = rows[0]
        return {
            "doc_id": r[0],
            "url": r[1],
            "title": r[2],
            "lang": r[3],
            "fetched_at": r[4],
            "etag": r[5],
            "last_modified": r[6],
        }

    def doc_list(self, lang: str | None, limit: int) -> list[dict[str, Any]]:
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
            {
                "doc_id": r[0],
                "url": r[1],
                "title": r[2],
                "lang": r[3],
                "fetched_at": r[4],
            }
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
        assert cur.lastrowid is not None  # INSERT always sets lastrowid on success
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
        assert cur.lastrowid is not None  # INSERT always sets lastrowid on success
        return int(cur.lastrowid)

    def session_list(self, limit: int) -> list[dict[str, Any]]:
        rows = self._db.fetchall(
            "SELECT session_id, created_at, title FROM sessions"
            " ORDER BY created_at DESC LIMIT ?",
            (limit,),
        )
        return [{"session_id": r[0], "created_at": r[1], "title": r[2]} for r in rows]

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

    def message_list(self, session_id: int) -> list[dict[str, Any]]:
        rows = self._db.fetchall(
            "SELECT role, content, tool_calls FROM messages"
            " WHERE session_id = ? ORDER BY message_id",
            (session_id,),
        )
        return [{"role": r[0], "content": r[1], "tool_calls": r[2]} for r in rows]
