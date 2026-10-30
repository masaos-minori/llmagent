#!/usr/bin/env python3
"""scripts/db/schema_sql.py

SQL DDL templates for rag.sqlite, session.sqlite, workflow.sqlite, and eventbus.sqlite schema creation.

Templates use DIMS placeholder that must be replaced with the actual embedding
dimension count before execution (done by build_rag_schema_sql(dims) /
build_session_schema_sql(dims), both defined below in this module).

Functions:
  build_rag_schema_sql(dims) — return DDL for rag.sqlite with given dimension
  build_session_schema_sql(dims) — return DDL for session.sqlite with given dimension
  build_workflow_schema_sql() — return DDL for workflow.sqlite (metadata DB)
  build_eventbus_schema_sql() — return DDL for eventbus.sqlite, read from scripts/eventbus/schema.sql
"""

import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

# Bump this constant whenever the workflow schema changes; it must equal the last
# `to_version` registered in db/migrations_workflow.py.
WORKFLOW_SCHEMA_VERSION = "1.3.0"

_RAG_SCHEMA_TEMPLATE: str = """
    CREATE TABLE IF NOT EXISTS documents (
        doc_id             INTEGER PRIMARY KEY AUTOINCREMENT,
        url                TEXT    NOT NULL UNIQUE,
        title              TEXT,
        lang               TEXT    NOT NULL CHECK (lang IN ('ja', 'en')),
        fetched_at         TEXT    NOT NULL,
        etag               TEXT,
        last_modified      TEXT,
        chunking_strategy  TEXT    NOT NULL DEFAULT 'text'
    );
   CREATE TABLE IF NOT EXISTS chunks (
        chunk_id           INTEGER PRIMARY KEY AUTOINCREMENT,
        doc_id             INTEGER NOT NULL
                           REFERENCES documents(doc_id) ON DELETE CASCADE,
        chunk_index        INTEGER NOT NULL,
        content            TEXT    NOT NULL,
        normalized_content TEXT,
        chunk_type         TEXT    NOT NULL DEFAULT 'text',
        source_file        TEXT    NOT NULL DEFAULT '',
        UNIQUE (doc_id, chunk_index),
        CHECK (chunk_index >= 0),
        CHECK (chunk_type IN ('text', 'code')),
        CHECK (length(content) > 0)
    );
    CREATE VIRTUAL TABLE IF NOT EXISTS chunks_vec USING vec0(
        chunk_id  INTEGER PRIMARY KEY,
        -- distance_metric is a column-level option, not a separate constructor arg (no comma)
        embedding float[DIMS] distance_metric=L2
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
    CREATE TRIGGER IF NOT EXISTS chunks_vec_ad
    AFTER DELETE ON chunks BEGIN
        DELETE FROM chunks_vec WHERE chunk_id = old.chunk_id;
    END;
"""

# session.sqlite uses recreate-only DDL (CREATE TABLE IF NOT EXISTS).
# Unlike rag.sqlite, session.sqlite's data (conversation history, semantic/episodic
# memory) is not trivially re-derivable from an external source. This gap is a
# known, accepted risk (cross-reference issues/done/20260819-183436_risks.md);
# the migration-mechanism-vs-recreate decision is deliberately deferred to the
# next concrete session.sqlite schema-change proposal, which must address data
# preservation rather than silently defaulting to a lossy recreate.
_SESSION_SCHEMA_TEMPLATE: str = """
    CREATE TABLE IF NOT EXISTS sessions (
        session_id              INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at              TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
        title                   TEXT,
        undo_floor_message_id   INTEGER NOT NULL DEFAULT 0
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
        -- Provenance only. This value may refer to a session that has been deleted.
        -- It does not establish ownership and has no foreign-key constraint.
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
    CREATE VIRTUAL TABLE IF NOT EXISTS memories_vec USING vec0(
        memory_id TEXT PRIMARY KEY,
        -- distance_metric is a column-level option, not a separate constructor arg (no comma)
        embedding float[DIMS] distance_metric=L2
    );
"""


