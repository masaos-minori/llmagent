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
  - agent_10_01_operations-and-observability-startup-and-health.md
  - agent_08_03_configuration-tools-memory.md
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

- Gate behavior (`use_memory_layer = false` bypass, `VectorRetriever.knn_search()` raising `OperationalError` when `memories_vec` is missing) is defined in [agent_11_02](agent_11_02_memory-gate-data-model-search.md).

### Core and Store

- `MemoryStore.list_entries()` branch filtering behavior: uses `branch = '' OR branch = ?`, meaning entries with an empty string branch always match regardless of the specified branch value.
- `embed_dim` is not in `MemoryStore` itself; it is passed by the caller `agent/factory.py` (`MemoryStore(embed_dim=get_embedding_dims())`), sourced from `scripts/db/store_protocols.py::get_embedding_dims()` (a fixed code-level constant), not a config field.

### Retrieval and Injection

- `HybridRetriever.search()` performs FTS only if embeddings are unavailable; otherwise, it performs RRF merging.
- Default `InjectionPolicy`: `max_semantic` (semantic memories per turn), `max_episodic` (episodic memories per turn), `min_importance` (importance threshold), `max_snippet_length` (characters per snippet); values: see `InjectionPolicy` in `scripts/agent/memory/injection.py`.
- `knn_search` uses L2/Euclidean distance metric (explicit `distance_metric=L2` in vec0 DDL).

### Extraction and Facade

- When `EmbeddingClient.enabled=False`, `fetch()` returns `EmbeddingResult(success=False, error_kind=DISABLED)` immediately without making an HTTP call.
- `JsonlMemoryStore` is an append-only archive of memory lines and change events (`delete`, `pin`, `unpin`); lines without an `event` field are memory lines, and existing lines are never rewritten.
- Automatic extraction (`on_session_stop`) discards a new entry (`DedupAction.SKIP_NEW`) when an existing entry is closer than the threshold for its `source_type`; manual writes intentionally bypass this deduplication.
- If writing to JSONL fails with `OSError`, a warning is logged and processing continues (not treated as a fatal error since SQLite is the source of truth).

### Ops and Scoring

- If insertion into `memory_links` fails with `sqlite3.OperationalError`/`IntegrityError`, only a warning is logged and processing continues.

## Operational Notes

### Core and Store

- There is no session-scoped memory deletion: memory is independent of the source session, so rows are removed only per memory (`delete`) or by retention (`/memory prune`).
- Retrieval for injection excludes memories whose provenance `session_id` equals the current session, because that session's restored history is already in context.
- Chunk splitting occurs for content exceeding `memory_max_content_chars`. This is a limit per chunk, not on total content volume.

### Retrieval and Injection

- **Branch Awareness:** A hard SQL branch filter is applied if a non-empty branch is specified (`AND (? = '' OR m.branch = '' OR m.branch = ?)`).
- Entries with `branch=""` (Global Memory) are always included regardless of the current branch.
- If `get_repo_info()` fails or HEAD is detached, the branch defaults to `""` (safe degradation).
- KNN deduplication during ingestion uses `branch=""` (global scope) to ensure cross-branch duplicate detection.
- Snippets are subject to PII filtering and length limits (integrated with `snippet_filter.py`).

### Extraction and Facade

- Current mode and counters (including embed-skip) are shown by `/memory status`; the embed-skip count is also logged in the `on_session_stop()` summary.

### Ops and Scoring

- `import_from_jsonl()` replays the JSONL archive to compute and import the final state (replay rules: [agent_11_02](agent_11_02_memory-gate-data-model-search.md)).
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
