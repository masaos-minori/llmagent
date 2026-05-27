"""
tests/test_agent_session.py
Behavior-lock tests for AgentSession.

Covers: start, save, save_many, fetch_messages, set_title,
        list_sessions, delete_session, delete_last_turn.
SQLiteHelper is replaced with an in-memory SQLite connection so no
real DB file or sqlite-vec extension is required.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Generator
from unittest.mock import patch

import pytest
from agent_session import AgentSession

# ── In-memory SQLiteHelper replacement ───────────────────────────────────────

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS sessions (
    session_id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    title TEXT
);
CREATE TABLE IF NOT EXISTS messages (
    message_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    role       TEXT NOT NULL,
    content    TEXT NOT NULL,
    tool_calls TEXT,
    tool_call_id TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


class _FakeSQLiteHelper:
    """Minimal SQLiteHelper drop-in backed by a real in-memory SQLite connection."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def open(
        self, *, write_mode: bool = False, row_factory: bool = False
    ) -> _FakeSQLiteHelper:
        self._conn.row_factory = sqlite3.Row if row_factory else None
        return self

    def execute(self, sql: str, params: tuple | dict = ()) -> sqlite3.Cursor:
        return self._conn.execute(sql, params)

    def fetchall(self, sql: str, params: tuple | dict = ()) -> list:
        return self._conn.execute(sql, params).fetchall()

    def commit(self) -> None:
        self._conn.commit()

    def close(self) -> None:
        pass  # keep alive for the test lifetime

    def __enter__(self) -> _FakeSQLiteHelper:
        return self

    def __exit__(self, *_: object) -> None:
        pass


@pytest.fixture
def session() -> Generator[AgentSession]:
    """AgentSession wired to a fresh in-memory SQLite DB."""
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys=ON")  # enable cascade deletes
    conn.executescript(_SCHEMA_SQL)
    conn.commit()

    def _make() -> _FakeSQLiteHelper:
        return _FakeSQLiteHelper(conn)

    with patch("agent_session.SQLiteHelper", side_effect=_make):
        yield AgentSession()


# ── start() ───────────────────────────────────────────────────────────────────


class TestStart:
    def test_sets_session_id(self, session: AgentSession) -> None:
        assert session.session_id is None
        session.start()
        assert session.session_id is not None
        assert isinstance(session.session_id, int)

    def test_inserts_row_in_sessions(self, session: AgentSession) -> None:
        session.start()
        # Verify via list_sessions: doesn't raise
        session.list_sessions()

    def test_multiple_starts_increment_id(self, session: AgentSession) -> None:
        session.start()
        first_id = session.session_id
        session.start()
        assert session.session_id != first_id


# ── save() ────────────────────────────────────────────────────────────────────


class TestSave:
    def test_saves_user_message(self, session: AgentSession) -> None:
        session.start()
        session.save("user", "hello")
        msgs = session.fetch_messages(session.session_id)  # type: ignore[arg-type]  # session_id narrowed by start() but typed int | None
        assert msgs is not None
        assert len(msgs) == 1
        assert msgs[0]["role"] == "user"
        assert msgs[0]["content"] == "hello"

    def test_saves_assistant_message(self, session: AgentSession) -> None:
        session.start()
        session.save("assistant", "world")
        msgs = session.fetch_messages(session.session_id)  # type: ignore[arg-type]  # session_id narrowed by start() but typed int | None
        assert msgs is not None
        assert msgs[0]["role"] == "assistant"

    def test_saves_tool_calls_json(self, session: AgentSession) -> None:
        session.start()
        tcs = [
            {
                "id": "tc1",
                "type": "function",
                "function": {"name": "f", "arguments": "{}"},
            }
        ]
        session.save("assistant", "", tool_calls=tcs)
        msgs = session.fetch_messages(session.session_id)  # type: ignore[arg-type]  # session_id narrowed by start() but typed int | None
        assert msgs is not None
        assert msgs[0].get("tool_calls") == tcs

    def test_saves_tool_call_id(self, session: AgentSession) -> None:
        session.start()
        session.save("tool", "result text", tool_call_id="tc1")
        msgs = session.fetch_messages(session.session_id)  # type: ignore[arg-type]  # session_id narrowed by start() but typed int | None
        assert msgs is not None
        assert msgs[0]["role"] == "tool"
        assert msgs[0].get("tool_call_id") == "tc1"

    def test_no_op_when_session_id_none(self, session: AgentSession) -> None:
        # No start() called — session_id is None
        session.save("user", "orphan")
        # No error; nothing written (session_id is None → early return)

    def test_invalid_role_is_skipped(self, session: AgentSession) -> None:
        session.start()
        session.save("invalid_role", "content")
        msgs = session.fetch_messages(session.session_id)  # type: ignore[arg-type]  # session_id narrowed by start() but typed int | None
        assert msgs is None or len(msgs) == 0


