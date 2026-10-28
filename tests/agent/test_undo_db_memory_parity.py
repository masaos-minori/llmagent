"""tests/agent/test_undo_db_memory_parity.py

Regression module for the `/undo` memory/DB parity contract (REQ-007).

Proves that undo trims memory history to exactly the rows the DB deletes, that
the row-list return type and boundary gate behave (REQ-001), that an ambiguous
match (orphan DB tail absent from memory) triggers a reload-from-DB fallback
with a logged decision (REQ-003), and that a memory-only injected block is
trimmed along with its turn on the primary path (REQ-002).
"""

from __future__ import annotations

import logging
import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass
from threading import Lock
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from agent.services import undo_service
from agent.services.models import DeletedRow, UndoResult
from agent.session import AgentSession

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS sessions (
    session_id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    title TEXT,
    undo_floor_message_id INTEGER NOT NULL DEFAULT 0
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


@dataclass
class _Env:
    conn: sqlite3.Connection
    session: AgentSession
    sid: int


@pytest.fixture(autouse=True)
def reset_fake_helper() -> Generator[None]:
    _FakeSQLiteHelper.reset()
    yield


@pytest.fixture
def env() -> Generator[_Env]:
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(_SCHEMA_SQL)
    conn.execute("INSERT INTO sessions (session_id) VALUES (1)")
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
        yield _Env(conn, s, s.session_id)


def _ctx(
    sess: AgentSession, history: list[dict], undo_floor: int = 0
) -> SimpleNamespace:
    """Build a minimal AgentContext-like object for undo_service.undo_last_turn."""
    return SimpleNamespace(
        conv=SimpleNamespace(history=history, undo_floor=undo_floor),
        session=sess,
        stats=SimpleNamespace(stat_turns=len(history)),
    )


def _contents(sess: AgentSession, sid: int) -> list[str]:
    messages, _found, _floor = sess.fetch_messages(sid)
    return [m["content"] for m in messages]


class TestUndoParity:
    def test_parity_restored_after_orphan_divergence(self, env: _Env) -> None:
        """T-001 (REQ-007): an orphan DB tail row absent from memory makes undo
        reload memory from the DB, so history equals the remaining DB rows."""
        sid = env.sid
        env.session.save_many(
            [
                ("user", "q1", None, None),
                ("assistant", "a1", None, None),
                ("user", "q2", None, None),
                ("assistant", "a2", None, None),
            ]
        )
        # Orphan tool row in the DB tail only (absent from memory).
        env.conn.execute(
            "INSERT INTO messages (session_id, role, content, tool_call_id)"
            " VALUES (?, 'tool', 'orphan-result', 'tcX')",
            (sid,),
        )
        env.conn.commit()

        history = [
            {"role": "user", "content": "q1"},
            {"role": "assistant", "content": "a1"},
            {"role": "user", "content": "q2"},
            {"role": "assistant", "content": "a2"},
        ]
        ctx = _ctx(env.session, history)

        result = undo_service.undo_last_turn(ctx)

        assert isinstance(result, UndoResult)
        assert not result.block_reason
        assert len(result.deleted_rows) == 3  # q2, a2, orphan
        remaining = _contents(env.session, sid)
        # Memory reloaded from DB: both sides now hold q1, a1.
        assert [m["content"] for m in ctx.conv.history] == remaining
        assert remaining == ["q1", "a1"]

    def test_row_list_return_and_boundary_gate(self, env: _Env) -> None:
        """T-002 (REQ-001): healthy undo returns an ascending row list; a turn at
        or before the boundary returns an empty list."""
        sid = env.sid
        env.session.save_many(
            [
                ("user", "q1", None, None),
                ("assistant", "a1", None, None),
                ("user", "q2", None, None),
                ("assistant", "a2", None, None),
            ]
        )
        history = [
            {"role": "user", "content": "q1"},
            {"role": "assistant", "content": "a1"},
            {"role": "user", "content": "q2"},
            {"role": "assistant", "content": "a2"},
        ]

        healthy = undo_service.undo_last_turn(_ctx(env.session, history))
        deleted: list[DeletedRow] = healthy.deleted_rows
        assert len(deleted) == 2
        ids = [r.message_id for r in deleted]
        assert ids == sorted(ids)  # ascending message_id
        # Parity holds: memory trimmed to the same two pre-turn rows as the DB.
        assert len(_contents(env.session, sid)) == 2

        # Boundary gate: floor at id 3 (q2) blocks the last user turn.
        env.conn.execute(
            "UPDATE sessions SET undo_floor_message_id = ? WHERE session_id = ?",
            (3, sid),
        )
        env.conn.commit()
        blocked = undo_service.undo_last_turn(_ctx(env.session, history, undo_floor=0))
        assert blocked.deleted_rows == []
        assert blocked.block_reason


class TestUndoReloadFallback:
    def test_ambiguous_match_reloads_and_logs(
        self, env: _Env, caplog: pytest.LogCaptureFixture
    ) -> None:
        """T-003 (REQ-003): when the DB tail cannot match the memory tail, undo
        reloads memory from the DB and logs a warning naming the deleted ids."""
        sid = env.sid
        env.session.save_many(
            [
                ("user", "q1", None, None),
                ("assistant", "a1", None, None),
                ("user", "q2", None, None),
                ("assistant", "a2", None, None),
            ]
        )
        env.conn.execute(
            "INSERT INTO messages (session_id, role, content, tool_call_id)"
            " VALUES (?, 'tool', 'orphan-result', 'tcX')",
            (sid,),
        )
        env.conn.commit()

        history = [
            {"role": "user", "content": "q1"},
            {"role": "assistant", "content": "a1"},
            {"role": "user", "content": "q2"},
            {"role": "assistant", "content": "a2"},
        ]
        caplog.at_level(logging.WARNING, logger="agent.services.undo_service")

        ctx = _ctx(env.session, history)
        undo_service.undo_last_turn(ctx)

        remaining = _contents(env.session, sid)
        # Reload fallback fired: memory now equals the remaining DB rows.
        assert [m["content"] for m in ctx.conv.history] == remaining
        assert remaining == ["q1", "a1"]
        # The decision was logged at WARNING with the deleted ids.
        assert any(
            "ambiguous" in r.message
            for r in caplog.records
            if r.levelno == logging.WARNING
        )


class TestUndoArtifactTrim:
    def test_injected_block_trimmed_on_primary_path(self, env: _Env) -> None:
        """T-004 (REQ-002): a memory-only _memory_injected block immediately before
        the last user turn is trimmed along with that turn on the matched path."""
        sid = env.sid
        env.session.save_many(
            [
                ("user", "q1", None, None),
                ("assistant", "a1", None, None),
                ("user", "q2", None, None),
                ("assistant", "a2", None, None),
            ]
        )
        # Injected memory block exists in memory only, just before the last turn.
        history = [
            {"role": "user", "content": "q1"},
            {"role": "assistant", "content": "a1"},
            {"role": "user", "content": "", "_memory_injected": True},
            {"role": "user", "content": "q2"},
            {"role": "assistant", "content": "a2"},
        ]

        ctx = _ctx(env.session, history)
        result = undo_service.undo_last_turn(ctx)

        assert not result.block_reason
        # Primary (matched) path trims the injected block together with the turn.
        assert [m.get("role") for m in ctx.conv.history] == ["user", "assistant"]
        assert all("_memory_injected" not in m for m in ctx.conv.history)
        # Parity: DB also holds exactly q1, a1.
        assert _contents(env.session, sid) == ["q1", "a1"]
