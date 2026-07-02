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

**Caller:** `scripts/mcp/rag_pipeline/service.py` (`RagPipelineMCPService`). Agent REPL does not
call `RagPipeline` directly.

### MCP サーバー呼び出しパス

```
MCP クライアント
  → scripts/mcp/rag_pipeline/server.py (HTTP ルート)
    → RagPipelineMCPService.run_pipeline() (service.py)
      → RagPipeline.run() (scripts/rag/pipeline.py)
```

---

## 2. RagPipeline Class (`scripts/rag/pipeline.py`)

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
| `last_search_diagnostics` | `SearchDiagnostics` | Search diagnostics from last `run()`; includes `result_source`, `http_result_kind`, `remote_status_code`, `remote_latency_ms`, `fallback_reason` for HTTP mode |
| `stat_search_embed_failed` | `int` | Cumulative embedding failure count across all `run()` calls on this instance |
| `stat_search_fts_errors` | `int` | Cumulative FTS error count across all `run()` calls on this instance |

### Public methods

| Method | Signature | Description |
|---|---|---|
| `run` | `async (query, db, history_context="", hook_strict=False) -> PipelineRunResult` | Execute MQE→search→RRF→rerank+PluginHooks; return `PipelineRunResult` (queries, search_results, merged, reranked, stage_results, diagnostics); `hook_strict=True` re-raises first plugin hook failure (default: log warning and skip); always calls `on_clear()` in `finally` |
| `augment` | `async (query, debug_fn=None, history_context="") -> str` | Full pipeline + Augment stage; returns context block string or `""`; raises `RagPipelineError` on DB failure |
| `search_queries` | `async (queries, db) -> list[list[RagHit]]` | Standalone helper: parallel embed + sequential DB search |
| `rerank_candidates` | `async (query, merged) -> list[RagHit]` | Standalone helper: cross-encoder or RRF fallback + dedup |

### Private methods

| Method | Description |
|---|---|
| `_format_chunks(reranked) -> str` (static) | Format as `[Source: title \| url]\n{sanitize_document(content)}` blocks with `[RAG_CONTEXT_START]`/`[RAG_CONTEXT_END]` markers; empty reranked returns `[RAG_CONTEXT_START]\n\n[RAG_CONTEXT_END]` |
| `_get_stage_status(stage, ctx) -> tuple[str, str \| None]` | Determine status (`"success"`/`"fallback"`/`"failure"`) and reason for each stage (used internally by `run()`) |

### HTTP Mode (`rag_service_url`)

When `rag_service_url` is non-empty, `augment()` delegates to the external RAG service via
`call_rag_service()` in `scripts/rag/pipeline_service.py` instead of running the in-process pipeline.

| Behavior | Detail |
|---|---|
| Auth | `X-RAG-Token: {rag_auth_token}` header added when `rag_auth_token != ""` (default: no header) |
| Timeout | 10.0 seconds per HTTP attempt (connect + read) |
| Retry | Up to 2 retries on 5xx or transport errors; exponential backoff (1s, 2s); no retry on 4xx or JSON parse errors |
| Fallback | `None` returned → in-process pipeline; `""` (empty context) → accepted as valid result |
| Anti-loop | MCP adapter hardcodes `rag_service_url=""` so in-process `augment()` never re-delegates |
| Return values | `call_rag_service()` returns `(context: str \| None, status_code: int \| None, elapsed_ms: float)` — `status_code` and `elapsed_ms` are available for diagnostics |

Config fields in `RagConfig` Protocol (`shared/types.py`):
- `rag_service_url: str` — remote endpoint URL; empty string disables HTTP mode
- `rag_auth_token: str` — optional bearer token for `X-RAG-Token` header; `""` = no auth (default)

#### call_rag_service() function (`scripts/rag/pipeline_service.py`)

```python
call_rag_service(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]
```

Return contract:

| Return value | Condition |
|---|---|
| `str` (non-empty) | HTTP 200 + response body has `"result"` key with non-empty string value |
| `""` (empty string) | HTTP 200 but `"result"` key is absent, None, or empty — valid empty result |
| `None` | HTTP 4xx (no retry), 5xx with retries exhausted, transport error, or JSON parse error — triggers in-process fallback |

