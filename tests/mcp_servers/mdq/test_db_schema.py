"""tests/mcp_servers/mdq/test_db_schema.py
Characterization tests for scripts/mcp_servers/mdq/db_schema.py.

Locks current behavior of create_production_tables() before refactoring:
- legacy schema detection/rebuild branch
- production table/FTS5/trigger creation
- error logging + re-raise on sqlite3.OperationalError
"""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path
from unittest.mock import patch

import pytest
from mcp_servers.mdq.db_schema import create_production_tables


def _table_names(conn: sqlite3.Connection) -> set[str]:
    rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    return {row[0] for row in rows}


def _trigger_names(conn: sqlite3.Connection) -> set[str]:
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='trigger'"
    ).fetchall()
    return {row[0] for row in rows}


class TestCreateProductionTablesFreshDb:
    """Behavior when creating tables on a brand-new database file."""

    def test_creates_expected_tables(self, tmp_path: Path) -> None:
        db_path = str(tmp_path / "fresh.sqlite")
        conn = sqlite3.connect(db_path)
        try:
            create_production_tables(conn, db_path, sqlite_busy_timeout=5000)
            names = _table_names(conn)
            assert {"documents", "chunks", "chunks_fts", "index_state"} <= names
        finally:
            conn.close()

    def test_creates_expected_triggers(self, tmp_path: Path) -> None:
        db_path = str(tmp_path / "fresh.sqlite")
        conn = sqlite3.connect(db_path)
        try:
            create_production_tables(conn, db_path, sqlite_busy_timeout=5000)
            names = _trigger_names(conn)
            assert {"chunks_ai", "chunks_ad", "chunks_au"} <= names
        finally:
            conn.close()

    def test_chunks_table_uses_chunk_id_primary_key(self, tmp_path: Path) -> None:
        db_path = str(tmp_path / "fresh.sqlite")
        conn = sqlite3.connect(db_path)
        try:
            create_production_tables(conn, db_path, sqlite_busy_timeout=5000)
            cols = conn.execute("PRAGMA table_info(chunks)").fetchall()
            pk_cols = [c[1] for c in cols if c[5] > 0]  # index 5 = pk rank
            assert pk_cols == ["chunk_id"]
        finally:
            conn.close()

    def test_creates_parent_directory_if_missing(self, tmp_path: Path) -> None:
        nested_path = str(tmp_path / "nested" / "dir" / "mdq.sqlite")
        conn = sqlite3.connect(":memory:")
        try:
            create_production_tables(conn, nested_path, sqlite_busy_timeout=5000)
            assert Path(nested_path).parent.is_dir()
        finally:
            conn.close()

    def test_is_idempotent_on_repeated_calls(self, tmp_path: Path) -> None:
        db_path = str(tmp_path / "fresh.sqlite")
        conn = sqlite3.connect(db_path)
        try:
            create_production_tables(conn, db_path, sqlite_busy_timeout=5000)
            create_production_tables(conn, db_path, sqlite_busy_timeout=5000)
            names = _table_names(conn)
            assert {"documents", "chunks", "chunks_fts", "index_state"} <= names
        finally:
            conn.close()


