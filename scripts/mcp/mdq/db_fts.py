#!/usr/bin/env python3
"""mcp/mdq/db_fts.py

FTS5 operations for MdqService.

Dependency direction: db_fts → models
Import from here:  from mcp.mdq.db_fts import fts_consistency_check, fts_rebuild
"""

from __future__ import annotations

import sqlite3

from mcp.mdq.models import MdqConsistencyError


def fts_consistency_check(conn: sqlite3.Connection) -> str:
    """Check FTS5 consistency between chunks and chunks_fts tables."""
    try:
        chunks_count = conn.execute(
            "SELECT COUNT(*) as cnt FROM chunks"
        ).fetchone()["cnt"]
        fts_count = conn.execute(
            "SELECT COUNT(*) as cnt FROM chunks_fts"
        ).fetchone()["cnt"]
        integrity_rows = conn.execute("PRAGMA integrity_check").fetchall()
        integrity_ok = all(row[0] == "ok" for row in integrity_rows)
        consistent = chunks_count == fts_count
        status = "consistent" if consistent else "INCONSISTENT"
        if not integrity_ok:
            status = "INTEGRITY_ERROR"
        return (
            f"FTS5 consistency check: {status}\n"
            f"  chunks rows: {chunks_count}\n"
            f"  chunks_fts rows: {fts_count}\n"
            f"  integrity_check: {'ok' if integrity_ok else 'FAILED'}"
        )
    except sqlite3.OperationalError as e:
        raise MdqConsistencyError(f"FTS5 table missing or corrupted: {e}") from e


def fts_rebuild(conn: sqlite3.Connection, chunks_count: int) -> str:
    """Rebuild the FTS5 index."""
    try:
        conn.execute("BEGIN IMMEDIATE")
        conn.execute("INSERT INTO chunks_fts(chunks_fts) VALUES('rebuild')")
        conn.execute("COMMIT")
        return f"FTS5 index rebuilt successfully (chunks: {chunks_count})"
    except sqlite3.Error as e:
        try:
            conn.execute("ROLLBACK")
        except sqlite3.Error:
            pass
        return f"FTS5 rebuild failed: {e}"