Side effects:
- `set_fetch_result` called with `TwoStageFetchResult` holding fetch stage status and hits from response body
- `set_fallback_reason` called with reason string on non-success path (4xx, transport error, etc.)

When `rag_service_url` is set, `augment()` classifies the HTTP result and records it
in `get_diagnostics()["http_result_kind"]` and in `StageResult.fallback_reason`.

| `http_result_kind` | `StageResult` status | `fallback_reason` | Condition |
|---|---|---|---|
| `"remote_nonempty"` | `"success"` | `None` | HTTP call succeeded; non-empty context returned |
| `"remote_empty"` | `"success"` | `None` | HTTP 200 but context field is `""` — valid empty result, not a fallback |
| `"in_process_fallback"` | `"fallback"` | error string | HTTP error; in-process RAG pipeline ran instead |
| `None` | — | — | `rag_service_url` not set; HTTP mode not used |

The `"remote_empty"` case is a **success**, not a fallback: the remote service
responded with HTTP 200 but found no relevant context. The in-process pipeline does NOT
run in this case. `fallback_reason` is `None` for both `remote_nonempty` and `remote_empty`
to prevent confusion with actual fallback events.

The classification is visible in:
- `get_diagnostics()["http_result_kind"]`
- `/rag search --debug`: `[debug] http mode: result_source=remote http_result_kind=success (empty response — no in-process fallback)`

#### HTTP RAG request details

| Detail | Value |
|---|---|
| Endpoint | `{rag_url}/v1/call_tool` |
| Request body | `{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [history_context]}}` (empty list when history_context is empty) |
| `_MAX_ATTEMPTS` | 3 total attempts (initial + 2 retries) |
| Retry backoff | Exponential: `min(2**attempt, 5)` seconds |

---

## 3. PipelineStage Protocol (`scripts/rag/stage.py`)

```python
from rag.stage import PipelineStage, PipelineContext

class MyStage(PipelineStage):
    async def run(self, ctx: PipelineContext, **kwargs: object) -> None:
        ...
```

`kwargs` receives `db: SQLiteHelper` and other stage-specific args.
The stage mutates `ctx` in-place; it does not return a value.

---

## 4. PipelineContext Dataclass (`scripts/rag/stage.py`)

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
| `search_diagnostics` | `SearchDiagnostics` | `SearchDiagnostics()` (default_factory) | `SearchStage` — created empty, populated with embed_ok/embed_failed/fts_errors during search; also populated by HTTP mode with `result_source`, `http_result_kind`, `remote_status_code`, `remote_latency_ms`, `fallback_reason` |

### 4.2 SearchDiagnostics (`scripts/rag/models_result.py`)

```python
from rag.models_result import SearchDiagnostics, ResultSource, HttpResultKind
```

| Field | Type | Default | Description |
|---|---|---|---|
| `embed_ok` | int | 0 | Successful embedding count |
| `embed_failed` | int | 0 | Failed embedding count |
| `fts_errors` | int | 0 | FTS5 query error count |
| `result_source` | ResultSource | ResultSource.LOCAL | Source of the final result (in HTTP mode only) |
| `http_result_kind` | HttpResultKind | HttpResultKind.NOT_USED | Classification of HTTP RAG result (in HTTP mode only) |
| `remote_status_code` | int \| None | None | HTTP status code from remote service (HTTP mode only) |
| `remote_latency_ms` | float \| None | None | Latency in milliseconds for remote call (HTTP mode only) |
| `fallback_reason` | str \| None | None | Reason for fallback when HTTP mode fails (HTTP mode only) |

### 4.1 StageResult TypedDict (`scripts/rag/stage.py`)

