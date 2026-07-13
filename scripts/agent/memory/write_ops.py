#!/usr/bin/env python3
"""agent/memory/write_ops.py — Write operations for memory CRUD."""

import logging

from agent.memory.mapper import _floats_to_blob, _stamp_entry
from agent.memory.sql_constants import _INSERT_SQL, _UPSERT_SQL
from agent.memory.types import MemoryEntry
from db.helper import SQLiteHelper
from shared.json_utils import dumps, now_iso

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
) -> None:
    """Insert a new MemoryEntry; sets created_at/updated_at if empty.

    When embedding is provided, also writes to memories_vec for KNN search.
    Uses BEGIN IMMEDIATE for atomicity across memories + memories_fts + memories_vec.
    """
    now = now_iso()
    stamped = _stamp_entry(entry, now)
    with SQLiteHelper("session").open(write_mode=True) as db:
        with db.begin_immediate():
            db.execute(_INSERT_SQL, _build_row_params(stamped))
            _write_fts(db, stamped)
            if embedding is not None:
                _write_vec(db, stamped.memory_id, embedding, embed_dim)
    logger.debug("MemoryStore.add memory_id=%r", entry.memory_id)


def upsert(
    entry: MemoryEntry,
    embedding: list[float] | None = None,
    embed_dim: int | None = None,
) -> None:
    """Insert or replace a MemoryEntry; updates updated_at.

    When embedding is provided, also upserts memories_vec.
    Uses BEGIN IMMEDIATE for atomicity across memories + memories_fts + memories_vec.
    """
    from dataclasses import replace as _replace

    now = now_iso()
    stamped = _replace(
        entry,
        updated_at=now,
        created_at=entry.created_at or now,
    )
    with SQLiteHelper("session").open(write_mode=True) as db:
        with db.begin_immediate():
            db.execute(_UPSERT_SQL, _build_row_params(stamped))
            # Sync FTS5: delete old row (if any) then re-insert
            db.execute(
                "DELETE FROM memories_fts WHERE memory_id = ?",
                (stamped.memory_id,),
            )
            _write_fts(db, stamped)
            if embedding is not None:
                _write_vec(db, stamped.memory_id, embedding, embed_dim)
    logger.debug("MemoryStore.upsert memory_id=%r", entry.memory_id)


def delete(memory_id: str) -> bool:
    """Delete one entry by memory_id; return True when found and deleted."""
    with SQLiteHelper("session").open(write_mode=True) as db:
        cur = db.execute("DELETE FROM memories WHERE memory_id = ?", (memory_id,))
        deleted = cur.rowcount > 0
        if deleted:
            db.execute("DELETE FROM memories_fts WHERE memory_id = ?", (memory_id,))
            db.execute(
                "DELETE FROM memories_vec WHERE memory_id = ?",
                (memory_id,),
            )
        db.commit()
    deleted_flag: bool = deleted
    return deleted_flag


def clear_by_session(session_id: int) -> int:
    """Delete all entries for session_id; return count deleted."""
    with SQLiteHelper("session").open(write_mode=True) as db:
        rows = db.fetchall(
            "SELECT memory_id FROM memories WHERE session_id = ?",
            (session_id,),
        )
        cur = db.execute("DELETE FROM memories WHERE session_id = ?", (session_id,))
        for row in rows:
            mid = row[0]
            db.execute("DELETE FROM memories_fts WHERE memory_id = ?", (mid,))
            db.execute("DELETE FROM memories_vec WHERE memory_id = ?", (mid,))
        count: int = cur.rowcount
        db.commit()
    return count
