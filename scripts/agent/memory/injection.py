"""agent/memory/injection.py
MemoryInjectionService — on_session_start / on_user_prompt lifecycle hooks.

Reads from the memory store and injects relevant snippets into the LLM context.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from agent.memory.embedding_client import EmbeddingClient
from agent.memory.enums import MemoryType
from agent.memory.exceptions import InjectionValidationError
from agent.memory.retriever import HybridRetriever
from agent.memory.types import MemoryQuery

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class InjectionPolicy:
    max_semantic: int = 5
    max_episodic: int = 3
    min_importance: float = 0.3
    format_prefix_semantic: str = "[Semantic memory]"
    format_prefix_episodic: str = "[Episodic memory]"


class MemoryInjectionService:
    """Injects relevant memory snippets into the LLM context per lifecycle hook."""

    def __init__(
        self,
        policy: InjectionPolicy,
        retriever: HybridRetriever,
        embed_client: EmbeddingClient,
        project: str = "",
        repo: str = "",
    ) -> None:
        self._policy = policy
        self._retriever = retriever
        self._embed_client = embed_client
        self._project = project
        self._repo = repo

    def on_session_start(self) -> list[str]:
        """Return top semantic snippets for injection at session start (sync)."""
        entries = self._retriever.top_semantic(
            limit=self._policy.max_semantic,
            min_importance=self._policy.min_importance,
            project=self._project,
            repo=self._repo,
        )
        if not entries:
            return []
        snippets = [
            f"{self._policy.format_prefix_semantic} "
            f"{e.summary if e.summary else e.content[:100]}"
            for e in entries
        ]
        logger.info(
            "MemoryInjectionService.on_session_start: injecting %d entries",
            len(snippets),
        )
        return snippets

    async def on_user_prompt(
        self,
        query: str,
        session_id: int | None,
    ) -> list[str]:
        """Return relevant snippets for the current user query (async)."""
        if not query.strip():
            raise InjectionValidationError("on_user_prompt query must not be empty")
        embed_result = await self._embed_client.fetch(query)
        embedding = embed_result.embedding if embed_result.success else None
        hits_s = self._retriever.search(
            MemoryQuery(
                query=query,
                memory_type=MemoryType.SEMANTIC,
                limit=self._policy.max_semantic,
            ),
            embedding=embedding,
            project=self._project,
            repo=self._repo,
        )
        hits_e = self._retriever.search(
            MemoryQuery(
                query=query,
                memory_type=MemoryType.EPISODIC,
                limit=self._policy.max_episodic,
            ),
            embedding=embedding,
            project=self._project,
            repo=self._repo,
        )
        snippets: list[str] = []
        for hit in hits_s:
            snippet = (
                hit.entry.summary if hit.entry.summary else hit.entry.content[:100]
            )
            snippets.append(f"{self._policy.format_prefix_semantic} {snippet}")
        for hit in hits_e:
            snippet = (
                hit.entry.summary if hit.entry.summary else hit.entry.content[:100]
            )
            snippets.append(f"{self._policy.format_prefix_episodic} {snippet}")
        if snippets:
            logger.debug(
                "MemoryInjectionService.on_user_prompt: returning %d snippets",
                len(snippets),
            )
        return snippets
