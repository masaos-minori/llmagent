---
title: "Memory Layer — Module Reference: Retrieval and Injection"
area: agent
tags:
  - agent
  - memory
  - retrieval-injection
related:
  - 05_agent_12_01_memory-overview-and-modes.md
  - 05_agent_12_03_memory-module-ref-core-and-store.md
  - 05_agent_12_05_memory-module-ref-extraction-and-facade.md
---
# Memory Layer — Module Reference: Retrieval and Injection

- Operations and Observability $\rightarrow$ [05_agent_10_01_operations-and-observability-startup-and-health.md](05_agent_10_01_operations-and-observability-startup-and-health.md)
- Configuration $\rightarrow$ [05_agent_08_03_configuration-tools-memory.md](05_agent_08_03_configuration-tools-memory.md)

## Purpose

Defines the responsibility boundaries for memory searching (FTS5 + KNN + Hybrid), lifecycle injection, and extraction + deduplication + persistence.

## Design Intent

Since the memory layer is optional, all public APIs are designed to be safely guarded when `ctx.services.memory is None`. Core types are defined as immutable DTOs and are compatible with both JSONL and SQLite storage layers.

## Responsibility Boundary

- **Memory Layer owns:** Persistence, search, and injection of memory entries.
- **Memory Layer does NOT own:** LLM context generation, tool execution, or RAG document search.

## Key Constraints

- If `use_memory_layer = false` is set, the memory service is not constructed and all memory operations are completely bypassed.
- `VectorRetriever.knn_search()` raises an `OperationalError` if the `memories_vec` table does not exist (exceptions propagate if embeddings are enabled while tables are uninitialized).
- `HybridRetriever.search()` performs FTS only if embeddings are unavailable; otherwise, it performs RRF merging.
- Default `InjectionPolicy`: `max_semantic=5`, `max_episodic=3`, `min_importance=0.5`, `max_snippet_length=500`.
- If embedding retrieval fails, processing continues and the entry is saved without embeddings (`stat_embed_skip` counter increases).
- Automatic extraction (`on_session_stop`) applies deduplication via `DedupAction.SKIP_NEW`, but manual writes intentionally bypass this deduplication.
- `knn_search` uses L2/Euclidean distance metric (explicit `distance_metric=L2` in vec0 DDL).

## Operational Notes

- **Branch Awareness:** A hard SQL branch filter is applied if a non-empty branch is specified (`AND (? = '' OR m.branch = '' OR m.branch = ?)`).
- Entries with `branch=""` (Global Memory) are always included regardless of the current branch.
- If `get_repo_info()` fails or HEAD is detached, the branch defaults to `""` (safe degradation).
- KNN deduplication during ingestion uses `branch=""` (global scope) to ensure cross-branch duplicate detection.
- Snippets are subject to PII filtering and length limits (integrated with `snippet_filter.py`).
- If a single source message is split into multiple chunks, each appears as an independent hit during search (fragmentation limitation).

## Known Limitations

- If a single source message is split into multiple chunks, each appears as an independent hit during search (fragmentation).
- Enterprise filters based on `RETENTION_DAYS` retention period are currently unreachable (NC-007).

## Related Docs

- `05_agent_00_document-guide.md`
- `05_agent_12_01_memory-overview-and-modes.md`
- `05_agent_12_02_memory-gate-data-model-search.md`
- `05_agent_12_03_memory-module-ref-core-and-store.md`
- `05_agent_12_05_memory-module-ref-extraction-and-facade.md`
- `05_agent_12_06_memory-module-ref-ops-and-scoring.md`
