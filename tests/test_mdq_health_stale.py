"""tests/test_mdq_health_stale.py
Unit tests for mdq-mcp /health stale_document_count field (documents/chunks schema).
"""

from __future__ import annotations

import sqlite3
import time
from pathlib import Path

import pytest


def _create_test_db(path: str) -> None:
    """Create a test database with documents, chunks, and chunks_fts tables."""
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(
        """CREATE TABLE documents (
            doc_id TEXT PRIMARY KEY,
            source_path TEXT NOT NULL,
            mtime_ns INTEGER NOT NULL
        )"""
    )
    conn.execute(
        """CREATE TABLE chunks (
            seq INTEGER PRIMARY KEY,
            doc_id TEXT NOT NULL,
            heading_path TEXT NOT NULL,
            ordinal INTEGER NOT NULL,
            content TEXT NOT NULL,
            source_path TEXT NOT NULL
        )"""
    )
    conn.execute(
        """CREATE VIRTUAL TABLE chunks_fts USING fts5(
            doc_id, heading_path, ordinal, content,
            content=chunks, content_rowid=seq
        )"""
    )
    conn.execute(
        "CREATE TRIGGER chunks_ai AFTER INSERT ON chunks BEGIN "
        "INSERT INTO chunks_fts(rowid, doc_id, heading_path, ordinal, content) "
        "VALUES(new.seq, new.doc_id, new.heading_path, new.ordinal, new.content); END"
    )
    conn.execute(
        "CREATE TRIGGER chunks_ad AFTER DELETE ON chunks BEGIN "
        "INSERT INTO chunks_fts(chunks_fts, rowid, doc_id, heading_path, ordinal, content) "
        "VALUES('delete', old.seq, old.doc_id, old.heading_path, old.ordinal, old.content); END"
    )
    conn.execute(
        "CREATE TRIGGER chunks_au AFTER UPDATE ON chunks BEGIN "
        "INSERT INTO chunks_fts(chunks_fts, rowid, doc_id, heading_path, ordinal, content) "
        "VALUES('delete', old.seq, old.doc_id, old.heading_path, old.ordinal, old.content); "
        "INSERT INTO chunks_fts(rowid, doc_id, heading_path, ordinal, content) "
        "VALUES(new.seq, new.doc_id, new.heading_path, new.ordinal, new.content); END"
    )
    conn.commit()
    conn.close()


@pytest.fixture
def db_path(tmp_path: Path) -> str:
    """Create a test database with documents/chunks/chunks_fts schema."""
    path = str(tmp_path / "mdq_test.sqlite")
    _create_test_db(path)
    return path


def _insert_documents(db_path: str, rows: list[tuple[str | int, str, int]]) -> None:
    """Insert document rows (doc_id, source_path, mtime_ns) into the test database."""
    conn = sqlite3.connect(db_path)
    try:
        for doc_id, source_path, mtime_ns in rows:
            conn.execute(
                "INSERT INTO documents (doc_id, source_path, mtime_ns) VALUES (?, ?, ?)",
                (str(doc_id), source_path, mtime_ns),
            )
        conn.commit()
    finally:
        conn.close()


