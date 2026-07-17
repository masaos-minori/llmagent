"""agent/memory/ingestion.py

MemoryIngestionService — on_session_stop / write_* / dedup policy.

Extracts memory from conversation history, deduplicates via embedding KNN,
and persists to JSONL + SQLite.

DedupAction.SKIP_NEW: if a near-duplicate embedding exists in the store,
the new entry is discarded instead of stored.
"""

from __future__ import annotations

import logging
import sqlite3
import uuid

from db.helper import SQLiteHelper
from shared.json_utils import now_iso

from agent.memory.embedding_client import (
    EmbeddingClient,
    EmbeddingErrorKind,
    EmbeddingResult,
)
from agent.memory.enums import DEDUP_THRESHOLDS, DedupAction, DedupPolicy, MemoryType
from agent.memory.extract import extract_memories
from agent.memory.jsonl_store import JsonlMemoryStore
from agent.memory.models import HistoryMessage
from agent.memory.retriever import HybridRetriever
from agent.memory.store import MemoryStore
from agent.memory.types import MemoryEntry, SourceType
from agent.memory.write_ops import upsert as write_upsert

logger = logging.getLogger(__name__)


class MemoryIngestionService:
    """Extracts, deduplicates, and persists memory entries from session history."""

    def __init__(
        self,
        store: MemoryStore,
        jsonl: JsonlMemoryStore,
        retriever: HybridRetriever,
        embed_client: EmbeddingClient,
        dedup_policy: DedupPolicy | None = None,
        project: str = "",
        repo: str = "",
        branch: str = "",
        max_content_chars: int = 500,
    ) -> None:
        self._store = store
        self._jsonl = jsonl
        self._retriever = retriever
        self._embed_client = embed_client
        self._dedup_policy = dedup_policy or DedupPolicy()
        self._project = project
        self._repo = repo
        self._branch = branch
        self._max_content_chars = max_content_chars
        self.stat_embed_skip: int = 0

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    async def on_session_stop(
        self,
        session_id: int | None,
        history: list[HistoryMessage],
        turn_id: str | None = None,
    ) -> None:
        """Extract memories from history and persist with optional dedup.

        Applies embedding-based dedup (SKIP_NEW) and records duplicate links.
        Manual writes via write_semantic/write_episodic bypass dedup intentionally.
        """
        entries = extract_memories(
            history=history,
            session_id=session_id,
            turn_id=turn_id,
            project=self._project,
            repo=self._repo,
            branch=self._branch,
            max_content_chars=self._max_content_chars,
        )
        if not entries:
            logger.debug("MemoryIngestionService.on_session_stop: no entries extracted")
            return
        for entry in entries:
            await self._persist_entry_with_dedup(entry)
        logger.info(
            "MemoryIngestionService.on_session_stop: persisted %d entries; %d embed_skipped",
            len(entries),
            self.stat_embed_skip,
        )

    async def _persist_entry_with_dedup(self, entry: MemoryEntry) -> None:
        """Embed, dedup-check, and persist a single memory entry."""
        embed_result = await self._fetch_embed_result(entry.content)
        if not embed_result.success:
            self.stat_embed_skip += 1
            logger.info(
                "memory.embed_skip: stored without embedding (reason=%s) memory_id=%r",
                embed_result.error_kind,
                entry.memory_id,
            )
        if self._should_skip_dedup(embed_result, entry.memory_id, entry):
            return
        await self._persist_entry_with_embedding(entry, embed_result)

    async def _persist_entry(self, entry: MemoryEntry) -> None:
        """Persist one entry directly without dedup or duplicate-link checks.

        Used by write_semantic() and write_episodic() (manual writes).
        Automatic session extraction uses on_session_stop() which applies dedup.
        """
        embed_result = await self._fetch_embed_result(entry.content)
        if not embed_result.success:
            self.stat_embed_skip += 1
            logger.info(
                "memory.embed_skip: stored without embedding (reason=%s) memory_id=%r",
                embed_result.error_kind,
                entry.memory_id,
            )
        await self._persist_entry_with_embedding(entry, embed_result)

    async def _fetch_embed_result(self, content: str) -> EmbeddingResult:
        """Fetch embedding and return result (with fallback on failure)."""
        try:
            return await self._embed_client.fetch(content)
        except Exception:
            return EmbeddingResult(
                success=False,
                error_kind=EmbeddingErrorKind.UNKNOWN_ERROR,
                embedding=None,
            )

    async def _persist_entry_with_embedding(
        self, entry: MemoryEntry, embed_result: EmbeddingResult
    ) -> None:
        """Persist an entry to SQLite and JSONL with the given embedding result."""
        embedding = embed_result.embedding if embed_result.success else None
        write_upsert(entry, embedding=embedding, embed_dim=self._store._embed_dim)
        try:
            await self._jsonl.write(entry)
        except OSError as e:
            logger.warning(
                "memory.jsonl_write_failed memory_id=%r — entry saved in SQLite only: %s",
                entry.memory_id,
                e,
            )
        if embed_result.success and embed_result.embedding is not None:
            self._link_duplicates(entry.memory_id, embed_result.embedding)
        logger.info(
            "memory.persist memory_id=%r type=%s importance=%.2f",
            entry.memory_id,
            entry.memory_type,
            entry.importance,
        )

    def _should_skip_dedup(
        self, embed_result: EmbeddingResult, memory_id: str, entry: MemoryEntry
    ) -> bool:
        """Return True when dedup skips this entry."""
        if (
            self._dedup_policy.action == DedupAction.SKIP_NEW
            and embed_result.success
            and embed_result.embedding is not None
            and self._has_near_duplicate(memory_id, embed_result.embedding, entry)
        ):
            logger.debug("memory.skip_dup memory_id=%r", memory_id)
            return True
        return False

    # ── Dedup helpers ─────────────────────────────────────────────────────────

    def _get_dedup_threshold(self, entry: MemoryEntry) -> float:
        """Return the dedup similarity threshold for this entry's source type."""
        source_key = str(entry.source_type).upper()
        threshold: float = DEDUP_THRESHOLDS.get(
            source_key, self._dedup_policy.threshold
        )
        return threshold

    def _has_near_duplicate(
        self, memory_id: str, embedding: list[float], entry: MemoryEntry
    ) -> bool:
        """Return True if a near-duplicate entry exists within source-type dedup threshold."""
        threshold = self._get_dedup_threshold(entry)
        neighbors = self._retriever.knn_search(embedding, memory_type=None, limit=5)
        return any(
            -h.score < threshold and h.entry.memory_id != memory_id for h in neighbors
        )

    def _link_duplicates(self, memory_id: str, embedding: list[float]) -> None:
        """Find near-duplicate entries and record links in memory_links."""
        neighbors = self._retriever.knn_search(embedding, memory_type=None, limit=5)
        for hit in neighbors:
            if hit.entry.memory_id == memory_id:
                continue
            distance = -hit.score
            if distance < self._dedup_policy.threshold:
                try:
                    with SQLiteHelper("session").open(write_mode=True) as db:
                        db.execute(
                            "INSERT OR IGNORE INTO memory_links(src_id, dst_id) VALUES (?,?)",
                            (memory_id, hit.entry.memory_id),
                        )
                        db.commit()
                    logger.debug(
                        "memory_links: %r → %r distance=%.3f",
                        memory_id,
                        hit.entry.memory_id,
                        distance,
                    )
                except (sqlite3.OperationalError, sqlite3.IntegrityError) as e:
                    logger.warning("memory_links insert failed: %s", e)

    # ── Manual write ──────────────────────────────────────────────────────────

    def _build_manual_entry(
        self,
        *,
        memory_type: MemoryType,
        source_type: SourceType,
        content: str,
        session_id: int | None,
        importance: float,
    ) -> MemoryEntry:
        now = now_iso()
        return MemoryEntry(
            memory_id=str(uuid.uuid4()),
            memory_type=memory_type,
            source_type=source_type,
            session_id=session_id,
            turn_id=None,
            project=self._project,
            repo=self._repo,
            branch=self._branch,
            content=content,
            summary=content[:120],
            tags=["manual"],
            importance=importance,
            pinned=False,
            created_at=now,
            updated_at=now,
        )

    async def write_semantic(self, session_id: int | None, content: str) -> None:
        """Persist a semantic memory entry manually."""
        entry = self._build_manual_entry(
            memory_type=MemoryType.SEMANTIC,
            source_type=SourceType.RULE,
            content=content,
            session_id=session_id,
            importance=0.7,
        )
        await self._persist_entry(entry)

    async def write_episodic(self, session_id: int | None, content: str) -> None:
        """Persist an episodic memory entry manually."""
        entry = self._build_manual_entry(
            memory_type=MemoryType.EPISODIC,
            source_type=SourceType.CONVERSATION,
            content=content,
            session_id=session_id,
            importance=0.5,
        )
        await self._persist_entry(entry)
