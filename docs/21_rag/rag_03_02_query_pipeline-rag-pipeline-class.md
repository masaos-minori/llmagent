---
title: "RAG Query Pipeline - RagPipeline Class Detail"
area: rag
tags:
  - rag-pipeline-class
  - http-mode
related:
  - rag_00_document-guide.md
  - rag_01_system_overview.md
  - rag_03_01_query_pipeline-overview.md
  - rag_03_03_query_pipeline-context-and-diagnostics.md
  - rag_03_04_query_pipeline-search-stages.md
  - rag_03_05_query_pipeline-augment-stages.md
  - rag_03_06_query_pipeline-helpers-and-cache.md
  - rag_04_05_dto-types.md
  - rag_05_1-configuration-reference.md
source:
  - rag_03_02_query_pipeline-rag-pipeline-class.md

---


# RAG Query Pipeline

- System Overview → [rag_01_system_overview.md](rag_01_system_overview.md)
- Configuration → [rag_05_1-configuration-reference.md](rag_05_1-configuration-reference.md)
- Type Definitions → [rag_04_05_dto-types.md](rag_04_01_dto-models_data.md)

---

## 2. RagPipeline Class (`scripts/rag/pipeline.py`)

```python
from rag.pipeline import RagPipeline, RagPipelineError
```

> **Documentation vs. Implementation Mismatch**: `fetch_full_document` is not provided by `rag/pipeline.py`. Its actual implementation is defined in `rag/repository.py` (`from rag.repository import fetch_full_document`). Similarly, `sanitize_document` is a function from `rag/utils.py` and does not exist in `rag.pipeline`. Actual imports in test and implementation code are only `from rag.pipeline import RagPipeline, RagPipelineError`.
> (Evidence classification: Explicit in code — `scripts/rag/pipeline.py` import statements, `fetch_full_document()` function in `scripts/rag/repository.py`)

The constructor of this class configures it bypassing `module_cfg`. Please refer to the source code for details.

Refer to the source code for a list of public attributes and methods.

### Implementation Note

- **Removed.** The `invalidate_cache()` method was deliberately removed as part of the semantic cache feature removal (`282b08f38`, `09093016d`). Its absence is verified by `tests/rag/test_rag_pipeline_no_cache_freshness.py` (three assertions: `assert hasattr(pipeline, "invalidate_cache") is False`). No cache invalidation mechanism exists in the current implementation.

## Related Documents

- `rag_00_document-guide.md`
- `rag_01_system_overview.md`
- `rag_03_01_query_pipeline-overview.md`
- `rag_03_03_query_pipeline-context-and-diagnostics.md`
- `rag_03_04_query_pipeline-search-stages.md`
- `rag_03_05_query_pipeline-augment-stages.md`
- `rag_03_06_query_pipeline-helpers-and-cache.md`
- `rag_04_05_dto-types.md`
- `rag_05_1-configuration-reference.md`
- `rag_03_02_query_pipeline-rag-pipeline-class.md`

## Keywords

rag-pipeline-class
http-mode
rag


### HTTP Mode (`rag_service_url`)

If `rag_service_url` is not empty, `augment()` delegates to an external RAG service via `call_rag_service()` in `scripts/rag/pipeline_service.py` instead of executing the in-process pipeline.

| Behavior | Details |
|---|---|
| Authentication | If `rag_auth_token != ""` the `X-RAG-Token: {rag_auth_token}` header is added (default: no header) |
| Timeout | 10.0 seconds per HTTP attempt (connection + read) |
| Retries | Max 2 retries for 5xx or transport errors with exponential backoff (1s, 2s); no retries for 4xx or JSON parsing errors |
| Fallback | If `None` is returned → In-process pipeline; if "" (empty context) → accepted as valid result |
| Prevention of infinite delegation | The MCP adapter hardcodes `rag_service_url=""`, so the in-process `augment()` will not re-delegate |
| Return value | `call_rag_service()` returns `(context: str ∣ None, status_code: int ∣ None, elapsed_ms: float)` — `status_code` and `elapsed_ms` can be used for diagnostics |

`RagConfig` Protocol (`shared/types.py`) configuration fields:
- `rag_service_url: str` — URL of the remote endpoint; if empty string, HTTP mode is disabled
- `rag_auth_token: str` — An arbitrary bearer token for the `X-RAG-Token` header; "" = no authentication (default)

#### `call_rag_service()` Function (`scripts/rag/pipeline_service.py`)

```python
def call_rag_service(
    rag_config: RagConfig,
    query: str,
    search_results: list[Hit],
) -> tuple[str | None, int | None, float]:
    ...
```

Returns `(context, status_code, elapsed_ms)`: `context` is the augmented text or `None`; `status_code` is the HTTP response code or `None`; `elapsed_ms` is total time in milliseconds.

The `"remote_empty"` case is NOT a fallback, it is a **SUCCESS**. It means the remote service responded with HTTP 200 but found no relevant context. In this case, the in-process pipeline is not executed. Do not confuse this with actual fallback events; both `remote_nonempty` and `remote_empty` have `fallback_reason = None`.

This classification result can be verified here:
- `get_diagnostics()["http_result_kind"]`

> **Note**: `get_diagnostics()["http_result_kind"]` (values: `remote_nonempty`/`remote_empty`/`in_process_fallback`) and `SearchDiagnostics.http_result_kind` (`rag.models_result.HttpResultKind` enum, values: `success`/`empty`/`error`/`not_used`) have similar names but are different fields with different vocabularies. See [rag_03_03_query_pipeline-context-and-diagnostics.md](rag_03_03_query_pipeline-context-and-diagnostics.md) section 4.2 for details.
> (Evidence classification: Explicit in code — `HttpAugmentResult.__init__` and `RagPipeline._run_http_augment`)
---

## Related Documents

- `rag_00_document-guide.md`
- `rag_01_system_overview.md`
- `rag_03_01_query_pipeline-overview.md`
- `rag_03_03_query_pipeline-context-and-diagnostics.md`
- `rag_03_04_query_pipeline-search-stages.md`
- `rag_03_05_query_pipeline-augment-stages.md`
- `rag_03_06_query_pipeline-helpers-and-cache.md`
- `rag_04_05_dto-types.md`
- `rag_05_1-configuration-reference.md`
- `rag_03_02_query_pipeline-rag-pipeline-class.md`

## Keywords

rag-pipeline-class
http-mode
rag
