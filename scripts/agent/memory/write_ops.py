#!/usr/bin/env python3
"""scripts/agent/memory/write_ops.py — Write operations for memory CRUD."""

import logging
import sqlite3
import threading

from db.config import DbConfig
from db.helper import SQLiteHelper
from shared.json_utils import dumps, now_iso

from agent.memory.mapper import _floats_to_blob, _stamp_entry
from agent.memory.models import MemoryMaintenanceResult
from agent.memory.sql_constants import _INSERT_SQL, _UPSERT_SQL
from agent.memory.types import MemoryEntry

logger = logging.getLogger(__name__)


def _build_row_params(entry: MemoryEntry) -> tuple[object, ...]:
    """Return the param tuple for a memories INSERT statement."""
    tags_json = dumps(entry.tags)
    return (
        entry.memory_id,
        entry.memory_type,
        entry.source_type,
        entry.session_id,
        entry.turn_id,
        entry.project,
        entry.repo,
        entry.branch,
        entry.content,
        entry.summary,
        tags_json,
        entry.importance,
        int(entry.pinned),
        entry.created_at,
        entry.updated_at,
    )


def _write_fts(db: SQLiteHelper, entry: MemoryEntry) -> None:
    """Sync one row into memories_fts; caller must be inside a transaction."""
    db.execute(
        "INSERT INTO memories_fts(memory_id, content, summary, tags) VALUES (?,?,?,?)",
        (entry.memory_id, entry.content, entry.summary, " ".join(entry.tags)),
    )


def _write_vec(
    db: SQLiteHelper, memory_id: str, embedding: list[float], embed_dim: int | None
) -> None:
    """Upsert one embedding into memories_vec; raises on failure."""
    db.execute(
        "INSERT OR REPLACE INTO memories_vec(memory_id, embedding) VALUES (?,?)",
        (memory_id, _floats_to_blob(embedding, embed_dim)),
    )


def add(
    entry: MemoryEntry,
    embedding: list[float] | None = None,
    embed_dim: int | None = None,
    *,
    db_config: DbConfig,
    db: SQLiteHelper | None = None,
) -> None:
    """Insert a new MemoryEntry; sets created_at/updated_at if empty.

    When embedding is provided, also writes to memories_vec for KNN search.
    Uses BEGIN IMMEDIATE for atomicity across memories + memories_fts + memories_vec.
    `db` is the connection a caller that owns the transaction supplies, such as the import
    run through the `MemoryStore` accessor; without it this function opens its own.
    """
    now = now_iso()
    stamped = _stamp_entry(entry, now)
    if db is not None:
        _insert_entry(db, stamped, embedding, embed_dim)
        return
    with SQLiteHelper("session", db_config=db_config).open(write_mode=True) as own:
        with own.begin_immediate():
            _insert_entry(own, stamped, embedding, embed_dim)
    logger.debug("MemoryStore.add memory_id=%r", entry.memory_id)


def upsert(
    entry: MemoryEntry,
    embedding: list[float] | None = None,
    embed_dim: int | None = None,
    *,
    db_config: DbConfig,
    db: SQLiteHelper | None = None,
) -> None:
    """Insert or replace a MemoryEntry; updates updated_at.

    When embedding is provided, also upserts memories_vec.
    Uses BEGIN IMMEDIATE for atomicity across memories + memories_fts + memories_vec.
    `db` is the connection a caller that owns the transaction supplies; without it this
    function opens its own.
    """
    from dataclasses import replace as _replace

    now = now_iso()
    stamped = _replace(
        entry,
        updated_at=now,
        created_at=entry.created_at or now,
    )
    if db is not None:
        _upsert_entry(db, stamped, embedding, embed_dim)
        return
    with SQLiteHelper("session", db_config=db_config).open(write_mode=True) as own:
        with own.begin_immediate():
            _upsert_entry(own, stamped, embedding, embed_dim)
    logger.debug("MemoryStore.upsert memory_id=%r", entry.memory_id)


