"""tests/test_memory_consistency.py
Tests for memory consistency check and rebuild:
  - JsonlMemoryStore.count_all()
  - import_ops.import_from_jsonl()
  - /memory check-consistency command
  - /memory rebuild command
"""

from __future__ import annotations

import asyncio
import sqlite3
import tempfile
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from agent.memory.import_ops import import_from_jsonl
from agent.memory.jsonl_store import JsonlMemoryStore
from agent.memory.models import ConsistencyReport
from agent.memory.types import MemoryEntry
from agent.memory.write_ops import add as write_add

# Backing dir for rebuild backup writes in unit tests.
_TMP_JSONL_DIR = tempfile.mkdtemp(prefix="mem-consistency-test-jsonl-")


def _make_entry(
    memory_type: str = "semantic",
    content: str = "test content",
    memory_id: str | None = None,
) -> MemoryEntry:
    import uuid

    return MemoryEntry(
        memory_id=memory_id or str(uuid.uuid4()),
        memory_type=memory_type,
        source_type="rule",
        session_id=1,
        turn_id=None,
        project="proj",
        repo="repo",
        branch="main",
        content=content,
        summary=content[:50],
        tags=["test"],
        importance=0.5,
        pinned=False,
        created_at="2025-01-01T00:00:00Z",
        updated_at="2025-01-01T00:00:00Z",
    )


# ── JsonlMemoryStore.count_all() ─────────────────────────────────────────────


class TestCountAll:
    def test_empty_file_returns_zero(self, tmp_path: Path) -> None:
        store = JsonlMemoryStore(tmp_path / "mem.jsonl")
        assert store.count_all() == 0

    def test_nonexistent_file_returns_zero(self, tmp_path: Path) -> None:
        store = JsonlMemoryStore(tmp_path / "nonexistent.jsonl")
        assert store.count_all() == 0

    def test_returns_number_of_entries(self, tmp_path: Path) -> None:
        path = tmp_path / "mem.jsonl"
        store = JsonlMemoryStore(path)
        for i in range(3):
            asyncio.run(store.write(_make_entry(memory_id=f"id-{i}")))
        assert store.count_all() == 3

    def test_skips_blank_lines(self, tmp_path: Path) -> None:
        path = tmp_path / "mem.jsonl"
        store = JsonlMemoryStore(path)
        asyncio.run(store.write(_make_entry(memory_id="id-0")))
        # Append a blank line manually
        with path.open("a") as f:
            f.write("\n")
        assert store.count_all() == 1


# ── MemoryStore.import_from_jsonl() ─────────────────────────────────────────

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
def import_ops_fake_helper(db_conn: sqlite3.Connection) -> Generator[_FakeSQLiteHelper]:
    """Return a fake SQLiteHelper patched into both import_ops and write_ops modules."""
    fake = _FakeSQLiteHelper(db_conn)
    # Replace the module-level references that import_ops and write_ops resolved at
    # import time; patching db.helper.SQLiteHelper would not reach them.
    import agent.memory.import_ops as _import_ops
    import agent.memory.write_ops as _write_ops

    orig_import = _import_ops.SQLiteHelper
    orig_write = _write_ops.SQLiteHelper
    _import_ops.SQLiteHelper = lambda *a, **kw: fake
    _write_ops.SQLiteHelper = lambda *a, **kw: fake
    yield fake
    _import_ops.SQLiteHelper = orig_import
    _write_ops.SQLiteHelper = orig_write


