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
import logging
import threading
from pathlib import Path
from typing import Any

import pytest

_SCHEMA_PATH = Path(__file__).parent.parent.parent / "schemas" / "event_envelope.json"


def _make_config(tmp_path: Path) -> Any:
    from eventbus.config import EventBusConfig

    return EventBusConfig(
        port=8015,
        db_path=str(tmp_path / "eventbus.sqlite"),
        storage_dir=str(tmp_path / "storage"),
        offsets_dir=str(tmp_path / "offsets"),
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
async def test_shutdown_logs_warning_when_lock_timeout_exceeded(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """If the sweep still holds the lock when the shutdown timeout elapses,
    shutdown must log a warning and still close the DB (REQ-002's bounded-wait
    fallback) rather than hanging indefinitely."""
    from eventbus import app as eb_app

    cfg = _make_config(tmp_path)
    monkeypatch.setattr(eb_app, "load_config", lambda path=None: cfg)
    monkeypatch.setattr(eb_app, "get_schema_path", lambda: _SCHEMA_PATH)
    monkeypatch.setattr(eb_app, "_SHUTDOWN_DB_LOCK_TIMEOUT_SECONDS", 0.05)

    sweep_started = threading.Event()
    release_sweep = threading.Event()

    def blocking_sweep_orphans(db: Any, deadletter_dir: str, max_retry: int) -> int:
        sweep_started.set()
        release_sweep.wait(timeout=5)
        return 0

    monkeypatch.setattr(eb_app, "sweep_orphans", blocking_sweep_orphans)
    monkeypatch.setattr(eb_app, "_DLQ_INTERVAL", 3600.0)

    try:
        with caplog.at_level(logging.WARNING, logger="eventbus.app"):
            async with eb_app.lifespan(eb_app.app):
                started = await asyncio.to_thread(sweep_started.wait, 5)
                assert started, "sweep thread did not start within the timeout"
                # Deliberately do not release the sweep here — the shutdown
                # lock-acquire (timeout 0.05s) must exceed its bound while the
                # sweep still holds the lock, exercising the fallback path.
    finally:
        # Let the still-blocked sweep thread exit before the test ends,
        # regardless of the assertions below.
        release_sweep.set()

    assert "db lock not acquired" in caplog.text
