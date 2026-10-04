---
title: "Memory Layer — Module Reference: Retrieval and Injection"
area: agent
tags:
  - agent
  - memory
  - retrieval-injection
related:
  - agent_12_01_memory-overview-and-modes.md
  - agent_12_03_memory-module-ref-core-and-store.md
  - agent_12_05_memory-module-ref-extraction-and-facade.md
---
# Memory Layer — Module Reference: Retrieval and Injection

- Operations and Observability $\rightarrow$ [agent_10_01_operations-and-observability-startup-and-health.md](agent_10_01_operations-and-observability-startup-and-health.md)
- Configuration $\rightarrow$ [agent_08_03_configuration-tools-memory.md](agent_08_03_configuration-tools-memory.md)

## Purpose

Defines the responsibility boundaries for memory searching (FTS5 + KNN + Hybrid), lifecycle injection, and extraction + deduplication + persistence.

## Design Intent

Same as in [agent_12_03_memory-module-ref-core-and-store.md](agent_12_03_memory-module-ref-core-and-store.md) (memory layer is optional: guarded public APIs and shared immutable DTOs).

## Responsibility Boundary

Same as in [agent_12_03_memory-module-ref-core-and-store.md](agent_12_03_memory-module-ref-core-and-store.md) (the Memory Layer owns persistence, search and injection of memory entries).

## Key Constraints

- Common constraints (`use_memory_layer = false` bypass; `VectorRetriever.knn_search()` on a missing `memories_vec` table): see Key Constraints in [agent_12_03_memory-module-ref-core-and-store.md](agent_12_03_memory-module-ref-core-and-store.md).
- Embedding, deduplication and archive-write constraints: see Key Constraints in [agent_12_05_memory-module-ref-extraction-and-facade.md](agent_12_05_memory-module-ref-extraction-and-facade.md).
- `HybridRetriever.search()` performs FTS only if embeddings are unavailable; otherwise, it performs RRF merging.
- Default `InjectionPolicy`: `max_semantic=5`, `max_episodic=3`, `min_importance=0.5`, `max_snippet_length=500`.
- `knn_search` uses L2/Euclidean distance metric (explicit `distance_metric=L2` in vec0 DDL).

## Operational Notes

- **Branch Awareness:** A hard SQL branch filter is applied if a non-empty branch is specified (`AND (? = '' OR m.branch = '' OR m.branch = ?)`).
- Entries with `branch=""` (Global Memory) are always included regardless of the current branch.
- If `get_repo_info()` fails or HEAD is detached, the branch defaults to `""` (safe degradation).
- KNN deduplication during ingestion uses `branch=""` (global scope) to ensure cross-branch duplicate detection.
- Snippets are subject to PII filtering and length limits (integrated with `snippet_filter.py`).
- If a single source message is split into multiple chunks, each appears as an independent hit during search (fragmentation limitation).

## Known Limitations

Same as in [agent_12_03_memory-module-ref-core-and-store.md](agent_12_03_memory-module-ref-core-and-store.md) (chunk fragmentation in search hits; `RETENTION_DAYS` filters unreachable).

## Related Docs

- `agent_00_document-guide.md`
- `agent_12_01_memory-overview-and-modes.md`
- `agent_12_02_memory-gate-data-model-search.md`
- `agent_12_03_memory-module-ref-core-and-store.md`
- `agent_12_05_memory-module-ref-extraction-and-facade.md`
- `agent_12_06_memory-module-ref-ops-and-scoring.md`

## Related Documents

- `agent_12_01_memory-overview-and-modes.md`
- `agent_12_03_memory-module-ref-core-and-store.md`
- `agent_12_05_memory-module-ref-extraction-and-facade.md`

## Keywords

- agent
- memory
- retrieval-injection
