"""tests/db/test_helper_thread_safety.py
REQ-005 threading probes for db/helper.py: SQLiteHelper cross-thread behavior.

These probes gate the scripts/agent/turn_persistence.py offload wiring (REQ-005):
they prove the per-call open pattern is safe inside asyncio.to_thread workers,
that check_same_thread=False (REQ-002) permits sequential cross-thread reuse, and
that the default True keeps the sqlite3 same-thread assertion in force.

The last three probes cover the db write gate (cliplc004 REQ-004, REQ-005) on the
same threaded paths: an authorization held by a shutdown step reaches the worker
thread it started, a thread outside the authorization does not inherit it, and an
authorization started inside a worker does not leak back to the caller.
"""

from __future__ import annotations

import asyncio
import sqlite3
from collections.abc import Iterator
from pathlib import Path

import pytest
from db.helper import SQLiteHelper
from db.write_gate import WriteGate, WriteGateClosed, get_write_gate

_SCHEMA = "CREATE TABLE probe (id INTEGER PRIMARY KEY, val TEXT);"


@pytest.fixture(autouse=True)
def _gate_open() -> Iterator[WriteGate]:
    """Hand every probe in this file an open process-wide gate, and leave one open.

    The probes drive the exact write entry points the shutdown gate now guards, so
    a gate closed by an earlier case in the same xdist worker would fail them.
    """
    gate = get_write_gate()
    gate.reset()
    yield gate
    gate.reset()


def _make_helper(tmp_path: Path, check_same_thread: bool = True) -> SQLiteHelper:
    """Create a tmp-file-backed SQLiteHelper with one table (explicit-path branch)."""
    db_path = tmp_path / "probe.db"
    conn = sqlite3.connect(db_path)
    conn.execute(_SCHEMA)
    conn.commit()
    conn.close()
    return SQLiteHelper(db_path=str(db_path), check_same_thread=check_same_thread)


async def test_per_call_open_pattern_safe_in_worker_thread(tmp_path: Path) -> None:
    """Probe 1: connect-use-close entirely inside a worker thread succeeds, twice."""
    helper = _make_helper(tmp_path)

    def write_row(value: str) -> None:
        with helper.open(write_mode=True):
            helper.execute("INSERT INTO probe (val) VALUES (?)", (value,))
            helper.commit()

    await asyncio.to_thread(write_row, "first")
    await asyncio.to_thread(write_row, "second")

    with helper.open() as db:
        rows = db.execute("SELECT val FROM probe ORDER BY id").fetchall()
    assert [row[0] for row in rows] == ["first", "second"]


async def test_check_same_thread_false_sequential_cross_thread_ok(
    tmp_path: Path,
) -> None:
    """Probe 2: a False connection opened on main thread is used sequentially on a worker."""
    helper = _make_helper(tmp_path, check_same_thread=False)

    def use_conn() -> None:
        helper.execute("INSERT INTO probe (val) VALUES (?)", ("worker",))
        helper.commit()

    helper.open(write_mode=True)
    try:
        await asyncio.to_thread(use_conn)
        rows = helper.execute("SELECT val FROM probe").fetchall()
    finally:
        helper.close()
    assert [row[0] for row in rows] == ["worker"]


async def test_default_check_same_thread_true_cross_thread_raises(
    tmp_path: Path,
) -> None:
    """Probe 3: the default True connection used from another thread raises ProgrammingError."""
    helper = _make_helper(tmp_path)

    def use_conn() -> None:
        helper.execute("SELECT val FROM probe").fetchall()

    helper.open()
    try:
        with pytest.raises(sqlite3.ProgrammingError):
            await asyncio.to_thread(use_conn)
    finally:
        helper.close()  # owner-thread teardown: never leaks an error


async def test_open_check_same_thread_override_applies_to_that_open(
    tmp_path: Path,
) -> None:
    """Probe 4: the per-open override opens a False connection despite the True default."""
    helper = _make_helper(tmp_path)

    def use_conn() -> None:
        helper.execute("INSERT INTO probe (val) VALUES (?)", ("override",))
        helper.commit()

    helper.open(write_mode=True, check_same_thread=False)
    try:
        await asyncio.to_thread(use_conn)
        rows = helper.execute("SELECT val FROM probe").fetchall()
    finally:
        helper.close()
    assert [row[0] for row in rows] == ["override"]


async def test_authorized_step_reaches_a_worker_thread_when_gate_closed(
    tmp_path: Path,
) -> None:
    """Probe 5: asyncio.to_thread copies the caller's context, so a shutdown step
    that authorized its writes reaches the DB from the worker thread it started."""
    gate = get_write_gate()
    helper = _make_helper(tmp_path)

    def write_row(value: str) -> None:
        with helper.open(write_mode=True):
            helper.execute("INSERT INTO probe (val) VALUES (?)", (value,))
            helper.commit()

    gate.close_now()
    with gate.authorize("persist_snapshot"):
        await asyncio.to_thread(write_row, "authorized")

    with helper.open() as db:
        rows = db.fetchall("SELECT val FROM probe")
    assert [row[0] for row in rows] == ["authorized"]
    assert gate.refused_count == 0


async def test_unauthorized_worker_thread_is_refused_when_gate_closed(
    tmp_path: Path,
) -> None:
    """Probe 6: a thread not started inside the authorization does not inherit it,
    which is what turns a leftover background writer into a counted refusal."""
    gate = get_write_gate()
    helper = _make_helper(tmp_path)

    def write_row() -> None:
        with helper.open(write_mode=True):
            helper.execute("INSERT INTO probe (val) VALUES (?)", ("late",))
            helper.commit()

    gate.close_now()
    with pytest.raises(WriteGateClosed):
        await asyncio.to_thread(write_row)
    assert gate.refused_count == 1

    with helper.open() as db:
        assert db.fetchall("SELECT val FROM probe") == []


async def test_authorization_started_in_a_worker_thread_does_not_reach_the_caller(
    tmp_path: Path,
) -> None:
    """Probe 7: an authorization entered inside the worker is gone when the worker
    returns, so it cannot unlock the thread that scheduled the next step."""
    gate = get_write_gate()
    helper = _make_helper(tmp_path)

    def authorized_write() -> None:
        with gate.authorize("checkpoint"), helper.open(write_mode=True):
            helper.execute("INSERT INTO probe (val) VALUES (?)", ("worker",))
            helper.commit()

    gate.close_now()
    await asyncio.to_thread(authorized_write)

    assert gate.authorized_step is None
    with pytest.raises(WriteGateClosed):
        helper.open(write_mode=True)
