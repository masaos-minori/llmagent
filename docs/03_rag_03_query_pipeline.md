# RAG Query Pipeline

- System overview → [03_rag_01_system_overview.md](03_rag_01_system_overview.md)
- Configuration → [03_rag_05_configuration_and_operations.md](03_rag_05_configuration_and_operations.md)
- Type definitions → [03_rag_04_data_model_and_interfaces.md](03_rag_04_data_model_and_interfaces.md)

---

## 1. Pipeline Overview

`RagPipeline` orchestrates 5 sequential stages. Each stage implements `PipelineStage` Protocol
and mutates a shared `PipelineContext` dataclass in-place.

```
RagPipeline.augment(query)
  → use_search=False? → return ""
  → rag_service_url set? → _augment_http() → fallback to in-process on failure
  → run(query, db, history_context)
      [1] MqeStage    — expand query into N variants
      [2] SearchStage — KNN + BM25 per variant
      [3] FusionStage — RRF merge (Σ 1/(60+rank))
      [4] RerankStage — cross-encoder scoring + dedup
      [5] AugmentStage — format [RAG_CONTEXT_START]...[RAG_CONTEXT_END]
  → use_refiner=True? → _augment_refiner() (compress chunks; fallback to raw on error)
  → return context block string
```

**Caller:** `mcp/rag_pipeline/service.py` (`RagPipelineMCPService`). Agent REPL does not
call `RagPipeline` directly.

---

## 2. RagPipeline Class (`rag/pipeline.py`)

```python
from rag.pipeline import RagPipeline, RagPipelineError, fetch_full_document, get_embedding, sanitize_document
```

### Constructor

```python
RagPipeline(
    http: httpx.AsyncClient,
    cfg: RagConfig,
    on_status: Callable[[str], None] | None = None,
    on_clear: Callable[[], None] | None = None,
)
```

### Public attributes

| Attribute | Type | Description |
|---|---|---|
| `last_fetch_result` | `TwoStageFetchResult \| None` | Reranked hits from last `run()`/`augment()`. Holds `hits`, `min_score_applied`, `max_chunks_per_doc` |
| `last_timings` | `dict[str, float]` | Wall-clock seconds per stage from last `run()` |
| `semantic_cache` | `SemanticCache` | In-memory nearest-neighbor cache |

### Public methods

| Method | Signature | Description |
|---|---|---|
| `run` | `async (query, db, history_context="") -> tuple[list[str], list[list[RagHit]], list[RagHit], list[RagHit]]` | Execute MQE→Search→Fusion→Rerank; return `(queries, search_results, merged, reranked)`; always calls `on_clear()` in `finally` |
| `augment` | `async (query, debug_fn=None, history_context="") -> str` | Full pipeline + Augment stage; returns context block string or `""` |
| `search_queries` | `(queries, db) -> list[list[RagHit]]` | Standalone helper: parallel embed + sequential DB search |
| `rerank_candidates` | `(query, merged) -> list[RagHit]` | Standalone helper: cross-encoder or RRF fallback + dedup |

### Private methods

| Method | Description |
|---|---|
| `_augment_http(rag_url, query, history_context) -> str \| None` | POST to `{rag_url}/v1/search`; update `last_fetch_result`; return `None` on failure |
| `_augment_refiner(reranked, query) -> str \| None` | Compress chunks via `RagLLM.refine_context`; return `None` on empty/error |
| `_format_chunks(reranked) -> str` (static) | Format as `[Source: title \| url]\ncontent` blocks with `[RAG_CONTEXT_START]`/`[RAG_CONTEXT_END]` markers |

---

## 3. PipelineStage Protocol (`rag/stage.py`)

```python
from rag.stage import PipelineStage, PipelineContext

class MyStage(PipelineStage):
    async def run(self, ctx: PipelineContext, **kwargs: object) -> None:
        ...
```

`kwargs` receives `db: SQLiteHelper` and other stage-specific args.
The stage mutates `ctx` in-place; it does not return a value.

---

## 4. PipelineContext Dataclass (`rag/stage.py`)

```python
ctx = PipelineContext(query="search query", history_context="conversation history")
```

| Field | Type | Initial | Mutated by |
|---|---|---|---|
| `query` | `str` | (required) | — |
| `history_context` | `str` | `""` | — |
| `queries` | `list[str]` | `[]` | `MqeStage` |
| `search_results` | `list[list[RawHit]]` | `[]` | `SearchStage` |
| `merged` | `list[RagHit]` | `[]` | `FusionStage` |
| `reranked` | `list[RagHit]` | `[]` | `RerankStage` |
| `augment_result` | `str` | `""` | `AugmentStage` |
| `observers` | `list[Any]` | `[]` | — |

**Method:** `add_observer(observer: Any) -> None`

---

## 5. Stage Details

### 5.1 MqeStage

```python
MqeStage(cfg: dict, llm: RagLLM)
```

- `use_mqe=False`: sets `ctx.queries = [ctx.query]` (single query, no expansion)
- `use_mqe=True`: calls `RagLLM.expand_queries(query, context)` → `ctx.queries`
- `mqe_n_queries` config controls number of variants

