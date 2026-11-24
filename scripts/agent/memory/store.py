#!/usr/bin/env python3
"""scripts/agent/memory/store.py

Read-only CRUD layer for the memories / memories_fts / memories_vec SQLite tables, and the
single owner of the Memory maintenance write path: every maintenance write a command mixin
performs goes through a `MemoryStore` accessor, which opens the session connection and the
transaction the ops modules run inside (REQ-005).

Write operations (add, upsert, delete) are in write_ops module.

Responsibilities:
  - search_by_type()   : Filter memories by memory_type (semantic|episodic)
  - count_vec()        : Return total row count in memories_vec
  - check_consistency(): Return counts for memories / memories_fts / memories_vec
  - pinned_count()     : Return the pinned count on the store's connection
  - delete/pin/unpin   : Row writes through write_ops and pin_ops on the store's connection
  - prune              : Single-transaction select-and-delete, reporting the rows deleted
  - reindex/rebuild    : Index rebuilds with a cancellation boundary and a verified count
  - import_jsonl       : Archive replay inside the store's transaction
"""

from __future__ import annotations

import logging
import threading
from collections.abc import Generator
from contextlib import contextmanager

from db.config import DbConfig
from db.helper import SQLiteHelper
from db.maintenance import MaintenanceResult, prune_old_memories
from db.store_impl import SQLiteMemoryDeleteStore

from agent.memory import count_ops, import_ops, pin_ops, rebuild_ops, write_ops
from agent.memory.mapper import row_to_entry
from agent.memory.models import (
    ConsistencyReport,
    MemoryImportResult,
    MemoryMaintenanceResult,
)
from agent.memory.sql_constants import _count_fts
from agent.memory.types import MemoryEntry

logger = logging.getLogger(__name__)

_MEMORY_COLUMNS = """memory_id, memory_type, source_type, session_id, turn_id,
                      project, repo, branch, content, summary, tags,
                      importance, pinned, created_at, updated_at"""


