#!/usr/bin/env python3
"""scripts/agent/memory/import_ops.py — Import operations for memory tables."""

from __future__ import annotations

import logging
import sqlite3
import threading
from dataclasses import replace
from typing import TYPE_CHECKING

from db.config import DbConfig
from db.helper import SQLiteHelper

from agent.memory.models import MemoryImportResult
from agent.memory.write_ops import add

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from agent.memory.types import MemoryEntry


def import_from_jsonl(
    jsonl_store: object,
    *,
    dry_run: bool = False,
    embed_dim: int | None = None,
    backup: bool = False,
    allow_loss: bool = False,
    db_config: DbConfig,
    db: SQLiteHelper | None = None,
    stop: threading.Event | None = None,
) -> MemoryImportResult:
    """Import entries from a JSONL archive into SQLite memories/FTS/vec tables.

    The archive is replayed top-to-bottom to compute the final state before any
    SQLite write: a memory line adds/overwrites its id, a ``delete`` event removes
    it (a later memory line may re-add it), a ``pin``/``unpin`` event updates
    ``pinned`` when the entry currently exists, and unparsable lines are skipped
    and counted. Only the resulting final state is written, in one transaction, so
    a delete-then-re-add pair never leaves a stale row.

    `db` is the connection the `MemoryStore` accessor opened for the run; the transaction
    boundary is the store's, so this module supplies only the statements inside it. Without
    it this function opens its own. `stop` is the job's cancellation event: an interrupted
    run rolls back and reports no inserted count.

    Returns the archive counts and the post-import count measured after the commit, so the
    reported count is the committed count rather than the number of statements attempted
    (REQ-004). When ``dry_run=True`` the tables are left untouched and nothing is verified.

    ``backup`` / ``allow_loss``: a no-loss ``backup`` cannot proceed past
    records that cannot be reconstructed from the archive alone; ``allow_loss`` opts
    out. Faithful-reconstruction (SQLite-only) detection lives in the rebuild row;
    here the guard refuses when a backup is requested without ``allow_loss`` and
    unparsable (unreconstructable) records were encountered.
    """
    from agent.memory.jsonl_store import JsonlMemoryStore as _JsonlMemoryStore
    from agent.memory.jsonl_store import _entry_from_dict

    if not isinstance(jsonl_store, _JsonlMemoryStore):
        raise TypeError(f"Expected JsonlMemoryStore, got {type(jsonl_store).__name__}")

    state: dict[str, MemoryEntry] = {}
    memory_lines = 0
    skipped = 0
    for kind, data in jsonl_store.iter_records():
        if kind == "malformed":
            skipped += 1
            continue
        if kind == "event":
            mid = data.get("memory_id")
            if data.get("event") == "delete":
                if mid in state:
                    del state[mid]
            elif data.get("event") in ("pin", "unpin"):
                if mid in state:
                    state[mid] = replace(state[mid], pinned=data["event"] == "pin")
            # pin/unpin for a missing entry: nothing to do
            continue
        # kind == "memory"
        entry = _entry_from_dict(data)  # reuse jsonl_store's deserializer
        memory_lines += 1
        state[entry.memory_id] = entry
    jsonl_count = memory_lines

    if dry_run:
        return MemoryImportResult(jsonl_count=jsonl_count, skipped=skipped)

    # a no-loss backup must not silently drop records that cannot be
    # reconstructed from the archive. The precise SQLite-only detection lives in
    # the rebuild row; refuse here when a backup is requested without allow_loss
    # and unparsable (unreconstructable) records were encountered.
    if backup and not allow_loss and skipped > 0:
        raise ValueError(
            "backup=True requires allow_loss=True: "
            f"{skipped} archive record(s) could not be reconstructed"
        )

    if db is not None:
        return _run_import(db, state, jsonl_count, skipped, embed_dim, db_config)

    with SQLiteHelper("session", db_config=db_config).open(write_mode=True) as own:
        own.interrupt_when(stop)
        return _run_import(own, state, jsonl_count, skipped, embed_dim, db_config)


def _run_import(
    db: SQLiteHelper,
    state: dict[str, MemoryEntry],
    jsonl_count: int,
    skipped: int,
    embed_dim: int | None,
    db_config: DbConfig,
) -> MemoryImportResult:
    """Replay the archive inside one transaction on the caller's connection."""
    try:
        with db.begin_immediate():
            db.execute("DELETE FROM memories_vec")
            db.execute("DELETE FROM memories_fts")
            db.execute("DELETE FROM memories")
            for entry in state.values():
                add(entry, embed_dim=embed_dim, db_config=db_config, db=db)
            attempted = len(state)
    except sqlite3.Error:
        # The transaction rolled back, so the archive replay wrote nothing.
        return MemoryImportResult(
            jsonl_count=jsonl_count, skipped=skipped, interrupted=True
        )

    rows = db.fetchall("SELECT COUNT(*) FROM memories")
    committed = int(rows[0][0]) if rows else 0
    logger.info(
        "import_from_jsonl: inserted %d entries from %d JSONL memory lines",
        committed,
        jsonl_count,
    )
    return MemoryImportResult(
        jsonl_count=jsonl_count,
        inserted=committed,
        skipped=skipped,
        verified=committed == attempted,
    )