class TestStaleDocumentCount:
    """Verify stale_document_count queries use mtime_ns (nanoseconds) on documents table."""

    def test_stale_count_zero_when_fresh(self, db_path: str, tmp_path: Path) -> None:
        """mtime_ns matching current time means 0 stale documents."""
        ref_mtime_ns = int(tmp_path.stat().st_mtime * 1_000_000_000)
        _insert_documents(db_path, [(1, "/test/file1.md", ref_mtime_ns)])

        conn = sqlite3.connect(db_path)
        try:
            count = conn.execute(
                "SELECT COUNT(DISTINCT source_path) FROM documents WHERE mtime_ns < ?",
                (ref_mtime_ns,),
            ).fetchone()[0]
        finally:
            conn.close()

        assert (count or 0) == 0

    def test_stale_count_positive_when_outdated(self, db_path: str) -> None:
        """mtime_ns older than current time means stale count > 0."""
        old_ns = int((time.time() - 86400) * 1_000_000_000)
        ref_ns = int(time.time() * 1_000_000_000)
        _insert_documents(db_path, [(1, "/test/file1.md", old_ns)])

        conn = sqlite3.connect(db_path)
        try:
            count = conn.execute(
                "SELECT COUNT(DISTINCT source_path) FROM documents WHERE mtime_ns < ?",
                (ref_ns,),
            ).fetchone()[0]
        finally:
            conn.close()

        assert (count or 0) == 1

    def test_stale_count_deduplicates_by_source_path(self, db_path: str) -> None:
        """Multiple documents for same source_path counted once."""
        old_ns = int((time.time() - 86400) * 1_000_000_000)
        ref_ns = int(time.time() * 1_000_000_000)
        _insert_documents(
            db_path,
            [
                (1, "/test/file1.md", old_ns),
                (2, "/test/file1.md", old_ns),
            ],
        )

        conn = sqlite3.connect(db_path)
        try:
            count = conn.execute(
                "SELECT COUNT(DISTINCT source_path) FROM documents WHERE mtime_ns < ?",
                (ref_ns,),
            ).fetchone()[0]
        finally:
            conn.close()

        assert (count or 0) == 1

    def test_stale_count_mixed_fresh_and_old(
        self, db_path: str, tmp_path: Path
    ) -> None:
        """Only stale documents (older mtime_ns) are counted."""
        ref_ns = int(tmp_path.stat().st_mtime * 1_000_000_000)
        old_ns = ref_ns - 86_400_000_000_000
        _insert_documents(
            db_path,
            [
                (1, "/test/file1.md", ref_ns),
                (2, "/test/file2.md", old_ns),
                (3, "/test/file3.md", old_ns),
            ],
        )

        conn = sqlite3.connect(db_path)
        try:
            count = conn.execute(
                "SELECT COUNT(DISTINCT source_path) FROM documents WHERE mtime_ns < ?",
                (ref_ns,),
            ).fetchone()[0]
        finally:
            conn.close()

        assert (count or 0) == 2


class TestCheckStaleDocuments:
    """Unit tests for _check_stale_documents() using new schema."""

    def test_stale_one_old_document(self, db_path: str, tmp_path: Path) -> None:
        """_check_stale_documents returns 1 when one document is older than index path mtime."""
        from mcp.mdq.server import _check_stale_documents  # noqa: PLC0415

        ref_ns = int(tmp_path.stat().st_mtime * 1_000_000_000)
        old_ns = ref_ns - 86_400_000_000_000
        _insert_documents(db_path, [("doc1", "/test/file1.md", old_ns)])  # type: ignore[arg-type]

        conn = sqlite3.connect(db_path)
        try:
            result = _check_stale_documents(conn, {"index_paths": [str(tmp_path)]})
        finally:
            conn.close()

        assert result == 1

    def test_zero_stale_when_all_fresh(self, db_path: str, tmp_path: Path) -> None:
        """_check_stale_documents returns 0 when all documents have future mtime_ns."""
        from mcp.mdq.server import _check_stale_documents  # noqa: PLC0415

        # Use a future mtime so the document is always newer than index path mtime
        future_ns = int((time.time() + 86400) * 1_000_000_000)
        _insert_documents(db_path, [("doc1", "/test/file1.md", future_ns)])

        conn = sqlite3.connect(db_path)
        try:
            result = _check_stale_documents(conn, {"index_paths": [str(tmp_path)]})
        finally:
            conn.close()

        assert result == 0

    def test_returns_none_when_no_index_paths(self, db_path: str) -> None:
        """_check_stale_documents returns None when index_paths is empty."""
        from mcp.mdq.server import _check_stale_documents  # noqa: PLC0415

        conn = sqlite3.connect(db_path)
        try:
            result = _check_stale_documents(conn, {})
        finally:
            conn.close()

        assert result is None

    def test_returns_none_when_path_nonexistent(self, db_path: str) -> None:
        """_check_stale_documents returns None when the index path does not exist."""
        from mcp.mdq.server import _check_stale_documents  # noqa: PLC0415

        conn = sqlite3.connect(db_path)
        try:
            result = _check_stale_documents(conn, {"index_paths": ["/no/such/path"]})
        finally:
            conn.close()

        assert result is None

    def test_mixed_fresh_and_stale(self, db_path: str, tmp_path: Path) -> None:
        """_check_stale_documents returns count of stale source paths only."""
        from mcp.mdq.server import _check_stale_documents  # noqa: PLC0415

        future_ns = int((time.time() + 86400) * 1_000_000_000)
        old_ns = int((time.time() - 86400) * 1_000_000_000)
        _insert_documents(
            db_path,
            [
                ("doc1", "/test/fresh.md", future_ns),
                ("doc2", "/test/stale.md", old_ns),
            ],
        )

        conn = sqlite3.connect(db_path)
        try:
            result = _check_stale_documents(conn, {"index_paths": [str(tmp_path)]})
        finally:
            conn.close()

        assert result == 1