```
StageResult = TypedDict with keys:
  stage_name: str         — class name of the stage
  status: str             — "success" | "fallback" | "failure"
  elapsed_seconds: float  — wall-clock seconds for the stage
  fallback_reason: str | None — reason when status is "failure" or "fallback"; None on success
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

> `use_rrf=False` activates `_dedup_hits()` fallback (simple chunk_id dedup, all `rrf_score=0.0`). `pipeline.py:184` passes `use_rrf=self._cfg.use_rrf` to `FusionStage`.

#### Retrieval-quality tradeoff: `use_rrf=False` vs `use_rrf=True`

> **Warning:** `use_rrf=False` is a **significant quality degradation**, not a harmless fallback.
> Rank signal is completely disabled: MQE multi-query expansion provides no additional ranking benefit.
> Use only for diagnostics or when latency must be minimized and ranking quality can be sacrificed.

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
- `/rag search --debug` shows `[debug] fusion: use_rrf=False (rank signal disabled)`
- `get_diagnostics()["fusion_mode"]` returns `"rrf"` or `"dedup_only"`
- Log: `INFO FusionStage: dedup-only mode (use_rrf=False) — rank signal disabled, MQE provides no ranking benefit`
- Startup: `WARNING rag config warning: use_rrf=false degrades retrieval quality; use only for diagnostics` (via `config_validator.py` during pipeline initialization)

### 5.4 RerankStage

```python
RerankStage(cfg: RagConfig, llm: RagLLM)
```

- `use_rerank=False`: return top `rag_top_k` by RRF order (slice) + `deduplicate_chunks`
- `use_rerank=True`: `RagLLM.cross_encoder_rerank(query, candidates, top_k, rag_min_score)`; raises `RagRerankError` on LLM failure
- Filters by `rag_min_score`; no fallback on cross-encoder failure (exception propagates)
- Post-rerank dedup: `deduplicate_chunks(hits, max_chunks_per_doc)` — caps same-URL hits; input must be descending-sorted; applied AFTER reranking (not before)

### 5.5 AugmentStage

No constructor (inherits from `PipelineStage`).

- Formats `ctx.reranked` as `[Source: {title if title else url} | {url}]\n{sanitize_document(content)}` blocks; when title is empty, uses URL as fallback
- Joined by `\n\n---\n\n`; wrapped in `[RAG_CONTEXT_START]` / `[RAG_CONTEXT_END]`
- Stored in `ctx.augment_result`
- Uses `sanitize_document(c.content)` from `rag.utils` to sanitize content before formatting
- Empty reranked returns `[RAG_CONTEXT_START]\n\n[RAG_CONTEXT_END]`

**Content-only invariant (DESIGN-2):** AugmentStage formats `content` only — never `normalized_content`.

- `chunks.content` is the original chunk text and the **only** text used for LLM context
- `chunks.normalized_content` is Sudachi-normalized Japanese text used **exclusively** for FTS5 search indexing; it must never appear in LLM context
- Replacing `content` with `normalized_content` would degrade LLM context quality (Sudachi-normalized text loses original readability)
- RAG context blocks must always contain original readable chunk text

#### RefineResult dataclass (`scripts/rag/pipeline_refiner.py`)

```python
from rag.pipeline_refiner import RefineResult
```

| Field | Type | Description |
|---|---|---|
| `text` | `str \| None` | Refined context text; `None` on failure (fallback to raw chunks) |
| `reason` | `str \| None` | Reason for failure; `None` on success; `"refiner_returned_empty"` or `"refiner_exception: ..."` on fallback |

#### Refiner fallback reasons

When `use_refiner=true` and refinement fails, `augment()` falls back to raw-chunk
formatting. The fallback reason is recorded in `last_stage_results` and
`get_diagnostics()["fallback_reasons"]`.

| Reason | Condition |
|---|---|
| `refiner_returned_empty` | LLM response content is `""` or whitespace-only after `.strip()`. The `if refined:` guard is falsy. Common causes: content-policy refusal, empty LLM generation, prompt format producing no extractable key points. |
| `refiner_exception: {e}` | `httpx.HTTPStatusError`, `httpx.RequestError`, or `ValueError` raised during the LLM call. The exception message is included in the reason string. Not retried. |

**No retry policy**: Refiner failure is treated as a non-critical degradation — raw chunks are acceptable output. Retrying a failed LLM call adds latency with low expected benefit (transient errors are rare; content-policy refusals will not succeed on retry). Use `use_refiner=false` to disable the refiner entirely when degraded output is not acceptable.

Both reasons are:
- Visible at INFO level in application logs (`augment: refiner fallback (reason=...)`)
- Visible in `/rag search` output as `[warn] refiner fallback: <reason>`
- Visible in `/rag search --debug` stage results as `~ Refiner: fallback — <reason>` and summary line `[refiner] fallback: N time(s)`
- Available via `pipeline.get_diagnostics()["fallback_reasons"]`, `["refiner_fallback_count"]`, `["refiner_exception_count"]`

---

## 6. SemanticCache (`scripts/rag/cache.py`)

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
| `invalidate` | `() -> None` | Bump generation counter and clear all cached entries atomically |
| `generation` | property `int` | Current cache invalidation generation count |

Cache is initialized in `RagPipeline.__init__` using `cfg.semantic_cache_max_size` and
`cfg.semantic_cache_threshold`.

---

## 7. Helper Classes

### 7.1 RagRepository (`scripts/rag/repository.py`)

Owns all SQL. Used internally by stages. Logs query / fts_query / top_k / elapsed_ms on every call for observability.

**SQL queries:**

| Method | SQL |
|---|---|
| `vector_search` | `SELECT c.chunk_id, c.content, d.url, d.title, cv.distance FROM chunks_vec cv JOIN chunks c ON c.chunk_id = cv.chunk_id JOIN documents d ON d.doc_id = c.doc_id WHERE cv.embedding MATCH ? ORDER BY cv.distance LIMIT ?` |
| `fts_search` | `SELECT c.chunk_id, c.content, d.url, d.title, bm25(chunks_fts) AS bm25_score FROM chunks_fts JOIN chunks c ON c.chunk_id = chunks_fts.rowid JOIN documents d ON d.doc_id = c.doc_id WHERE chunks_fts MATCH ? ORDER BY bm25(chunks_fts) LIMIT ?` |

**Japanese FTS5 tokenization:**

| Constant | Value | Description |
|---|---|---|
| `_MAX_FTS_TOKENS` | 20 | Maximum tokens in an FTS5 query |
| `_FTS_KEEP_POS` | `{"名詞", "動詞", "形容詞"}` | Sudachi POS categories retained for Japanese tokens |

**Private functions:**

| Function | Description |
|---|---|
| `_build_fts_tokens_ja(text)` | Extract normalized_form() of nouns/verbs/adjectives from Japanese text via Sudachi; propagates ImportError if Sudachi not installed; raises RuntimeError on tokenization failure |
| `_build_fts_query(text)` | Convert text to FTS5 query; Japanese uses Sudachi POS filter with quoted tokens, English uses alphanumeric regex |

**Lazy Sudachi loading:**

`_SudachiTokenizer` loads Sudachi on first use. Dictionary: `core`, SplitMode: `C`.

| Method | Signature | Description |
|---|---|---|
| `tokenize_pos_filter` | `(text: str, keep_pos: frozenset[str]) -> list[str]` | Return normalized_form() for tokens whose part_of_speech()[0] is in keep_pos; raises RuntimeError on tokenization failure |

**Public methods:**

| Method | Signature | Description |
|---|---|---|
| `vector_search` | `(embedding: list[float], top_k: int) -> list[RagHit]` | KNN via sqlite-vec; returns RawHit with `distance` field; logs `top_k`/`hits`/`elapsed_ms` |
| `fts_search` | `(query: str, top_k: int) -> list[RagHit]` | BM25 via FTS5; returns RawHit with `bm25_score` field; raises `sqlite3.OperationalError` on FTS syntax errors (caller handles); logs `query`/`fts_query`/`top_k`/`hits`/`elapsed_ms` |

**Module-level standalone wrappers:**
- `vector_search(embedding, top_k, db)` → delegates to `RagRepository(db).vector_search()`
- `fts_search(query, top_k, db)` → delegates to `RagRepository(db).fts_search()`
- `fetch_full_document(chunk_id, db, window=None)` → same-doc chunks by `chunk_index` asc; `window=N` → ±N
- `deduplicate_chunks(hits, max_per_doc)` → cap same-URL hits; input must be descending-sorted
- `cosine_sim(a, b) -> float` → cosine similarity; returns `0.0` for zero vectors

### 7.2 RagScorer (`scripts/rag/repository.py`)

| Method | Signature | Description |
|---|---|---|
| `rrf_merge` (static) | `(results_list: list[list[RawHit]] \| list[list[RagHit]], rrf_k: int = 60) -> list[RagHit]` | RRF score Σ 1/(rrf_k+rank); descending order; assigns `rrf_score`; accepts RawHit or RagHit result lists |

### 7.3 RagLLM (`scripts/rag/llm_client.py`)

Implementations live in:

- `scripts/rag/llm_client.py` — `RagLLM` class, `get_embedding()`, `summarize_tool_result()`
- `scripts/rag/llm_prompts.py` — prompt templates, `RagExpansionError`, `RagRerankError`, `MqeParseError`

```python
from rag.llm_client import RagLLM
llm = RagLLM(client=http_client, llm_url="http://127.0.0.1:8001/v1/chat/completions")
```

| Method | Signature | Description |
|---|---|---|
| `expand_queries` | `async (query: str, context: str = "") -> list[str]` | MQE; raises `RagExpansionError` on HTTP failure, connection error, or parse failure |
| `cross_encoder_rerank` | `async (query: str, candidates: list[RagHit], top_k: int, rag_min_score=0.0) -> list[RagHit]` | Cross-encoder; raises `RagRerankError` on HTTP failure, connection error, or parse failure; filters by `rag_min_score` |
| `summarize_tool_result` | `async (text: str, tool_name: str, args: dict[str, object]) -> str` | Summarize tool output via LLM; raises on any HTTP or parse failure — callers decide how to handle |
| `refine_context` | `async (chunks: list[RagHit], query: str, max_tokens: int, per_chunk_chars: int, timeout: float) -> str` | Compress chunks to query-relevant key points via single LLM call; raises on error so callers can fall back |

**Module-level functions:**

| Function | Signature | Description |
|---|---|---|
| `get_embedding` | `async (text, client, embed_url) -> list[float]` | Convert text to embedding vector; uses `"query: "` prefix (E5 convention); raises on HTTP failure or missing/empty embedding field |
| `summarize_tool_result` | `async (text, tool_name, args, client, llm_url=None) -> str` | Standalone summarization; loads `llm_url` from cached config when `None`; raises on LLM call failure |

### 7.4 PipelineRunResult (`scripts/rag/types.py`)

```python
@dataclass
class PipelineRunResult:
    queries: list[str]
    search_results: list[list[RawHit]]
    merged: list[RagHit]
    reranked: list[RagHit]
    stage_results: list[StageResult]
    diagnostics: SearchDiagnostics
    result_source: str | None = None
```

Returned by `RagPipeline.run()`. The `result_source` field is a `ResultSource` enum value: `REMOTE` for HTTP mode, `LOCAL` for in-process, or `FALLBACK` for in-process fallback from HTTP failure.

---

## 8. Tests

### 8.1 Deterministic regression tests (`tests/test_rag_quality_regression.py`)

Fixtures: in-memory SQLite DB with 3 known documents, fixed-vector mock embedder.

| Test | Mode | Assertion |
|---|---|---|
| `test_rrf_returns_result_for_known_query` | RRF (default) | `len(result.reranked) >= 0` — must not raise |
| `test_no_rrf_returns_result` | No-RRF | `len(result.reranked) >= 0` — must not raise |
| `test_semantic_cache_hit` | RRF + cache | Second identical query returns cached context or reranked results |
| `test_fallback_no_embed_server` | RRF, embed failure | `result.reranked == []` — fallback yields empty result, not exception |

Run: `uv run pytest tests/test_rag_quality_regression.py -v`
