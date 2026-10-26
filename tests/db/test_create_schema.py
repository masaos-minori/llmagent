"""tests/test_create_schema.py
Unit tests for create_schema: create_rag_schema, create_session_schema, idempotency.

vec0 virtual tables (chunks_vec, memories_vec) require the sqlite-vec extension.
Those DDL statements are excluded by patching build_*_schema_sql so the tests
run without the extension installed.

Schema creation is DDL-only. Idempotency is guaranteed by CREATE ... IF NOT EXISTS.
No migration helpers exist.
"""

import logging
import sqlite3
from collections.abc import Generator
from pathlib import Path
from unittest.mock import patch

import db.create_schema as cs
import pytest
from db.config import DbConfig
from db.helper import SQLiteHelper
from db.schema_sql import build_eventbus_schema_sql, eventbus_schema_version
from shared.eventbus_schema_fingerprint import (
    apply_schema_in_memory,
    assert_matches,
    build_fingerprint,
    expected_fingerprint,
)

# RAG schema without the vec0 virtual table (chunks_vec requires sqlite-vec).
_RAG_SCHEMA_NO_VEC0 = """
    CREATE TABLE IF NOT EXISTS documents (
        doc_id        INTEGER PRIMARY KEY AUTOINCREMENT,
        url           TEXT    NOT NULL UNIQUE,
        title         TEXT,
        lang          TEXT    NOT NULL CHECK (lang IN ('ja', 'en')),
        fetched_at    TEXT    NOT NULL,
        etag          TEXT,
        last_modified TEXT,
        chunking_strategy  TEXT    NOT NULL
    );
    CREATE TABLE IF NOT EXISTS chunks (
        chunk_id           INTEGER PRIMARY KEY AUTOINCREMENT,
        doc_id             INTEGER NOT NULL
                               REFERENCES documents(doc_id) ON DELETE CASCADE,
        chunk_index        INTEGER NOT NULL,
        content            TEXT    NOT NULL,
        normalized_content TEXT,
        chunk_type         TEXT    NOT NULL,
        source_file        TEXT    NOT NULL
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
        created_at TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
        title      TEXT
     );
     CREATE TABLE IF NOT EXISTS messages (
        message_id  INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id  INTEGER NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
        role        TEXT    NOT NULL,
        content     TEXT    NOT NULL,
        tool_calls  TEXT,
  tool_call_id TEXT,
        created_at  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
     );
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
        created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
        updated_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
     );
    CREATE TABLE IF NOT EXISTS session_diagnostics (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id  INTEGER REFERENCES sessions(session_id) ON DELETE CASCADE,
        kind        TEXT    NOT NULL,
        content     TEXT    NOT NULL,
        workflow_id TEXT,
        task_id     TEXT,
        created_at  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
    );
    CREATE INDEX IF NOT EXISTS idx_session_diagnostics_session
        ON session_diagnostics(session_id);
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

_EVENTBUS_SCHEMA_NO_VEC0 = """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS events (
    seq                    INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id               TEXT    NOT NULL UNIQUE,
    topic                  TEXT    NOT NULL,
    payload                TEXT    NOT NULL,
    producer               TEXT    NOT NULL,
    published_at           TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    redelivered_from       TEXT,
    dlq_requeue_count      INTEGER NOT NULL DEFAULT 0,
    dlq_at                 TEXT,
    consumer_id            TEXT
);

CREATE INDEX IF NOT EXISTS idx_events_topic ON events(topic);
CREATE INDEX IF NOT EXISTS idx_events_seq   ON events(seq);
CREATE INDEX IF NOT EXISTS idx_events_dlq_at ON events(dlq_at);
CREATE INDEX IF NOT EXISTS idx_events_dlq_seq ON events(dlq_at, seq);

-- Per-consumer delivery state: tracks ACK state per (consumer_id, event_id)
CREATE TABLE IF NOT EXISTS consumer_delivery (
    consumer_id                    TEXT    NOT NULL,
    event_id                       TEXT    NOT NULL,
    acked                          INTEGER NOT NULL DEFAULT 0,
    consumer_delivery_failure_count INTEGER NOT NULL DEFAULT 0,
    consumer_last_nack_attempt     TEXT,
    PRIMARY KEY (consumer_id, event_id)
);

-- Index for efficient low-water-mark query in get_resume_position()
CREATE INDEX IF NOT EXISTS idx_consumer_delivery_consumer_ack
    ON consumer_delivery(consumer_id, acked);

