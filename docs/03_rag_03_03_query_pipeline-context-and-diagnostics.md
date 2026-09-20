---
title: "RAG Query Pipeline Context and Diagnostics"
area: rag
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

Fields and defaults are defined in `scripts/rag/stage.py::PipelineContext`. Each
stage-populated field is written by a specific pipeline stage:

- `queries` — written by `MqeStage`
- `search_results` — written by `SearchStage`
- `merged` — written by `FusionStage`
- `reranked` — written by `RerankStage`
- `augment_result` — written by `AugmentStage`
- `stage_results` — appended by `RagPipeline.run()`
- `search_diagnostics` — replaced by `SearchStage` with a new `SearchDiagnostics`
  object containing populated `embed_ok`/`embed_failed`/`fts_errors` during search; in
  HTTP mode, the HTTP augment handler replaces it using `dataclasses.replace()` with
  `result_source`, `http_result_kind`, `remote_status_code`, and `remote_latency_ms`.

### 4.2 SearchDiagnostics (`scripts/rag/models_result.py`)

```python
from rag.models_result import SearchDiagnostics, ResultSource, HttpResultKind
```

For detailed field lists, types, and default values, see <a href="../03_rag_04_02_dto-models_result.md">docs/03_rag_04_02_dto-models_result.md</a>. This section describes boundary conditions and ownership specifically in HTTP mode.

#### Boundary Conditions (Boundary and ownership)

Note that the name `http_result_kind` is used in two different value systems; do not confuse them (Explicit in code).

- `SearchDiagnostics.http_result_kind` (this section, `HttpResultKind` enum in `rag/models_result.py`) has 4 values: `SUCCESS` / `EMPTY` / `ERROR` / `NOT_USED`. It is set within the HTTP augment execution in `pipeline.py` as either `HttpResultKind.SUCCESS` (non-empty), `HttpResultKind.EMPTY` (`""`), or `HttpResultKind.ERROR` (`None`) via the `RagPipeline.get_diagnostics()` method.
- `get_diagnostics()["http_result_kind"]` (via `HttpAugment.run()`) also carries an `HttpResultKind` enum value; the three string literals (`"remote_nonempty"` / `"remote_empty"` / `"in_process_fallback"`) exist only as an internal implementation detail inside `HttpAugment`: `HttpAugment._http_result_kind` stores these literals, but `_map_http_result_kind()` converts them to the `HttpResultKind` enum before either public field is set — the string literals never reach a caller reading either field.

Both `SearchDiagnostics.http_result_kind` and `get_diagnostics()["http_result_kind"]` carry the same `HttpResultKind` enum value by the time either is read from `get_diagnostics()` or `last_search_diagnostics`. The three string literals (`"remote_nonempty"` / `"remote_empty"` / `"in_process_fallback"`) exist only as an internal implementation detail inside `HttpAugment` (`http_augment.py`): `HttpAugment._http_result_kind` stores these literals, but `_map_http_result_kind()` converts them to the `HttpResultKind` enum before either public field is set — the string literals never reach a caller reading either field.

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
| `http_result_kind` | `HttpResultKind` | Classification for HTTP mode (enum value from `HttpResultKind`, never raw string literal) |
| `fallback_count` | `int` | Number of stages where fallback occurred |
| `fallback_reasons` | `list[str]` | List of fallback reasons for all stages |
| `refiner_fallback_count` | `int` | Number of times the refiner fell back |
| `refiner_returned_empty` | `int` | Number of times the refiner returned empty content |
| `refiner_exception_count` | `int` | Number of exceptions caught in the refiner |
| `refiner_exception` | `bool` | `True` if any exception occurred in the refiner |
| `hit_counts` | `dict[str, int]` | `{merged: int}` — Hits after merging |
| `search_diagnostics` | `dict` | `{embed_ok, embed_failed, fts_errors, degraded}` |

> **Note:** In HTTP mode, `fetch_result` may be stale when the HTTP call succeeds but returns zero hits (`selected_hits` is empty). In that case `_forward_fetch_result()` skips the callback invocation (augments.py:104: `if selected_hits:` guard), so `last_fetch_result` retains its prior value. On normal HTTP success with non-empty hits, the callback chain is: `HttpAugment` → `AugmentRefiner._forward_fetch_result(selected_hits)` → `RagPipeline.__init__`'s `set_fetch_result` callback → `setattr(self, "last_fetch_result", fetch_result)`.

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
