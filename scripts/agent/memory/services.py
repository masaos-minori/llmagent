"""agent/memory/services.py
MemoryServices — container for the three memory service instances.

Replaces MemoryLayer as the AppServices.memory type.
"""

from __future__ import annotations

from dataclasses import dataclass

from agent.memory.ingestion import MemoryIngestionService
from agent.memory.injection import MemoryInjectionService
from agent.memory.retriever import HybridRetriever
from agent.memory.store import MemoryStore


@dataclass
class MemoryServices:
    """Container for memory sub-services; injected into AppServices.memory."""

    injection: MemoryInjectionService
    ingestion: MemoryIngestionService
    store: MemoryStore
    retriever: HybridRetriever
