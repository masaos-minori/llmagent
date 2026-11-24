---
title: "Memory Layer — Activation Gate, Data Model, and Search"
area: agent
tags:
  - agent
  - memory
  - search
related:
  - agent_11_01_memory-overview-and-modes.md
  - agent_11_03_memory-module-reference.md
  - agent_00_document-guide.md
  - agent_10_01_operations-and-observability-startup-and-health.md
  - agent_08_03_configuration-tools-memory.md
---
# Memory Layer — Activation Gate, Data Model, and Search

- Operations and Observability → [agent_10_01_operations-and-observability-startup-and-health.md](agent_10_01_operations-and-observability-startup-and-health.md)
- Configuration → [agent_08_03_configuration-tools-memory.md](agent_08_03_configuration-tools-memory.md)

## Purpose

Defines the three layers of activation gates that control the timing of memory operation execution, and how each module behaves when disabled.

## Design Intent

The memory layer is controlled by three independent gates: complete bypass via a config flag, phased fallback via embedding client enablement, and a single entry point via a facade. This ensures the implementation guarantee that the memory layer remains optional.

## Responsibility Boundary

- **Memory Layer owns:** Memory operation lifecycle (injection at session start, response to user prompts, extraction at session end).
- **Memory Layer does NOT own:** LLM context generation, tool execution, or RAG document search.

## Key Constraints

- If `use_memory_layer = false` is set, the memory service is not constructed and all memory operations are completely bypassed.
- If the embedding endpoint is unavailable, `HybridRetriever.search()` falls back to FTS5 only.
- `VectorRetriever.knn_search()` raises an `OperationalError` if the `memories_vec` table does not exist (exceptions propagate if embeddings are enabled while tables are uninitialized).

## Operational Notes

- The current retrieval mode is reported by `/stats` once the diagnostics are implemented (SHARED-003).
- If embeddings are unavailable, the system falls back to FTS only (no manual intervention required).

## Known Limitations

None currently known.

## Data Model

### MemoryEntry (Stored in SQLite)

A `MemoryEntry` carries the provenance session/turn, the `project` / `repo` / `branch` context filters, `content` and `summary`, `tags`, and UTC timestamps (schema: `MemoryEntry` in the memory module). The initial Episodic event types are `failure`, `resolution`, `review_finding`, `investigation_result`, `work_result`, and `decision_history` (agent_11_01), and the code still carries fields of the retired dual model (SHARED-003).

> **Branch filtering:** When a non-empty branch is specified, search includes ONLY the following via hard SQL filtering:
> - Memories where `branch = ''` (Global memories, always included)
> - Memories where `branch = <current branch>`
>
> Memories from other branches are completely excluded (not just deprioritized).

Storage ownership (SQLite as source of truth, FTS/vector as derived indexes, no JSONL) is defined in [agent_09_01](agent_09_01_data-layer-session-db.md).

### MemorySnippet (Injected into LLM Context)

A `MemorySnippet` is the formatted text and the relevance score (RRF merge rank or FTS5 rank).

## Search Strategies

### FTS5 (Full-Text Search)

- **Engine:** SQLite FTS5 with BM25 ranking
- **Index:** Tokenized `content` column in `memories_fts`
- **Fallback:** Used when `EmbeddingClient.enabled=False` or when embeddings are not returned
- **Strengths:** Exact keyword matching, no API dependency, fast for small datasets
- **Weaknesses:** No semantic understanding

### KNN (K-Nearest Neighbors)

- **Engine:** sqlite-vec extension using L2 distance
- **Index:** Dense embedding vectors in `memories_vec`
- **Requirements:** `EmbeddingClient.enabled=True` along with a valid embedding API endpoint
- **Strengths:** Semantic similarity matching, language agnostic
- **Weaknesses:** Requires embedding API calls, requires loading the `sqlite-vec` extension

### Hybrid (RRF Merge)

- **Engine:** Integrates FTS5 and KNN results using Reciprocal Rank Fusion (RRF)
- **Formula:** `rrf_score = 1.0 / (k + rank + 1)`. Where `k` is `memory_rrf_k` (value: see `MemoryConfig` in `scripts/agent/config_dataclasses.py`) and `rank` is 0-indexed
- **Result:** De-duplicated and sorted by descending RRF score
- **Strengths:** Benefits from both methods regardless of query type
- **Weaknesses:** High latency (two searches + merge). Requires embedding API

---

## Disabled Behavior

- `use_memory_layer=False` → `ctx.services.memory` is `None`, skipping all memory operations.
- `EmbeddingClient.enabled=False` → `fetch()` returns a `DISABLED` error, falling back to FTS5 search.

## Keywords

- activation gate
- disabled behavior by module
- MemoryEntry
- MemorySnippet
- FTS5
- KNN
- hybrid RRF
- disabled behavior
