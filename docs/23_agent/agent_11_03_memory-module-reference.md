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

Defines the responsibility boundaries of the Episodic Memory Layer's modules: core types and the SQLite store; search (FTS5 + KNN + hybrid) and lifecycle injection; rule-based extraction, the HTTP embedding client and the facade; scoring, RRF merging and the FTS5 query builder. The JSONL, import, rebuild, pin, and manual-write modules are retired by ADR-008 (see Retired by ADR-008).

## Design Intent

Since the Episodic Memory Layer is optional, all public APIs are designed to be safely guarded when `ctx.services.memory is None`. Core types are defined as immutable DTOs stored in SQLite.

## Responsibility Boundary

- **Episodic Memory Layer owns:** Persistence, search, and injection of Episodic Memory entries.
- **Episodic Memory Layer does NOT own:** LLM context generation, tool execution, or RAG document search.

## Key Constraints

### Common

- Gate behavior (`use_memory_layer = false` bypass, `VectorRetriever.knn_search()` raising `OperationalError` when `memories_vec` is missing) is defined in [agent_11_02](agent_11_02_memory-gate-data-model-search.md).

### Core and Store

- `MemoryStore.list_entries()` branch filtering behavior: uses `branch = '' OR branch = ?`, meaning entries with an empty string branch always match regardless of the specified branch value.
- `embed_dim` is not in `MemoryStore` itself; it is passed by the caller `agent/factory.py` (`MemoryStore(embed_dim=get_embedding_dims())`), sourced from `scripts/db/store_protocols.py::get_embedding_dims()` (a fixed code-level constant), not a config field.

### Retrieval and Injection

- `HybridRetriever.search()` performs FTS only if embeddings are unavailable; otherwise, it performs RRF merging.
- Default `InjectionPolicy`: `max_episodic` (episodic memories per turn) and `max_snippet_length` (characters per snippet); values: see `InjectionPolicy` in `scripts/agent/memory/injection.py`. The semantic count and the importance threshold belong to the retired dual model (SHARED-003).
- `knn_search` uses L2/Euclidean distance metric (explicit `distance_metric=L2` in vec0 DDL).

### Extraction and Facade

- When `EmbeddingClient.enabled=False`, `fetch()` returns `EmbeddingResult(success=False, error_kind=DISABLED)` immediately without making an HTTP call.
- Automatic extraction (`on_session_stop`) discards a new entry (`DedupAction.SKIP_NEW`) when an existing entry is closer than the threshold for its `source_type`.

### Ops and Scoring

- If insertion into `memory_links` fails with `sqlite3.OperationalError`/`IntegrityError`, only a warning is logged and processing continues.

## Operational Notes

### Core and Store

- There is no session-scoped memory deletion: Episodic Memory is independent of the source session and is retained internally (state-aware per event type; period values undecided, SHARED-005).
- Retrieval for injection excludes memories whose provenance `session_id` equals the current session, because that session's restored history is already in context.
- Chunk splitting occurs for content exceeding `memory_max_content_chars`. This is a limit per chunk, not on total content volume.

### Retrieval and Injection

- **Branch Awareness:** A hard SQL branch filter is applied if a non-empty branch is specified (`AND (? = '' OR m.branch = '' OR m.branch = ?)`).
- Entries with `branch=""` (Global Memory) are always included regardless of the current branch.
- If `get_repo_info()` fails or HEAD is detached, the branch defaults to `""` (safe degradation).
- KNN deduplication during ingestion uses `branch=""` (global scope) to ensure cross-branch duplicate detection.
- Snippets are subject to PII filtering and length limits (integrated with `snippet_filter.py`).

### Extraction and Facade

- Mode and counters (including embed-skip) are reported by `/stats` once the diagnostics are implemented (SHARED-003); the embed-skip count is also logged in the `on_session_stop()` summary.

### Ops and Scoring

- Use `rebuild_fts()` to rebuild the FTS5 index and `rebuild_vec()` to rebuild the vector index.

## Retired by ADR-008

These modules belong to the retired dual memory model and the JSONL archive. They exist in code only until SHARED-003 is resolved and are not supported API:

- the JSONL store (`jsonl_store.py`)
- the JSONL import (`import_ops.py`)
- the rebuild operations (`rebuild_ops.py`)
- the pin operations (`pin_ops.py`)
- the manual-write operations (`write_ops.py`)

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
