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
  - check_consistency(): Return counts for memories / memories_fts / memories_vec
"""

from __future__ import annotations

import logging
import struct
from datetime import UTC, datetime
from typing import Any

import orjson

from agent.memory.mapper import row_to_entry
from agent.memory.types import MemoryEntry
from db.helper import SQLiteHelper

logger = logging.getLogger(__name__)


def _now_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _floats_to_blob(values: list[float], expected_dim: int | None = None) -> bytes:
    """Pack float list to little-endian IEEE-754 BLOB for vec0 MATCH queries.

    When expected_dim is set, raises ValueError if len(values) != expected_dim.
    """
    if expected_dim is not None and len(values) != expected_dim:
        raise ValueError(
            f"Embedding dimension mismatch: expected {expected_dim}, got {len(values)}",
        )
    return struct.pack(f"{len(values)}f", *values)


class MemoryStore:
    """CRUD operations for memories, memories_fts, and memories_vec tables."""

    def __init__(self, embed_dim: int | None = None) -> None:
        # When set, embeddings passed to add()/upsert() are validated against this dimension.
        self._embed_dim = embed_dim

    # ── Private helpers ───────────────────────────────────────────────────────

    def _build_row_params(self, entry: MemoryEntry) -> tuple[Any, ...]:
        """Return the param tuple for a memories INSERT statement."""
        tags_json: bytes = orjson.dumps(entry.tags)
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
            tags_json.decode(),
            entry.importance,
            int(entry.pinned),
            entry.created_at,
            entry.updated_at,
        )

    _INSERT_SQL = (
        "INSERT INTO memories"
        " (memory_id, memory_type, source_type, session_id, turn_id,"
        "  project, repo, branch, content, summary, tags,"
        "  importance, pinned, created_at, updated_at)"
        " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
    )
    _UPSERT_SQL = _INSERT_SQL.replace("INSERT INTO", "INSERT OR REPLACE INTO", 1)

    def _write_fts(self, db: SQLiteHelper, entry: MemoryEntry) -> None:
        """Sync one row into memories_fts; caller must be inside a transaction."""
        db.execute(
            "INSERT INTO memories_fts(memory_id, content, summary, tags)"
            " VALUES (?,?,?,?)",
            (entry.memory_id, entry.content, entry.summary, " ".join(entry.tags)),
        )

    def _write_vec(
        self, db: SQLiteHelper, memory_id: str, embedding: list[float]
    ) -> None:
        """Upsert one embedding into memories_vec; logs warning on failure."""
        try:
            db.execute(
                "INSERT OR REPLACE INTO memories_vec(memory_id, embedding)"
                " VALUES (?,?)",
                (memory_id, _floats_to_blob(embedding, self._embed_dim)),
            )
        except Exception as e:
            logger.warning(f"memories_vec write skipped: {e}")

    # ── Public API ────────────────────────────────────────────────────────────

    def add(self, entry: MemoryEntry, embedding: list[float] | None = None) -> None:
        """Insert a new MemoryEntry; sets created_at/updated_at if empty.

        When embedding is provided, also writes to memories_vec for KNN search.
        Uses BEGIN IMMEDIATE for atomicity across memories + memories_fts + memories_vec.
        """
        now = _now_iso()
        if not entry.created_at:
            entry.created_at = now
        if not entry.updated_at:
            entry.updated_at = now
        with SQLiteHelper("session").open(write_mode=True) as db:
            with db.begin_immediate():
                db.execute(self._INSERT_SQL, self._build_row_params(entry))
                self._write_fts(db, entry)
                if embedding is not None:
                    self._write_vec(db, entry.memory_id, embedding)
        logger.debug(f"MemoryStore.add memory_id={entry.memory_id!r}")

    def upsert(self, entry: MemoryEntry, embedding: list[float] | None = None) -> None:
        """Insert or replace a MemoryEntry; updates updated_at.

        When embedding is provided, also upserts memories_vec.
        Uses BEGIN IMMEDIATE for atomicity across memories + memories_fts + memories_vec.
        """
        entry.updated_at = _now_iso()
        if not entry.created_at:
            entry.created_at = entry.updated_at
        with SQLiteHelper("session").open(write_mode=True) as db:
            with db.begin_immediate():
                db.execute(self._UPSERT_SQL, self._build_row_params(entry))
                # Sync FTS5: delete old row (if any) then re-insert
                db.execute(
                    "DELETE FROM memories_fts WHERE memory_id = ?",
                    (entry.memory_id,),
                )
                self._write_fts(db, entry)
                if embedding is not None:
                    self._write_vec(db, entry.memory_id, embedding)
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
            return [row_to_entry(r) for r in rows]

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

    def check_consistency(self) -> dict[str, int]:
        """Return row counts for memories / memories_fts / memories_vec.

        Use to detect index drift after unexpected failures.
        """
        result: dict[str, int] = {}
        with SQLiteHelper("session").open() as db:
            rows = db.fetchall("SELECT COUNT(*) FROM memories")
            result["memories"] = int(rows[0][0]) if rows else 0
            try:
                fts_rows = db.fetchall(
                    "SELECT COUNT(*) FROM memories_fts WHERE memories_fts MATCH '*'"
                )
                result["memories_fts"] = int(fts_rows[0][0]) if fts_rows else 0
            except Exception:
                # Fallback: direct count without FTS predicate
                try:
                    fts_rows = db.fetchall("SELECT COUNT(*) FROM memories_fts")
                    result["memories_fts"] = int(fts_rows[0][0]) if fts_rows else 0
                except Exception:
                    result["memories_fts"] = -1
        result["memories_vec"] = self.count_vec()
        return result

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
        return row_to_entry(rows[0]) if rows else None
