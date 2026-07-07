# Memory Layer — Module Reference

- Operations and observability → [05_agent_10_operations-and-observability.md](05_agent_10_operations-and-observability.md)
- Configuration → [05_agent_08_configuration.md](05_agent_08_configuration.md)

## Persistent Semantic Memory — Overview

Persistent Semantic Memory stores abstract rules, design decisions, failure patterns,
and conversational Q&A across agent sessions.

**Memory types**:
- Semantic: long-lived rules and decisions (importance ≥ 0.5 for session startup injection)
- Episodic: session-specific failures and Q&A (injected on first user prompt)

**Source types**: RULE / DECISION / FAILURE / CONVERSATION

**Local-only guarantee**: set `memory_local_only = true` to enforce that the embedding
endpoint is a loopback address. Fails startup if `embed_url` is non-local.

**Automatic context restoration**:
- Session start: pinned + high-importance semantic injected
- First user prompt: task-specific hybrid retrieval (semantic + episodic)

## Production Checklist

- [ ] `memory_local_only = true` if data must not leave the machine
- [ ] `embed_url` points to local embedding service (e.g., `http://localhost:11434`)
- [ ] `/memory status` shows `mode: hybrid` or `mode: fts-only` (not `disabled`)
- [ ] `/memory rebuild` tested after restoring JSONL backup

---

## Purpose

API reference for all modules under `scripts/agent/memory/`. A developer should
understand each module's responsibility, public API surface, and disabled behavior
without reading source code.

---

## Overview

| Module | Responsibility |
|---|---|
| `__init__.py` | Public API barrel — re-exports all public symbols |
| `types.py` | Core runtime types (MemoryEntry, MemoryQuery, MemoryHit, EmbeddingResult) |
| `enums.py` | Domain enums (MemoryType, DedupAction, RetrievalMode, ExtractionDecision) |
| `exceptions.py` | Exception hierarchy |
| `models.py` | Frozen DTOs (HistoryMessage, JsonlRecord, MemorySnippet, ConsistencyReport) |
| `store.py` | CRUD for memories / memories_fts / memories_vec tables |
| `retriever.py` | FTS5 / KNN / Hybrid search (FtsRetriever, VectorRetriever, HybridRetriever) |
| `injection.py` | MemoryInjectionService — lifecycle hooks for snippet injection |
| `ingestion.py` | MemoryIngestionService — extract, dedup, persist |
| `extract.py` | Rule-based extraction from conversation history |
| `jsonl_store.py` | Append-only JSONL archive |
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
         |                                       | 4. write_ops.upsert()       |
         v                                       +-----------------------------+
+-----------------+
| jsonl_store.py  |  Append-only archive
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
- When `False`, memory services are not built; `ctx.services.memory` is `None`
- All callers guard with `if ctx.services.memory is None: return`
- Bypasses injection, ingestion, and retrieval entirely

**Layer 2: Embedding client enabled**
- Embedding client enabled flag gates HTTP and embedding calls
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

> **Current behavior:** When a non-empty branch is provided, retrieval applies a hard SQL
> filter that includes only:
> - memories with `branch = ''` (global memories — always included)
> - memories with `branch = <current branch>`
>
> Memories from other branches are excluded entirely (not merely ranked lower).
| `content` | `str` | Full message content |
| `summary` | `str` | Short summary of the content |
| `tags` | `list[str]` | Keyword tags for classification |
| `importance` | `float` | 0.0–1.0; higher = higher retrieval priority (default: 0.5) |
| `pinned` | `bool` | When `True`, injected at every session start |
| `created_at` | `str` | ISO 8601 UTC timestamp; filled by `write_ops.add()` |
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
- File path controlled by `memory_jsonl_dir` config (filename: `memories.jsonl`)
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

### 7. `retriever.py` — Search (FTS5 + KNN + Hybrid)

| Class | Role |
|---|---|
| `FtsRetriever` | FTS5 BM25 search with importance / pin / recency rescoring |
| `VectorRetriever` | KNN search via sqlite-vec |
| `HybridRetriever` | Primary external interface — composes both with RRF merge |

**`HybridRetriever` attributes and methods:**

