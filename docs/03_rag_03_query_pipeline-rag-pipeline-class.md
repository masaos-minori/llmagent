---
title: "RAG Query Pipeline - RagPipeline Class Detail"
category: rag
tags:
  - rag-pipeline-class
  - http-mode
related:
  - 03_rag_00_document-guide.md
  - 03_rag_01_system_overview.md
  - 03_rag_03_query_pipeline.md
  - 03_rag_03_query_pipeline-context-and-diagnostics.md
  - 03_rag_03_query_pipeline-stages.md
  - 03_rag_03_query_pipeline-helpers-and-cache.md
  - 03_rag_04_data_model_and_interfaces.md
  - 03_rag_05_configuration_and_operations.md
source:
  - 03_rag_03_query_pipeline.md
---

# RAG Query Pipeline

- System overview → [03_rag_01_system_overview.md](03_rag_01_system_overview.md)
- Configuration → [03_rag_05_configuration_and_operations.md](03_rag_05_1-configuration-reference.md)
- Type definitions → [03_rag_04_data_model_and_interfaces.md](03_rag_04_dto-models_data.md)

---

## 2. RagPipeline Class (`scripts/rag/pipeline.py`)

```python
from rag.pipeline import RagPipeline, RagPipelineError, fetch_full_document, get_embedding, sanitize_document
```

### Constructor

| Parameter | Type | Description |
|---|---|---|
| `http` | `httpx.AsyncClient` | HTTP client for LLM/embedding calls |
| `cfg` | `RagConfig` | RAG configuration from agent.toml |
| `module_cfg` | `dict \| None` | Optional config override; bypasses load_all() / agent.toml (agent process path); when None, falls back to internal module config retrieval |
| `on_status` | `Callable[[str], None] \| None` | Progress callback; defaults to no-op |
| `on_clear` | `Callable[[], None] \| None` | Cleanup callback; always called in `finally` block of `run()`/`augment()` |

```python
RagPipeline(
    http: httpx.AsyncClient,
    cfg: RagConfig,
    *,
    module_cfg: dict | None = None,
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
| `run` | `async (query, db, history_context="", hook_strict=False) -> PipelineRunResult` | Execute MQE→search→RRF→rerank+PluginHooks; return `PipelineRunResult` (queries, search_results, merged, reranked, stage_results, diagnostics); **does NOT set `result_source`** — always `None` in local mode; `hook_strict=True` re-raises first plugin hook failure (default: log warning and skip); always calls `on_clear()` in `finally` |
| `augment` | `async (query, debug_fn=None, history_context="") -> str` | Full pipeline + Augment stage; returns context block string or `""`; raises `RagPipelineError` on DB failure |
| `search_queries` | `async (queries, db) -> list[list[RagHit]]` | Standalone helper: parallel embed + sequential DB search; **does NOT record diagnostics** — unlike SearchStage which populates `SearchDiagnostics` |
| `rerank_candidates` | `async (query, merged) -> list[RagHit]` | Standalone helper: cross-encoder or slice+dedup fallback + dedup |
| `get_diagnostics` | `() -> dict` | Return structured diagnostics for the last pipeline execution; safe to call before `run()`/`augment()` — returns empty/zero values |

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
| Maximum attempts | 3 total attempts (initial + 2 retries) |
| Retry backoff | Exponential: `min(2**attempt, 5)` seconds |

---

## Related Documents

- `03_rag_00_document-guide.md`
- `03_rag_01_system_overview.md`
- `03_rag_03_query_pipeline.md`
- `03_rag_03_query_pipeline-context-and-diagnostics.md`
- `03_rag_03_query_pipeline-stages.md`
- `03_rag_03_query_pipeline-helpers-and-cache.md`
- `03_rag_04_data_model_and_interfaces.md`
- `03_rag_05_configuration_and_operations.md`

## Keywords

rag-pipeline-class
http-mode
rag
