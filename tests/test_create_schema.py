"""tests/test_create_schema.py
Unit tests for create_schema: create_rag_schema, create_session_schema, idempotency.

vec0 virtual tables (chunks_vec, memories_vec) require the sqlite-vec extension.
Those DDL statements are excluded by patching build_*_schema_sql so the tests
run without the extension installed.

create_schema.py contains _migrate_rag_schema() and _migrate_session_schema() for
backward-compatible schema additions; these migration helpers are tested indirectly
via idempotency tests (running create_*_schema twice must not raise).
"""

import sqlite3
from collections.abc import Generator
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
def rag_tmp_db(tmp_path: Path) -> Generator[sqlite3.Connection]:
    """Open a temp rag.sqlite via SQLiteHelper with vec0 skipped."""
    db_file = tmp_path / "rag.sqlite"
    cfg = _make_db_config(db_file, "rag")
    with (
        patch("db.helper.build_db_config", return_value=cfg),
        patch("db.store_protocols.build_db_config", return_value=cfg),
        patch(
            "db.create_schema.build_rag_schema_sql", return_value=_RAG_SCHEMA_NO_VEC0
        ),
        patch.object(SQLiteHelper, "_load_vec_extension", return_value=None),
    ):
        cs.create_rag_schema()
    conn = sqlite3.connect(str(db_file))
    yield conn
    conn.close()


@pytest.fixture
def session_tmp_db(tmp_path: Path) -> Generator[sqlite3.Connection]:
    """Open a temp session.sqlite via SQLiteHelper with vec0 skipped."""
    db_file = tmp_path / "session.sqlite"
    cfg = _make_db_config(db_file, "session")
    with (
        patch("db.helper.build_db_config", return_value=cfg),
        patch("db.store_protocols.build_db_config", return_value=cfg),
        patch(
            "db.create_schema.build_session_schema_sql",
            return_value=_SESSION_SCHEMA_NO_VEC0,
        ),
        patch.object(SQLiteHelper, "_load_vec_extension", return_value=None),
    ):
        cs.create_session_schema()
    conn = sqlite3.connect(str(db_file))
    yield conn
    conn.close()


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
            patch(
                "db.create_schema.build_rag_schema_sql",
                return_value=_RAG_SCHEMA_NO_VEC0,
            ),
            patch.object(SQLiteHelper, "_load_vec_extension", return_value=None),
        ):
            cs.create_rag_schema()
            cs.create_rag_schema()  # must not raise

    def test_no_session_tables_in_rag_db(self, rag_tmp_db: sqlite3.Connection) -> None:
        """RAG schema must not create Agent session tables — RAG and session schemas are independent."""
        table_names = _table_names(rag_tmp_db)
        assert "sessions" not in table_names
        assert "messages" not in table_names
        assert "tool_results" not in table_names
        assert "workflow_tasks" not in table_names


class TestCreateSessionSchema:
    def test_creates_sessions_table(self, session_tmp_db: sqlite3.Connection) -> None:
        assert "sessions" in _table_names(session_tmp_db)

    def test_creates_messages_table(self, session_tmp_db: sqlite3.Connection) -> None:
        assert "messages" in _table_names(session_tmp_db)

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
                "db.create_schema.build_session_schema_sql",
                return_value=_SESSION_SCHEMA_NO_VEC0,
            ),
            patch.object(SQLiteHelper, "_load_vec_extension", return_value=None),
        ):
            cs.create_session_schema()
            cs.create_session_schema()  # must not raise


