"""tests/test_create_schema.py
Unit tests for create_schema: create_rag_schema, create_session_schema, idempotency.

vec0 virtual tables (chunks_vec, memories_vec) require the sqlite-vec extension.
Those DDL statements are excluded by patching build_*_schema_sql so the tests
run without the extension installed.
Migration code has been removed from create_schema.py; no migration tests here.
"""

import logging
import sqlite3
from pathlib import Path
from unittest.mock import patch

import db.create_schema as cs
import pytest
from db.config import DbConfig
from db.helper import SQLiteHelper

# RAG schema without the vec0 virtual table (chunks_vec requires sqlite-vec).
_RAG_SCHEMA_NO_VEC0 = """
    CREATE TABLE IF NOT EXISTS documents (
        doc_id        INTEGER PRIMARY KEY AUTOINCREMENT,
        url           TEXT    NOT NULL UNIQUE,
        title         TEXT,
        lang          TEXT    NOT NULL CHECK (lang IN ('ja', 'en')),
        fetched_at    TEXT    NOT NULL DEFAULT (datetime('now')),
        etag          TEXT,
        last_modified TEXT
    );
    CREATE TABLE IF NOT EXISTS chunks (
        chunk_id           INTEGER PRIMARY KEY AUTOINCREMENT,
        doc_id             INTEGER NOT NULL
                               REFERENCES documents(doc_id) ON DELETE CASCADE,
        chunk_index        INTEGER NOT NULL,
        content            TEXT    NOT NULL,
        normalized_content TEXT
    );
    CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
        content,
        content       = 'chunks',
        content_rowid = 'chunk_id',
        tokenize      = 'unicode61'
    );
"""

# Session schema without the vec0 virtual tables (memories_vec requires sqlite-vec).
_SESSION_SCHEMA_NO_VEC0 = """
    CREATE TABLE IF NOT EXISTS sessions (
        session_id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT    NOT NULL DEFAULT (datetime('now')),
        title      TEXT
    );
    CREATE TABLE IF NOT EXISTS messages (
        message_id  INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id  INTEGER NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
        role        TEXT    NOT NULL,
        content     TEXT    NOT NULL,
        tool_calls  TEXT,
        tool_call_id TEXT,
        created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS notes (
        note_id    INTEGER PRIMARY KEY AUTOINCREMENT,
        content    TEXT    NOT NULL,
        created_at TEXT    NOT NULL DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS tool_results (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER,
        turn       INTEGER NOT NULL,
        tool_name  TEXT    NOT NULL,
        args_masked  TEXT,
        full_text  TEXT    NOT NULL,
        summary    TEXT,
        is_error   INTEGER NOT NULL DEFAULT 0,
        created_at TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
    );
    CREATE INDEX IF NOT EXISTS idx_tool_results_session
        ON tool_results(session_id);
    CREATE TABLE IF NOT EXISTS memories (
        memory_id   TEXT PRIMARY KEY,
        memory_type TEXT NOT NULL CHECK(memory_type IN ('semantic','episodic')),
        source_type TEXT NOT NULL DEFAULT 'conversation',
        session_id  INTEGER,
        turn_id     TEXT,
        project     TEXT NOT NULL DEFAULT '',
        repo        TEXT NOT NULL DEFAULT '',
        branch      TEXT NOT NULL DEFAULT '',
        content     TEXT NOT NULL,
        summary     TEXT NOT NULL DEFAULT '',
        tags        TEXT NOT NULL DEFAULT '[]',
        importance  REAL NOT NULL DEFAULT 0.5,
        pinned      INTEGER NOT NULL DEFAULT 0,
        created_at  TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
    );
    CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
        memory_id UNINDEXED,
        content,
        summary,
        tags
    );
    CREATE TABLE IF NOT EXISTS memory_links (
        src_id  TEXT NOT NULL REFERENCES memories(memory_id) ON DELETE CASCADE,
        dst_id  TEXT NOT NULL REFERENCES memories(memory_id) ON DELETE CASCADE,
        PRIMARY KEY (src_id, dst_id)
    );
"""


def _table_names(conn: sqlite3.Connection) -> set[str]:
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    return {row[0] for row in rows}


def _make_db_config(db_file: Path, target: str) -> DbConfig:
    if target == "rag":
        return DbConfig(
            rag_db_path=str(db_file),
            session_db_path="/tmp/session.sqlite",
        )
    return DbConfig(
        rag_db_path="/tmp/rag.sqlite",
        session_db_path=str(db_file),
    )


@pytest.fixture
def rag_tmp_db(tmp_path: Path) -> sqlite3.Connection:
    """Open a temp rag.sqlite via SQLiteHelper with vec0 skipped."""
    db_file = tmp_path / "rag.sqlite"
    cfg = _make_db_config(db_file, "rag")
    with (
        patch("db.helper.build_db_config", return_value=cfg),
        patch("db.store_protocols.build_db_config", return_value=cfg),
        patch("db.create_schema.build_rag_schema_sql", return_value=_RAG_SCHEMA_NO_VEC0),
        patch.object(SQLiteHelper, "_load_vec_extension", return_value=None),
        patch.object(
            cs, "_get_logger", return_value=logging.getLogger("test.create_schema")
        ),
    ):
        cs.create_rag_schema()
    return sqlite3.connect(str(db_file))


