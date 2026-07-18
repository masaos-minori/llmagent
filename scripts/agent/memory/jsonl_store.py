#!/usr/bin/env python3
"""agent/memory/jsonl_store.py

Append-only JSONL archive for MemoryEntry.

Each line is one JSON object representing a MemoryEntry at the time of write.
The JSONL file is an append-only archive; it does NOT record mutations (delete,
pin, unpin). SQLite (via MemoryStore) is the authoritative source of truth.

Use read_all() for audit, export, or one-time import. Do not use it to rebuild
authoritative state — use MemoryStore directly or restore from a SQLite backup.
"""

from __future__ import annotations

import asyncio
import datetime
import logging
from collections.abc import Mapping
from dataclasses import asdict
from pathlib import Path

import orjson
from shared.json_utils import dumps as _json_dumps

from agent.memory.enums import RETENTION_DAYS, MemoryType
from agent.memory.exceptions import JsonlFormatError
from agent.memory.mapper import row_to_entry
from agent.memory.types import MemoryEntry

logger = logging.getLogger(__name__)


def _entry_from_dict(d: Mapping[str, object]) -> MemoryEntry:
    """Deserialise one JSONL dict to MemoryEntry; raises JsonlFormatError on error."""
    if "memory_type" not in d:
        raise JsonlFormatError("Missing required field: 'memory_type'")
    memory_type = d["memory_type"]
    if not isinstance(memory_type, str):
        raise JsonlFormatError(
            f"'memory_type' must be a str, got {type(memory_type).__name__}"
        )
    try:
        MemoryType(memory_type)
    except ValueError:
        raise JsonlFormatError(f"Invalid memory_type={memory_type!r}") from None
    return row_to_entry(d)


class JsonlMemoryStore:
    """Append-only JSONL store.  Thread-unsafe — use from a single asyncio event loop."""

    def __init__(self, path: str | Path) -> None:
        """Initialize the JSONL store with the given file path."""
        self._path = Path(path)
        self._lock: asyncio.Lock | None = None  # lazy: created after event loop starts

    def _get_lock(self) -> asyncio.Lock:
        """Return the asyncio.Lock, creating it lazily after the event loop starts."""
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    async def write(self, entry: MemoryEntry) -> None:
        """Append one entry to the JSONL file; serialized by asyncio.Lock."""
        async with self._get_lock():
            line = _json_dumps(asdict(entry)) + "\n"
            self._path.parent.mkdir(parents=True, exist_ok=True)
            with self._path.open("a", encoding="utf-8") as f:
                f.write(line)

    def read_all(self) -> list[MemoryEntry]:
        """Read all entries; raises JsonlFormatError on first malformed line."""
        if not self._path.exists():
            return []
        entries: list[MemoryEntry] = []
        with self._path.open("r", encoding="utf-8") as f:
            for lineno, raw_line in enumerate(f, 1):
                line = raw_line.strip()
                if not line:
                    continue
                try:
                    d = orjson.loads(line)
                    entries.append(_entry_from_dict(d))
                except (orjson.JSONDecodeError, ValueError, TypeError) as e:
                    raise JsonlFormatError(
                        f"Malformed JSONL at line {lineno}: {e}"
                    ) from e
        return entries

    def read_active(self) -> list[MemoryEntry]:
        """Return entries that have not expired based on per-source-type retention policy."""
        entries = self.read_all()
        now = datetime.datetime.now(datetime.UTC)
        active: list[MemoryEntry] = []
        for entry in entries:
            source_key = str(entry.source_type).upper()
            max_days = RETENTION_DAYS.get(source_key)
            if max_days is None:
                active.append(entry)
                continue
            try:
                created = datetime.datetime.fromisoformat(
                    entry.created_at.replace("Z", "+00:00")
                )
                age_days = (now - created).total_seconds() / 86_400.0
                if age_days <= max_days:
                    active.append(entry)
            except (ValueError, OverflowError):
                active.append(entry)
        return active

    def count_all(self) -> int:
        """Return total number of valid records in the JSONL file."""
        return len(self.read_all())
