---
title: "Memory Layer - Module Reference: Retrieval and Injection"
category: agent
tags:
  - agent
  - memory
  - module-reference
  - retriever
  - injection
  - ingestion
related:
  - 05_agent_00_document-guide.md
  - 05_agent_12_memory-overview-and-modes.md
  - 05_agent_12_memory-gate-data-model-search.md
  - 05_agent_12_memory-module-ref-core-and-store.md
  - 05_agent_12_memory-module-ref-extraction-and-facade.md
  - 05_agent_12_memory-module-ref-ops-and-scoring.md
source:
  - 05_agent_12_memory.md
---

# Memory Layer — Module Reference

- Operations and observability → [05_agent_10_operations-and-observability-startup-and-health.md](05_agent_10_operations-and-observability-startup-and-health.md)
- Configuration → [05_agent_08_configuration-tools-memory.md](05_agent_08_configuration-tools-memory.md)

### 7. `retriever.py` — Search (FTS5 + KNN + Hybrid)

| Class | Role |
|---|---|
| `FtsRetriever` | FTS5 BM25 search with importance / pin / recency rescoring |
| `VectorRetriever` | KNN search via sqlite-vec |
| `HybridRetriever` | Primary external interface — composes both with RRF merge |

**`HybridRetriever` attributes and methods:**

| Method / Attribute | Returns | Description |
|---|---|---|
| `search(query: MemoryQuery, embedding: list[float] | None = None, project="", repo="", branch="")` | `list[MemoryHit]` | FTS-only when no embedding; RRF merge when embedding present. Takes a `MemoryQuery` object (not raw string) — the query text is extracted from `query.query` internally. Sets `last_retrieval_mode` on return. |
| `knn_search(embedding, memory_type, limit, branch="")` | `list[MemoryHit]` | Delegate to VectorRetriever (used by ingestion dedup) |
| `top_semantic(limit=5, min_importance=0.0, project="", repo="", branch="")` | `list[MemoryEntry]` | Direct SQL — no FTS needed |
| `embed_client` | `EmbeddingClient \| None` | Injected at construction; used by `/memory status` |
| `last_retrieval_mode` | `str` | `"hybrid"` / `"fts_only"` / `"unknown"` — set on each `search()` call |
| `fts_fallback_count` | `int` | Count of FTS fallbacks during hybrid search |

**`FtsRetriever` methods and attributes:**

| Method / Attribute | Returns | Description |
|---|---|---|
| `search(query: MemoryQuery, project="", repo="", branch="")` | `list[MemoryHit]` | FTS5 BM25 search with rescoring. Returns [] on error or empty query. |
| `candidate_limit` | `int` | Maximum candidate results from FTS query |

**`VectorRetriever` methods:**

| Method | Returns | Description |
|---|---|---|
| `knn_search(embedding, memory_type, limit, branch="")` | `list[MemoryHit]` | KNN search; score is cosine similarity (higher-is-better). When embeddings disabled, returns []. |

**Scoring formula:**
```
score = -bm25_rank + importance_boost + pin_boost + recency_decay + context_match
```
- Semantic: importance_weight=1.0, recency_weight=0.5
- Episodic: importance_weight=0.5, recency_weight=1.0

**Failure modes:**
- `sqlite3.OperationalError` — vec table missing → KNN returns []
- `MemorySchemaError` — invalid created_at timestamp

**Branch Awareness:**

All retrieval paths apply a hard SQL branch filter when a non-empty branch is provided:

```sql
AND (? = '' OR m.branch = '' OR m.branch = ?)
```

- Branch is resolved once at startup via `shared.git_helper.get_repo_info()` in `factory.py`.
- Entries with `branch=""` (global memories) are always included regardless of current branch.
- When `get_repo_info()` fails or HEAD is detached, branch defaults to `""` — no filter is applied (safe degraded behavior).
- The injection service passes the resolved branch value to all `retriever.search()` calls.
- Dedup KNN in ingestion uses `branch=""` (global scope) to ensure cross-branch duplicate detection.

### 8. `injection.py` — Lifecycle injection service

Class `MemoryInjectionService(policy, retriever, embed_client, project="", repo="", branch="", enabled=False)`:

| Method | Returns | Description |
|---|---|---|
| `on_session_start()` | `list[MemorySnippet]` | Top semantic entries by importance (sync) |
| `on_user_prompt(query, session_id)` | `list[MemorySnippet]` | Semantic + episodic search with embedding (async) |

Uses `InjectionPolicy(max_semantic=5, max_episodic=3, min_importance=0.5)`.

**Failure modes:** `InjectionValidationError` when query is empty.

| Attribute / Method | Type / Returns | Default | Description |
|---|---|---|---|
| `max_semantic` | `int` | `5` | Max semantic snippets to inject |
| `max_episodic` | `int` | `3` | Max episodic snippets to inject |
| `min_importance` | `float` | `0.5` | Min importance threshold for retrieval |
| `format_prefix_semantic` | `str` | `"[Semantic memory]"` | Prefix for semantic snippets |
| `format_prefix_episodic` | `str` | `"[Episodic memory]"` | Prefix for episodic snippets |

**Failure modes:** `InjectionValidationError` when query is empty.

### 9. `ingestion.py` — Extraction + dedup + persist

Class `MemoryIngestionService(store, jsonl, retriever, embed_client=None, *, dedup_policy=None, project="", repo="", branch="", max_content_chars=500)`:

| Method / Attribute | Returns | Description |
|---|---|---|
| `on_session_stop(session_id, history, turn_id=None)` | `None` | Extract, dedup, persist from conversation history |
| `write_semantic(session_id, content)` | `None` | Manual persist (no dedup) |
| `write_episodic(session_id, content)` | `None` | Manual persist (no dedup) |
| `stat_embed_skip` | `int` | Counter of embeddings skipped due to errors |

Dedup: uses `DedupPolicy(action=SKIP_NEW, threshold=...)` with KNN near-duplicate detection.

**Failure modes:** `sqlite3.OperationalError` on memory_links insert (swallowed with warning).

**Embed failure tracking:** `stat_embed_skip` counter increments whenever a write operation stores an entry without embedding (embedding failed). Logged in `on_session_stop()` summary: `"MemoryIngestionService.on_session_stop: persisted %d entries; %d embed_skipped"`.

## Related Documents

- `05_agent_00_document-guide.md`
- `05_agent_12_memory-overview-and-modes.md`
- `05_agent_12_memory-gate-data-model-search.md`
- `05_agent_12_memory-module-ref-core-and-store.md`
- `05_agent_12_memory-module-ref-extraction-and-facade.md`
- `05_agent_12_memory-module-ref-ops-and-scoring.md`

## Keywords

retriever.py
injection.py
ingestion.py
