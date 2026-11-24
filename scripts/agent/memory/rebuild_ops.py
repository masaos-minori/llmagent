#!/usr/bin/env python3
"""scripts/agent/memory/rebuild_ops.py — Rebuild operations for memory tables."""

from __future__ import annotations

import sqlite3
import threading

from db.config import DbConfig
from db.helper import SQLiteHelper

from agent.memory.models import MemoryMaintenanceResult


def _interrupted(operation: str) -> MemoryMaintenanceResult:
    """Report a run the cancellation event stopped: it rolled back, so it measured nothing."""
    return MemoryMaintenanceResult(operation=operation, interrupted=True)


def rebuild_fts(
    db: SQLiteHelper,
    *,
    db_config: DbConfig,
    stop: threading.Event | None = None,
) -> MemoryMaintenanceResult:
    """Rebuild memories_fts from the memories table inside one transaction.

    `db` is the connection the `MemoryStore` accessor opened for the run; the transaction
    boundary is the store's, so this module supplies only the statements inside it. The
    reported count is the FTS row count measured after the commit, not the number of
    inserts attempted, and an interrupted run rolls back so it reports no count (REQ-006).
    """
    if stop is not None:
        db.interrupt_when(stop)
    try:
        with db.begin_immediate():
            db.execute("DELETE FROM memories_fts")
            rows = db.fetchall("SELECT memory_id, content, summary, tags FROM memories")
            for row in rows:
                db.execute(
                    "INSERT INTO memories_fts(memory_id, content, summary, tags) VALUES (?,?,?,?)",
                    (row["memory_id"], row["content"], row["summary"], row["tags"]),
                )
            attempted = len(rows)
    except sqlite3.Error:
        return _interrupted("reindex")

    count = _scalar(db, "SELECT COUNT(*) FROM memories_fts")
    return MemoryMaintenanceResult(
        operation="reindex",
        count=count,
        verified=count == attempted,
    )


def rebuild_vec(
    db: SQLiteHelper,
    *,
    db_config: DbConfig,
    stop: threading.Event | None = None,
) -> MemoryMaintenanceResult:
    """Remove memories_vec rows that have no matching memories row, inside one transaction.

    Embeddings live only in `memories_vec`: the `memories` table has no embedding column
    (`scripts/db/schema_sql.py:100-118`), so vector rows cannot be regenerated from the
    source table. The postcondition this run can measure is that the index holds no row for
    a memory that no longer exists, which is the same contract as the RAG vector prune
    (`scripts/agent/services/rag_maintenance_service.py:92-97`). The reported count is the
    rows removed, measured after the commit.
    """
    if stop is not None:
        db.interrupt_when(stop)
    try:
        with db.begin_immediate():
            cur = db.execute(
                "DELETE FROM memories_vec WHERE memory_id NOT IN "
                "(SELECT memory_id FROM memories)"
            )
            removed = cur.rowcount
    except sqlite3.Error:
        return _interrupted("reindex")

    orphans = _scalar(
        db,
        "SELECT COUNT(*) FROM memories_vec WHERE memory_id NOT IN (SELECT memory_id FROM memories)",
    )
    return MemoryMaintenanceResult(
        operation="reindex",
        count=removed,
        verified=orphans == 0,
    )


def _scalar(db: SQLiteHelper, sql: str) -> int:
    """Return the scalar result of a count query on the caller's connection."""
    rows = db.fetchall(sql)
    return int(rows[0][0]) if rows else 0


def reindex(
    index_type: str,
    *,
    db_config: DbConfig,
    db: SQLiteHelper | None = None,
    stop: threading.Event | None = None,
) -> MemoryMaintenanceResult:
    """Rebuild a single memory index ('fts' or 'vec'); return the measured outcome.

    `db` is the connection the `MemoryStore` accessor opened for the run; without it this
    function opens its own, which is the only place the Memory package opens a connection.
    """
    if index_type not in ("fts", "vec"):
        raise ValueError(f"Unknown index type {index_type!r}; expected 'fts' or 'vec'")
    if db is not None:
        return (
            rebuild_fts(db, db_config=db_config, stop=stop)
            if index_type == "fts"
            else rebuild_vec(db, db_config=db_config, stop=stop)
        )

    with SQLiteHelper("session", db_config=db_config).open(write_mode=True) as own:
        own.interrupt_when(stop)
        return reindex(index_type, db_config=db_config, db=own, stop=stop)
