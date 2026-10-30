"""tests/eventbus/test_eventbus_shutdown.py

Regression test for the lifespan shutdown-vs-sweep race: `asyncio.Task.cancel()`
on `_dlq_loop`'s task does not stop its `asyncio.to_thread()`-wrapped sweep once
that thread has actually started running — the wrapping asyncio future is
marked cancelled immediately (letting `await app.state.dlq_task` return right
away with `CancelledError`), while the underlying `concurrent.futures.Future`
keeps running on its worker thread. Closing the DB connection immediately after
could race a still-running sweep and crash the process (confirmed independently:
`Fatal Python error: Segmentation fault` reproduced non-deterministically — about
2 times in 5 full-suite runs — on the pre-fix code, via a full `tests/eventbus/`
run rather than this narrower test). See
implementations/done/20260913-102829_01_scripts_eventbus_app_py.md.

This test drives `lifespan()` directly (bypassing `TestClient`, whose own
startup/shutdown timing was found to be too non-deterministic to reliably force
the race — the very first sweep can complete before `TestClient.__enter__`
itself returns) and uses a `threading.Event` to deterministically confirm the
sweep thread has actually started running before exiting the `lifespan()`
context (triggering its shutdown code — the fix under test), removing the
timing non-determinism a fixed `time.sleep()` would leave.
"""

from __future__ import annotations

import asyncio
import sqlite3
import threading
from pathlib import Path
from typing import Any, cast

import pytest
from fastapi import FastAPI

_SCHEMA_PATH = Path(__file__).parent.parent.parent / "schemas" / "event_envelope.json"


def _make_config(tmp_path: Path) -> Any:
    from eventbus.config import EventBusConfig

    return EventBusConfig(
        port=8015,
        db_path=str(tmp_path / "eventbus.sqlite"),
        storage_dir=str(tmp_path / "storage"),
        deadletter_dir=str(tmp_path / "deadletter"),
        max_retry=3,
        auth_token="test-token",
    )


