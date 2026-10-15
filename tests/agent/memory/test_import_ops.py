"""tests/agent/memory/test_import_ops.py

Tests for ``import_ops.import_from_jsonl()`` ordered replay (REQ-002) and the
``backup`` / ``allow_loss`` guard (REQ-007).

Archives are built through the production serialization path
(``JsonlMemoryStore.write`` / ``append_event``) so the on-disk format matches
what the store actually emits; malformed lines are appended raw.
"""

from __future__ import annotations

import asyncio
import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import cast

import pytest
from agent.memory.enums import MemoryType
from agent.memory.import_ops import import_from_jsonl
from agent.memory.jsonl_store import JsonlMemoryStore
from agent.memory.types import MemoryEntry, SourceType
from agent.memory.write_ops import add as write_add

_OPS = list[tuple[str, object, str]]


_SCHEMA_SQL = """
CREATE TABLE memories (
    memory_id   TEXT PRIMARY KEY,
    memory_type TEXT NOT NULL CHECK(memory_type IN ('semantic','episodic')),
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
    memory_id UNINDEXED,
    content,
    summary,
    tags
);
CREATE TABLE memories_vec (
    memory_id TEXT PRIMARY KEY,
    embedding BLOB
);
"""


class _FakeSQLiteHelper:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn
        self.conn: sqlite3.Connection | None = conn

    def open(
        self, *, write_mode: bool = False, row_factory: bool = False
    ) -> _FakeSQLiteHelper:
        self._conn.row_factory = sqlite3.Row if row_factory else None
        self.conn = self._conn
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

    @contextmanager
    def begin_immediate(self) -> Generator[None]:
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            yield
            self._conn.execute("COMMIT")
        except BaseException:
            try:
                self._conn.execute("ROLLBACK")
            except Exception:  # noqa: BLE001 — rollback-on-error is best-effort; must not mask the original exception being re-raised
                pass
            raise


@pytest.fixture()
def db_conn() -> Generator[sqlite3.Connection]:
    conn = sqlite3.connect(":memory:")
    conn.executescript(_SCHEMA_SQL)
    conn.commit()
    yield conn
    conn.close()


@pytest.fixture()
def import_ops_fake_helper(
    db_conn: sqlite3.Connection,
) -> Generator[_FakeSQLiteHelper]:
    """Return a fake SQLiteHelper patched into both import_ops and write_ops modules."""
    fake = _FakeSQLiteHelper(db_conn)
    import agent.memory.import_ops as _import_ops
    import agent.memory.write_ops as _write_ops

    orig_import = _import_ops.SQLiteHelper
    orig_write = _write_ops.SQLiteHelper
    _import_ops.SQLiteHelper = lambda *a, **kw: fake
    _write_ops.SQLiteHelper = lambda *a, **kw: fake
    yield fake
    _import_ops.SQLiteHelper = orig_import
    _write_ops.SQLiteHelper = orig_write


def _make_entry(
    memory_id: str,
    memory_type: str = "semantic",
    content: str = "test content",
    pinned: bool = False,
) -> MemoryEntry:
    return MemoryEntry(
        memory_id=memory_id,
        memory_type=MemoryType(memory_type),
        source_type=SourceType.RULE,
        session_id=1,
        turn_id=None,
        project="proj",
        repo="repo",
        branch="main",
        content=content,
        summary=content[:50],
        tags=["test"],
        importance=0.5,
        pinned=pinned,
        created_at="2025-01-01T00:00:00Z",
        updated_at="2025-01-01T00:00:00Z",
    )


def _write_archive(
    path: Path,
    *,
    ops: list[tuple[str, object, str]] | None = None,
    malformed: list[str] | None = None,
) -> JsonlMemoryStore:
    """Build a JSONL archive by replaying ``ops`` in order via production serialization.

    Each op is ``("mem", MemoryEntry, "")`` or ``("event", event_name, memory_id)``.
    Malformed lines are appended raw after the ops.
    """
    ops = ops or []
    malformed = malformed or []
    store = JsonlMemoryStore(path)
    for kind, payload, mid in ops:
        if kind == "mem":
            asyncio.run(store.write(cast(MemoryEntry, payload)))
        else:  # event
            store.append_event(cast(str, payload), mid)
    with path.open("a", encoding="utf-8") as f:
        for raw in malformed:
            f.write(raw + "\n")
    return store


def _ids(conn: sqlite3.Connection) -> list[str]:
    return [r[0] for r in conn.execute("SELECT memory_id FROM memories").fetchall()]


def _pinned(conn: sqlite3.Connection, mid: str) -> int:
    row = conn.execute(
        "SELECT pinned FROM memories WHERE memory_id=?", (mid,)
    ).fetchone()
    return row[0] if row else -1


