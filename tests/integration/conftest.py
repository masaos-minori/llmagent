"""Shared fixtures for integration tests."""

from __future__ import annotations

import asyncio
import os
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any

import pytest


@pytest.fixture
async def stdio_echo_server():
    """Minimal stdio MCP server that echoes requests with ID field."""
    script = (
        "import sys, json\n"
        "for line in sys.stdin:\n"
        "    req = json.loads(line)\n"
        "    resp = {'id': req['id'], 'result': f'echo:{req[\"name\"]}', 'is_error': False, 'truncated': False, 'total_bytes': 0}\n"
        "    sys.stdout.write(json.dumps(resp) + '\\n')\n"
        "    sys.stdout.flush()\n"
    )
    proc = await asyncio.create_subprocess_exec(
        "python",
        "-c",
        script,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
    )
    yield proc
    if proc.returncode is None:
        proc.terminate()
        await proc.wait()


@pytest.fixture
def tmp_sqlite_db(tmp_path: Path) -> str:
    """Temp SQLite DB with workflow schema initialized."""
    from scripts.db.create_schema import create_workflow_schema

    # Create workflow schema in temp directory
    old_cwd = os.getcwd()
    os.chdir(str(tmp_path))
    try:
        create_workflow_schema()
    finally:
        os.chdir(old_cwd)

    db_path = str(tmp_path / "workflow.sqlite")
    return db_path


def make_llm_stream(tokens: list[str], error: Exception | None = None):
    """Return an async generator that yields token deltas and optionally raises."""

    async def _stream(*args: Any, **kwargs: Any):
        for t in tokens:
            yield {"type": "content_block_delta", "delta": {"text": t}}
        if error is not None:
            raise error

    return _stream


def hold_write_lock(db_path: str, duration_sec: float) -> threading.Thread:
    """Start a thread that holds a SQLite EXCLUSIVE lock for duration_sec seconds."""

    def _lock() -> None:
        conn = sqlite3.connect(db_path, timeout=0)
        conn.execute("PRAGMA locking_mode = EXCLUSIVE")
        conn.execute("BEGIN EXCLUSIVE")
        time.sleep(duration_sec)
        conn.close()

    t = threading.Thread(target=_lock, daemon=True)
    t.start()
    return t


@pytest.fixture
async def hanging_stdio_process():
    """Subprocess that reads one line from stdin, then sleeps forever.

    Used to test bounded-timeout reads against a wedged MCP server
    subprocess (see tests/integration/test_mcp_transport_crash.py).
    """
    script = "import sys, time\nsys.stdin.readline()\ntime.sleep(3600)\n"
    proc = await asyncio.create_subprocess_exec(
        "python",
        "-c",
        script,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
    )
    yield proc
    if proc.returncode is None:
        proc.kill()
        await proc.wait()


def _has_table(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone()
    return row is not None


@pytest.fixture
def corrupt_wal_db(tmp_path: Path) -> str:
    """A WAL-mode session-schema SQLite DB, byte-truncated to fail
    PRAGMA integrity_check while still opening successfully via
    sqlite3.connect() (header intact, b-tree pages corrupted).

    Used by tests/integration/test_session_recovery.py.
    """
    from db.schema_sql import build_session_schema_sql

    db_path = str(tmp_path / "corrupt.sqlite")
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    try:
        conn.executescript(build_session_schema_sql(4))
    except Exception:
        pass  # memories_vec may be unavailable without sqlite-vec; ignore
    if _has_table(conn, "sessions"):
        conn.execute("INSERT INTO sessions (session_id) VALUES (1)")
    conn.commit()
    conn.close()

    # Byte-level truncation: corrupts b-tree pages while preserving the
    # SQLite header (first 16 bytes), so sqlite3.connect() still succeeds
    # but PRAGMA integrity_check fails. Offset confirmed empirically
    # during implementation (see plan UNK-02 resolution).
    size = Path(db_path).stat().st_size
    with open(db_path, "r+b") as f:
        f.seek(size // 2)
        f.truncate()

    return db_path
