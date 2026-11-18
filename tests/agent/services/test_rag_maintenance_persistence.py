"""tests/agent/services/test_rag_maintenance_persistence.py

Persistence and result-mapping tests for RagMaintenanceService on a real database file.

Contracts under test:
- rebuild_vec() removes chunks_vec rows with no chunks row, keeps valid rows, returns the
  rows left, and persists (a new connection sees the result).
- reconcile_url() inserts only the missing chunks_fts entries of one URL, never deletes an
  entry that is not indexed, leaves chunks_vec alone, and persists.
- A failing commit leaves the database unchanged for a new connection.
- recover() reports integrity_ok from the integrity outcome, not from the VACUUM step.

The tests replace the SQLiteHelper name of the service module with a factory for a file
under tmp_path, so no production path is reached. chunks_vec is a plain table stand-in
for the vec0 table; commit behavior does not depend on the table type.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Callable
from pathlib import Path
from typing import Any

import agent.services.rag_maintenance_service as svc_module
import pytest
from agent.services.rag_maintenance_service import RagMaintenanceService
from db.helper import SQLiteHelper
from db.models import RecoveryResult

_SCHEMA = """
CREATE TABLE documents (
    doc_id INTEGER PRIMARY KEY AUTOINCREMENT,
    url    TEXT NOT NULL UNIQUE
);
CREATE TABLE chunks (
    chunk_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_id             INTEGER NOT NULL REFERENCES documents(doc_id) ON DELETE CASCADE,
    chunk_index        INTEGER NOT NULL,
    content            TEXT NOT NULL,
    normalized_content TEXT,
    UNIQUE (doc_id, chunk_index)
);
CREATE TABLE chunks_vec (
    chunk_id  INTEGER PRIMARY KEY,
    embedding BLOB
);
CREATE VIRTUAL TABLE chunks_fts USING fts5(
    content,
    content       = 'chunks',
    content_rowid = 'chunk_id',
    tokenize      = 'unicode61'
);
CREATE TRIGGER chunks_ai AFTER INSERT ON chunks BEGIN
    INSERT INTO chunks_fts (rowid, content)
    VALUES (new.chunk_id, COALESCE(new.normalized_content, new.content));
END;
"""

_URL_A = "http://a.example"
_URL_B = "http://b.example"


class _FailingCommitHelper(SQLiteHelper):
    """SQLiteHelper whose commit fails, to prove a failed repair is rolled back."""

    def commit(self) -> None:
        raise RuntimeError("commit failed")


def _query(path: Path, sql: str) -> list[Any]:
    """Run one query on a brand-new connection, as another process would."""
    conn = sqlite3.connect(path)
    try:
        return conn.execute(sql).fetchall()
    finally:
        conn.close()


@pytest.fixture
def rag_db_path(tmp_path: Path) -> Path:
    """rag.sqlite with canonical table shapes: chunks has no embedding column."""
    path = tmp_path / "rag.sqlite"
    conn = sqlite3.connect(path)
    conn.executescript(_SCHEMA)
    conn.execute("INSERT INTO documents (url) VALUES (?)", (_URL_A,))
    conn.execute("INSERT INTO documents (url) VALUES (?)", (_URL_B,))
    chunks = [
        (1, 0, "alpha text"),
        (1, 1, "beta text"),
        (2, 0, "gamma text"),
    ]
    for doc_id, chunk_index, content in chunks:
        conn.execute(
            "INSERT INTO chunks (doc_id, chunk_index, content) VALUES (?, ?, ?)",
            (doc_id, chunk_index, content),
        )
    for chunk_id in (1, 2, 3, 99):  # 99 is an orphan: no chunks row
        conn.execute(
            "INSERT INTO chunks_vec (chunk_id, embedding) VALUES (?, ?)",
            (chunk_id, b"\x01"),
        )
    conn.commit()
    conn.close()
    return path


@pytest.fixture
def use_file_db(
    monkeypatch: pytest.MonkeyPatch, rag_db_path: Path
) -> Callable[[type[SQLiteHelper]], None]:
    """Point the service at rag_db_path; the returned callable swaps the helper class."""

    def install(helper_cls: type[SQLiteHelper] = SQLiteHelper) -> None:
        monkeypatch.setattr(
            svc_module,
            "SQLiteHelper",
            lambda *_a, **_k: helper_cls(db_path=str(rag_db_path)),
        )

    install()
    return install


def _make_fts_gap(path: Path, chunk_id: int, indexed_text: str) -> None:
    """Remove one chunk's index entry only, leaving a gap the repair must fill."""
    conn = sqlite3.connect(path)
    conn.execute(
        "INSERT INTO chunks_fts (chunks_fts, rowid, content) VALUES ('delete', ?, ?)",
        (chunk_id, indexed_text),
    )
    conn.commit()
    conn.close()


