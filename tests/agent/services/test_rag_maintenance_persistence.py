"""tests/agent/services/test_rag_maintenance_persistence.py

Persistence and result-mapping tests for RagMaintenanceService on a real database file.

Contracts under test:
- prune_orphan_vectors() removes chunks_vec rows with no chunks row, keeps valid rows,
  reports the pruned and remaining counts it measured, and persists (a new connection
  sees the result).
- reconcile_url() inserts only the missing chunks_fts entries of one URL, never deletes an
  entry that is not indexed, leaves chunks_vec alone, and persists.
- A failing commit leaves the database unchanged for a new connection.
- rebuild_fts() reports the counts the postcondition measured after the commit, and a run
  stopped by the job's cancellation event reports itself as stopped rather than as success.
- recover() reports integrity_ok from the integrity outcome, not from the VACUUM step.

The tests replace the SQLiteHelper name of the service module with a factory for a file
under tmp_path, so no production path is reached. chunks_vec is a plain table stand-in
for the vec0 table; commit behavior does not depend on the table type.
"""

from __future__ import annotations

import sqlite3
import threading
from collections.abc import Callable
from pathlib import Path
from typing import Any, ClassVar

import agent.services.rag_maintenance_service as svc_module
import pytest
from agent.services.rag_maintenance_service import RagMaintenanceService
from db.helper import SQLiteHelper
from db.models import RecoveryResult

from tests.agent._config_test_defaults import MIN_DB_CONFIG

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


class _RefusedAfterStopHelper(SQLiteHelper):
    """SQLiteHelper that refuses the next statement once the job's event is set.

    The real `interrupt_when` observes the event through the connection progress handler,
    which only fires after `check_every` VM steps, so a short statement on a real connection
    is not stopped deterministically. This records the event it is given and applies the
    documented contract, so the tests prove the write path accepts the event and reports the
    state it reached, not a count it did not measure.
    """

    received: ClassVar[list[threading.Event]] = []

    def interrupt_when(
        self, stop: threading.Event | None, *, check_every: int = 1000
    ) -> None:
        if stop is None:
            return
        self._stop = stop
        type(self).received.append(stop)
        super().interrupt_when(stop, check_every=check_every)

    def execute(self, sql: str, params: tuple | dict = ()) -> sqlite3.Cursor:
        if getattr(self, "_stop", None) is not None and self._stop.is_set():
            raise sqlite3.OperationalError("interrupted")
        return super().execute(sql, params)


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


class TestPruneOrphanVectors:
    """Row 22, Phase 6: the renamed operation reports the counts it measured."""

    def test_removes_orphan_rows_and_persists(
        self, rag_db_path: Path, use_file_db: Callable[..., None]
    ) -> None:
        result = RagMaintenanceService(db_config=MIN_DB_CONFIG).prune_orphan_vectors()

        assert result.pruned == 1
        assert result.remaining == 3
        assert result.verified is True
        rows = _query(rag_db_path, "SELECT chunk_id FROM chunks_vec ORDER BY chunk_id")
        assert rows == [(1,), (2,), (3,)]

    def test_keeps_valid_rows_when_there_is_no_orphan(
        self, rag_db_path: Path, use_file_db: Callable[..., None]
    ) -> None:
        conn = sqlite3.connect(rag_db_path)
        conn.execute("DELETE FROM chunks_vec WHERE chunk_id = 99")
        conn.commit()
        conn.close()

        result = RagMaintenanceService(db_config=MIN_DB_CONFIG).prune_orphan_vectors()

        assert result.pruned == 0
        assert result.remaining == 3
        assert result.verified is True

        rows = _query(rag_db_path, "SELECT chunk_id FROM chunks_vec ORDER BY chunk_id")
        assert rows == [(1,), (2,), (3,)]

    def test_failed_commit_leaves_the_database_unchanged(
        self, rag_db_path: Path, use_file_db: Callable[..., None]
    ) -> None:
        use_file_db(_FailingCommitHelper)

        with pytest.raises(RuntimeError, match="commit failed"):
            RagMaintenanceService(db_config=MIN_DB_CONFIG).prune_orphan_vectors()

        rows = _query(rag_db_path, "SELECT chunk_id FROM chunks_vec ORDER BY chunk_id")
        assert rows == [(1,), (2,), (3,), (99,)]

    def test_stopped_run_reports_the_state_it_was_in(
        self, rag_db_path: Path, use_file_db: Callable[..., None]
    ) -> None:
        """A run stopped by the job's event reports itself as stopped and verifies nothing."""
        _RefusedAfterStopHelper.received.clear()
        use_file_db(_RefusedAfterStopHelper)
        stop = threading.Event()
        stop.set()

        result = RagMaintenanceService(db_config=MIN_DB_CONFIG).prune_orphan_vectors(
            stop=stop
        )

        assert _RefusedAfterStopHelper.received == [stop]
        assert result.interrupted is True
        assert result.verified is False
        assert result.pruned == 0
        assert result.remaining == 0
        # The run wrote nothing, so the orphan row is still there for a new connection.
        assert _query(rag_db_path, "SELECT COUNT(*) FROM chunks_vec") == [(4,)]


