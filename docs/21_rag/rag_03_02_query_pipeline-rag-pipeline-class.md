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

`RagPipeline` is constructed from a flat `module_cfg` (the `RagConfig` Protocol) and exposes `augment()` and `run()`. See the source for the public attribute and method set.

### Implementation Note

- `RagPipeline` has no cache invalidation mechanism because it has no cache; see [rag_03_06_query_pipeline-helpers-and-cache.md](rag_03_06_query_pipeline-helpers-and-cache.md) section 6.

### HTTP Mode (`rag_service_url`)

If `rag_service_url` is not empty, `augment()` delegates to an external RAG service via `call_rag_service()` in `scripts/rag/pipeline_service.py` instead of executing the in-process pipeline. `rag_auth_token` is the outbound Bearer token for that service; an empty value sends no `Authorization` header.

| Behavior | Details |
|---|---|
| Authentication | If `rag_auth_token != ""` the `Authorization: Bearer {rag_auth_token}` header is added (default: no header); no other authentication header is sent |
| Timeout | Fixed per-HTTP-attempt timeout (connection + read), the module constant `_REQUEST_TIMEOUT_SECONDS` in `scripts/rag/pipeline_service.py` |
| Retries | Bounded retries for 5xx or transport errors with exponential backoff; no retries for 4xx or JSON parsing errors |
| Fallback | `transient_failure` (HTTP 5xx or transport error after retries, other 4xx, or `is_error` true) → In-process pipeline; `empty` ("" context) → accepted as valid result; `auth_error` (HTTP 401/403) → `RagPipelineError`, no in-process fallback (fail closed) |
| Prevention of infinite delegation | The MCP adapter hardcodes `rag_service_url=""`, so the in-process `augment()` will not re-delegate |
| Return value | `call_rag_service()` returns a frozen `CallRagResult(kind, result, status_code, latency_ms)` — `kind` is `success`, `empty`, `auth_error` or `transient_failure`; `result` is the augmented text, `""` for `empty`, or `None` for failures |

HTTP 401/403 yields `auth_error`, which `HttpAugment` maps to `http_result_kind="auth_error"` and `AugmentRefiner.run_http_augment` converts to `RagPipelineError`.

The `"remote_empty"` case is NOT a fallback, it is a **SUCCESS**. It means the remote service responded with HTTP 200 but found no relevant context. In this case, the in-process pipeline is not executed. Do not confuse this with actual fallback events; both `remote_nonempty` and `remote_empty` have `fallback_reason = None`.

> **Note**: `get_diagnostics()["http_result_kind"]` and `SearchDiagnostics.http_result_kind` both carry the `rag.models_result.HttpResultKind` enum (`success`/`empty`/`error`/`not_used`/`auth_error`); the strings `remote_nonempty`/`remote_empty`/`in_process_fallback`/`auth_error` are internal to `HttpAugment` and are mapped to the enum before being exposed. See [rag_03_03_query_pipeline-context-and-diagnostics.md](rag_03_03_query_pipeline-context-and-diagnostics.md) section 4.2 for details.
> (Explicit in code — `HttpAugment` in `scripts/rag/http_augment.py`)

## Keywords

- rag-pipeline-class
- http-mode
- rag