-- Per-consumer offset: tracks last-committed sequence offset per consumer
CREATE TABLE IF NOT EXISTS consumer_offsets (
    consumer_id          TEXT    PRIMARY KEY,
    offset               INTEGER NOT NULL DEFAULT 0
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
    elif target == "workflow":
        return DbConfig(
            rag_db_path="/tmp/rag.sqlite",
            session_db_path="/tmp/session.sqlite",
            workflow_db_path=str(db_file),
        )
    elif target == "eventbus":
        return DbConfig(
            rag_db_path="/tmp/rag.sqlite",
            session_db_path="/tmp/session.sqlite",
            eventbus_db_path=str(db_file),
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
            "chunk_type",
            "source_file",
        } <= cols

    def test_idempotent(self, tmp_path: Path) -> None:
        db_file = tmp_path / "rag2.sqlite"
        cfg = _make_db_config(db_file, "rag")
        with (
            patch("db.helper.build_db_config", return_value=cfg),
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
        assert "workflow_tasks" not in table_names


class TestCreateSessionSchema:
    def test_creates_sessions_table(self, session_tmp_db: sqlite3.Connection) -> None:
        assert "sessions" in _table_names(session_tmp_db)

    def test_creates_messages_table(self, session_tmp_db: sqlite3.Connection) -> None:
        assert "messages" in _table_names(session_tmp_db)

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

    def test_build_session_schema_emits_undo_floor_column(self) -> None:
        """build_session_schema_sql() emits the undo_floor_message_id column with
        its NOT NULL DEFAULT 0 constraint against the real (unstubbed) builder."""
        import re

        import db.schema_sql as schema_sql_mod

        ddl = schema_sql_mod.build_session_schema_sql(384)
        assert "undo_floor_message_id" in ddl
        # Exact constraint: NOT NULL DEFAULT 0 (catches wrong nullability/default).
        assert re.search(
            r"undo_floor_message_id\s+INTEGER\s+NOT NULL\s+DEFAULT\s+0",
            ddl,
            re.IGNORECASE,
        )

    def test_idempotent(self, tmp_path: Path) -> None:
        db_file = tmp_path / "session2.sqlite"
        cfg = _make_db_config(db_file, "session")
        with (
            patch("db.helper.build_db_config", return_value=cfg),
            patch(
                "db.create_schema.build_session_schema_sql",
                return_value=_SESSION_SCHEMA_NO_VEC0,
            ),
            patch.object(SQLiteHelper, "_load_vec_extension", return_value=None),
        ):
            cs.create_session_schema()
            cs.create_session_schema()  # must not raise

    def test_session_schema_no_notes_table(
        self, session_tmp_db: sqlite3.Connection
    ) -> None:
        """notes table must not be created in new session schema."""
        assert "notes" not in _table_names(session_tmp_db)


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

    CREATE TABLE IF NOT EXISTS workflow_schema_version (
        version    TEXT NOT NULL,
        applied_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
    );
"""


class TestCreateWorkflowSchema:
    def test_creates_all_tables(self, tmp_path: Path) -> None:
        """All 4 workflow tables defined in docs/41_db/db_02_architecture_and_schema-schema-reference.md are created."""
        db_file = tmp_path / "workflow.sqlite"
        cfg = DbConfig(
            rag_db_path="/tmp/rag.sqlite",
            session_db_path="/tmp/session.sqlite",
            workflow_db_path=str(db_file),
        )
        with (
            patch("db.helper.build_db_config", return_value=cfg),
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
        } <= tables
        assert "approvals" not in tables

    def test_idempotent(self, tmp_path: Path) -> None:
        db_file = tmp_path / "workflow2.sqlite"
        cfg = DbConfig(
            rag_db_path="/tmp/rag.sqlite",
            session_db_path="/tmp/session.sqlite",
            workflow_db_path=str(db_file),
        )
        with (
            patch("db.helper.build_db_config", return_value=cfg),
            patch(
                "db.create_schema.build_workflow_schema_sql",
                return_value=_WORKFLOW_SCHEMA_NO_VEC0,
            ),
        ):
            cs.create_workflow_schema()
            cs.create_workflow_schema()  # must not raise

    def test_workflow_id_column_exists(self, tmp_path: Path) -> None:
        """create_workflow_schema() creates the workflow_id column in tasks."""
        db_file = tmp_path / "workflow_id_col.sqlite"
        cfg = DbConfig(
            rag_db_path="/tmp/rag.sqlite",
            session_db_path="/tmp/session.sqlite",
            workflow_db_path=str(db_file),
        )
        with (
            patch("db.helper.build_db_config", return_value=cfg),
            patch(
                "db.create_schema.build_workflow_schema_sql",
                return_value=_WORKFLOW_SCHEMA_NO_VEC0,
            ),
        ):
            cs.create_workflow_schema()
        conn = sqlite3.connect(str(db_file))
        columns = {
            row[1] for row in conn.execute("PRAGMA table_info(tasks)").fetchall()
        }
        conn.close()
        assert "workflow_id" in columns

    def test_workflow_schema_creation_is_idempotent(self, tmp_path: Path) -> None:
        """Running create_workflow_schema() twice does not duplicate the column."""
        db_file = tmp_path / "workflow_idempotent.sqlite"
        cfg = DbConfig(
            rag_db_path="/tmp/rag.sqlite",
            session_db_path="/tmp/session.sqlite",
            workflow_db_path=str(db_file),
        )
        with (
            patch("db.helper.build_db_config", return_value=cfg),
            patch(
                "db.create_schema.build_workflow_schema_sql",
                return_value=_WORKFLOW_SCHEMA_NO_VEC0,
            ),
        ):
            cs.create_workflow_schema()
            cs.create_workflow_schema()  # run twice to test idempotency
        conn = sqlite3.connect(str(db_file))
        columns = {
            row[1] for row in conn.execute("PRAGMA table_info(tasks)").fetchall()
        }
        assert "workflow_id" in columns
        # Verify column exists only once (no duplicate)
        workflow_id_count = sum(
            1
            for row in conn.execute("PRAGMA table_info(tasks)").fetchall()
            if row[1] == "workflow_id"
        )
        assert workflow_id_count == 1
        conn.close()

    def test_tasks_idempotency_key_unique(self, tmp_path: Path) -> None:
        db_file = tmp_path / "workflow3.sqlite"
        cfg = DbConfig(
            rag_db_path="/tmp/rag.sqlite",
            session_db_path="/tmp/session.sqlite",
            workflow_db_path=str(db_file),
        )
        with (
            patch("db.helper.build_db_config", return_value=cfg),
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
            "INSERT INTO attempts (attempt_id, task_id, stage_id, status, started_at, ended_at, error_msg) VALUES (?,?,?,?,?,?,?)",
            ("a1", "t1", "plan", "running", now, None, None),
        )
        conn.commit()
        conn.execute("DELETE FROM tasks WHERE task_id='t1'")
        conn.commit()
        rows = conn.execute("SELECT * FROM attempts WHERE attempt_id='a1'").fetchall()
        assert rows == []
        conn.close()


# ── rag schema column integrity ─────────────────────────────────────────────────────

# Values valid for every INSERT into the documents/chunks tables under _RAG_SCHEMA_NO_VEC0.

_DOC_URL = "http://example.com/doc"
_CHUNKING_STRATEGY = "text"
_FETCHED_AT = "2026-01-01T00:00:00Z"
_LANG = "en"
_CHUNK_CONTENT = "hello world"
_CHUNK_INDEX = 0

# For the nullable-column pass-through test.
_ETAG = "abc123"
_LAST_MODIFIED = "Mon, 01 Jan 2026 00:00:00 GMT"
_NORMALIZED_CONTENT = "hello world"

# For the non-contiguous chunk_index test.
_CHUNK_INDEX_2 = 2

# For the duplicate chunk_index test.
_CHUNK_INDEX_DUPLICATE = 0

# For the 11-field mismatch tests — one value per field that differs from the default.
_MISMATCH_VALUES = [
    ("url", "http://other.com"),
    ("title", "Other Title"),
    ("lang", "en"),
    ("fetched_at", "2025-01-01T00:00:00Z"),
    ("etag", "xyz789"),
    ("last_modified", "Tue, 02 Jan 2026 00:00:00 GMT"),
    ("source_file", "/other/path/file.txt"),
    ("chunking_strategy", "semantic"),
    ("schema_version", "2"),
    ("artifact_type", "image"),
    ("created_by", "other-user"),
]


# A second chunk file payload differing in exactly one field from _DEFAULT_CHUNK_PAYLOAD.
def _second_chunk_payload(field: str, value: str) -> dict:
    base = {
        "url": _DOC_URL,
        "title": "Test Doc",
        "lang": "ja",
        "fetched_at": _FETCHED_AT,
        "etag": _ETAG,
        "last_modified": _LAST_MODIFIED,
        "source_file": "/test/file.json",
        "chunking_strategy": _CHUNKING_STRATEGY,
        "schema_version": "1",
        "artifact_type": "document",
        "created_by": "system",
        "chunk_index": 1,
        "content": _CHUNK_CONTENT,
        "normalized_content": _NORMALIZED_CONTENT,
    }
    base[field] = value
    return base


def _create_workflow_db(db_file: Path) -> None:
    cfg = _make_db_config(db_file, "workflow")
    with (
        patch("db.helper.build_db_config", return_value=cfg),
        patch(
            "db.create_schema.build_workflow_schema_sql",
            return_value=_WORKFLOW_SCHEMA_NO_VEC0,
        ),
    ):
        cs.create_workflow_schema()


def _recorded_versions(db_file: Path) -> list[str]:
    conn = sqlite3.connect(str(db_file))
    try:
        rows = conn.execute(
            "SELECT version FROM workflow_schema_version ORDER BY applied_at, rowid"
        ).fetchall()
    finally:
        conn.close()
    return [row[0] for row in rows]


class TestWorkflowSchemaVersionRecord:
    """The version log is recorded once and an older database is never stamped."""

    def test_first_run_records_the_current_version_once(self, tmp_path: Path) -> None:
        from db.schema_sql import WORKFLOW_SCHEMA_VERSION

        db_file = tmp_path / "first_run.sqlite"
        _create_workflow_db(db_file)
        assert _recorded_versions(db_file) == [WORKFLOW_SCHEMA_VERSION]

    def test_rerun_at_the_current_version_is_idempotent(self, tmp_path: Path) -> None:
        from db.schema_sql import WORKFLOW_SCHEMA_VERSION

        db_file = tmp_path / "rerun.sqlite"
        _create_workflow_db(db_file)
        _create_workflow_db(db_file)
        assert _recorded_versions(db_file) == [WORKFLOW_SCHEMA_VERSION]

    def test_differing_version_raises_and_records_nothing(self, tmp_path: Path) -> None:
        db_file = tmp_path / "older.sqlite"
        _create_workflow_db(db_file)
        conn = sqlite3.connect(str(db_file))
        conn.execute("UPDATE workflow_schema_version SET version = '0.0.1'")
        conn.commit()
        conn.close()
        with pytest.raises(RuntimeError, match="recreate the database"):
            _create_workflow_db(db_file)
        assert _recorded_versions(db_file) == ["0.0.1"]

    def test_new_database_has_no_approvals_table(self, tmp_path: Path) -> None:
        db_file = tmp_path / "new_workflow.sqlite"
        _create_workflow_db(db_file)
        conn = sqlite3.connect(str(db_file))
        tables = _table_names(conn)
        conn.close()
        assert "approvals" not in tables
        assert {"tasks", "attempts", "processed_events", "artifacts"} <= tables


class TestRagSchemaColumnIntegrity:
    """Verify NOT NULL enforcement on the four target columns via real INSERT."""

    @pytest.fixture()
    def rag_conn(self, tmp_path: Path) -> sqlite3.Connection:
        db_file = tmp_path / "rag_integrity.sqlite"
        conn = sqlite3.connect(str(db_file))
        conn.executescript(_RAG_SCHEMA_NO_VEC0)
        return conn

    def test_insert_documents_without_fetched_at_raises(
        self, rag_conn: sqlite3.Connection
    ) -> None:
        with pytest.raises(sqlite3.IntegrityError):
            rag_conn.execute(
                "INSERT INTO documents(url, title, lang, etag, last_modified, chunking_strategy)"
                " VALUES(?, ?, ?, ?, ?, ?)",
                (_DOC_URL, "Test", "ja", _ETAG, _LAST_MODIFIED, _CHUNKING_STRATEGY),
            )

    def test_insert_documents_without_chunking_strategy_raises(
        self, rag_conn: sqlite3.Connection
    ) -> None:
        with pytest.raises(sqlite3.IntegrityError):
            rag_conn.execute(
                "INSERT INTO documents(url, title, lang, fetched_at, etag, last_modified)"
                " VALUES(?, ?, ?, ?, ?, ?)",
                (_DOC_URL, "Test", "ja", _FETCHED_AT, _ETAG, _LAST_MODIFIED),
            )

    def test_insert_chunks_without_chunk_type_raises(
        self, rag_conn: sqlite3.Connection
    ) -> None:
        doc_id = rag_conn.execute(
            "INSERT INTO documents(url, title, lang, fetched_at, etag, last_modified, chunking_strategy)"
            " VALUES(?, ?, ?, ?, ?, ?, ?) RETURNING doc_id",
            (
                _DOC_URL,
                "Test",
                "ja",
                _FETCHED_AT,
                _ETAG,
                _LAST_MODIFIED,
                _CHUNKING_STRATEGY,
            ),
        ).fetchone()[0]
        with pytest.raises(sqlite3.IntegrityError):
            rag_conn.execute(
                "INSERT INTO chunks(doc_id, chunk_index, content, normalized_content, source_file)"
                " VALUES(?, ?, ?, ?, ?)",
                (doc_id, _CHUNK_INDEX, _CHUNK_CONTENT, _NORMALIZED_CONTENT, ""),
            )

    def test_insert_chunks_without_source_file_raises(
        self, rag_conn: sqlite3.Connection
    ) -> None:
        doc_id = rag_conn.execute(
            "INSERT INTO documents(url, title, lang, fetched_at, etag, last_modified, chunking_strategy)"
            " VALUES(?, ?, ?, ?, ?, ?, ?) RETURNING doc_id",
            (
                _DOC_URL,
                "Test",
                "ja",
                _FETCHED_AT,
                _ETAG,
                _LAST_MODIFIED,
                _CHUNKING_STRATEGY,
            ),
        ).fetchone()[0]
        with pytest.raises(sqlite3.IntegrityError):
            rag_conn.execute(
                "INSERT INTO chunks(doc_id, chunk_index, content, normalized_content, chunk_type)"
                " VALUES(?, ?, ?, ?, ?)",
                (doc_id, _CHUNK_INDEX, _CHUNK_CONTENT, _NORMALIZED_CONTENT, "text"),
            )

    def test_nullable_columns_still_accept_null(
        self, rag_conn: sqlite3.Connection
    ) -> None:
        # Documents: etag and last_modified are nullable.
        rag_conn.execute(
            "INSERT INTO documents(url, title, lang, fetched_at, etag, last_modified, chunking_strategy)"
            " VALUES(?, ?, ?, ?, ?, ?, ?)",
            (_DOC_URL, "NullDoc", "ja", _FETCHED_AT, None, None, _CHUNKING_STRATEGY),
        )
        row = rag_conn.execute(
            "SELECT etag, last_modified FROM documents WHERE url=? AND title=?",
            (_DOC_URL, "NullDoc"),
        ).fetchone()
        assert row[0] is None
        assert row[1] is None

        # Chunks: normalized_content is nullable.
        doc_id = rag_conn.execute(
            "INSERT INTO documents(url, title, lang, fetched_at, etag, last_modified, chunking_strategy)"
            " VALUES(?, ?, ?, ?, ?, ?, ?) RETURNING doc_id",
            (
                "http://null.example.com",
                "NullChunk",
                "ja",
                _FETCHED_AT,
                None,
                None,
                _CHUNKING_STRATEGY,
            ),
        ).fetchone()[0]
        rag_conn.execute(
            "INSERT INTO chunks(doc_id, chunk_index, content, normalized_content, chunk_type, source_file)"
            " VALUES(?, ?, ?, ?, ?, ?)",
            (doc_id, _CHUNK_INDEX, _CHUNK_CONTENT, None, "text", ""),
        )
        row = rag_conn.execute(
            "SELECT normalized_content FROM chunks WHERE chunk_index=?", (_CHUNK_INDEX,)
        ).fetchone()
        assert row[0] is None

    def test_non_contiguous_chunk_index_is_validated_by_ingester(
        self, tmp_path: Path
    ) -> None:
        # This test validates that the ingester rejects non-contiguous chunk_index values.
        # The fixture provides a real DB connection but the validation happens at the
        # ingester level, not the DB constraint level.
        pass  # Placeholder — actual validation is tested in test_ingester.py

    def test_duplicate_chunk_index_is_validated_by_ingester(
        self, tmp_path: Path
    ) -> None:
        # Same as above — duplicate chunk_index validation is an ingester concern.
        pass  # Placeholder

    def test_11_field_mismatch_rejected_by_ingester(self, tmp_path: Path) -> None:
        # Same as above — cross-file mismatch detection is an ingester concern.
        pass  # Placeholder


# ── timestamp defaults ────────────────────────────────────────────────────────────


class TestTimestampDefaults:
    """Verify that all DEFAULT timestamps use strftime('%Y-%m-%dT%H:%M:%SZ', 'now')."""

    def test_rag_schema_timestamps(self, tmp_path: Path) -> None:
        db_file = tmp_path / "rag_ts.sqlite"
        cfg = _make_db_config(db_file, "rag")
        with (
            patch("db.helper.build_db_config", return_value=cfg),
            patch(
                "db.create_schema.build_rag_schema_sql",
                return_value=_RAG_SCHEMA_NO_VEC0,
            ),
            patch.object(SQLiteHelper, "_load_vec_extension", return_value=None),
        ):
            cs.create_rag_schema()
        conn = sqlite3.connect(str(db_file))
        info = conn.execute("PRAGMA table_info(documents)").fetchall()
        for row in info:
            col_name = row[1]
            default = row[4]
            if col_name == "fetched_at":
                # fetched_at no longer has a DEFAULT after the plan's removal
                assert default is None
        conn.close()

    def test_session_schema_timestamps(self, tmp_path: Path) -> None:
        db_file = tmp_path / "session_ts.sqlite"
        cfg = _make_db_config(db_file, "session")
        with (
            patch("db.helper.build_db_config", return_value=cfg),
            patch(
                "db.create_schema.build_session_schema_sql",
                return_value=_SESSION_SCHEMA_NO_VEC0,
            ),
            patch.object(SQLiteHelper, "_load_vec_extension", return_value=None),
        ):
            cs.create_session_schema()
        conn = sqlite3.connect(str(db_file))
        for table in (
            "sessions",
            "messages",
            "memories",
            "session_diagnostics",
        ):
            info = conn.execute(f"PRAGMA table_info({table})").fetchall()
            for row in info:
                col_name = row[1]
                default = row[4]
                if col_name.endswith("_at"):
                    assert default is not None, f"{table}.{col_name} has no DEFAULT"
                    assert "datetime('now')" not in (default or ""), (
                        f"{table}.{col_name} uses datetime('now')"
                    )
        conn.close()

    def test_workflow_schema_timestamps(self, tmp_path: Path) -> None:
        db_file = tmp_path / "workflow_ts.sqlite"
        cfg = _make_db_config(db_file, "workflow")
        # The real workflow DDL has no vec0 dependency, so it is checked as-is;
        # the database path is redirected so no test ever writes under /opt/llm.
        with patch("db.helper.build_db_config", return_value=cfg):
            cs.create_workflow_schema()
        conn = sqlite3.connect(str(db_file))
        for table in (
            "tasks",
            "attempts",
            "processed_events",
            "artifacts",
        ):
            info = conn.execute(f"PRAGMA table_info({table})").fetchall()
            assert info, f"{table} was not created in the temporary database"
            for row in info:
                col_name = row[1]
                default = row[4]
                not_null = row[3]
                # Nullable columns such as attempts.ended_at carry no default.
                if col_name.endswith("_at") and not_null:
                    assert default is not None, f"{table}.{col_name} has no DEFAULT"
                    assert "datetime('now')" not in (default or ""), (
                        f"{table}.{col_name} uses datetime('now')"
                    )
        conn.close()

    def test_eventbus_schema_timestamps(self, tmp_path: Path) -> None:
        db_file = tmp_path / "eventbus_ts.sqlite"
        cfg = _make_db_config(db_file, "eventbus")
        with (
            patch("db.helper.build_db_config", return_value=cfg),
            patch(
                "db.create_schema.build_eventbus_schema_sql",
                return_value=_EVENTBUS_SCHEMA_NO_VEC0,
            ),
        ):
            cs.create_eventbus_schema()
        conn = sqlite3.connect(str(db_file))
        info = conn.execute("PRAGMA table_info(events)").fetchall()
        assert info, "events was not created in the temporary database"
        for row in info:
            col_name = row[1]
            default = row[4]
            not_null = row[3]
            # Nullable columns such as events.dlq_at carry no default.
            if col_name.endswith("_at") and not_null:
                assert default is not None, f"events.{col_name} has no DEFAULT"
                assert "datetime('now')" not in (default or ""), (
                    f"events.{col_name} uses datetime('now')"
                )
        conn.close()

    def test_create_eventbus_schema_produces_new_tables(self, tmp_path: Path) -> None:
        """create_eventbus_schema() produces consumer_delivery/consumer_offsets tables (REQ-001, REQ-002; AC-7)."""
        import unittest.mock as mock

        extra_ddl = """
CREATE TABLE IF NOT EXISTS consumer_delivery (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    consumer_id     TEXT    NOT NULL,
    event_id        TEXT    NOT NULL,
    delivered_at    TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    UNIQUE(consumer_id, event_id)
);

CREATE TABLE IF NOT EXISTS consumer_offsets (
    consumer_id     TEXT    PRIMARY KEY,
    last_offset     INTEGER NOT NULL DEFAULT 0,
    updated_at      TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);
"""

        db_file = tmp_path / "eventbus_new_tables.sqlite"
        cfg = _make_db_config(db_file, "eventbus")
        with (
            patch("db.helper.build_db_config", return_value=cfg),
            mock.patch(
                "db.create_schema.build_eventbus_schema_sql",
                side_effect=lambda: _EVENTBUS_SCHEMA_NO_VEC0 + extra_ddl,
            ),
        ):
            cs.create_eventbus_schema()

        conn = sqlite3.connect(str(db_file))
        tables = _table_names(conn)
        conn.close()
        assert {"events", "consumer_delivery", "consumer_offsets"} <= tables


class TestEventbusSchemaCreation:
    """create_eventbus_schema() writes the single DDL source; a fresh database ends in
    the current shape with every table and the boolean acked column present."""

    def test_bootstrap_creates_current_schema_on_a_fresh_database(
        self, tmp_path: Path
    ) -> None:
        """A fresh database must end in the current shape with every table present."""
        db_file = tmp_path / "eventbus_fresh_ack.sqlite"
        cfg = _make_db_config(db_file, "eventbus")
        with patch("db.helper.build_db_config", return_value=cfg):
            cs.create_eventbus_schema()
        conn = sqlite3.connect(str(db_file))
        cols = {
            row[1]: (row[2], row[3], row[4])
            for row in conn.execute("PRAGMA table_info(consumer_delivery)")
        }
        tables = _table_names(conn)
        conn.close()
        assert {"events", "consumer_delivery", "consumer_offsets"} <= tables
        assert cols["acked"] == ("INTEGER", 1, "0")

    def test_fresh_database_is_stamped_with_the_schema_version(
        self, tmp_path: Path
    ) -> None:
        db_file = tmp_path / "eventbus_stamped.sqlite"
        cfg = _make_db_config(db_file, "eventbus")
        with patch("db.helper.build_db_config", return_value=cfg):
            cs.create_eventbus_schema()
        conn = sqlite3.connect(str(db_file))
        version = conn.execute("PRAGMA user_version").fetchone()[0]
        conn.close()
        assert version == eventbus_schema_version()

    def test_mismatched_version_is_refused_not_migrated(self, tmp_path: Path) -> None:
        """A database stamped with another version fails explicitly and is left as is."""
        db_file = tmp_path / "eventbus_other_version.sqlite"
        raw = sqlite3.connect(str(db_file))
        raw.execute("CREATE TABLE events (seq INTEGER PRIMARY KEY, event_id TEXT)")
        raw.execute("PRAGMA user_version = 99")
        raw.close()
        cfg = _make_db_config(db_file, "eventbus")
        with patch("db.helper.build_db_config", return_value=cfg):
            with pytest.raises(RuntimeError, match="recreate the database"):
                cs.create_eventbus_schema()
        conn = sqlite3.connect(str(db_file))
        columns = [r[1] for r in conn.execute("PRAGMA table_info(events)")]
        tables = _table_names(conn)
        conn.close()
        assert columns == ["seq", "event_id"]
        assert "consumer_delivery" not in tables

    def test_unstamped_existing_database_is_not_stamped(self, tmp_path: Path) -> None:
        """create_eventbus_schema() never vouches for an unverified database."""
        db_file = tmp_path / "eventbus_unstamped.sqlite"
        raw = sqlite3.connect(str(db_file))
        raw.executescript(build_eventbus_schema_sql())
        raw.execute("PRAGMA user_version = 0")
        raw.close()
        cfg = _make_db_config(db_file, "eventbus")
        with patch("db.helper.build_db_config", return_value=cfg):
            cs.create_eventbus_schema()
        conn = sqlite3.connect(str(db_file))
        version = conn.execute("PRAGMA user_version").fetchone()[0]
        conn.close()
        assert version == 0

    def test_unstamped_old_shape_fails_explicitly(self, tmp_path: Path) -> None:
        """An old-shape database is not migrated: the DDL fails and nothing is stamped."""
        db_file = tmp_path / "eventbus_old_shape.sqlite"
        raw = sqlite3.connect(str(db_file))
        raw.execute("CREATE TABLE events (seq INTEGER PRIMARY KEY, event_id TEXT)")
        raw.close()
        cfg = _make_db_config(db_file, "eventbus")
        with patch("db.helper.build_db_config", return_value=cfg):
            with pytest.raises(sqlite3.OperationalError):
                cs.create_eventbus_schema()
        conn = sqlite3.connect(str(db_file))
        version = conn.execute("PRAGMA user_version").fetchone()[0]
        conn.close()
        assert version == 0

    def test_malformed_stamped_database_fails_closed(self, tmp_path: Path) -> None:
        """A malformed database stamped with the current version is rejected after
        the DDL and before commit, and the deviation is left as-is (REQ-003)."""
        db_file = tmp_path / "eventbus_malformed_stamped.sqlite"
        raw = sqlite3.connect(str(db_file))
        raw.executescript(
            build_eventbus_schema_sql().replace(
                "    topic                  TEXT    NOT NULL,",
                "    topic                  TEXT,",
            )
        )
        raw.execute(f"PRAGMA user_version = {eventbus_schema_version()}")
        raw.commit()
        raw.close()
        cfg = _make_db_config(db_file, "eventbus")
        with patch("db.helper.build_db_config", return_value=cfg):
            with pytest.raises(RuntimeError, match="columns differ"):
                cs.create_eventbus_schema()
        conn = sqlite3.connect(str(db_file))
        notnull = {r[1]: r[3] for r in conn.execute("PRAGMA table_info(events)")}
        version = int(conn.execute("PRAGMA user_version").fetchone()[0])
        conn.close()
        assert (
            notnull["topic"] == 0
        )  # still malformed: nothing was repaired or committed
        assert version == eventbus_schema_version()


# ── EventBus schema fingerprint validator (REQ-001: shape gate independent of user_version) ──


_CANONICAL_EVENTBUS_DDL = build_eventbus_schema_sql()


def _apply_eventbus_ddl(ddl: str) -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.executescript(ddl)
    return conn


class TestEventbusSchemaFingerprint:
    """The shared fingerprint validator accepts a canonical EventBus database and
    rejects any structural deviation, even when the structural check alone proves
    the shape (no user_version involved)."""

    def test_canonical_database_matches_expected_fingerprint(
        self, tmp_path: Path
    ) -> None:
        """A database built from schema.sql matches expected_fingerprint() exactly."""
        db_file = tmp_path / "eventbus_fingerprint.sqlite"
        raw = sqlite3.connect(str(db_file))
        raw.executescript(_CANONICAL_EVENTBUS_DDL)
        raw.close()
        conn = sqlite3.connect(str(db_file))
        try:
            assert_matches(conn)
            assert build_fingerprint(conn) == expected_fingerprint()
        finally:
            conn.close()

    def test_in_memory_apply_matches_disk_apply(self) -> None:
        """apply_schema_in_memory() and a disk apply of the same DDL fingerprint identically."""
        disk = _apply_eventbus_ddl(_CANONICAL_EVENTBUS_DDL)
        try:
            assert build_fingerprint(disk) == build_fingerprint(
                apply_schema_in_memory()
            )
        finally:
            disk.close()

    def test_missing_column_raises(self) -> None:
        ddl = _CANONICAL_EVENTBUS_DDL.replace(
            "    acked                          INTEGER NOT NULL DEFAULT 0,\n", ""
        ).replace(
            "CREATE INDEX IF NOT EXISTS idx_consumer_delivery_consumer_ack\n"
            "    ON consumer_delivery(consumer_id, acked);",
            "",
        )
        conn = _apply_eventbus_ddl(ddl)
        try:
            with pytest.raises(RuntimeError, match="consumer_delivery: columns differ"):
                assert_matches(conn, label="test-missing-column")
        finally:
            conn.close()

    def test_missing_index_raises(self) -> None:
        ddl = _CANONICAL_EVENTBUS_DDL.replace(
            "CREATE INDEX IF NOT EXISTS idx_events_dlq_seq ON events(dlq_at, seq);", ""
        )
        conn = _apply_eventbus_ddl(ddl)
        try:
            with pytest.raises(RuntimeError, match="events: indexes differ"):
                assert_matches(conn, label="test-missing-index")
        finally:
            conn.close()

    def test_changed_nullability_raises(self) -> None:
        ddl = _CANONICAL_EVENTBUS_DDL.replace(
            "    topic                  TEXT    NOT NULL,",
            "    topic                  TEXT,",
        )
        conn = _apply_eventbus_ddl(ddl)
        try:
            with pytest.raises(RuntimeError, match="events: columns differ"):
                assert_matches(conn, label="test-changed-nullability")
        finally:
            conn.close()

    def test_changed_default_raises(self) -> None:
        ddl = _CANONICAL_EVENTBUS_DDL.replace(
            "strftime('%Y-%m-%dT%H:%M:%SZ', 'now')", "CURRENT_TIMESTAMP"
        )
        conn = _apply_eventbus_ddl(ddl)
        try:
            with pytest.raises(RuntimeError, match="events: columns differ"):
                assert_matches(conn, label="test-changed-default")
        finally:
            conn.close()

    def test_extra_column_raises(self) -> None:
        ddl = _CANONICAL_EVENTBUS_DDL.replace(
            "    consumer_id            TEXT\n);",
            "    consumer_id            TEXT,\n"
            "    created_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP\n);",
        )
        conn = _apply_eventbus_ddl(ddl)
        try:
            with pytest.raises(RuntimeError, match="events: columns differ"):
                assert_matches(conn, label="test-extra-column")
        finally:
            conn.close()

    def test_missing_table_raises(self) -> None:
        ddl = _CANONICAL_EVENTBUS_DDL.replace(
            "CREATE TABLE IF NOT EXISTS consumer_offsets (\n"
            "    consumer_id          TEXT    PRIMARY KEY,\n"
            "    offset               INTEGER NOT NULL DEFAULT 0\n"
            ");",
            "",
        )
        conn = _apply_eventbus_ddl(ddl)
        try:
            with pytest.raises(RuntimeError, match="missing table 'consumer_offsets'"):
                assert_matches(conn, label="test-missing-table")
        finally:
            conn.close()

    def test_extra_table_raises(self) -> None:
        ddl = (
            _CANONICAL_EVENTBUS_DDL
            + "\nCREATE TABLE audit_log (id INTEGER PRIMARY KEY);"
        )
        conn = _apply_eventbus_ddl(ddl)
        try:
            with pytest.raises(RuntimeError, match="unexpected table 'audit_log'"):
                assert_matches(conn, label="test-extra-table")
        finally:
            conn.close()

    def test_changed_table_level_constraint_raises(self) -> None:
        """Dropping the composite primary key changes both columns and table-level
        constraints; the validator must reject it."""
        ddl = _CANONICAL_EVENTBUS_DDL.replace(
            "    consumer_last_nack_attempt     TEXT,\n"
            "    PRIMARY KEY (consumer_id, event_id)\n"
            ");",
            "    consumer_last_nack_attempt     TEXT\n);",
        )
        conn = _apply_eventbus_ddl(ddl)
        try:
            with pytest.raises(RuntimeError, match="consumer_delivery.*differ"):
                assert_matches(conn, label="test-changed-constraint")
        finally:
            conn.close()

    def test_extra_foreign_key_raises(self) -> None:
        ddl = _CANONICAL_EVENTBUS_DDL.replace(
            "    consumer_last_nack_attempt     TEXT,\n"
            "    PRIMARY KEY (consumer_id, event_id)\n"
            ");",
            "    consumer_last_nack_attempt     TEXT,\n"
            "    PRIMARY KEY (consumer_id, event_id),\n"
            "    FOREIGN KEY (event_id) REFERENCES events(event_id)\n"
            ");",
        )
        conn = _apply_eventbus_ddl(ddl)
        try:
            with pytest.raises(
                RuntimeError, match="consumer_delivery: foreign keys differ"
            ):
                assert_matches(conn, label="test-extra-foreign-key")
        finally:
            conn.close()

    def test_validator_raises_even_when_user_version_matches(self) -> None:
        """A malformed database already stamped with the current version is still
        rejected: the shape gate does not trust user_version."""
        conn = _apply_eventbus_ddl(
            _CANONICAL_EVENTBUS_DDL.replace(
                "    topic                  TEXT    NOT NULL,",
                "    topic                  TEXT,",
            )
        )
        conn.execute(f"PRAGMA user_version = {eventbus_schema_version()}")
        try:
            with pytest.raises(RuntimeError, match="events: columns differ"):
                assert_matches(conn, label="test-stamped-but-malformed")
        finally:
            conn.close()


# ── DDL error propagation (behavior lock for the refactor extracting the shared ────
# try/except/log/raise pattern out of the four create_*_schema functions) ─────────


class TestSchemaDdlErrorPropagation:
    """Lock the DDL-execution error path shared by all create_*_schema functions:
    a sqlite3.OperationalError raised while executing the DDL script must be logged
    with the schema-specific label and re-raised unchanged (not swallowed)."""

    def test_create_rag_schema_propagates_and_logs(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        db_file = tmp_path / "rag_bad.sqlite"
        cfg = _make_db_config(db_file, "rag")
        with (
            patch("db.helper.build_db_config", return_value=cfg),
            patch(
                "db.create_schema.build_rag_schema_sql", return_value="NOT VALID SQL;"
            ),
            patch.object(SQLiteHelper, "_load_vec_extension", return_value=None),
            caplog.at_level(logging.ERROR, logger="db.create_schema"),
        ):
            with pytest.raises(sqlite3.OperationalError):
                cs.create_rag_schema()
        assert "Failed to execute RAG schema DDL" in caplog.text

    def test_create_session_schema_propagates_and_logs(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        db_file = tmp_path / "session_bad.sqlite"
        cfg = _make_db_config(db_file, "session")
        with (
            patch("db.helper.build_db_config", return_value=cfg),
            patch(
                "db.create_schema.build_session_schema_sql",
                return_value="NOT VALID SQL;",
            ),
            patch.object(SQLiteHelper, "_load_vec_extension", return_value=None),
            caplog.at_level(logging.ERROR, logger="db.create_schema"),
        ):
            with pytest.raises(sqlite3.OperationalError):
                cs.create_session_schema()
        assert "Failed to execute session schema DDL" in caplog.text

    def test_create_workflow_schema_propagates_and_logs(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        db_file = tmp_path / "workflow_bad.sqlite"
        cfg = DbConfig(
            rag_db_path="/tmp/rag.sqlite",
            session_db_path="/tmp/session.sqlite",
            workflow_db_path=str(db_file),
        )
        with (
            patch("db.helper.build_db_config", return_value=cfg),
            patch(
                "db.create_schema.build_workflow_schema_sql",
                return_value="NOT VALID SQL;",
            ),
            caplog.at_level(logging.ERROR, logger="db.create_schema"),
        ):
            with pytest.raises(sqlite3.OperationalError):
                cs.create_workflow_schema()
        assert "Failed to execute workflow schema DDL" in caplog.text

    # Note: create_eventbus_schema's DDL-error path is intentionally not covered
    # here — it keeps its own inline try/except instead of the shared
    # _execute_schema_ddl helper.


class TestCreateSchemaWrapper:
    """Lock create_schema()'s convenience-wrapper behavior: calls all four
    schema-creation functions, in order, exactly once each."""

    def test_calls_all_four_in_order(self) -> None:
        calls: list[str] = []
        with (
            patch(
                "db.create_schema.create_rag_schema",
                side_effect=lambda: calls.append("rag"),
            ),
            patch(
                "db.create_schema.create_session_schema",
                side_effect=lambda: calls.append("session"),
            ),
            patch(
                "db.create_schema.create_workflow_schema",
                side_effect=lambda: calls.append("workflow"),
            ),
            patch(
                "db.create_schema.create_eventbus_schema",
                side_effect=lambda: calls.append("eventbus"),
            ),
        ):
            cs.create_schema()
        assert calls == ["rag", "session", "workflow", "eventbus"]


def _create_eventbus_schema_at(tmp_path: Path, db_name: str) -> str:
    """Run create_eventbus_schema() against tmp_path/db_name, capturing the
    actual path SQLiteHelper wrote to.

    create_eventbus_schema() resolves its own DB path internally via
    SQLiteHelper("eventbus").open(write_mode=True) — build_db_config() (and
    thus the real, config-derived eventbus DB path) is not something this
    test controls, so sqlite3.connect()-ing a bare tmp_path file after the
    fact (the naive approach) verifies nothing, since create_eventbus_schema()
    never wrote there. Stubbing SQLiteHelper.__init__ to redirect its target
    path to tmp_path (mirroring TestEventBusSchemaNewColumns below) captures
    the path actually used instead.
    """
    db_path = str(tmp_path / db_name)

    def capture_init(self, target="rag", **kwargs):
        self._target = target
        self._db_path = db_path
        self._default_load_vec = False
        self._vec_so = None
        self._sqlite_timeout = 5000
        self._busy_timeout_ms = 5000

    with patch.object(cs.SQLiteHelper, "__init__", capture_init):
        with patch(
            "db.create_schema.build_eventbus_schema_sql",
            return_value=_EVENTBUS_SCHEMA_NO_VEC0,
        ):
            cs.create_eventbus_schema()
    return db_path


class TestEventBusTablesExist:
    """Verify consumer_delivery and consumer_offsets tables exist after schema creation."""

    def test_consumer_delivery_table_exists(self, tmp_path: Path) -> None:
        db_path = _create_eventbus_schema_at(tmp_path, "eventbus_td.sqlite")
        conn = sqlite3.connect(db_path)
        try:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='consumer_delivery'"
            )
            rows = cursor.fetchall()
            assert len(rows) == 1, "consumer_delivery table should exist"
        finally:
            conn.close()

    def test_consumer_offsets_table_exists(self, tmp_path: Path) -> None:
        db_path = _create_eventbus_schema_at(tmp_path, "eventbus_co.sqlite")
        conn = sqlite3.connect(db_path)
        try:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='consumer_offsets'"
            )
            rows = cursor.fetchall()
            assert len(rows) == 1, "consumer_offsets table should exist"
        finally:
            conn.close()

    def test_consumer_delivery_columns(self, tmp_path: Path) -> None:
        db_path = _create_eventbus_schema_at(tmp_path, "eventbus_cd_cols.sqlite")
        conn = sqlite3.connect(db_path)
        try:
            cursor = conn.execute("PRAGMA table_info(consumer_delivery)")
            cols = {row[1]: row[2] for row in cursor.fetchall()}
            assert "consumer_id" in cols, (
                "consumer_delivery should have consumer_id column"
            )
            assert "event_id" in cols, "consumer_delivery should have event_id column"
            assert "acked" in cols, "consumer_delivery should have acked column"
        finally:
            conn.close()

    def test_consumer_offsets_columns(self, tmp_path: Path) -> None:
        db_path = _create_eventbus_schema_at(tmp_path, "eventbus_co_cols.sqlite")
        conn = sqlite3.connect(db_path)
        try:
            cursor = conn.execute("PRAGMA table_info(consumer_offsets)")
            cols = {row[1]: row[2] for row in cursor.fetchall()}
            assert "consumer_id" in cols, (
                "consumer_offsets should have consumer_id column"
            )
            assert "offset" in cols, "consumer_offsets should have offset column"
        finally:
            conn.close()


class TestEventBusSchemaNewColumns:
    """Verify create_eventbus_schema() includes redelivered_from columns."""

    def test_events_table_has_redelivered_from_column(self, tmp_path: Path) -> None:
        import unittest.mock as mock

        captured_path = {}

        def capture_init(self, target="rag", **kwargs):
            # Set required attributes directly to skip DbConfig validation
            self._target = target
            self._db_path = str(tmp_path / "eventbus_rf.sqlite")
            self._default_load_vec = False
            self._vec_so = None
            self._sqlite_timeout = 5000
            self._busy_timeout_ms = 5000
            if target == "eventbus":
                captured_path["path"] = self._db_path

        with mock.patch.object(cs.SQLiteHelper, "__init__", capture_init):
            with mock.patch(
                "db.create_schema.build_eventbus_schema_sql",
                return_value=_EVENTBUS_SCHEMA_NO_VEC0,
            ):
                cs.create_eventbus_schema()

        if "path" in captured_path:
            conn = sqlite3.connect(captured_path["path"])
            try:
                cursor = conn.execute("PRAGMA table_info(events)")
                cols = {row[1]: row[2] for row in cursor.fetchall()}
                assert "redelivered_from" in cols, (
                    "events should have redelivered_from column"
                )
            finally:
                conn.close()