class MemoryStore:
    """CRUD operations for memories, memories_fts, and memories_vec tables.

    Write operations (add, upsert, delete) are delegated to
    the write_ops module.
    """

    def __init__(self, embed_dim: int | None = None, *, db_config: DbConfig) -> None:
        """Initialize the store with the typed DB configuration and an optional embedding dimension.

        `db_config` is the typed configuration supplied by the process that owns the
        configuration file; the store resolves no path itself. When `embed_dim` is set,
        embeddings passed to add()/upsert() are validated against it.
        """
        self._db_config = db_config
        # When set, embeddings passed to add()/upsert() are validated against this dimension.
        self._embed_dim = embed_dim

    @property
    def embed_dim(self) -> int | None:
        """The embedding dimension configured at construction, or None when unset."""
        return self._embed_dim

    # ── Read-only API ────────────────────────────────────────────────────────

    def search_by_type(
        self,
        memory_type: str,
        limit: int = 10,
        min_importance: float = 0.0,
    ) -> list[MemoryEntry]:
        """Return recent entries of memory_type ordered by importance DESC, created_at DESC."""
        with SQLiteHelper("session", db_config=self._db_config).open(
            row_factory=True
        ) as db:
            rows = db.fetchall(
                f"""SELECT {_MEMORY_COLUMNS}
                   FROM memories
                   WHERE memory_type = ? AND importance >= ?
                   ORDER BY pinned DESC, importance DESC, created_at DESC
                   LIMIT ?""",  # nosec B608 — _MEMORY_COLUMNS is a static module constant, no user input; params via ?
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
        sql = f"""SELECT {_MEMORY_COLUMNS}
                  FROM memories
                  {where}
                  ORDER BY pinned DESC, importance DESC, created_at DESC
                  LIMIT ?"""  # nosec B608 — where clause uses only literal strings; params via ?
        with SQLiteHelper("session", db_config=self._db_config).open(
            row_factory=True
        ) as db:
            rows = db.fetchall(sql, tuple(params))
        return [row_to_entry(dict(r)) for r in rows]

    def count_vec(self) -> int:
        """Return total entry count in memories_vec. Raises sqlite3.OperationalError if unavailable."""
        with SQLiteHelper("session", db_config=self._db_config).open() as db:
            rows = db.fetchall("SELECT COUNT(*) FROM memories_vec")
            return int(rows[0][0]) if rows else 0

    def check_consistency(self) -> ConsistencyReport:
        """Return row counts for memories / memories_fts / memories_vec.

        Raises MemoryConsistencyError if FTS count cannot be determined.
        """
        with SQLiteHelper("session", db_config=self._db_config).open() as db:
            rows = db.fetchall("SELECT COUNT(*) FROM memories")
            memories = int(rows[0][0]) if rows else 0
            fts = _count_fts(db)
        vec = self.count_vec()
        return ConsistencyReport(memories=memories, fts=fts, vec=vec)

    def get_by_id(self, memory_id: str) -> MemoryEntry | None:
        """Return one MemoryEntry by memory_id, or None if not found."""
        with SQLiteHelper("session", db_config=self._db_config).open(
            row_factory=True
        ) as db:
            rows = db.fetchall(
                f"""SELECT {_MEMORY_COLUMNS}
                   FROM memories WHERE memory_id=?""",  # nosec B608 — _MEMORY_COLUMNS is a static module constant, no user input; params via ?
                (memory_id,),
            )
        return row_to_entry(rows[0]) if rows else None

    # ── Maintenance accessors ─────────────────────────────────────────────────

    @contextmanager
    def _maintenance_connection(
        self, stop: threading.Event | None
    ) -> Generator[SQLiteHelper]:
        """Open the session connection the Memory maintenance run uses (REQ-005).

        `MemoryStore` is the only place the Memory package opens a connection for
        maintenance, which is what makes the single-writer contract for `session.sqlite`
        effective. The cancellation event is installed through the existing progress-handler
        mechanism (REQ-002), so a run that cannot be interrupted is not silently uncancelled.
        """
        helper = SQLiteHelper("session", db_config=self._db_config)
        with helper.open(write_mode=True, row_factory=True) as db:
            if stop is not None:
                db.interrupt_when(stop)
            yield db

    def pinned_count(self, *, stop: threading.Event | None = None) -> int:
        """Return the number of currently pinned memories on the store's connection."""
        with self._maintenance_connection(stop) as db:
            return count_ops.count_pinned(db)

    def delete(
        self, memory_id: str, *, stop: threading.Event | None = None
    ) -> MemoryMaintenanceResult:
        """Delete one entry through `write_ops` on the store's connection."""
        with self._maintenance_connection(stop) as db:
            return write_ops.delete(memory_id, db_config=self._db_config, db=db)

    def pin(
        self,
        memory_id: str,
        *,
        max_pinned: int,
        stop: threading.Event | None = None,
    ) -> MemoryMaintenanceResult:
        """Pin one entry through `pin_ops`, enforcing the limit inside the transaction."""
        with self._maintenance_connection(stop) as db:
            return pin_ops.pin(
                memory_id, db_config=self._db_config, db=db, max_pinned=max_pinned
            )

    def unpin(
        self, memory_id: str, *, stop: threading.Event | None = None
    ) -> MemoryMaintenanceResult:
        """Release one entry through `pin_ops` on the store's connection."""
        with self._maintenance_connection(stop) as db:
            return pin_ops.unpin(memory_id, db_config=self._db_config, db=db)

    def prune(
        self,
        days: int,
        *,
        dry_run: bool = False,
        stop: threading.Event | None = None,
    ) -> MemoryMaintenanceResult:
        """Prune entries older than `days` days, reporting the rows actually deleted.

        A real run selects and deletes in one transaction, so the reported count is the
        committed count rather than a count read on a second connection (REQ-008). A dry run
        changes nothing and is never verified.
        """
        with self._maintenance_connection(stop) as db:
            if dry_run:
                ids = tuple(SQLiteMemoryDeleteStore(db).collect_prunable_ids(days))
                return MemoryMaintenanceResult(
                    operation="prune", count=len(ids), ids=ids
                )
            result = prune_old_memories(db, days, stop=stop)
            return _maintenance_outcome("prune", result)

    def reindex(
        self, index_type: str, *, stop: threading.Event | None = None
    ) -> MemoryMaintenanceResult:
        """Rebuild one memory index through `rebuild_ops` on the store's connection."""
        with self._maintenance_connection(stop) as db:
            return rebuild_ops.reindex(index_type, db_config=self._db_config, db=db)

    def rebuild(
        self, *, stop: threading.Event | None = None
    ) -> MemoryMaintenanceResult:
        """Rebuild both memory indexes through `rebuild_ops` on the store's connection."""
        with self._maintenance_connection(stop) as db:
            fts = rebuild_ops.rebuild_fts(db, db_config=self._db_config)
            vec = rebuild_ops.rebuild_vec(db, db_config=self._db_config)
            return MemoryMaintenanceResult(
                operation="rebuild",
                count=fts.count + vec.count,
                verified=fts.verified and vec.verified,
                interrupted=fts.interrupted or vec.interrupted,
            )

    def import_jsonl(
        self,
        jsonl_store: object,
        *,
        dry_run: bool = False,
        backup: bool = False,
        allow_loss: bool = False,
        stop: threading.Event | None = None,
    ) -> MemoryImportResult:
        """Replay the JSONL archive through `import_ops` on the store's connection."""
        with self._maintenance_connection(stop) as db:
            return import_ops.import_from_jsonl(
                jsonl_store,
                dry_run=dry_run,
                embed_dim=self._embed_dim,
                backup=backup,
                allow_loss=allow_loss,
                db_config=self._db_config,
                db=db,
            )


def _maintenance_outcome(
    operation: str, result: MaintenanceResult
) -> MemoryMaintenanceResult:
    """Turn one `db.maintenance` result into the Memory outcome the caller reports.

    A run stopped by the cancellation event is reported as interrupted with no count, so a
    rolled-back run cannot read as a partial success (REQ-004).
    """
    data = result.data or {}
    ids = tuple(data.get("pruned_ids", ()))
    interrupted = result.interrupted
    return MemoryMaintenanceResult(
        operation=operation,
        count=0 if interrupted else int(data.get("deleted", 0)),
        verified=result.success and not interrupted,
        interrupted=interrupted,
        ids=() if interrupted else ids,
    )
