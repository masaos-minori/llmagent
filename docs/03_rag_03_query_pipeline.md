# RAG Query Pipeline

- System overview → [03_rag_01_system_overview.md](03_rag_01_system_overview.md)
- Configuration → [03_rag_05_configuration_and_operations.md](03_rag_05_configuration_and_operations.md)
- Type definitions → [03_rag_04_data_model_and_interfaces.md](03_rag_04_data_model_and_interfaces.md)

---

## 1. Pipeline Overview

`RagPipeline` orchestrates 6 sequential stages (5 fixed + PluginHooks). Each stage implements
`PipelineStage` Protocol and mutates a shared `PipelineContext` dataclass in-place.

```
RagPipeline.augment(query)
  → use_search=False? → return ""
  → rag_service_url set? → call_rag_service() → fallback to in-process on failure
  → run(query, db, history_context, hook_strict=False)
      [1] MqeStage    — expand query into N variants
      [2] SearchStage — KNN + BM25 per variant
      [3] FusionStage — RRF merge (Σ 1/(rrf_k+rank); rrf_k configurable via config, default: 60)
      [4] RerankStage — cross-encoder scoring; filter by rag_min_score; post-rerank dedup by URL
      [5] PluginHooks — registered post-rerank hooks (error-isolated; strict mode re-raises); runs between RerankStage and AugmentStage (not a PipelineStage)
      [6] AugmentStage — format [RAG_CONTEXT_START]...[RAG_CONTEXT_END]
  → use_refiner=True? → refine_context() (compress chunks; fallback to raw on error)
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
| `last_stage_results` | `list[StageResult]` | Per-stage outcome records (status, fallback reason, elapsed) from last `run()` |
| `semantic_cache` | `SemanticCache` | In-memory nearest-neighbor cache |

### Public methods

| Method | Signature | Description |
|---|---|---|
| `run` | `async (query, db, history_context="", hook_strict=False) -> tuple[list[str], list[list[RawHit]], list[RagHit], list[RagHit]]` | Execute MQE→search→RRF→rerank+PluginHooks; return `(queries, search_results, merged, reranked)`; `hook_strict=True` re-raises first plugin hook failure (default: log warning and skip); always calls `on_clear()` in `finally` |
| `augment` | `async (query, debug_fn=None, history_context="") -> str` | Full pipeline + Augment stage; returns context block string or `""` |
| `search_queries` | `(queries, db) -> list[list[RagHit]]` | Standalone helper: parallel embed + sequential DB search |
| `rerank_candidates` | `(query, merged) -> list[RagHit]` | Standalone helper: cross-encoder or RRF fallback + dedup |

### Private methods

| Method | Description |
|---|---|
| `_format_chunks(reranked) -> str` (static) | Format as `[Source: title \| url]\ncontent` blocks with `[RAG_CONTEXT_START]`/`[RAG_CONTEXT_END]` markers |
| `_get_stage_status(stage, ctx) -> tuple[str, str \| None]` | Determine status (`"success"`/`"fallback"`) and reason for each stage (used internally by `run()`) |

### HTTP Mode (`rag_service_url`)

When `rag_service_url` is non-empty, `augment()` delegates to the external RAG service via
`call_rag_service()` in `rag/pipeline_service.py` instead of running the in-process pipeline.

| Behavior | Detail |
|---|---|
| Auth | `X-RAG-Token: {rag_auth_token}` header added when `rag_auth_token != ""` (default: no header) |
| Timeout | 10.0 seconds per HTTP attempt (connect + read) |
| Retry | Up to 2 retries on 5xx or transport errors; exponential backoff (1s, 2s); no retry on 4xx |
| Fallback | `None` returned → in-process pipeline; `""` (empty context) → accepted as valid result |
| Anti-loop | MCP adapter hardcodes `rag_service_url=""` so in-process `augment()` never re-delegates |

Config fields in `RagConfig` Protocol (`shared/types.py`):
- `rag_service_url: str` — remote endpoint URL; empty string disables HTTP mode
- `rag_auth_token: str` — optional bearer token for `X-RAG-Token` header; `""` = no auth (default)

#### HTTP RAG result classification

When `rag_service_url` is set, `augment()` classifies the HTTP result and records it
in `get_diagnostics()["http_result_kind"]` and in `StageResult.fallback_reason`.

| `http_result_kind` | `StageResult` status | `fallback_reason` | Condition |
|---|---|---|---|
| `"remote_nonempty"` | `"success"` | `None` | HTTP call succeeded; non-empty context returned |
| `"remote_empty"` | `"success"` | `"http_remote_empty"` | HTTP 200 but context field is `""` — valid empty result |
| `"in_process_fallback"` | `"fallback"` | error string | HTTP error; in-process RAG pipeline ran instead |
| `None` | — | — | `rag_service_url` not set; HTTP mode not used |

The `"remote_empty"` case is a normal condition (not a failure): the remote service
responded successfully but found no relevant context. The in-process pipeline does NOT
run in this case.

The classification is visible in:
- `get_diagnostics()["http_result_kind"]`
- `/rag search --debug` stage results: `✓ HttpAugment: success — http_remote_empty`

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
| `stage_results` | `list[StageResult]` | `[]` | `RagPipeline.run()` |
| `search_diagnostics` | `SearchDiagnostics` | `SearchDiagnostics()` | `SearchStage` (embed_ok, embed_failed, fts_errors) |

### 4.2 SearchDiagnostics (`rag/models_result.py`)

| Field | Type | Description |
|---|---|---|
| `embed_ok` | int | Successful embedding count |
| `embed_failed` | int | Failed embedding count |
| `fts_errors` | int | FTS5 query error count |

### 4.1 StageResult TypedDict (`rag/stage.py`)

```
StageResult = TypedDict with keys:
  stage_name: str         — class name of the stage
  status: str             — "success" | "fallback" | "failure"
  elapsed_seconds: float  — wall-clock seconds for the stage
  fallback_reason: str | None — reason when status is "fallback"