class TestLegacySchemaMigration:
    """Behavior when an old (id INTEGER PK + chunk_id TEXT UNIQUE) chunks table exists."""

    def _make_legacy_db(self, db_path: str) -> None:
        conn = sqlite3.connect(db_path)
        try:
            conn.execute(
                """
                CREATE TABLE chunks (
                    id INTEGER PRIMARY KEY,
                    chunk_id TEXT UNIQUE,
                    content TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE VIRTUAL TABLE chunks_fts USING fts5(content)
                """
            )
            conn.execute(
                """
                CREATE TRIGGER chunks_ai AFTER INSERT ON chunks
                BEGIN
                    INSERT INTO chunks_fts(rowid, content) VALUES (new.id, new.content);
                END
                """
            )
            conn.execute(
                """
                CREATE TRIGGER chunks_ad AFTER DELETE ON chunks
                BEGIN
                    DELETE FROM chunks_fts WHERE rowid = old.id;
                END
                """
            )
            conn.execute(
                """
                CREATE TRIGGER chunks_au AFTER UPDATE ON chunks
                BEGIN
                    DELETE FROM chunks_fts WHERE rowid = old.id;
                    INSERT INTO chunks_fts(rowid, content) VALUES (new.id, new.content);
                END
                """
            )
            conn.execute(
                "INSERT INTO chunks (chunk_id, content) VALUES ('c1', 'legacy content')"
            )
            conn.commit()
        finally:
            conn.close()

    def test_rebuilds_chunks_table_with_chunk_id_primary_key(
        self, tmp_path: Path
    ) -> None:
        db_path = str(tmp_path / "legacy.sqlite")
        self._make_legacy_db(db_path)
        conn = sqlite3.connect(db_path)
        try:
            create_production_tables(conn, db_path, sqlite_busy_timeout=5000)
            cols = conn.execute("PRAGMA table_info(chunks)").fetchall()
            col_names = [c[1] for c in cols]
            assert "id" not in col_names
            pk_cols = [c[1] for c in cols if c[5] > 0]
            assert pk_cols == ["chunk_id"]
        finally:
            conn.close()

    def test_legacy_data_is_dropped_on_rebuild(self, tmp_path: Path) -> None:
        db_path = str(tmp_path / "legacy.sqlite")
        self._make_legacy_db(db_path)
        conn = sqlite3.connect(db_path)
        try:
            create_production_tables(conn, db_path, sqlite_busy_timeout=5000)
            rows = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()
            assert rows[0] == 0
        finally:
            conn.close()

    def test_logs_info_message_on_legacy_schema_detection(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        db_path = str(tmp_path / "legacy.sqlite")
        self._make_legacy_db(db_path)
        conn = sqlite3.connect(db_path)
        try:
            with caplog.at_level(logging.INFO, logger="mcp_servers.mdq.db_schema"):
                create_production_tables(conn, db_path, sqlite_busy_timeout=5000)
            assert any(
                "old chunks schema" in record.message.lower()
                for record in caplog.records
            )
        finally:
            conn.close()

    def test_new_schema_is_not_treated_as_legacy(self, tmp_path: Path) -> None:
        """A chunks table already using chunk_id PRIMARY KEY must not trigger migration."""
        db_path = str(tmp_path / "already_new.sqlite")
        conn = sqlite3.connect(db_path)
        try:
            create_production_tables(conn, db_path, sqlite_busy_timeout=5000)
            conn.execute(
                "INSERT INTO documents (doc_id, source_path, mtime_ns, size_bytes, "
                "content_hash, indexed_at) VALUES ('d1', '/p', 1, 1, 'h', 1.0)"
            )
            conn.execute(
                "INSERT INTO chunks (chunk_id, doc_id, source_path, heading, "
                "start_line, end_line, content, content_hash, indexed_at) VALUES "
                "('c1', 'd1', '/p', 'h', 1, 2, 'body', 'h', 1.0)"
            )
            conn.commit()

            # Re-run against the same (already new-schema) database.
            create_production_tables(conn, db_path, sqlite_busy_timeout=5000)

            rows = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()
            assert rows[0] == 1  # data survives — no rebuild triggered
        finally:
            conn.close()


class TestErrorHandling:
    """Behavior when a sqlite3.OperationalError occurs during table creation."""

    def test_operational_error_is_logged_and_reraised(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        db_path = str(tmp_path / "broken.sqlite")
        conn = sqlite3.connect(db_path)
        try:
            with (
                patch(
                    "mcp_servers.mdq.db_schema.apply_connection_pragmas",
                    side_effect=sqlite3.OperationalError("disk I/O error"),
                ),
                caplog.at_level(logging.ERROR, logger="mcp_servers.mdq.db_schema"),
                pytest.raises(sqlite3.OperationalError, match="disk I/O error"),
            ):
                create_production_tables(conn, db_path, sqlite_busy_timeout=5000)

            assert any(
                "Failed to create production tables" in record.message
                for record in caplog.records
            )
        finally:
            conn.close()

    def test_non_operational_error_propagates_without_the_error_log(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Only sqlite3.OperationalError is caught; other exceptions pass through untouched."""
        db_path = str(tmp_path / "broken2.sqlite")
        conn = sqlite3.connect(db_path)
        try:
            with (
                patch(
                    "mcp_servers.mdq.db_schema.apply_connection_pragmas",
                    side_effect=ValueError("unexpected"),
                ),
                caplog.at_level(logging.ERROR, logger="mcp_servers.mdq.db_schema"),
                pytest.raises(ValueError, match="unexpected"),
            ):
                create_production_tables(conn, db_path, sqlite_busy_timeout=5000)

            assert not any(
                "Failed to create production tables" in record.message
                for record in caplog.records
            )
        finally:
            conn.close()
