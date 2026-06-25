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
import sqlite3
from dataclasses import replace

import orjson
from db.helper import SQLiteHelper

from agent.memory.exceptions import MemoryConsistencyError
from agent.memory.mapper import _floats_to_blob, _now_iso, _stamp_entry, row_to_entry
from agent.memory.models import ConsistencyReport
from agent.memory.types import MemoryEntry

logger = logging.getLogger(__name__)


def _count_fts(db: SQLiteHelper) -> int:
    """Return row count in memories_fts; try MATCH predicate, fall back to plain COUNT.

    Raises MemoryConsistencyError when neither query succeeds.
    """
    try:
        rows = db.fetchall(
            "SELECT COUNT(*) FROM memories_fts WHERE memories_fts MATCH '*'"
        )
        return int(rows[0][0]) if rows else 0
    except sqlite3.OperationalError:
        pass
    try:
        rows = db.fetchall("SELECT COUNT(*) FROM memories_fts")
        return int(rows[0][0]) if rows else 0
    except sqlite3.OperationalError as e:
        raise MemoryConsistencyError(f"Cannot count memories_fts: {e}") from e


class MemoryStore:
    """CRUD operations for memories, memories_fts, and memories_vec tables."""

    def __init__(self, embed_dim: int | None = None) -> None:
        # When set, embeddings passed to add()/upsert() are validated against this dimension.
        self._embed_dim = embed_dim

    # ── Private helpers ───────────────────────────────────────────────────────

    def _build_row_params(self, entry: MemoryEntry) -> tuple[object, ...]:
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
    _UPSERT_SQL = (
        "INSERT INTO memories"
        " (memory_id, memory_type, source_type, session_id, turn_id,"
        "  project, repo, branch, content, summary, tags,"
        "  importance, pinned, created_at, updated_at)"
        " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
        " ON CONFLICT(memory_id) DO UPDATE SET"
        "   memory_type=excluded.memory_type,"
        "   source_type=excluded.source_type,"
        "   content=excluded.content,"
        "   summary=excluded.summary,"
        "   tags=excluded.tags,"
        "   importance=excluded.importance,"
        "   pinned=excluded.pinned,"
        "   updated_at=excluded.updated_at"
    )

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
        """Upsert one embedding into memories_vec; raises on failure."""
        db.execute(
            "INSERT OR REPLACE INTO memories_vec(memory_id, embedding) VALUES (?,?)",
            (memory_id, _floats_to_blob(embedding, self._embed_dim)),
        )

    # ── Public API ────────────────────────────────────────────────────────────

    def add(self, entry: MemoryEntry, embedding: list[float] | None = None) -> None:
        """Insert a new MemoryEntry; sets created_at/updated_at if empty.

        When embedding is provided, also writes to memories_vec for KNN search.
        Uses BEGIN IMMEDIATE for atomicity across memories + memories_fts + memories_vec.
        """
        now = _now_iso()
        stamped = _stamp_entry(entry, now)
        with SQLiteHelper("session").open(write_mode=True) as db:
            with db.begin_immediate():
                db.execute(self._INSERT_SQL, self._build_row_params(stamped))
                self._write_fts(db, stamped)
                if embedding is not None:
                    self._write_vec(db, stamped.memory_id, embedding)
        logger.debug("MemoryStore.add memory_id=%r", entry.memory_id)

    def upsert(self, entry: MemoryEntry, embedding: list[float] | None = None) -> None:
        """Insert or replace a MemoryEntry; updates updated_at.

        When embedding is provided, also upserts memories_vec.
        Uses BEGIN IMMEDIATE for atomicity across memories + memories_fts + memories_vec.
        """
        now = _now_iso()
        stamped = replace(
            entry,
            updated_at=now,
            created_at=entry.created_at or now,
        )
        with SQLiteHelper("session").open(write_mode=True) as db:
            with db.begin_immediate():
                db.execute(self._UPSERT_SQL, self._build_row_params(stamped))
                # Sync FTS5: delete old row (if any) then re-insert
                db.execute(
                    "DELETE FROM memories_fts WHERE memory_id = ?",
                    (stamped.memory_id,),
                )
                self._write_fts(db, stamped)
                if embedding is not None:
                    self._write_vec(db, stamped.memory_id, embedding)
        logger.debug("MemoryStore.upsert memory_id=%r", entry.memory_id)

    def delete(self, memory_id: str) -> bool:
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
                db.execute("DELETE FROM memories_vec WHERE memory_id = ?", (mid,))
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
        """Return {memory_type: count} for all rows in memories. Diagnostic use only."""
        with SQLiteHelper("session").open() as db:
            rows = db.fetchall(
                "SELECT memory_type, COUNT(*) FROM memories GROUP BY memory_type",
            )
            return {row[0]: row[1] for row in rows}

    def count_vec(self) -> int:
        """Return total entry count in memories_vec. Raises sqlite3.OperationalError if unavailable."""
        with SQLiteHelper("session").open() as db:
            rows = db.fetchall("SELECT COUNT(*) FROM memories_vec")
            return int(rows[0][0]) if rows else 0

    def check_consistency(self) -> ConsistencyReport:
        """Return row counts for memories / memories_fts / memories_vec.

        Raises MemoryConsistencyError if FTS count cannot be determined.
        """
        with SQLiteHelper("session").open() as db:
            rows = db.fetchall("SELECT COUNT(*) FROM memories")
            memories = int(rows[0][0]) if rows else 0
            fts = _count_fts(db)
        vec = self.count_vec()
        return ConsistencyReport(memories=memories, fts=fts, vec=vec)

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

    def count_entries(self) -> int:
        """Return total entry count across all types. Raises sqlite3.OperationalError on DB error."""
        with SQLiteHelper("session").open() as db:
            rows = db.fetchall("SELECT COUNT(*) FROM memories")
        return int(rows[0][0]) if rows else 0

    def count_prunable(self, days: int) -> int:
        """Return count of entries older than `days` days. Raises sqlite3.OperationalError on DB error."""
        with SQLiteHelper("session").open() as db:
            row = db.fetchall(
                "SELECT COUNT(*) FROM memories WHERE created_at < datetime('now', ?)",
                (f"-{days} days",),
            )
            return int(row[0][0]) if row else 0

    def import_from_jsonl(
        self,
        jsonl_store: object,
        *,
        dry_run: bool = False,
    ) -> tuple[int, int]:
        """Import entries from a JSONL archive into SQLite memories/FTS/vec tables.

        WARNING: This does NOT replay deletions, pin state, or dedup history.
        Entries deleted from SQLite will be re-inserted. This is intended for
        initial import from an external archive only — NOT for disaster recovery
        or routine consistency repair.

        For consistency repair (memories vs FTS vs vec out of sync), use
        repair_index() instead.

        Returns (jsonl_count, inserted_count).
        When dry_run=True, returns (jsonl_count, 0) without modifying SQLite.
        """
        from agent.memory.jsonl_store import JsonlMemoryStore

        assert isinstance(jsonl_store, JsonlMemoryStore)
        entries = jsonl_store.read_all()
        jsonl_count = len(entries)
        if dry_run:
            return jsonl_count, 0
        with SQLiteHelper("session").open(write_mode=True) as db:
            with db.begin_immediate():
                db.execute("DELETE FROM memories_vec")
                db.execute("DELETE FROM memories_fts")
                db.execute("DELETE FROM memories")
                for entry in entries:
                    db.execute(self._INSERT_SQL, self._build_row_params(entry))
                    self._write_fts(db, entry)
        logger.info("import_from_jsonl: inserted %d entries from JSONL", jsonl_count)
        return jsonl_count, jsonl_count
