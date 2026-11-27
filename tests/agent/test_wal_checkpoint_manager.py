"""tests/agent/test_wal_checkpoint_manager.py — WalCheckpointManager against a real SQLite WAL database."""

from __future__ import annotations

import asyncio
import logging
import os
import shutil
import sqlite3
import threading
import time
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import BinaryIO
from unittest.mock import MagicMock, patch

import pytest
from agent.wal_checkpoint_manager import (
    _MAX_TRUNCATE_ATTEMPTS,
    WalCheckpointManager,
    format_sqlite_error,
)
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


class TestBoundedRetryAndInterrupt:
    """REQ-008: the retry loop stops at the deadline and on an interrupt request."""

    @pytest.mark.asyncio
    async def test_spent_deadline_stops_the_retry_before_the_next_attempt(
        self, db: _Db, tmp_path: Path
    ) -> None:
        """The loop reports the attempts it did not get to make instead of running them."""
        db.insert(5)
        factory = _helper_factory(
            db, passive_raises=True, truncate_failures=_MAX_TRUNCATE_ATTEMPTS
        )
        deadline = time.monotonic() + 0.4
        started = time.monotonic()
        with patch("agent.wal_checkpoint_manager.SQLiteHelper", factory):
            ok, errors = await _manager(tmp_path).checkpoint_sync(deadline=deadline)
        elapsed = time.monotonic() - started

        assert ok is False
        assert [name for name, _ in errors] == ["wal_checkpoint_deadline"]
        assert "before attempt 2 of 3" in errors[0][1]
        # The unclamped backoff alone would be 1 s; the deadline is 0.4 s.
        assert elapsed < 1.0, elapsed

    @pytest.mark.asyncio
    async def test_checkpoint_interrupt_stops_worker_thread(
        self, db: _Db, tmp_path: Path
    ) -> None:
        """An interrupt set during the backoff ends the worker instead of abandoning it."""
        db.insert(5)
        factory = _helper_factory(db, passive_raises=True, truncate_failures=2)
        stop = threading.Event()
        timer = threading.Timer(0.2, stop.set)
        timer.start()
        started = time.monotonic()
        try:
            with patch("agent.wal_checkpoint_manager.SQLiteHelper", factory):
                ok, errors = await _manager(tmp_path).checkpoint_sync(stop=stop)
        finally:
            timer.cancel()
        elapsed = time.monotonic() - started

        assert ok is False
        assert [name for name, _ in errors] == ["wal_checkpoint_interrupted"]
        # The first backoff is 1 s: returning early is the interrupt ending the sleep.
        assert elapsed < 0.9, elapsed

    @pytest.mark.asyncio
    async def test_interrupt_set_before_the_step_ends_it_without_an_attempt(
        self, db: _Db, tmp_path: Path
    ) -> None:
        db.insert(5)
        factory = _helper_factory(db, passive_raises=True, truncate_failures=1)
        stop = threading.Event()
        stop.set()
        with patch("agent.wal_checkpoint_manager.SQLiteHelper", factory):
            ok, errors = await _manager(tmp_path).checkpoint_sync(stop=stop)

        assert ok is False
        assert [name for name, _ in errors] == ["wal_checkpoint_interrupted"]

    @pytest.mark.asyncio
    async def test_progress_handler_is_installed_and_cleared(
        self, db: _Db, tmp_path: Path
    ) -> None:
        """REQ-008: the stop is wired to the connection, so a running statement aborts."""
        db.insert(5)
        calls: list[object] = []

        class _Recording(RealHelper):
            def interrupt_when(self, stop, *, check_every: int = 1000) -> None:
                calls.append(stop)
                super().interrupt_when(stop, check_every=check_every)

        stop = threading.Event()
        with (
            patch(
                "agent.wal_checkpoint_manager.SQLiteHelper",
                lambda *_a, **_k: _Recording(db_path=str(db.path)),
            ),
        ):
            ok, errors = await _manager(tmp_path).checkpoint_sync(stop=stop)

        assert (ok, errors) == (True, [])
        assert calls == [stop, None]

    @pytest.mark.asyncio
    async def test_no_stop_means_no_progress_handler(
        self, db: _Db, tmp_path: Path
    ) -> None:
        """A step with no interrupt channel leaves the connection's handler untouched."""
        db.insert(5)
        calls: list[object] = []

        class _Recording(RealHelper):
            def interrupt_when(self, stop, *, check_every: int = 1000) -> None:
                calls.append(stop)
                super().interrupt_when(stop, check_every=check_every)

        with patch(
            "agent.wal_checkpoint_manager.SQLiteHelper",
            lambda *_a, **_k: _Recording(db_path=str(db.path)),
        ):
            ok, errors = await _manager(tmp_path).checkpoint_sync()

        assert (ok, errors) == (True, [])
        assert calls == []


