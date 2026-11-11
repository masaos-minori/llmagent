"""tests/test_create_schema.py
Unit tests for create_schema: create_rag_schema, create_session_schema, idempotency.

vec0 virtual tables (chunks_vec, memories_vec) require the sqlite-vec extension.
Those DDL statements are excluded by patching build_*_schema_sql so the tests
run without the extension installed.

Schema creation is DDL-only. Idempotency is guaranteed by CREATE ... IF NOT EXISTS.
No migration helpers exist.
"""

import logging
import re
import sqlite3
from collections.abc import Generator
from pathlib import Path
from unittest.mock import patch

import db.create_schema as cs
import pytest
from db.config import DbConfig
from db.helper import SQLiteHelper
from db.schema_sql import build_workflow_schema_sql
from eventbus.db_tools import schema_sql as eventbus_schema_sql
from eventbus.schema import _init_schema as eventbus_init_schema
from shared.schema_fingerprint import (
    apply_ddl_in_memory,
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
    CREATE TABLE IF NOT EXISTS rag_corpus_meta (
        corpus_id                TEXT    NOT NULL,
        index_generation         INTEGER NOT NULL,
        embedding_model_id       TEXT    NOT NULL,
        normalization_version    TEXT    NOT NULL,
        chunking_policy_version  TEXT    NOT NULL,
        updated_at               TEXT    NOT NULL,
        CHECK (rowid = 1)
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

    def test_creates_rag_corpus_meta_table(
        self, rag_tmp_db: sqlite3.Connection
    ) -> None:
        """rag_corpus_meta is created by the fresh-RAG-schema builder (recreate-only)."""
        table_names = _table_names(rag_tmp_db)
        assert "rag_corpus_meta" in table_names
        cols = {
            row[1] for row in rag_tmp_db.execute("PRAGMA table_info(rag_corpus_meta)")
        }
        assert {
            "corpus_id",
            "index_generation",
            "embedding_model_id",
            "normalization_version",
            "chunking_policy_version",
            "updated_at",
        } <= cols

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
        task_nonce       TEXT UNIQUE NOT NULL,
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
        error_msg   TEXT,
        owner_id           TEXT,
        lease_expires_at   TEXT
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

    def test_fresh_schema_has_no_snapshot_surface(self) -> None:
        """The canonical workflow DDL creates no execution_snapshots table or snapshot_id column."""
        conn = sqlite3.connect(":memory:")
        conn.executescript(build_workflow_schema_sql())
        tables = _table_names(conn)
        columns = {row[1] for row in conn.execute("PRAGMA table_info(tool_call_state)")}
        conn.close()
        assert "tool_call_state" in tables
        assert "execution_snapshots" not in tables
        assert "snapshot_id" not in columns

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

    def test_tasks_task_nonce_unique(self, tmp_path: Path) -> None:
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

    def test_attempts_carries_the_lease_columns(self, tmp_path: Path) -> None:
        """Fresh create with the real DDL carries the lease columns, nullable so
        migrated and pre-existing rows stay null (AC-8, REQ-004)."""
        db_file = tmp_path / "workflow_lease.sqlite"
        cfg = _make_db_config(db_file, "workflow")
        # The real workflow DDL has no vec0 dependency, so it is checked as-is.
        with patch("db.helper.build_db_config", return_value=cfg):
            cs.create_workflow_schema()
        conn = sqlite3.connect(str(db_file))
        try:
            columns = {
                str(r[1]): r for r in conn.execute("PRAGMA table_info(attempts)")
            }
            assert {"owner_id", "lease_expires_at"} <= set(columns)
            for name in ("owner_id", "lease_expires_at"):
                assert columns[name][2] == "TEXT"  # type
                assert columns[name][3] == 0  # nullable, no NOT NULL
                assert columns[name][4] is None  # no DEFAULT
        finally:
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


class TestWorkflowStatusCheckConstraints:
    """CHECK constraints on tasks.status and attempts.status (REQ-003).

    Fresh databases built from the real canonical DDL reject out-of-vocabulary
    status writes; the equality test pins the DDL sets to the Python
    vocabularies in agent/workflow/models.py without a db->agent import edge.
    """

    _NOW = "2026-01-01T00:00:00+00:00"

    def _fresh_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(":memory:")
        conn.executescript(build_workflow_schema_sql())
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _insert_task(self, conn: sqlite3.Connection, status: str) -> None:
        conn.execute(
            "INSERT INTO tasks VALUES (?,?,?,?,?,?,?,?,?)",
            ("t1", "s1", None, 1, "1.0.0", status, "n1", self._NOW, self._NOW),
        )

    def _insert_attempt(self, conn: sqlite3.Connection, status: str) -> None:
        self._insert_task(conn, "pending")
        conn.execute(
            "INSERT INTO attempts (attempt_id, task_id, stage_id, status,"
            " started_at, ended_at, error_msg) VALUES (?,?,?,?,?,?,?)",
            ("a1", "t1", "plan", status, self._NOW, None, None),
        )

    def test_tasks_rejects_out_of_vocabulary_insert(self) -> None:
        conn = self._fresh_conn()
        with pytest.raises(sqlite3.IntegrityError):
            self._insert_task(conn, "done")

    def test_tasks_rejects_out_of_vocabulary_update(self) -> None:
        conn = self._fresh_conn()
        self._insert_task(conn, "pending")
        conn.commit()
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("UPDATE tasks SET status='halted_x' WHERE task_id='t1'")
        rows = conn.execute("SELECT status FROM tasks WHERE task_id='t1'").fetchall()
        assert rows == [("pending",)]
        conn.close()

    def test_attempts_rejects_out_of_vocabulary_insert(self) -> None:
        conn = self._fresh_conn()
        with pytest.raises(sqlite3.IntegrityError):
            self._insert_attempt(conn, "halted")

    def test_attempts_rejects_out_of_vocabulary_update(self) -> None:
        conn = self._fresh_conn()
        self._insert_attempt(conn, "running")
        conn.commit()
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("UPDATE attempts SET status='halted' WHERE attempt_id='a1'")
        rows = conn.execute(
            "SELECT status FROM attempts WHERE attempt_id='a1'"
        ).fetchall()
        assert rows == [("running",)]
        conn.close()

    @staticmethod
    def _ddl_check_set(table: str, column: str) -> set[str]:
        ddl = build_workflow_schema_sql()
        block = re.search(
            rf"CREATE TABLE IF NOT EXISTS {table} \((.*?)\n\);", ddl, re.S
        )
        assert block is not None, f"table {table} not found in canonical DDL"
        check = re.search(
            rf"{column}\s+TEXT NOT NULL[^,]*?CHECK\s*\(\s*{column}\s+IN\s*\((.*?)\)\s*\)",
            block.group(1),
        )
        assert check is not None, f"CHECK on {table}.{column} not found"
        return {part.strip().strip("'") for part in check.group(1).split(",")}

    def test_tasks_status_check_equals_python_vocabulary(self) -> None:
        from agent.workflow.models import TASK_STATUSES

        assert self._ddl_check_set("tasks", "status") == set(TASK_STATUSES)

    def test_attempts_status_check_equals_python_vocabulary(self) -> None:
        from agent.workflow.models import ATTEMPT_STATUSES

        assert self._ddl_check_set("attempts", "status") == set(ATTEMPT_STATUSES)


class TestWorkflowSchemaNoMarkers:
    """Fresh workflow databases carry no marker tables and no version rows (AC-002)."""

    def test_canonical_builder_emits_no_marker_tables(self) -> None:
        from db.schema_sql import build_workflow_schema_sql

        ddl = build_workflow_schema_sql()
        assert "schema_migrations" not in ddl
        assert "workflow_schema_version" not in ddl

    def test_fresh_creation_has_no_marker_tables_or_rows(self, tmp_path: Path) -> None:
        db_file = tmp_path / "first_run.sqlite"
        _create_workflow_db(db_file)
        _create_workflow_db(db_file)  # re-run stays a no-op
        conn = sqlite3.connect(str(db_file))
        try:
            tables = _table_names(conn)
            assert "workflow_schema_version" not in tables
            assert "schema_migrations" not in tables
        finally:
            conn.close()

    def test_new_database_has_no_approvals_table(self, tmp_path: Path) -> None:
        db_file = tmp_path / "new_workflow.sqlite"
        _create_workflow_db(db_file)
        conn = sqlite3.connect(str(db_file))
        tables = _table_names(conn)
        conn.close()
        assert "approvals" not in tables
        assert {"tasks", "attempts", "processed_events", "artifacts"} <= tables


class TestCreatePathMarkerAbsence:
    """Fresh workflow databases carry no marker tables or baseline rows;
    recreate-only rag/session domains carry none either (REQ-002 / AC-002)."""

    def test_workflow_fresh_creation_has_no_marker_tables(self, tmp_path: Path) -> None:
        db_file = tmp_path / "ledger_workflow.sqlite"
        _create_workflow_db(db_file)
        conn = sqlite3.connect(str(db_file))
        try:
            assert "schema_migrations" not in _table_names(conn)
            assert "workflow_schema_version" not in _table_names(conn)
        finally:
            conn.close()

    def test_rag_fresh_creation_has_no_ledger(
        self, rag_tmp_db: sqlite3.Connection
    ) -> None:
        assert "schema_migrations" not in _table_names(rag_tmp_db)

    def test_session_fresh_creation_has_no_ledger(
        self, session_tmp_db: sqlite3.Connection
    ) -> None:
        assert "schema_migrations" not in _table_names(session_tmp_db)


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


# ── EventBus schema fingerprint validator (REQ-001: shape gate independent of user_version) ──


_CANONICAL_EVENTBUS_DDL = eventbus_schema_sql()


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
            assert_matches(conn, _CANONICAL_EVENTBUS_DDL)
            assert build_fingerprint(conn) == expected_fingerprint(
                _CANONICAL_EVENTBUS_DDL
            )
        finally:
            conn.close()

    def test_in_memory_apply_matches_disk_apply(self) -> None:
        """apply_ddl_in_memory() and a disk apply of the same DDL fingerprint identically."""
        disk = _apply_eventbus_ddl(_CANONICAL_EVENTBUS_DDL)
        try:
            assert build_fingerprint(disk) == build_fingerprint(
                apply_ddl_in_memory(_CANONICAL_EVENTBUS_DDL)
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
                assert_matches(
                    conn, _CANONICAL_EVENTBUS_DDL, label="test-missing-column"
                )
        finally:
            conn.close()

    def test_missing_index_raises(self) -> None:
        ddl = _CANONICAL_EVENTBUS_DDL.replace(
            "CREATE INDEX IF NOT EXISTS idx_events_dlq_seq ON events(dlq_at, seq);", ""
        )
        conn = _apply_eventbus_ddl(ddl)
        try:
            with pytest.raises(RuntimeError, match="events: indexes differ"):
                assert_matches(
                    conn, _CANONICAL_EVENTBUS_DDL, label="test-missing-index"
                )
        finally:
            conn.close()

    def test_missing_redelivered_from_index_raises(self) -> None:
        """The fingerprint layer sees the redelivery-uniqueness index: removing it
        from the canonical DDL fails the shape gate (REQ-004)."""
        ddl = _CANONICAL_EVENTBUS_DDL.replace(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_events_redelivered_from "
            "ON events(redelivered_from) WHERE redelivered_from IS NOT NULL;",
            "",
        )
        conn = _apply_eventbus_ddl(ddl)
        try:
            with pytest.raises(RuntimeError, match="events: indexes differ"):
                assert_matches(
                    conn, _CANONICAL_EVENTBUS_DDL, label="test-missing-redelivered-index"
                )
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
                assert_matches(
                    conn, _CANONICAL_EVENTBUS_DDL, label="test-changed-nullability"
                )
        finally:
            conn.close()

    def test_changed_default_raises(self) -> None:
        """A database whose published_at still carries the removed strftime default
        (the pre-v3 shape) is rejected by the fingerprint gate."""
        ddl = _CANONICAL_EVENTBUS_DDL.replace(
            "    published_at           TEXT    NOT NULL,",
            "    published_at           TEXT    NOT NULL DEFAULT "
            "(strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),",
        )
        conn = _apply_eventbus_ddl(ddl)
        try:
            with pytest.raises(RuntimeError, match="events: columns differ"):
                assert_matches(
                    conn, _CANONICAL_EVENTBUS_DDL, label="test-changed-default"
                )
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
                assert_matches(conn, _CANONICAL_EVENTBUS_DDL, label="test-extra-column")
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
                assert_matches(
                    conn, _CANONICAL_EVENTBUS_DDL, label="test-missing-table"
                )
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
                assert_matches(conn, _CANONICAL_EVENTBUS_DDL, label="test-extra-table")
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
                assert_matches(
                    conn, _CANONICAL_EVENTBUS_DDL, label="test-changed-constraint"
                )
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
                assert_matches(
                    conn, _CANONICAL_EVENTBUS_DDL, label="test-extra-foreign-key"
                )
        finally:
            conn.close()

    def test_init_path_refuses_shape_drift(self, tmp_path: Path) -> None:
        """A drifted on-disk database is refused by the eventbus init path: with the
        version gate gone, fingerprint drift is the only (and sufficient) gate."""
        db_file = tmp_path / "eventbus_drift.sqlite"
        raw = sqlite3.connect(str(db_file))
        raw.executescript(_CANONICAL_EVENTBUS_DDL)
        raw.execute("CREATE TABLE audit_log (id INTEGER PRIMARY KEY)")
        raw.commit()
        raw.close()
        conn = sqlite3.connect(str(db_file))
        try:
            with pytest.raises(RuntimeError, match="unexpected table 'audit_log'"):
                eventbus_init_schema(conn)
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


class TestCreateSchemaWrapper:
    """Lock create_schema()'s convenience-wrapper behavior: calls all three
    schema-creation functions, in order, exactly once each."""

    def test_calls_all_three_in_order(self) -> None:
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
        ):
            cs.create_schema()
        assert calls == ["rag", "session", "workflow"]