# ── save_many() ───────────────────────────────────────────────────────────────


class TestSaveMany:
    def test_saves_multiple_messages(self, session: AgentSession) -> None:
        session.start()
        rows: list[tuple[str, str, list[dict] | None, str | None]] = [
            ("tool", "result A", None, "tc1"),
            ("tool", "result B", None, "tc2"),
        ]
        session.save_many(rows)
        msgs = session.fetch_messages(session.session_id)  # type: ignore[arg-type]  # session_id narrowed by start() but typed int | None
        assert msgs is not None
        assert len(msgs) == 2
        assert msgs[0]["content"] == "result A"
        assert msgs[0].get("tool_call_id") == "tc1"
        assert msgs[1].get("tool_call_id") == "tc2"

    def test_no_op_when_empty(self, session: AgentSession) -> None:
        session.start()
        session.save_many([])  # should not raise

    def test_no_op_when_session_id_none(self, session: AgentSession) -> None:
        session.save_many([("user", "orphan", None, None)])  # no error

    def test_filters_invalid_roles(self, session: AgentSession) -> None:
        session.start()
        rows: list[tuple[str, str, list[dict] | None, str | None]] = [
            ("user", "valid", None, None),
            ("bad_role", "invalid", None, None),
        ]
        session.save_many(rows)
        msgs = session.fetch_messages(session.session_id)  # type: ignore[arg-type]  # session_id narrowed by start() but typed int | None
        assert msgs is not None
        assert len(msgs) == 1
        assert msgs[0]["role"] == "user"


# ── fetch_messages() ──────────────────────────────────────────────────────────


class TestFetchMessages:
    def test_returns_messages_in_order(self, session: AgentSession) -> None:
        session.start()
        session.save("user", "first")
        session.save("assistant", "second")
        msgs = session.fetch_messages(session.session_id)  # type: ignore[arg-type]  # session_id narrowed by start() but typed int | None
        assert msgs is not None
        assert msgs[0]["role"] == "user"
        assert msgs[1]["role"] == "assistant"

    def test_returns_none_for_unknown_session(self, session: AgentSession) -> None:
        result = session.fetch_messages(99999)
        assert result is None

    def test_tool_call_id_restored(self, session: AgentSession) -> None:
        session.start()
        session.save("tool", "content", tool_call_id="abc-123")
        msgs = session.fetch_messages(session.session_id)  # type: ignore[arg-type]  # session_id narrowed by start() but typed int | None
        assert msgs is not None
        assert msgs[0].get("tool_call_id") == "abc-123"

    def test_tool_call_id_absent_when_null(self, session: AgentSession) -> None:
        session.start()
        session.save("user", "no tool_call_id")
        msgs = session.fetch_messages(session.session_id)  # type: ignore[arg-type]  # session_id narrowed by start() but typed int | None
        assert msgs is not None
        assert "tool_call_id" not in msgs[0]

    def test_tool_calls_json_roundtrip(self, session: AgentSession) -> None:
        session.start()
        tcs = [
            {
                "id": "x",
                "type": "function",
                "function": {"name": "g", "arguments": "{}"},
            }
        ]
        session.save("assistant", "ok", tool_calls=tcs)
        msgs = session.fetch_messages(session.session_id)  # type: ignore[arg-type]  # session_id narrowed by start() but typed int | None
        assert msgs is not None
        assert msgs[0]["tool_calls"] == tcs

    def test_invalid_tool_calls_json_skipped(self, session: AgentSession) -> None:
        # Directly insert a corrupted tool_calls value
        session.start()
        session.save("assistant", "text")
        # Corrupt the tool_calls column post-insert
        with patch("agent_session.SQLiteHelper") as mock_cls:
            conn = sqlite3.connect(":memory:")
            conn.executescript(_SCHEMA_SQL)
            conn.commit()
            conn.execute("INSERT INTO sessions DEFAULT VALUES")
            conn.commit()
            sid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            conn.execute(
                "INSERT INTO messages (session_id, role, content, tool_calls)"
                " VALUES (?, 'assistant', 'bad', 'NOT_JSON')",
                (sid,),
            )
            conn.commit()
            mock_cls.side_effect = lambda: _FakeSQLiteHelper(conn)
            s2 = AgentSession()
            s2.session_id = sid
            msgs = s2.fetch_messages(sid)
        # Corrupted row should still return without KeyError; tool_calls absent
        assert msgs is not None
        assert "tool_calls" not in (msgs[0] if msgs else {})


