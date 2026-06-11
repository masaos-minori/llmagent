"""agent/memory/services.py
MemoryServices — facade over the three memory service instances.

Replaces MemoryLayer as the AppServices.memory type.
"""

from __future__ import annotations

from agent.memory.ingestion import MemoryIngestionService
from agent.memory.injection import MemoryInjectionService
from agent.memory.models import HistoryMessage
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
    ) -> None:
        self.injection = injection
        self.ingestion = ingestion
        self.store = store
        self.retriever = retriever

    def on_session_start(self, session_id: int | None) -> list[str]:
        """Return top semantic snippets for injection at session start."""
        return (
            self.injection.on_session_start()
        )  # session_id not used by injection layer

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
    ) -> list[str]:
        """Return relevant snippets for the current user query."""
        return await self.injection.on_user_prompt(query, session_id)
