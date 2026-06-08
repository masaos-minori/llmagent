"""agent/memory/ingestion.py
MemoryIngestionService — on_session_stop / write_* / dedup policy.

Extracts memory from conversation history, deduplicates via embedding KNN,
and persists to JSONL + SQLite.

DedupAction.SKIP_NEW (default): if a near-duplicate embedding exists in the
store, the new entry is discarded instead of stored.
LINK_ONLY: persist the entry even when a near-duplicate exists, then link them.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum

from db.helper import SQLiteHelper
from shared.types import LLMMessage

from agent.memory.embedding_client import EmbeddingClient
from agent.memory.extract import extract_memories
from agent.memory.jsonl_store import JsonlMemoryStore
from agent.memory.retriever import MemoryRetriever
from agent.memory.store import MemoryStore
from agent.memory.types import MemoryEntry, SourceType

logger = logging.getLogger(__name__)


class DedupAction(StrEnum):
    LINK_ONLY = "link_only"  # persist entry and link to near-duplicate without skipping
    SKIP_NEW = (
        "skip_new"  # skip new entry when a near-duplicate already exists (default)
    )


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
        retriever: MemoryRetriever,
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
        history: list[LLMMessage],
        turn_id: str | None = None,
    ) -> None:
        """Extract memories from history and persist with optional dedup."""
        try:
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
                logger.debug(
                    "MemoryIngestionService.on_session_stop: no entries extracted"
                )
                return
            for entry in entries:
                embedding = await self._embed_client.fetch(entry.content)
                if (
                    self._dedup_policy.action == DedupAction.SKIP_NEW
                    and embedding is not None
                    and self._has_near_duplicate(entry.memory_id, embedding)
                ):
                    logger.debug("memory.skip_dup memory_id=%r", entry.memory_id)
                    continue
                await self._jsonl.write(entry)
                self._store.upsert(entry, embedding=embedding)
                if embedding is not None:
                    self._link_duplicates(entry.memory_id, embedding)
                logger.info(
                    "memory.persist memory_id=%r type=%s importance=%.2f",
                    entry.memory_id,
                    entry.memory_type,
                    entry.importance,
                )
            logger.info("MemoryIngestionService.on_session_stop: persisted entries")
        except Exception as e:
            logger.warning("MemoryIngestionService.on_session_stop failed: %s", e)

    # ── Dedup helpers ─────────────────────────────────────────────────────────

    def _has_near_duplicate(self, memory_id: str, embedding: list[float]) -> bool:
        """Return True if a near-duplicate entry exists within dedup threshold."""
        neighbors = self._retriever._vec_search(embedding, None, limit=5)
        return any(
            -h.score < self._dedup_policy.threshold and h.entry.memory_id != memory_id
            for h in neighbors
        )

    def _link_duplicates(self, memory_id: str, embedding: list[float]) -> None:
        """Find near-duplicate entries and record links in memory_links."""
        neighbors = self._retriever._vec_search(embedding, None, limit=5)
        for hit in neighbors:
            if hit.entry.memory_id == memory_id:
                continue
            distance = -hit.score  # _vec_search returns -distance as score
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
                except Exception as e:
                    logger.warning("memory_links insert failed: %s", e)

    # ── Manual write ──────────────────────────────────────────────────────────

    def _build_manual_entry(
        self,
        *,
        memory_type: str,
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
        embedding = await self._embed_client.fetch(entry.content)
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
            memory_type="semantic",
            source_type=SourceType.RULE,
            content=content,
            session_id=session_id,
            importance=0.7,
        )
        await self._persist_entry(entry)

    async def write_episodic(self, session_id: int | None, content: str) -> None:
        """Persist an episodic memory entry manually."""
        entry = self._build_manual_entry(
            memory_type="episodic",
            source_type=SourceType.CONVERSATION,
            content=content,
            session_id=session_id,
            importance=0.5,
        )
        await self._persist_entry(entry)
