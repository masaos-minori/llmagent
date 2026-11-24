"""scripts/agent/memory/services.py

MemoryServices — facade over the three memory service instances.

Replaces MemoryLayer as the AppServices.memory type.
"""

from __future__ import annotations

import threading

from db.config import DbConfig

from agent.memory.embedding_client import EmbeddingClient
from agent.memory.ingestion import MemoryIngestionService
from agent.memory.injection import MemoryInjectionService
from agent.memory.models import (
    HistoryMessage,
    MemoryImportResult,
    MemoryMaintenanceResult,
    MemorySnippet,
)
from agent.memory.retriever import HybridRetriever
from agent.memory.store import MemoryStore


class MemoryServices:
    """Facade over memory sub-services; injected into AppServices.memory."""

    def __init__(
        self,
        injection: MemoryInjectionService,
        ingestion: MemoryIngestionService,
        store: MemoryStore,
        retriever: HybridRetriever,
        embedding_client: EmbeddingClient | None = None,
        use_memory_layer: bool = True,
        *,
        db_config: DbConfig,
    ) -> None:
        """Initialize the memory services facade with injection, ingestion, storage, and retrieval components."""
        self._db_config = db_config
        self.injection = injection
        self.ingestion = ingestion
        self.store = store
        self.retriever = retriever
        self.embedding_client = embedding_client or getattr(
            retriever, "embed_client", None
        )
        self._use_memory_layer = use_memory_layer

    def get_activation_mode(self) -> str:
        """Return one of: 'disabled' / 'fts-only' / 'degraded' / 'hybrid'."""
        if not self._use_memory_layer:
            return "disabled"
        embed_client = self.embedding_client
        if embed_client is None:
            return "fts-only"
        embed_status = embed_client.get_status()
        if not embed_status.enabled:
            return "fts-only"
        if embed_status.circuit_open:
            return "degraded"
        return "hybrid"

    def get_stats(self) -> dict:
        """Return entry counts, embed_skip, and last retrieval mode."""
        from agent.memory.count_ops import count_by_source_type, count_by_type

        counts = count_by_type(db_config=self._db_config)
        source_counts = count_by_source_type(db_config=self._db_config)
        return {
            "total": sum(counts.values()),
            "semantic": counts.get("semantic", 0),
            "episodic": counts.get("episodic", 0),
            "by_source": source_counts,
            "embed_skip": self.ingestion.stat_embed_skip,
            "last_retrieval_mode": self.retriever.last_retrieval_mode,
            "fts_fallback_count": self.retriever.fts_fallback_count,
        }

    def on_session_start(self, session_id: int | None) -> list[MemorySnippet]:
        """Return top semantic snippets for injection at session start."""
        # session_id not used by injection layer
        return self.injection.on_session_start()

    async def on_session_stop(
        self,
        session_id: int | None,
        history: list[HistoryMessage],
        turn_id: str | None = None,
    ) -> None:
        """Extract and persist memories from session history."""
        await self.ingestion.on_session_stop(session_id, history, turn_id)

    async def on_user_prompt(
        self,
        query: str,
        session_id: int | None,
    ) -> list[MemorySnippet]:
        """Return relevant snippets for the current user query."""
        return await self.injection.on_user_prompt(query, session_id)

    # ── Maintenance accessors ─────────────────────────────────────────────────
    #
    # Each name is the `MemoryStore` accessor of the same name; the facade forwards and
    # implements nothing, so the store stays the single owner of the transaction boundary
    # and the command mixins reach SQLite only through it (REQ-005).

    def pinned_count(self, *, stop: threading.Event | None = None) -> int:
        """Return the pinned count through the store."""
        return self.store.pinned_count(stop=stop)

    def delete(
        self, memory_id: str, *, stop: threading.Event | None = None
    ) -> MemoryMaintenanceResult:
        """Delete one entry through the store."""
        return self.store.delete(memory_id, stop=stop)

    def pin(
        self,
        memory_id: str,
        *,
        max_pinned: int,
        stop: threading.Event | None = None,
    ) -> MemoryMaintenanceResult:
        """Pin one entry through the store."""
        return self.store.pin(memory_id, max_pinned=max_pinned, stop=stop)

    def unpin(
        self, memory_id: str, *, stop: threading.Event | None = None
    ) -> MemoryMaintenanceResult:
        """Release one entry through the store."""
        return self.store.unpin(memory_id, stop=stop)

    def prune(
        self,
        days: int,
        *,
        dry_run: bool = False,
        stop: threading.Event | None = None,
    ) -> MemoryMaintenanceResult:
        """Prune entries older than `days` days through the store."""
        return self.store.prune(days, dry_run=dry_run, stop=stop)

    def reindex(
        self, index_type: str, *, stop: threading.Event | None = None
    ) -> MemoryMaintenanceResult:
        """Rebuild one memory index through the store."""
        return self.store.reindex(index_type, stop=stop)

    def rebuild(
        self, *, stop: threading.Event | None = None
    ) -> MemoryMaintenanceResult:
        """Rebuild both memory indexes through the store."""
        return self.store.rebuild(stop=stop)

    def import_jsonl(
        self,
        jsonl_store: object,
        *,
        dry_run: bool = False,
        backup: bool = False,
        allow_loss: bool = False,
        stop: threading.Event | None = None,
    ) -> MemoryImportResult:
        """Replay the JSONL archive through the store."""
        return self.store.import_jsonl(
            jsonl_store,
            dry_run=dry_run,
            backup=backup,
            allow_loss=allow_loss,
            stop=stop,
        )