| Method / Attribute | Returns | Description |
|---|---|---|
| `search(query: MemoryQuery, embedding: list[float] | None = None, project="", repo="", branch="")` | `list[MemoryHit]` | FTS-only when no embedding; RRF merge when embedding present. Takes a `MemoryQuery` object (not raw string) — the query text is extracted from `query.query` internally. Sets `last_retrieval_mode` on return. |
| `knn_search(embedding, memory_type, limit, branch="")` | `list[MemoryHit]` | Delegate to VectorRetriever (used by ingestion dedup) |
| `top_semantic(limit=5, min_importance=0.0, project="", repo="", branch="")` | `list[MemoryEntry]` | Direct SQL — no FTS needed |
| `embed_client` | `EmbeddingClient \| None` | Injected at construction; used by `/memory status` |
| `last_retrieval_mode` | `str` | `"hybrid"` / `"fts_only"` / `"unknown"` — set on each `search()` call |
| `fts_fallback_count` | `int` | Count of FTS fallbacks during hybrid search |

**`FtsRetriever` methods and attributes:**

| Method / Attribute | Returns | Description |
|---|---|---|
| `search(query: MemoryQuery, project="", repo="", branch="")` | `list[MemoryHit]` | FTS5 BM25 search with rescoring. Returns [] on error or empty query. |
| `candidate_limit` | `int` | Maximum candidate results from FTS query |

**`VectorRetriever` methods:**

| Method | Returns | Description |
|---|---|---|
| `knn_search(embedding, memory_type, limit, branch="")` | `list[MemoryHit]` | KNN search; score is cosine similarity (higher-is-better). When embeddings disabled, returns []. |

**Scoring formula:**
```
score = -bm25_rank + importance_boost + pin_boost + recency_decay + context_match
```
- Semantic: importance_weight=1.0, recency_weight=0.5
- Episodic: importance_weight=0.5, recency_weight=1.0

**Failure modes:**
- `sqlite3.OperationalError` — vec table missing → KNN returns []
- `MemorySchemaError` — invalid created_at timestamp

**Branch Awareness:**

All retrieval paths apply a hard SQL branch filter when a non-empty branch is provided:

```sql
AND (? = '' OR m.branch = '' OR m.branch = ?)
```

- Branch is resolved once at startup via `shared.git_helper.get_repo_info()` in `factory.py`.
- Entries with `branch=""` (global memories) are always included regardless of current branch.
- When `get_repo_info()` fails or HEAD is detached, branch defaults to `""` — no filter is applied (safe degraded behavior).
- The injection service passes the resolved branch value to all `retriever.search()` calls.
- Dedup KNN in ingestion uses `branch=""` (global scope) to ensure cross-branch duplicate detection.

### 8. `injection.py` — Lifecycle injection service

Class `MemoryInjectionService(policy, retriever, embed_client, project="", repo="", branch="", enabled=False)`:

| Method | Returns | Description |
|---|---|---|
| `on_session_start()` | `list[MemorySnippet]` | Top semantic entries by importance (sync) |
| `on_user_prompt(query, session_id)` | `list[MemorySnippet]` | Semantic + episodic search with embedding (async) |

Uses `InjectionPolicy(max_semantic=5, max_episodic=3, min_importance=0.5)`.

**Failure modes:** `InjectionValidationError` when query is empty.

| Attribute / Method | Type / Returns | Default | Description |
|---|---|---|---|
| `max_semantic` | `int` | `5` | Max semantic snippets to inject |
| `max_episodic` | `int` | `3` | Max episodic snippets to inject |
| `min_importance` | `float` | `0.5` | Min importance threshold for retrieval |
| `format_prefix_semantic` | `str` | `"[Semantic memory]"` | Prefix for semantic snippets |
| `format_prefix_episodic` | `str` | `"[Episodic memory]"` | Prefix for episodic snippets |

**Failure modes:** `InjectionValidationError` when query is empty.

### 9. `ingestion.py` — Extraction + dedup + persist

Class `MemoryIngestionService(store, jsonl, retriever, embed_client=None, *, dedup_policy=None, project="", repo="", branch="", max_content_chars=500)`:

| Method / Attribute | Returns | Description |
|---|---|---|
| `on_session_stop(session_id, history, turn_id=None)` | `None` | Extract, dedup, persist from conversation history |
| `write_semantic(session_id, content)` | `None` | Manual persist (no dedup) |
| `write_episodic(session_id, content)` | `None` | Manual persist (no dedup) |
| `stat_embed_skip` | `int` | Counter of embeddings skipped due to errors |

Dedup: uses `DedupPolicy(action=SKIP_NEW, threshold=...)` with KNN near-duplicate detection.

**Failure modes:** `sqlite3.OperationalError` on memory_links insert (swallowed with warning).

