#!/usr/bin/env python3
"""agent/memory/jsonl_store.py
Append-only JSONL storage for MemoryEntry (source of truth).

Each line is one JSON object representing a MemoryEntry.
Reads back all entries via read_all() for audit and reconstruction.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import asdict
from pathlib import Path
from typing import Any

import orjson
from shared.json_utils import dumps as _json_dumps

from agent.memory.enums import MemoryType
from agent.memory.exceptions import JsonlFormatError
from agent.memory.mapper import row_to_entry
from agent.memory.types import MemoryEntry

logger = logging.getLogger(__name__)


def _entry_from_dict(d: dict[str, Any]) -> MemoryEntry:
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
        self._path = Path(path)
        self._lock: asyncio.Lock | None = None  # lazy: created after event loop starts

    def _get_lock(self) -> asyncio.Lock:
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