class TestRebuildFromJsonl:
    def test_dry_run_returns_jsonl_count_and_zero(
        self,
        tmp_path: Path,
        import_ops_fake_helper: _FakeSQLiteHelper,
        db_conn: sqlite3.Connection,
    ) -> None:
        jsonl = JsonlMemoryStore(tmp_path / "mem.jsonl")
        asyncio.run(jsonl.write(_make_entry(memory_id="e1")))
        asyncio.run(jsonl.write(_make_entry(memory_id="e2")))

        jsonl_count, inserted = import_from_jsonl(jsonl, dry_run=True)

        assert jsonl_count == 2
        assert inserted == 0
        # SQLite untouched
        rows = db_conn.execute("SELECT COUNT(*) FROM memories").fetchone()
        assert rows[0] == 0

    def test_rebuild_inserts_all_jsonl_entries(
        self,
        tmp_path: Path,
        import_ops_fake_helper: _FakeSQLiteHelper,
        db_conn: sqlite3.Connection,
    ) -> None:
        jsonl = JsonlMemoryStore(tmp_path / "mem.jsonl")
        asyncio.run(jsonl.write(_make_entry(memory_id="e1")))
        asyncio.run(jsonl.write(_make_entry(memory_id="e2", memory_type="episodic")))

        jsonl_count, inserted = import_from_jsonl(jsonl)

        assert jsonl_count == 2
        assert inserted == 2
        rows = db_conn.execute(
            "SELECT memory_id FROM memories ORDER BY memory_id"
        ).fetchall()
        assert [r[0] for r in rows] == ["e1", "e2"]

    def test_rebuild_clears_existing_rows(
        self,
        tmp_path: Path,
        import_ops_fake_helper: _FakeSQLiteHelper,
        db_conn: sqlite3.Connection,
    ) -> None:
        # Pre-populate SQLite with a stale row
        write_add(_make_entry(memory_id="stale"))

        jsonl = JsonlMemoryStore(tmp_path / "mem.jsonl")
        asyncio.run(jsonl.write(_make_entry(memory_id="fresh")))

        import_from_jsonl(jsonl)

        ids = [
            r[0] for r in db_conn.execute("SELECT memory_id FROM memories").fetchall()
        ]
        assert "stale" not in ids
        assert "fresh" in ids

    def test_rebuild_syncs_fts(
        self,
        tmp_path: Path,
        import_ops_fake_helper: _FakeSQLiteHelper,
        db_conn: sqlite3.Connection,
    ) -> None:
        jsonl = JsonlMemoryStore(tmp_path / "mem.jsonl")
        asyncio.run(jsonl.write(_make_entry(memory_id="e1", content="unique keyword")))

        import_from_jsonl(jsonl)

        rows = db_conn.execute(
            "SELECT memory_id FROM memories_fts WHERE memories_fts MATCH 'unique'"
        ).fetchall()
        assert len(rows) == 1

    def test_empty_jsonl_clears_sqlite(
        self,
        tmp_path: Path,
        import_ops_fake_helper: _FakeSQLiteHelper,
        db_conn: sqlite3.Connection,
    ) -> None:
        write_add(_make_entry(memory_id="existing"))
        jsonl = JsonlMemoryStore(tmp_path / "empty.jsonl")

        jsonl_count, inserted = import_from_jsonl(jsonl)

        assert jsonl_count == 0
        assert inserted == 0
        rows = db_conn.execute("SELECT COUNT(*) FROM memories").fetchone()
        assert rows[0] == 0


# ── /memory check-consistency command ────────────────────────────────────────


def _make_mem_services(
    *,
    memories: int = 5,
    fts: int = 5,
    vec: int = 0,
    jsonl_count: int = 5,
) -> MagicMock:
    from agent.memory.models import ConsistencyReport

    mem = MagicMock()
    mem.store.check_consistency.return_value = ConsistencyReport(
        memories=memories, fts=fts, vec=vec
    )
    mem.ingestion._jsonl.count_all.return_value = jsonl_count
    return mem


def _make_mixin(embed_enabled: bool = False) -> object:
    from agent.commands.memory_rebuild_ops import MemoryRebuildOps
    from agent.commands.output_port import CliOutputPort

    ctx = MagicMock()
    ctx.services_required.audit_logger = None
    ctx.cfg.memory.memory_embed_enabled = embed_enabled
    ctx.cfg.memory.memory_jsonl_dir = _TMP_JSONL_DIR
    out = MagicMock(spec=CliOutputPort)
    return MemoryRebuildOps(ctx, out)


