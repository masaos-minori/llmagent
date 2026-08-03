"""tests/test_fetch_order.py
Ordering regression tests for fetch_full_document() in rag/repository.py.

Verifies that full-document and windowed retrieval return chunks in correct
ascending chunk_index order.
"""

from __future__ import annotations

import sqlite3

from rag.repository import fetch_full_document

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS documents (
    doc_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    url       TEXT NOT NULL UNIQUE,
    title     TEXT
);
CREATE TABLE IF NOT EXISTS chunks (
    chunk_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_id             INTEGER NOT NULL REFERENCES documents(doc_id) ON DELETE CASCADE,
    chunk_index        INTEGER NOT NULL,
    content            TEXT NOT NULL,
    normalized_content TEXT
);
CREATE TABLE IF NOT EXISTS chunks_vec (
    chunk_id INTEGER PRIMARY KEY
)
"""


class _FakeSQLiteHelper:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn
        self._conn.row_factory = sqlite3.Row

    def execute(self, sql: str, params: tuple | dict = ()) -> sqlite3.Cursor:
        return self._conn.execute(sql, params)

    def fetchall(self, sql: str, params: tuple | dict = ()) -> list:
        return self._conn.execute(sql, params).fetchall()

    def commit(self) -> None:
        self._conn.commit()


def _make_db() -> _FakeSQLiteHelper:
    conn = sqlite3.connect(":memory:")
    conn.executescript(_SCHEMA_SQL)
    return _FakeSQLiteHelper(conn)


def _insert_doc(db: _FakeSQLiteHelper, url: str = "https://example.com/doc") -> int:
    cur = db.execute("INSERT INTO documents (url, title) VALUES (?, ?)", (url, "Test"))
    db.commit()
    assert cur.lastrowid is not None
    return cur.lastrowid


def _insert_chunk(
    db: _FakeSQLiteHelper, doc_id: int, chunk_index: int, content: str
) -> int:
    cur = db.execute(
        "INSERT INTO chunks (doc_id, chunk_index, content) VALUES (?, ?, ?)",
        (doc_id, chunk_index, content),
    )
    db.commit()
    assert cur.lastrowid is not None
    return cur.lastrowid


class TestFetchFullDocumentOrder:
    def test_fetch_full_document_returns_chunks_in_index_order(self) -> None:
        db = _make_db()
        doc_id = _insert_doc(db)
        ids = [_insert_chunk(db, doc_id, i, f"content {i}") for i in range(5)]
        result = fetch_full_document(ids[2], db)
        assert len(result) == 5
        assert [r.content for r in result] == [f"content {i}" for i in range(5)]

    def test_fetch_from_middle_chunk_returns_all_chunks(self) -> None:
        db = _make_db()
        doc_id = _insert_doc(db)
        ids = [_insert_chunk(db, doc_id, i, f"chunk {i}") for i in range(4)]
        for cid in ids:
            result = fetch_full_document(cid, db)
            assert len(result) == 4

    def test_fetch_nonexistent_chunk_id_returns_empty(self) -> None:
        db = _make_db()
        assert fetch_full_document(99999, db) == []

    def test_window_fetch_returns_correct_subset(self) -> None:
        """window=2 around index 5 returns indices 3-7 (5 chunks)."""
        db = _make_db()
        doc_id = _insert_doc(db)
        ids = [_insert_chunk(db, doc_id, i, f"c{i}") for i in range(10)]
        result = fetch_full_document(ids[5], db, window=2)
        assert len(result) == 5
        assert [r.content for r in result] == [f"c{i}" for i in range(3, 8)]

    def test_window_fetch_ordered_within_subset(self) -> None:
        db = _make_db()
        doc_id = _insert_doc(db)
        ids = [_insert_chunk(db, doc_id, i, f"c{i}") for i in range(8)]
        result = fetch_full_document(ids[4], db, window=3)
        contents = [r.content for r in result]
        assert contents == sorted(contents, key=lambda c: int(c[1:]))

    def test_window_fetch_at_start_boundary(self) -> None:
        """window around index 0 does not produce negative-index chunks."""
        db = _make_db()
        doc_id = _insert_doc(db)
        ids = [_insert_chunk(db, doc_id, i, f"c{i}") for i in range(5)]
        result = fetch_full_document(ids[0], db, window=3)
        assert len(result) == 4  # indices 0..3
        assert result[0].content == "c0"

    def test_window_fetch_at_end_boundary(self) -> None:
        """window around last index does not exceed available chunks."""
        db = _make_db()
        doc_id = _insert_doc(db)
        ids = [_insert_chunk(db, doc_id, i, f"c{i}") for i in range(5)]
        result = fetch_full_document(ids[4], db, window=3)
        assert len(result) == 4  # indices 1..4
        assert result[-1].content == "c4"

    def test_window_fetch_nonexistent_chunk_id_returns_empty(self) -> None:
        db = _make_db()
        assert fetch_full_document(99999, db, window=2) == []

    def test_duplicate_chunk_index_documents_current_limitation(self) -> None:
        """Chunks with same chunk_index (BUG-3 state) are returned in rowid order."""
        db = _make_db()
        doc_id = _insert_doc(db)
        id0 = _insert_chunk(db, doc_id, 0, "first")
        id1 = _insert_chunk(db, doc_id, 0, "second")
        id2 = _insert_chunk(db, doc_id, 0, "third")
        result = fetch_full_document(id0, db)
        assert len(result) == 3
        assert [r.chunk_id for r in result] == [id0, id1, id2]
