---
title: "Memory Layer - Module Reference: Ops and Scoring"
category: agent
tags:
  - agent
  - memory
  - module-reference
  - write-ops
  - scoring
  - rrf
related:
  - 05_agent_00_document-guide.md
  - 05_agent_12_01_memory-overview-and-modes.md
  - 05_agent_12_02_memory-gate-data-model-search.md
  - 05_agent_12_03_memory-module-ref-core-and-store.md
  - 05_agent_12_04_memory-module-ref-retrieval-and-injection.md
  - 05_agent_12_05_memory-module-ref-extraction-and-facade.md
source:
  - 05_agent_12_memory.md
---

# Memory Layer — Module Reference

- Operations and observability → [05_agent_10_01_operations-and-observability-startup-and-health.md](05_agent_10_01_operations-and-observability-startup-and-health.md)
- Configuration → [05_agent_08_03_configuration-tools-memory.md](05_agent_08_03_configuration-tools-memory.md)

### 14. `mapper.py` — Row conversion utils

| Function | Returns | Description |
|---|---|---|
| `row_to_entry(dict)` | `MemoryEntry` | SQLite row to MemoryEntry |

Internal helper functions for float-to-BLOB conversion, timestamp stamping, and ISO 8601 timestamp generation.

### 15. `write_ops.py` — Write operations

| Function | Returns | Description |
|---|---|---|
| `add(entry, embedding=None, embed_dim=None)` | `None` | Insert + FTS sync; BEGIN IMMEDIATE for atomicity. When `embedding` is provided, also writes to memories_vec. |
| `upsert(entry, embedding=None, embed_dim=None)` | `None` | Insert-or-replace + FTS sync. When `embedding` is provided, also upserts memories_vec. |
| `delete(memory_id)` | `bool` | Remove entry by ID |
| `clear_by_session(session_id)` | `int` | Bulk delete for one session |

### 16. `pin_ops.py` — Pin/unpin operations

| Function | Returns | Description |
|---|---|---|
| `pin(memory_id, conn=None)` | `bool` | Set pinned=1; returns True when found. When `conn` is provided, uses that connection (caller must commit). |
| `unpin(memory_id, conn=None)` | `bool` | Set pinned=0; returns True when found. When `conn` is provided, uses that connection (caller must commit). |

### 17. `count_ops.py` — Diagnostic counts

| Function | Returns | Description |
|---|---|---|
| `count_entries()` | `int` | Row count in memories table (diagnostic) |
| `count_by_type()` | `dict[str, int]` | {memory_type: count} for all rows (diagnostic) |
| `count_by_source_type()` | `dict[str, int]` | {source_type: count} for all rows (diagnostic) |
| `count_vec()` | `int` | Row count in memories_vec (raises OperationalError if unavailable) |
| `count_prunable(days)` | `int` | Count of entries older than `days` days |

### 18. `rebuild_ops.py` — Rebuild operations

| Function | Returns | Description |
|---|---|---|
| `rebuild_fts()` | `int` | Rebuild FTS5 index from memories table; returns row count inserted |
| `rebuild_vec()` | `int` | Rebuild vec index from memories table; returns row count inserted |

### 19. `import_ops.py` — Import operations

| Function | Returns | Description |
|---|---|---|
| `import_from_jsonl(jsonl_store, *, dry_run=False, embed_dim=None)` | `tuple[int, int]` | Import entries from JSONL archive into SQLite; returns (jsonl_count, inserted_count). When `dry_run=True`, returns counts without inserting. Does NOT replay deletes or pin/unpin state changes. |

### 20. `scoring.py` — BM25 scoring with boosts

**Constants:**
- `_PIN_BOOST = 0.3` — pin boost for pinned entries
- `_IMPORTANCE_BOOST_SCALE = 0.5` — scale factor for importance (importance × 0.5)
- `_RECENCY_MAX_BOOST = 0.2` — max recency boost for entries within 7 days
- `_CONTEXT_MATCH_BOOST = 0.1` — base context match boost for project/repo matches
- `_RECENCY_DAYS = 7.0` — recency window in days

| Function / Constant | Returns | Description |
|---|---|---|
| `score(bm25_rank, entry, project, repo[, recency_days, branch])` | `float` | Combined score: `-bm25_rank + importance_boost + pin_boost + recency_decay + context_match`. Formula: `score = -bm25_rank + (importance_w × importance × 0.5) + (0.3 if pinned else 0) + (recency_w × recency_boost(created_at)) + context_boost(entry, project, repo, branch)` |
| `recency_boost(created_at[, recency_days])` | `float` | Boost inversely proportional to entry age: `_RECENCY_MAX_BOOST × (1 - age_days / recency_days)`, returns 0.0 when age ≥ recency_days |
| `context_boost(entry, project, repo[, branch])` | `float` | Branch match: 0.15; project/repo match: 0.1; no match: 0.0 |

### 21. `rrf.py` — Reciprocal Rank Fusion merge

| Constant / Function | Returns | Description |
|---|---|---|
| `RRF_K` | `60` | Reciprocal rank fusion constant |
| `rrf_merge(hit_lists, k=60)` | `list[MemoryHit]` | Merge multiple ranked hit lists by rank position using RRF scoring (each list contributes 1.0 / (k + rank + 1)) |

### 22. `fts_query.py` — FTS5 query builder

| Function / Constant | Returns | Description |
|---|---|---|
| `build_fts_query(text: str)` | `str` | Build FTS5 MATCH query with token quoting |

### 23. `sql_constants.py` — SQL constants

Internal helper module; no public API.

---

## Related Documents

- `05_agent_00_document-guide.md`
- `05_agent_12_01_memory-overview-and-modes.md`
- `05_agent_12_02_memory-gate-data-model-search.md`
- `05_agent_12_03_memory-module-ref-core-and-store.md`
- `05_agent_12_04_memory-module-ref-retrieval-and-injection.md`
- `05_agent_12_05_memory-module-ref-extraction-and-facade.md`

## Keywords

mapper.py
write_ops.py
pin_ops.py
count_ops.py
rebuild_ops.py
import_ops.py
scoring.py
rrf.py
fts_query.py
sql_constants.py
