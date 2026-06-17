"""agent/memory — Persistent memory layer.

Sub-modules:
  embedding_client  : HTTP embedding client with retry/circuit-breaker
  enums             : Domain enums (MemoryType, DedupAction, etc.)
  exceptions        : Domain exceptions
  extract           : Rule-based extraction from conversation history
  ingestion         : MemoryIngestionService (extract, dedup, persist)
  injection         : MemoryInjectionService (inject snippets into context)
  jsonl_store       : Append-only JSONL persistence
  mapper            : SQLite row ↔ MemoryEntry conversion + shared utils
  models            : Frozen DTOs (HistoryMessage, MemorySnippet, etc.)
  retriever         : FTS5/KNN/Hybrid search
  services          : MemoryServices facade
  store             : CRUD layer for memories / memories_fts / memories_vec
  types             : Runtime types (MemoryEntry, MemoryQuery, EmbeddingResult)
"""

from agent.memory.embedding_client import EmbeddingClient, EmbeddingClientConfig
from agent.memory.enums import DedupAction, DedupPolicy, MemoryType
from agent.memory.exceptions import (
    EmbeddingProtocolError,
    EmbeddingTransportError,
    ExtractionError,
    InjectionValidationError,
    JsonlFormatError,
    MemoryConsistencyError,
    MemorySchemaError,
    UnknownMemoryTypeError,
)
from agent.memory.extract import ExtractionPolicy, extract_memories
from agent.memory.ingestion import MemoryIngestionService
from agent.memory.injection import InjectionPolicy, MemoryInjectionService
from agent.memory.jsonl_store import JsonlMemoryStore
from agent.memory.mapper import (
    _floats_to_blob,
    _now_iso,
    row_to_entry,
    _stamp_entry,
)
from agent.memory.models import ConsistencyReport, HistoryMessage, MemorySnippet
from agent.memory.retriever import FtsRetriever, HybridRetriever, VectorRetriever
from agent.memory.services import MemoryServices
from agent.memory.store import MemoryStore
from agent.memory.types import (
    EmbeddingErrorKind,
    EmbeddingResult,
    MemoryEntry,
    MemoryHit,
    MemoryQuery,
    SourceType,
)

__all__ = [
    # types
    "EmbeddingErrorKind",
    "EmbeddingResult",
    "MemoryEntry",
    "MemoryHit",
    "MemoryQuery",
    "SourceType",
    # enums
    "DedupAction",
    "DedupPolicy",
    "MemoryType",
    # exceptions
    "EmbeddingProtocolError",
    "EmbeddingTransportError",
    "ExtractionError",
    "InjectionValidationError",
    "JsonlFormatError",
    "MemoryConsistencyError",
    "MemorySchemaError",
    "UnknownMemoryTypeError",
    # models
    "ConsistencyReport",
    "HistoryMessage",
    "MemorySnippet",
    # services
    "MemoryIngestionService",
    "MemoryInjectionService",
    "MemoryServices",
    # store
    "MemoryStore",
    # jsonl_store
    "JsonlMemoryStore",
    # retriever
    "FtsRetriever",
    "HybridRetriever",
    "VectorRetriever",
    # mapper / utils
    "_floats_to_blob",
    "_now_iso",
    "row_to_entry",
    "_stamp_entry",
    # extract
    "ExtractionPolicy",
    "extract_memories",
    # embedding_client
    "EmbeddingClient",
    "EmbeddingClientConfig",
    # injection policy
    "InjectionPolicy",
]
