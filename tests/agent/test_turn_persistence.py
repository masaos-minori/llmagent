"""
tests/agent/test_turn_persistence.py

End-to-end tests for the turn-persistence boundary
(``scripts/agent/turn_persistence.py``): per-phase commit on the happy path,
the single ``ConversationPersistenceError`` type on failure, compensation that
deletes exactly the failed turn's rows, and memory restore to the turn-start
snapshot (REQ-001..REQ-004).

Uses the same in-memory SQLite pattern as test_agent_session.py: a real
in-memory connection wrapped by a fake ``SQLiteHelper`` so no real DB file or
sqlite-vec extension is required.
"""

from __future__ import annotations

import sqlite3
import threading
from collections.abc import Generator
from contextlib import contextmanager
from unittest.mock import patch

import pytest
from agent.context import ConversationState
from agent.session import AgentSession
from agent.session_message_repo import SessionMessageRepository
from agent.turn_persistence import ConversationPersistenceError, TurnPersistence

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS sessions (
    session_id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    title TEXT,
    undo_floor_message_id INTEGER NOT NULL DEFAULT 0
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

_write_lock = threading.Lock()


class _FakeSQLiteHelper:
    """SQLiteHelper drop-in backed by a real in-memory connection.

    ``_state`` is a shared mutable holder (installed by ``_make``) whose
    ``fail_next`` counter injects exactly one ``sqlite3.DatabaseError`` to
    exercise the compensation path.
    """

    _initialized_conns: set[int] = set()

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn
        self._state: dict[str, int] | None = None

    def _guard(self) -> None:
        if self._state is not None and self._state["fail_next"] > 0:
            self._state["fail_next"] -= 1
            raise sqlite3.DatabaseError("injected turn-persistence failure")

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
        self._guard()
        return self._conn.execute(sql, params)

    def executemany(self, sql: str, params_seq: list) -> sqlite3.Cursor:
        self._guard()
        return self._conn.executemany(sql, params_seq)

    def fetchall(self, sql: str, params: tuple | dict = ()) -> list:
        return self._conn.execute(sql, params).fetchall()

    def commit(self) -> None:
        self._conn.commit()

    def close(self) -> None:
        pass  # keep alive for the test lifetime

    @contextmanager
    def begin_immediate(self) -> Generator[None]:
        self._guard()
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
    _FakeSQLiteHelper._initialized_conns.clear()
    yield


@pytest.fixture
def wired() -> Generator[tuple[sqlite3.Connection, dict[str, int]]]:
    """AgentSession + repo + in-memory DB; yields (connection, injector state)."""
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(_SCHEMA_SQL)
    conn.execute("INSERT INTO sessions (session_id) VALUES (1)")
    conn.commit()

    state: dict[str, int] = {"fail_next": 0}

    def _make(target: str = "rag") -> _FakeSQLiteHelper:  # noqa: ARG001 — target selects the fake's backing store but is unused in the body
        fake = _FakeSQLiteHelper(conn)
        fake._state = state
        return fake

    with (
        patch("agent.session.SQLiteHelper", side_effect=_make),
        patch("agent.session_message_repo.SQLiteHelper", side_effect=_make),
    ):
        yield conn, state


def _message_rows(conn: sqlite3.Connection) -> list[tuple[int, str, str]]:
    return [
        (mid, role, content)
        for mid, role, content in conn.execute(
            "SELECT message_id, role, content FROM messages ORDER BY message_id"
        ).fetchall()
    ]


async def _boundary(
    session: AgentSession, conv: ConversationState, marker: int
) -> TurnPersistence:
    snapshot = await conv.snapshot_messages()
    repo = SessionMessageRepository(session.session_id)
    session._message_repo = repo
    return TurnPersistence(session, conv, marker, snapshot)


# ── Happy path ────────────────────────────────────────────────────────────────


class TestHappyPath:
    async def test_save_phase_grouped_commits_rows(self, wired) -> None:
        conn, _state = wired
        session = AgentSession()
        session.session_id = 1
        conv = ConversationState()
        boundary = await _boundary(session, conv, marker=0)

        await boundary.save_phase_grouped(
            [
                ("assistant", "answer", None, None),
                ("tool", "result", None, "call-1"),
            ]
        )

        rows = _message_rows(conn)
        assert [role for _, role, _ in rows] == ["assistant", "tool"]
        assert rows[0][2] == "answer"
        assert rows[1][2] == "result"

    async def test_save_and_replace_messages_route_through_boundary(
        self, wired
    ) -> None:
        conn, _state = wired
        session = AgentSession()
        session.session_id = 1
        conv = ConversationState()
        boundary = await _boundary(session, conv, marker=0)

        await boundary.save("user", "hello")
        await boundary.replace_messages([{"role": "system", "content": "sys"}])

        roles = [role for _, role, _ in _message_rows(conn)]
        assert roles == ["system"]  # replace cleared the user row, inserted system


# ── Exception type ─────────────────────────────────────────────────────────────


class TestExceptionType:
    async def test_db_failure_surfaces_as_persistence_error(self, wired) -> None:
        _conn, state = wired
        session = AgentSession()
        session.session_id = 1
        conv = ConversationState()
        boundary = await _boundary(session, conv, marker=0)

        state["fail_next"] = 1
        with pytest.raises(ConversationPersistenceError) as exc_info:
            await boundary.save_phase_grouped([("assistant", "x", None, None)])

        # REQ-003: original sqlite3.Error chained on __cause__
        assert isinstance(exc_info.value.__cause__, sqlite3.Error)
        assert isinstance(exc_info.value.cause, sqlite3.Error)


# ── Compensation ───────────────────────────────────────────────────────────────


class TestCompensation:
    async def test_deletes_only_turn_rows_not_prior_turns(self, wired) -> None:
        conn, state = wired
        # Prior turns occupy message_id 1 and 2; this turn's marker is 2.
        conn.executemany(
            "INSERT INTO messages (session_id, role, content) VALUES (1, ?, ?)",
            [("user", "prior-1"), ("assistant", "prior-2")],
        )
        conn.commit()

        session = AgentSession()
        session.session_id = 1
        conv = ConversationState()
        conv.history = [
            {"role": "user", "content": "prior-1"},
            {"role": "assistant", "content": "prior-2"},
        ]
        boundary = await _boundary(session, conv, marker=2)

        # Phase 1 of the turn commits (single save autocommits): message_id 3.
        await boundary.save("user", "turn-3")
        assert [role for _, role, _ in _message_rows(conn)] == [
            "user",
            "assistant",
            "user",
        ]

        # Phase 2 fails; compensation must delete only the turn's row (id 3).
        state["fail_next"] = 1
        with pytest.raises(ConversationPersistenceError):
            await boundary.save_phase_grouped([("assistant", "p", None, None)])

        # AC-002: prior-turn rows (1,2) survive; zero of this turn's rows remain.
        rows = _message_rows(conn)
        assert [role for _, role, _ in rows] == ["user", "assistant"]
        assert rows[0][2] == "prior-1"
        assert rows[1][2] == "prior-2"

    async def test_compensation_leaves_zero_rows_for_fresh_turn(self, wired) -> None:
        conn, state = wired
        session = AgentSession()
        session.session_id = 1
        conv = ConversationState()
        boundary = await _boundary(session, conv, marker=0)

        # Two phases: first commits, second fails.
        await boundary.save("user", "q")
        state["fail_next"] = 1
        with pytest.raises(ConversationPersistenceError):
            await boundary.save_many(
                [
                    ("assistant", "a", None, None),
                    ("tool", "t", None, "c"),
                ]
            )

        assert _message_rows(conn) == []


# ── Snapshot restore ───────────────────────────────────────────────────────────


class TestSnapshotRestore:
    async def test_memory_restored_to_turn_start_snapshot(self, wired) -> None:
        conn, state = wired
        session = AgentSession()
        session.session_id = 1
        conv = ConversationState()
        conv.history = [{"role": "user", "content": "start"}]
        boundary = await _boundary(session, conv, marker=0)

        # History mutates during the (failed) turn.
        conv.history.append({"role": "assistant", "content": "partial"})

        state["fail_next"] = 1
        with pytest.raises(ConversationPersistenceError):
            await boundary.save_phase_grouped([("assistant", "x", None, None)])

        # AC-004: memory equals the turn-start snapshot element-wise.
        assert conv.history == [{"role": "user", "content": "start"}]
