#!/usr/bin/env python3
"""agent/memory/layer.py
High-level orchestration layer for persistent semantic memory.

Lifecycle hooks:
  on_session_start()  — inject top semantic entries into context at session begin (sync)
  on_user_prompt()    — retrieve relevant memories for each user turn (async, Phase 2)
  on_session_stop()   — extract and persist new memories at session end (async, Phase 2)

Phase 2 additions:
  - embedding generation via embed_url (requires http client + memory_embed_enabled)
  - KNN search integrated into on_user_prompt via MemoryRetriever._vec_search
  - deduplication: embeddings close than dedup_threshold are linked in memory_links

All hooks are no-ops when use_memory_layer=False (ctx.services.memory is None).
No print() calls — all output goes through logger or caller's display layer.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import UTC, datetime

import httpx
from shared.types import LLMMessage

from agent.memory.extract import extract_memories
from agent.memory.jsonl_store import JsonlMemoryStore
from agent.memory.retriever import MemoryRetriever
from agent.memory.store import MemoryStore
from agent.memory.types import MemoryEntry, MemoryQuery
from db.helper import SQLiteHelper

logger = logging.getLogger(__name__)


async def _fetch_embedding(
    text: str,
    http: httpx.AsyncClient,
    embed_url: str,
) -> list[float] | None:
    """Call the embedding service; return None on any error."""
    try:
        resp = await http.post(embed_url, json={"content": f"query: {text}"})
        resp.raise_for_status()
        embedding = resp.json().get("embedding")
        if isinstance(embedding, list) and embedding:
            return [float(v) for v in embedding]
        logger.warning("embed response missing 'embedding' field")
        return None
    except Exception as e:
        logger.warning(f"MemoryLayer embedding fetch failed: {e}")
        return None


class MemoryLayer:
    """High-level memory orchestration: SessionStart / UserPromptSubmit / Stop.

    Injected into ServiceContainer.memory by AgentREPL._init_components()
    when use_memory_layer=True.
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
        self._store = store
        self._retriever = retriever
        self._jsonl = jsonl
        self._max_inject_semantic = max_inject_semantic
        self._max_inject_episodic = max_inject_episodic
        self._min_importance = min_importance
        self._project = project
        self._repo = repo
        self._branch = branch
        self._http = http
        self._embed_url = embed_url
        self._embed_enabled = embed_enabled
        self._dedup_threshold = dedup_threshold
        self._embed_timeout = embed_timeout
        self._max_content_chars = max_content_chars

    async def _get_embedding(self, text: str) -> list[float] | None:
        """Generate embedding when embed is enabled and http client available.

        Caps each call to _embed_timeout seconds via asyncio.wait_for.
        """
        if not self._embed_enabled or self._http is None or not self._embed_url:
            return None
        try:
            return await asyncio.wait_for(
                _fetch_embedding(text, self._http, self._embed_url),
                timeout=self._embed_timeout,
            )
        except TimeoutError:
            logger.warning(
                f"MemoryLayer._get_embedding timed out after {self._embed_timeout}s",
            )
            return None

    # ── SessionStart ──────────────────────────────────────────────────────────

    def on_session_start(self, session_id: int | None) -> list[str]:
        """Return text snippets to inject at session start.

        Fetches top semantic entries (by importance + pin) for injection into
        the system prompt.  Returns [] on any DB error.
        Stays synchronous — no embedding needed for session-start injection.
        """
        try:
            entries = self._retriever.top_semantic(
                limit=self._max_inject_semantic,
                min_importance=self._min_importance,
                project=self._project,
                repo=self._repo,
            )
            if not entries:
                return []
            snippets = [f"[Memory] {e.summary or e.content[:100]}" for e in entries]
            logger.info(
                f"MemoryLayer.on_session_start: injecting {len(snippets)} semantic entries",
            )
            return snippets
        except Exception as e:
            logger.warning(f"MemoryLayer.on_session_start failed: {e}")
            return []

    # ── UserPromptSubmit ─────────────────────────────────────────────────────

    async def on_user_prompt(
        self,
        query: str,
        session_id: int | None,
    ) -> list[str]:
        """Return text snippets relevant to the user's query.

        Phase 2: generates embedding for query and merges FTS5 + KNN via RRF.
        Returns [] on any DB error or when no results are found.
        """
        if not query.strip():
            return []
        try:
            embedding = await self._get_embedding(query)
            hits_s = self._retriever.search(
                MemoryQuery(
                    query=query,
                    session_id=session_id,
                    memory_type="semantic",
                    limit=self._max_inject_semantic,
                ),
                embedding=embedding,
                project=self._project,
                repo=self._repo,
            )
            hits_e = self._retriever.search(
                MemoryQuery(
                    query=query,
                    session_id=session_id,
                    memory_type="episodic",
                    limit=self._max_inject_episodic,
                ),
                embedding=embedding,
                project=self._project,
                repo=self._repo,
            )
            snippets = []
            for hit in hits_s:
                snippets.append(
                    f"[Semantic memory] {hit.entry.summary or hit.entry.content[:100]}",
                )
            for hit in hits_e:
                snippets.append(
                    f"[Episodic memory] {hit.entry.summary or hit.entry.content[:100]}",
                )
            if snippets:
                logger.debug(
                    f"MemoryLayer.on_user_prompt: returning {len(snippets)} snippets",
                )
            return snippets
        except Exception as e:
            logger.warning(f"MemoryLayer.on_user_prompt failed: {e}")
            return []

    # ── Stop ─────────────────────────────────────────────────────────────────

    async def on_session_stop(
        self,
        session_id: int | None,
        history: list[LLMMessage],
        turn_id: str | None = None,
    ) -> None:
        """Extract memories from history and persist to JSONL + SQLite.

        Phase 2: generates embeddings for each entry and runs dedup linking.
        Called with await in AgentREPL.run() finally block.
        """
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
                logger.debug("MemoryLayer.on_session_stop: no entries extracted")
                return
            for entry in entries:
                embedding = await self._get_embedding(entry.content)
                self._jsonl.append(entry)
                self._store.upsert(entry, embedding=embedding)
                if embedding is not None:
                    self._link_duplicates(entry.memory_id, embedding)
                logger.info(
                    f"memory.persist memory_id={entry.memory_id!r}"
                    f" type={entry.memory_type} importance={entry.importance:.2f}",
                )
            logger.info(
                f"MemoryLayer.on_session_stop: persisted {len(entries)} entries",
            )
        except Exception as e:
            logger.warning(f"MemoryLayer.on_session_stop failed: {e}")

    def _link_duplicates(self, memory_id: str, embedding: list[float]) -> None:
        """Find near-duplicate entries via KNN and record links in memory_links."""
        neighbors = self._retriever._vec_search(embedding, None, limit=5)
        for hit in neighbors:
            if hit.entry.memory_id == memory_id:
                continue
            # score from _vec_search is -distance; closer = higher score
            distance = -hit.score
            if distance < self._dedup_threshold:
                try:
                    with SQLiteHelper("session").open(write_mode=True) as db:
                        db.execute(
                            "INSERT OR IGNORE INTO memory_links(src_id, dst_id)"
                            " VALUES (?,?)",
                            (memory_id, hit.entry.memory_id),
                        )
                        db.commit()
                    logger.debug(
                        f"memory_links: {memory_id!r} → {hit.entry.memory_id!r}"
                        f" distance={distance:.3f}",
                    )
                except Exception as e:
                    logger.warning(f"memory_links insert failed: {e}")

    # ── Manual write operations ───────────────────────────────────────────────

    async def write_semantic(self, session_id: int | None, content: str) -> None:
        """Manually persist a semantic memory entry."""
        now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        entry = MemoryEntry(
            memory_id=str(uuid.uuid4()),
            memory_type="semantic",
            source_type="rule",
            session_id=session_id,
            turn_id=None,
            project=self._project,
            repo=self._repo,
            branch=self._branch,
            content=content,
            summary=content[:120],
            tags=["manual"],
            importance=0.7,
            pinned=False,
            created_at=now,
            updated_at=now,
        )
        embedding = await self._get_embedding(content)
        self._jsonl.append(entry)
        self._store.upsert(entry, embedding=embedding)
        logger.info(
            f"memory.write memory_id={entry.memory_id!r} type=semantic"
            f" importance={entry.importance:.2f}",
        )

    async def write_episodic(self, session_id: int | None, content: str) -> None:
        """Manually persist an episodic memory entry."""
        now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        entry = MemoryEntry(
            memory_id=str(uuid.uuid4()),
            memory_type="episodic",
            source_type="conversation",
            session_id=session_id,
            turn_id=None,
            project=self._project,
            repo=self._repo,
            branch=self._branch,
            content=content,
            summary=content[:120],
            tags=["manual"],
            importance=0.5,
            pinned=False,
            created_at=now,
            updated_at=now,
        )
        embedding = await self._get_embedding(content)
        self._jsonl.append(entry)
        self._store.upsert(entry, embedding=embedding)
        logger.info(
            f"memory.write memory_id={entry.memory_id!r} type=episodic"
            f" importance={entry.importance:.2f}",
        )

    # ── Housekeeping ──────────────────────────────────────────────────────────

    def clear(self, session_id: int | None = None) -> None:
        """Remove entries for session_id, or all entries when session_id is None."""
        cleared: int
        if session_id is not None:
            cleared = self._store.clear_by_session(session_id)
        else:
            # Full clear: delete all rows via SQL directly
            try:
                with SQLiteHelper("session").open(write_mode=True) as db:
                    cur = db.execute("DELETE FROM memories")
                    db.execute("DELETE FROM memories_fts")
                    try:
                        db.execute("DELETE FROM memories_vec")
                    except Exception as e:
                        logger.warning(f"memories_vec DELETE skipped: {e}")
                    cleared = cur.rowcount
                    db.commit()
            except Exception as e:
                logger.warning(f"MemoryLayer.clear failed: {e}")
                return
        logger.info(
            f"MemoryLayer.clear: removed {cleared} entries"
            f" (session_id={session_id if session_id is not None else 'all'})",
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
            logger.warning(f"MemoryLayer.stat_entries failed: {e}")
            return 0

    @property
    def stat_by_type(self) -> dict[str, int]:
        """Entry counts per memory_type; {} on DB error."""
        try:
            return self._store.count_by_type()
        except Exception as e:
            logger.warning(f"MemoryLayer.stat_by_type failed: {e}")
            return {}

    @property
    def stat_vec_entries(self) -> int:
        """Total entry count in memories_vec; 0 if embed disabled or error."""
        return self._store.count_vec()