```

`RagPipeline.run()` records a `StageResult` per stage and also exposes the full list as
`pipeline.last_stage_results: list[StageResult]`. The same list is stored in
`PipelineContext.stage_results` for debugging and inspection.

---

## 5. Stage Details

### 5.1 MqeStage

```python
MqeStage(cfg: RagConfig, llm: RagLLM)
```

- `use_mqe=False`: sets `ctx.queries = [ctx.query]` (single query, no expansion)
- `use_mqe=True`: calls `RagLLM.expand_queries(query, context)` → `ctx.queries`
- `mqe_n_queries` config controls number of variants

### 5.2 SearchStage

```python
SearchStage(cfg: RagConfig, http: httpx.AsyncClient | None = None, embed_url: str = "")
```

- Parallel embed generation for all queries in `ctx.queries`
- Sequential DB search (one connection per query to avoid contention)
- Each query contributes one `list[RawHit]` to `ctx.search_results`
- KNN: `vector_search(embedding, top_k)` via sqlite-vec
- BM25: `fts_search(query, top_k)` via FTS5

### 5.3 FusionStage

```python
FusionStage(rrf_k: int = 60, use_rrf: bool = True)
```

- Merges `ctx.search_results` using Reciprocal Rank Fusion: score = Σ 1/(rrf_k + rank)
- `rrf_k` default: 60; configurable via `cfg.rrf_k` (RagConfig Protocol includes `rrf_k` field)
- Assigns `rrf_score` to each `MergedHit`; stores in `ctx.merged`

> `use_rrf=False` activates `_dedup_hits()` fallback (simple chunk_id dedup, all `rrf_score=0.0`). `pipeline.py:184` passes `use_rrf=self._cfg.use_rrf` to `FusionStage`.

#### Retrieval-quality tradeoff: `use_rrf=False` vs `use_rrf=True`

| Mode | Mechanism | Quality impact |
|---|---|---|
| `use_rrf=True` (default) | RRF: each hit scored as `Σ 1/(rrf_k + rank)` across all result lists | Chunks seen by multiple queries get promoted; robust cross-list ranking |
| `use_rrf=False` | `_dedup_hits()`: chunk_id dedup, first-occurrence wins; all hits get `rrf_score=0.0` | No rank signal; MQE results provide no additional ranking benefit |

**When `use_rrf=False`:**
- `_dedup_hits()` is used: deduplication by `chunk_id`; first occurrence across result lists wins
- All merged hits receive `rrf_score=0.0` — no rank-weighted scoring
- MQE-generated multi-query results provide **no additional ranking benefit**: a chunk seen
  by 3 queries scores identically to one seen by only 1
- Recommendation: keep `use_rrf=True` (default) unless embedding/FTS overhead must be
  minimized and ranking quality can be sacrificed

**Observability:**
- `--debug` shows `~ FusionStage: fallback — use_rrf=False`
- `get_diagnostics()["fusion_mode"]` returns `"rrf"` or `"dedup_only"`
- `logger.info("FusionStage: dedup-only mode (use_rrf=False)")` at INFO level

### 5.4 RerankStage

```python
RerankStage(cfg: RagConfig, llm: RagLLM)
```

- `use_rerank=False`: return top `rag_top_k` by RRF order via `deduplicate_chunks`
- `use_rerank=True`: `RagLLM.cross_encoder_rerank(query, candidates, top_k, rag_min_score)`
- Filters by `rag_min_score`; fallback to RRF order on cross-encoder failure
- Post-rerank dedup: `deduplicate_chunks(hits, max_chunks_per_doc)` — caps same-URL hits; input must be descending-sorted; applied AFTER reranking (not before)

### 5.5 AugmentStage

```python
AugmentStage()
```

- Formats `ctx.reranked` as `[Source: title | url]\ncontent` blocks
- Joined by `\n\n---\n\n`; wrapped in `[RAG_CONTEXT_START]` / `[RAG_CONTEXT_END]`
- Stored in `ctx.augment_result`

#### Refiner fallback reasons

When `use_refiner=true` and refinement fails, `augment()` falls back to raw-chunk
formatting. The fallback reason is recorded in `last_stage_results` and
`get_diagnostics()["fallback_reasons"]`.

| Reason | Condition |
|---|---|
| `refiner_returned_empty` | LLM response content is `""` or whitespace-only after `.strip()`. The `if refined:` guard is falsy. Common causes: content-policy refusal, empty LLM generation, prompt format producing no extractable key points. |
| `refiner_exception: {e}` | `httpx.HTTPStatusError`, `httpx.RequestError`, or `ValueError` raised during the LLM call. The exception message is included in the reason string. Not retried. |

Both reasons are:
- Visible at INFO level in application logs (`augment: refiner fallback (reason=...)`)
- Visible in `/rag search` output as `[warn] refiner fallback: <reason>`
- Visible in `/rag search --debug` stage results as `~ Refiner: fallback — <reason>`
- Available via `pipeline.get_diagnostics()["fallback_reasons"]`

---

## 6. SemanticCache (`rag/cache.py`)

```python
from rag.cache import SemanticCache  # defined in rag/cache.py:30; imported by rag/pipeline.py:30

