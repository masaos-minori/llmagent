"""
tests/test_session_message_repo.py
Direct unit tests for SessionMessageRepository.

Uses the same in-memory SQLite pattern as test_agent_session.py.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Generator
from unittest.mock import patch

import pytest
from agent.session_message_repo import SessionMessageRepository

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS messages (
    message_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
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

    def executemany(self, sql: str, params_seq: list) -> sqlite3.Cursor:
        return self._conn.executemany(sql, params_seq)

    def fetchall(self, sql: str, params: tuple | dict = ()) -> list:
        return self._conn.execute(sql, params).fetchall()

    def commit(self) -> None:
        self._conn.commit()

    def close(self) -> None:
        pass

    def __enter__(self) -> _FakeSQLiteHelper:
        return self

    def __exit__(self, *_: object) -> None:
        pass


@pytest.fixture
def repo() -> Generator[SessionMessageRepository]:
    conn = sqlite3.connect(":memory:")
    conn.executescript(_SCHEMA_SQL)
    conn.commit()

    def _make(target: str = "rag") -> _FakeSQLiteHelper:
        return _FakeSQLiteHelper(conn)

    with patch("agent.session_message_repo.SQLiteHelper", side_effect=_make):
        yield SessionMessageRepository(session_id=1)


class TestSave:
    def test_saves_user_message(self, repo: SessionMessageRepository) -> None:
        repo.save("user", "Hello")
        msgs = repo.fetch_messages(1)
        assert msgs is not None  # non-empty list
        assert len(msgs) == 1
        assert msgs[0]["role"] == "user"
        assert msgs[0]["content"] == "Hello"

    def test_saves_assistant_with_tool_calls(
        self, repo: SessionMessageRepository
    ) -> None:
        repo.save("assistant", "", tool_calls=[{"id": "call_1", "type": "function"}])
        msgs = repo.fetch_messages(1)
        assert msgs is not None  # non-empty list
        assert len(msgs) == 1
        assert msgs[0]["tool_calls"] == [{"id": "call_1", "type": "function"}]

    def test_saves_tool_with_tool_call_id(self, repo: SessionMessageRepository) -> None:
        repo.save("tool", "result", tool_call_id="call_1")
        msgs = repo.fetch_messages(1)
        assert msgs is not None  # non-empty list
        assert msgs[0]["role"] == "tool"
        assert msgs[0]["tool_call_id"] == "call_1"

    def test_noop_when_session_id_none(self) -> None:
        r = SessionMessageRepository(session_id=None)
        with patch("agent.session_message_repo.SQLiteHelper") as mock_helper:
            r.save("user", "should not save")
            mock_helper.assert_not_called()

    def test_skips_invalid_role(self, repo: SessionMessageRepository) -> None:
        repo.save("invalid_role", "data")
        msgs = repo.fetch_messages(1)
        assert msgs == []

    def test_handles_db_exception_gracefully(
        self, repo: SessionMessageRepository
    ) -> None:
        with patch("agent.session_message_repo.SQLiteHelper") as mock:
            mock.return_value.open.return_value.__enter__.return_value.execute.side_effect = sqlite3.OperationalError(
                "DB fail"
            )
            with pytest.raises(sqlite3.OperationalError):
                repo.save("user", "data")


class TestSaveMany:
    def test_saves_multiple_messages(self, repo: SessionMessageRepository) -> None:
        messages = [
            ("user", "Hello", None, None),
            ("assistant", "Hi", None, None),
            ("tool", "data", None, "call_1"),
        ]
        repo.save_many(messages)
        msgs = repo.fetch_messages(1)
        assert msgs is not None  # non-empty list
        assert len(msgs) == 3

    def test_skips_invalid_roles(self, repo: SessionMessageRepository) -> None:
        messages = [
            ("user", "valid", None, None),
            ("bad_role", "invalid", None, None),
        ]
        repo.save_many(messages)
        msgs = repo.fetch_messages(1)
        assert msgs is not None  # non-empty list
        assert len(msgs) == 1
        assert msgs[0]["content"] == "valid"

    def test_noop_when_session_id_none(self) -> None:
        r = SessionMessageRepository(session_id=None)
        with patch("agent.session_message_repo.SQLiteHelper") as mock_helper:
            r.save_many([("user", "x", None, None)])
            mock_helper.assert_not_called()

    def test_noop_when_empty_list(self, repo: SessionMessageRepository) -> None:
        repo.save_many([])
        assert repo.fetch_messages(1) == []

    def test_serializes_tool_calls(self, repo: SessionMessageRepository) -> None:
        repo.save_many(
            [
                ("assistant", "", [{"id": "c1"}], None),
            ]
        )
        msgs = repo.fetch_messages(1)
        assert msgs is not None  # non-empty list
        assert msgs[0]["tool_calls"] == [{"id": "c1"}]

    def test_handles_db_exception_gracefully(
        self, repo: SessionMessageRepository
    ) -> None:
        messages = [("user", "data", None, None)]
        with patch("agent.session_message_repo.SQLiteHelper") as mock:
            mock.return_value.open.return_value.__enter__.return_value.executemany.side_effect = sqlite3.OperationalError(
                "DB fail"
            )
            with pytest.raises(sqlite3.OperationalError):
                repo.save_many(messages)

    def test_all_invalid_roles_returns_early(
        self, repo: SessionMessageRepository
    ) -> None:
        repo.save_many([("bad", "x", None, None)])
        assert repo.fetch_messages(1) == []


@pytest.fixture
def strict_repo() -> Generator[SessionMessageRepository]:
    conn = sqlite3.connect(":memory:")
    conn.executescript(_SCHEMA_SQL)
    conn.commit()

    def _make(target: str = "rag") -> _FakeSQLiteHelper:
        return _FakeSQLiteHelper(conn)

    with patch("agent.session_message_repo.SQLiteHelper", side_effect=_make):
        yield SessionMessageRepository(session_id=1, strict_mode=True)


class TestCountersAndStrictMode:
    def test_save_increments_no_session_counter(self) -> None:
        r = SessionMessageRepository(session_id=None)
        r.save("user", "hello")
        assert r.stat_skipped_no_session == 1

    def test_save_increments_invalid_role_counter(
        self, repo: SessionMessageRepository
    ) -> None:
        repo.save("bad_role", "x")
        assert repo.stat_skipped_invalid_role == 1

    def test_save_many_increments_no_session_counter(self) -> None:
        r = SessionMessageRepository(session_id=None)
        r.save_many([("user", "x", None, None)])
        assert r.stat_skipped_no_session == 1

    def test_save_many_increments_invalid_role_counter(
        self, repo: SessionMessageRepository
    ) -> None:
        repo.save_many([("bad", "x", None, None)])
        assert repo.stat_skipped_invalid_role == 1

    def test_strict_mode_save_raises_on_no_session(self) -> None:
        r = SessionMessageRepository(session_id=None, strict_mode=True)
        with pytest.raises(RuntimeError, match="no session_id"):
            r.save("user", "hello")

    def test_strict_mode_save_raises_on_invalid_role(
        self, strict_repo: SessionMessageRepository
    ) -> None:
        with pytest.raises(RuntimeError, match="invalid role"):
            strict_repo.save("bad_role", "x")

    def test_strict_mode_save_many_raises_on_no_session(self) -> None:
        r = SessionMessageRepository(session_id=None, strict_mode=True)
        with pytest.raises(RuntimeError, match="no session_id"):
            r.save_many([("user", "x", None, None)])

    def test_non_strict_mode_does_not_raise(
        self, repo: SessionMessageRepository
    ) -> None:
        repo.save("invalid_role", "x")  # must not raise
        assert repo.stat_skipped_invalid_role == 1


class TestFetchMessages:
    def test_returns_empty_when_session_not_found(
        self, repo: SessionMessageRepository
    ) -> None:
        assert repo.fetch_messages(999) == []

    def test_returns_messages_in_order(self, repo: SessionMessageRepository) -> None:
        repo.save("user", "first")
        repo.save("assistant", "second")
        msgs = repo.fetch_messages(1)
        assert msgs is not None  # non-empty list
        assert msgs[0]["content"] == "first"
        assert msgs[1]["content"] == "second"

    def test_handles_invalid_tool_calls_json(
        self, repo: SessionMessageRepository
    ) -> None:
        import logging

        logging.disable(logging.WARNING)
        conn = sqlite3.connect(":memory:")
        conn.executescript(_SCHEMA_SQL)
        conn.execute(
            "INSERT INTO messages (session_id, role, content, tool_calls) VALUES (?, ?, ?, ?)",
            (1, "assistant", "", "not valid json"),
        )
        conn.commit()

        def _make(target: str = "rag") -> _FakeSQLiteHelper:
            return _FakeSQLiteHelper(conn)

        with patch("agent.session_message_repo.SQLiteHelper", side_effect=_make):
            r = SessionMessageRepository(session_id=1)
            msgs = r.fetch_messages(1)
        logging.disable(logging.NOTSET)
        assert msgs is not None  # non-empty list
        assert "tool_calls" not in msgs[0]

    def test_invalid_role_skipped_in_fetch(
        self, repo: SessionMessageRepository
    ) -> None:
        repo.save("user", "hello")
        repo.save("assistant", "world")
        msgs = repo.fetch_messages(1)
        assert len(msgs) == 2
        assert msgs[0]["role"] == "user"
        assert msgs[1]["role"] == "assistant"

    def test_handles_db_exception_raises(self, repo: SessionMessageRepository) -> None:
        with patch("agent.session_message_repo.SQLiteHelper") as mock:
            mock.side_effect = sqlite3.OperationalError("DB Error")
            with pytest.raises(sqlite3.OperationalError):
                repo.fetch_messages(1)


class TestNoneContentNormalization:
    """Tests for None content normalization at the repository boundary."""

    def test_save_assistant_with_none_content(
        self, repo: SessionMessageRepository
    ) -> None:
        """assistant message with content=None is saved and restored as empty string."""
        repo.save("assistant", None, tool_calls=[{"id": "call_1", "type": "function"}])
        msgs = repo.fetch_messages(1)
        assert msgs is not None
        assert len(msgs) == 1
        assert msgs[0]["content"] == ""
        assert msgs[0]["tool_calls"] == [{"id": "call_1", "type": "function"}]

    def test_save_assistant_with_none_content_no_tool_calls(
        self, repo: SessionMessageRepository
    ) -> None:
        """assistant message with content=None and no tool_calls is saved as empty string."""
        repo.save("assistant", None)
        msgs = repo.fetch_messages(1)
        assert msgs is not None
        assert len(msgs) == 1
        assert msgs[0]["content"] == ""

    def test_save_many_with_one_none_content(
        self, repo: SessionMessageRepository
    ) -> None:
        """save_many with one message having content=None normalizes it to empty string."""
        messages = [
            ("user", "Hello", None, None),
            ("assistant", None, [{"id": "call_1"}], None),
            ("tool", "result", None, "call_1"),
        ]
        repo.save_many(messages)
        msgs = repo.fetch_messages(1)
        assert msgs is not None
        assert len(msgs) == 3
        assert msgs[0]["content"] == "Hello"
        assert msgs[1]["content"] == ""
        assert msgs[2]["content"] == "result"

    def test_save_many_all_none_contents(self, repo: SessionMessageRepository) -> None:
        """save_many where all messages have content=None normalizes all to empty strings."""
        messages = [
            ("assistant", None, [{"id": "call_1"}], None),
            ("assistant", None, [{"id": "call_2"}], None),
        ]
        repo.save_many(messages)
        msgs = repo.fetch_messages(1)
        assert msgs is not None
        assert len(msgs) == 2
        assert msgs[0]["content"] == ""
        assert msgs[1]["content"] == ""

    def test_save_with_empty_string_preserved(
        self, repo: SessionMessageRepository
    ) -> None:
        """Empty string content is preserved as-is (not changed to None)."""
        repo.save("assistant", "")
        msgs = repo.fetch_messages(1)
        assert msgs is not None
        assert len(msgs) == 1
        assert msgs[0]["content"] == ""

    def test_save_with_normal_string_preserved(
        self, repo: SessionMessageRepository
    ) -> None:
        """Normal string content is preserved unchanged."""
        repo.save("assistant", "Hello world")
        msgs = repo.fetch_messages(1)
        assert msgs is not None
        assert len(msgs) == 1
        assert msgs[0]["content"] == "Hello world"

    def test_save_many_mixed_none_and_string_contents(
        self, repo: SessionMessageRepository
    ) -> None:
        """save_many with mix of None and string contents preserves strings, normalizes None."""
        messages = [
            ("assistant", None, [{"id": "call_1"}], None),
            ("assistant", "response", None, None),
            ("user", "Follow-up", None, None),
        ]
        repo.save_many(messages)
        msgs = repo.fetch_messages(1)
        assert msgs is not None
        assert len(msgs) == 3
        assert msgs[0]["content"] == ""
        assert msgs[1]["content"] == "response"
        assert msgs[2]["content"] == "Follow-up"

    def test_strict_mode_save_with_none_content_does_not_raise(
        self, strict_repo: SessionMessageRepository
    ) -> None:
        """None content does not raise in strict mode; it is normalized to empty string."""
        strict_repo.save("assistant", None, tool_calls=[{"id": "call_1"}])
        msgs = strict_repo.fetch_messages(1)
        assert msgs is not None
        assert len(msgs) == 1
        assert msgs[0]["content"] == ""

    def test_strict_mode_save_many_with_none_content(
        self, strict_repo: SessionMessageRepository
    ) -> None:
        """None content in save_many does not raise in strict mode."""
        messages = [
            ("assistant", None, [{"id": "call_1"}], None),
            ("user", "Hello", None, None),
        ]
        strict_repo.save_many(messages)
        msgs = strict_repo.fetch_messages(1)
        assert msgs is not None
        assert len(msgs) == 2
        assert msgs[0]["content"] == ""
        assert msgs[1]["content"] == "Hello"


class TestReplaceMessages:
    """Tests for SessionMessageRepository.replace_messages()."""

    def test_replace_messages_clears_existing_rows(
        self, repo: SessionMessageRepository
    ) -> None:
        repo.save("user", "old")
        assert len(repo.fetch_messages(1)) == 1
        repo.replace_messages(1, [{"role": "assistant", "content": "new"}])
        msgs = repo.fetch_messages(1)
        assert len(msgs) == 1
        assert msgs[0]["content"] == "new"

    def test_replace_messages_inserts_compressed_set(
        self, repo: SessionMessageRepository
    ) -> None:
        msgs_in = [
            {"role": "system", "content": "summary"},
            {"role": "user", "content": "user msg"},
            {"role": "assistant", "content": "assistant msg"},
        ]
        repo.replace_messages(1, msgs_in)
        assert len(repo.fetch_messages(1)) == 3

    def test_replace_messages_with_summary_message(
        self, repo: SessionMessageRepository
    ) -> None:
        repo.replace_messages(
            1, [{"role": "system", "content": "[Conversation summary]"}]
        )
        msgs = repo.fetch_messages(1)
        assert len(msgs) == 1
        assert msgs[0]["role"] == "system"
        assert "[Conversation summary]" in msgs[0]["content"]

    def test_replace_messages_no_session_id_skips(self) -> None:
        import sqlite3
        from unittest.mock import patch

        conn = sqlite3.connect(":memory:")
        conn.executescript(_SCHEMA_SQL)
        conn.commit()

        def _make(target: str = "session") -> _FakeSQLiteHelper:
            return _FakeSQLiteHelper(conn)

        from agent.session import AgentSession

        with patch("agent.session_message_repo.SQLiteHelper", side_effect=_make):
            with patch("agent.session.SQLiteHelper", side_effect=_make):
                agent_session = AgentSession()
                agent_session.replace_messages([{"role": "user", "content": "test"}])

    def test_replace_messages_with_tool_calls(
        self, repo: SessionMessageRepository
    ) -> None:
        """replace_messages() correctly serializes tool_calls."""
        msgs = [
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [{"id": "call_1", "type": "function"}],
            }
        ]
        repo.replace_messages(1, msgs)
        rows = repo.fetch_messages(1)
        assert len(rows) == 1
        assert rows[0]["tool_calls"] == [{"id": "call_1", "type": "function"}]

    def test_replace_messages_empty_list_skips(self, repo: SessionMessageRepository) -> None:
        """replace_messages() with empty list does nothing."""
        repo.save("user", "existing")
        assert len(repo.fetch_messages(1)) == 1
        repo.replace_messages(1, [])
        assert len(repo.fetch_messages(1)) == 1

    def test_replace_messages_deletes_all_then_inserts(
        self, repo: SessionMessageRepository
    ) -> None:
        """replace_messages() fully replaces all messages — old rows are gone."""
        repo.save("user", "old1")
        repo.save("assistant", "old2")
        repo.save("tool", "old3", tool_call_id="call_1")
        assert len(repo.fetch_messages(1)) == 3
        new_msgs = [
            {"role": "system", "content": "[Conversation summary]"},
            {"role": "user", "content": "new user"},
        ]
        repo.replace_messages(1, new_msgs)
        rows = repo.fetch_messages(1)
        assert len(rows) == 2
        assert rows[0]["content"] == "[Conversation summary]"
        assert rows[1]["content"] == "new user"
