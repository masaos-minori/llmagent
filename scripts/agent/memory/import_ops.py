#!/usr/bin/env python3
"""scripts/agent/memory/import_ops.py — Import operations for memory tables."""

import logging
from dataclasses import replace
from typing import TYPE_CHECKING

from db.helper import SQLiteHelper

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
) -> tuple[int, int]:
    """Import entries from a JSONL archive into SQLite memories/FTS/vec tables.

    The archive is replayed top-to-bottom to compute the final state before any
    SQLite write: a memory line adds/overwrites its id, a ``delete`` event removes
    it (a later memory line may re-add it), a ``pin``/``unpin`` event updates
    ``pinned`` when the entry currently exists, and unparsable lines are skipped
    and counted. Only the resulting final state is written, in one transaction, so
    a delete-then-re-add pair never leaves a stale row.

    Returns (jsonl_count, inserted_count): ``jsonl_count`` counts memory lines
    seen, ``inserted_count`` counts rows written. When ``dry_run=True`` the tables
    are left untouched and (jsonl_count, 0) is returned.

    ``backup`` / ``allow_loss`` (REQ-007): a no-loss ``backup`` cannot proceed past
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
    order: list[str] = []
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
                    if mid in order:
                        order.remove(mid)
            elif data.get("event") in ("pin", "unpin"):
                if mid in state:
                    state[mid] = replace(state[mid], pinned=data["event"] == "pin")
            # pin/unpin for a missing entry: nothing to do
            continue
        # kind == "memory"
        entry = _entry_from_dict(data)  # reuse jsonl_store's deserializer
        memory_lines += 1
        state[entry.memory_id] = entry
        if entry.memory_id not in order:
            order.append(entry.memory_id)
    jsonl_count = memory_lines

    if dry_run:
        return jsonl_count, 0

    # REQ-007: a no-loss backup must not silently drop records that cannot be
    # reconstructed from the archive. The precise SQLite-only detection lives in
    # the rebuild row; refuse here when a backup is requested without allow_loss
    # and unparsable (unreconstructable) records were encountered.
    if backup and not allow_loss and skipped > 0:
        raise ValueError(
            "backup=True requires allow_loss=True: "
            f"{skipped} archive record(s) could not be reconstructed"
        )

    with SQLiteHelper("session").open(write_mode=True) as db:
        db.execute("DELETE FROM memories_vec")
        db.execute("DELETE FROM memories_fts")
        db.execute("DELETE FROM memories")
        db.commit()
        for mid in order:
            add(state[mid], embed_dim=embed_dim)

    inserted = len(order)
    logger.info(
        "import_from_jsonl: inserted %d entries from %d JSONL memory lines",
        inserted,
        jsonl_count,
    )
    return jsonl_count, inserted
