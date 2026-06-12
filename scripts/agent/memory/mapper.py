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


def _opt_str(d: dict[str, Any], key: str) -> str:
    """Return string value for key, or "" if absent or None; raises MemorySchemaError on wrong type."""
    v = d.get(key)
    if v is None:
        return ""
    if not isinstance(v, str):
        raise MemorySchemaError(
            f"Field {key!r} must be str or None, got {type(v).__name__}"
        )
    return v


def _require(d: dict[str, Any], key: str) -> Any:
    try:
        return d[key]
    except KeyError:
        raise MemorySchemaError(f"Memory row missing required field: {key!r}")


def _parse_tags(raw: Any) -> list[str]:
    """Parse tags from a JSON string or list value."""
    if isinstance(raw, str):
        return orjson.loads(raw)  # type: ignore[no-any-return]
    if isinstance(raw, list):
        return list(raw)
    raise MemorySchemaError(
        f"tags must be a JSON string or list, got {type(raw).__name__}"
    )


def _parse_importance(d: dict[str, Any]) -> float:
    """Parse importance with a default of 0.5 when None."""
    val = d.get("importance")
    if val is None:
        return 0.5
    try:
        return float(val)
    except (TypeError, ValueError) as e:
        raise MemorySchemaError(
            f"Invalid importance value: {d.get('importance')!r}"
        ) from e


def _parse_memory_type(d: dict[str, Any]) -> MemoryType:
    """Parse and validate the memory_type field."""
    try:
        return MemoryType(str(_require(d, "memory_type")))
    except ValueError as e:
        raise MemorySchemaError(str(e)) from e


def _parse_source_type(raw: Any | None) -> SourceType:
    """Parse source_type with CONVERSATION as default."""
    if raw is None:
        return SourceType.CONVERSATION
    try:
        return SourceType(str(raw))
    except ValueError as e:
        raise MemorySchemaError(f"Invalid source_type: {e}") from e


def row_to_entry(row: sqlite3.Row | dict[str, Any]) -> MemoryEntry:
    """Convert a sqlite3.Row or dict to MemoryEntry.

    Required fields (NOT NULL in schema): memory_id, memory_type, content.
    Optional fields with defaults: source_type → CONVERSATION, importance → 0.5.
    Other optional fields (nullable): session_id, turn_id, project, repo, branch, summary, tags, pinned.
    """
    d = dict(row)
    _mid = _require(d, "memory_id")
    _mid = str(_mid) if not isinstance(_mid, str) else _mid
    _content = _require(d, "content")
    if not isinstance(_content, str):
        raise MemorySchemaError(f"content must be str, got {type(_content).__name__}")
    return MemoryEntry(
        memory_id=_mid,
        memory_type=_parse_memory_type(d),
        source_type=_parse_source_type(d.get("source_type")),
        session_id=d.get("session_id"),
        turn_id=d.get("turn_id"),
        project=_opt_str(d, "project"),
        repo=_opt_str(d, "repo"),
        branch=_opt_str(d, "branch"),
        content=_content,
        summary=_opt_str(d, "summary"),
        tags=_parse_tags(d.get("tags", "[]")),
        importance=_parse_importance(d),
        pinned=bool(d.get("pinned")) if d.get("pinned") is not None else False,
        created_at=_opt_str(d, "created_at"),
        updated_at=_opt_str(d, "updated_at"),
    )
