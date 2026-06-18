# Memory Layer — Module Reference

- Operations and observability → [05_agent_10_operations-and-observability.md](05_agent_10_operations-and-observability.md)
- Configuration → [05_agent_08_configuration.md](05_agent_08_configuration.md)

## Purpose

API reference for all 14 modules under `scripts/agent/memory/`. A developer should
understand each module's responsibility, public API surface, and disabled behavior
without reading source code.

---

## Overview

| Module | Responsibility |
|---|---|
| `__init__.py` | Public API barrel — re-exports all public symbols |
| `types.py` | Core runtime types (MemoryEntry, MemoryQuery, MemoryHit, EmbeddingResult) |
| `enums.py` | Domain enums (MemoryType, DedupAction, DedupPolicy) |
| `exceptions.py` | Exception hierarchy |
| `models.py` | Frozen DTOs (HistoryMessage, MemorySnippet, ConsistencyReport) |
| `store.py` | CRUD for memories / memories_fts / memories_vec tables |
| `retriever.py` | FTS5 / KNN / Hybrid search (FtsRetriever, VectorRetriever, HybridRetriever) |
| `injection.py` | MemoryInjectionService — lifecycle hooks for snippet injection |
| `ingestion.py` | MemoryIngestionService — extract, dedup, persist |
| `extract.py` | Rule-based extraction from conversation history |
| `jsonl_store.py` | Append-only JSONL source of truth |
| `embedding_client.py` | HTTP embedding client with retry and circuit breaker |
| `services.py` | MemoryServices facade over injection, ingestion, store, retriever |
| `mapper.py` | SQLite row conversion, embedding blob serialisation |

---

## Module Reference

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
- **Mapper:** `_floats_to_blob`, `_now_iso`, `row_to_entry`, `_stamp_entry`
- **Extract:** `ExtractionPolicy`, `extract_memories`
- **Embedding:** `EmbeddingClient`, `EmbeddingClientConfig`
- **Injection:** `InjectionPolicy`

Notable: internal mapper utils (`_floats_to_blob`, `_stamp_entry`) are exported in `__all__`.

### 2. `types.py` — Core runtime types

| Type | Description | Key fields |
|---|---|---|
| `MemoryEntry` | Persisted memory entry | memory_id, memory_type, source_type, session_id, content, summary, tags, importance, pinned, created_at, updated_at, project / repo / branch |
| `MemoryQuery` | Search input | query (str), memory_type (str \| None), limit (int) |
| `MemoryHit` | Ranked search result | entry (MemoryEntry), score (float) |
| `EmbeddingResult` | Embedding fetch outcome | success (bool), embedding (list[float] \| None), error_kind (EmbeddingErrorKind \| None) |
| `EmbeddingErrorKind` | Error classification | DISABLED, TIMEOUT, HTTP_ERROR, CIRCUIT_OPEN, INVALID_RESPONSE, UNKNOWN_ERROR |
| `SourceType` | Entry origin | RULE, CONVERSATION, FAILURE, MANUAL |

### 3. `enums.py` — Domain enums

| Enum | Values | Description |
|---|---|---|
| `MemoryType` | `semantic`, `episodic` | Memory classification |
| `DedupAction` | `SKIP_NEW`, `ALWAYS_WRITE` | Dedup behavior when near-duplicate found |
| `DedupPolicy` | action + threshold | Dedup configuration dataclass |

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

### 5. `models.py` — Frozen DTOs

| Class | Fields | Purpose |
|---|---|---|
| `HistoryMessage` | role (str), content (str) | Single message in conversation history |
| `MemorySnippet` | text (str), source (str) | Injected context snippet with source tag |
| `ConsistencyReport` | memories (int), fts (int), vec (int) | Row count comparison for consistency check |

### 6. `store.py` — CRUD layer

Class `MemoryStore(embed_dim=None)`:

| Method | Returns | Description |
|---|---|---|
| `add(entry, embedding=None)` | `None` | Insert + FTS sync; BEGIN IMMEDIATE for atomicity |
| `upsert(entry, embedding=None)` | `None` | Insert-or-replace + FTS sync |
| `delete(memory_id)` | `bool` | Remove entry by ID |
| `clear_by_session(session_id)` | `int` | Bulk delete for one session |
| `search_by_type(memory_type, limit=10, min_importance=0.0)` | `list[MemoryEntry]` | Filter by type, sorted by importance + pinned |
| `count_by_type()` | `dict[str, int]` | Entry count per memory_type |
| `count_vec()` | `int` | Row count in memories_vec |
| `check_consistency()` | `ConsistencyReport` | Compare memories / memories_fts / memories_vec counts |
| `pin(memory_id)` | `bool` | Set pinned=1 |
| `unpin(memory_id)` | `bool` | Set pinned=0 |
| `get_by_id(memory_id)` | `MemoryEntry \| None` | Lookup by primary key |
| `count_entries()` | `int` | Total entries |
| `count_prunable(days)` | `int` | Entries older than `days` days |

**Failure modes:**
- `sqlite3.OperationalError` — DB locked, missing vec table, etc.
- `MemoryConsistencyError` — FTS count determination fails

### 7. `retriever.py` — Search (FTS5 + KNN + Hybrid)

| Class | Role |
|---|---|
| `FtsRetriever` | FTS5 BM25 search with importance / pin / recency rescoring |
| `VectorRetriever` | KNN search via sqlite-vec |
| `HybridRetriever` | Primary external interface — composes both with RRF merge |

**`HybridRetriever` methods:**

