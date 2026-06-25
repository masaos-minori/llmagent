"""Shared fixtures for integration tests."""

from __future__ import annotations

import asyncio
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
    from db.workflow_schema import init_schema

    db_path = str(tmp_path / "test.sqlite")
    init_schema(db_path)
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
