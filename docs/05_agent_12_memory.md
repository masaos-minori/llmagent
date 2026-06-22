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
| `models.py` | Frozen DTOs (HistoryMessage, JsonlRecord, MemorySnippet, ConsistencyReport) |
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

## Session Lifecycle Data Flow

```
session_start
    |
    v
+-----------------+
| services.py     |  MemoryServices.on_session_start()
|                 |---> injection.on_session_start()
+--------+--------+
         |
         v
+-----------------+     +------------------+
| injection.py    |---->| retriever.py     |
| MemoryInject    |     | HybridRetriever  |
| Service         |     | top_semantic()   |
+--------+--------+     +------------------+
         |
         v
+-----------------+
| models.py       |  MemorySnippet[] -> injected into LLM context
| MemorySnippet   |
+-----------------+

user_prompt (during session)
    |
    v
+-----------------+     +-----------------+     +---------------------+
| services.py     |---->| injection.py    |---->| embedding_client.py |
| on_user_prompt  |     | on_user_prompt  |     | EmbeddingClient     |
+-----------------+     +--------+--------+     +---------------------+
                                 |
                                 v
                         +------------------+
                         | retriever.py     |
                         | HybridRetriever  |
                         | search() (RRF)   |
                         +--------+---------+
                                  |
                                  v
                         +-----------------+
                         | models.py       |
                         | MemorySnippet[] |
                         +-----------------+

session_stop
    |
    v
+-----------------+
| services.py     |  MemoryServices.on_session_stop()
|                 |---> ingestion.on_session_stop()
+--------+--------+
         |
         v
+-----------------+     +------------------+     +-----------------------------+
| ingestion.py    |---->| extract.py       |---->| For each MemoryEntry:       |
| MemoryIngestion |     | extract_memories |     | 1. EmbeddingClient.fetch()  |
| Service         |     +------------------+     | 2. Dedup check (KNN)        |
+--------+--------+                              | 3. JsonlMemoryStore.write() |
         |                                       | 4. MemoryStore.upsert()     |
         v                                       +-----------------------------+
+-----------------+
| jsonl_store.py  |  Append-only source of truth
| JsonlMemoryStore|
+--------+--------+
         |
         v
+-----------------+     +------------------+
| store.py        |---->| retriever.py     |
| MemoryStore     |     | .fts_search()    |
| (SQLite index)  |     | .knn_search()    |
+-----------------+     +------------------+
```

---

## Activation Gate

The memory layer has a 3-layer activation gate that controls when memory operations execute.

**Layer 1: Config bypass**
- `use_memory_layer` config flag (default: `False`)
- When `False`, `factory._build_memory_services()` returns `None`; `ctx.services.memory` is `None`
- All callers guard with `if ctx.services.memory is None: return`
- Bypasses injection, ingestion, and retrieval entirely

**Layer 2: Embedding client enabled**
- `EmbeddingClient._enabled` gates HTTP and embedding calls
- When `False`: `fetch()` returns `EmbeddingResult(success=False, error_kind=DISABLED)` immediately
- `HybridRetriever.search()` falls back to FTS5-only when embedding is unavailable

**Layer 3: Service facade invocation**
- `MemoryServices` is the single entry point (`on_session_start`, `on_user_prompt`, `on_session_stop`)
- All memory operations route through this facade; direct sub-service access is for testing only

### Disabled Behavior by Module

| Module | Disabled condition | Behavior |
|---|---|---|
| `services.py` | `use_memory_layer=False` (Layer 1) | `ctx.services.memory` is `None`; callers skip |
| `injection.py` | Layer 1 bypassed | `MemoryInjectionService` never constructed; no snippets injected |
| `ingestion.py` | Layer 1 bypassed | `MemoryIngestionService` never constructed; no entries written |
| `embedding_client.py` | `enabled=False` (Layer 2) | `fetch()` returns `EmbeddingResult(error_kind=DISABLED)` without HTTP call |
| `retriever.py` | Layer 2 disabled | `HybridRetriever.search()` uses FTS5-only; `knn_search()` returns `[]` |
| `jsonl_store.py` | Layer 1 bypassed | `write()` never called; file unchanged |
| `store.py` | Layer 1 bypassed | `upsert()` never called; SQLite index unchanged |
| `extract.py` | Layer 1 bypassed | `extract_memories()` never called |
| `mapper.py` | N/A (pure utility) | Always available |
| `models.py` | N/A (pure data) | Always available |
| `types.py` | N/A (pure data) | Always available |
| `enums.py` | N/A (pure data) | Always available |
| `exceptions.py` | N/A (pure data) | Always available |

---

## Data Model

### MemoryEntry (stored in JSONL + SQLite)

