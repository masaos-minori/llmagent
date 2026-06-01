#!/usr/bin/env python3
"""agent/memory/store.py
CRUD layer for the memories / memories_fts / memories_vec SQLite tables.

Responsibilities:
  - add()              : Insert a MemoryEntry and sync memories_fts; optionally sync memories_vec
  - upsert()           : Insert-or-replace and sync memories_fts; optionally sync memories_vec
  - delete()           : Remove a single entry by memory_id
  - clear_by_session() : Bulk-delete entries for one session
  - search_by_type()   : Filter memories by memory_type (semantic|episodic)
  - count_by_type()    : Return entry counts per memory_type
  - count_vec()        : Return total row count in memories_vec
"""

from __future__ import annotations

import logging
import struct
from datetime import UTC, datetime
from typing import Any

import orjson

from agent.memory.types import MemoryEntry
from db.helper import SQLiteHelper

logger = logging.getLogger(__name__)


def _now_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _floats_to_blob(values: list[float]) -> bytes:
    """Pack float list to little-endian IEEE-754 BLOB for vec0 MATCH queries."""
    return struct.pack(f"{len(values)}f", *values)


def _row_to_entry(row: Any) -> MemoryEntry:
    """Convert a sqlite3.Row (or dict) to MemoryEntry."""
    d = dict(row)
    tags_raw = d.get("tags", "[]")
    try:
        tags: list[str] = (
            orjson.loads(tags_raw) if isinstance(tags_raw, str) else tags_raw
        )
    except Exception:
        tags = []
    return MemoryEntry(
        memory_id=d["memory_id"],
        memory_type=d["memory_type"],
        source_type=d.get("source_type", "conversation"),
        session_id=d.get("session_id"),
        turn_id=d.get("turn_id"),
        project=d.get("project", ""),
        repo=d.get("repo", ""),
        branch=d.get("branch", ""),
        content=d["content"],
        summary=d.get("summary", ""),
        tags=tags,
        importance=float(d.get("importance", 0.5)),
        pinned=bool(d.get("pinned", 0)),
        created_at=d.get("created_at", ""),
        updated_at=d.get("updated_at", ""),
    )


