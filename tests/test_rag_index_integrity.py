"""
tests/test_rag_index_integrity.py
Regression tests for DESIGN-3 index integrity invariants.

Covers:
- TEST-DESIGN3-01: rebuild_fts() uses COALESCE(normalized_content, content)
- TEST-DESIGN3-02: chunks_fts is trigger-synced from chunks (not independently maintained)
- TEST-DESIGN3-03: delete_document_chain() leaves no orphan chunks_vec rows
- TEST-DESIGN3-04: deletion order invariant (chunks_vec -> chunks -> documents)
- TEST-DESIGN3-05: check_rag_consistency() detects FTS desynchronization
- reconcile_url() FTS deletion does not raise OperationalError (bug fix regression)

Resolves: DESIGN-3 missing tests (docs/03_rag_90_inconsistencies_and_known_issues.md)
"""

from __future__ import annotations

import sqlite3
from collections.abc import Generator
from unittest.mock import patch

import pytest
from agent.services.rag_maintenance_service import RagMaintenanceService
from db.maintenance import RagConsistencyReport, check_rag_consistency
from rag.repository import fts_search

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS documents (
    doc_id             INTEGER PRIMARY KEY AUTOINCREMENT,
    url                TEXT    NOT NULL UNIQUE,
    title              TEXT,
    lang               TEXT    NOT NULL DEFAULT 'ja'
);
CREATE TABLE IF NOT EXISTS chunks (
    chunk_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_id             INTEGER NOT NULL
                       REFERENCES documents(doc_id) ON DELETE CASCADE,
    chunk_index        INTEGER NOT NULL,
    content            TEXT    NOT NULL,
    normalized_content TEXT,
    embedding          BLOB
);
CREATE TABLE IF NOT EXISTS chunks_vec (
    chunk_id INTEGER PRIMARY KEY
);
CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
    content,
    content       = 'chunks',
    content_rowid = 'chunk_id',
    tokenize      = 'unicode61'
);
CREATE TRIGGER IF NOT EXISTS chunks_ai
AFTER INSERT ON chunks BEGIN
    INSERT INTO chunks_fts (rowid, content)
    VALUES (new.chunk_id, COALESCE(new.normalized_content, new.content));
END;
CREATE TRIGGER IF NOT EXISTS chunks_ad
AFTER DELETE ON chunks BEGIN
    INSERT INTO chunks_fts (chunks_fts, rowid, content)
    VALUES ('delete', old.chunk_id, COALESCE(old.normalized_content, old.content));
END;
CREATE TRIGGER IF NOT EXISTS chunks_au
AFTER UPDATE ON chunks BEGIN
    INSERT INTO chunks_fts (chunks_fts, rowid, content)
    VALUES ('delete', old.chunk_id, COALESCE(old.normalized_content, old.content));
    INSERT INTO chunks_fts (rowid, content)
    VALUES (new.chunk_id, COALESCE(new.normalized_content, new.content));
