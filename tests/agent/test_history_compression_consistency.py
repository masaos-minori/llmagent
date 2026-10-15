"""tests/test_history_compression_consistency.py
History compression/undo consistency tests.

Locks down: replace_messages() atomicity after compression, undo_last_turn()
behavior on compressed history, and fallback truncation in-memory contract.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Generator
from types import SimpleNamespace
from typing import cast
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from agent.commands.cmd_rag_export import _RagExportMixin
from agent.context import AgentContext, ConversationState
from agent.conversation_state_manager import ConversationStateManager
from agent.history import HistoryManager
from agent.services.undo_service import undo_last_turn
from agent.session import AgentSession
from agent.session_message_repo import SessionMessageRepository
from shared.types import LLMMessage


def _msgs(result):
    """Unwrap (messages, session_found) tuple returned by fetch_messages."""
    if isinstance(result, tuple):
        return result[0]
    return result


_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS sessions (
    session_id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    title TEXT,
    undo_floor_message_id INTEGER NOT NULL DEFAULT 0
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
    conn.execute("INSERT INTO sessions (session_id) VALUES (1)")
    conn.commit()
    fake = _FakeSQLiteHelper(conn)

    with patch("agent.session_message_repo.SQLiteHelper", return_value=fake):
        yield SessionMessageRepository(session_id=1)


@pytest.fixture
def session_and_conn() -> Generator[tuple[AgentSession, sqlite3.Connection]]:
    conn = sqlite3.connect(":memory:")
    conn.executescript(_SCHEMA_SQL)
    conn.execute("INSERT INTO sessions (session_id) VALUES (1)")
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

    loaded = _msgs(repo.fetch_messages(1))
    assert len(loaded) == 1
    assert loaded[0]["content"] == "[SUMMARY] compressed"


def test_reload_after_compression_no_original_rows_remain(
    repo: SessionMessageRepository,
) -> None:
    """replace_messages() must remove ALL prior rows for the session."""
    for msg in _make_history(3):
        repo.save(msg["role"], msg["content"])

    repo.replace_messages(1, [{"role": "assistant", "content": "[SUMMARY]"}])

    loaded = _msgs(repo.fetch_messages(1))
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
    loaded = _msgs(repo.fetch_messages(1))
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

    loaded = _msgs(session.fetch_messages(1))
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
    loaded = _msgs(session.fetch_messages(1))
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
    loaded = _msgs(repo.fetch_messages(1))
    assert len(loaded) == len(compressed_messages)


# --- Compression entry points establish the /undo boundary (rows 08/09) ---


def _compression_ctx(
    session: AgentSession,
    history: list[LLMMessage],
    *,
    force: bool,
) -> object:
    """Build a minimal ctx driving a compression entry point.

    ``session`` is backed by a real (patched) in-memory DB so that
    ``replace_messages()`` persists the boundary; ``hist_mgr`` is stubbed to
    return a compressed result with ``compressed_count > 0``.
    """
    conv = ConversationState()
    conv.history = list(history)
    conv.undo_floor = 0
    conv.system_prompt_content = ""
    result = SimpleNamespace(compressed_count=1, summary_added=True, is_fallback=False)
    if force:
        hist_mgr = SimpleNamespace(
            compress_turns=2,
            force_compress=AsyncMock(return_value=(list(history), result)),
        )
    else:
        hist_mgr = SimpleNamespace(
            compress=AsyncMock(return_value=(list(history), result)),
        )
    return SimpleNamespace(
        conv=conv,
        session=session,
        services_required=SimpleNamespace(hist_mgr=hist_mgr),
    )


async def test_manager_path_sets_undo_floor_to_snapshot_length(
    session_and_conn: tuple[AgentSession, sqlite3.Connection],
) -> None:
    session, conn = session_and_conn
    history = _make_history(4)  # 8 messages
    ctx = cast(AgentContext, _compression_ctx(session, history, force=False))
    mgr = ConversationStateManager(ctx, tasks=set(), on_discard=lambda t: None)
    await mgr.handle_history_compression()
    assert ctx.conv.undo_floor == len(history)
    boundary = conn.execute(
        "SELECT undo_floor_message_id FROM sessions WHERE session_id = 1"
    ).fetchone()[0]
    assert boundary == len(history)


async def test_compact_path_sets_undo_floor_to_snapshot_length(
    session_and_conn: tuple[AgentSession, sqlite3.Connection],
) -> None:
    session, conn = session_and_conn
    history = _make_history(4)  # 8 messages
    ctx = cast(AgentContext, _compression_ctx(session, history, force=True))
    mixin = _RagExportMixin()
    mixin._ctx = ctx
    mixin._out = MagicMock()
    await mixin._cmd_compact()
    assert ctx.conv.undo_floor == len(history)
    boundary = conn.execute(
        "SELECT undo_floor_message_id FROM sessions WHERE session_id = 1"
    ).fetchone()[0]
    assert boundary == len(history)


# --- /undo gated by the boundary (rows 02/03) ---


def _gate_ctx(
    session: AgentSession,
    history: list[LLMMessage],
    *,
    undo_floor: int,
    db_floor: int,
) -> object:
    conv = ConversationState()
    conv.history = list(history)
    conv.undo_floor = undo_floor
    conv.system_prompt_content = ""
    return SimpleNamespace(
        conv=conv,
        session=session,
        stats=SimpleNamespace(stat_turns=0),
        services_required=SimpleNamespace(),
    )


async def test_undo_blocked_when_last_user_at_boundary(
    session_and_conn: tuple[AgentSession, sqlite3.Connection],
) -> None:
    session, conn = session_and_conn
    history = _make_history(2)  # [q0,a0,q1,a1], ids 1..4
    for m in history:
        session.save(m["role"], m["content"])  # type: ignore[arg-type]  # test messages always carry string content
    # In-memory floor lets the search reach q1 (idx 2); DB floor at id 3 blocks it.
    ctx = cast(AgentContext, _gate_ctx(session, history, undo_floor=2, db_floor=3))
    conn.execute("UPDATE sessions SET undo_floor_message_id = 3 WHERE session_id = 1")
    result = undo_last_turn(ctx)
    assert result.block_reason is not None
    assert result.n_removed == 0
    assert len(ctx.conv.history) == 4  # history untouched
    remaining = conn.execute(
        "SELECT COUNT(*) FROM messages WHERE session_id = 1"
    ).fetchone()[0]
    assert remaining == 4


async def test_undo_after_boundary_removes_turn_from_history_and_db(
    session_and_conn: tuple[AgentSession, sqlite3.Connection],
) -> None:
    session, conn = session_and_conn
    history = _make_history(2)  # [q0,a0,q1,a1], ids 1..4
    for m in history:
        session.save(m["role"], m["content"])  # type: ignore[arg-type]  # test messages always carry string content
    ctx = cast(AgentContext, _gate_ctx(session, history, undo_floor=2, db_floor=2))
    conn.execute("UPDATE sessions SET undo_floor_message_id = 2 WHERE session_id = 1")
    result = undo_last_turn(ctx)
    assert result.block_reason is None
    assert result.n_removed == 2
    assert [m["content"] for m in ctx.conv.history] == [
        "User message 0",
        "Assistant reply 0",
    ]
    remaining = conn.execute(
        "SELECT COUNT(*) FROM messages WHERE session_id = 1"
    ).fetchone()[0]
    assert remaining == 2
