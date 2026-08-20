---
title: "RAG Query Pipeline - RagPipeline Class Detail"
category: rag
tags:
  - rag-pipeline-class
  - http-mode
related:
  - 03_rag_00_document-guide.md
  - 03_rag_01_system_overview.md
  - 03_rag_03_01_query_pipeline-overview.md
  - 03_rag_03_03_query_pipeline-context-and-diagnostics.md
  - 03_rag_03_04_query_pipeline-search-stages.md
  - 03_rag_03_05_query_pipeline-augment-stages.md
  - 03_rag_03_06_query_pipeline-helpers-and-cache.md
  - 03_rag_04_05_dto-types.md
  - 03_rag_05_1-configuration-reference.md
source:
  - 03_rag_03_02_query_pipeline-rag-pipeline-class.md

---


# RAG Query Pipeline

- System Overview → [03_rag_01_system_overview.md](03_rag_01_system_overview.md)
- Configuration → [03_rag_05_1-configuration-reference.md](03_rag_05_1-configuration-reference.md)
- Type Definitions → [03_rag_04_05_dto-types.md](03_rag_04_01_dto-models_data.md)

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

- `invalidate_cache()` is intended to be called only after corpus changes that this pipeline instance is aware of; the caller (e.g., MCP service layer) is responsible for detecting corpus changes and explicitly calling it. The pipeline itself does not have a mechanism to detect DB changes and automatically invalidate the cache ("Call after any corpus-changing operation this pipeline instance is aware of").

## Related Documents

- `03_rag_00_document-guide.md`
- `03_rag_01_system_overview.md`
- `03_rag_03_01_query_pipeline-overview.md`
- `03_rag_03_03_query_pipeline-context-and-diagnostics.md`
- `03_rag_03_04_query_pipeline-search-stages.md`
- `03_rag_03_05_query_pipeline-augment-stages.md`
- `03_rag_03_06_query_pipeline-helpers-and-cache.md`
- `03_rag_04_05_dto-types.md`
- `03_rag_05_1-configuration-reference.md`
- `03_rag_03_02_query_pipeline-rag-pipeline-class.md`

## Keywords

rag-pipeline-class
http-mode
rag

---

## 2a. RagPipeline Class (`scripts/rag/pipeline.py`)

```python
from rag.pipeline import RagPipeline, RagPipelineError
```

> **Documentation vs. Implementation Mismatch**: `fetch_full_document` (`rag/repository.py`) and `sanitize_document` (`rag/utils.py`) are not provided by `rag.pipeline`. See [Part 1](03_rag_03_02_query_pipeline-rag-pipeline-class.md) for details.
> (Evidence classification: Explicit in code)

The constructor of this class configures it bypassing `module_cfg`. Please refer to the source code for details.

Refer to the source code for a list of public attributes and methods.

### Implementation Note

- `invalidate_cache()` is intended to be called only after corpus changes that this pipeline instance is aware of; the caller (e.g., MCP service layer) is responsible for detecting corpus changes and explicitly calling it. The pipeline itself does not have a mechanism to detect DB changes and automatically invalidate the cache ("Call after any corpus-changing operation this pipeline instance is aware of").

## Related Documents

- `03_rag_00_document-guide.md`
- `03_rag_01_system_overview.md`
- `03_rag_03_01_query_pipeline-overview.md`
- `03_rag_03_03_query_pipeline-context-and-diagnostics.md`
- `03_rag_03_04_query_pipeline-search-stages.md`
- `03_rag_03_05_query_pipeline-augment-stages.md`
- `03_rag_03_06_query_pipeline-helpers-and-cache.md`
- `03_rag_04_05_dto-types.md`
- `03_rag_05_1-configuration-reference.md`
- `03_rag_03_02_query_pipeline-rag-pipeline-class.md`

## Keywords

rag-pipeline-class
http-mode
rag

---

## 2b. RagPipeline Class (`scripts/rag/pipeline.py`)

```python
from rag.pipeline import RagPipeline, RagPipelineError
```

> **Documentation vs. Implementation Mismatch**: `fetch_full_document` (`rag/repository.py`) and `sanitize_document` (`rag/utils.py`) are not provided by `rag.pipeline`. See the Documentation vs. Implementation Mismatch note under "## 2. RagPipeline Class" at the top of this document for details.
> (Evidence classification: Explicit in code)

### HTTP Mode (`rag_service_url`)