class TestCmdMemoryCheckConsistency:
    def test_consistent_shows_yes(self) -> None:
        mixin = _make_mixin(embed_enabled=False)
        mem = _make_mem_services(memories=3, fts=3, vec=0, jsonl_count=3)

        mixin.check_consistency(mem)

        args = mixin._out.write_table.call_args[0]
        rows = args[1]
        consistent_row = next(r for r in rows if r[0] == "Consistent")
        assert consistent_row[1] == "Yes"

    def test_fts_mismatch_shows_no(self) -> None:
        mixin = _make_mixin(embed_enabled=False)
        mem = _make_mem_services(memories=3, fts=2, vec=0, jsonl_count=3)

        mixin.check_consistency(mem)

        args = mixin._out.write_table.call_args[0]
        rows = args[1]
        consistent_row = next(r for r in rows if r[0] == "Consistent")
        assert "NO" in consistent_row[1]

    def test_jsonl_mismatch_does_not_affect_consistency(self) -> None:
        mixin = _make_mixin(embed_enabled=False)
        mem = _make_mem_services(memories=3, fts=3, vec=0, jsonl_count=4)

        mixin.check_consistency(mem)

        args = mixin._out.write_table.call_args[0]
        rows = args[1]
        consistent_row = next(r for r in rows if r[0] == "Consistent")
        assert consistent_row[1] == "Yes"

    def test_consistency_error_writes_error(self) -> None:
        from agent.memory.exceptions import MemoryConsistencyError

        mixin = _make_mixin(embed_enabled=False)
        mem = MagicMock()
        mem.store.check_consistency.side_effect = MemoryConsistencyError("fts broken")

        mixin.check_consistency(mem)

        mixin._out.write.assert_called_once()
        msg = mixin._out.write.call_args[0][0]
        assert "fts broken" in msg


# ── /memory rebuild command ───────────────────────────────────────────────────


