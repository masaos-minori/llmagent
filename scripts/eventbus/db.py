from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)

_SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def open_db(db_path: str) -> sqlite3.Connection:
    """Return a shared SQLite connection for the Event Bus.

    Uses check_same_thread=False because FastAPI runs on a single async event
    loop thread; WAL mode serializes concurrent writers at the SQLite level.
    A single shared connection avoids per-request churn and is safe here.
    """
    try:
        conn = sqlite3.connect(db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        _init_schema(conn)
        return conn
    except sqlite3.Error as exc:
        logger.error(
            "eventbus: failed to open SQLite connection path=%s err=%s", db_path, exc
        )
        raise


def _init_schema(conn: sqlite3.Connection) -> None:
    sql = _SCHEMA_PATH.read_text()
    conn.executescript(sql)