def _insert_entry(
    db: SQLiteHelper,
    entry: MemoryEntry,
    embedding: list[float] | None,
    embed_dim: int | None,
) -> None:
    """Run one entry's statements on the caller's connection inside its transaction."""
    db.execute(_INSERT_SQL, _build_row_params(entry))
    _write_fts(db, entry)
    if embedding is not None:
        _write_vec(db, entry.memory_id, embedding, embed_dim)


def _upsert_entry(
    db: SQLiteHelper,
    entry: MemoryEntry,
    embedding: list[float] | None,
    embed_dim: int | None,
) -> None:
    """Run one entry's upsert statements, syncing the FTS row, on the caller's connection."""
    db.execute(_UPSERT_SQL, _build_row_params(entry))
    # Sync FTS5: delete old row (if any) then re-insert
    db.execute("DELETE FROM memories_fts WHERE memory_id = ?", (entry.memory_id,))
    _write_fts(db, entry)
    if embedding is not None:
        _write_vec(db, entry.memory_id, embedding, embed_dim)


def _delete_run(db: SQLiteHelper, memory_id: str) -> MemoryMaintenanceResult:
    """Remove one entry inside one transaction on the caller's connection.

    The row removal and its FTS/vec/link rows are one transaction, so an interruption
    leaves either the row present or the row and its dependent rows gone, never a partial
    delete. The change event is appended only after the commit, so the event set matches
    the row set (REQ-008).
    """
    try:
        with db.begin_immediate():
            cur = db.execute("DELETE FROM memories WHERE memory_id = ?", (memory_id,))
            count = cur.rowcount
            if count:
                # SQLite foreign keys are off, so cascade cannot be relied on.
                db.execute("DELETE FROM memories_fts WHERE memory_id = ?", (memory_id,))
                db.execute("DELETE FROM memories_vec WHERE memory_id = ?", (memory_id,))
                db.execute("DELETE FROM memory_links WHERE src_id = ?", (memory_id,))
                db.execute("DELETE FROM memory_links WHERE dst_id = ?", (memory_id,))
    except sqlite3.Error:
        # The transaction rolled back: the row is still there and no event was emitted.
        return MemoryMaintenanceResult(operation="delete", interrupted=True)

    verified = count > 0 and _postcondition(db, memory_id)
    result = MemoryMaintenanceResult(
        operation="delete",
        count=count,
        verified=verified,
        ids=(memory_id,) if count else (),
    )
    if verified:
        _emit_delete_event(memory_id)
    return result


def _postcondition(db: SQLiteHelper, memory_id: str) -> bool:
    """Measure the committed state for the row the run reported as deleted."""
    rows = db.fetchall(
        "SELECT COUNT(*) FROM memories WHERE memory_id = ?", (memory_id,)
    )
    return bool(rows) and int(rows[0][0]) == 0


def delete(
    memory_id: str,
    *,
    db_config: DbConfig,
    db: SQLiteHelper | None = None,
    stop: threading.Event | None = None,
) -> MemoryMaintenanceResult:
    """Delete one entry by memory_id and return the measured outcome.

    Also removes any ``memory_links`` rows referencing ``memory_id`` in either column
    within the same transaction, and appends a ``delete`` change event to the JSONL archive
    after the commit (SQLite-first; a failed append propagates so the caller can surface
    M-07 while the SQLite change stands). An interrupted run rolls back, so it reports
    ``interrupted=True`` with no count and emits nothing.
    """
    if db is not None:
        # The store owns the connection and the cancellation handler for the run.
        return _delete_run(db, memory_id)

    with SQLiteHelper("session", db_config=db_config).open(write_mode=True) as own:
        own.interrupt_when(stop)
        return _delete_run(own, memory_id)


def _emit_delete_event(memory_id: str) -> None:
    """Append a 'delete' change event after the SQLite write (SQLite-first).

    The SQLite change stands even if the archive append fails; the error
    propagates so the caller can surface M-07.
    """
    from agent.memory.jsonl_store import _emit_change_event

    _emit_change_event("delete", memory_id)
