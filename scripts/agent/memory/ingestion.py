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
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum

from db.helper import SQLiteHelper

from agent.memory.embedding_client import EmbeddingClient
from agent.memory.enums import MemoryType
from agent.memory.extract import extract_memories
from agent.memory.jsonl_store import JsonlMemoryStore
from agent.memory.models import HistoryMessage
from agent.memory.retriever import HybridRetriever
from agent.memory.store import MemoryStore
from agent.memory.types import MemoryEntry, SourceType

logger = logging.getLogger(__name__)


class DedupAction(StrEnum):
    SKIP_NEW = "skip_new"  # skip new entry when a near-duplicate already exists


@dataclass
class DedupPolicy:
    action: DedupAction = DedupAction.SKIP_NEW
    threshold: float = 0.3


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
            embed_result = await self._embed_client.fetch(entry.content)
            embedding = embed_result.embedding if embed_result.success else None
            if (
                self._dedup_policy.action == DedupAction.SKIP_NEW
                and embed_result.success
                and embed_result.embedding is not None
                and self._has_near_duplicate(entry.memory_id, embed_result.embedding)
            ):
                logger.debug("memory.skip_dup memory_id=%r", entry.memory_id)
                continue
            await self._jsonl.write(entry)
            self._store.upsert(entry, embedding=embedding)
            if embed_result.success and embed_result.embedding is not None:
                self._link_duplicates(entry.memory_id, embed_result.embedding)
            logger.info(
                "memory.persist memory_id=%r type=%s importance=%.2f",
                entry.memory_id,
                entry.memory_type,
                entry.importance,
            )
        logger.info("MemoryIngestionService.on_session_stop: persisted entries")

    # ── Dedup helpers ─────────────────────────────────────────────────────────

    def _has_near_duplicate(self, memory_id: str, embedding: list[float]) -> bool:
        """Return True if a near-duplicate entry exists within dedup threshold."""
        neighbors = self._retriever.knn_search(embedding, memory_type=None, limit=5)
        return any(
            # score = -distance (higher is better); negate to get raw L2 distance for comparison
            -h.score < self._dedup_policy.threshold and h.entry.memory_id != memory_id
            for h in neighbors
        )

    def _link_duplicates(self, memory_id: str, embedding: list[float]) -> None:
        """Find near-duplicate entries and record links in memory_links."""
        neighbors = self._retriever.knn_search(embedding, memory_type=None, limit=5)
        for hit in neighbors:
            if hit.entry.memory_id == memory_id:
                continue
            distance = (
                -hit.score
            )  # score = -distance (higher is better); restore for threshold check
            if distance < self._dedup_policy.threshold:
                try:
                    with SQLiteHelper("session").open(write_mode=True) as db:
                        db.execute(
                            "INSERT OR IGNORE INTO memory_links(src_id, dst_id)"
                            " VALUES (?,?)",
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
        now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
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

    async def _persist_entry(self, entry: MemoryEntry) -> None:
        """Persist one entry directly without dedup or duplicate-link checks.

        Used by write_semantic() and write_episodic() (manual writes).
        Automatic session extraction uses on_session_stop() which applies dedup.
        """
        embed_result = await self._embed_client.fetch(entry.content)
        embedding = embed_result.embedding if embed_result.success else None
        await self._jsonl.write(entry)
        self._store.upsert(entry, embedding=embedding)
        logger.info(
            "memory.write memory_id=%r type=%s importance=%.2f",
            entry.memory_id,
            entry.memory_type,
            entry.importance,
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