# Workflow schema without the vec0 virtual table (chunks_vec requires sqlite-vec).
_WORKFLOW_SCHEMA_NO_VEC0 = """
    PRAGMA journal_mode=WAL;
    PRAGMA foreign_keys=ON;

    CREATE TABLE IF NOT EXISTS tasks (
        task_id          TEXT PRIMARY KEY,
        session_id       TEXT,
        workflow_id      TEXT,
        turn_number      INTEGER,
        workflow_version TEXT NOT NULL,
        status           TEXT NOT NULL DEFAULT 'pending',
        idempotency_key  TEXT UNIQUE NOT NULL,
        created_at       TEXT NOT NULL,
        updated_at       TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS attempts (
        attempt_id  TEXT PRIMARY KEY,
        task_id     TEXT NOT NULL REFERENCES tasks(task_id) ON DELETE CASCADE,
        stage_id    TEXT NOT NULL,
        status      TEXT NOT NULL DEFAULT 'running',
        started_at  TEXT NOT NULL,
        ended_at    TEXT,
        error_msg   TEXT
    );

    CREATE TABLE IF NOT EXISTS processed_events (
        event_id    TEXT PRIMARY KEY,
        task_id     TEXT NOT NULL REFERENCES tasks(task_id) ON DELETE CASCADE,
        stage_id    TEXT NOT NULL,
        recorded_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS artifacts (
        artifact_id TEXT PRIMARY KEY,
        task_id     TEXT NOT NULL REFERENCES tasks(task_id) ON DELETE CASCADE,
        stage_id    TEXT NOT NULL,
        uri         TEXT NOT NULL,
        created_at  TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS approvals (
        approval_id TEXT PRIMARY KEY,
        task_id     TEXT NOT NULL REFERENCES tasks(task_id) ON DELETE CASCADE,
        stage_id    TEXT,
        status      TEXT NOT NULL DEFAULT 'pending',
        reason      TEXT,
        created_at  TEXT NOT NULL,
        resolved_at TEXT
    );
"""