class TestCmdMemoryRebuild:
    def test_dry_run_writes_dry_run_message(self) -> None:
        from unittest.mock import patch

        mixin = _make_mixin()
        mem = MagicMock()
        mem.ingestion._jsonl = MagicMock()
        mem.ingestion._jsonl.count_all.return_value = 5
        mem.ingestion._jsonl.iter_records.return_value = []
        mem.store.list_entries.return_value = []

        with patch(
            "agent.commands.memory_rebuild_ops.import_from_jsonl", return_value=(5, 0)
        ):
            mixin.rebuild(mem, ["--dry-run"])

        all_messages = [c[0][0] for c in mixin._out.write.call_args_list]
        assert any("dry-run" in msg for msg in all_messages)
        # Dry-run table reports the JSONL record count.
        table_rows = mixin._out.write_table.call_args[0][1]
        assert any("5" in str(row) for row in table_rows)

    def test_rebuild_writes_success(self) -> None:
        from unittest.mock import patch

        from agent.memory.models import ConsistencyReport

        mixin = _make_mixin()
        mem = MagicMock()
        mem.ingestion._jsonl = MagicMock()
        mem.ingestion._jsonl.count_all.return_value = 4
        mem.store.check_consistency.return_value = ConsistencyReport(
            memories=4, fts=4, vec=0
        )
        mem.ingestion._jsonl.iter_records.return_value = []
        mem.store.list_entries.return_value = []

        with patch(
            "agent.commands.memory_rebuild_ops.import_from_jsonl", return_value=(4, 4)
        ):
            mixin.rebuild(mem, ["--confirm"])

        mixin._out.write_success.assert_called_once()
        msg = mixin._out.write_success.call_args[0][0]
        assert "4" in msg

    def test_dry_run_table_reports_metrics(self) -> None:
        from unittest.mock import patch

        mixin = _make_mixin()
        mem = MagicMock()
        jsonl = MagicMock()
        jsonl.count_all.return_value = 7
        jsonl.iter_records.return_value = []
        mem.store.list_entries.return_value = []
        mem.store.check_consistency.return_value = ConsistencyReport(
            memories=6, fts=6, vec=0
        )
        mem.ingestion._jsonl = jsonl

        with patch(
            "agent.commands.memory_rebuild_ops.import_from_jsonl", return_value=(7, 0)
        ):
            mixin.rebuild(mem, ["--dry-run"])

        headers, rows = mixin._out.write_table.call_args[0]
        assert headers == ["Metric", "Value"]
        values = {r[0]: r[1] for r in rows}
        assert values["JSONL archive records"] == "7"
        assert values["Current SQLite memories"] == "6"
        assert "SQLite-only (at risk)" in values

    def test_sqlite_only_counts_ids_absent_from_archive(self) -> None:
        from types import SimpleNamespace
        from unittest.mock import patch

        mixin = _make_mixin()
        mem = MagicMock()
        jsonl = MagicMock()
        jsonl.count_all.return_value = 2
        # Archive has m1, m2; SQLite has m1, m2, m3 → 1 SQLite-only.
        jsonl.iter_records.return_value = [
            ("memory", {"memory_id": "m1"}),
            ("memory", {"memory_id": "m2"}),
        ]
        mem.store.list_entries.return_value = [
            SimpleNamespace(memory_id="m1"),
            SimpleNamespace(memory_id="m2"),
            SimpleNamespace(memory_id="m3"),
        ]
        mem.store.check_consistency.return_value = ConsistencyReport(
            memories=3, fts=3, vec=0
        )
        mem.ingestion._jsonl = jsonl

        with patch(
            "agent.commands.memory_rebuild_ops.import_from_jsonl", return_value=(2, 2)
        ):
            result = mixin.rebuild(mem, ["--dry-run"])

        assert result.sqlite_only == 1

    def test_confirm_refuses_sqlite_only_without_allow_loss(self) -> None:

        from unittest.mock import patch

        mixin = _make_mixin()
        mem = MagicMock()
        jsonl = MagicMock()
        jsonl.count_all.return_value = 2
        jsonl.iter_records.return_value = [
            ("memory", {"memory_id": "m1"}),
            ("memory", {"memory_id": "m2"}),
        ]
        mem.store.list_entries.return_value = [
            _make_entry(memory_id="m1"),
            _make_entry(memory_id="m2"),
            _make_entry(memory_id="m3"),
        ]
        mem.store.check_consistency.return_value = ConsistencyReport(
            memories=3, fts=3, vec=0
        )
        mem.ingestion._jsonl = jsonl

        with patch(
            "agent.commands.memory_rebuild_ops.import_from_jsonl", return_value=(2, 2)
        ) as patched_import:
            result = mixin.rebuild(mem, ["--confirm"])

        assert result.loss_blocked is True
        assert result.sqlite_only == 1
        patched_import.assert_not_called()

    def test_confirm_proceeds_with_allow_loss(self) -> None:
        from unittest.mock import patch

        mixin = _make_mixin()
        mem = MagicMock()
        jsonl = MagicMock()
        jsonl.count_all.return_value = 2
        jsonl.iter_records.return_value = [("memory", {"memory_id": "m1"})]
        mem.store.list_entries.return_value = [
            _make_entry(memory_id="m1"),
            _make_entry(memory_id="m3"),  # SQLite-only
        ]
        mem.store.check_consistency.return_value = ConsistencyReport(
            memories=2, fts=2, vec=0
        )
        mem.ingestion._jsonl = jsonl

        with patch(
            "agent.commands.memory_rebuild_ops.import_from_jsonl", return_value=(2, 2)
        ) as patched_import:
            result = mixin.rebuild(mem, ["--confirm", "--allow-loss"])

        assert result.loss_blocked is False
        assert result.sqlite_only == 1
        patched_import.assert_called_once()

    def test_backup_failure_aborts_rebuild(self) -> None:
        from unittest.mock import patch

        from agent.commands.memory_rebuild_ops import MemoryRebuildOps

        mixin = _make_mixin()
        mem = MagicMock()
        jsonl = MagicMock()
        jsonl.count_all.return_value = 2
        jsonl.iter_records.return_value = []
        mem.store.list_entries.return_value = []
        mem.store.check_consistency.return_value = ConsistencyReport(
            memories=2, fts=2, vec=0
        )
        mem.ingestion._jsonl = jsonl

        with (
            patch.object(
                MemoryRebuildOps,
                "_backup_memories_as_jsonl",
                side_effect=RuntimeError("disk full"),
            ),
            patch(
                "agent.commands.memory_rebuild_ops.import_from_jsonl",
                return_value=(2, 2),
            ) as patched_import,
        ):
            result = mixin.rebuild(mem, ["--confirm"])

        assert result.error == "disk full"
        patched_import.assert_not_called()


