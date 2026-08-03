"""
tests/test_regression_undo_artifact.py
Regression tests: undo + DB consistency.

Locks down:
  - session.undo_last_turn() deletes the last user message and everything after it.
  - After undo, fetch_messages() returns only pre-undo messages.
  - History length after undo matches DB row count.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from threading import Lock
from unittest.mock import patch

import pytest
from agent.session import AgentSession

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS sessions (
    session_id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    title TEXT
);
CREATE TABLE IF NOT EXISTS messages (
    message_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id   INTEGER NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    role         TEXT NOT NULL,
    content      TEXT NOT NULL,
    tool_calls   TEXT,
    tool_call_id TEXT,
    created_at   TEXT NOT NULL DEFAULT (datetime('now'))
);
"""

_write_lock = Lock()


class _FakeSQLiteHelper:
    _initialized_conns: set[int] = set()

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def open(
        self, *, write_mode: bool = False, row_factory: bool = False
    ) -> _FakeSQLiteHelper:
        self._conn.row_factory = sqlite3.Row if row_factory else None
        return self

    def execute(self, sql: str, params: tuple | dict = ()) -> sqlite3.Cursor:
        conn_id = id(self._conn)
        if conn_id not in _FakeSQLiteHelper._initialized_conns:
            with _write_lock:
                if conn_id not in _FakeSQLiteHelper._initialized_conns:
                    self._conn.executescript(_SCHEMA_SQL)
                    _FakeSQLiteHelper._initialized_conns.add(conn_id)
        return self._conn.execute(sql, params)

    @classmethod
    def reset(cls) -> None:
        cls._initialized_conns.clear()

    def executemany(self, sql: str, params_seq: list) -> sqlite3.Cursor:
        return self._conn.executemany(sql, params_seq)

    def fetchall(self, sql: str, params: tuple | dict = ()) -> list:
        return self._conn.execute(sql, params).fetchall()

    @contextmanager
    def write_transaction(
        self, sql: str, params: tuple = ()
    ) -> Generator[sqlite3.Cursor]:
        with _write_lock:
            cur = self._conn.execute(sql, params)
            yield cur
            self._conn.commit()

    def commit(self) -> None:
        with _write_lock:
            self._conn.commit()

    def close(self) -> None:
        pass

    @contextmanager
    def begin_immediate(self) -> Generator[None]:
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            yield
            self._conn.execute("COMMIT")
        except Exception:
            try:
                self._conn.execute("ROLLBACK")
            except sqlite3.OperationalError:
                pass
            raise

    def __enter__(self) -> _FakeSQLiteHelper:
        return self

    def __exit__(self, *_: object) -> None:
        pass


@pytest.fixture(autouse=True)
def reset_fake_helper() -> Generator[None]:
    _FakeSQLiteHelper.reset()
    yield


@pytest.fixture
def session() -> Generator[AgentSession]:
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(_SCHEMA_SQL)
    conn.commit()

    def _make(target: str = "session") -> _FakeSQLiteHelper:
        return _FakeSQLiteHelper(conn)

    with (
        patch("agent.session.SQLiteHelper", side_effect=_make),
        patch("agent.session_message_repo.SQLiteHelper", side_effect=_make),
        patch("agent.diagnostic_store.SQLiteHelper", side_effect=_make),
    ):
        s = AgentSession()
        s.start()
        yield s


class TestUndoLastTurnDeletesFromDb:
    def test_undo_removes_user_and_assistant(self, session: AgentSession) -> None:
        """undo_last_turn() deletes user + assistant from DB."""
        sid = session.session_id
        session.save_many(
            [
                ("user", "Hello", None, None),
                ("assistant", "Hi there", None, None),
            ]
        )
        assert len(session.fetch_messages(sid)) == 2

        deleted = session.undo_last_turn()

        assert deleted == 2
        assert session.fetch_messages(sid) == []

    def test_undo_preserves_earlier_turns(self, session: AgentSession) -> None:
        """undo_last_turn() only removes the last turn, not earlier ones."""
        sid = session.session_id
        session.save_many(
            [
                ("user", "First question", None, None),
                ("assistant", "First answer", None, None),
                ("user", "Second question", None, None),
                ("assistant", "Second answer", None, None),
            ]
        )

        session.undo_last_turn()

        msgs = session.fetch_messages(sid)
        assert len(msgs) == 2
        assert msgs[0]["content"] == "First question"
        assert msgs[1]["content"] == "First answer"


class TestUndoHistoryDbParity:
    def test_history_length_matches_db_after_undo(self, session: AgentSession) -> None:
        """DB row count after undo matches expected history length."""
        sid = session.session_id
        session.save_many(
            [
                ("system", "system prompt", None, None),
                ("user", "Hello", None, None),
                ("assistant", "Hi", None, None),
            ]
        )

        session.undo_last_turn()

        msgs = session.fetch_messages(sid)
        assert len(msgs) == 1
        assert msgs[0]["role"] == "system"

    def test_undo_noop_when_no_messages(self, session: AgentSession) -> None:
        """undo_last_turn() returns 0 and leaves DB empty when no messages exist."""
        deleted = session.undo_last_turn()

        assert deleted == 0
        assert session.fetch_messages(session.session_id) == []


class TestUndoReturnValue:
    def test_undo_returns_count_of_deleted_rows(self, session: AgentSession) -> None:
        """undo_last_turn() returns the number of rows deleted."""
        session.save_many(
            [
                ("user", "q1", None, None),
                ("assistant", "a1", None, None),
            ]
        )

        count = session.undo_last_turn()

        assert count == 2

    def test_undo_single_message_returns_one(self, session: AgentSession) -> None:
        """undo_last_turn() returns 1 when only one message exists (e.g., LLM never replied)."""
        session.save_many(
            [
                ("user", "orphaned user turn", None, None),
            ]
        )

        count = session.undo_last_turn()

        assert count == 1
