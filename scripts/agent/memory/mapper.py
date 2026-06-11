"""agent/memory/mapper.py
Shared SQLite row → MemoryEntry conversion helper.

Used by both store.py (Row objects) and retriever.py (dict rows).
"""

from __future__ import annotations

import sqlite3
from typing import Any

import orjson

from agent.memory.enums import MemoryType
from agent.memory.exceptions import MemorySchemaError
from agent.memory.types import MemoryEntry, SourceType


def _require(d: dict[str, Any], key: str) -> Any:
    try:
        return d[key]
    except KeyError:
        raise MemorySchemaError(f"Memory row missing required field: {key!r}")


def row_to_entry(row: sqlite3.Row | dict[str, Any]) -> MemoryEntry:
    """Convert a sqlite3.Row or dict to MemoryEntry.

    Required fields (NOT NULL in schema): memory_id, memory_type, source_type,
    content, importance, created_at, updated_at.
    Missing required fields raise MemorySchemaError.
    Optional fields (nullable): session_id, turn_id, project, repo, branch, summary, tags, pinned.
    """
    d = dict(row)
    tags_raw = d.get("tags", "[]")
    if isinstance(tags_raw, str):
        tags: list[str] = orjson.loads(tags_raw)
    elif isinstance(tags_raw, list):
        tags = list(tags_raw)
    else:
        raise MemorySchemaError(
            f"tags must be a JSON string or list, got {type(tags_raw).__name__}"
        )
    try:
        importance = float(_require(d, "importance"))
    except (TypeError, ValueError) as e:
        raise MemorySchemaError(
            f"Invalid importance value: {d.get('importance')!r}"
        ) from e
    try:
        memory_type = MemoryType(str(_require(d, "memory_type")))
    except ValueError as e:
        raise MemorySchemaError(str(e)) from e
    try:
        source_type = SourceType(str(_require(d, "source_type")))
    except ValueError as e:
        raise MemorySchemaError(str(e)) from e
    return MemoryEntry(
        memory_id=str(_require(d, "memory_id")),
        memory_type=memory_type,
        source_type=source_type,
        session_id=d.get("session_id"),
        turn_id=d.get("turn_id"),
        project=d.get("project") or "",
        repo=d.get("repo") or "",
        branch=d.get("branch") or "",
        content=str(_require(d, "content")),
        summary=d.get("summary") or "",
        tags=tags,
        importance=importance,
        pinned=bool(d.get("pinned", 0)),
        created_at=d.get("created_at") or "",
        updated_at=d.get("updated_at") or "",
    )