class TestMdqHealthSchemaChecks:
    """Verify health() checks documents/chunks/chunks_fts/triggers schema."""

    def test_health_ok_with_full_schema(self, db_path: str) -> None:
        """health() returns ready=True when all tables and triggers are present."""
        from unittest.mock import patch  # noqa: PLC0415

        from fastapi.testclient import TestClient  # noqa: PLC0415
        from mcp.mdq.server import app  # noqa: PLC0415

        cfg = {"mdq_mcp_server": {"db_path": db_path, "index_paths": []}}
        with patch("shared.config_loader.ConfigLoader.load_all", return_value=cfg):
            client = TestClient(app, raise_server_exceptions=False)
            response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["ready"] is True
        assert data["status"] == "ok"

    def test_health_degraded_when_documents_table_missing(self, tmp_path: Path) -> None:
        """health() returns degraded with error message when documents table is absent."""
        from unittest.mock import patch  # noqa: PLC0415

        from fastapi.testclient import TestClient  # noqa: PLC0415
        from mcp.mdq.server import app  # noqa: PLC0415

        empty_db = str(tmp_path / "empty.sqlite")
        sqlite3.connect(empty_db).close()

        cfg = {"mdq_mcp_server": {"db_path": empty_db, "index_paths": []}}
        with patch("shared.config_loader.ConfigLoader.load_all", return_value=cfg):
            client = TestClient(app, raise_server_exceptions=False)
            response = client.get("/health")
        assert response.status_code == 503
        data = response.json()
        assert data["ready"] is False
        assert "db_schema" in data["dependencies"]
        assert "documents" in data["dependencies"]["db_schema"]

    def test_health_degraded_when_chunks_table_missing(self, tmp_path: Path) -> None:
        """health() returns degraded when chunks table is absent (documents exists)."""
        from unittest.mock import patch  # noqa: PLC0415

        from fastapi.testclient import TestClient  # noqa: PLC0415
        from mcp.mdq.server import app  # noqa: PLC0415

        partial_db = str(tmp_path / "partial.sqlite")
        conn = sqlite3.connect(partial_db)
        conn.execute(
            "CREATE TABLE documents (doc_id TEXT PRIMARY KEY, source_path TEXT, mtime_ns INTEGER)"
        )
        conn.commit()
        conn.close()

        cfg = {"mdq_mcp_server": {"db_path": partial_db, "index_paths": []}}
        with patch("shared.config_loader.ConfigLoader.load_all", return_value=cfg):
            client = TestClient(app, raise_server_exceptions=False)
            response = client.get("/health")
        assert response.status_code == 503
        data = response.json()
        assert data["ready"] is False
        assert "db_schema" in data["dependencies"]
        assert "chunks" in data["dependencies"]["db_schema"]

    def test_health_degraded_when_db_file_missing(self, tmp_path: Path) -> None:
        """health() returns degraded when db_file does not exist."""
        from unittest.mock import patch  # noqa: PLC0415

        from fastapi.testclient import TestClient  # noqa: PLC0415
        from mcp.mdq.server import app  # noqa: PLC0415

        cfg = {
            "mdq_mcp_server": {
                "db_path": str(tmp_path / "nonexistent.sqlite"),
                "index_paths": [],
            }
        }
        with patch("shared.config_loader.ConfigLoader.load_all", return_value=cfg):
            client = TestClient(app, raise_server_exceptions=False)
            response = client.get("/health")
        assert response.status_code == 503
        data = response.json()
        assert data["ready"] is False
        assert "db_file" in data["dependencies"]