@pytest.mark.asyncio
async def test_shutdown_waits_for_inflight_sweep_before_closing_db(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Deterministically force `_dlq_loop`'s sweep thread to be running when
    `lifespan()`'s shutdown sequence runs, and confirm it completes without
    crashing the process."""
    from eventbus import app as eb_app

    cfg = _make_config(tmp_path)
    monkeypatch.setattr(eb_app, "load_config", lambda path=None: cfg)
    monkeypatch.setattr(eb_app, "get_schema_path", lambda: _SCHEMA_PATH)

    sweep_started = threading.Event()
    release_sweep = threading.Event()

    def blocking_sweep_orphans(db: Any, deadletter_dir: str, max_retry: int) -> int:
        sweep_started.set()
        # Hold the worker thread (and, via run_with_db_lock, get_db_lock())
        # until the test explicitly releases it, simulating a sweep that is
        # still running when shutdown begins.
        release_sweep.wait(timeout=5)
        return 0

    monkeypatch.setattr(eb_app, "sweep_orphans", blocking_sweep_orphans)
    monkeypatch.setattr(eb_app, "_DLQ_INTERVAL", 3600.0)  # only the first sweep matters

    async def _release_after_delay() -> None:
        # Release shortly after lifespan's shutdown code (the `async with`
        # block below exiting) has had a chance to begin, simulating the
        # in-flight sweep finishing while shutdown is waiting for it.
        await asyncio.sleep(0.2)
        release_sweep.set()

    async with eb_app.lifespan(eb_app.app):
        # Deterministically wait for the sweep thread to actually start (not a
        # fixed sleep) before proceeding — this removes the timing
        # non-determinism that made the race hard to force via TestClient.
        started = await asyncio.to_thread(sweep_started.wait, 5)
        assert started, "sweep thread did not start within the timeout"
        release_task = asyncio.create_task(_release_after_delay())
        # Exiting this `async with` block here runs lifespan()'s shutdown
        # sequence — the code under test — while the sweep thread is
        # confirmed still in flight.

    await release_task

    # Reaching this line means shutdown completed without a segfault — a
    # crash would have killed the test process before this line ran.
    assert True


@pytest.mark.asyncio
async def test_shutdown_raises_when_lock_timeout_exceeded(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When the sweep still holds the lock when the shutdown timeout elapses,
    shutdown must refuse to close the connection by raising, rather
    than logging a warning and closing anyway (the removed fallback)."""
    from eventbus import app as eb_app

    cfg = _make_config(tmp_path)
    monkeypatch.setattr(eb_app, "load_config", lambda path=None: cfg)
    monkeypatch.setattr(eb_app, "get_schema_path", lambda: _SCHEMA_PATH)
    monkeypatch.setattr(eb_app, "_SHUTDOWN_DB_LOCK_TIMEOUT_SECONDS", 0.05)

    sweep_started = threading.Event()
    release_sweep = threading.Event()

    def blocking_sweep_orphans(db: Any, deadletter_dir: str, max_retry: int) -> int:
        sweep_started.set()
        # Hold the lock (via run_with_db_lock) so the shutdown lock-acquire
        # cannot succeed within the bound, exercising the refuse-to-close path.
        release_sweep.wait(timeout=5)
        return 0

    monkeypatch.setattr(eb_app, "sweep_orphans", blocking_sweep_orphans)
    monkeypatch.setattr(eb_app, "_DLQ_INTERVAL", 3600.0)

    try:
        with pytest.raises(RuntimeError, match="could not acquire db lock within"):
            async with eb_app.lifespan(eb_app.app):
                started = await asyncio.to_thread(sweep_started.wait, 5)
                assert started, "sweep thread did not start within the timeout"
                # Deliberately do not release the sweep here — the shutdown
                # lock-acquire (timeout 0.05s) must exceed its bound while the
                # sweep still holds the lock, so lifespan() raises.
    finally:
        # Let the still-blocked sweep thread exit before the test ends.
        release_sweep.set()


@pytest.mark.asyncio
async def test_run_with_db_lock_refuses_after_shutdown_flag() -> None:
    """Once set_shutdown_flag() has run, run_with_db_lock() must raise
    before spawning a worker thread, so no thread queues on the lock behind a
    connection that is about to be closed."""
    from eventbus import db_conn
    from eventbus.route_helpers import run_with_db_lock

    db_conn.set_shutdown_flag()  # conftest _reset_db_conn_state restores it after
    with pytest.raises(RuntimeError, match="refusing new DB work"):
        await run_with_db_lock(lambda: None)


@pytest.mark.asyncio
async def test_queued_worker_refuses_sql_after_shutdown_began(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A worker admitted before shutdown that acquires the lock after the
    flag is set must raise the shutdown error and never run `func`."""
    from eventbus import db as eb_db
    from eventbus import db_conn
    from eventbus.route_helpers import run_with_db_lock

    real_lock = threading.Lock()
    worker_waiting = threading.Event()

    class _SignalingLock:
        """Signal that a worker reached the lock, then block on the real lock."""

        def __enter__(self) -> None:
            worker_waiting.set()
            real_lock.acquire()

        def __exit__(self, *exc_info: object) -> None:
            real_lock.release()

    monkeypatch.setattr(eb_db, "get_db_lock", lambda: _SignalingLock())
    calls: list[int] = []

    real_lock.acquire()  # the test plays the role of the lock holder
    task = asyncio.create_task(run_with_db_lock(lambda: calls.append(1)))
    assert await asyncio.to_thread(worker_waiting.wait, 5), "worker never queued"

    db_conn.set_shutdown_flag()  # conftest _reset_db_conn_state restores it
    real_lock.release()

    with pytest.raises(RuntimeError, match="refusing new DB work"):
        await asyncio.wait_for(task, 5)
    assert calls == []


@pytest.mark.asyncio
async def test_inflight_request_completes_before_connection_close() -> None:
    """An admitted worker holding the lock finishes before shutdown closes the db."""
    from types import SimpleNamespace
    from unittest.mock import MagicMock

    from eventbus import app as eb_app
    from eventbus import db_conn
    from eventbus.route_helpers import run_with_db_lock

    order: list[str] = []
    worker_started = threading.Event()
    release_worker = threading.Event()

    def _inflight() -> None:
        worker_started.set()
        release_worker.wait(timeout=5)
        order.append("worker_done")

    db = MagicMock()
    db.close.side_effect = lambda: order.append("closed")
    app = SimpleNamespace(state=SimpleNamespace(dlq_task=None, broker=None, db=db))

    worker = asyncio.create_task(run_with_db_lock(_inflight))
    assert await asyncio.to_thread(worker_started.wait, 5), "worker never started"
    shutdown = asyncio.create_task(eb_app._shutdown_lifespan(cast(FastAPI, app)))
    for _ in range(100):  # yield until shutdown has begun, without sleeping
        if db_conn.is_shutting_down():
            break
        await asyncio.sleep(0)
    assert db_conn.is_shutting_down()

    release_worker.set()
    await asyncio.wait_for(worker, 5)
    await asyncio.wait_for(shutdown, 5)
    assert order == ["worker_done", "closed"]


@pytest.mark.asyncio
async def test_shutdown_clears_app_state_db(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """After shutdown the shared reference is cleared, so a later lookup
    raises the explicit not-initialized error instead of returning a closed db."""
    from eventbus import app as eb_app
    from eventbus.route_helpers import app_get_db

    cfg = _make_config(tmp_path)
    monkeypatch.setattr(eb_app, "load_config", lambda path=None: cfg)
    monkeypatch.setattr(eb_app, "get_schema_path", lambda: _SCHEMA_PATH)
    monkeypatch.setattr(eb_app, "_DLQ_INTERVAL", 3600.0)

    async with eb_app.lifespan(eb_app.app):
        assert app_get_db(eb_app.app) is not None

    assert eb_app.app.state.db is None
    with pytest.raises(RuntimeError, match="db not initialized"):
        app_get_db(eb_app.app)


@pytest.mark.asyncio
async def test_second_lifecycle_does_not_inherit_shutdown_flag(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A fresh lifespan clears the shutdown flag left by the previous one."""
    from eventbus import app as eb_app
    from eventbus.route_helpers import run_with_db_lock

    cfg = _make_config(tmp_path)
    monkeypatch.setattr(eb_app, "load_config", lambda path=None: cfg)
    monkeypatch.setattr(eb_app, "get_schema_path", lambda: _SCHEMA_PATH)
    monkeypatch.setattr(eb_app, "_DLQ_INTERVAL", 3600.0)

    async with eb_app.lifespan(eb_app.app):
        pass
    async with eb_app.lifespan(eb_app.app):
        assert await run_with_db_lock(lambda: 42) == 42


@pytest.mark.asyncio
async def test_second_lifecycle_opens_new_usable_connection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Two sequential lifespans: the second opens a new connection and never reuses
    the closed first one, and the shutdown flag does not leak into it."""
    from eventbus import app as eb_app
    from eventbus.route_helpers import run_with_db_lock

    cfg = _make_config(tmp_path)
    monkeypatch.setattr(eb_app, "load_config", lambda path=None: cfg)
    monkeypatch.setattr(eb_app, "get_schema_path", lambda: _SCHEMA_PATH)
    monkeypatch.setattr(eb_app, "_DLQ_INTERVAL", 3600.0)

    async with eb_app.lifespan(eb_app.app):
        first_db = eb_app.app.state.db
    async with eb_app.lifespan(eb_app.app):
        second_db = eb_app.app.state.db
        assert second_db is not None
        assert second_db is not first_db
        assert (
            await run_with_db_lock(lambda: second_db.execute("SELECT 1").fetchone()[0])
            == 1
        )

    with pytest.raises(sqlite3.ProgrammingError):
        first_db.execute("SELECT 1")


@pytest.mark.asyncio
async def test_shutdown_joins_inflight_outbox_cycle_before_closing_db(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """REQ-008/AC-6: shutdown with an outbox cycle in flight joins dlq_task and
    closes the connection only behind the lock; the pending row survives intact."""
    from eventbus import app as eb_app
    from eventbus import dlq
    from eventbus.db import open_db
    from eventbus.dlq import now_iso

    cfg = _make_config(tmp_path)
    monkeypatch.setattr(eb_app, "load_config", lambda path=None: cfg)
    monkeypatch.setattr(eb_app, "get_schema_path", lambda: _SCHEMA_PATH)
    monkeypatch.setattr(eb_app, "_DLQ_INTERVAL", 3600.0)  # only the first cycle matters

    # Seed a promoted event with a pending outbox row before the app starts,
    # so the lifespan's first dlq_loop cycle enters process_outbox immediately.
    db = open_db(cfg.db_path)
    event_id = "outbox-shutdown-inflight"
    db.execute(
        "INSERT INTO events (event_id, topic, payload, producer, published_at, dlq_at)"
        " VALUES (?, ?, ?, ?, ?, ?)",
        (
            event_id,
            "t",
            '{"key": "value"}',
            "test-producer",
            "2026-01-01T00:00:00Z",
            now_iso(),
        ),
    )
    db.execute(
        "INSERT INTO dlq_outbox (event_id, requested_at) VALUES (?, ?)",
        (event_id, now_iso()),
    )
    db.commit()
    db.close()

    fetch_started = threading.Event()
    release_fetch = threading.Event()
    real_fetch = dlq.fetch_due_pending

    def blocking_fetch(db_arg: Any, now: str) -> Any:
        fetch_started.set()
        # Hold the worker thread (and, via run_with_db_lock, get_db_lock())
        # inside the outbox fetch, simulating a cycle still running at shutdown.
        release_fetch.wait(timeout=5)
        return real_fetch(db_arg, now)

    monkeypatch.setattr(dlq, "fetch_due_pending", blocking_fetch)

    async def _release_after_delay() -> None:
        # Release shortly after lifespan's shutdown sequence has begun,
        # simulating the in-flight cycle finishing while shutdown waits for it.
        await asyncio.sleep(0.2)
        release_fetch.set()

    with caplog.at_level("ERROR"):
        async with eb_app.lifespan(eb_app.app):
            started = await asyncio.to_thread(fetch_started.wait, 5)
            assert started, "outbox fetch thread did not start within the timeout"
            release_task = asyncio.create_task(_release_after_delay())
            # Exiting here runs the shutdown sequence while the cycle is in flight.
        await release_task

    # No closed-connection use anywhere in the shutdown sequence.
    assert "ProgrammingError" not in caplog.text

    # The cancelled cycle never touched the row: it stays a clean pending row,
    # consumable by the next process (no half-committed state).
    db2 = open_db(cfg.db_path)
    try:
        row = db2.execute(
            "SELECT status, attempts, last_error FROM dlq_outbox WHERE event_id = ?",
            (event_id,),
        ).fetchone()
        assert row["status"] == "pending"
        assert row["attempts"] == 0
        assert row["last_error"] is None
        due = real_fetch(db2, now_iso())
        assert [str(r["event_id"]) for r in due] == [event_id]
    finally:
        db2.close()


@pytest.mark.asyncio
async def test_dlq_loop_logs_outbox_and_reconcile_activity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """REQ-004/REQ-007: a dlq_loop cycle that processes outbox rows and finds an
    outbox inconsistency logs both warnings; the pending row completes and the
    orphan file is reported, never deleted."""
    from eventbus import app as eb_app
    from eventbus.db import open_db
    from eventbus.dlq import now_iso

    cfg = _make_config(tmp_path)
    monkeypatch.setattr(eb_app, "load_config", lambda path=None: cfg)
    monkeypatch.setattr(eb_app, "get_schema_path", lambda: _SCHEMA_PATH)
    monkeypatch.setattr(eb_app, "_DLQ_INTERVAL", 3600.0)  # only the first cycle matters

    # Seed a promoted event with a due pending outbox row, plus a stray DLQ file
    # with no event row and no done outbox row (an orphan), before the app starts.
    Path(cfg.deadletter_dir).mkdir(parents=True, exist_ok=True)
    orphan_file = Path(cfg.deadletter_dir) / "no-such-event.json"
    orphan_file.write_text('{"event_id": "no-such-event"}', encoding="utf-8")

    db = open_db(cfg.db_path)
    event_id = "outbox-loop-pending"
    db.execute(
        "INSERT INTO events (event_id, topic, payload, producer, published_at, dlq_at)"
        " VALUES (?, ?, ?, ?, ?, ?)",
        (
            event_id,
            "t",
            '{"key": "value"}',
            "test-producer",
            "2026-01-01T00:00:00Z",
            now_iso(),
        ),
    )
    db.execute(
        "INSERT INTO dlq_outbox (event_id, requested_at) VALUES (?, ?)",
        (event_id, now_iso()),
    )
    db.commit()
    db.close()

    reconcile_finished = threading.Event()
    real_reconcile = eb_app.reconcile_missing_dlq_files

    def _spy_reconcile(db_arg: Any, deadletter_dir: str) -> dict[str, int]:
        result = real_reconcile(db_arg, deadletter_dir)
        reconcile_finished.set()  # the cycle's last step has run
        return result

    monkeypatch.setattr(eb_app, "reconcile_missing_dlq_files", _spy_reconcile)

    with caplog.at_level("WARNING"):
        async with eb_app.lifespan(eb_app.app):
            done = await asyncio.to_thread(reconcile_finished.wait, 10)
            assert done, "dlq_loop first cycle did not complete"

    assert "outbox processed=1 generated=1" in caplog.text
    assert "reconcile checked=1" in caplog.text
    assert "orphans=1" in caplog.text

    db2 = open_db(cfg.db_path)
    try:
        row = db2.execute(
            "SELECT status FROM dlq_outbox WHERE event_id = ?", (event_id,)
        ).fetchone()
        assert row["status"] == "done"
        assert (Path(cfg.deadletter_dir) / f"{event_id}.json").exists()
        assert orphan_file.exists()  # report-only: reconcile never deletes orphans
    finally:
        db2.close()
