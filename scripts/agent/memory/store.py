#!/usr/bin/env python3
"""
memory_store.py
CRUD layer for the Long-term / Task memory tables (memory_entries, memory_vec).

Responsibilities:
  - add()            : Insert a memory entry atomically (text + optional embedding)
  - search_semantic(): KNN search via memory_vec (vec0 required; degrades to empty list)
  - search_by_type() : Filter memory_entries by mem_type
  - delete()         : Remove a single entry by entry_id
  - clear()          : Bulk-delete entries (optionally scoped to a session)

All write operations use a single SQLiteHelper("session").open(write_mode=True) context to
guarantee atomicity between memory_entries and memory_vec inserts (same pattern as
rag_ingester._insert_chunk()).

The vec0 extension may not be available in dev environments; any vec0-dependent
operation is wrapped in try/except and falls back to a warning log + empty result.
"""

import logging
import struct
from typing import Any

from db.helper import SQLiteHelper

logger = logging.getLogger(__name__)


def _floats_to_blob(values: list[float]) -> bytes:
    """Pack a list of float32 values into a little-endian binary blob.

    Used instead of rag_utils.floats_to_blob to avoid a cross-module dependency
    from memory_store (RAG layer) back into rag_utils (pipeline layer).
    """
    return struct.pack(f"<{len(values)}f", *values)


class MemoryStore:
    """CRUD operations for memory_entries and memory_vec.

    All public methods open their own SQLiteHelper connection and close it on
    completion.  Callers do not need to manage connections.
    """

    def add(
        self,
        session_id: int | None,
        mem_type: str,
        content: str,
        embedding: list[float] | None = None,
    ) -> int:
        """Insert a memory entry; return the new entry_id.

        Both memory_entries and memory_vec (when embedding is provided) are
        inserted within a single write transaction to prevent orphaned rows.
        The vec0 INSERT is guarded by try/except so add() succeeds even when
        vec0 is unavailable (Semantic search will simply return empty results).

        Args:
            session_id: Session to associate the entry with, or None for global.
            mem_type: 'long_term' or 'task' (enforced by DB CHECK constraint).
            content: Text content of the memory entry.
            embedding: 384-dim float vector for semantic search, or None to skip.

        Returns:
            The entry_id (INTEGER PRIMARY KEY) of the inserted row.
        """
        with SQLiteHelper("session").open(write_mode=True) as db:
            cur = db.execute(
                "INSERT INTO memory_entries (session_id, mem_type, content)"
                " VALUES (?, ?, ?)",
                (session_id, mem_type, content),
            )
            entry_id: int = cur.lastrowid  # type: ignore[assignment]
            if embedding is not None:
                try:
                    db.execute(
                        "INSERT INTO memory_vec (entry_id, embedding) VALUES (?, ?)",
                        (entry_id, _floats_to_blob(embedding)),
                    )
                except Exception as e:
                    # vec0 may not be available in dev environments
                    logger.warning(
                        f"memory_vec INSERT skipped (vec0 unavailable?): {e}"
                    )
            db.commit()
        return entry_id

    def search_semantic(
        self, query_embedding: list[float], limit: int = 5
    ) -> list[dict[str, Any]]:
        """KNN search over memory_vec; returns matching memory_entries rows.

        Returns an empty list when vec0 is unavailable or no entries exist.

        Args:
            query_embedding: 384-dim query vector.
            limit: Maximum number of results to return.

        Returns:
            List of dicts with keys: entry_id, session_id, mem_type, content, created_at.
        """
        try:
            with SQLiteHelper("session").open(row_factory=True) as db:
                rows = db.fetchall(
                    """
                    SELECT e.entry_id, e.session_id, e.mem_type, e.content, e.created_at
                    FROM memory_vec v
                    JOIN memory_entries e ON e.entry_id = v.entry_id
                    WHERE v.embedding MATCH ?
                      AND k = ?
                    ORDER BY v.distance
                    """,
                    (_floats_to_blob(query_embedding), limit),
                )
                return [dict(r) for r in rows]
        except Exception as e:
            logger.warning(f"search_semantic failed (vec0 unavailable?): {e}")
            return []

    def search_by_type(self, mem_type: str, limit: int = 10) -> list[dict[str, Any]]:
        """Return the most-recent memory entries of a given type.

        Args:
            mem_type: 'long_term' or 'task'.
            limit: Maximum number of rows to return (ordered by created_at DESC).

        Returns:
            List of dicts with keys: entry_id, session_id, mem_type, content, created_at.
        """
        with SQLiteHelper("session").open(row_factory=True) as db:
            rows = db.fetchall(
                "SELECT entry_id, session_id, mem_type, content, created_at"
                " FROM memory_entries"
                " WHERE mem_type = ?"
                " ORDER BY created_at DESC"
                " LIMIT ?",
                (mem_type, limit),
            )
            return [dict(r) for r in rows]

    def delete(self, entry_id: int) -> bool:
        """Delete a single memory entry by entry_id.

        The corresponding memory_vec row is also deleted because the FK cascade
        on memory_vec is not guaranteed (virtual table); a separate DELETE is issued.

        Returns:
            True when the entry existed and was deleted; False otherwise.
        """
        with SQLiteHelper("session").open(write_mode=True) as db:
            cur = db.execute(
                "DELETE FROM memory_entries WHERE entry_id = ?", (entry_id,)
            )
            deleted = cur.rowcount > 0
            if deleted:
                try:
                    db.execute("DELETE FROM memory_vec WHERE entry_id = ?", (entry_id,))
                except Exception as e:
                    # vec0 may not be available; log and continue
                    logger.warning(
                        f"memory_vec DELETE skipped (vec0 unavailable?): {e}"
                    )
            db.commit()
        return deleted

    def clear(self, session_id: int | None = None) -> int:
        """Bulk-delete memory entries.

        When session_id is provided, only entries belonging to that session are
        removed.  When None, ALL entries are deleted (full reset).

        Returns:
            Number of rows deleted from memory_entries.
        """
        with SQLiteHelper("session").open(write_mode=True) as db:
            if session_id is None:
                cur = db.execute("DELETE FROM memory_entries")
                try:
                    db.execute("DELETE FROM memory_vec")
                except Exception as e:
                    logger.warning(f"memory_vec clear skipped (vec0 unavailable?): {e}")
            else:
                # Collect entry_ids to also clean up memory_vec
                rows = db.fetchall(
                    "SELECT entry_id FROM memory_entries WHERE session_id = ?",
                    (session_id,),
                )
                cur = db.execute(
                    "DELETE FROM memory_entries WHERE session_id = ?", (session_id,)
                )
                for row in rows:
                    try:
                        db.execute(
                            "DELETE FROM memory_vec WHERE entry_id = ?", (row[0],)
                        )
                    except Exception as e:
                        logger.warning(
                            f"memory_vec DELETE skipped (vec0 unavailable?): {e}"
                        )
            count: int = cur.rowcount
            db.commit()
        return count
