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

- Current mode can be checked with `/memory status`.
- If embeddings are unavailable, the system falls back to FTS only (no manual intervention required).

## Known Limitations

None currently known.

## Data Model

### MemoryEntry (Stored in JSONL + SQLite)

A `MemoryEntry` is typed `semantic` / `episodic` and sourced `rule` / `conversation` / `decision` / `failure`. It carries the provenance session/turn, the `project` / `repo` / `branch` context filters, `content` and `summary`, `tags`, an `importance` score (0.0-1.0; higher means higher search priority), a `pinned` flag (pinned entries are injected at every session start) and UTC timestamps (schema: `MemoryEntry` in the memory module).

> **Branch filtering:** When a non-empty branch is specified, search includes ONLY the following via hard SQL filtering:
> - Memories where `branch = ''` (Global memories, always included)
> - Memories where `branch = <current branch>`
>
> Memories from other branches are completely excluded (not just deprioritized).

Storage ownership (SQLite as source of truth, FTS/vector as derived indexes, JSONL as archive) is defined in [agent_09_01](agent_09_01_data-layer-session-db.md).

### MemorySnippet (Injected into LLM Context)

A `MemorySnippet` is the formatted text with a memory-type prefix, its `semantic` / `episodic` source, and the relevance score (RRF merge rank or FTS5 rank).

## JSONL Format

Each line of the JSONL store is one JSON object: either a full serialized `MemoryEntry` or a change event (`delete`, `pin`, `unpin`) carrying an `event` field, `memory_id` and a UTC timestamp.

**Characteristics:**
- Append-only: existing lines are never modified or deleted. SQLite remains the authoritative source of truth; JSONL is a non-authoritative archive.
- One entry per line, UTF-8, each line valid JSON. The path is controlled by `memory_jsonl_dir` (filename `memories.jsonl`).

> **Implementation Note (Explicit in code — `scripts/agent/memory/jsonl_store.py`):** `read_all()` is limited to auditing, exporting, and initial import; do NOT use it to rebuild authoritative state. Use `MemoryStore` directly or restore from a SQLite backup. Rebuilding with `import_ops.import_from_jsonl()` is a destructive operation: it deletes all rows in `memories` / `memories_fts` / `memories_vec` / `memory_links` before re-inserting the final state computed by replaying the JSONL lines in order (a `delete` event removes the entry unless a later memory line re-adds it; `pin` / `unpin` update `pinned` when the entry exists; unparsable lines are skipped with a warning). A delete or pin change with no change event in the archive is not reproduced. To fix inconsistencies between FTS/vec and SQLite, use `rebuild_ops.rebuild_fts()` / `rebuild_vec()`.

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
- JSONL format
- FTS5
- KNN
- hybrid RRF
- disabled behavior
