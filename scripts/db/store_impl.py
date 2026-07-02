#!/usr/bin/env python3
"""db/store_impl.py
SQLite-backed implementations for the RAG pipeline store Protocols.

Classes:
  SQLiteVectorStore       — embedding CRUD over chunks_vec (sqlite-vec)
  SQLiteDocumentStore     — document + chunk metadata CRUD over documents + chunks
  SQLiteSessionStore      — conversation session + message CRUD over sessions + messages
  SQLiteMemoryDeleteStore — atomic cross-table deletion for memories tables

Protocols are defined in db/store_protocols.py.
"""

from db.helper import SQLiteHelper
from db.models import DocumentRow, MessageRow, SessionRow
from db.store_protocols import (
    MemoryDeleteResult,
    validate_embedding_blob,
)


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
        if k < 1:
            return []
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
            "  fetched_at = strftime('%Y-%m-%dT%H:%M:%SZ', 'now')"
            " RETURNING doc_id",
            (url, title, lang, etag, last_modified),
        )
        row = cur.fetchone()
        if row is None:
            raise RuntimeError("doc_upsert: RETURNING doc_id returned no row")
        return int(row[0])

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
                lang=str(r[3]),
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
        normalized: str | None = None,
        chunk_type: str = "",
        source_file: str = "",
    ) -> int:
        cur = self._db.execute(
            "INSERT INTO chunks (doc_id, chunk_index, content, normalized_content, chunk_type, source_file)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (doc_id, index, content, normalized, chunk_type, source_file),
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
        tool_call_id: str | None = None,
    ) -> None:
        self._db.execute(
            "INSERT INTO messages (session_id, role, content, tool_calls, tool_call_id)"
            " VALUES (?, ?, ?, ?, ?)",
            (session_id, role, content, tool_calls, tool_call_id),
        )

    def message_list(self, session_id: int) -> list[MessageRow]:
        rows = self._db.fetchall(
            "SELECT role, content, tool_calls, tool_call_id FROM messages"
            " WHERE session_id = ? ORDER BY message_id",
            (session_id,),
        )
        return [
            MessageRow(
                role=str(r[0]),
                content=str(r[1]) if r[1] is not None else "",
                tool_calls=r[2],
                tool_call_id=r[3] if r[3] is not None else None,
            )
            for r in rows
        ]


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
        with self._db.begin_immediate():
            cur = self._db.execute(
                f"DELETE FROM memories WHERE memory_id IN ({placeholders})",  # nosec B608 — mids are UUIDs from DB; placeholders use ?
                tuple(mids),
            )
            deleted = cur.rowcount
            for mid in mids:
                self._db.execute("DELETE FROM memories_fts WHERE memory_id=?", (mid,))
            for mid in mids:
                self._db.execute("DELETE FROM memories_vec WHERE memory_id=?", (mid,))
        return MemoryDeleteResult(deleted=deleted)
