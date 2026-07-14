#!/usr/bin/env python3
"""agent/memory/store.py

Read-only CRUD layer for the memories / memories_fts / memories_vec SQLite tables.

Write operations (add, upsert, delete, clear_by_session) are in write_ops module.

Responsibilities:
  - search_by_type()   : Filter memories by memory_type (semantic|episodic)
  - count_vec()        : Return total row count in memories_vec
  - check_consistency(): Return counts for memories / memories_fts / memories_vec
"""

from __future__ import annotations

import logging

from agent.memory.mapper import row_to_entry
from agent.memory.models import ConsistencyReport
from agent.memory.sql_constants import _count_fts
from agent.memory.types import MemoryEntry
from db.helper import SQLiteHelper

logger = logging.getLogger(__name__)


class MemoryStore:
    """CRUD operations for memories, memories_fts, and memories_vec tables.

    Write operations (add, upsert, delete, clear_by_session) are delegated to
    the write_ops module.
    """

    def __init__(self, embed_dim: int | None = None) -> None:
        # When set, embeddings passed to add()/upsert() are validated against this dimension.
        self._embed_dim = embed_dim

    # ── Read-only API ────────────────────────────────────────────────────────

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

    def list_entries(
        self,
        source_type: str | None = None,
        branch: str | None = None,
        limit: int = 50,
    ) -> list[MemoryEntry]:
        """Return entries filtered by optional source_type and/or branch."""
        where_clauses = []
        params: list[object] = []
        if source_type:
            where_clauses.append("source_type = ?")
            params.append(source_type)
        if branch is not None:
            where_clauses.append("(branch = '' OR branch = ?)")
            params.append(branch)
        where = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
        params.append(limit)
        sql = f"""SELECT memory_id, memory_type, source_type, session_id, turn_id,
                         project, repo, branch, content, summary, tags,
                         importance, pinned, created_at, updated_at
                  FROM memories
                  {where}
                  ORDER BY pinned DESC, importance DESC, created_at DESC
                  LIMIT ?"""  # nosec B608 — where clause uses only literal strings; params via ?
        with SQLiteHelper("session").open(row_factory=True) as db:
            rows = db.fetchall(sql, tuple(params))
        return [row_to_entry(dict(r)) for r in rows]

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
