"""tests/test_history_compression_consistency.py
History compression/undo consistency tests.

Locks down: replace_messages() atomicity after compression, undo_last_turn()
behavior on compressed history, and fallback truncation in-memory contract.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Generator
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from agent.history import HistoryManager
from agent.session import AgentSession
from agent.session_message_repo import SessionMessageRepository
from shared.types import LLMMessage

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS sessions (
    session_id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    title TEXT
);
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
    fake = _FakeSQLiteHelper(conn)

    with patch("agent.session_message_repo.SQLiteHelper", return_value=fake):
        yield SessionMessageRepository(session_id=1)


@pytest.fixture
def session_and_conn() -> Generator[tuple[AgentSession, sqlite3.Connection]]:
    conn = sqlite3.connect(":memory:")
    conn.executescript(_SCHEMA_SQL)
    conn.commit()
    fake = _FakeSQLiteHelper(conn)

    with (
        patch("agent.session.SQLiteHelper", return_value=fake),
        patch("agent.session_message_repo.SQLiteHelper", return_value=fake),
    ):
        s = AgentSession()
        s.session_id = 1
        s._message_repo = SessionMessageRepository(session_id=1)
        yield s, conn


def _make_history(n_turns: int) -> list[LLMMessage]:
    messages: list[LLMMessage] = []
    for i in range(n_turns):
        messages.append({"role": "user", "content": f"User message {i}"})
        messages.append({"role": "assistant", "content": f"Assistant reply {i}"})
    return messages


def _make_manager(char_limit: int = 1) -> HistoryManager:
    return HistoryManager(
        http=AsyncMock(spec=httpx.AsyncClient),
        llm_url="http://localhost:8002/v1/chat/completions",
        char_limit=char_limit,
        compress_turns=2,
        compress_temperature=0.1,
        compress_max_tokens=200,
        protect_turns=0,
    )


# --- Compression -> reload ---


def test_reload_after_compression_restores_compressed_history(
    repo: SessionMessageRepository,
) -> None:
    """After replace_messages(), fetch_messages() must return only the summary."""
    for msg in _make_history(5):
        repo.save(msg["role"], msg["content"])

    summary_msg: LLMMessage = {"role": "assistant", "content": "[SUMMARY] compressed"}
    repo.replace_messages(1, [summary_msg])

    loaded = repo.fetch_messages(1)
    assert len(loaded) == 1
    assert loaded[0]["content"] == "[SUMMARY] compressed"


def test_reload_after_compression_no_original_rows_remain(
    repo: SessionMessageRepository,
) -> None:
    """replace_messages() must remove ALL prior rows for the session."""
    for msg in _make_history(3):
        repo.save(msg["role"], msg["content"])

    repo.replace_messages(1, [{"role": "assistant", "content": "[SUMMARY]"}])

    loaded = repo.fetch_messages(1)
    assert all("[SUMMARY]" in m["content"] for m in loaded)


def test_replace_messages_preserves_role_sequence(
    repo: SessionMessageRepository,
) -> None:
    for msg in _make_history(2):
        repo.save(msg["role"], msg["content"])
    compressed: list[LLMMessage] = [
        {"role": "user", "content": "summarized user context"},
        {"role": "assistant", "content": "[SUMMARY]"},
    ]
    repo.replace_messages(1, compressed)
    loaded = repo.fetch_messages(1)
    assert [m["role"] for m in loaded] == ["user", "assistant"]


# --- /undo after compression ---


def test_undo_after_compression_removes_summary_message(
    session_and_conn: tuple[AgentSession, sqlite3.Connection],
) -> None:
    """/undo after compression removes the user+summary turn from DB."""
    session, conn = session_and_conn
    conn.execute(
        "INSERT INTO messages (session_id, role, content) VALUES (1, 'user', 'user')"
    )
    conn.execute(
        "INSERT INTO messages (session_id, role, content) VALUES (1, 'assistant', '[SUMMARY]')"
    )
    conn.commit()

    session.undo_last_turn()

    loaded = session.fetch_messages(1)
    assert not any("[SUMMARY]" in m.get("content", "") for m in loaded)


def test_undo_on_single_compressed_message_is_safe(
    session_and_conn: tuple[AgentSession, sqlite3.Connection],
) -> None:
    """Undo when only the assistant summary remains (no user row) is a no-op."""
    session, conn = session_and_conn
    conn.execute(
        "INSERT INTO messages (session_id, role, content) VALUES (1, 'assistant', '[SUMMARY]')"
    )
    conn.commit()

    deleted = session.undo_last_turn()

    assert deleted == 0
    loaded = session.fetch_messages(1)
    assert len(loaded) == 1


# --- Undo invariants ---


def test_undo_last_turn_returns_deleted_count(
    session_and_conn: tuple[AgentSession, sqlite3.Connection],
) -> None:
    """undo_last_turn() returns the number of rows deleted."""
    session, conn = session_and_conn
    conn.execute(
        "INSERT INTO messages (session_id, role, content) VALUES (1, 'user', 'q')"
    )
    conn.execute(
        "INSERT INTO messages (session_id, role, content) VALUES (1, 'assistant', 'a')"
    )
    conn.commit()

    deleted = session.undo_last_turn()
    assert deleted == 2


def test_undo_empty_session_returns_zero(
    session_and_conn: tuple[AgentSession, sqlite3.Connection],
) -> None:
    """undo_last_turn() on an empty session returns 0 without raising."""
    session, _ = session_and_conn
    deleted = session.undo_last_turn()
    assert deleted == 0


# --- Fallback truncation (in-memory only) ---


def test_fallback_truncation_reduces_history_size() -> None:
    """_fallback_truncate() returns a shorter history; operates in-memory only."""
    mgr = _make_manager(char_limit=100)
    history = _make_history(10)  # 20 messages, well over 100 chars
    new_history, result = mgr._fallback_truncate(history)
    assert len(new_history) < len(history)
    assert result.is_fallback is True


def test_fallback_truncation_result_flags() -> None:
    """_fallback_truncate() returns is_fallback=True and summary_added=False."""
    mgr = _make_manager(char_limit=100)
    history = _make_history(5)
    _, result = mgr._fallback_truncate(history)
    assert result.is_fallback is True
    assert result.summary_added is False


# --- Message count invariants ---


def test_compress_result_count_matches_replace(repo: SessionMessageRepository) -> None:
    """Number of messages passed to replace_messages() must match fetch_messages() output."""
    for msg in _make_history(4):
        repo.save(msg["role"], msg["content"])

    compressed_messages: list[LLMMessage] = [
        {"role": "assistant", "content": "[SUMMARY of 8 messages]"}
    ]
    repo.replace_messages(1, compressed_messages)
    loaded = repo.fetch_messages(1)
    assert len(loaded) == len(compressed_messages)
