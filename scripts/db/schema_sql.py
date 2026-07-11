#!/usr/bin/env python3
"""db/schema_sql.py
SQL DDL templates for rag.sqlite, session.sqlite, workflow.sqlite, and eventbus.sqlite schema creation.

Templates use DIMS placeholder that must be replaced with the actual embedding
dimension count before execution (done by _build_rag_schema_sql /
_build_session_schema_sql in create_schema.py).

Functions:
  build_rag_schema_sql(dims) — return DDL for rag.sqlite with given dimension
  build_session_schema_sql(dims) — return DDL for session.sqlite with given dimension
  build_workflow_schema_sql() — return DDL for workflow.sqlite (metadata DB)
  build_eventbus_schema_sql() — return DDL for eventbus.sqlite (event bus message queue)
  apply_workflow_migrations(conn) — apply incremental schema migrations to an existing workflow DB
"""

import sqlite3

# Bump this constant whenever a new entry is added to _WORKFLOW_MIGRATIONS.
WORKFLOW_SCHEMA_VERSION = "1.0.0"

_RAG_SCHEMA_TEMPLATE: str = """
    CREATE TABLE IF NOT EXISTS documents (
        doc_id             INTEGER PRIMARY KEY AUTOINCREMENT,
        url                TEXT    NOT NULL UNIQUE,
        title              TEXT,
        lang               TEXT    NOT NULL CHECK (lang IN ('ja', 'en')),
        fetched_at         TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
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
        source_file        TEXT    NOT NULL DEFAULT ''
    );
    CREATE VIRTUAL TABLE IF NOT EXISTS chunks_vec USING vec0(
        chunk_id  INTEGER PRIMARY KEY,
        embedding float[DIMS]
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

_SESSION_SCHEMA_TEMPLATE: str = """
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
        embedding float[DIMS]
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
    status           TEXT NOT NULL DEFAULT 'pending',
    idempotency_key  TEXT UNIQUE NOT NULL,
    created_at       TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    updated_at       TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE TABLE IF NOT EXISTS attempts (
    attempt_id   TEXT PRIMARY KEY,
    task_id      TEXT NOT NULL REFERENCES tasks(task_id) ON DELETE CASCADE,
    stage_id     TEXT NOT NULL,
    status       TEXT NOT NULL DEFAULT 'running',
    started_at   TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    ended_at     TEXT,
    error_msg    TEXT,
    error_kind   TEXT,
    error_detail TEXT
);

CREATE TABLE IF NOT EXISTS processed_events (
    event_id    TEXT PRIMARY KEY,
    task_id     TEXT NOT NULL REFERENCES tasks(task_id) ON DELETE CASCADE,
    stage_id    TEXT NOT NULL,
    recorded_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    workflow_id TEXT
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

CREATE TABLE IF NOT EXISTS approvals (
    approval_id TEXT PRIMARY KEY,
    task_id     TEXT NOT NULL REFERENCES tasks(task_id) ON DELETE CASCADE,
    stage_id    TEXT,
    status      TEXT NOT NULL DEFAULT 'pending',
    reason      TEXT,
    created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    resolved_at TEXT,
    workflow_id TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS workflow_schema_version (
    version    TEXT NOT NULL,
    applied_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);
"""

_EVENTBUS_SCHEMA: str = """
PRAGMA journal_mode=WAL;

-- Timestamps use ISO-8601 UTC Z suffix format: 2026-07-02T10:00:00Z
-- acked_at and dlq_at are nullable (unset until acknowledged/dead-lettered)

CREATE TABLE IF NOT EXISTS events (
    seq                    INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id               TEXT    NOT NULL UNIQUE,
    topic                  TEXT    NOT NULL,
    payload                TEXT    NOT NULL,
    producer               TEXT    NOT NULL,
    published_at           TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    acked_at               TEXT,
    retry_count            INTEGER NOT NULL DEFAULT 0, -- deprecated; use delivery_failure_count
    delivery_failure_count INTEGER NOT NULL DEFAULT 0,
    dlq_requeue_count      INTEGER NOT NULL DEFAULT 0,
    dlq_at                 TEXT
);

CREATE INDEX IF NOT EXISTS idx_events_topic ON events(topic);
CREATE INDEX IF NOT EXISTS idx_events_seq   ON events(seq);
CREATE INDEX IF NOT EXISTS idx_events_dlq_at ON events(dlq_at);
CREATE INDEX IF NOT EXISTS idx_events_dlq_seq ON events(dlq_at, seq);
"""


def build_eventbus_schema_sql() -> str:
    """Return DDL for eventbus.sqlite (event bus message queue)."""
    return _EVENTBUS_SCHEMA


_WORKFLOW_MIGRATIONS: list[str] = [
    "ALTER TABLE attempts ADD COLUMN error_kind TEXT",
    "ALTER TABLE attempts ADD COLUMN error_detail TEXT",
    "ALTER TABLE artifacts ADD COLUMN workflow_id TEXT",
    "ALTER TABLE artifacts ADD COLUMN attempt_number INTEGER",
    "ALTER TABLE processed_events ADD COLUMN workflow_id TEXT",
]


def build_workflow_schema_sql() -> str:
    """Return DDL for workflow.sqlite (metadata DB)."""
    return _WORKFLOW_SCHEMA


def apply_workflow_migrations(conn: sqlite3.Connection) -> None:
    """Apply incremental migrations to an existing workflow.sqlite; idempotent."""
    for stmt in _WORKFLOW_MIGRATIONS:
        try:
            conn.execute(stmt)
        except sqlite3.OperationalError:
            pass  # column already exists
    conn.commit()