class TestCreateWorkflowSchema:
    def test_creates_all_tables(self, tmp_path: Path) -> None:
        db_file = tmp_path / "workflow.sqlite"
        cfg = DbConfig(
            rag_db_path="/tmp/rag.sqlite",
            session_db_path="/tmp/session.sqlite",
            workflow_db_path=str(db_file),
        )
        with (
            patch("db.helper.build_db_config", return_value=cfg),
            patch("db.store_protocols.build_db_config", return_value=cfg),
            patch(
                "db.create_schema.build_workflow_schema_sql",
                return_value=_WORKFLOW_SCHEMA_NO_VEC0,
            ),
        ):
            cs.create_workflow_schema()
        conn = sqlite3.connect(str(db_file))
        tables = _table_names(conn)
        conn.close()
        assert {
            "tasks",
            "attempts",
            "processed_events",
            "artifacts",
            "approvals",
        } <= tables

    def test_creates_all_tables_via_workflow_schema_init(self, tmp_path: Path) -> None:
        """workflow_schema.init_schema() creates the same tables as create_workflow_schema()."""
        import db.workflow_schema as ws

        db_file = tmp_path / "workflow2.sqlite"
        cfg = DbConfig(
            rag_db_path="/tmp/rag.sqlite",
            session_db_path="/tmp/session.sqlite",
            workflow_db_path=str(db_file),
        )
        with (
            patch("db.helper.build_db_config", return_value=cfg),
            patch("db.store_protocols.build_db_config", return_value=cfg),
            patch(
                "db.workflow_schema.build_workflow_schema_sql",
                return_value=_WORKFLOW_SCHEMA_NO_VEC0,
            ),
        ):
            ws.init_schema()
        conn = sqlite3.connect(str(db_file))
        tables = _table_names(conn)
        conn.close()
        assert {
            "tasks",
            "attempts",
            "processed_events",
            "artifacts",
            "approvals",
        } <= tables

    def test_both_paths_create_same_tables(self, tmp_path: Path) -> None:
        """Both workflow initialization paths produce the same set of tables."""
        import db.workflow_schema as ws

        db_file1 = tmp_path / "workflow_a.sqlite"
        db_file2 = tmp_path / "workflow_b.sqlite"
        cfg = DbConfig(
            rag_db_path="/tmp/rag.sqlite",
            session_db_path="/tmp/session.sqlite",
            workflow_db_path=str(db_file1),
        )
        with (
            patch("db.helper.build_db_config", return_value=cfg),
            patch("db.store_protocols.build_db_config", return_value=cfg),
            patch(
                "db.create_schema.build_workflow_schema_sql",
                return_value=_WORKFLOW_SCHEMA_NO_VEC0,
            ),
        ):
            cs.create_workflow_schema()
        cfg2 = DbConfig(
            rag_db_path="/tmp/rag.sqlite",
            session_db_path="/tmp/session.sqlite",
            workflow_db_path=str(db_file2),
        )
        with (
            patch("db.helper.build_db_config", return_value=cfg2),
            patch("db.store_protocols.build_db_config", return_value=cfg2),
            patch(
                "db.workflow_schema.build_workflow_schema_sql",
                return_value=_WORKFLOW_SCHEMA_NO_VEC0,
            ),
        ):
            ws.init_schema()
        conn1 = sqlite3.connect(str(db_file1))
        tables1 = _table_names(conn1)
        conn1.close()
        conn2 = sqlite3.connect(str(db_file2))
        tables2 = _table_names(conn2)
        conn2.close()
        assert tables1 == tables2

    def test_idempotent(self, tmp_path: Path) -> None:
        db_file = tmp_path / "workflow2.sqlite"
        cfg = DbConfig(
            rag_db_path="/tmp/rag.sqlite",
            session_db_path="/tmp/session.sqlite",
            workflow_db_path=str(db_file),
        )
        with (
            patch("db.helper.build_db_config", return_value=cfg),
            patch("db.store_protocols.build_db_config", return_value=cfg),
            patch(
                "db.create_schema.build_workflow_schema_sql",
                return_value=_WORKFLOW_SCHEMA_NO_VEC0,
            ),
        ):
            cs.create_workflow_schema()
            cs.create_workflow_schema()  # must not raise

    def test_tasks_idempotency_key_unique(self, tmp_path: Path) -> None:
        db_file = tmp_path / "workflow3.sqlite"
        cfg = DbConfig(
            rag_db_path="/tmp/rag.sqlite",
            session_db_path="/tmp/session.sqlite",
            workflow_db_path=str(db_file),
        )
        with (
            patch("db.helper.build_db_config", return_value=cfg),
            patch("db.store_protocols.build_db_config", return_value=cfg),
            patch(
                "db.create_schema.build_workflow_schema_sql",
                return_value=_WORKFLOW_SCHEMA_NO_VEC0,
            ),
        ):
            cs.create_workflow_schema()
        conn = sqlite3.connect(str(db_file))
        now = "2026-01-01T00:00:00+00:00"
        conn.execute(
            "INSERT INTO tasks VALUES (?,?,?,?,?,?,?,?,?)",
            ("t1", "s1", None, 1, "1.0.0", "pending", "s1:1", now, now),
        )
        conn.commit()
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO tasks VALUES (?,?,?,?,?,?,?,?,?)",
                ("t2", "s1", None, 1, "1.0.0", "pending", "s1:1", now, now),
            )
            conn.commit()
        conn.close()

    def test_attempts_foreign_key_cascade(self, tmp_path: Path) -> None:
        db_file = tmp_path / "workflow4.sqlite"
        cfg = DbConfig(
            rag_db_path="/tmp/rag.sqlite",
            session_db_path="/tmp/session.sqlite",
            workflow_db_path=str(db_file),
        )
        with (
            patch("db.helper.build_db_config", return_value=cfg),
            patch("db.store_protocols.build_db_config", return_value=cfg),
            patch(
                "db.create_schema.build_workflow_schema_sql",
                return_value=_WORKFLOW_SCHEMA_NO_VEC0,
            ),
        ):
            cs.create_workflow_schema()
        conn = sqlite3.connect(str(db_file))
        conn.execute("PRAGMA foreign_keys=ON")
        now = "2026-01-01T00:00:00+00:00"
        conn.execute(
            "INSERT INTO tasks VALUES (?,?,?,?,?,?,?,?,?)",
            ("t1", "s1", None, 1, "1.0.0", "pending", "s1:1", now, now),
        )
        conn.execute(
            "INSERT INTO attempts VALUES (?,?,?,?,?,?,?)",
            ("a1", "t1", "plan", "running", now, None, None),
        )
        conn.commit()
        conn.execute("DELETE FROM tasks WHERE task_id='t1'")
        conn.commit()
        rows = conn.execute("SELECT * FROM attempts WHERE attempt_id='a1'").fetchall()
        assert rows == []
        conn.close()