If `rag_service_url` is not empty, `augment()` delegates to an external RAG service via `call_rag_service()` in `scripts/rag/pipeline_service.py` instead of executing the in-process pipeline.

| Behavior | Details |
|---|---|
| Authentication | If `rag_auth_token != ""` the `X-RAG-Token: {rag_auth_token}` header is added (default: no header) |
| Timeout | 10.0 seconds per HTTP attempt (connection + read) |
| Retries | Max 2 retries for 5xx or transport errors with exponential backoff (1s, 2s); no retries for 4xx or JSON parsing errors |
| Fallback | If `None` is returned $\rightarrow$ In-process pipeline; if `""` (empty context) $\rightarrow$ accepted as valid result |
| Prevention of infinite delegation | The MCP adapter hardcodes `rag_service_url=""`, so the in-process `augment()` will not re-delegate |
| Return value | `call_rag_service()` returns `(context: str \| None, status_code: int \| None, elapsed_ms: float)` — `status_code` and `elapsed_ms` can be used for diagnostics |

`RagConfig` Protocol (`shared/types.py`) configuration fields:
- `rag_service_url: str` — URL of the remote endpoint; if empty string, HTTP mode is disabled
- `rag_auth_token: str` — An arbitrary bearer token for the `X-RAG-Token` header; `""` = no authentication (default)

#### `call_rag_service()` Function (`scripts/rag/pipeline_service.py`)

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

Return Value Contract:

| Return Value | Condition |
|---|---|
| `str` (non-empty) | HTTP 200 and response body contains a `"result"` key with a non-empty string value |
| `""` (empty string) | HTTP 200 but `"result"` key is missing, `None`, or empty — accepted as a valid empty result |
| `None` | HTTP 4xx (no retry), exhausted retries for 5xx, transport error, or JSON parsing error — triggers fallback to in-process |

Side Effects:
- `set_fetch_result` is called along with a `TwoStageFetchResult` containing the fetch stage status and hit information extracted from the response body
- `set_fallback_reason` is called with a reason string during non-success paths (4xx, transport errors, etc.)

When `rag_service_url` is set, `augment()` categorizes the HTTP result and records it in `get_diagnostics()["http_result_kind"]` and `StageResult.fallback_reason`.

| `http_result_kind` | `StageResult` status | `fallback_reason` | Condition |
|---|---|---|---|
| `"remote_nonempty"` | `"success"` | `None` | HTTP call successful; non-empty context returned |
| `"remote_empty"` | `"success"` | `None` | HTTP 200 but `context` field is `""` — valid empty result, not a fallback |
| `"in_process_fallback"` | `"fallback"` | Error string | HTTP error; in-process RAG pipeline was executed instead |
| `None` | — | — | `rag_service_url` not set; HTTP mode not used |

The `"remote_empty"` case is NOT a fallback, it is a **SUCCESS**. It means the remote service responded with HTTP 200 but found no relevant context. In this case, the in-process pipeline is not executed. Do not confuse this with actual fallback events; both `remote_nonempty` and `remote_empty` have `fallback_reason = None`.

This classification result can be verified here:
- `get_diagnostics()["http_result_kind"]`

> **Note**: `get_diagnostics()["http_result_kind"]` (values: `remote_nonempty`/`remote_empty`/`in_process_fallback`) and `SearchDiagnostics.http_result_kind` (`rag.models_result.HttpResultKind` enum, values: `success`/`empty`/`error`/`not_used`) have similar names but are different fields with different vocabularies. See [03_rag_03_03_query_pipeline-context-and-diagnostics.md](03_rag_03_03_query_pipeline-context-and-diagnostics.md) §4.2 for details.
> (Evidence classification: Explicit in code — `HttpAugmentResult.__init__` and `RagPipeline._run_http_augment`)

---

## Related Documents

- `03_rag_00_document-guide.md`
- `03_rag_01_system_overview.md`
- `03_rag_03_01_query_pipeline-overview.md`
- `03_rag_03_03_query_pipeline-context-and-diagnostics.md`
- `03_rag_03_04_query_pipeline-search-stages.md`
- `03_rag_03_05_query_pipeline-augment-stages.md`
- `03_rag_03_06_query_pipeline-helpers-and-cache.md`
- `03_rag_04_05_dto-types.md`
- `03_rag_05_1-configuration-reference.md`
- `03_rag_03_02_query_pipeline-rag-pipeline-class.md`

## Keywords

rag-pipeline-class
http-mode
rag
