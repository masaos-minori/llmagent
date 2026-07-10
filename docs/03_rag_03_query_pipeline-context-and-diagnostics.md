---
title: "RAG Query Pipeline Context and Diagnostics"
category: rag
tags:
  - pipeline-context
  - search-diagnostics
related:
  - 03_rag_00_document-guide.md
  - 03_rag_01_system_overview.md
  - 03_rag_03_query_pipeline.md
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
| `search_diagnostics` | `SearchDiagnostics` | `SearchDiagnostics()` (default_factory) | `SearchStage` — replaced entirely with a new `SearchDiagnostics` object populated with embed_ok/embed_failed/fts_errors during search; in HTTP mode, HTTP augment handler replaces it via `dataclasses.replace()` with `result_source`, `http_result_kind`, `remote_status_code`, `remote_latency_ms` |

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

### 4.3 get_diagnostics() Return Value (`scripts/rag/pipeline.py:562`)

```python
pipeline.get_diagnostics() -> dict
```

Returns structured diagnostics with the following keys:

| Key | Type | Description |
|---|---|---|
| `stage_results` | `list[dict]` | Per-stage outcomes (same as `last_stage_results`) |
| `timings` | `dict[str, float]` | Wall-clock seconds per stage (same as `last_timings`) |
| `fetch_result` | `dict \| None` | Fetch result: `{hits: int, min_score_applied: float}` or `None` |
| `fusion_mode` | `str` | `"rrf"` or `"dedup_only"` |
| `http_result_kind` | `str \| None` | HTTP mode classification (same as `_http_result_kind`) |
| `fallback_count` | `int` | Number of fallback stages |
| `fallback_reasons` | `list[str]` | Fallback reason strings from all stages |
| `refiner_fallback_count` | `int` | Number of refiner fallbacks |
| `refiner_returned_empty` | `int` | Count of refiner returns with empty content |
| `refiner_exception_count` | `int` | Count of refiner exceptions |
| `refiner_exception` | `bool` | True if any refiner exception occurred |
| `hit_counts` | `dict[str, int]` | `{merged: int}` — count of merged hits |
| `search_diagnostics` | `dict` | `{embed_ok, embed_failed, fts_errors, degraded}` |

**Safe to call before `run()` / `augment()`** — returns empty/zero values. Callers should serialize with `orjson.dumps(pipeline.get_diagnostics())`.

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

## Related Documents

- `03_rag_00_document-guide.md`
- `03_rag_01_system_overview.md`
- `03_rag_03_query_pipeline.md`
- `03_rag_04_data_model_and_interfaces.md`
- `03_rag_05_configuration_and_operations.md`

## Keywords

pipeline-context
search-diagnostics
rag
