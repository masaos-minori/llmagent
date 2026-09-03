---
title: "Memory Layer — Activation Gate, Data Model, and Search (Part 1)"
area: agent
tags:
  - agent
  - memory
  - search
related:
  - 05_agent_12_01_memory-overview-and-modes.md
  - 05_agent_12_03_memory-module-ref-core-and-store.md
---
# Memory Layer — Activation Gate, Data Model, and Search (Part 1)

- Operations and Observability $\rightarrow$ [05_agent_10_01_operations-and-observability-startup-and-health.md](05_agent_10_01_operations-and-observability-startup-and-health.md)
- Configuration $\rightarrow$ [05_agent_08_03_configuration-tools-memory.md](05_agent_08_03_configuration-tools-memory.md)

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
- `DEDUP_THRESHOLDS` is consumed in `ingestion.py` as deduplication thresholds per `source_type`.
- `RETENTION_DAYS` is defined but currently unreachable (dead code). See NC-007 for details.

## Known Limitations

- Enterprise filters based on `RETENTION_DAYS` retention period are currently unreachable (NC-007).

## Related Docs

- `05_agent_00_document-guide.md`
- `05_agent_12_01_memory-overview-and-modes.md`
- `05_agent_12_03_memory-module-ref-core-and-store.md`
- `05_agent_12_04_memory-module-ref-retrieval-and-injection.md`
- `05_agent_12_05_memory-module-ref-extraction-and-facade.md`
- `05_agent_12_06_memory-module-ref-ops-and-scoring.md`
- `05_agent_12_02_memory-gate-data-model-search.md`


# Memory Layer — Module Reference

- Operations and Observability $\rightarrow$ [05_agent_10_01_operations-and-observability-startup-and-health.md](05_agent_10_01_operations-and-observability-startup-and-health.md)
- Configuration $\rightarrow$ [05_agent_08_03_configuration-tools-memory.md](05_agent_08_03_configuration-tools-memory.md)

## Data Model

### MemoryEntry (Stored in JSONL + SQLite)

| Field | Type | Description |
|---|---|---|
| `memory_id` | `str` | UUID v4, Primary Key |
| `memory_type` | `MemoryType` | `"semantic"` \| `"episodic"` |
| `source_type` | `SourceType` | `"rule"` \| `"conversation"` \| `"decision"` \| `"failure"` (Note: Actual values in `StrEnum` are lowercase. This table uses capitalized names for legacy categorization; refer to `agent/memory/types.py` for actual values.) |
| `session_id` | `int \| None` | Parent session ID |
| `turn_id` | `str \| None` | UUID linking to the originating conversation turn |
| `project` | `str` | Project name for context filtering |
| `repo` | `str` | Repository name for context filtering |
| `branch` | `str` | Git branch for context filtering |

> **Current Behavior:** When a non-empty branch is specified, search includes ONLY the following via hard SQL filtering:
> - Memories where `branch = ''` (Global memories, always included)
> - Memories where `branch = <current branch>`
>
> Memories from other branches are completely excluded (not just deprioritized).

| `content` | `str` | Full text of the message |
| `summary` | `str` | Short summary of the content |
| `tags` | `list[str]` | Keyword tags for classification |
| `importance` | `float` | 0.0–1.0. Higher means higher search priority (Default: 0.5) |
| `pinned` | `bool` | If `True`, injected at every session start |
| `created_at` | `str` | ISO 8601 UTC timestamp. Set by `write_ops.add()` |
| `updated_at` | `str` | ISO 8601 UTC timestamp |

**DB Mapping:** Stored in the `memories` table (SQLite), and one line per entry is written to the JSONL file. The FTS5 index is in `memories_fts`. The vector index is in `memories_vec` (if embeddings are enabled).

### MemorySnippet (Injected into LLM Context)

| Field | Type | Description |
|---|---|---|
| `text` | `str` | Formatted string with the memory type prefix (e.g., `"[Semantic memory] ..."`) |
| `source` | `str` | `"semantic"` \| `"episodic"` |
| `score` | `float` | Relevance score from search (RRF merge rank or FTS5 rank) |

---

## JSONL Format

Each line in the JSONL store is a single JSON object serializing all `MemoryEntry` fields.

