---
title: "Memory Layer — Module Reference"
category: agent
tags:
  - agent
  - agent
  - memory
  - semantic
  - episodic
  - embedding
related:
  - 05_agent_00_document-guide.md
---

# Memory Layer — Module Reference

## Module Reference

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

## Related Documents

- `agent`
- `memory`
- `semantic`

## Keywords

agent
memory
semantic
episodic
embedding
