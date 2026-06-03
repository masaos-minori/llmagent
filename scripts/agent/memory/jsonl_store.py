#!/usr/bin/env python3
"""agent/memory/jsonl_store.py
Append-only JSONL storage for MemoryEntry (source of truth).

Each line is one JSON object representing a MemoryEntry.
Reads back all entries via read_all() for audit and reconstruction.
"""

from __future__ import annotations

import logging
from dataclasses import asdict
from pathlib import Path

import orjson

from agent.memory.types import MEMORY_TYPES, MemoryEntry, SourceType

logger = logging.getLogger(__name__)


def _entry_from_dict(d: dict) -> MemoryEntry | None:
    """Deserialise one JSONL dict to MemoryEntry; return None on validation error."""
    try:
        memory_type = d.get("memory_type", "")
        raw_source = d.get("source_type", "conversation")
        if memory_type not in MEMORY_TYPES:
            logger.warning(f"Skipping JSONL entry: invalid memory_type={memory_type!r}")
            return None
        try:
            source_type = SourceType(raw_source)
        except ValueError:
            logger.warning(f"Unknown source_type={raw_source!r}; falling back to conversation")
            source_type = SourceType.CONVERSATION
        return MemoryEntry(
            memory_id=str(d["memory_id"]),
            memory_type=memory_type,
            source_type=source_type,
            session_id=d.get("session_id"),
            turn_id=d.get("turn_id"),
            project=d.get("project", ""),
            repo=d.get("repo", ""),
            branch=d.get("branch", ""),
            content=str(d.get("content", "")),
            summary=str(d.get("summary", "")),
            tags=list(d.get("tags", [])),
            importance=float(d.get("importance", 0.5)),
            pinned=bool(d.get("pinned", False)),
            created_at=str(d.get("created_at", "")),
            updated_at=str(d.get("updated_at", "")),
        )
    except Exception as e:
        logger.warning(f"Skipping malformed JSONL entry: {e}")
        return None


class JsonlMemoryStore:
    """Append-only JSONL store.  Thread-unsafe — use from a single asyncio event loop."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)

    def _ensure_parent(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, entry: MemoryEntry) -> None:
        """Append one entry as a single JSONL line."""
        self._ensure_parent()
        line: bytes = orjson.dumps(asdict(entry)) + b"\n"
        with self._path.open("ab") as f:
            f.write(line)
        logger.debug(f"JSONL appended memory_id={entry.memory_id!r}")

    def read_all(self) -> list[MemoryEntry]:
        """Read every entry; skip and log malformed lines."""
        if not self._path.exists():
            return []
        entries: list[MemoryEntry] = []
        with self._path.open("rb") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line:
                    continue
                try:
                    d = orjson.loads(line)
                except Exception as e:
                    logger.warning(f"JSONL parse error: {e}")
                    continue
                entry = _entry_from_dict(d)
                if entry is not None:
                    entries.append(entry)
        return entries