# ── /memory reindex command ───────────────────────────────────────────────────


class TestCmdMemoryReindex:
    def test_reindex_fts_delegates_and_audits(self) -> None:
        mixin = _make_mixin()
        mem = MagicMock()
        with patch(
            "agent.commands.memory_rebuild_ops._reindex", return_value=42
        ) as spy:
            mixin.reindex(mem, ["--fts"])

        spy.assert_called_once_with("fts")
        mixin._out.write_success.assert_called_once()
        msg = mixin._out.write_success.call_args[0][0]
        assert "memories_fts rebuilt: 42" in msg

    def test_reindex_vec_requires_embedding(self) -> None:
        mixin = _make_mixin(embed_enabled=False)
        mem = MagicMock()
        with patch(
            "agent.commands.memory_rebuild_ops._reindex", return_value=99
        ) as spy:
            mixin.reindex(mem, ["--vec"])

        spy.assert_not_called()
        any_msg = " ".join(c[0][0] for c in mixin._out.write.call_args_list)
        assert "embedding disabled" in any_msg

    def test_reindex_missing_args_prints_usage(self) -> None:
        mixin = _make_mixin()
        mem = MagicMock()
        with patch("agent.commands.memory_rebuild_ops._reindex", return_value=1) as spy:
            mixin.reindex(mem, [])

        spy.assert_not_called()
        mixin._out.write_validation_error.assert_called_once()

    def test_reindex_vec_success(self) -> None:
        mixin = _make_mixin(embed_enabled=True)
        mem = MagicMock()
        with patch("agent.commands.memory_rebuild_ops._reindex", return_value=7) as spy:
            mixin.reindex(mem, ["--vec"])

        spy.assert_called_once_with("vec")
        msg = mixin._out.write_success.call_args[0][0]
        assert "memories_vec rebuilt: 7" in msg


# ── rebuild_ops.reindex dispatcher ────────────────────────────────────────────


class TestReindex:
    def test_reindex_fts_delegates_to_rebuild_fts(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import agent.memory.rebuild_ops as rebuild_ops

        spy = MagicMock(return_value=7)
        monkeypatch.setattr(rebuild_ops, "rebuild_fts", spy)
        monkeypatch.setattr(rebuild_ops, "rebuild_vec", MagicMock(return_value=0))

        assert rebuild_ops.reindex("fts") == 7
        spy.assert_called_once()

    def test_reindex_vec_delegates_to_rebuild_vec(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import agent.memory.rebuild_ops as rebuild_ops

        spy = MagicMock(return_value=3)
        monkeypatch.setattr(rebuild_ops, "rebuild_vec", spy)
        monkeypatch.setattr(rebuild_ops, "rebuild_fts", MagicMock(return_value=0))

        assert rebuild_ops.reindex("vec") == 3
        spy.assert_called_once()

    def test_reindex_unknown_raises_value_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import agent.memory.rebuild_ops as rebuild_ops

        monkeypatch.setattr(rebuild_ops, "rebuild_fts", MagicMock(return_value=0))
        monkeypatch.setattr(rebuild_ops, "rebuild_vec", MagicMock(return_value=0))

        with pytest.raises(ValueError, match="Unknown index type"):
            rebuild_ops.reindex("bogus")