def build_rag_schema_sql(dims: int) -> str:
    """Return DDL for rag.sqlite with the given embedding dimension."""
    return _RAG_SCHEMA_TEMPLATE.replace("DIMS", str(dims))


def build_session_schema_sql(dims: int) -> str:
    """Return DDL for session.sqlite with the given embedding dimension."""
    return _SESSION_SCHEMA_TEMPLATE.replace("DIMS", str(dims))


_WORKFLOW_SCHEMA: str = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS tasks (
    task_id          TEXT PRIMARY KEY,
    session_id       TEXT,
    workflow_id      TEXT,
    turn_number      INTEGER,
    workflow_version TEXT NOT NULL,
    status           TEXT NOT NULL DEFAULT 'pending'
                     CHECK (status IN ('pending', 'running', 'completed', 'failed', 'halted')),
    task_nonce       TEXT UNIQUE NOT NULL,
    created_at       TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    updated_at       TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE TABLE IF NOT EXISTS attempts (
    attempt_id   TEXT PRIMARY KEY,
    task_id      TEXT NOT NULL REFERENCES tasks(task_id) ON DELETE CASCADE,
    stage_id     TEXT NOT NULL,
    status       TEXT NOT NULL DEFAULT 'running'
                 CHECK (status IN ('running', 'completed', 'failed')),
    started_at   TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    ended_at     TEXT,
    error_msg    TEXT,
    error_kind   TEXT,
    error_detail TEXT,
    attempt_number INTEGER NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_attempts_task_stage_number
    ON attempts(task_id, stage_id, attempt_number);

CREATE TABLE IF NOT EXISTS processed_events (
    event_id    TEXT PRIMARY KEY,
    task_id     TEXT NOT NULL REFERENCES tasks(task_id) ON DELETE CASCADE,
    stage_id    TEXT NOT NULL,
    recorded_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    workflow_id TEXT,
    attempt_id  TEXT NOT NULL REFERENCES attempts(attempt_id) ON DELETE CASCADE,
    attempt_number INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS artifacts (
    artifact_id    TEXT PRIMARY KEY,
    task_id        TEXT NOT NULL REFERENCES tasks(task_id) ON DELETE CASCADE,
    stage_id       TEXT NOT NULL,
    uri            TEXT NOT NULL,
    created_at     TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    workflow_id    TEXT,
    attempt_number INTEGER
);

CREATE TABLE IF NOT EXISTS workflow_schema_version (
    version    TEXT NOT NULL,
    applied_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

-- Applied-migration ledger; the same shape as LEDGER_DDL in shared/db_migrations.py.
CREATE TABLE IF NOT EXISTS schema_migrations (
    id           TEXT PRIMARY KEY,
    applied_at   TEXT NOT NULL,
    from_version TEXT NOT NULL,
    to_version   TEXT NOT NULL
);
"""

# eventbus.sqlite's DDL is owned by the EventBus service (ADR-008 INV-04). The db layer
# reads it as a file and never imports the eventbus package.
EVENTBUS_SCHEMA_SQL_PATH: Path = (
    Path(__file__).resolve().parents[1] / "eventbus" / "schema.sql"
)


def eventbus_schema_version() -> int:
    """Return the version schema.sql stamps with PRAGMA user_version."""
    match = re.search(
        r"^PRAGMA\s+user_version\s*=\s*(\d+)\s*;",
        build_eventbus_schema_sql(),
        re.MULTILINE,
    )
    if match is None:
        raise RuntimeError(f"{EVENTBUS_SCHEMA_SQL_PATH} does not stamp user_version")
    return int(match.group(1))


def build_eventbus_schema_sql() -> str:
    """Return DDL for eventbus.sqlite (event bus message queue), read from scripts/eventbus/schema.sql."""
    return EVENTBUS_SCHEMA_SQL_PATH.read_text(encoding="utf-8")


def build_workflow_schema_sql() -> str:
    """Return DDL for workflow.sqlite (metadata DB)."""
    return _WORKFLOW_SCHEMA
