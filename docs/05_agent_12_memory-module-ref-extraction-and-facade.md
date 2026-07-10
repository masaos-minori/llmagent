---
title: "Memory Layer - Module Reference: Extraction and Facade"
category: agent
tags:
  - agent
  - memory
  - module-reference
  - extract
  - jsonl-store
  - embedding-client
  - services
related:
  - 05_agent_00_document-guide.md
  - 05_agent_12_memory-overview-and-modes.md
  - 05_agent_12_memory-gate-data-model-search.md
  - 05_agent_12_memory-module-ref-core-and-store.md
  - 05_agent_12_memory-module-ref-retrieval-and-injection.md
  - 05_agent_12_memory-module-ref-ops-and-scoring.md
source:
  - 05_agent_12_memory.md
---

# Memory Layer — Module Reference

- Operations and observability → [05_agent_10_operations-and-observability-startup-and-health.md](05_agent_10_operations-and-observability-startup-and-health.md)
- Configuration → [05_agent_08_configuration-tools-memory.md](05_agent_08_configuration-tools-memory.md)

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

## Related Documents

- `05_agent_00_document-guide.md`
- `05_agent_12_memory-overview-and-modes.md`
- `05_agent_12_memory-gate-data-model-search.md`
- `05_agent_12_memory-module-ref-core-and-store.md`
- `05_agent_12_memory-module-ref-retrieval-and-injection.md`
- `05_agent_12_memory-module-ref-ops-and-scoring.md`

## Keywords

extract.py
jsonl_store.py
embedding_client.py
services.py