class MemoryStore:
    """CRUD operations for memories, memories_fts, and memories_vec tables."""

    def add(self, entry: MemoryEntry, embedding: list[float] | None = None) -> None:
        """Insert a new MemoryEntry; sets created_at/updated_at if empty.

        When embedding is provided, also writes to memories_vec for KNN search.
        """
        now = _now_iso()
        if not entry.created_at:
            entry.created_at = now
        if not entry.updated_at:
            entry.updated_at = now
        tags_json: bytes = orjson.dumps(entry.tags)
        with SQLiteHelper("session").open(write_mode=True) as db:
            db.execute(
                """INSERT INTO memories
                   (memory_id, memory_type, source_type, session_id, turn_id,
                    project, repo, branch, content, summary, tags,
                    importance, pinned, created_at, updated_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
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
                    tags_json.decode(),
                    entry.importance,
                    int(entry.pinned),
                    entry.created_at,
                    entry.updated_at,
                ),
            )
            db.execute(
                "INSERT INTO memories_fts(memory_id, content, summary, tags)"
                " VALUES (?,?,?,?)",
                (
                    entry.memory_id,
                    entry.content,
                    entry.summary,
                    " ".join(entry.tags),
                ),
            )
            if embedding is not None:
                try:
                    db.execute(
                        "INSERT OR REPLACE INTO memories_vec(memory_id, embedding)"
                        " VALUES (?,?)",
                        (entry.memory_id, _floats_to_blob(embedding)),
                    )
                except Exception as e:
                    logger.warning(f"memories_vec INSERT skipped: {e}")
            db.commit()
        logger.debug(f"MemoryStore.add memory_id={entry.memory_id!r}")

    def upsert(self, entry: MemoryEntry, embedding: list[float] | None = None) -> None:
        """Insert or replace a MemoryEntry; updates updated_at.

        When embedding is provided, also upserts memories_vec.
        """
        entry.updated_at = _now_iso()
        if not entry.created_at:
            entry.created_at = entry.updated_at
        tags_json: bytes = orjson.dumps(entry.tags)
        with SQLiteHelper("session").open(write_mode=True) as db:
            db.execute(
                """INSERT OR REPLACE INTO memories
                   (memory_id, memory_type, source_type, session_id, turn_id,
                    project, repo, branch, content, summary, tags,
                    importance, pinned, created_at, updated_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
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
                    tags_json.decode(),
                    entry.importance,
                    int(entry.pinned),
                    entry.created_at,
                    entry.updated_at,
                ),
            )
            # Sync FTS5: delete old row (if any) then re-insert
            db.execute(
                "DELETE FROM memories_fts WHERE memory_id = ?",
                (entry.memory_id,),
            )
            db.execute(
                "INSERT INTO memories_fts(memory_id, content, summary, tags)"
                " VALUES (?,?,?,?)",
                (
                    entry.memory_id,
                    entry.content,
                    entry.summary,
                    " ".join(entry.tags),
                ),
            )
            if embedding is not None:
                try:
                    db.execute(
                        "INSERT OR REPLACE INTO memories_vec(memory_id, embedding)"
                        " VALUES (?,?)",
                        (entry.memory_id, _floats_to_blob(embedding)),
                    )
                except Exception as e:
                    logger.warning(f"memories_vec upsert skipped: {e}")
            db.commit()
        logger.debug(f"MemoryStore.upsert memory_id={entry.memory_id!r}")

    def delete(self, memory_id: str) -> bool:
        """Delete one entry by memory_id; return True when found and deleted."""
        with SQLiteHelper("session").open(write_mode=True) as db:
            cur = db.execute("DELETE FROM memories WHERE memory_id = ?", (memory_id,))
            deleted = cur.rowcount > 0
            if deleted:
                db.execute("DELETE FROM memories_fts WHERE memory_id = ?", (memory_id,))
                try:
                    db.execute(
                        "DELETE FROM memories_vec WHERE memory_id = ?",
                        (memory_id,),
                    )
                except Exception as e:
                    logger.warning(f"memories_vec DELETE skipped: {e}")
            db.commit()
        return deleted

    def clear_by_session(self, session_id: int) -> int:
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
                try:
                    db.execute("DELETE FROM memories_vec WHERE memory_id = ?", (mid,))
                except Exception as e:
                    logger.warning(f"memories_vec DELETE skipped for {mid!r}: {e}")
            count: int = cur.rowcount
            db.commit()
        return count

    def search_by_type(
        self,
        memory_type: str,
        limit: int = 10,
        min_importance: float = 0.0,
    ) -> list[MemoryEntry]:
        """Return recent entries of memory_type ordered by importance DESC, created_at DESC."""
        with SQLiteHelper("session").open(row_factory=True) as db:
            rows = db.fetchall(
                """SELECT memory_id, memory_type, source_type, session_id, turn_id,
                          project, repo, branch, content, summary, tags,
                          importance, pinned, created_at, updated_at
                   FROM memories
                   WHERE memory_type = ? AND importance >= ?
                   ORDER BY pinned DESC, importance DESC, created_at DESC
                   LIMIT ?""",
                (memory_type, min_importance, limit),
            )
            return [_row_to_entry(r) for r in rows]

    def count_by_type(self) -> dict[str, int]:
        """Return {memory_type: count} for all rows in memories."""
        with SQLiteHelper("session").open() as db:
            rows = db.fetchall(
                "SELECT memory_type, COUNT(*) FROM memories GROUP BY memory_type",
            )
            return {row[0]: row[1] for row in rows}

    def count_vec(self) -> int:
        """Return total entry count in memories_vec; 0 if table unavailable."""
        try:
            with SQLiteHelper("session").open() as db:
                rows = db.fetchall("SELECT COUNT(*) FROM memories_vec")
                return int(rows[0][0]) if rows else 0
        except Exception as e:
            logger.warning(f"MemoryStore.count_vec failed: {e}")
            return 0

    def pin(self, memory_id: str) -> bool:
        """Set pinned=1 for memory_id; return True when found."""
        with SQLiteHelper("session").open(write_mode=True) as db:
            cur = db.execute(
                "UPDATE memories SET pinned=1, updated_at=? WHERE memory_id=?",
                (_now_iso(), memory_id),
            )
            db.commit()
        return cur.rowcount > 0

    def unpin(self, memory_id: str) -> bool:
        """Set pinned=0 for memory_id; return True when found."""
        with SQLiteHelper("session").open(write_mode=True) as db:
            cur = db.execute(
                "UPDATE memories SET pinned=0, updated_at=? WHERE memory_id=?",
                (_now_iso(), memory_id),
            )
            db.commit()
        return cur.rowcount > 0

    def get_by_id(self, memory_id: str) -> MemoryEntry | None:
        """Return one MemoryEntry by memory_id, or None if not found."""
        with SQLiteHelper("session").open(row_factory=True) as db:
            rows = db.fetchall(
                """SELECT memory_id, memory_type, source_type, session_id, turn_id,
                          project, repo, branch, content, summary, tags,
                          importance, pinned, created_at, updated_at
                   FROM memories WHERE memory_id=?""",
                (memory_id,),
            )
        return _row_to_entry(rows[0]) if rows else None
