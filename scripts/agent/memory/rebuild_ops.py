#!/usr/bin/env python3
"""scripts/agent/memory/rebuild_ops.py — Rebuild operations for memory tables."""

from db.config import DbConfig
from db.helper import SQLiteHelper


def rebuild_fts(*, db_config: DbConfig) -> int:
    """Rebuild memories_fts from the memories table. Returns number of rows inserted."""
    with SQLiteHelper("session", db_config=db_config).open(write_mode=True) as db:
        db.execute("DELETE FROM memories_fts")
        rows = db.execute(
            "SELECT memory_id, content, summary, tags FROM memories"
        ).fetchall()
        for row in rows:
            db.execute(
                "INSERT INTO memories_fts(memory_id, content, summary, tags) VALUES (?,?,?,?)",
                (row["memory_id"], row["content"], row["summary"], row["tags"]),
            )
        return len(rows)


def rebuild_vec(*, db_config: DbConfig) -> int:
    """Rebuild memories_vec from the memories table. Returns number of rows inserted."""
    with SQLiteHelper("session", db_config=db_config).open(write_mode=True) as db:
        db.execute("DELETE FROM memories_vec")
        rows = db.execute(
            "SELECT memory_id, embedding FROM memories WHERE embedding IS NOT NULL"
        ).fetchall()
        for row in rows:
            db.execute(
                "INSERT INTO memories_vec(memory_id, embedding) VALUES (?,?)",
                (row["memory_id"], row["embedding"]),
            )
        return len(rows)


def reindex(index_type: str, *, db_config: DbConfig) -> int:
    """Rebuild a single memory index ('fts' or 'vec'); return rows inserted."""
    if index_type == "fts":
        return rebuild_fts(db_config=db_config)
    if index_type == "vec":
        return rebuild_vec(db_config=db_config)
    raise ValueError(f"Unknown index type {index_type!r}; expected 'fts' or 'vec'")
