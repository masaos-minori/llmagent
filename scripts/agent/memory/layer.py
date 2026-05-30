#!/usr/bin/env python3
"""
memory_layer.py
Orchestration layer for the 4-tier memory architecture.

Tier mapping:
  Short-term  : ctx.history (managed by HistoryManager — outside this module)
  Long-term   : memory_entries WHERE mem_type='long_term'
  Semantic    : memory_vec KNN search (requires vec0 extension)
  Task        : memory_entries WHERE mem_type='task'

MemoryLayer provides a clean facade over MemoryStore:
  write_long_term() / write_task() — store factual or task-scoped text
  read()                           — retrieve entries by type
  clear()                          — evict entries (session-scoped or full reset)
  stat_entries                     — total entry count for /context display

Design: MemoryLayer does NOT call print(); all output goes through logger or
        the caller's display layer (CLIView callbacks).
"""

import logging

from agent.memory.store import MemoryStore
from db.helper import SQLiteHelper

logger = logging.getLogger(__name__)


class MemoryLayer:
    """High-level memory orchestration built on top of MemoryStore.

    Injected into ServiceContainer.memory by AgentREPL._init_components()
    when use_memory_layer=True.  All I/O is delegated to the MemoryStore.
    """

    def __init__(self, store: MemoryStore) -> None:
        self._store = store

    # ── Write operations ──────────────────────────────────────────────────────

    def write_long_term(self, session_id: int | None, content: str) -> None:
        """Persist a fact to long-term memory; pass session_id=None for cross-session facts."""
        entry_id = self._store.add(session_id, "long_term", content)
        logger.debug(f"MemoryLayer: long_term entry added (entry_id={entry_id})")

    def write_task(self, session_id: int | None, content: str) -> None:
        """Persist a task-scoped note; clear when done via clear(session_id=...)."""
        entry_id = self._store.add(session_id, "task", content)
        logger.debug(f"MemoryLayer: task entry added (entry_id={entry_id})")

    # ── Read operations ───────────────────────────────────────────────────────

    def read(self, mem_type: str, limit: int = 5) -> list[str]:
        """Return the most-recent entries of mem_type ('long_term' or 'task') as strings."""
        rows = self._store.search_by_type(mem_type, limit=limit)
        return [row["content"] for row in rows]

    # ── Housekeeping ──────────────────────────────────────────────────────────

    def clear(self, session_id: int | None = None) -> None:
        """Remove entries for session_id, or all entries when session_id is None."""
        count = self._store.clear(session_id=session_id)
        logger.info(
            f"MemoryLayer: cleared {count} entries"
            f" (session_id={session_id if session_id is not None else 'all'})"
        )

    # ── Statistics ────────────────────────────────────────────────────────────

    @property
    def stat_entries(self) -> int:
        """Total entry count across all types; 0 on DB error."""
        try:
            with SQLiteHelper("session").open() as db:
                rows = db.fetchall("SELECT COUNT(*) FROM memory_entries")
            result: int = rows[0][0] if rows else 0
            return result
        except Exception as e:
            logger.warning(f"MemoryLayer.stat_entries failed: {e}")
            return 0
