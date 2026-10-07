---
title: "Memory Layer — Module Reference"
area: agent
tags:
  - agent
  - memory
  - module-reference
  - types
  - store
  - retrieval-injection
  - extraction-facade
  - write-ops
  - scoring
  - rrf
related:
  - agent_00_document-guide.md
  - agent_11_01_memory-overview-and-modes.md
  - agent_11_02_memory-gate-data-model-search.md
  - agent_11_04_memory-module-reference-generated.md
---

# Memory Layer — Module Reference

- Operations and Observability → [agent_10_01_operations-and-observability-startup-and-health.md](agent_10_01_operations-and-observability-startup-and-health.md)
- Configuration → [agent_08_03_configuration-tools-memory.md](agent_08_03_configuration-tools-memory.md)

## Purpose

Defines the responsibility boundaries of the memory layer's modules: core types and persistence stores; search (FTS5 + KNN + hybrid) and lifecycle injection; rule-based extraction, append-only archiving, the HTTP embedding client and the facade; write operations, scoring, RRF merging and the FTS5 query builder.

## Design Intent

Since the memory layer is optional, all public APIs are designed to be safely guarded when `ctx.services.memory is None`. Core types are defined as immutable DTOs and are compatible with both JSONL and SQLite storage layers.

## Responsibility Boundary

- **Memory Layer owns:** Persistence, search, and injection of memory entries.
- **Memory Layer does NOT own:** LLM context generation, tool execution, or RAG document search.

## Key Constraints

### Common

- If `use_memory_layer = false` is set, the memory service is not constructed and all memory operations are completely bypassed.
- `VectorRetriever.knn_search()` raises an `OperationalError` if the `memories_vec` table does not exist (exceptions propagate if embeddings are enabled while tables are uninitialized).

### Core and Store

- `MemoryStore.list_entries()` branch filtering behavior: uses `branch = '' OR branch = ?`, meaning entries with an empty string branch always match regardless of the specified branch value.
- `embed_dim` is not in `MemoryStore` itself; it is passed by the caller `agent/factory.py` (`MemoryStore(embed_dim=get_embedding_dims())`), sourced from `scripts/db/store_protocols.py::get_embedding_dims()` (a fixed code-level constant), not a config field.

### Retrieval and Injection

- `HybridRetriever.search()` performs FTS only if embeddings are unavailable; otherwise, it performs RRF merging.
- Default `InjectionPolicy`: `max_semantic` (semantic memories per turn), `max_episodic` (episodic memories per turn), `min_importance` (importance threshold), `max_snippet_length` (characters per snippet); values: see `InjectionPolicy` in `scripts/agent/memory/injection.py`.
- `knn_search` uses L2/Euclidean distance metric (explicit `distance_metric=L2` in vec0 DDL).

### Extraction and Facade

- When `EmbeddingClient.enabled=False`, `fetch()` returns `EmbeddingResult(success=False, error_kind=DISABLED)` immediately without making an HTTP call.
- If embedding retrieval fails, processing continues and the entry is saved without embeddings (`stat_embed_skip` counter increases).
- `JsonlMemoryStore` is an append-only archive. Deletions and changes to pin/unpin status are not replayed.
- Automatic extraction (`on_session_stop`) applies deduplication via `DedupAction.SKIP_NEW`, but manual writes intentionally bypass this deduplication.
- After retrieving embeddings, KNN nearest neighbors are searched; if an existing entry is found that is closer than the threshold for its `source_type`, the new entry is discarded (SKIP_NEW).
- If writing to JSONL fails with `OSError`, a warning is logged and processing continues (not treated as a fatal error since SQLite is the source of truth).

### Ops and Scoring

- If insertion into `memory_links` fails with `sqlite3.OperationalError`/`IntegrityError`, only a warning is logged and processing continues.

## Operational Notes

### Core and Store

- Write operations are in `write_ops.py`; read operations are in `store.py`.
- Chunk splitting occurs for content exceeding `memory_max_content_chars`. This is a limit per chunk, not on total content volume.

### Retrieval and Injection

- **Branch Awareness:** A hard SQL branch filter is applied if a non-empty branch is specified (`AND (? = '' OR m.branch = '' OR m.branch = ?)`).
- Entries with `branch=""` (Global Memory) are always included regardless of the current branch.
- If `get_repo_info()` fails or HEAD is detached, the branch defaults to `""` (safe degradation).
- KNN deduplication during ingestion uses `branch=""` (global scope) to ensure cross-branch duplicate detection.
- Snippets are subject to PII filtering and length limits (integrated with `snippet_filter.py`).

### Extraction and Facade

- Current mode can be checked with `/memory status` (Disabled / FTS-only / Degraded / Hybrid).
- `get_stats()` contains the following keys: total, semantic, episodic, by_source, embed_skip, last_retrieval_mode, fts_fallback_count.
- If embedding retrieval fails, the `stat_embed_skip` counter increases and is logged in the summary of `on_session_stop()`.

### Ops and Scoring

- `import_from_jsonl()` imports entries from a JSONL archive into SQLite. Deletions and changes to pin/unpin status are not replayed.
- Use `rebuild_fts()` to rebuild the FTS5 index and `rebuild_vec()` to rebuild the vector index.

## Known Limitations

- If a single source message is split into multiple chunks, each appears as an independent hit during search (fragmentation).

## Keywords

- agent
- memory
- module-reference
- types
- store
- retrieval-injection
- extraction-facade
- write-ops
- scoring
- rrf