| Field | Type | Description |
|---|---|---|
| `memory_id` | `str` | UUID v4, primary key |
| `memory_type` | `MemoryType` | `"semantic"` \| `"episodic"` |
| `source_type` | `SourceType` | `"RULE"` \| `"CONVERSATION"` \| `"DECISION"` \| `"FAILURE"` |
| `session_id` | `int \| None` | Parent session ID |
| `turn_id` | `str \| None` | UUID linking to the originating conversation turn |
| `project` | `str` | Project name for context filtering |
| `repo` | `str` | Repository name for context filtering |
| `branch` | `str` | Git branch for context filtering |
| `content` | `str` | Full message content |
| `summary` | `str` | Short summary of the content |
| `tags` | `list[str]` | Keyword tags for classification |
| `importance` | `float` | 0.0–1.0; higher = higher retrieval priority (default: 0.5) |
| `pinned` | `bool` | When `True`, injected at every session start |
| `created_at` | `str` | ISO 8601 UTC timestamp; filled by `MemoryStore.add()` |
| `updated_at` | `str` | ISO 8601 UTC timestamp |

**DB mapping:** Stored in `memories` table (SQLite) and one line per entry in the JSONL file. FTS5 index in `memories_fts`. Vector index in `memories_vec` (when embedding enabled).

### MemorySnippet (injected into LLM context)

| Field | Type | Description |
|---|---|---|
| `text` | `str` | Formatted string with memory type prefix (e.g. `"[Semantic memory] ..."`) |
| `source` | `str` | `"semantic"` \| `"episodic"` |
| `score` | `float` | Relevance score from search (RRF merge rank or FTS5 rank) |

---

## JSONL Format

Each line in the JSONL store is a single JSON object serializing all `MemoryEntry` fields:

```json
{"memory_id": "uuid-here", "memory_type": "semantic", "source_type": "RULE", "session_id": 1, "turn_id": null, "project": "myproj", "repo": "myrepo", "branch": "main", "content": "Use orjson for JSON.", "summary": "orjson preference", "tags": [], "importance": 0.7, "pinned": false, "created_at": "2026-06-19T23:00:00Z", "updated_at": "2026-06-19T23:00:00Z"}
```

**Properties:**
- Append-only: entries are never modified or deleted in the file
- One entry per line; UTF-8 encoded; valid JSON per line
- File path controlled by `memory_jsonl_path` config
- Source of truth: SQLite index is rebuilt from JSONL if needed

---

## Search Strategies

### FTS5 (Full-Text Search)

- **Engine:** SQLite FTS5 with BM25 ranking
- **Index:** Tokenized `content` column in `memories_fts`
- **Fallback:** Used when `EmbeddingClient.enabled=False` or no embedding returned
- **Strengths:** Exact keyword matching, no API dependency, fast on small datasets
- **Weaknesses:** No semantic understanding

### KNN (Vector Search)

- **Engine:** sqlite-vec extension with cosine similarity
- **Index:** Dense embedding vectors in `memories_vec`
- **Requirement:** `EmbeddingClient.enabled=True` with a valid embedding API endpoint
- **Strengths:** Semantic similarity matching, language-agnostic
- **Weaknesses:** Requires embedding API call, sqlite-vec extension must be loaded

### Hybrid (RRF Merge)

- **Engine:** Combines FTS5 + KNN results using Reciprocal Rank Fusion (RRF)
- **Formula:** `rrf_score = 1.0 / (k + rank + 1)` where `k=60`, `rank` is 0-based
- **Result:** Deduplicated, sorted by descending RRF score
- **Strengths:** Best-of-both-worlds across query types
- **Weaknesses:** Higher latency (two searches + merge); requires embedding API

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
| `SourceType` | Entry origin | RULE, CONVERSATION, DECISION, FAILURE |

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
| `JsonlRecord` | memory_id, memory_type, source_type, session_id, turn_id, project, repo, branch, content, summary, tags, importance, pinned, created_at, updated_at | Deserialized record from the JSONL memory store |
| `MemorySnippet` | text (str), source (str), score (float) | Injected context snippet with source tag and retrieval score |
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
| `rebuild_from_jsonl(jsonl_store, *, dry_run=False)` | `tuple[int, int]` | Rebuild memories/FTS/vec from JSONL; returns (jsonl_count, inserted_count) |

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

**Embed failure tracking:** `stat_embed_skip` counter increments whenever `_persist_entry()` or `_persist_entry_with_dedup()` stores an entry without embedding (embedding failed). Logged in `on_session_stop()` summary: `"MemoryIngestionService.on_session_stop: persisted %d entries; %d embed_skipped"`.

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
| `count_all()` | `int` | Count of valid records (delegates to `read_all()`) |

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

See the [Activation Gate](#activation-gate) section and [Disabled Behavior by Module](#disabled-behavior-by-module) table above for the full per-module breakdown.

Summary:
- `use_memory_layer=False` → `ctx.services.memory` is `None`; all memory operations are skipped
- `EmbeddingClient.enabled=False` → `fetch()` returns `DISABLED` error; retrieval falls back to FTS5-only
- `cli_view.py` reflects memory layer status at startup banner

---

## Related Documents

- Runtime architecture: [05_agent_02_runtime-architecture.md](05_agent_02_runtime-architecture.md)
- Configuration: [05_agent_08_configuration.md](05_agent_08_configuration.md)
