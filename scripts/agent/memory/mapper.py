"""agent/memory/mapper.py
Shared SQLite row → MemoryEntry conversion helper, plus shared utilities.

Used by both store.py (Row objects) and retriever.py (dict rows).
"""

from __future__ import annotations

import datetime
import sqlite3
import struct
from collections.abc import Mapping
from dataclasses import replace
from typing import cast

import orjson

from agent.memory.enums import MemoryType
from agent.memory.exceptions import MemorySchemaError
from agent.memory.types import MemoryEntry, SourceType


def _now_iso() -> str:
    return datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _stamp_entry(entry: MemoryEntry, now: str) -> MemoryEntry:
    """Return entry with created_at/updated_at filled if empty (frozen-safe)."""
    need_created = not entry.created_at
    need_updated = not entry.updated_at
    if need_created and need_updated:
        return replace(entry, created_at=now, updated_at=now)
    if need_created:
        return replace(entry, created_at=now)
    if need_updated:
        return replace(entry, updated_at=now)
    return entry


def _floats_to_blob(values: list[float], expected_dim: int | None = None) -> bytes:
    """Pack float list to little-endian IEEE-754 BLOB for vec0 MATCH queries.

    When expected_dim is set, raises ValueError if len(values) != expected_dim.
    """
    if expected_dim is not None and len(values) != expected_dim:
        raise ValueError(
            f"Embedding dimension mismatch: expected {expected_dim}, got {len(values)}",
        )
    return struct.pack(f"{len(values)}f", *values)


def _opt_str(d: Mapping[str, object], key: str) -> str:
    """Return string value for key, or "" if absent or None; raises MemorySchemaError on wrong type."""
    v = d.get(key)
    if v is None:
        return ""
    if not isinstance(v, str):
        raise MemorySchemaError(
            f"Field {key!r} must be str or None, got {type(v).__name__}"
        )
    return v


def _require(d: Mapping[str, object], key: str) -> object:
    try:
        return d[key]
    except KeyError:
        raise MemorySchemaError(f"Memory row missing required field: {key!r}")


def _parse_tags(raw: object) -> list[str]:
    """Parse tags from a JSON string or list value."""
    if isinstance(raw, str):
        return cast(list[str], orjson.loads(raw))
    if isinstance(raw, list):
        return [str(v) for v in raw]
    raise MemorySchemaError(
        f"tags must be a JSON string or list, got {type(raw).__name__}"
    )


def _parse_importance(d: Mapping[str, object]) -> float:
    """Parse importance with a default of 0.5 when None."""
    val = d.get("importance")
    if val is None:
        return 0.5
    try:
        return float(val)  # type: ignore[arg-type]
    except (TypeError, ValueError) as e:
        raise MemorySchemaError(
            f"Invalid importance value: {d.get('importance')!r}"
        ) from e


def _parse_memory_type(d: Mapping[str, object]) -> MemoryType:
    """Parse and validate the memory_type field."""
    try:
        return MemoryType(str(_require(d, "memory_type")))
    except ValueError as e:
        raise MemorySchemaError(str(e)) from e


def _parse_source_type(raw: object | None) -> SourceType:
    """Parse source_type with CONVERSATION as default."""
    if raw is None:
        return SourceType.CONVERSATION
    try:
        return SourceType(str(raw))
    except ValueError as e:
        raise MemorySchemaError(f"Invalid source_type: {e}") from e


def row_to_entry(row: sqlite3.Row | Mapping[str, object]) -> MemoryEntry:
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