cache = SemanticCache(max_size=100, threshold=0.92)
```

| Method / Property | Signature | Description |
|---|---|---|
| `lookup` | `(embedding, history_context="") -> str \| None` | Return cached result if cosine similarity ≥ threshold among matching `history_context` entries; raises `ValueError` on embedding dimension mismatch; else `None` |
| `put` | `(embedding, history_context, context_str) -> None` | Store entry; `history_context` is part of cache key; raises `ValueError` on embedding dimension mismatch; calls `prune()` after |
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
| `vector_search` | `(embedding: list[float], top_k: int) -> list[RagHit]` | KNN via sqlite-vec; logs `top_k`/`hits`/`elapsed_ms` |
| `fts_search` | `(query: str, top_k: int) -> list[RagHit]` | BM25 via FTS5; returns `[]` on `sqlite3.OperationalError`; logs `query`/`fts_query`/`top_k`/`hits`/`elapsed_ms` |

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

### 7.3 RagLLM (`rag/llm.py` — re-export stub)

`rag/llm.py` is a backward-compatibility re-export module. The actual implementations live in:

- `rag/llm_client.py` — `RagLLM` class, `get_embedding()`, `summarize_tool_result()`
- `rag/llm_prompts.py` — prompt templates, `RagExpansionError`, `RagRerankError`, `MqeParseError`

```python
from rag.llm import RagLLM  # re-exported from rag.llm_client
llm = RagLLM(client=http_client, llm_url="http://127.0.0.1:8001/v1/chat/completions")
```

| Method | Signature | Description |
|---|---|---|
| `expand_queries` | `(query: str, context: str = "") -> list[str]` | MQE; raises `RagExpansionError` on failure |
| `cross_encoder_rerank` | `(query, candidates, top_k, rag_min_score=0.0) -> list[RagHit]` | Cross-encoder; raises `RagRerankError` on failure; filters by `rag_min_score` |
| `summarize_tool_result` | `(text, tool_name, args) -> str` | Summarize tool output; raises on HTTP/parse failure |
| `refine_context` | `(chunks, query, max_tokens, per_chunk_chars, timeout) -> str` | Compress chunks to query-relevant points via `rag/pipeline_refiner.py`; caller handles fallback on error |

**Module-level functions:**

| Function | Signature | Description |
|---|---|---|
| `get_embedding` | `(text, client, embed_url) -> list[float]` | Convert text to embedding vector; uses `"query: "` prefix (E5 convention) |
| `summarize_tool_result` | `(text, tool_name, args, client, llm_url=None) -> str` | Standalone summarization; loads `llm_url` from cached config when `None` |
