---
title: "Memory Layer Reference — Generated Class/Function Index"
area: agent
tags:
  - agent
  - memory
  - api-reference
  - generated
related:
  - 05_agent_12_01_memory-overview-and-modes.md
  - 05_agent_12_02_memory-gate-data-model-search.md
  - 05_agent_12_03_memory-module-ref-core-and-store.md
  - 05_agent_12_04_memory-module-ref-retrieval-and-injection.md
  - 05_agent_12_05_memory-module-ref-extraction-and-facade.md
  - 05_agent_12_06_memory-module-ref-ops-and-scoring.md
---

# Memory Layer Reference — Generated Class/Function Index

## Purpose

Generated index of every public top-level class/function under
`scripts/agent/memory/*.py` (`tools/generate_reference_table.py --type memory`).
Companion to the six hand-curated Memory Layer chapter documents
(`05_agent_12_01` through `05_agent_12_06`); kept as a separate generated file so none
of those hand-curated documents needs to embed a mechanically-derived class/function
listing. Do not hand-edit between the guard comments — run the generator.

## Related Documents

- [05_agent_12_01_memory-overview-and-modes.md](05_agent_12_01_memory-overview-and-modes.md)
- [05_agent_12_02_memory-gate-data-model-search.md](05_agent_12_02_memory-gate-data-model-search.md)
- [05_agent_12_03_memory-module-ref-core-and-store.md](05_agent_12_03_memory-module-ref-core-and-store.md)
- [05_agent_12_04_memory-module-ref-retrieval-and-injection.md](05_agent_12_04_memory-module-ref-retrieval-and-injection.md)
- [05_agent_12_05_memory-module-ref-extraction-and-facade.md](05_agent_12_05_memory-module-ref-extraction-and-facade.md)
- [05_agent_12_06_memory-module-ref-ops-and-scoring.md](05_agent_12_06_memory-module-ref-ops-and-scoring.md)
- [governance_01_documentation-policy.md](../00_governance/governance_01_documentation-policy.md) — ADR-015 Reference Document Class Disposition

## Keywords

agent, memory, api-reference, generated

## Module Class/Function Reference (auto-generated)

<!-- AUTO-GENERATED: gen_memory_reference.py class-function-reference -->
Generated from `scripts/agent/memory/*.py` top-level public classes and functions. Do not hand-edit between the guard comments; run `python tools/generate_reference_table.py --type memory` to refresh.

