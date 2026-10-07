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
  - rag_04_dto-models-types.md
  - rag_05_01-configuration-reference.md
---


# RAG Query Pipeline

- System Overview → [rag_01_system_overview.md](rag_01_system_overview.md)
- Configuration → [rag_05_01-configuration-reference.md](rag_05_01-configuration-reference.md)
- Type Definitions → [rag_04_dto-models-types.md](rag_04_dto-models-types.md)

---

## 2. RagPipeline Class (`scripts/rag/pipeline.py`)

```python
from rag.pipeline import RagPipeline, RagPipelineError
```

> **Note**: `fetch_full_document` is not provided by `rag/pipeline.py`. Its actual implementation is defined in `rag/repository.py` (`from rag.repository import fetch_full_document`). Similarly, `sanitize_document` is a function from `rag/utils.py` and does not exist in `rag.pipeline`. Actual imports in test and implementation code are only `from rag.pipeline import RagPipeline, RagPipelineError`.
> (Explicit in code — `scripts/rag/pipeline.py` import statements, `fetch_full_document()` function in `scripts/rag/repository.py`)

The constructor of this class is configured by passing `module_cfg`. Please refer to the source code for details.

Refer to the source code for a list of public attributes and methods.

### Implementation Note

- `RagPipeline` has no cache invalidation mechanism. This is verified by `tests/rag/test_rag_pipeline_no_cache_freshness.py`.

### HTTP Mode (`rag_service_url`)

If `rag_service_url` is not empty, `augment()` delegates to an external RAG service via `call_rag_service()` in `scripts/rag/pipeline_service.py` instead of executing the in-process pipeline.

| Behavior | Details |
|---|---|
| Authentication | If `rag_auth_token != ""` the `X-RAG-Token: {rag_auth_token}` header is added (default: no header) |
| Timeout | Fixed per-HTTP-attempt timeout (connection + read), hardcoded in `call_rag_service()` |
| Retries | Bounded retries for 5xx or transport errors with exponential backoff; no retries for 4xx or JSON parsing errors |
| Fallback | If `None` is returned → In-process pipeline; if "" (empty context) → accepted as valid result |
| Prevention of infinite delegation | The MCP adapter hardcodes `rag_service_url=""`, so the in-process `augment()` will not re-delegate |
| Return value | `call_rag_service()` returns `(context: str ∣ None, status_code: int ∣ None, elapsed_ms: float)` — `status_code` and `elapsed_ms` can be used for diagnostics |

`RagConfig` Protocol (`shared/types.py`) configuration fields:
- `rag_service_url: str` — URL of the remote endpoint; if empty string, HTTP mode is disabled
- `rag_auth_token: str` — An arbitrary bearer token for the `X-RAG-Token` header; "" = no authentication (default)

#### `call_rag_service()` Function (`scripts/rag/pipeline_service.py`)

`call_rag_service()` is an `async` coroutine. It takes the shared async HTTP client, the RAG service URL, the query and the history context, plus keyword-only options for the auth token and for callbacks that receive the fetched hits and the fallback reason.

Returns `(context, status_code, elapsed_ms)`: `context` is the augmented text or `None`; `status_code` is the HTTP response code or `None`; `elapsed_ms` is total time in milliseconds.

The `"remote_empty"` case is NOT a fallback, it is a **SUCCESS**. It means the remote service responded with HTTP 200 but found no relevant context. In this case, the in-process pipeline is not executed. Do not confuse this with actual fallback events; both `remote_nonempty` and `remote_empty` have `fallback_reason = None`.

This classification result can be verified here:
- `get_diagnostics()["http_result_kind"]`

> **Note**: `get_diagnostics()["http_result_kind"]` and `SearchDiagnostics.http_result_kind` both carry the `rag.models_result.HttpResultKind` enum (`success`/`empty`/`error`/`not_used`/`auth_error`); the strings `remote_nonempty`/`remote_empty`/`in_process_fallback`/`auth_error` are internal to `HttpAugment` and are mapped to the enum before being exposed. See [rag_03_03_query_pipeline-context-and-diagnostics.md](rag_03_03_query_pipeline-context-and-diagnostics.md) section 4.2 for details.
> (Explicit in code — `HttpAugment` (`scripts/rag/http_augment.py`) and `AugmentRefiner.run_http_augment`)

## Keywords

- rag-pipeline-class
- http-mode
- rag
