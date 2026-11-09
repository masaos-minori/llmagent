---
title: "RAG Query Pipeline - Search Stages"
area: rag
tags:
  - mqe-stage
  - search-stage
  - fusion-stage
related:
  - rag_00_document-guide.md
  - rag_01_system_overview.md
  - rag_03_01_query_pipeline-overview.md
  - rag_03_02_query_pipeline-rag-pipeline-class.md
  - rag_03_05_query_pipeline-augment-stages.md
  - rag_03_03_query_pipeline-context-and-diagnostics.md
  - rag_04_dto-models-types.md
  - rag_05_01-configuration-reference.md
---


# RAG Query Pipeline

- System Overview → [rag_01_system_overview.md](rag_01_system_overview.md)
- Configuration → [rag_05_01-configuration-reference.md](rag_05_01-configuration-reference.md)
- Type Definitions → [rag_04_dto-models-types.md](rag_04_dto-models-types.md)

---

## 5. Stage Details

### 5.1 MqeStage

- `use_mqe=False`: Sets `ctx.queries = [ctx.query]` (single query, no expansion).
- `use_mqe=True`: Calls `RagLLM.expand_queries(query)` and stores results in `ctx.queries` (context is applied via prompt templates in `cfg`, not as a direct parameter). If expansion fails with `RagExpansionError`, the stage catches it, sets `ctx.queries = [ctx.query]` (the original query) and records the fallback reason `mqe_exception`; the error does not propagate.
- The expanded list holds the original query first, then at most `mqe_n_queries` distinct paraphrases: entries are trimmed, whitespace-only entries are dropped, and case-insensitive duplicates (including duplicates of the original query) are removed.

### 5.2 SearchStage

- Generates embeddings for all queries in `ctx.queries` in parallel, with a bounded number of concurrent requests.
- Database searches are executed sequentially (one connection per query to avoid contention).
- Each query adds 0–2 `list[RawHit]` items to `ctx.search_results` (KNN + BM25). The vector leg runs only when an embedding is available and the BM25 leg always runs, so an embedding failure or a vector-search error does not suppress the BM25 hits for that query.
- KNN: Uses `vector_search(embedding, top_k)` via `sqlite-vec`.
- BM25: Uses `fts_search(query, top_k)` via FTS5.
- Logs to the search log file: warnings for embedding failures and search degradation (count of `embed_failed` and retrieval-leg errors `fts_errors`).
- If `db=None`, it processes with an empty result and a warning.

> **Error handling**: Errors raised by the vector or BM25 retrieval legs — `sqlite3.OperationalError` / `RuntimeError`, plus packing failures (`ValueError`, `OverflowError`, `struct.error`) surfacing from the search path — are caught per leg within `SearchStage` and never propagated as exceptions to the caller. `fts_errors` counts failed retrieval legs (vector or BM25), once per failed leg per query; `embed_failed` counts embedding failures. The diagnostics report `degraded` when either counter is positive, and the stage reports `fallback` only when no leg returned any hit. A failure in one query does not stop processing of remaining queries. Embedding acquisition failures are likewise swallowed individually (`return_exceptions=True`) and reflected only in the `SearchDiagnostics` counters; out-of-range or non-finite embedding elements are rejected at `get_embedding` and land in `embed_failed`.


### 5.3 FusionStage

- Merges `ctx.search_results` using Reciprocal Rank Fusion: `score = sum(1 / (rrf_k + rank))`.
- `rrf_k` is configurable (`cfg.rrf_k`).
- Assigns an `rrf_score` to each `MergedHit` and stores it in `ctx.merged`.

Using `use_rrf=False` triggers a fallback to deduplication only (all scores set to `0.0`).

#### Search Quality Trade-off: `use_rrf=False` vs. `use_rrf=True`

> **Warning:** `use_rrf=False` is NOT a harmless fallback; it represents a **significant degradation in quality**.
> Ranking signals are completely disabled: multi-query expansion via MQE provides no additional ranking benefit.
> Use only for diagnostic purposes or when latency must be minimized at the expense of search quality.

| Mode | Mechanism | Impact on Quality |
|---|---|---|
| `use_rrf=True` | RRF: Scores hits across the entire result list using `sum(1 / (rrf_k + rank))` | Prioritizes chunks seen across multiple queries; provides robust cross-list ranking |
| `use_rrf=False` | Deduplication only: Deduplicates by `chunk_id` and prioritizes the first occurrence; all hits get `rrf_score=0.0` | No ranking signal; MQE results provide no additional ranking benefit |

With `use_rrf=False`, a chunk seen in 3 queries scores the same as a chunk seen in only 1. Keep `use_rrf=True` (default) unless Embedding/FTS overhead must be minimized and search quality can be sacrificed.

**Observability:**
- `get_diagnostics()["fusion_mode"]` returns `"rrf"` or `"dedup_only"`.
- An INFO log is emitted when the stage runs in dedup-only mode.
- Startup: a WARNING that `use_rrf=false` degrades retrieval quality and is for diagnostics only (`RagConfigValidator.validate()`, logged in `RagPipeline.__init__`).

Note: No quantitative benchmark data (recall@k/precision@k or other metrics) comparing `use_rrf=True`/`False` exists in this repository, nor does any ADR document specific thresholds for when disabling RRF is acceptable. If RRF is disabled for latency reasons, measure the actual quality impact for your specific use case rather than relying on this qualitative warning alone.

---

## Keywords

- mqe-stage
- search-stage
- fusion-stage
- rag