class TestRebuildVec:
    def test_removes_orphan_rows_and_persists(
        self, rag_db_path: Path, use_file_db: Callable[..., None]
    ) -> None:
        remaining = RagMaintenanceService().rebuild_vec()

        assert remaining == 3
        rows = _query(rag_db_path, "SELECT chunk_id FROM chunks_vec ORDER BY chunk_id")
        assert rows == [(1,), (2,), (3,)]

    def test_keeps_valid_rows_when_there_is_no_orphan(
        self, rag_db_path: Path, use_file_db: Callable[..., None]
    ) -> None:
        conn = sqlite3.connect(rag_db_path)
        conn.execute("DELETE FROM chunks_vec WHERE chunk_id = 99")
        conn.commit()
        conn.close()

        assert RagMaintenanceService().rebuild_vec() == 3

        rows = _query(rag_db_path, "SELECT chunk_id FROM chunks_vec ORDER BY chunk_id")
        assert rows == [(1,), (2,), (3,)]

    def test_failed_commit_leaves_the_database_unchanged(
        self, rag_db_path: Path, use_file_db: Callable[..., None]
    ) -> None:
        use_file_db(_FailingCommitHelper)

        with pytest.raises(RuntimeError, match="commit failed"):
            RagMaintenanceService().rebuild_vec()

        rows = _query(rag_db_path, "SELECT chunk_id FROM chunks_vec ORDER BY chunk_id")
        assert rows == [(1,), (2,), (3,), (99,)]


class TestReconcileUrl:
    def test_inserts_the_missing_fts_entry_and_persists(
        self, rag_db_path: Path, use_file_db: Callable[..., None]
    ) -> None:
        _make_fts_gap(rag_db_path, 1, "alpha text")
        match = "SELECT rowid FROM chunks_fts WHERE chunks_fts MATCH 'alpha'"
        assert _query(rag_db_path, match) == []

        result = RagMaintenanceService().reconcile_url(_URL_A)

        assert result == {"found": True, "chunks": 2}
        assert _query(rag_db_path, match) == [(1,)]

    def test_leaves_vector_rows_and_indexed_entries_unchanged(
        self, rag_db_path: Path, use_file_db: Callable[..., None]
    ) -> None:
        _make_fts_gap(rag_db_path, 1, "alpha text")

        RagMaintenanceService().reconcile_url(_URL_A)

        vec = _query(rag_db_path, "SELECT chunk_id FROM chunks_vec ORDER BY chunk_id")
        assert vec == [(1,), (2,), (3,), (99,)]
        beta = "SELECT rowid FROM chunks_fts WHERE chunks_fts MATCH 'beta'"
        assert _query(rag_db_path, beta) == [(2,)]
        conn = sqlite3.connect(rag_db_path)
        try:
            conn.execute(
                "INSERT INTO chunks_fts (chunks_fts) VALUES ('integrity-check')"
            )
        finally:
            conn.close()

    def test_consistent_index_is_not_touched(
        self, rag_db_path: Path, use_file_db: Callable[..., None]
    ) -> None:
        result = RagMaintenanceService().reconcile_url(_URL_A)

        assert result == {"found": True, "chunks": 2}
        match = "SELECT rowid FROM chunks_fts WHERE chunks_fts MATCH 'alpha'"
        assert _query(rag_db_path, match) == [(1,)]

    def test_unknown_url_returns_found_false(
        self, use_file_db: Callable[..., None]
    ) -> None:
        assert RagMaintenanceService().reconcile_url("http://none.example") == {
            "found": False
        }

    def test_failed_commit_leaves_the_gap(
        self, rag_db_path: Path, use_file_db: Callable[..., None]
    ) -> None:
        _make_fts_gap(rag_db_path, 1, "alpha text")
        use_file_db(_FailingCommitHelper)

        with pytest.raises(RuntimeError, match="commit failed"):
            RagMaintenanceService().reconcile_url(_URL_A)

        match = "SELECT rowid FROM chunks_fts WHERE chunks_fts MATCH 'alpha'"
        assert _query(rag_db_path, match) == []


class TestRecoverIntegrityMapping:
    @pytest.mark.parametrize(
        ("success", "action", "integrity_ok", "recovered"),
        [
            (True, "vacuum", True, False),
            (False, "vacuum_failed", True, False),
            (True, "restored", True, True),
            (False, "restore_verify_failed", False, False),
            (False, "no_backup", False, False),
            (False, "rollback_failed", False, False),
        ],
    )
    def test_integrity_ok_reflects_the_integrity_outcome(
        self,
        monkeypatch: pytest.MonkeyPatch,
        success: bool,
        action: str,
        integrity_ok: bool,
        recovered: bool,
    ) -> None:
        monkeypatch.setattr(
            svc_module,
            "recover_corruption",
            lambda _path: RecoveryResult(success=success, action=action, detail="d"),
        )

        result = RagMaintenanceService().recover(None)

        assert (result.integrity_ok, result.recovered) == (integrity_ok, recovered)
