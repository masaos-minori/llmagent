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
from agent.memory.models import MemorySnippet
from agent.memory.retriever import HybridRetriever
from agent.memory.types import MemoryHit, MemoryQuery

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class InjectionPolicy:
    max_semantic: int = 5
    max_episodic: int = 3
    min_importance: float = 0.5
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
        branch: str = "",
    ) -> None:
        self._policy = policy
        self._retriever = retriever
        self._embed_client = embed_client
        self._project = project
        self._repo = repo
        self._branch = branch

    def on_session_start(self) -> list[MemorySnippet]:
        # Injects pinned and high-importance semantic memories only (importance >= min_importance).
        # Task-specific retrieval happens at on_user_prompt() — do not broaden this call.
        entries = self._retriever.top_semantic(
            limit=self._policy.max_semantic,
            min_importance=self._policy.min_importance,
            project=self._project,
            repo=self._repo,
            branch=self._branch,
        )
        if not entries:
            return []
        snippets = [
            MemorySnippet(
                text=f"{self._policy.format_prefix_semantic} {e.summary if e.summary else e.content[:100]}",
                source="semantic",
            )
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
    ) -> list[MemorySnippet]:
        # Primary task-specific restoration path. Performs query-based hybrid retrieval.
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
        snippets_s = self._build_snippets_from_hits(
            hits_s, self._policy.format_prefix_semantic, "semantic"
        )
        snippets_e = self._build_snippets_from_hits(
            hits_e, self._policy.format_prefix_episodic, "episodic"
        )
        snippets = snippets_s + snippets_e
        if snippets:
            logger.debug(
                "MemoryInjectionService.on_user_prompt: returning %d snippets",
                len(snippets),
            )
        return snippets

    def _build_snippets_from_hits(
        self, hits: list[MemoryHit], prefix: str, source: str
    ) -> list[MemorySnippet]:
        """Build MemorySnippet list from ranked hits."""
        snippets: list[MemorySnippet] = []
        for hit in hits:
            snippet_text = (
                hit.entry.summary if hit.entry.summary else hit.entry.content[:100]
            )
            snippets.append(
                MemorySnippet(
                    text=f"{prefix} {snippet_text}",
                    source=source,
                )
            )
        return snippets
