"""
tests/test_regression_diagnostic_persist.py
Regression tests: diagnostic persistence isolation.

Locks down:
  - DiagnosticStore.fetch() excludes rows from a different session_id.
  - Entries saved with session_id=None are stored and retrievable via fetch_all().
  - AgentSession.save_diagnostic() routes to session_diagnostics, not messages.
"""

from __future__ import annotations

import sqlite3
from unittest.mock import patch

import pytest
from agent.diagnostic_store import DiagnosticStore

_SCHEMA = """
CREATE TABLE IF NOT EXISTS session_diagnostics (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  INTEGER,
    kind        TEXT NOT NULL,
    content     TEXT NOT NULL,
    workflow_id TEXT,
    task_id     TEXT,
    created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);
CREATE INDEX IF NOT EXISTS idx_diag_session ON session_diagnostics(session_id);
CREATE TABLE IF NOT EXISTS messages (
    message_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id   INTEGER NOT NULL,
    role         TEXT NOT NULL,
    content      TEXT NOT NULL,
    tool_calls   TEXT,
    tool_call_id TEXT,
    created_at   TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


class _FakeSQLiteHelper:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def open(
        self, *, write_mode: bool = False, row_factory: bool = False, **_: object
    ) -> _FakeSQLiteHelper:
        self._conn.row_factory = sqlite3.Row if row_factory else None
        return self

    def __enter__(self) -> _FakeSQLiteHelper:
        return self

    def __exit__(self, *_: object) -> None:
        pass

    def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        return self._conn.execute(sql, params)

    def fetchall(self, sql: str, params: tuple = ()) -> list:
        return self._conn.execute(sql, params).fetchall()

    def commit(self) -> None:
        self._conn.commit()


@pytest.fixture
def fake_db() -> _FakeSQLiteHelper:
    conn = sqlite3.connect(":memory:")
    conn.executescript(_SCHEMA)
    return _FakeSQLiteHelper(conn)


class TestDiagnosticCrossSessionIsolation:
    def test_fetch_excludes_different_session(self, fake_db: _FakeSQLiteHelper) -> None:
        """fetch(session_id=2) returns empty when only session_id=1 has diagnostics."""
        with patch("agent.diagnostic_store.SQLiteHelper", return_value=fake_db):
            store = DiagnosticStore(session_id=1)
            store.save(session_id=1, kind="session_summary", content="session 1 entry")

            results = store.fetch(session_id=2)

        assert results == []

    def test_fetch_returns_own_session_entries(
        self, fake_db: _FakeSQLiteHelper
    ) -> None:
        """fetch(session_id=1) returns entries saved for session_id=1."""
        with patch("agent.diagnostic_store.SQLiteHelper", return_value=fake_db):
            store = DiagnosticStore(session_id=1)
            store.save(session_id=1, kind="session_summary", content="session 1 entry")

            results = store.fetch(session_id=1)

        assert len(results) == 1
        assert results[0]["content"] == "session 1 entry"

    def test_fetch_two_stores_same_db_isolation(
        self, fake_db: _FakeSQLiteHelper
    ) -> None:
        """Two stores sharing DB: each sees only its own session's diagnostics."""
        with patch("agent.diagnostic_store.SQLiteHelper", return_value=fake_db):
            store1 = DiagnosticStore(session_id=1)
            store2 = DiagnosticStore(session_id=2)

            store1.save(session_id=1, kind="session_summary", content="for session 1")

            assert store2.fetch(session_id=2) == []
            assert len(store1.fetch(session_id=1)) == 1


class TestDiagnosticNullSessionId:
    def test_null_session_id_entry_stored(self, fake_db: _FakeSQLiteHelper) -> None:
        """Diagnostics saved with session_id=None are stored and retrievable."""
        with patch("agent.diagnostic_store.SQLiteHelper", return_value=fake_db):
            store = DiagnosticStore(session_id=None)
            store.save(
                kind="llm_transport_error", session_id=None, content="conn error"
            )

            results = store.fetch_all()

        assert len(results) == 1
        assert results[0]["session_id"] is None


class TestSaveDiagnosticRoutesToDiagnosticsTable:
    def test_save_diagnostic_does_not_write_to_messages(
        self, fake_db: _FakeSQLiteHelper
    ) -> None:
        """AgentSession.save_diagnostic() must not insert into the messages table."""
        from agent.session import AgentSession

        _SESSIONS_SCHEMA = """
        CREATE TABLE IF NOT EXISTS sessions (
            session_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            title TEXT
        );
        """
        fake_db._conn.executescript(_SESSIONS_SCHEMA)

        with (
            patch("agent.session.SQLiteHelper", return_value=fake_db),
            patch("agent.session_message_repo.SQLiteHelper", return_value=fake_db),
            patch("agent.diagnostic_store.SQLiteHelper", return_value=fake_db),
        ):
            session = AgentSession()
            session.start()
            session.save_diagnostic("transport error")

        rows = fake_db.fetchall(
            "SELECT COUNT(*) FROM messages WHERE session_id = ?", (session.session_id,)
        )
        assert rows[0][0] == 0

    def test_save_diagnostic_writes_to_session_diagnostics(
        self, fake_db: _FakeSQLiteHelper
    ) -> None:
        """AgentSession.save_diagnostic() writes to session_diagnostics."""
        from agent.session import AgentSession

        _SESSIONS_SCHEMA = """
        CREATE TABLE IF NOT EXISTS sessions (
            session_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            title TEXT
        );
        """
        fake_db._conn.executescript(_SESSIONS_SCHEMA)

        with (
            patch("agent.session.SQLiteHelper", return_value=fake_db),
            patch("agent.session_message_repo.SQLiteHelper", return_value=fake_db),
            patch("agent.diagnostic_store.SQLiteHelper", return_value=fake_db),
        ):
            session = AgentSession()
            session.start()
            session.save_diagnostic("transport error")

        rows = fake_db.fetchall(
            "SELECT kind, content FROM session_diagnostics WHERE session_id = ?",
            (session.session_id,),
        )
        assert len(rows) == 1
        assert rows[0][0] == "llm_transport_error"
