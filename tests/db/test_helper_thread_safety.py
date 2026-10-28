"""tests/db/test_helper_thread_safety.py
REQ-005 threading probes for db/helper.py: SQLiteHelper cross-thread behavior.

These probes gate the scripts/agent/turn_persistence.py offload wiring (REQ-005):
they prove the per-call open pattern is safe inside asyncio.to_thread workers,
that check_same_thread=False (REQ-002) permits sequential cross-thread reuse, and
that the default True keeps the sqlite3 same-thread assertion in force.
"""

from __future__ import annotations

import asyncio
import sqlite3
from pathlib import Path

import pytest
from db.helper import SQLiteHelper

_SCHEMA = "CREATE TABLE probe (id INTEGER PRIMARY KEY, val TEXT);"


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
