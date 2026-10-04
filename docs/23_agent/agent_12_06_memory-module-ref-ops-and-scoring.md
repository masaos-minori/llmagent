---
title: "Memory Layer - Module Reference: Ops and Scoring"
area: agent
tags:
  - agent
  - memory
  - module-reference
  - write-ops
  - scoring
  - rrf
related:
  - agent_00_document-guide.md
  - agent_12_01_memory-overview-and-modes.md
  - agent_12_02_memory-gate-data-model-search.md
  - agent_12_03_memory-module-ref-core-and-store.md
  - agent_12_04_memory-module-ref-retrieval-and-injection.md
  - agent_12_05_memory-module-ref-extraction-and-facade.md
---

# Memory Layer — Module Reference: Ops and Scoring

- Operations and Observability $\rightarrow$ [agent_10_01_operations-and-observability-startup-and-health.md](agent_10_01_operations-and-observability-startup-and-health.md)
- Configuration $\rightarrow$ [agent_08_03_configuration-tools-memory.md](agent_08_03_configuration-tools-memory.md)

## Purpose

Defines the responsibility boundaries for write operations, scoring, RRF merging, and the FTS5 query builder within the memory layer.

## Design Intent

Same as in [agent_12_03_memory-module-ref-core-and-store.md](agent_12_03_memory-module-ref-core-and-store.md) (memory layer is optional: guarded public APIs and shared immutable DTOs).

## Responsibility Boundary

Same as in [agent_12_03_memory-module-ref-core-and-store.md](agent_12_03_memory-module-ref-core-and-store.md) (the Memory Layer owns persistence, search and injection of memory entries).

## Key Constraints

- Common constraints (`use_memory_layer = false` bypass; `VectorRetriever.knn_search()` on a missing `memories_vec` table): see Key Constraints in [agent_12_03_memory-module-ref-core-and-store.md](agent_12_03_memory-module-ref-core-and-store.md).
- Embedding, deduplication and archive-write constraints: see Key Constraints in [agent_12_05_memory-module-ref-extraction-and-facade.md](agent_12_05_memory-module-ref-extraction-and-facade.md).
- After retrieving embeddings, the top 5 nearest neighbors via KNN are searched; if an existing entry is found that is closer than the threshold for its `source_type`, the new entry is discarded (SKIP_NEW).
- If insertion into `memory_links` fails with `sqlite3.OperationalError`/`IntegrityError`, only a warning is logged and processing continues.

## Operational Notes

- Current mode can be checked with `/memory status` (Disabled / FTS-only / Degraded / Hybrid).
- `get_stats()` contains the following keys: total, semantic, episodic, by_source, embed_skip, last_retrieval_mode, fts_fallback_count.
- If embedding retrieval fails, the `stat_embed_skip` counter increases and is logged in the summary of `on_session_stop()`.
- `import_from_jsonl()` imports entries from a JSONL archive into SQLite. Deletions and changes to pin/unpin status are not replayed.
- Use `rebuild_fts()` to rebuild the FTS5 index and `rebuild_vec()` to rebuild the vector index.

## Known Limitations

Same as in [agent_12_03_memory-module-ref-core-and-store.md](agent_12_03_memory-module-ref-core-and-store.md) (chunk fragmentation in search hits).

## Keywords

- agent
- memory
- module-reference
- write-ops
- scoring
- rrf
