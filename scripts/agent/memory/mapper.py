"""agent/memory/mapper.py
Shared SQLite row → MemoryEntry conversion helper.

Used by both store.py (Row objects) and retriever.py (dict rows).
"""

from __future__ import annotations

from typing import Any

import orjson

from agent.memory.types import MemoryEntry, SourceType


def row_to_entry(row: Any) -> MemoryEntry:
    """Convert a sqlite3.Row or dict to MemoryEntry.

    Accepts sqlite3.Row (supports dict(row)) or plain dict.
    Falls back to SourceType.CONVERSATION for unknown source_type values.
    """
    d = dict(row)
    tags_raw = d.get("tags", "[]")
    try:
        tags: list[str] = (
            orjson.loads(tags_raw) if isinstance(tags_raw, str) else list(tags_raw)
        )
    except Exception:
        tags = []
    raw_source = d.get("source_type", "conversation")
    try:
        source_type = SourceType(raw_source)
    except ValueError:
        source_type = SourceType.CONVERSATION
    return MemoryEntry(
        memory_id=d["memory_id"],
        memory_type=d["memory_type"],
        source_type=source_type,
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
