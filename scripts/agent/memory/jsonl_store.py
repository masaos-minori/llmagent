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

import orjson

from agent.memory.mapper import row_to_entry
from agent.memory.types import MEMORY_TYPES, MemoryEntry

logger = logging.getLogger(__name__)


def _entry_from_dict(d: dict) -> MemoryEntry | None:
    """Deserialise one JSONL dict to MemoryEntry; return None on validation error."""
    try:
        memory_type = d.get("memory_type", "")
        if memory_type not in MEMORY_TYPES:
            logger.warning(f"Skipping JSONL entry: invalid memory_type={memory_type!r}")
            return None
        return row_to_entry(d)
    except Exception as e:
        logger.warning(f"Skipping malformed JSONL entry: {e}")
        return None


class JsonlMemoryStore:
    """Append-only JSONL store.  Thread-unsafe — use from a single asyncio event loop."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._lock: asyncio.Lock | None = None  # lazy: created after event loop starts
        self._malformed_count: int = 0

    def _get_lock(self) -> asyncio.Lock:
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    @property
    def malformed_count(self) -> int:
        return self._malformed_count

    async def write(self, entry: MemoryEntry) -> None:
        """Append one entry to the JSONL file; serialized by asyncio.Lock."""
        async with self._get_lock():
            line = orjson.dumps(asdict(entry)).decode() + "\n"
            self._path.parent.mkdir(parents=True, exist_ok=True)
            with self._path.open("a", encoding="utf-8") as f:
                f.write(line)

    def read_all(self) -> list[MemoryEntry]:
        """Read all entries; skip and count malformed lines."""
        if not self._path.exists():
            return []
        entries: list[MemoryEntry] = []
        with self._path.open("r", encoding="utf-8") as f:
            for lineno, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    d = orjson.loads(line)
                    entry = _entry_from_dict(d)
                    if entry is not None:
                        entries.append(entry)
                    else:
                        self._malformed_count += 1
                        logger.warning(
                            "Skipping malformed JSONL line %d (count=%d)",
                            lineno,
                            self._malformed_count,
                        )
                except orjson.JSONDecodeError as e:
                    self._malformed_count += 1
                    logger.warning(
                        "JSON decode error at line %d (count=%d): %s",
                        lineno,
                        self._malformed_count,
                        e,
                    )
        return entries