**Embed failure tracking:** `stat_embed_skip` counter increments whenever a write operation stores an entry without embedding (embedding failed). Logged in `on_session_stop()` summary: `"MemoryIngestionService.on_session_stop: persisted %d entries; %d embed_skipped"`.

### 10. `extract.py` — Rule-based extraction

| Function / Class | Returns | Description |
|---|---|---|
| `extract_memories(history, session_id=None, turn_id=None, project="", repo="", branch="")` | `list[MemoryEntry]` | Main entry point |
| `ExtractionPolicy(...)` | Config | min_content_chars=80, min_turns=2, max_entries=20, min_user_content_chars=60 |

**Module-level constants:** `MIN_CONTENT_CHARS = 80`, `MIN_USER_CONTENT_CHARS = 60`, `MIN_TURNS = 2`, `MAX_ENTRIES = 20`, `SEMANTIC_HITS_REQUIRED_STRONG = 2`, `SEMANTIC_CONTENT_THRESHOLD = 200`, `IMPORTANCE_LENGTH_DIVISOR = 2000.0`


Classification logic:
- Semantic (rules/decisions): assistant messages with rule/policy keywords or long content
- Episodic (failures/Q&A): failure keywords or substantial answers

Importance heuristic: 0.4 base + length_bonus + keyword_bonus.

### 11. `jsonl_store.py` — Append-only JSONL archive

Class `JsonlMemoryStore(path)`:

| Method | Returns | Description |
|---|---|---|
| `write(entry)` | `None` | Async append (asyncio.Lock serialised) |
| `read_all()` | `list[MemoryEntry]` | Sync read of all entries |
| `read_active()` | `list[MemoryEntry]` | Read entries that have not expired based on per-source-type retention policy |
| `count_all()` | `int` | Count of valid records (delegates to `read_all()`) |

**Failure modes:** `JsonlFormatError` on malformed lines.

**Note:** SQLite memory tables are authoritative for current memory state. JSONL is retained as an append-only archive for import/export and disaster recovery. Deletes and pin/unpin state changes are not replayed from JSONL.

### 12. `embedding_client.py` — HTTP embedding client

Class `EmbeddingClient(config, http=None, *, enabled=False)`:

| Method | Returns | Description |
|---|---|---|
| `fetch(text)` | `EmbeddingResult` | Async embedding with retry + circuit breaker |
| `get_status()` | `EmbeddingClientStatus` | Snapshot of enabled, circuit_open, fail_count, resets_in_sec |

`EmbeddingClientConfig`: embed_url, timeout=5.0, max_retries=2, circuit_open_after=3, circuit_reset_sec=60.0, query_prefix="query: ", embed_dim=384, local_only=False.

**Disabled behavior:** When `enabled=False`, `fetch()` returns `EmbeddingResult(success=False, error_kind=DISABLED)` immediately without HTTP call.

`EmbeddingClientStatus` fields: `enabled: bool`, `circuit_open: bool`, `fail_count: int`, `resets_in_sec: float | None` (None when circuit closed, otherwise seconds until circuit resets), `local_only: bool`.

`EmbeddingErrorKind` values: `DISABLED`, `CIRCUIT_OPEN`, `TIMEOUT`, `HTTP_ERROR`, `INVALID_RESPONSE`, `UNKNOWN_ERROR`, `DIMENSION_MISMATCH`.

### 13. `services.py` — MemoryServices facade

Class `MemoryServices(injection, ingestion, store, retriever, embedding_client=None, *, use_memory_layer=False)`:

| Attribute / Method | Description |
|---|---|
| `injection` | MemoryInjectionService instance |
| `ingestion` | MemoryIngestionService instance |
| `store` | MemoryStore instance |
| `retriever` | HybridRetriever instance |
| `embedding_client` | EmbeddingClient (from retriever if not provided) |
| `get_activation_mode()` | Returns: "disabled" / "fts-only" / "degraded" / "hybrid" |
| `get_stats()` | Returns `dict` with keys: total (int), semantic (int), episodic (int), by_source (dict[str, int]), embed_skip (int), last_retrieval_mode (str), fts_fallback_count (int) |
| `on_session_start(session_id)` | Delegates to `injection.on_session_start()` |
| `on_session_stop(session_id, history, turn_id)` | Delegates to `ingestion.on_session_stop()` |
| `on_user_prompt(query, session_id)` | Delegates to `injection.on_user_prompt()` |

### 14. `mapper.py` — Row conversion utils

| Function | Returns | Description |
|---|---|---|
| `row_to_entry(dict)` | `MemoryEntry` | SQLite row to MemoryEntry |

