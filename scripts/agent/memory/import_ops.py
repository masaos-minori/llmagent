#!/usr/bin/env python3
"""agent/memory/import_ops.py — Import operations for memory tables."""

import logging

from db.helper import SQLiteHelper

from agent.memory.write_ops import add

logger = logging.getLogger(__name__)


def import_from_jsonl(
    jsonl_store: object,
    *,
    dry_run: bool = False,
    embed_dim: int | None = None,
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
    from agent.memory.jsonl_store import JsonlMemoryStore as _JsonlMemoryStore

    if not isinstance(jsonl_store, _JsonlMemoryStore):
        raise TypeError(f"Expected JsonlMemoryStore, got {type(jsonl_store).__name__}")
    entries = jsonl_store.read_all()
    jsonl_count = len(entries)
    if dry_run:
        return jsonl_count, 0
    with SQLiteHelper("session").open(write_mode=True) as db:
        db.execute("DELETE FROM memories_vec")
        db.execute("DELETE FROM memories_fts")
        db.execute("DELETE FROM memories")
        db.commit()
    for entry in entries:
        add(entry, embed_dim=embed_dim)
    logger.info("import_from_jsonl: inserted %d entries from JSONL", jsonl_count)
    return jsonl_count, jsonl_count
