"""tests/agent/test_wal_checkpoint_manager.py — WalCheckpointManager against a real SQLite WAL database."""

from __future__ import annotations

import asyncio
import sqlite3
import threading
from collections.abc import Callable, Iterator
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from agent.wal_checkpoint_manager import WalCheckpointManager
from db.helper import SQLiteHelper as RealHelper
from db.models import WalCheckpointCounts


class _Db:
    """A temporary WAL database with a long-lived writer connection that keeps the WAL alive."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.writer = sqlite3.connect(path, isolation_level=None)
        self.writer.execute("PRAGMA journal_mode=WAL")
        self.writer.execute("PRAGMA wal_autocheckpoint=0")
        self.writer.execute("CREATE TABLE t (v INTEGER)")
        self.reader: sqlite3.Connection | None = None

    def insert(self, rows: int) -> None:
        for i in range(rows):
            self.writer.execute("INSERT INTO t VALUES (?)", (i,))

    def truncate(self) -> None:
        self.writer.execute("PRAGMA wal_checkpoint(TRUNCATE)")

    def hold_reader(self) -> None:
        """Open a read snapshot that pins the WAL position (the checkpoint cannot pass it)."""
        self.reader = sqlite3.connect(self.path, isolation_level=None)
        self.reader.execute("BEGIN")
        self.reader.execute("SELECT count(*) FROM t").fetchone()

    def release_reader(self) -> None:
        if self.reader is not None:
            self.reader.close()
            self.reader = None

    def close(self) -> None:
        self.release_reader()
        self.writer.close()


@pytest.fixture
def db(tmp_path: Path) -> Iterator[_Db]:
    database = _Db(tmp_path / "session.db")
    try:
        yield database
    finally:
        database.close()


def _manager(tmp_path: Path) -> WalCheckpointManager:
    ctx = MagicMock()
    ctx.cfg.approval.allowed_root = str(tmp_path)
    ctx.session.session_id = 7
    return WalCheckpointManager(ctx)


def _helper_factory(
    db: _Db,
    *,
    passive_raises: bool = False,
    truncate_failures: int = 0,
    busy_timeout_ms: int = 100,
    closed: threading.Event | None = None,
) -> Callable[..., RealHelper]:
    class _Helper(RealHelper):
        failures_left = truncate_failures

        def checkpoint(self, mode: str = "TRUNCATE") -> WalCheckpointCounts:
            if mode == "PASSIVE" and passive_raises:
                raise sqlite3.OperationalError("database is locked")
            if mode == "TRUNCATE" and type(self).failures_left > 0:
                type(self).failures_left -= 1
                raise sqlite3.OperationalError("database is locked")
            return super().checkpoint(mode)

        def close(self) -> None:
            super().close()
            if closed is not None:
                closed.set()

    return lambda *_a, **_k: _Helper(
        db_path=str(db.path), sqlite_busy_timeout_ms=busy_timeout_ms
    )


class TestCheckpointReadsItsCounts:
    @pytest.mark.asyncio
    async def test_uncontended_checkpoint_succeeds(
        self, db: _Db, tmp_path: Path
    ) -> None:
        db.insert(20)
        with patch("agent.wal_checkpoint_manager.SQLiteHelper", _helper_factory(db)):
            ok, errors = await _manager(tmp_path).checkpoint_sync()
        assert (ok, errors) == (True, [])

    @pytest.mark.asyncio
    async def test_zero_frame_checkpoint_over_a_non_empty_wal_is_recorded(
        self, db: _Db, tmp_path: Path
    ) -> None:
        db.truncate()
        db.hold_reader()
        db.insert(20)
        with patch("agent.wal_checkpoint_manager.SQLiteHelper", _helper_factory(db)):
            ok, errors = await _manager(tmp_path).checkpoint_sync()
        assert ok is False
        assert [name for name, _ in errors] == ["wal_checkpoint_no_progress"]
        assert "copied 0 of" in errors[0][1]

    @pytest.mark.asyncio
    async def test_empty_wal_records_nothing(self, db: _Db, tmp_path: Path) -> None:
        db.truncate()
        with patch("agent.wal_checkpoint_manager.SQLiteHelper", _helper_factory(db)):
            ok, errors = await _manager(tmp_path).checkpoint_sync()
        assert (ok, errors) == (True, [])


class TestStepRunsOffTheEventLoop:
    @pytest.mark.asyncio
    async def test_loop_stays_responsive_during_the_retry_backoff(
        self, db: _Db, tmp_path: Path
    ) -> None:
        db.insert(5)
        factory = _helper_factory(db, passive_raises=True, truncate_failures=1)
        loop_ran = asyncio.Event()

        async def _sentinel() -> None:
            await asyncio.sleep(0.05)
            loop_ran.set()

        sentinel = asyncio.ensure_future(_sentinel())
        with patch("agent.wal_checkpoint_manager.SQLiteHelper", factory):
            ok, errors = await _manager(tmp_path).checkpoint_sync()
        # Checked before awaiting the sentinel: a step that blocks the loop through its
        # 1 s backoff leaves the 0.05 s sentinel unrun when it returns.
        ran_during_the_step = loop_ran.is_set()
        await sentinel
        assert (ok, errors) == (True, [])
        assert ran_during_the_step

    @pytest.mark.asyncio
    async def test_bound_expires_while_a_contended_step_still_runs(
        self, db: _Db, tmp_path: Path
    ) -> None:
        db.truncate()
        db.hold_reader()
        db.insert(20)
        closed = threading.Event()
        factory = _helper_factory(
            db, passive_raises=True, busy_timeout_ms=3000, closed=closed
        )
        try:
            with patch("agent.wal_checkpoint_manager.SQLiteHelper", factory):
                with pytest.raises(TimeoutError):
                    await asyncio.wait_for(
                        _manager(tmp_path).checkpoint_sync(), timeout=0.3
                    )
        finally:
            db.release_reader()
            await asyncio.to_thread(closed.wait, 15)
        assert closed.is_set(), (
            "the abandoned worker finished and closed its connection"
        )


class TestBackupRunsOffTheEventLoop:
    @pytest.mark.asyncio
    async def test_backup_copies_the_wal_and_reports_its_path(
        self, db: _Db, tmp_path: Path
    ) -> None:
        db.insert(20)
        with patch("agent.wal_checkpoint_manager.SQLiteHelper", _helper_factory(db)):
            path, errors = await _manager(tmp_path).backup_sync()
        assert errors == []
        assert path is not None
        assert Path(path).exists()
