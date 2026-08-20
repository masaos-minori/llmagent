# Memory Layer — Module Reference: Extraction and Facade

- Operations and Observability $\rightarrow$ [05_agent_10_01_operations-and-observability-startup-and-health.md](05_agent_10_01_operations-and-observability-startup-and-health.md)
- Configuration $\rightarrow$ [05_agent_08_03_configuration-tools-memory.md](05_agent_08_03_configuration-tools-memory.md)

## Purpose

Defines the responsibility boundaries for rule-based extraction, append-only archiving, HTTP embedding clients, and the facade within the memory layer.

## Design Intent

Since the memory layer is optional, all public APIs are designed to be safely guarded when `ctx.services.memory is None`. Core types are defined as immutable DTOs and are compatible with both JSONL and SQLite storage layers.

## Responsibility Boundary

- **Memory Layer owns:** Persistence, search, and injection of memory entries.
- **Memory Layer does NOT own:** LLM context generation, tool execution, or RAG document search.

## Key Constraints

- If `use_memory_layer = false` is set, the memory service is not constructed and all memory operations are completely bypassed.
- `VectorRetriever.knn_search()` raises an `OperationalError` if the `memories_vec` table does not exist (exceptions propagate if embeddings are enabled while tables are uninitialized).
- When `EmbeddingClient.enabled=False`, `fetch()` returns `EmbeddingResult(success=False, error_kind=DISABLED)` immediately without making an HTTP call.
- If embedding retrieval fails, processing continues and the entry is saved without embeddings (`stat_embed_skip` counter increases).
- `JsonlMemoryStore` is an append-only archive. Deletions and changes to pin/unpin status are not replayed.
- Automatic extraction (`on_session_stop`) applies deduplication via `DedupAction.SKIP_NEW`, but manual writes intentionally bypass this deduplication.
- After retrieving embeddings, KNN nearest neighbors are searched; if an existing entry is found that is closer than the threshold for its `source_type`, the new entry is discarded (SKIP_NEW).
- If embedding retrieval fails, saving to SQLite/JSONL continues without embeddings (fail-open).
- If writing to JSONL fails with `OSError`, a warning is logged and processing continues (not treated as a fatal error since SQLite is the source of truth).

## Operational Notes

- Current mode can be checked with `/memory status` (Disabled / FTS-only / Degraded / Hybrid).
- `get_stats()` contains the following keys: total, semantic, episodic, by_source, embed_skip, last_retrieval_mode, fts_fallback_count.
- If embedding retrieval fails, the `stat_embed_skip` counter increases and is logged in the summary of `on_session_stop()`.
- If insertion into `memory_links` fails with `sqlite3.OperationalError`/`IntegrityError`, only a warning is logged and processing continues.

## Known Limitations

- If a single source message is split into multiple chunks, each appears as an independent hit during search (fragmentation).
- Enterprise filters based on `RETENTION_DAYS` retention period are currently unreachable (NC-007).

## Related Docs

- `05_agent_00_document-guide.md`
- `05_agent_12_01_memory-overview-and-modes.md`
- `05_agent_12_02_memory-gate-data-model-search.md`
- `05_agent_12_03_memory-module-ref-core-and-store.md`
- `05_agent_12_04_memory-module-ref-retrieval-and-injection.md`
- `05_agent_12_06_memory-module-ref-ops-and-scoring.md`
