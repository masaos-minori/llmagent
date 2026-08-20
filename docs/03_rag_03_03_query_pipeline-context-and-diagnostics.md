---
title: "RAG Query Pipeline Context and Diagnostics"
category: rag
tags:
  - pipeline-context
  - search-diagnostics
related:
  - 03_rag_00_document-guide.md
  - 03_rag_01_system_overview.md
  - 03_rag_03_01_query_pipeline-overview.md
  - 03_rag_04_05_dto-types.md
  - 03_rag_05_1-configuration-reference.md
source:
  - 03_rag_03_01_query_pipeline-overview.md
---


# RAG Query Pipeline

- System Overview → [03_rag_01_system_overview.md](03_rag_01_system_overview.md)
- Configuration → [03_rag_05_1-configuration-reference.md](03_rag_05_1-configuration-reference.md)
- Type Definitions → [03_rag_04_05_dto-types.md](03_rag_04_01_dto-models_data.md)

---

## 4. PipelineContext Dataclass (`scripts/rag/stage.py`)

```python
ctx = PipelineContext(query="search query", history_context="conversation history")
```

| Field | Type | Default | Modified By |
|---|---|---|---|
| `query` | `str` | (Required) | — |
| `history_context` | `str` | `""` | — |
| `queries` | `list[str]` | `[]` | `MqeStage` |
| `search_results` | `list[list[RawHit]]` | `[]` | `SearchStage` |
| `merged` | `list[RagHit]` | `[]` | `FusionStage` |
| `reranked` | `list[RagHit]` | `[]` | `RerankStage` |
| `augment_result` | `str` | `""` | `AugmentStage` |
| `stage_results` | `list[StageResult]` | `[]` | `RagPipeline.run()` |
| `search_diagnostics` | `SearchDiagnostics` | `SearchDiagnostics()` (default_factory) | `SearchStage` — Replaced by a new `SearchDiagnostics` object containing populated `embed_ok`/`embed_failed`/`fts_errors` during search; In HTTP mode, the HTTP augment handler replaces it using `dataclasses.replace()` with `result_source`, `http_result_kind`, `remote_status_code`, and `remote_latency_ms`. |

### 4.2 SearchDiagnostics (`scripts/rag/models_result.py`)

```python
from rag.models_result import SearchDiagnostics, ResultSource, HttpResultKind
```

For detailed field lists, types, and default values, see <a href="../03_rag_04_02_dto-models_result.md">docs/03_rag_04_02_dto-models_result.md</a>. This section describes boundary conditions and ownership specifically in HTTP mode.

#### Boundary Conditions (Boundary and ownership)

Note that the name `http_result_kind` is used in two different value systems; do not confuse them (Explicit in code).

- `SearchDiagnostics.http_result_kind` (this section, `HttpResultKind` enum in `rag/models_result.py`) has 4 values: `SUCCESS` / `EMPTY` / `ERROR` / `NOT_USED`. It is set within the HTTP augment execution in `pipeline.py` as either `HttpResultKind.SUCCESS` (non-empty), `HttpResultKind.EMPTY` (`""`), or `HttpResultKind.ERROR` (`None`) via the `RagPipeline._run_http_augment()` method.
- `get_diagnostics()["http_result_kind"]` (via `RagPipeline._http_result_kind` attribute, `HttpAugment.run()`) uses 3 string literals: `"remote_nonempty"` / `"remote_empty"` / `"in_process_fallback"`. These are calculated in `HttpAugment.run()` and copied in `RagPipeline._run_http_augment()`.

Both represent the same HTTP call results but use different vocabularies and granularities; one cannot be directly derived from the other.

### 4.3 get_diagnostics() Return Value (`RagPipeline.get_diagnostics()`)

```python
pipeline.get_diagnostics() -> dict
```

Returns structured diagnostic information with the following keys:

| Key | Type | Description |
|---|---|---|
| `stage_results` | `list[dict]` | Results per stage (same as `last_stage_results`) |
| `timings` | `dict[str, float]` | Actual duration in seconds for each stage (same as `last_timings`) |
| `fetch_result` | `dict \| None` | Fetch result: `{hits: int, min_score_applied: float}` or `None` |
| `fusion_mode` | `str` | `"rrf"` or `"dedup_only"` |
| `http_result_kind` | `str \| None` | Classification for HTTP mode (same as `_http_result_kind`) |
| `fallback_count` | `int` | Number of stages where fallback occurred |
| `fallback_reasons` | `list[str]` | List of fallback reasons for all stages |
| `refiner_fallback_count` | `int` | Number of times the refiner fell back |
| `refiner_returned_empty` | `int` | Number of times the refiner returned empty content |
| `refiner_exception_count` | `int` | Number of exceptions caught in the refiner |
| `refiner_exception` | `bool` | `True` if any exception occurred in the refiner |
| `hit_counts` | `dict[str, int]` | `{merged: int}` — Hits after merging |
| `search_diagnostics` | `dict` | `{embed_ok, embed_failed, fts_errors, degraded}` |

> **Note:** In HTTP mode, `fetch_result` might contain stale values from the previous in-process execution rather than the current call's result. This is because `RagPipeline._run_http_augment()` does not call `self.run()` upon an HTTP success (see `self.last_fetch_result` updates in `RagPipeline.run()`, `RagPipeline._run_http_augment()`, and the `call_rag_service` function for details).

**Safe to call before `run()` / `augment()`** — returns empty/zero values. Callers should serialize using `orjson.dumps(pipeline.get_diagnostics())`.

``` text
StageResult = TypedDict with keys:
  stage_name: str         — class name of the stage
  status: str             — "success" | "fallback" | "failure"
  elapsed_seconds: float  — wall-clock seconds for the stage
  fallback_reason: str | None — reason when status is "failure" or "fallback"; None on success
```

`RagPipeline.run()` records a `StageResult` for each stage and makes the full list available via `pipeline.last_stage_results: list[StageResult]`. The same list is also stored in `PipelineContext.stage_results` for debugging and inspection.

---

## Related Documents

- `03_rag_00_document-guide.md`
- `03_rag_01_system_overview.md`
- `03_rag_03_01_query_pipeline-overview.md`
- `03_rag_04_05_dto-types.md`
- `03_rag_05_1-configuration-reference.md`

## Keywords

pipeline-context
search-diagnostics
rag