| File | Class/Function | Signature | Summary |
|---|---|---|---|
| `scripts/agent/memory/count_ops.py` | `count_by_type` | `def count_by_type() -> dict[str, int]` | Return {memory_type: count} for all rows in memories. Diagnostic use only. |
|  | `count_by_source_type` | `def count_by_source_type() -> dict[str, int]` | Return {source_type: count} for all rows in memories. Diagnostic use only. |
|  | `count_vec` | `def count_vec() -> int` | Return total entry count in memories_vec. Raises sqlite3.OperationalError if unavailable. |
|  | `count_entries` | `def count_entries() -> int` | Return total entry count across all types. Raises sqlite3.OperationalError on DB error. |
|  | `count_prunable` | `def count_prunable(days) -> int` | Return count of entries older than `days` days. Raises sqlite3.OperationalError on DB error. |
| `scripts/agent/memory/embedding_client.py` | `EmbeddingClientConfig` | `class EmbeddingClientConfig` | Configuration for the embedding client connection. |
|  | `EmbeddingClientStatus` | `class EmbeddingClientStatus` | Runtime health status of the embedding client. |
|  | `EmbeddingClient` | `class EmbeddingClient` | Async HTTP client for embedding generation. |
| `scripts/agent/memory/enums.py` | `MemoryType` | `class MemoryType` | Types of persistent memory supported by the agent. |
|  | `RetrievalMode` | `class RetrievalMode` | Modes for retrieving memory entries. |
|  | `ExtractionDecision` | `class ExtractionDecision` | Decisions made during memory extraction. |
|  | `DedupAction` | `class DedupAction` | Actions taken when a near-duplicate is detected. |
|  | `DedupPolicy` | `class DedupPolicy` | Configuration for deduplication behavior. |
| `scripts/agent/memory/exceptions.py` | `MemorySchemaError` | `class MemorySchemaError` | Raised when a memory row or field fails schema validation. |
|  | `UnknownMemoryTypeError` | `class UnknownMemoryTypeError` | Raised when an unrecognized memory_type value is encountered. |
|  | `MemoryStorageError` | `class MemoryStorageError` | Raised when a DB write operation fails. |
|  | `JsonlFormatError` | `class JsonlFormatError` | Raised when a JSONL line cannot be parsed or fails schema validation. |
|  | `MemoryConsistencyError` | `class MemoryConsistencyError` | Raised when memories / memories_fts / memories_vec counts are inconsistent. |
|  | `EmbeddingTransportError` | `class EmbeddingTransportError` | Raised when an HTTP-level error prevents embedding retrieval. |
|  | `EmbeddingProtocolError` | `class EmbeddingProtocolError` | Raised when the embedding service response violates the expected schema. |
|  | `ExtractionError` | `class ExtractionError` | Raised when memory extraction from conversation history fails. |
|  | `InjectionValidationError` | `class InjectionValidationError` | Raised when injection inputs fail validation (e.g. empty query). |
| `scripts/agent/memory/extract.py` | `ExtractionPolicy` | `class ExtractionPolicy` | Configurable thresholds for memory extraction. |
|  | `extract_memories` | `def extract_memories(history, session_id, turn_id, project, repo, branch, max_content_chars, policy) -> list[MemoryEntry]` | Extract MemoryEntry candidates from a conversation history list. |
| `scripts/agent/memory/fts_query.py` | `build_fts_query` | `def build_fts_query(text) -> str` | Build FTS5 MATCH query with token quoting to escape reserved terms. |
| `scripts/agent/memory/import_ops.py` | `import_from_jsonl` | `def import_from_jsonl(jsonl_store, *, dry_run, embed_dim) -> tuple[int, int]` | Import entries from a JSONL archive into SQLite memories/FTS/vec tables. |
| `scripts/agent/memory/ingestion.py` | `MemoryIngestionService` | `class MemoryIngestionService` | Extracts, deduplicates, and persists memory entries from session history. |
| `scripts/agent/memory/injection.py` | `InjectionPolicy` | `class InjectionPolicy` | Controls how many semantic/episodic memories are injected per turn. |
|  | `MemoryInjectionService` | `class MemoryInjectionService` | Injects relevant memory snippets into the LLM context per lifecycle hook. |
| `scripts/agent/memory/jsonl_store.py` | `JsonlMemoryStore` | `class JsonlMemoryStore` | Append-only JSONL store.  Thread-unsafe — use from a single asyncio event loop. |
| `scripts/agent/memory/mapper.py` | `row_to_entry` | `def row_to_entry(row) -> MemoryEntry` | Convert a sqlite3.Row or dict to MemoryEntry. |
| `scripts/agent/memory/models.py` | `HistoryMessage` | `class HistoryMessage` | Memory-local representation of one conversation message. |
|  | `JsonlRecord` | `class JsonlRecord` | One deserialized record from the JSONL memory store. |
|  | `ConsistencyReport` | `class ConsistencyReport` | Row counts across memories / memories_fts / memories_vec tables. |
|  | `MemorySnippet` | `class MemorySnippet` | One memory snippet ready for LLM context injection. |
| `scripts/agent/memory/pin_ops.py` | `pin` | `def pin(memory_id, conn) -> bool` | Set pinned=1 for memory_id; return True when found. |
|  | `unpin` | `def unpin(memory_id, conn) -> bool` | Set pinned=0 for memory_id; return True when found. |
| `scripts/agent/memory/rebuild_ops.py` | `rebuild_fts` | `def rebuild_fts() -> int` | Rebuild memories_fts from the memories table. Returns number of rows inserted. |
|  | `rebuild_vec` | `def rebuild_vec() -> int` | Rebuild memories_vec from the memories table. Returns number of rows inserted. |
| `scripts/agent/memory/retriever.py` | `FtsRetriever` | `class FtsRetriever` | FTS5 BM25 search with importance / pin / recency rescoring. |
|  | `VectorRetriever` | `class VectorRetriever` | KNN search on memories_vec using sqlite-vec extension. |
|  | `HybridRetriever` | `class HybridRetriever` | FTS5 + optional KNN hybrid search with RRF merge. |
| `scripts/agent/memory/rrf.py` | `rrf_merge` | `def rrf_merge(hit_lists, k) -> list[MemoryHit]` | Reciprocal Rank Fusion: merge multiple ranked hit lists by rank position. |
| `scripts/agent/memory/scoring.py` | `recency_boost` | `def recency_boost(created_at, recency_days) -> float` | Return 0.0–_RECENCY_MAX_BOOST based on age in days (newer = higher). |
|  | `context_boost` | `def context_boost(entry, project, repo, branch) -> float` | Return a context match boost based on branch, project, or repo match. |
|  | `score` | `def score(bm25_rank, entry, project, repo, recency_days, branch) -> float` | Combined score; higher is better. |
| `scripts/agent/memory/services.py` | `MemoryServices` | `class MemoryServices` | Facade over memory sub-services; injected into AppServices.memory. |
| `scripts/agent/memory/snippet_filter.py` | `FilteredSnippet` | `class FilteredSnippet` | Result of PII filtering on a snippet. |
|  | `TruncatedSnippet` | `class TruncatedSnippet` | Result of length enforcement on a snippet. |
|  | `filter_pii` | `def filter_pii(text) -> FilteredSnippet` | Redact PII from *text* using regex-based patterns. |
|  | `truncate_snippet` | `def truncate_snippet(text, max_length) -> TruncatedSnippet` | Truncate *text* to *max_length* characters with an indicator suffix. |
| `scripts/agent/memory/store.py` | `MemoryStore` | `class MemoryStore` | CRUD operations for memories, memories_fts, and memories_vec tables. |
| `scripts/agent/memory/types.py` | `SourceType` | `class SourceType` | Taxonomy of memory source types. |
|  | `EmbeddingErrorKind` | `class EmbeddingErrorKind` | Enumeration of embedding failure reasons. |
|  | `MemoryEntry` | `class MemoryEntry` | One persistent memory unit stored in JSONL and indexed in SQLite. |
|  | `MemoryQuery` | `class MemoryQuery` | Search parameters for memory retrieval. |
|  | `MemoryHit` | `class MemoryHit` | One ranked result from memory retrieval. |
|  | `EmbeddingResult` | `class EmbeddingResult` | Result of an embedding generation attempt. |
| `scripts/agent/memory/write_ops.py` | `add` | `def add(entry, embedding, embed_dim) -> None` | Insert a new MemoryEntry; sets created_at/updated_at if empty. |
|  | `upsert` | `def upsert(entry, embedding, embed_dim) -> None` | Insert or replace a MemoryEntry; updates updated_at. |
|  | `delete` | `def delete(memory_id) -> bool` | Delete one entry by memory_id; return True when found and deleted. |
|  | `clear_by_session` | `def clear_by_session(session_id) -> int` | Delete all entries for session_id; return count deleted. |
<!-- END AUTO-GENERATED -->
