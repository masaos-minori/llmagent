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


def _entry_from_dict(d: dict) -> MemoryEntry:
    """Deserialise one JSONL dict to MemoryEntry; raises on validation error."""
    memory_type = d.get("memory_type", "")
    if memory_type not in MEMORY_TYPES:
        raise ValueError(f"Invalid memory_type={memory_type!r}")
    return row_to_entry(d)


class JsonlMemoryStore:
    """Append-only JSONL store.  Thread-unsafe — use from a single asyncio event loop."""

    def __init__(
        self,
        path: str | Path,
        quarantine_path: str | Path | None = None,
    ) -> None:
        self._path = Path(path)
        self._quarantine = Path(quarantine_path) if quarantine_path else None
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

    def read_all(self, *, strict: bool = False) -> list[MemoryEntry]:
        """Read all entries.

        strict=True: raises ValueError on first malformed line.
        strict=False (default): malformed lines are written to quarantine_path if set,
          otherwise raises ValueError.
        """
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
                    if strict or self._quarantine is None:
                        raise ValueError(
                            f"Malformed JSONL at line {lineno}: {e}"
                        ) from e
                    self._malformed_count += 1
                    logger.warning(
                        "Malformed JSONL line %d (count=%d): %s",
                        lineno,
                        self._malformed_count,
                        e,
                    )
                    self._quarantine.parent.mkdir(parents=True, exist_ok=True)
                    with self._quarantine.open("a", encoding="utf-8") as qf:
                        qf.write(raw_line)
        return entries