@pytest.fixture
def session_tmp_db(tmp_path: Path) -> sqlite3.Connection:
    """Open a temp session.sqlite via SQLiteHelper with vec0 skipped."""
    db_file = tmp_path / "session.sqlite"
    cfg = _make_db_config(db_file, "session")
    with (
        patch("db.helper.build_db_config", return_value=cfg),
        patch("db.store_protocols.build_db_config", return_value=cfg),
        patch(
            "db.create_schema.build_session_schema_sql", return_value=_SESSION_SCHEMA_NO_VEC0
        ),
        patch.object(SQLiteHelper, "_load_vec_extension", return_value=None),
        patch.object(
            cs, "_get_logger", return_value=logging.getLogger("test.create_schema")
        ),
    ):
        cs.create_session_schema()
    return sqlite3.connect(str(db_file))


class TestCreateRagSchema:
    def test_creates_documents_table(self, rag_tmp_db: sqlite3.Connection) -> None:
        assert "documents" in _table_names(rag_tmp_db)

    def test_creates_chunks_table(self, rag_tmp_db: sqlite3.Connection) -> None:
        assert "chunks" in _table_names(rag_tmp_db)

    def test_creates_chunks_fts_table(self, rag_tmp_db: sqlite3.Connection) -> None:
        assert "chunks_fts" in _table_names(rag_tmp_db)

    def test_no_schema_version_table(self, rag_tmp_db: sqlite3.Connection) -> None:
        assert "schema_version" not in _table_names(rag_tmp_db)

    def test_documents_columns(self, rag_tmp_db: sqlite3.Connection) -> None:
        cols = {row[1] for row in rag_tmp_db.execute("PRAGMA table_info(documents)")}
        assert {"doc_id", "url", "title", "lang", "etag", "last_modified"} <= cols

    def test_chunks_columns(self, rag_tmp_db: sqlite3.Connection) -> None:
        cols = {row[1] for row in rag_tmp_db.execute("PRAGMA table_info(chunks)")}
        assert {
            "chunk_id",
            "doc_id",
            "chunk_index",
            "content",
            "normalized_content",
        } <= cols

    def test_idempotent(self, tmp_path: Path) -> None:
        db_file = tmp_path / "rag2.sqlite"
        cfg = _make_db_config(db_file, "rag")
        with (
            patch("db.helper.build_db_config", return_value=cfg),
            patch("db.store_protocols.build_db_config", return_value=cfg),
            patch("db.create_schema.build_rag_schema_sql", return_value=_RAG_SCHEMA_NO_VEC0),
            patch.object(SQLiteHelper, "_load_vec_extension", return_value=None),
            patch.object(
                cs, "_get_logger", return_value=logging.getLogger("test.create_schema")
            ),
        ):
            cs.create_rag_schema()
            cs.create_rag_schema()  # must not raise


class TestCreateSessionSchema:
    def test_creates_sessions_table(self, session_tmp_db: sqlite3.Connection) -> None:
        assert "sessions" in _table_names(session_tmp_db)

    def test_creates_messages_table(self, session_tmp_db: sqlite3.Connection) -> None:
        assert "messages" in _table_names(session_tmp_db)

    def test_creates_notes_table(self, session_tmp_db: sqlite3.Connection) -> None:
        assert "notes" in _table_names(session_tmp_db)

    def test_creates_tool_results_table(
        self, session_tmp_db: sqlite3.Connection
    ) -> None:
        assert "tool_results" in _table_names(session_tmp_db)

    def test_no_schema_version_table(self, session_tmp_db: sqlite3.Connection) -> None:
        assert "schema_version" not in _table_names(session_tmp_db)

    def test_session_schema_no_legacy_memory_tables(
        self, session_tmp_db: sqlite3.Connection
    ) -> None:
        tables = _table_names(session_tmp_db)
        assert "memory_entries" not in tables
        assert "memory_vec" not in tables

    def test_session_schema_has_new_memory_tables(
        self, session_tmp_db: sqlite3.Connection
    ) -> None:
        tables = _table_names(session_tmp_db)
        assert "memories" in tables
        assert "memory_links" in tables

    def test_messages_has_tool_call_id(
        self, session_tmp_db: sqlite3.Connection
    ) -> None:
        cols = {row[1] for row in session_tmp_db.execute("PRAGMA table_info(messages)")}
        assert "tool_call_id" in cols

    def test_idempotent(self, tmp_path: Path) -> None:
        db_file = tmp_path / "session2.sqlite"
        cfg = _make_db_config(db_file, "session")
        with (
            patch("db.helper.build_db_config", return_value=cfg),
            patch("db.store_protocols.build_db_config", return_value=cfg),
            patch(
                "db.create_schema.build_session_schema_sql", return_value=_SESSION_SCHEMA_NO_VEC0
            ),
            patch.object(SQLiteHelper, "_load_vec_extension", return_value=None),
            patch.object(
                cs, "_get_logger", return_value=logging.getLogger("test.create_schema")
            ),
        ):
            cs.create_session_schema()
            cs.create_session_schema()  # must not raise