### 5.2 SearchStage

```python
SearchStage(cfg: dict, http: httpx.AsyncClient | None, embed_url: str)
```

- Parallel embed generation for all queries in `ctx.queries`
- Sequential DB search (one connection per query to avoid contention)
- Each query contributes one `list[RawHit]` to `ctx.search_results`
- KNN: `vector_search(embedding, top_k)` via sqlite-vec
- BM25: `fts_search(query, top_k)` via FTS5

### 5.3 FusionStage

```python
FusionStage(cfg: dict)
```

- Merges `ctx.search_results` using Reciprocal Rank Fusion: score = Σ 1/(rrf_k + rank)
- `rrf_k` default: 60 (from `cfg.get("rrf_k", 60)`)
- Assigns `rrf_score` to each `MergedHit`; stores in `ctx.merged`

> **Known Issue:** `use_rrf=False` has no effect — `FusionStage` always executes RRF.
> `_dedup_hits` fallback is dead code. See [03_rag_90_inconsistencies_and_known_issues.md](03_rag_90_inconsistencies_and_known_issues.md).

### 5.4 RerankStage

```python
RerankStage(cfg: dict, llm: RagLLM)
```

- `use_rerank=False`: return top `rag_top_k` by RRF order via `deduplicate_chunks`
- `use_rerank=True`: `RagLLM.cross_encoder_rerank(query, candidates, top_k, rag_min_score)`
- Filters by `rag_min_score`; fallback to RRF order on cross-encoder failure
- Post-process: `deduplicate_chunks(hits, max_chunks_per_doc)`

### 5.5 AugmentStage

```python
AugmentStage()
```

- Formats `ctx.reranked` as `[Source: title | url]\ncontent` blocks
- Joined by `\n\n---\n\n`; wrapped in `[RAG_CONTEXT_START]` / `[RAG_CONTEXT_END]`
- Stored in `ctx.augment_result`

---

## 6. SemanticCache (`rag/cache.py`)

```python
from rag.repository import SemanticCache  # canonical: rag.cache; re-exported from rag.repository

cache = SemanticCache(max_size=100, threshold=0.92)
```

| Method / Property | Signature | Description |
|---|---|---|
| `lookup` | `(embedding, history_context="") -> str \| None` | Return cached result if cosine similarity ≥ threshold among matching `history_context` entries; else `None` |
| `put` | `(embedding, history_context, context_str) -> None` | Store entry; `history_context` is part of cache key; call `prune()` after |
| `prune` | `() -> None` | Remove oldest entries (FIFO) until `len ≤ max_size` |
| `size` | property `int` | Current entry count |

Cache is initialized in `RagPipeline.__init__` using `cfg.semantic_cache_max_size` and
`cfg.semantic_cache_threshold`.

---

## 7. Helper Classes

### 7.1 RagRepository (`rag/repository.py`)

Owns all SQL. Used internally by stages.

| Method | Signature | Description |
|---|---|---|
| `vector_search` | `(embedding: list[float], top_k: int) -> list[RagHit]` | KNN via sqlite-vec; logs `top_k`/`hits`/`elapsed_ms` (not query) |
| `fts_search` | `(query: str, top_k: int) -> list[RagHit]` | BM25 via FTS5; returns `[]` on `sqlite3.OperationalError`; logs query/fts_query/top_k/hits/elapsed_ms |

**Module-level standalone wrappers:**
- `vector_search(embedding, top_k, db)` → delegates to `RagRepository(db).vector_search()`
- `fts_search(query, top_k, db)` → delegates to `RagRepository(db).fts_search()`
- `fetch_full_document(chunk_id, db, window=None)` → same-doc chunks by `chunk_index` asc; `window=N` → ±N
- `deduplicate_chunks(hits, max_per_doc)` → cap same-URL hits; input must be descending-sorted
- `cosine_sim(a, b) -> float` → cosine similarity; returns `0.0` for zero vectors

### 7.2 RagScorer (`rag/repository.py`)

| Method | Signature | Description |
|---|---|---|
| `rrf_merge` (static) | `(results_list: list[list[RagHit]], rrf_k: int = 60) -> list[RagHit]` | RRF score Σ 1/(rrf_k+rank); descending order; assigns `rrf_score` |

### 7.3 RagLLM (`rag/llm.py`)

```python
from rag.llm import RagLLM
llm = RagLLM(client=http_client, llm_url="http://127.0.0.1:8002/v1/chat/completions")
```

| Method | Signature | Description |
|---|---|---|
| `expand_queries` | `(query: str, context: str = "") -> list[str]` | MQE; returns `[query]` on failure |
| `cross_encoder_rerank` | `(query, candidates, top_k, rag_min_score=0.0) -> list[RagHit]` | Cross-encoder; RRF fallback on failure |
| `summarize_tool_result` | `(text, tool_name, args) -> str` | Summarize tool output; returns `text` on failure |
| `refine_context` | `(chunks, query, max_tokens, per_chunk_chars, timeout) -> str` | Compress chunks to query-relevant points; caller handles fallback on error |