class TestAtomicBackupPublication:
    """REQ-009, AC-3: publish through a .partial file, or not at all."""

    @pytest.mark.asyncio
    async def test_backup_copies_to_a_partial_file_and_publishes_it(
        self, db: _Db, tmp_path: Path
    ) -> None:
        db.insert(20)
        copied_to: list[str] = []
        real_copy = shutil.copyfileobj

        def _spy_copy(src: BinaryIO, dst: BinaryIO, length: int = 0) -> None:
            copied_to.append(str(dst.name))
            return real_copy(src, dst, length)

        with (
            patch("agent.wal_checkpoint_manager.SQLiteHelper", _helper_factory(db)),
            patch("agent.wal_checkpoint_manager.shutil.copyfileobj", _spy_copy),
        ):
            path, errors = await _manager(tmp_path).backup_sync()

        assert errors == []
        assert path is not None
        # The copy target is the temporary name; the final name only exists after replace.
        assert copied_to == [f"{path}.partial"]
        assert Path(path).exists()
        assert not any(p.name.endswith(".partial") for p in tmp_path.iterdir())

    @pytest.mark.asyncio
    async def test_partial_backup_never_visible_under_final_name(
        self, db: _Db, tmp_path: Path
    ) -> None:
        """An interrupted copy leaves no file at the name a later reader would trust."""
        db.insert(20)

        def _interrupted_copy(src: BinaryIO, dst: BinaryIO, length: int = 0) -> None:
            dst.write(b"half a wal")
            raise OSError("no space left on device")

        with (
            patch("agent.wal_checkpoint_manager.SQLiteHelper", _helper_factory(db)),
            patch("agent.wal_checkpoint_manager.shutil.copyfileobj", _interrupted_copy),
        ):
            path, errors = await _manager(tmp_path).backup_sync()

        assert path is None
        assert [name for name, _ in errors] == ["wal_backup"]
        assert "OSError" in errors[0][1]
        assert not any("wal-backup" in p.name for p in tmp_path.iterdir())

    @pytest.mark.asyncio
    async def test_size_mismatch_is_recorded_and_not_published(
        self, db: _Db, tmp_path: Path
    ) -> None:
        """A short copy is a distinct error, not a silently truncated backup."""
        db.insert(20)
        source_size = os.path.getsize(f"{db.path}-wal")
        assert source_size > 5

        def _short_copy(src: BinaryIO, dst: BinaryIO, length: int = 0) -> None:
            dst.write(b"short")

        with (
            patch("agent.wal_checkpoint_manager.SQLiteHelper", _helper_factory(db)),
            patch("agent.wal_checkpoint_manager.shutil.copyfileobj", _short_copy),
        ):
            path, errors = await _manager(tmp_path).backup_sync()

        assert path is None
        assert [name for name, _ in errors] == ["wal_backup_size_mismatch"]
        assert errors[0][1] == f"copied 5 of {source_size} bytes"
        assert not any("wal-backup" in p.name for p in tmp_path.iterdir())

    @pytest.mark.asyncio
    async def test_a_spent_deadline_stops_the_backup_before_it_writes(
        self, db: _Db, tmp_path: Path
    ) -> None:
        db.insert(20)
        with patch("agent.wal_checkpoint_manager.SQLiteHelper", _helper_factory(db)):
            path, errors = await _manager(tmp_path).backup_sync(
                deadline=time.monotonic() - 0.1
            )

        assert path is None
        assert [name for name, _ in errors] == ["wal_backup_deadline"]
        assert not any("wal-backup" in p.name for p in tmp_path.iterdir())

    @pytest.mark.asyncio
    async def test_an_interrupt_request_stops_the_backup_before_it_writes(
        self, db: _Db, tmp_path: Path
    ) -> None:
        db.insert(20)
        stop = threading.Event()
        stop.set()
        with patch("agent.wal_checkpoint_manager.SQLiteHelper", _helper_factory(db)):
            path, errors = await _manager(tmp_path).backup_sync(stop=stop)

        assert path is None
        assert [name for name, _ in errors] == ["wal_backup_interrupted"]


class TestSqliteErrorLogText:
    """REQ-004 (AC-2): a SQLite failure logs the error type name plus a masked message."""

    def test_formatter_reduces_paths_and_masks_credentials(self) -> None:
        err = sqlite3.OperationalError(
            "unable to open database file: /opt/llm/rag.sqlite password=SECRETVALUE"
        )
        assert format_sqlite_error(err) == (
            "OperationalError: unable to open database file: rag.sqlite "
            "password=***MASKED***"
        )

    @pytest.mark.asyncio
    async def test_passive_failure_line_carries_type_and_masked_message(
        self, db: _Db, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        class _Helper(RealHelper):
            def checkpoint(self, mode: str = "TRUNCATE") -> WalCheckpointCounts:
                raise sqlite3.OperationalError(
                    f"unable to open database file: {db.path} password=SECRETVALUE"
                )

        with caplog.at_level(logging.WARNING):
            with patch(
                "agent.wal_checkpoint_manager.SQLiteHelper",
                lambda *_a, **_k: _Helper(
                    db_path=str(db.path), sqlite_busy_timeout_ms=100
                ),
            ):
                ok, errors = await _manager(tmp_path).checkpoint_sync()

        assert ok is False
        # Both the log line and the recorded tuple carry the formatted text: the type name,
        # the masked credential, and the DB file reduced to its logical identifier.
        assert (
            f"OperationalError: unable to open database file: {db.path.name} "
            "password=***MASKED***" in caplog.text
        )
        assert "SECRETVALUE" not in caplog.text
        assert str(db.path) not in caplog.text
        assert errors[0][1].startswith("OperationalError:")
        assert "SECRETVALUE" not in errors[0][1]

    @pytest.mark.asyncio
    async def test_backup_failure_line_carries_type_and_masked_message(
        self, db: _Db, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        db.insert(20)

        def _fail_copy(*args: object, **kwargs: object) -> None:
            raise sqlite3.OperationalError(
                f"unable to open database file: {db.path} token=SECRETVALUE"
            )

        with caplog.at_level(logging.WARNING):
            with (
                patch("agent.wal_checkpoint_manager.SQLiteHelper", _helper_factory(db)),
                patch("agent.wal_checkpoint_manager.shutil.copyfileobj", _fail_copy),
            ):
                path, errors = await _manager(tmp_path).backup_sync()

        assert path is None
        assert [name for name, _ in errors] == ["wal_backup"]
        assert "OperationalError:" in caplog.text
        assert "SECRETVALUE" not in caplog.text
        assert str(db.path) not in caplog.text
