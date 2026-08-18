"""tests/test_delete_chain.py
Tests for delete_document_chain(): delete order, orphan-free, idempotent, isolation.
"""

from __future__ import annotations

import sqlite3

from rag.ingestion.document_manager import delete_document_chain

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS documents (
    doc_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    url      TEXT NOT NULL UNIQUE,
    title    TEXT
);
CREATE TABLE IF NOT EXISTS chunks (
    chunk_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_id      INTEGER NOT NULL REFERENCES documents(doc_id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content     TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS chunks_vec (
    chunk_id INTEGER PRIMARY KEY
);
"""


class _FakeSQLiteHelper:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def execute(self, sql: str, params: tuple | dict = ()) -> sqlite3.Cursor:
        return self._conn.execute(sql, params)

    def commit(self) -> None:
        self._conn.commit()


class _TrackingSQLiteHelper(_FakeSQLiteHelper):
    """Records SQL statements in order for delete-order verification."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        super().__init__(conn)
        self.sql_log: list[str] = []

    def execute(self, sql: str, params: tuple | dict = ()) -> sqlite3.Cursor:
        self.sql_log.append(sql.strip())
        return super().execute(sql, params)


def _make_db() -> _FakeSQLiteHelper:
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(_SCHEMA_SQL)
    return _FakeSQLiteHelper(conn)


def _make_tracking_db() -> _TrackingSQLiteHelper:
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(_SCHEMA_SQL)
    return _TrackingSQLiteHelper(conn)


def _insert_doc(db: _FakeSQLiteHelper, url: str = "https://example.com/doc") -> int:
    cur = db.execute("INSERT INTO documents (url, title) VALUES (?, ?)", (url, "T"))
    db.commit()
    assert cur.lastrowid is not None
    return cur.lastrowid


def _insert_chunk(db: _FakeSQLiteHelper, doc_id: int, content: str = "text") -> int:
    cur = db.execute(
        "INSERT INTO chunks (doc_id, chunk_index, content) VALUES (?, ?, ?)",
        (doc_id, 0, content),
    )
    db.commit()
    assert cur.lastrowid is not None
    return cur.lastrowid


def _insert_vec(db: _FakeSQLiteHelper, chunk_id: int) -> None:
    db.execute("INSERT INTO chunks_vec (chunk_id) VALUES (?)", (chunk_id,))
    db.commit()


class TestDeleteDocumentChain:
    def test_delete_removes_all_rows(self) -> None:
        db = _make_db()
        doc_id = _insert_doc(db)
        chunk_id = _insert_chunk(db, doc_id)
        _insert_vec(db, chunk_id)

        delete_document_chain(db, doc_id)

        assert db.execute("SELECT COUNT(*) FROM chunks_vec").fetchone()[0] == 0
        assert db.execute("SELECT COUNT(*) FROM chunks").fetchone()[0] == 0
        assert db.execute("SELECT COUNT(*) FROM documents").fetchone()[0] == 0

    def test_delete_chunks_vec_before_documents(self) -> None:
        """chunks_vec is deleted explicitly first; chunks is removed via
        ON DELETE CASCADE from the documents delete, not by an explicit statement."""
        db = _make_tracking_db()
        doc_id = _insert_doc(db)
        chunk_id = _insert_chunk(db, doc_id)
        _insert_vec(db, chunk_id)

        delete_document_chain(db, doc_id)

        delete_stmts = [s for s in db.sql_log if s.startswith("DELETE FROM")]
        tables = [s.split()[2] for s in delete_stmts]
        assert tables == ["chunks_vec", "documents"]

    def test_delete_idempotent(self) -> None:
        db = _make_db()
        doc_id = _insert_doc(db)
        chunk_id = _insert_chunk(db, doc_id)
        _insert_vec(db, chunk_id)

        delete_document_chain(db, doc_id)
        delete_document_chain(db, doc_id)

        assert db.execute("SELECT COUNT(*) FROM documents").fetchone()[0] == 0

    def test_delete_does_not_remove_other_docs(self) -> None:
        db = _make_db()
        doc_id_a = _insert_doc(db, "https://a.com")
        doc_id_b = _insert_doc(db, "https://b.com")
        chunk_a = _insert_chunk(db, doc_id_a, "a")
        chunk_b = _insert_chunk(db, doc_id_b, "b")
        _insert_vec(db, chunk_a)
        _insert_vec(db, chunk_b)

        delete_document_chain(db, doc_id_a)

        assert db.execute("SELECT COUNT(*) FROM documents").fetchone()[0] == 1
        assert db.execute("SELECT COUNT(*) FROM chunks").fetchone()[0] == 1
        assert db.execute("SELECT COUNT(*) FROM chunks_vec").fetchone()[0] == 1
        remaining_url = db.execute("SELECT url FROM documents").fetchone()[0]
        assert remaining_url == "https://b.com"