| Method | Returns | Description |
|---|---|---|
| `search(query, embedding=None, project="", repo="")` | `list[MemoryHit]` | FTS-only when no embedding; RRF merge when embedding present |
| `knn_search(embedding, memory_type, limit)` | `list[MemoryHit]` | Delegate to VectorRetriever (used by ingestion dedup) |
| `top_semantic(limit=5, min_importance=0.0, project="", repo="")` | `list[MemoryEntry]` | Direct SQL — no FTS needed |

**Scoring formula:**
```
score = -bm25_rank + importance_boost + pin_boost + recency_decay + context_match
```
- Semantic: importance_weight=1.0, recency_weight=0.5
- Episodic: importance_weight=0.5, recency_weight=1.0

**Failure modes:**
- `sqlite3.OperationalError` — vec table missing → KNN returns []
- `MemorySchemaError` — invalid created_at timestamp

### 8. `injection.py` — Lifecycle injection service

Class `MemoryInjectionService(policy, retriever, embed_client, project="", repo="")`:

| Method | Returns | Description |
|---|---|---|
| `on_session_start()` | `list[MemorySnippet]` | Top semantic entries by importance |
| `on_user_prompt(query, session_id)` | `list[MemorySnippet]` | Semantic + episodic search with embedding |

Uses `InjectionPolicy(max_semantic=5, max_episodic=3, min_importance=0.3)`.

**Failure modes:** `InjectionValidationError` when query is empty.

### 9. `ingestion.py` — Extraction + dedup + persist

Class `MemoryIngestionService(store, jsonl, retriever, embed_client, dedup_policy=None, ...)`:

| Method | Returns | Description |
|---|---|---|
| `on_session_stop(session_id, history, turn_id=None)` | `None` | Extract, dedup, persist from conversation history |
| `write_semantic(session_id, content)` | `None` | Manual persist (no dedup) |
| `write_episodic(session_id, content)` | `None` | Manual persist (no dedup) |

Dedup: uses `DedupPolicy(action=SKIP_NEW, threshold=...)` with KNN near-duplicate detection.

**Failure modes:** `sqlite3.OperationalError` on memory_links insert (swallowed with warning).

### 10. `extract.py` — Rule-based extraction

| Function / Class | Returns | Description |
|---|---|---|
| `extract_memories(history, session_id=None, turn_id=None, ...)` | `list[MemoryEntry]` | Main entry point |
| `ExtractionPolicy(...)` | Config | min_content_chars=80, min_turns=2, max_entries=20 |

Classification logic:
- Semantic (rules/decisions): assistant messages with rule/policy keywords or long content
- Episodic (failures/Q&A): failure keywords or substantial answers

Importance heuristic: 0.4 base + length_bonus + keyword_bonus.

### 11. `jsonl_store.py` — JSONL source of truth

Class `JsonlMemoryStore(path)`:

| Method | Returns | Description |
|---|---|---|
| `write(entry)` | `None` | Async append (asyncio.Lock serialised) |
| `read_all()` | `list[MemoryEntry]` | Sync read of all entries |

**Failure modes:** `JsonlFormatError` on malformed lines.

### 12. `embedding_client.py` — HTTP embedding client

Class `EmbeddingClient(config, http=None, *, enabled=False)`:

| Method | Returns | Description |
|---|---|---|
| `fetch(text)` | `EmbeddingResult` | Async embedding with retry + circuit breaker |

`EmbeddingClientConfig`: embed_url, timeout=5s, max_retries=2, circuit_open_after=3, circuit_reset_sec=60.

**Disabled behavior:** When `enabled=False`, `fetch()` returns `EmbeddingResult(success=False, error_kind=DISABLED)` immediately without HTTP call.

### 13. `services.py` — MemoryServices facade

Class `MemoryServices(injection, ingestion, store, retriever)`:

| Attribute / Method | Description |
|---|---|
| `injection` | MemoryInjectionService instance |
| `ingestion` | MemoryIngestionService instance |
| `store` | MemoryStore instance |
| `retriever` | HybridRetriever instance |
| `on_session_start(session_id)` | Delegates to `injection.on_session_start()` |
| `on_session_stop(session_id, history, turn_id)` | Delegates to `ingestion.on_session_stop()` |
| `on_user_prompt(query, session_id)` | Delegates to `injection.on_user_prompt()` |

### 14. `mapper.py` — Row conversion utils

| Function | Returns | Description |
|---|---|---|
| `row_to_entry(dict)` | `MemoryEntry` | SQLite row to MemoryEntry |
| `_floats_to_blob(list[float], dim=None)` | `bytes` | Embedding to sqlite-vec blob |
| `_stamp_entry(entry, now)` | `MemoryEntry` | Set created_at/updated_at |
| `_now_iso()` | `str` | UTC ISO timestamp |

---

## Disabled Behavior

When `config.memory.use_memory_layer` is `False`:

1. `factory._build_memory_services()` returns `None` — `MemoryServices` is never constructed.
2. `ctx.services.memory` is `None`.
3. All callers check `ctx.services.memory is None` before access (e.g. `cmd_memory.py`, `context.py`).
4. `EmbeddingClient` has its own `enabled` flag — when disabled, returns `DISABLED` error without HTTP call.
5. `cli_view.py` shows `Memory layer` status as disabled.

No individual module implements its own enabled/disabled gate — the factory-level None pattern covers all operations.

---

## Related Documents

- Runtime architecture: [05_agent_02_runtime-architecture.md](05_agent_02_runtime-architecture.md)
- Configuration: [05_agent_08_configuration.md](05_agent_08_configuration.md)