class TestImportReplayFinalState:
    def test_add_and_overwrite_on_memory_line(
        self,
        tmp_path: Path,
        import_ops_fake_helper: _FakeSQLiteHelper,
        db_conn: sqlite3.Connection,
    ) -> None:
        store = _write_archive(
            tmp_path / "m.jsonl",
            ops=[
                ("mem", _make_entry("e1", content="v1"), ""),
                ("mem", _make_entry("e1", content="v2"), ""),
                ("mem", _make_entry("e2"), ""),
            ],
        )
        jsonl_count, inserted = import_from_jsonl(store)

        assert jsonl_count == 3
        assert inserted == 2
        assert set(_ids(db_conn)) == {"e1", "e2"}
        row = db_conn.execute(
            "SELECT content FROM memories WHERE memory_id='e1'"
        ).fetchone()
        assert row[0] == "v2"

    def test_delete_then_readd_is_present(
        self,
        tmp_path: Path,
        import_ops_fake_helper: _FakeSQLiteHelper,
        db_conn: sqlite3.Connection,
    ) -> None:
        # delete removes; a later memory line re-adds -> final state has it.
        store = _write_archive(
            tmp_path / "m.jsonl",
            ops=[
                ("mem", _make_entry("e1", content="v1"), ""),
                ("event", "delete", "e1"),
                ("mem", _make_entry("e1", content="v2"), ""),
            ],
        )

        _, inserted = import_from_jsonl(store)

        assert inserted == 1
        assert _ids(db_conn) == ["e1"]

    def test_delete_stays_deleted(
        self,
        tmp_path: Path,
        import_ops_fake_helper: _FakeSQLiteHelper,
        db_conn: sqlite3.Connection,
    ) -> None:
        store = _write_archive(
            tmp_path / "m.jsonl",
            ops=[
                ("mem", _make_entry("e1"), ""),
                ("mem", _make_entry("e2"), ""),
                ("event", "delete", "e1"),
            ],
        )

        _, inserted = import_from_jsonl(store)

        assert inserted == 1
        assert _ids(db_conn) == ["e2"]

    def test_pin_sets_and_unpin_clears_last_wins(
        self,
        tmp_path: Path,
        import_ops_fake_helper: _FakeSQLiteHelper,
        db_conn: sqlite3.Connection,
    ) -> None:
        store = _write_archive(
            tmp_path / "m.jsonl",
            ops=[
                ("mem", _make_entry("e1"), ""),
                ("event", "pin", "e1"),
                ("event", "unpin", "e1"),
                ("event", "pin", "e1"),
            ],
        )

        import_from_jsonl(store)

        assert _pinned(db_conn, "e1") == 1

    def test_pin_for_missing_entry_is_noop(
        self,
        tmp_path: Path,
        import_ops_fake_helper: _FakeSQLiteHelper,
        db_conn: sqlite3.Connection,
    ) -> None:
        store = _write_archive(
            tmp_path / "m.jsonl",
            ops=[
                ("mem", _make_entry("e1"), ""),
                ("event", "pin", "ghost"),
                ("event", "delete", "ghost"),
            ],
        )

        _, inserted = import_from_jsonl(store)

        assert inserted == 1
        assert _ids(db_conn) == ["e1"]


class TestImportMalformedAndShape:
    def test_malformed_skipped_and_counted(
        self,
        tmp_path: Path,
        import_ops_fake_helper: _FakeSQLiteHelper,
        db_conn: sqlite3.Connection,
    ) -> None:
        store = _write_archive(
            tmp_path / "m.jsonl",
            ops=[
                ("mem", _make_entry("e1"), ""),
                ("mem", _make_entry("e2"), ""),
            ],
            malformed=["{not json", "also{bad"],
        )

        jsonl_count, inserted = import_from_jsonl(store)

        assert jsonl_count == 2
        assert inserted == 2
        assert set(_ids(db_conn)) == {"e1", "e2"}

    def test_dry_run_leaves_sqlite_untouched(
        self,
        tmp_path: Path,
        import_ops_fake_helper: _FakeSQLiteHelper,
        db_conn: sqlite3.Connection,
    ) -> None:
        write_add(_make_entry("existing"))
        store = _write_archive(
            tmp_path / "m.jsonl",
            ops=[
                ("mem", _make_entry("e1"), ""),
                ("mem", _make_entry("e2"), ""),
            ],
        )

        jsonl_count, inserted = import_from_jsonl(store, dry_run=True)

        assert jsonl_count == 2
        assert inserted == 0
        assert _ids(db_conn) == ["existing"]

    def test_return_shape_single_pass(
        self,
        tmp_path: Path,
        import_ops_fake_helper: _FakeSQLiteHelper,
        db_conn: sqlite3.Connection,
    ) -> None:
        store = _write_archive(
            tmp_path / "m.jsonl",
            ops=[
                ("mem", _make_entry("e1"), ""),
                ("mem", _make_entry("e2"), ""),
            ],
        )

        jsonl_count, inserted = import_from_jsonl(store)

        assert (jsonl_count, inserted) == (2, 2)

    def test_non_store_raises_type_error(self) -> None:
        with pytest.raises(TypeError):
            import_from_jsonl(object())


class TestBackupGuard:
    def test_backup_refuses_without_allow_loss(
        self,
        tmp_path: Path,
        import_ops_fake_helper: _FakeSQLiteHelper,
        db_conn: sqlite3.Connection,
    ) -> None:
        store = _write_archive(
            tmp_path / "m.jsonl",
            ops=[("mem", _make_entry("e1"), "")],
            malformed=["{bad json"],
        )

        with pytest.raises(ValueError, match="allow_loss"):
            import_from_jsonl(store, backup=True, allow_loss=False)

    def test_backup_proceeds_with_allow_loss(
        self,
        tmp_path: Path,
        import_ops_fake_helper: _FakeSQLiteHelper,
        db_conn: sqlite3.Connection,
    ) -> None:
        store = _write_archive(
            tmp_path / "m.jsonl",
            ops=[("mem", _make_entry("e1"), "")],
            malformed=["{bad json"],
        )

        _, inserted = import_from_jsonl(store, backup=True, allow_loss=True)

        assert inserted == 1
        assert _ids(db_conn) == ["e1"]