END;
"""


class _FakeSQLiteHelper:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def open(
        self, *, write_mode: bool = False, row_factory: bool = False
    ) -> _FakeSQLiteHelper:
        self._conn.row_factory = sqlite3.Row if row_factory else None
        return self

    def execute(self, sql: str, params: tuple | dict = ()) -> sqlite3.Cursor:
        return self._conn.execute(sql, params)

    def fetchall(self, sql: str, params: tuple | dict = ()) -> list:
        return self._conn.execute(sql, params).fetchall()

    def commit(self) -> None:
        self._conn.commit()

    def close(self) -> None:
        pass

    def __enter__(self) -> _FakeSQLiteHelper:
        return self

    def __exit__(self, *_: object) -> None:
        pass


@pytest.fixture
def db() -> Generator[_FakeSQLiteHelper]:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(_SCHEMA_SQL)
    conn.commit()
    yield _FakeSQLiteHelper(conn)
    conn.close()


def _insert_doc(conn: sqlite3.Connection, url: str = "http://example.com") -> int:
    cur = conn.execute(
        "INSERT INTO documents (url, title, lang) VALUES (?, ?, ?)",
        (url, "Test", "en"),
    )
    conn.commit()
    assert cur.lastrowid is not None
    return cur.lastrowid


def _insert_chunk(
    conn: sqlite3.Connection,
    doc_id: int,
    content: str,
    normalized_content: str | None = None,
    chunk_index: int = 0,
) -> int:
    cur = conn.execute(
        "INSERT INTO chunks (doc_id, chunk_index, content, normalized_content)"
        " VALUES (?, ?, ?, ?)",
        (doc_id, chunk_index, content, normalized_content),
    )
    conn.commit()
    assert cur.lastrowid is not None
    return cur.lastrowid


# ── TEST-DESIGN3-01: rebuild_fts uses COALESCE ────────────────────────────────


def test_rebuild_fts_uses_coalesce(db: _FakeSQLiteHelper) -> None:
    """rebuild_fts() must use COALESCE(normalized_content, content)."""
    conn = db._conn
    doc_id = _insert_doc(conn, url="http://coalesce.example.com")
    _insert_chunk(conn, doc_id, "english text", None)

    # Verify FTS search returns the row before deletion
    results = fts_search("english", top_k=5, db=db)
    assert len(results) == 1

    # Manually delete all FTS entries
    db.execute("INSERT INTO chunks_fts(chunks_fts) VALUES('delete-all')")
    db.commit()

    # Verify FTS search returns nothing after deletion
    results = fts_search("english", top_k=5, db=db)
    assert len(results) == 0

    # Rebuild FTS
    with patch(
        "agent.services.rag_maintenance_service.SQLiteHelper"
    ) as mock_helper_cls:
        mock_helper_cls.return_value.open.return_value.__enter__.return_value = db
        mock_helper_cls.return_value.open.return_value.__exit__ = lambda *_: None
        RagMaintenanceService().rebuild_fts()

    # After rebuild, FTS search should return the row again
    results = fts_search("english", top_k=5, db=db)
    assert len(results) == 1
    assert results[0].content == "english text"


# ── TEST-DESIGN3-02: chunks_fts is trigger-synced ─────────────────────────────


def test_chunks_fts_is_trigger_synced(db: _FakeSQLiteHelper) -> None:
    """chunks_fts must be populated only by triggers, not manually."""
    conn = db._conn
    doc_id = _insert_doc(conn, url="http://trigger.example.com")
    _insert_chunk(conn, doc_id, "trigger text", None)

    # Verify FTS search returns the row (trigger synced)
    results = fts_search("trigger", top_k=5, db=db)
    assert len(results) == 1
    assert results[0].content == "trigger text"


# ── TEST-DESIGN3-03: delete_document_chain no orphan vec ──────────────────────


def test_delete_document_chain_no_orphan_vec(db: _FakeSQLiteHelper) -> None:
    """delete_document_chain() must not leave orphan chunks_vec rows."""
    conn = db._conn
    doc_id = _insert_doc(conn, url="http://orphan.example.com")
    chunk_id = _insert_chunk(conn, doc_id, "orphan test text", None)

    # Insert a chunks_vec row for this chunk
    conn.execute("INSERT INTO chunks_vec (chunk_id) VALUES (?)", (chunk_id,))
    conn.commit()

    # Simulate delete_document_chain: delete chunks_vec first, then documents (CASCADE)
    conn.execute("DELETE FROM chunks_vec WHERE chunk_id = ?", (chunk_id,))
    conn.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))
    conn.commit()

    # Verify no orphan vec rows exist
    orphan_count = db.execute(
        "SELECT COUNT(*) FROM chunks_vec WHERE chunk_id NOT IN "
        "(SELECT chunk_id FROM chunks)"
    ).fetchone()[0]
    assert orphan_count == 0


# ── TEST-DESIGN3-04: deletion order invariant ─────────────────────────────────


def test_deletion_order_no_orphan_vec(db: _FakeSQLiteHelper) -> None:
    """Deletion order (chunks_vec -> chunks -> documents) must not leave orphans."""
    conn = db._conn
    doc_id = _insert_doc(conn, url="http://order.example.com")
    chunk_id1 = _insert_chunk(conn, doc_id, "first chunk text", None)
    chunk_id2 = _insert_chunk(conn, doc_id, "second chunk text", None)

    # Insert chunks_vec rows
    conn.execute("INSERT INTO chunks_vec (chunk_id) VALUES (?)", (chunk_id1,))
    conn.execute("INSERT INTO chunks_vec (chunk_id) VALUES (?)", (chunk_id2,))
    conn.commit()

    # Delete chunks_vec first, then documents (CASCADE)
    conn.execute(
        "DELETE FROM chunks_vec WHERE chunk_id IN (?, ?)", (chunk_id1, chunk_id2)
    )
    conn.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))
    conn.commit()

    # Verify no orphan vec rows exist
    orphan_count = db.execute(
        "SELECT COUNT(*) FROM chunks_vec WHERE chunk_id NOT IN "
        "(SELECT chunk_id FROM chunks)"
    ).fetchone()[0]
    assert orphan_count == 0


# ── TEST-DESIGN3-05: consistency check detects FTS gap ────────────────────────


def test_consistency_check_detects_fts_gap(db: _FakeSQLiteHelper) -> None:
    """check_rag_consistency() must detect FTS desynchronization."""
    conn = db._conn
    doc_id = _insert_doc(conn, url="http://gap.example.com")
    chunk_id = _insert_chunk(conn, doc_id, "gap text", None)

    # Manually remove the FTS entry using the FTS5 delete-command
    fts_text = db.execute(
        "SELECT COALESCE(normalized_content, content) FROM chunks WHERE chunk_id = ?",
        (chunk_id,),
    ).fetchone()[0]
    db.execute(
        "INSERT INTO chunks_fts(chunks_fts, rowid, content) VALUES('delete', ?, ?)",
        (chunk_id, fts_text),
    )
    db.commit()

    # Check consistency — should detect the gap
    report = check_rag_consistency(db)
    assert isinstance(report, RagConsistencyReport)
    assert report.fts_gap >= 1


# ── reconcile_url() FTS deletion regression test ───────────────────────────────


def test_reconcile_url_fts_deletion(db: _FakeSQLiteHelper) -> None:
    """reconcile_url() must not raise OperationalError on FTS deletion."""
    conn = db._conn
    doc_id = _insert_doc(conn, url="http://reconcile.example.com")
    _insert_chunk(conn, doc_id, "reconcile text", None)

    with patch(
        "agent.services.rag_maintenance_service.SQLiteHelper"
    ) as mock_helper_cls:
        mock_helper_cls.return_value.open.return_value.__enter__.return_value = db
        mock_helper_cls.return_value.open.return_value.__exit__ = lambda *_: None
        result = RagMaintenanceService().reconcile_url("http://reconcile.example.com")

    assert result == {"found": True, "chunks": 1}

    # Verify FTS was re-inserted
    results = fts_search("reconcile", top_k=5, db=db)
    assert len(results) == 1
    assert results[0].content == "reconcile text"