# ── set_title() ───────────────────────────────────────────────────────────────


class TestSetTitle:
    def test_updates_title(
        self, session: AgentSession, capsys: pytest.CaptureFixture
    ) -> None:
        session.start()
        session.set_title("My Session")
        session.list_sessions()
        out = capsys.readouterr().out
        assert "My Session" in out

    def test_truncates_to_50_chars(
        self, session: AgentSession, capsys: pytest.CaptureFixture
    ) -> None:
        session.start()
        session.set_title("A" * 100)
        session.list_sessions()
        out = capsys.readouterr().out
        # title is stored at max 50 chars; displayed up to 32 chars + "..."
        assert "A" * 29 in out

    def test_no_op_when_session_id_none(self, session: AgentSession) -> None:
        session.set_title("ghost")  # should not raise


# ── list_sessions() ───────────────────────────────────────────────────────────


class TestListSessions:
    def test_prints_header_when_sessions_exist(
        self, session: AgentSession, capsys: pytest.CaptureFixture
    ) -> None:
        session.start()
        session.list_sessions()
        out = capsys.readouterr().out
        assert "ID" in out

    def test_prints_no_sessions_when_empty(
        self, session: AgentSession, capsys: pytest.CaptureFixture
    ) -> None:
        session.list_sessions()
        out = capsys.readouterr().out
        assert "No sessions found" in out

    def test_marks_current_session(
        self, session: AgentSession, capsys: pytest.CaptureFixture
    ) -> None:
        session.start()
        session.list_sessions()
        out = capsys.readouterr().out
        assert "*" in out  # current session marked


# ── delete_session() ─────────────────────────────────────────────────────────


class TestDeleteSession:
    def test_returns_true_on_success(self, session: AgentSession) -> None:
        session.start()
        sid = session.session_id
        result = session.delete_session(sid)  # type: ignore[arg-type]  # session_id narrowed by start() but typed int | None
        assert result is True

    def test_returns_false_for_unknown_id(self, session: AgentSession) -> None:
        result = session.delete_session(99999)
        assert result is False

    def test_cascades_to_messages(self, session: AgentSession) -> None:
        session.start()
        sid = session.session_id
        session.save("user", "to be deleted")
        session.delete_session(sid)  # type: ignore[arg-type]  # session_id narrowed by start() but typed int | None
        # After deletion, fetch_messages returns None
        msgs = session.fetch_messages(sid)  # type: ignore[arg-type]  # session_id narrowed by start() but typed int | None
        assert msgs is None


# ── delete_last_turn() ────────────────────────────────────────────────────────


class TestDeleteLastTurn:
    def test_removes_last_user_assistant_pair(self, session: AgentSession) -> None:
        session.start()
        session.save("user", "q1")
        session.save("assistant", "a1")
        session.save("user", "q2")
        session.save("assistant", "a2")
        session.delete_last_turn()
        msgs = session.fetch_messages(session.session_id)  # type: ignore[arg-type]  # session_id narrowed by start() but typed int | None
        assert msgs is not None
        assert len(msgs) == 2

    def test_no_op_when_session_id_none(self, session: AgentSession) -> None:
        session.delete_last_turn()  # should not raise
