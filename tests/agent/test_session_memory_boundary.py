"""tests/agent/test_session_memory_boundary.py
Acceptance tests for the session / memory responsibility boundary.

Session operations change `sessions` and `messages` only; memory operations
change `memories*` only. `memories.session_id` is provenance, not ownership.
"""

from __future__ import annotations

import re
import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from unittest.mock import patch

import pytest
from agent.memory.store import MemoryStore
from agent.memory.types import MemoryEntry
from agent.memory.write_ops import add, delete
from agent.session import AgentSession
from db.schema_sql import build_session_schema_sql

_SCHEMA_SQL = """
CREATE TABLE sessions (
    session_id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    title TEXT,
    undo_floor_message_id INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE messages (
    message_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    role       TEXT NOT NULL,
    content    TEXT NOT NULL,
    tool_calls TEXT,
    tool_call_id TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE memories (
    memory_id   TEXT PRIMARY KEY,
    memory_type TEXT NOT NULL,
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
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE VIRTUAL TABLE memories_fts USING fts5(
    memory_id UNINDEXED, content, summary, tags
);
CREATE TABLE memories_vec (memory_id TEXT PRIMARY KEY, embedding BLOB);
CREATE TABLE memory_links (
    src_id  TEXT NOT NULL REFERENCES memories(memory_id),
    dst_id  TEXT NOT NULL REFERENCES memories(memory_id),
    PRIMARY KEY (src_id, dst_id)
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

    def __enter__(self) -> _FakeSQLiteHelper:
        return self

    def __exit__(self, *_: object) -> None:
        pass

    def execute(self, sql: str, params: tuple | dict = ()) -> sqlite3.Cursor:
        return self._conn.execute(sql, params)

    def fetchall(self, sql: str, params: tuple | dict = ()) -> list:
        return self._conn.execute(sql, params).fetchall()

    def commit(self) -> None:
        self._conn.commit()

    @contextmanager
    def begin_immediate(self) -> Generator[None]:
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            yield
            self._conn.execute("COMMIT")
        except BaseException:
            self._conn.execute("ROLLBACK")
            raise


def _entry(memory_id: str, session_id: int | None) -> MemoryEntry:
    return MemoryEntry(
        memory_id=memory_id,
        memory_type="semantic",
        source_type="rule",
        session_id=session_id,
        turn_id=None,
        project="proj",
        repo="repo",
        branch="main",
        content=f"fact {memory_id}",
        summary="",
        tags=[],
        importance=0.5,
        pinned=False,
        created_at="2025-01-01T00:00:00Z",
        updated_at="2025-01-01T00:00:00Z",
    )


@pytest.fixture()
def conn() -> Generator[sqlite3.Connection]:
    c = sqlite3.connect(":memory:")
    c.execute("PRAGMA foreign_keys=ON")
    c.executescript(_SCHEMA_SQL)
    c.execute("INSERT INTO sessions (session_id) VALUES (1)")
    c.execute("INSERT INTO sessions (session_id) VALUES (2)")
    c.executemany(
        "INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)",
        [(1, "user", "q1"), (1, "assistant", "a1"), (2, "user", "q2")],
    )
    c.commit()
    yield c
    c.close()


@pytest.fixture()
def wired(conn: sqlite3.Connection) -> Generator[AgentSession]:
    fake = _FakeSQLiteHelper(conn)
    with (
        patch("agent.session.SQLiteHelper", return_value=fake),
        patch("agent.memory.write_ops.SQLiteHelper", return_value=fake),
        patch("agent.memory.store.SQLiteHelper", return_value=fake),
    ):
        MemoryStore()
        add(_entry("m1", session_id=1))
        add(_entry("m2", session_id=2))
        yield AgentSession()


def _memory_ids(conn: sqlite3.Connection) -> list[str]:
    return [
        r[0] for r in conn.execute("SELECT memory_id FROM memories ORDER BY memory_id")
    ]


class TestSessionOperationsKeepMemory:
    def test_delete_session_keeps_memory_and_provenance(
        self, wired: AgentSession, conn: sqlite3.Connection
    ) -> None:
        assert wired.delete_session(1) is True
        assert (
            conn.execute("SELECT COUNT(*) FROM messages WHERE session_id=1").fetchone()[
                0
            ]
            == 0
        )
        assert _memory_ids(conn) == ["m1", "m2"]
        # provenance is retained and no foreign-key error occurs
        assert conn.execute(
            "SELECT session_id FROM memories WHERE memory_id='m1'"
        ).fetchone() == (1,)
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == []

    def test_deleted_source_memory_stays_searchable(
        self, wired: AgentSession, conn: sqlite3.Connection
    ) -> None:
        wired.delete_session(1)
        rows = conn.execute(
            "SELECT memory_id FROM memories_fts WHERE memories_fts MATCH 'fact'"
        ).fetchall()
        assert {r[0] for r in rows} == {"m1", "m2"}

    def test_undo_changes_messages_only(
        self, wired: AgentSession, conn: sqlite3.Connection
    ) -> None:
        wired.session_id = 1
        assert wired.undo_last_turn() == 2
        assert (
            conn.execute("SELECT COUNT(*) FROM messages WHERE session_id=1").fetchone()[
                0
            ]
            == 0
        )
        assert _memory_ids(conn) == ["m1", "m2"]


class TestMemoryOperationsKeepSession:
    @pytest.fixture(autouse=True)
    def _suppress_archive_write(self) -> Generator[None]:
        """Prevent delete()'s SQLite-first archive append from touching disk.

        ``delete()`` appends a ``delete`` change event to the JSONL archive after
        committing; patch the helper so this boundary test never writes to the
        real production archive (test isolation).
        """
        with patch("agent.memory.write_ops._emit_delete_event"):
            yield

    def test_memory_delete_removes_target_only(
        self, wired: AgentSession, conn: sqlite3.Connection
    ) -> None:
        assert delete("m1") is True
        assert _memory_ids(conn) == ["m2"]
        assert conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0] == 2
        assert conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0] == 3


class TestSchemaProvenance:
    def test_memories_session_id_has_no_foreign_key(self) -> None:
        ddl = build_session_schema_sql(4)
        match = re.search(
            r"CREATE TABLE IF NOT EXISTS memories \((.*?)\n\s*\);", ddl, re.DOTALL
        )
        assert match is not None
        assert "REFERENCES" not in match.group(1).upper()
        assert "Provenance only" in match.group(1)
