#!/usr/bin/env python3
"""tests/db/test_session_consistency.py — Unit tests for check_session_consistency()/is_consistent().

Mirrors test_rag_consistency.py's structure: a _FakeSQLiteHelper wrapper around a real
in-memory sqlite3.Connection, a local schema string (vec0-free copy of the production
schema), and one test class per concern group.
"""

from __future__ import annotations

import sqlite3

from scripts.db.session_consistency import check_session_consistency, is_consistent

# ── In-memory SQLite helper ───────────────────────────────────────────────────


class _FakeSQLiteHelper:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def fetchall(self, sql: str, params: tuple = ()) -> list[sqlite3.Row]:
        return self.conn.execute(sql, params).fetchall()

    def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        return self.conn.execute(sql, params)

    def commit(self) -> None:
        self.conn.commit()


# ── Schema (memories_vec replaced with a plain table to avoid vec0 extension) ──

_SESSION_SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    session_id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    title TEXT
);
CREATE TABLE IF NOT EXISTS messages (
    message_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    tool_calls TEXT,
    tool_call_id TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);
CREATE TABLE IF NOT EXISTS memories (
    memory_id TEXT PRIMARY KEY,
    memory_type TEXT NOT NULL CHECK(memory_type IN ('semantic','episodic')),
    source_type TEXT NOT NULL DEFAULT 'conversation',
    session_id INTEGER,
    turn_id TEXT,
    project TEXT NOT NULL DEFAULT '',
    repo TEXT NOT NULL DEFAULT '',
    branch TEXT NOT NULL DEFAULT '',
    content TEXT NOT NULL,
    summary TEXT NOT NULL DEFAULT '',
    tags TEXT NOT NULL DEFAULT '[]',
    importance REAL NOT NULL DEFAULT 0.5,
    pinned INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);
CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
    memory_id UNINDEXED,
    content,
    summary,
    tags
);
CREATE TABLE IF NOT EXISTS memory_links (
    src_id TEXT NOT NULL REFERENCES memories(memory_id) ON DELETE CASCADE,
    dst_id TEXT NOT NULL REFERENCES memories(memory_id) ON DELETE CASCADE,
    PRIMARY KEY (src_id, dst_id)
);
CREATE TABLE IF NOT EXISTS session_diagnostics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER REFERENCES sessions(session_id) ON DELETE CASCADE,
    kind TEXT NOT NULL,
    content TEXT NOT NULL,
    workflow_id TEXT,
    task_id TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);
CREATE INDEX IF NOT EXISTS idx_session_diagnostics_session
    ON session_diagnostics(session_id);
CREATE TABLE IF NOT EXISTS memories_vec (
    memory_id TEXT PRIMARY KEY,
    embedding BLOB
);
"""


def _make_session_db() -> _FakeSQLiteHelper:
    """Create an in-memory SQLite database with the session schema."""
    conn = sqlite3.connect(":memory:")
    conn.executescript(_SESSION_SCHEMA)
    conn.commit()
    return _FakeSQLiteHelper(conn)


# ── Tests ─────────────────────────────────────────────────────────────────────


class TestSessionConsistencyHealthy:
    """Tests for healthy (consistent) session database state."""

    def test_is_consistent_returns_true_on_healthy_db(self):
        db = _make_session_db()
        report = check_session_consistency(db)
        assert is_consistent(report) is True

    def test_all_checks_pass_on_healthy_db(self):
        db = _make_session_db()
        report = check_session_consistency(db)
        assert report.sessions >= 0
        assert report.messages >= 0
        assert report.memories >= 0
        assert report.orphaned_message_count == 0
        assert report.orphaned_memory_link_count == 0
        assert report.session_diagnostics_readable is True
        assert report.read_smoke_test_ok is True
        assert report.write_smoke_test_ok is True
        assert report.diagnostic_errors is None

    def test_no_content_leaked_in_healthy_report(self):
        """Assert no report field contains messages.content or memories.content strings."""
        db = _make_session_db()
        report = check_session_consistency(db)
        all_text = ""
        if report.diagnostic_errors:
            all_text += " ".join(report.diagnostic_errors)
        if report.affected_orphaned_message_ids:
            all_text += " ".join(str(i) for i in report.affected_orphaned_message_ids)
        if report.affected_orphaned_memory_link_pairs:
            all_text += " ".join(
                f"{a}{b}" for a, b in report.affected_orphaned_memory_link_pairs
            )
        assert "hello" not in all_text.lower()
        assert "world" not in all_text.lower()
        assert "test" not in all_text.lower()
        assert "message" not in all_text.lower()
        assert "memory" not in all_text.lower()

    def test_write_smoke_test_cleans_up(self):
        """Write smoke test must not leave the throwaway row behind."""
        db = _make_session_db()
        before = db.execute("SELECT COUNT(*) FROM session_diagnostics").fetchone()[0]
        report = check_session_consistency(db)
        after = db.execute("SELECT COUNT(*) FROM session_diagnostics").fetchone()[0]
        assert report.write_smoke_test_ok is True
        assert before == after

    def test_missing_table_detected(self):
        """Dropping a required table should set diagnostic_errors."""
        db = _make_session_db()
        db.execute("DROP TABLE IF EXISTS sessions")
        db.commit()
        report = check_session_consistency(db)
        assert report.diagnostic_errors is not None
        assert len(report.diagnostic_errors) > 0
        assert any("Missing table" in e for e in report.diagnostic_errors)
        assert is_consistent(report) is False

    def test_orphaned_messages_detected(self):
        """Inserting a messages row without a matching session should be detected."""
        db = _make_session_db()
        db.execute(
            "INSERT INTO messages(message_id, session_id, role, content) VALUES (9999, 9999, 'user', 'orphan')"
        )
        db.commit()
        report = check_session_consistency(db)
        assert report.orphaned_message_count == 1
        assert report.affected_orphaned_message_ids is not None
        assert 9999 in report.affected_orphaned_message_ids
        assert is_consistent(report) is False

    def test_orphaned_memory_links_detected(self):
        """Inserting a memory_links row without matching memories should be detected."""
        db = _make_session_db()
        db.execute(
            "INSERT OR IGNORE INTO memories(memory_id, memory_type, content, summary) VALUES ('valid_mem', 'semantic', 'valid_content', 'valid_summary')"
        )
        db.execute(
            "INSERT INTO memory_links(src_id, dst_id) VALUES ('nonexistent_src', 'nonexistent_dst')"
        )
        db.commit()
        report = check_session_consistency(db)
        assert report.orphaned_memory_link_count == 1
        assert report.affected_orphaned_memory_link_pairs is not None
        assert (
            "nonexistent_src",
            "nonexistent_dst",
        ) in report.affected_orphaned_memory_link_pairs
        assert is_consistent(report) is False

    def test_read_smoke_test_fails_when_table_missing(self):
        """Read smoke test should fail when a required table does not exist."""
        db = _make_session_db()
        db.execute("DROP TABLE IF EXISTS sessions")
        db.commit()
        report = check_session_consistency(db)
        assert report.read_smoke_test_ok is False
