---
title: "Memory Layer - Module Reference: Core and Store"
category: agent
tags:
  - agent
  - memory
  - module-reference
  - types
  - store
related:
  - 05_agent_00_document-guide.md
  - 05_agent_12_memory-overview-and-modes.md
  - 05_agent_12_memory-gate-data-model-search.md
  - 05_agent_12_memory-module-ref-retrieval-and-injection.md
  - 05_agent_12_memory-module-ref-extraction-and-facade.md
  - 05_agent_12_memory-module-ref-ops-and-scoring.md
source:
  - 05_agent_12_memory.md
---

# Memory Layer — Module Reference

- Operations and observability → [05_agent_10_operations-and-observability-startup-and-health.md](05_agent_10_operations-and-observability-startup-and-health.md)
- Configuration → [05_agent_08_configuration-tools-memory.md](05_agent_08_configuration-tools-memory.md)

### 1. `__init__.py` — Public API barrel

Re-exports all public symbols from sub-modules. Key categories:

- **Runtime types:** `MemoryEntry`, `MemoryQuery`, `MemoryHit`, `EmbeddingResult`, `EmbeddingErrorKind`, `SourceType`
- **Enums:** `DedupAction`, `DedupPolicy`, `MemoryType`
- **Exceptions:** `EmbeddingProtocolError`, `EmbeddingTransportError`, `ExtractionError`, `InjectionValidationError`, `JsonlFormatError`, `MemoryConsistencyError`, `MemorySchemaError`, `UnknownMemoryTypeError`
- **Models:** `ConsistencyReport`, `HistoryMessage`, `MemorySnippet`
- **Services:** `MemoryIngestionService`, `MemoryInjectionService`, `MemoryServices`
- **Store:** `MemoryStore`
- **JSONL:** `JsonlMemoryStore`
- **Retriever:** `FtsRetriever`, `HybridRetriever`, `VectorRetriever`
- **Mapper:** internal conversion functions for float-to-BLOB and timestamp stamping
- **Extract:** `ExtractionPolicy`, `extract_memories`
- **Embedding:** `EmbeddingClient`, `EmbeddingClientConfig`
- **Injection:** `InjectionPolicy`

Notable: internal mapper utilities are exported in `__all__` for use by other modules.

### 2. `types.py` — Core runtime types

| Type | Description | Key fields |
|---|---|---|
| `MemoryEntry` | Persisted memory entry | memory_id, memory_type (MemoryType: SEMANTIC="semantic" / EPISODIC="episodic"), source_type (SourceType: RULE="rule" / CONVERSATION="conversation" / DECISION="decision" / FAILURE="failure"), session_id (int \| None, default: None), turn_id (str \| None, default: None), content, summary, tags (list[str], default: []), importance (float, default: 0.5), pinned (bool, default: False), created_at (str, auto-filled by write_ops.add()), updated_at (str, auto-filled by write_ops.add()), project (str, default: ""), repo (str, default: ""), branch (str, default: "") |
| `MemoryQuery` | Search input | query (str), memory_type (str \| None, default: None), limit (int, default: 10), session_id (int \| None, default: None). `__post_init__` validates that `query` is not empty and `limit > 0`. |
| `MemoryHit` | Ranked search result | entry (MemoryEntry), score (float) |
| `EmbeddingResult` | Embedding fetch outcome | success (bool), embedding (list[float] \| None), error_kind (EmbeddingErrorKind \| None) |
| `EmbeddingErrorKind` | Error classification | `DISABLED`, `TIMEOUT`, `HTTP_ERROR`, `CIRCUIT_OPEN`, `DIMENSION_MISMATCH`, `INVALID_RESPONSE`, `UNKNOWN_ERROR` (StrEnum; values are lowercase: `"disabled"`, `"timeout"`, etc.) |
| `SourceType` | Entry origin | `"rule"`, `"conversation"`, `"decision"`, `"failure"` (StrEnum; member names uppercase: RULE, CONVERSATION, DECISION, FAILURE) |

### 3. `enums.py` — Domain enums

