"""agent/memory/layer.py
MemoryLayer — thin facade over three sub-services.

Delegates all lifecycle hooks and write operations to:
  MemoryInjectionService  (injection.py) — on_session_start / on_user_prompt
  MemoryIngestionService  (ingestion.py) — on_session_stop / write_* / dedup
  EmbeddingClient         (embedding_client.py) — embedding generation

Housekeeping (clear / stat_*) stays here as they use SQLiteHelper directly.

Constructor signature is intentionally identical to the old monolithic
MemoryLayer so factory.py and all callers need no changes.
"""

from __future__ import annotations

import logging

import httpx
from db.helper import SQLiteHelper
from db.maintenance import prune_old_memories
from shared.types import LLMMessage

from agent.memory.embedding_client import EmbeddingClient, EmbeddingClientConfig
from agent.memory.ingestion import DedupPolicy, MemoryIngestionService
from agent.memory.injection import InjectionPolicy, MemoryInjectionService
from agent.memory.jsonl_store import JsonlMemoryStore
from agent.memory.retriever import MemoryRetriever
from agent.memory.store import MemoryStore
from agent.memory.types import MemoryEntry, MemoryHit, MemoryQuery

logger = logging.getLogger(__name__)


class MemoryLayer:
    """High-level memory orchestration facade.

    Injected into AppServices.memory when use_memory_layer=True.
    All lifecycle hooks delegate to MemoryInjectionService / MemoryIngestionService.
    """

    def __init__(
        self,
        store: MemoryStore,
        retriever: MemoryRetriever,
        jsonl: JsonlMemoryStore,
        max_inject_semantic: int = 5,
        max_inject_episodic: int = 3,
        min_importance: float = 0.3,
        project: str = "",
        repo: str = "",
        branch: str = "",
        http: httpx.AsyncClient | None = None,
        embed_url: str = "",
        embed_enabled: bool = False,
        dedup_threshold: float = 0.3,
        embed_timeout: float = 5.0,
        max_content_chars: int = 500,
    ) -> None:
        embed_cfg = EmbeddingClientConfig(
            embed_url=embed_url,
            timeout=embed_timeout,
        )
        self._embed_client = EmbeddingClient(embed_cfg, http, enabled=embed_enabled)

        inj_policy = InjectionPolicy(
            max_semantic=max_inject_semantic,
            max_episodic=max_inject_episodic,
            min_importance=min_importance,
        )
        self._injection = MemoryInjectionService(
            policy=inj_policy,
            retriever=retriever,
            embed_client=self._embed_client,
            project=project,
            repo=repo,
        )

        dedup_policy = DedupPolicy(threshold=dedup_threshold)
        self._ingestion = MemoryIngestionService(
            store=store,
            jsonl=jsonl,
            retriever=retriever,
            embed_client=self._embed_client,
            dedup_policy=dedup_policy,
            project=project,
            repo=repo,
            branch=branch,
            max_content_chars=max_content_chars,
        )
        self._store = store

    # ── SessionStart ──────────────────────────────────────────────────────────

    def on_session_start(self, session_id: int | None) -> list[str]:
        return self._injection.on_session_start(session_id)

    # ── UserPromptSubmit ─────────────────────────────────────────────────────

    async def on_user_prompt(
        self,
        query: str,
        session_id: int | None,
    ) -> list[str]:
        return await self._injection.on_user_prompt(query, session_id)

    # ── Stop ─────────────────────────────────────────────────────────────────

    async def on_session_stop(
        self,
        session_id: int | None,
        history: list[LLMMessage],
        turn_id: str | None = None,
    ) -> None:
        await self._ingestion.on_session_stop(session_id, history, turn_id)

    # ── Manual write operations ───────────────────────────────────────────────

    async def write_semantic(self, session_id: int | None, content: str) -> None:
        await self._ingestion.write_semantic(session_id, content)

    async def write_episodic(self, session_id: int | None, content: str) -> None:
        await self._ingestion.write_episodic(session_id, content)

    # ── Public CRUD facade (no direct _store access from command layer) ──────

    def list_entries(self, mem_type: str = "", limit: int = 10) -> list:
        """Return entries filtered by mem_type ('semantic'|'episodic'|''), sorted by pinned/importance."""
        if mem_type:
            return self._store.search_by_type(memory_type=mem_type, limit=limit)
        sem = self._store.search_by_type("semantic", limit=limit)
        epi = self._store.search_by_type("episodic", limit=limit)
        return sorted(sem + epi, key=lambda e: (not e.pinned, -e.importance))[:limit]

    def get_entry(self, memory_id: str) -> MemoryEntry | None:
        """Return a single MemoryEntry by ID, or None if not found."""
        return self._store.get_by_id(memory_id)

    def pin_entry(self, memory_id: str) -> bool:
        """Pin the entry with the given ID; return True on success."""
        return self._store.pin(memory_id)

    def unpin_entry(self, memory_id: str) -> bool:
        """Unpin the entry with the given ID; return True on success."""
        return self._store.unpin(memory_id)

    def delete_entry(self, memory_id: str) -> bool:
        """Delete the entry with the given ID; return True on success."""
        ok = self._store.delete(memory_id)
        if ok:
            logger.info("MemoryLayer.delete_entry: memory_id=%r", memory_id)
        return ok

    def prune(self, days: int) -> int:
        """Delete entries older than `days` days from SQLite; return count deleted."""
        try:
            with SQLiteHelper("session").open(write_mode=True) as db:
                deleted = prune_old_memories(db, days)
            logger.info("MemoryLayer.prune: deleted=%d days=%d", deleted, days)
            return deleted
        except Exception as e:
            logger.warning("MemoryLayer.prune failed: %s", e)
            return 0

    def count_prunable(self, days: int) -> int:
        """Return count of entries older than `days` days without deleting."""
        try:
            with SQLiteHelper("session").open() as db:
                row = db.fetchall(
                    "SELECT COUNT(*) FROM memories WHERE created_at < datetime('now', ?)",
                    (f"-{days} days",),
                )
                return int(row[0][0]) if row else 0
        except Exception as e:
            logger.warning("MemoryLayer.count_prunable failed: %s", e)
            return 0

    # ── Search / store accessor ───────────────────────────────────────────────

    def search(self, query: str, limit: int = 10) -> list[MemoryHit]:
        """Search memories by FTS5 query; delegates to MemoryInjectionService retriever."""
        return self._ingestion._retriever.search(
            MemoryQuery(query=query, limit=limit),
            project=self._ingestion._project,
            repo=self._ingestion._repo,
        )

    # ── Housekeeping ──────────────────────────────────────────────────────────

    def clear(self, session_id: int | None = None) -> None:
        """Remove entries for session_id, or all entries when session_id is None."""
        cleared: int
        if session_id is not None:
            cleared = self._store.clear_by_session(session_id)
        else:
            try:
                with SQLiteHelper("session").open(write_mode=True) as db:
                    cur = db.execute("DELETE FROM memories")
                    db.execute("DELETE FROM memories_fts")
                    try:
                        db.execute("DELETE FROM memories_vec")
                    except Exception as e:
                        logger.warning("memories_vec DELETE skipped: %s", e)
                    cleared = cur.rowcount
                    db.commit()
            except Exception as e:
                logger.warning("MemoryLayer.clear failed: %s", e)
                return
        logger.info(
            "MemoryLayer.clear: removed %d entries (session_id=%s)",
            cleared,
            session_id if session_id is not None else "all",
        )

    # ── Statistics ────────────────────────────────────────────────────────────

    @property
    def stat_entries(self) -> int:
        """Total entry count across all types; 0 on DB error."""
        try:
            with SQLiteHelper("session").open() as db:
                rows = db.fetchall("SELECT COUNT(*) FROM memories")
            result: int = rows[0][0] if rows else 0
            return result
        except Exception as e:
            logger.warning("MemoryLayer.stat_entries failed: %s", e)
            return 0

    @property
    def stat_by_type(self) -> dict[str, int]:
        """Entry counts per memory_type; {} on DB error."""
        try:
            return self._store.count_by_type()
        except Exception as e:
            logger.warning("MemoryLayer.stat_by_type failed: %s", e)
            return {}

    @property
    def stat_vec_entries(self) -> int:
        """Total entry count in memories_vec; 0 if embed disabled or error."""
        return self._store.count_vec()
