---
title: "Memory Layer - Module Reference: Core and Store"
area: agent
tags:
  - agent
  - memory
  - module-reference
  - types
  - store
related:
  - 05_agent_00_document-guide.md
  - 05_agent_12_01_memory-overview-and-modes.md
  - 05_agent_12_02_memory-gate-data-model-search.md
  - 05_agent_12_04_memory-module-ref-retrieval-and-injection.md
  - 05_agent_12_05_memory-module-ref-extraction-and-facade.md
  - 05_agent_12_06_memory-module-ref-ops-and-scoring.md
source:
  - 05_agent_12_03_memory-module-ref-core-and-store.md
---


# Memory Layer — Module Reference: Core and Store

- Operations and Observability $\rightarrow$ [05_agent_10_01_operations-and-observability-startup-and-health.md](05_agent_10_01_operations-and-observability-startup-and-health.md)
- Configuration $\rightarrow$ [05_agent_08_03_configuration-tools-memory.md](05_agent_08_03_configuration-tools-memory.md)

## Purpose

Defines the responsibility boundaries for core types, data models, and persistence stores within the memory layer.

## Design Intent

Since the memory layer is optional, all public APIs are designed to be safely guarded when `ctx.services.memory is None`. Core types are defined as immutable DTOs and are compatible with both JSONL and SQLite storage layers.

## Responsibility Boundary

- **Memory Layer owns:** Persistence, search, and injection of memory entries.
- **Memory Layer does NOT own:** LLM context generation, tool execution, or RAG document search.

## Key Constraints

- If `use_memory_layer = false` is set, the memory service is not constructed and all memory operations are completely bypassed.
- `VectorRetriever.knn_search()` raises an `OperationalError` if the `memories_vec` table does not exist (exceptions propagate if embeddings are enabled while tables are uninitialized).
- `MemoryStore.list_entries()` branch filtering behavior: uses `branch = '' OR branch = ?`, meaning entries with an empty string branch always match regardless of the specified branch value.
- `embed_dim` is not in `MemoryStore` itself; it is passed by the caller `agent/factory.py` (`MemoryStore(embed_dim=get_embedding_dims())` at line 380), sourced from `scripts/db/store_protocols.py::get_embedding_dims()` (a fixed code-level constant), not a config field.

## Operational Notes

- Write operations are in `write_ops.py`; read operations are in `store.py`.
- Chunk splitting occurs for content exceeding `memory_max_content_chars` (default: 500). This is a limit per chunk, not on total content volume.
- If a single source message is split into multiple chunks, each appears as an independent hit during search (fragmentation limitation).
- `RETENTION_DAYS` is defined but currently unreachable (dead code). See NC-007 for details.

## Known Limitations

- Enterprise filters based on `RETENTION_DAYS` retention period are currently unreachable (NC-007).
- If a single source message is split into multiple chunks, each appears as an independent hit during search (fragmentation).

## Related Docs

- `05_agent_00_document-guide.md`
- `05_agent_12_01_memory-overview-and-modes.md`
- `05_agent_12_02_memory-gate-data-model-search.md`
- `05_agent_12_04_memory-module-ref-retrieval-and-injection.md`
- `05_agent_12_05_memory-module-ref-extraction-and-facade.md`
- `05_agent_12_06_memory-module-ref-ops-and-scoring.md`