| Enum / Dict | Values | Description |
|---|---|---|
| `MemoryType` | `"semantic"` (member: SEMANTIC), `"episodic"` (member: EPISODIC) | Memory classification |
| `DedupAction` | `"skip_new"` (member: SKIP_NEW) | Dedup behavior when near-duplicate found |
| `DedupPolicy` | action (DedupAction.SKIP_NEW) + threshold (0.3) | Dedup configuration dataclass |
| `RetrievalMode` | `"fts"`, `"knn"`, `"hybrid"` (members: FTS, KNN, HYBRID) | Search mode selection |
| `ExtractionDecision` | `"accept"`, `"reject_too_short"`, `"reject_no_keywords"`, `"reject_dedup"` (members: ACCEPT, REJECT_TOO_SHORT, REJECT_NO_KEYWORDS, REJECT_DEDUP) | Extraction outcome |
| `DEDUP_THRESHOLDS` | `RULE: 0.98`, `DECISION: 0.98`, `FAILURE: 0.90`, `CONVERSATION: 0.85` | Dedup similarity thresholds per source type |
| `RETENTION_DAYS` | `FAILURE: 180`, `CONVERSATION: 90`, `RULE/DECISION: None` | Per-source-type retention policy |

### 4. `exceptions.py` — Exception hierarchy

| Exception | Raised when |
|---|---|
| `MemorySchemaError` | Invalid data schema (e.g. invalid created_at in retriever) |
| `MemoryConsistencyError` | FTS count / memories count mismatch |
| `ExtractionError` | Memory extraction fails |
| `InjectionValidationError` | Empty query passed to on_user_prompt |
| `EmbeddingProtocolError` | Embedding API returned unexpected response |
| `EmbeddingTransportError` | HTTP transport failure to embedding API |
| `JsonlFormatError` | Malformed JSONL line during read |
| `UnknownMemoryTypeError` | Unrecognized memory_type string |
| `MemoryStorageError` | DB write operation fails |

### 5. `models.py` — Frozen DTOs

| Class | Fields | Purpose |
|---|---|---|
| `HistoryMessage` | role (str), content (str) | Single message in conversation history |
| `JsonlRecord` | Frozen DTO. Fields: memory_id (str), memory_type (MemoryType), source_type (SourceType), session_id (int \| None, default: None), turn_id (str \| None, default: None), project (str, default: ""), repo (str, default: ""), branch (str, default: ""), content (str), summary (str), tags (list[str], default: []), importance (float, default: 0.5), pinned (bool, default: False), created_at (str, default: ""), updated_at (str, default: "") | Deserialized record from the JSONL memory store |
| `MemorySnippet` | text (str), source (str), score (float) | Injected context snippet with source tag and retrieval score |
| `ConsistencyReport` | memories (int), fts (int), vec (int) | Row count comparison for consistency check |

### 6. `store.py` — Read-only CRUD layer

Write operations (`add`, `upsert`, `delete`, `clear_by_session`) are in `write_ops.py`.

Class `MemoryStore(embed_dim=None)`: when `embed_dim` is None, defaults to 384.

| Method | Returns | Description |
|---|---|---|
| `search_by_type(memory_type, limit=10, min_importance=0.0)` | `list[MemoryEntry]` | Filter by type, ordered by pinned DESC, importance DESC, created_at DESC |
| `list_entries(source_type=None, branch=None, limit=50)` | `list[MemoryEntry]` | Return entries filtered by optional source_type and/or branch |
| `count_vec()` | `int` | Row count in memories_vec |
| `check_consistency()` | `ConsistencyReport` | Compare memories / memories_fts / memories_vec counts |
| `get_by_id(memory_id)` | `MemoryEntry \| None` | Lookup by primary key |

**Failure modes:**
- `sqlite3.OperationalError` — DB locked, missing vec table, etc.
- `MemoryConsistencyError` — FTS count determination fails

## Related Documents

- `05_agent_00_document-guide.md`
- `05_agent_12_memory-overview-and-modes.md`
- `05_agent_12_memory-gate-data-model-search.md`
- `05_agent_12_memory-module-ref-retrieval-and-injection.md`
- `05_agent_12_memory-module-ref-extraction-and-facade.md`
- `05_agent_12_memory-module-ref-ops-and-scoring.md`

## Keywords

__init__.py
types.py
enums.py
exceptions.py
models.py
store.py