```json
{"memory_id": "uuid-here", "memory_type": "semantic", "source_type": "rule", "session_id": 1, "turn_id": null, "project": "myproj", "repo": "myrepo", "branch": "main", "content": "Use orjson for JSON.", "summary": "orjson preference", "tags": [], "importance": 0.7, "pinned": false, "created_at": "2026-06-19T23:00:00Z", "updated_at": "2026-06-19T23:00:00Z"}
```

**Characteristics:**
- Append-only: Entries within the file are not modified or deleted (`agent/memory/jsonl_store.py` docstring: "JSONL does NOT record mutations (delete, pin, unpin); SQLite is the authoritative source of truth")
- One entry per line. UTF-8 encoded. Each line is valid JSON.
- File path is controlled by `memory_jsonl_dir` config (Filename: `memories.jsonl`)
- Authoritative data: SQLite indexes can be rebuilt from JSONL if necessary.

> **Implementation Note (Explicit in code):** The `jsonl_store.py` docstring explicitly states that SQLite (via `MemoryStore`) is the authoritative source of truth, and JSONL is an append-only archive. `read_all()` is limited to auditing, exporting, and initial import; do NOT use it to rebuild authoritative state. Use `MemoryStore` directly or restore from a SQLite backup. Rebuilding using `import_ops.import_from_jsonl()` is a destructive operation that deletes all rows in `memories` / `memories_fts` / `memories_vec` before re-inserting from JSONL; deletions and pin/unpin changes are not replayed (as they don't exist in the JSONL history). For fixing inconsistencies between FTS/vec and SQLite, use `rebuild_ops.rebuild_fts()` / `rebuild_vec()`.

---

## Search Strategies

### FTS5 (Full-Text Search)

- **Engine:** SQLite FTS5 with BM25 ranking
- **Index:** Tokenized `content` column in `memories_fts`
- **Fallback:** Used when `EmbeddingClient.enabled=False` or when embeddings are not returned
- **Strengths:** Exact keyword matching, no API dependency, fast for small datasets
- **Weaknesses:** No semantic understanding

### KNN (K-Nearest Neighbors)

- **Engine:** sqlite-vec extension using cosine similarity
- **Index:** Dense embedding vectors in `memories_vec`
- **Requirements:** `EmbeddingClient.enabled=True` along with a valid embedding API endpoint
- **Strengths:** Semantic similarity matching, language agnostic
- **Weaknesses:** Requires embedding API calls, requires loading the `sqlite-vec` extension

### Hybrid (RRF Merge)

- **Engine:** Integrates FTS5 and KNN results using Reciprocal Rank Fusion (RRF)
- **Formula:** `rrf_score = 1.0 / (k + rank + 1)`. Where `k=60` and `rank` is 0-indexed
- **Result:** De-duplicated and sorted by descending RRF score
- **Strengths:** Benefits from both methods regardless of query type
- **Weaknesses:** High latency (two searches + merge). Requires embedding API

---

## Disabled Behavior

For detailed breakdown by module, see the [Activation Gate section in 05_agent_12_02](05_agent_12_02_memory-gate-data-model-search.md#activation-gate) and the [Module-specific behavior when disabled table](05_agent_12_02_memory-gate-data-model-search.md#module-specific-behavior-when-disabled).

Overview:
- `use_memory_layer=False` $\rightarrow$ `ctx.services.memory` becomes `None`, skipping all memory operations.
- `EmbeddingClient.enabled=False` $\rightarrow$ `fetch()` returns a `DISABLED` error, falling back to FTS5 search.
- `cli_view.py` reflects the memory layer status in the startup banner.

---

## Related Documents

- `05_agent_00_document-guide.md`
- `05_agent_12_01_memory-overview-and-modes.md`
- `05_agent_12_03_memory-module-ref-core-and-store.md`
- `05_agent_12_04_memory-module-ref-retrieval-and-injection.md`
- `05_agent_12_05_memory-module-ref-extraction-and-facade.md`
- `05_agent_12_06_memory-module-ref-ops-and-scoring.md`
- `05_agent_12_02_memory-gate-data-model-search.md`

## Keywords

activation gate
disabled behavior by module
MemoryEntry
MemorySnippet
JSONL format
FTS5
KNN
hybrid RRF
disabled behavior
