"""tests/test_rag_consistency.py
Regression tests for check_rag_consistency(), is_consistent(), and summarize_issues()
in db/maintenance.py.
"""

from __future__ import annotations

import sqlite3

from db.maintenance import (
    RagConsistencyReport,
    check_rag_consistency,
    is_consistent,
    summarize_issues,
)

# ── In-memory SQLite helper ───────────────────────────────────────────────────


class _FakeSQLiteHelper:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def fetchall(self, sql: str, params: tuple = ()) -> list[sqlite3.Row]:
        return self.conn.execute(sql, params).fetchall()

    def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        return self.conn.execute(sql, params)

    def commit(self) -> None:
        self.conn.commit()


# ── Schema (chunks_vec replaced with a plain table to avoid vec0 extension) ──

_RAG_SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    doc_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    url       TEXT NOT NULL UNIQUE,
    title     TEXT,
    lang      TEXT,
    fetched_at TEXT,
    etag      TEXT,
    last_modified TEXT,
    chunking_strategy TEXT
);
CREATE TABLE IF NOT EXISTS chunks (
    chunk_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_id             INTEGER NOT NULL REFERENCES documents(doc_id) ON DELETE CASCADE,
    content            TEXT NOT NULL,
    normalized_content TEXT,
    chunk_index        INTEGER,
    chunk_type         TEXT
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
END
"""


def _make_rag_db() -> _FakeSQLiteHelper:
    conn = sqlite3.connect(":memory:")
    conn.executescript(
        _RAG_SCHEMA
    )  # executescript handles trigger bodies with semicolons
    return _FakeSQLiteHelper(conn)


def _insert_doc(db: _FakeSQLiteHelper) -> int:
    cur = db.execute(
        "INSERT INTO documents (url, title) VALUES (?, ?)",
        ("https://example.com/doc", "Test Doc"),
    )
    db.commit()
    assert cur.lastrowid is not None
    return cur.lastrowid


def _insert_chunk(db: _FakeSQLiteHelper, doc_id: int, content: str) -> int:
    cur = db.execute(
        "INSERT INTO chunks (doc_id, content) VALUES (?, ?)",
        (doc_id, content),
    )
    db.commit()
    assert cur.lastrowid is not None
    return cur.lastrowid


# ── Tests ─────────────────────────────────────────────────────────────────────


class TestRagConsistency:
    def test_consistency_report_counts_match(self) -> None:
        db = _make_rag_db()
        doc_id = _insert_doc(db)
        chunk_id = _insert_chunk(db, doc_id, "hello world")
        db.execute("INSERT INTO chunks_vec (chunk_id) VALUES (?)", (chunk_id,))
        db.commit()

        report = check_rag_consistency(db)  # type: ignore[arg-type]  # _FakeSQLiteHelper is structurally compatible: exposes execute() and commit()
        assert report.chunks == 1
        assert report.fts == 1
        assert report.vec == 1
        assert report.orphan_vec_count == 0
        assert report.fts_gap == 0
        assert report.fts_orphan_count == 0
        assert isinstance(report, RagConsistencyReport)
        assert is_consistent(report)
        assert summarize_issues(report) == []

    def test_orphan_vec_detected(self) -> None:
        db = _make_rag_db()
        db.execute("INSERT INTO chunks_vec (chunk_id) VALUES (99999)", ())
        db.commit()

        report = check_rag_consistency(db)  # type: ignore[arg-type]  # _FakeSQLiteHelper is structurally compatible: exposes execute() and commit()
        assert report.orphan_vec_count == 1
        assert not is_consistent(report)
        issues = summarize_issues(report)
        assert any("Orphan vec" in i for i in issues)

    def test_fts_gap_after_clean_delete(self) -> None:
        db = _make_rag_db()
        doc_id = _insert_doc(db)
        chunk_id = _insert_chunk(db, doc_id, "text to delete")
        db.execute("INSERT INTO chunks_vec (chunk_id) VALUES (?)", (chunk_id,))
        db.execute("DELETE FROM chunks WHERE chunk_id = ?", (chunk_id,))
        db.execute("DELETE FROM chunks_vec WHERE chunk_id = ?", (chunk_id,))
        db.commit()

        report = check_rag_consistency(db)  # type: ignore[arg-type]  # _FakeSQLiteHelper is structurally compatible: exposes execute() and commit()
        assert report.chunks == 0
        assert report.fts == 0
        assert report.fts_gap == 0
        assert is_consistent(report)

    def test_fts_gap_detected_after_broken_delete(self) -> None:
        db = _make_rag_db()
        doc_id = _insert_doc(db)
        chunk_id = _insert_chunk(db, doc_id, "orphaned fts row")
        # Simulate broken trigger: manually remove FTS entry without touching chunks
        db.execute(
            "INSERT INTO chunks_fts (chunks_fts, rowid, content) VALUES ('delete', ?, ?)",
            (chunk_id, "orphaned fts row"),
        )
        db.commit()

        report = check_rag_consistency(db)  # type: ignore[arg-type]  # _FakeSQLiteHelper is structurally compatible: exposes execute() and commit()
        assert report.chunks == 1
        assert report.fts == 0
        assert report.fts_gap == 1
        assert not is_consistent(report)
        issues = summarize_issues(report)
        assert any("FTS gap" in i for i in issues)

    def test_consistency_after_force_reinsert(self) -> None:
        db = _make_rag_db()
        doc_id = _insert_doc(db)
        chunk_id = _insert_chunk(db, doc_id, "reinsert content")
        db.execute("INSERT INTO chunks_vec (chunk_id) VALUES (?)", (chunk_id,))
        db.commit()

        # Force-reinsert: delete order vec → chunks → documents
        db.execute("DELETE FROM chunks_vec WHERE chunk_id = ?", (chunk_id,))
        db.execute("DELETE FROM chunks WHERE chunk_id = ?", (chunk_id,))
        db.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))
        db.commit()

        # Re-insert
        doc_id2 = _insert_doc(db)
        chunk_id2 = _insert_chunk(db, doc_id2, "reinsert content")
        db.execute("INSERT INTO chunks_vec (chunk_id) VALUES (?)", (chunk_id2,))
        db.commit()

        report = check_rag_consistency(db)  # type: ignore[arg-type]  # _FakeSQLiteHelper is structurally compatible: exposes execute() and commit()
        assert report.chunks == 1
        assert report.fts == 1
        assert report.vec == 1
        assert is_consistent(report)


class TestRagConsistencySeverity:
    def test_fts_orphan_detected_when_fts_exceeds_chunks(self) -> None:
        # Simulate stale FTS entries (fts > chunks): insert chunk then delete only the
        # chunks row without updating the FTS index.
        db = _make_rag_db()
        doc_id = _insert_doc(db)
        chunk_id = _insert_chunk(db, doc_id, "stale fts content")
        # Remove from chunks without triggering the ad trigger (bypass cascade)
        db.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))
        # FTS entry still exists but chunk is gone (ON DELETE CASCADE removed the row,
        # but the ad trigger ran correctly). Re-insert FTS entry manually to simulate drift.
        db.execute(
            "INSERT INTO chunks_fts (rowid, content) VALUES (?, ?)",
            (chunk_id + 1000, "ghost entry"),
        )
        db.commit()

        report = check_rag_consistency(db)  # type: ignore[arg-type]
        assert report.fts > report.chunks
        assert report.fts_orphan_count > 0
        assert not is_consistent(report)
        issues = summarize_issues(report)
        assert any(
            "[CRITICAL]" in i and "FTS index has more entries" in i for i in issues
        )

    def test_summarize_issues_fts_gap_has_warning_prefix(self) -> None:
        db = _make_rag_db()
        doc_id = _insert_doc(db)
        chunk_id = _insert_chunk(db, doc_id, "gap test")
        db.execute(
            "INSERT INTO chunks_fts (chunks_fts, rowid, content) VALUES ('delete', ?, ?)",
            (chunk_id, "gap test"),
        )
        db.commit()

        issues = summarize_issues(check_rag_consistency(db))  # type: ignore[arg-type]
        assert any("[WARNING]" in i and "FTS gap" in i for i in issues)

    def test_summarize_issues_orphan_vec_has_critical_prefix(self) -> None:
        db = _make_rag_db()
        db.execute("INSERT INTO chunks_vec (chunk_id) VALUES (99999)", ())
        db.commit()

        issues = summarize_issues(check_rag_consistency(db))  # type: ignore[arg-type]
        assert any("[CRITICAL]" in i and "Orphan vec" in i for i in issues)

    def test_summarize_issues_fts_gap_includes_rebuild_guidance(self) -> None:
        db = _make_rag_db()
        doc_id = _insert_doc(db)
        chunk_id = _insert_chunk(db, doc_id, "rebuild guidance test")
        db.execute(
            "INSERT INTO chunks_fts (chunks_fts, rowid, content) VALUES ('delete', ?, ?)",
            (chunk_id, "rebuild guidance test"),
        )
        db.commit()

        issues = summarize_issues(check_rag_consistency(db))  # type: ignore[arg-type]
        assert any("/db rag rebuild-fts" in i for i in issues)

    def test_summarize_issues_orphan_vec_includes_force_guidance(self) -> None:
        db = _make_rag_db()
        db.execute("INSERT INTO chunks_vec (chunk_id) VALUES (88888)", ())
        db.commit()

        issues = summarize_issues(check_rag_consistency(db))  # type: ignore[arg-type]
        assert any("--force" in i for i in issues)

    def test_fts_gap_includes_doc_ids(self) -> None:
        db = _make_rag_db()
        doc_id = _insert_doc(db)
        chunk_id = _insert_chunk(db, doc_id, "doc id test")
        db.execute(
            "INSERT INTO chunks_fts (chunks_fts, rowid, content) VALUES ('delete', ?, ?)",
            (chunk_id, "doc id test"),
        )
        db.commit()

        report = check_rag_consistency(db)  # type: ignore[arg-type]
        assert report.fts_gap == 1
        assert report.affected_doc_ids is not None
        assert doc_id in report.affected_doc_ids
        assert report.affected_chunk_ids is not None
        assert chunk_id in report.affected_chunk_ids

    def test_fts_orphan_no_doc_ids_available(self) -> None:
        # Simulate stale FTS entries (fts > chunks): insert chunk then delete only the
        # chunks row without updating the FTS index.
        db = _make_rag_db()
        doc_id = _insert_doc(db)
        chunk_id = _insert_chunk(db, doc_id, "stale fts content")
        # Remove from chunks without triggering the ad trigger (bypass cascade)
        db.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))
        # FTS entry still exists but chunk is gone (ON DELETE CASCADE removed the row,
        # but the ad trigger ran correctly). Re-insert FTS entry manually to simulate drift.
        db.execute(
            "INSERT INTO chunks_fts (rowid, content) VALUES (?, ?)",
            (chunk_id + 1000, "ghost entry"),
        )
        db.commit()

        report = check_rag_consistency(db)  # type: ignore[arg-type]
        assert report.fts_orphan_count > 0
        # affected_doc_ids is None because chunks and documents rows are gone
        assert report.affected_doc_ids is None

    def test_vec_chunk_mismatch_detected(self) -> None:
        db = _make_rag_db()
        doc_id = _insert_doc(db)
        _insert_chunk(db, doc_id, "vec mismatch")
        # Insert into chunks but not chunks_vec
        db.commit()

        report = check_rag_consistency(db)  # type: ignore[arg-type]
        assert report.chunks == 1
        assert report.vec == 0
        assert report.vec != report.chunks
        assert not is_consistent(report)
        issues = summarize_issues(report)
        assert any("Vector count mismatch" in i for i in issues)

    def test_vec_chunk_mismatch_includes_repair_guidance(self) -> None:
        db = _make_rag_db()
        doc_id = _insert_doc(db)
        _insert_chunk(db, doc_id, "vec mismatch repair")
        db.commit()

        report = check_rag_consistency(db)  # type: ignore[arg-type]
        issues = summarize_issues(report)
        assert any("ingester.py --force" in i for i in issues)

    def test_fts_orphan_does_not_report_fts_gap_doc_ids(self) -> None:
        """FTS orphan_count > 0 with fts_gap == 0 should not include 'Affected doc_ids' in issue string."""
        db = _make_rag_db()
        doc_id = _insert_doc(db)
        chunk_id = _insert_chunk(db, doc_id, "stale fts content")
        db.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))
        db.execute(
            "INSERT INTO chunks_fts (rowid, content) VALUES (?, ?)",
            (chunk_id + 1000, "ghost entry"),
        )
        db.commit()

        report = check_rag_consistency(db)  # type: ignore[arg-type]
        assert report.fts_orphan_count > 0
        assert report.fts_gap == 0
        assert report.affected_doc_ids is None
        issues = summarize_issues(report)
        fts_orphan_issue = next(
            (
                i
                for i in issues
                if "[CRITICAL]" in i and "FTS index has more entries" in i
            ),
            None,
        )
        assert fts_orphan_issue is not None
        assert "Affected doc_ids" not in fts_orphan_issue