Internal helper functions for float-to-BLOB conversion, timestamp stamping, and ISO 8601 timestamp generation.

### 15. `write_ops.py` — Write operations

| Function | Returns | Description |
|---|---|---|
| `add(entry, embedding=None, embed_dim=None)` | `None` | Insert + FTS sync; BEGIN IMMEDIATE for atomicity. When `embedding` is provided, also writes to memories_vec. |
| `upsert(entry, embedding=None, embed_dim=None)` | `None` | Insert-or-replace + FTS sync. When `embedding` is provided, also upserts memories_vec. |
| `delete(memory_id)` | `bool` | Remove entry by ID |
| `clear_by_session(session_id)` | `int` | Bulk delete for one session |

### 16. `pin_ops.py` — Pin/unpin operations

| Function | Returns | Description |
|---|---|---|
| `pin(memory_id, conn=None)` | `bool` | Set pinned=1; returns True when found. When `conn` is provided, uses that connection (caller must commit). |
| `unpin(memory_id, conn=None)` | `bool` | Set pinned=0; returns True when found. When `conn` is provided, uses that connection (caller must commit). |

### 17. `count_ops.py` — Diagnostic counts

| Function | Returns | Description |
|---|---|---|
| `count_entries()` | `int` | Row count in memories table (diagnostic) |
| `count_by_type()` | `dict[str, int]` | {memory_type: count} for all rows (diagnostic) |
| `count_by_source_type()` | `dict[str, int]` | {source_type: count} for all rows (diagnostic) |
| `count_vec()` | `int` | Row count in memories_vec (raises OperationalError if unavailable) |
| `count_prunable(days)` | `int` | Count of entries older than `days` days |

### 18. `rebuild_ops.py` — Rebuild operations

| Function | Returns | Description |
|---|---|---|
| `rebuild_fts()` | `int` | Rebuild FTS5 index from memories table; returns row count inserted |
| `rebuild_vec()` | `int` | Rebuild vec index from memories table; returns row count inserted |

### 19. `import_ops.py` — Import operations

| Function | Returns | Description |
|---|---|---|
| `import_from_jsonl(jsonl_store, *, dry_run=False, embed_dim=None)` | `tuple[int, int]` | Import entries from JSONL archive into SQLite; returns (jsonl_count, inserted_count). When `dry_run=True`, returns counts without inserting. Does NOT replay deletes or pin/unpin state changes. |

### 20. `scoring.py` — BM25 scoring with boosts

**Constants:**
- `_PIN_BOOST = 0.3` — pin boost for pinned entries
- `_IMPORTANCE_BOOST_SCALE = 0.5` — scale factor for importance (importance × 0.5)
- `_RECENCY_MAX_BOOST = 0.2` — max recency boost for entries within 7 days
- `_CONTEXT_MATCH_BOOST = 0.1` — base context match boost for project/repo matches
- `_RECENCY_DAYS = 7.0` — recency window in days

| Function / Constant | Returns | Description |
|---|---|---|
| `score(bm25_rank, entry, project, repo[, recency_days, branch])` | `float` | Combined score: `-bm25_rank + importance_boost + pin_boost + recency_decay + context_match`. Formula: `score = -bm25_rank + (importance_w × importance × 0.5) + (0.3 if pinned else 0) + (recency_w × recency_boost(created_at)) + context_boost(entry, project, repo, branch)` |
| `recency_boost(created_at[, recency_days])` | `float` | Boost inversely proportional to entry age: `_RECENCY_MAX_BOOST × (1 - age_days / recency_days)`, returns 0.0 when age ≥ recency_days |
| `context_boost(entry, project, repo[, branch])` | `float` | Branch match: 0.15; project/repo match: 0.1; no match: 0.0 |

### 21. `rrf.py` — Reciprocal Rank Fusion merge

| Constant / Function | Returns | Description |
|---|---|---|
| `RRF_K` | `60` | Reciprocal rank fusion constant |
| `rrf_merge(hit_lists, k=60)` | `list[MemoryHit]` | Merge multiple ranked hit lists by rank position using RRF scoring (each list contributes 1.0 / (k + rank + 1)) |

### 22. `fts_query.py` — FTS5 query builder

| Function / Constant | Returns | Description |
|---|---|---|
| `build_fts_query(text: str)` | `str` | Build FTS5 MATCH query with token quoting |

### 23. `sql_constants.py` — SQL constants

Internal helper module; no public API.

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