class TestReconcileUrl:
    def test_inserts_the_missing_fts_entry_and_persists(
        self, rag_db_path: Path, use_file_db: Callable[..., None]
    ) -> None:
        _make_fts_gap(rag_db_path, 1, "alpha text")
        match = "SELECT rowid FROM chunks_fts WHERE chunks_fts MATCH 'alpha'"
        assert _query(rag_db_path, match) == []

        result = RagMaintenanceService(db_config=MIN_DB_CONFIG).reconcile_url(_URL_A)

        assert result == {"found": True, "chunks": 2}
        assert _query(rag_db_path, match) == [(1,)]

    def test_leaves_vector_rows_and_indexed_entries_unchanged(
        self, rag_db_path: Path, use_file_db: Callable[..., None]
    ) -> None:
        _make_fts_gap(rag_db_path, 1, "alpha text")

        RagMaintenanceService(db_config=MIN_DB_CONFIG).reconcile_url(_URL_A)

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
        result = RagMaintenanceService(db_config=MIN_DB_CONFIG).reconcile_url(_URL_A)

        assert result == {"found": True, "chunks": 2}
        match = "SELECT rowid FROM chunks_fts WHERE chunks_fts MATCH 'alpha'"
        assert _query(rag_db_path, match) == [(1,)]

    def test_unknown_url_returns_found_false(
        self, use_file_db: Callable[..., None]
    ) -> None:
        assert RagMaintenanceService(db_config=MIN_DB_CONFIG).reconcile_url(
            "http://none.example"
        ) == {"found": False}

    def test_failed_commit_leaves_the_gap(
        self, rag_db_path: Path, use_file_db: Callable[..., None]
    ) -> None:
        _make_fts_gap(rag_db_path, 1, "alpha text")
        use_file_db(_FailingCommitHelper)

        with pytest.raises(RuntimeError, match="commit failed"):
            RagMaintenanceService(db_config=MIN_DB_CONFIG).reconcile_url(_URL_A)

        match = "SELECT rowid FROM chunks_fts WHERE chunks_fts MATCH 'alpha'"
        assert _query(rag_db_path, match) == []


class TestRebuildFtsPostcondition:
    """Row 46: the FTS result is the postcondition's measurement, and a stopped run is reported as stopped."""

    def test_postcondition_counts_are_the_rows_the_commit_left(
        self, rag_db_path: Path, use_file_db: Callable[..., None]
    ) -> None:
        """The result reports what the index holds after the commit, not what the run inserted."""
        _make_fts_gap(rag_db_path, 1, "alpha text")
        use_file_db()

        result = RagMaintenanceService(db_config=MIN_DB_CONFIG).rebuild_fts()

        assert result.chunks == 3
        assert result.fts_rows == 3
        assert result.verified is True
        assert _query(rag_db_path, "SELECT COUNT(*) FROM chunks_fts_docsize") == [(3,)]

    def test_stopped_run_reports_the_state_it_was_in(
        self, rag_db_path: Path, use_file_db: Callable[..., None]
    ) -> None:
        """The job's event reaches the connection, and the run reports itself as stopped.

        A stopped run never reports success, and it reports no count it did not measure
        (REQ-002, REQ-004).
        """
        _make_fts_gap(rag_db_path, 1, "alpha text")
        _RefusedAfterStopHelper.received.clear()
        use_file_db(_RefusedAfterStopHelper)
        stop = threading.Event()
        stop.set()

        result = RagMaintenanceService(db_config=MIN_DB_CONFIG).rebuild_fts(stop=stop)

        assert _RefusedAfterStopHelper.received == [stop]
        assert result.interrupted is True
        assert result.verified is False
        assert result.rows_inserted == 0
        assert result.fts_rows == 0
        # The run wrote nothing, so the gap the fixture left is still there.
        assert _query(rag_db_path, "SELECT COUNT(*) FROM chunks_fts_docsize") == [(2,)]

    def test_write_methods_accept_the_cancellation_event(
        self, rag_db_path: Path, use_file_db: Callable[..., None]
    ) -> None:
        """Both RAG write paths install the event on the connection they run on (REQ-002)."""
        _RefusedAfterStopHelper.received.clear()
        use_file_db(_RefusedAfterStopHelper)
        stop = threading.Event()

        RagMaintenanceService(db_config=MIN_DB_CONFIG).rebuild_fts(stop=stop)
        RagMaintenanceService(db_config=MIN_DB_CONFIG).prune_orphan_vectors(stop=stop)

        assert _RefusedAfterStopHelper.received == [stop, stop]


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
            lambda _db_config, _backup: RecoveryResult(
                success=success, action=action, detail="d"
            ),
        )

        result = RagMaintenanceService(db_config=MIN_DB_CONFIG).recover(None)

        assert (result.integrity_ok, result.recovered) == (integrity_ok, recovered)
