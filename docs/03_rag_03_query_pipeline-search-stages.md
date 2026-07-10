---
title: "RAG Query Pipeline - Search Stages"
category: rag
tags:
  - mqe-stage
  - search-stage
  - fusion-stage
related:
  - 03_rag_00_document-guide.md
  - 03_rag_01_system_overview.md
  - 03_rag_03_query_pipeline.md
  - 03_rag_03_query_pipeline-rag-pipeline-class.md
  - 03_rag_03_query_pipeline-augment-stages.md
  - 03_rag_03_query_pipeline-context-and-diagnostics.md
  - 03_rag_04_data_model_and_interfaces.md
  - 03_rag_05_configuration_and_operations.md
source:
  - 03_rag_03_query_pipeline.md
---

# RAG Query Pipeline

- System overview → [03_rag_01_system_overview.md](03_rag_01_system_overview.md)
- Configuration → [03_rag_05_configuration_and_operations.md](03_rag_05_configuration_and_operations.md)
- Type definitions → [03_rag_04_data_model_and_interfaces.md](03_rag_04_data_model_and_interfaces.md)

---

## 5. Stage Details

### 5.1 MqeStage

```python
MqeStage(cfg: RagConfig, llm: RagLLM)
```

- `use_mqe=False`: sets `ctx.queries = [ctx.query]` (single query, no expansion)
- `use_mqe=True`: calls `RagLLM.expand_queries(query)` → `ctx.queries` (context is applied via prompt template from cfg, not as a direct parameter); raises `RagExpansionError` on LLM failure
- `mqe_n_queries` config controls number of variants

### 5.2 SearchStage

```python
SearchStage(cfg: RagConfig, http: httpx.AsyncClient | None = None, embed_url: str = "")
```

- Parallel embed generation for all queries in `ctx.queries`
- Sequential DB search (one connection per query to avoid contention)
- Each query contributes 0–2 `list[RawHit]` entries to `ctx.search_results` (KNN + BM25); empty on embed failure or DB error
- KNN: `vector_search(embedding, top_k)` via sqlite-vec
- BM25: `fts_search(query, top_k)` via FTS5; raises `sqlite3.OperationalError` on FTS syntax errors (caller handles)
- Logs to `/opt/llm/logs/search.log`: embed failure warnings, search degradation warnings (embed_failed count, FTS error count)
- Handles `db=None` by returning empty results with warning

### 5.3 FusionStage

```python
FusionStage(rrf_k: int = 60, use_rrf: bool = True)
```

- Merges `ctx.search_results` using Reciprocal Rank Fusion: score = Σ 1/(rrf_k + rank)
- `rrf_k` default: 60; configurable via `cfg.rrf_k` (RagConfig Protocol includes `rrf_k` field)
- Assigns `rrf_score` to each `MergedHit`; stores in `ctx.merged`

> `use_rrf=False` activates a dedup-only fallback (all `rrf_score=0.0`). `pipeline.py:184` passes the RRF configuration flag to `FusionStage`.

#### Retrieval-quality tradeoff: `use_rrf=False` vs `use_rrf=True`

> **Warning:** `use_rrf=False` is a **significant quality degradation**, not a harmless fallback.
> Rank signal is completely disabled: MQE multi-query expansion provides no additional ranking benefit.
> Use only for diagnostics or when latency must be minimized and ranking quality can be sacrificed.

| Mode | Mechanism | Quality impact |
|---|---|---|
| `use_rrf=True` (default) | RRF: each hit scored as `Σ 1/(rrf_k + rank)` across all result lists | Chunks seen by multiple queries get promoted; robust cross-list ranking |
| `use_rrf=False` | Dedup-only: chunk_id dedup, first-occurrence wins; all hits get `rrf_score=0.0` | No rank signal; MQE results provide no additional ranking benefit |

**When `use_rrf=False`:**
- Deduplication by `chunk_id`; first occurrence across result lists wins
- All merged hits receive `rrf_score=0.0` — no rank-weighted scoring
- MQE-generated multi-query results provide **no additional ranking benefit**: a chunk seen
  by 3 queries scores identically to one seen by only 1
- Recommendation: keep `use_rrf=True` (default) unless embedding/FTS overhead must be
  minimized and ranking quality can be sacrificed

**Observability:**
- `/rag search --debug` shows `[debug] fusion: use_rrf=False (rank signal disabled)`
- `get_diagnostics()["fusion_mode"]` returns `"rrf"` or `"dedup_only"`
- Log: `INFO FusionStage: dedup-only mode (use_rrf=False) — rank signal disabled, MQE provides no ranking benefit`
- Startup: `WARNING rag config warning: use_rrf=false degrades retrieval quality; use only for diagnostics` (via `config_validator.py` during pipeline initialization)

---

## Related Documents

- `03_rag_00_document-guide.md`
- `03_rag_01_system_overview.md`
- `03_rag_03_query_pipeline.md`
- `03_rag_03_query_pipeline-rag-pipeline-class.md`
- `03_rag_03_query_pipeline-augment-stages.md`
- `03_rag_03_query_pipeline-context-and-diagnostics.md`
- `03_rag_04_data_model_and_interfaces.md`
- `03_rag_05_configuration_and_operations.md`

## Keywords

mqe-stage
search-stage
fusion-stage
rag
