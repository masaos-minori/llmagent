---
title: "RAG Query Pipeline Context and Diagnostics"
area: rag
tags:
  - pipeline-context
  - search-diagnostics
related:
  - rag_00_document-guide.md
  - rag_01_system_overview.md
  - rag_03_01_query_pipeline-overview.md
  - rag_04_dto-models-types.md
  - rag_05_01-configuration-reference.md
  - mcp_04_03_rag-pipeline-and-cicd.md
---


# RAG Query Pipeline

- System Overview → [rag_01_system_overview.md](rag_01_system_overview.md)
- Configuration → [rag_05_01-configuration-reference.md](rag_05_01-configuration-reference.md)
- Type Definitions → [rag_04_dto-models-types.md](rag_04_dto-models-types.md)

---

## 4. PipelineContext Dataclass (`scripts/rag/stage.py`)

Fields and defaults are defined in `scripts/rag/stage.py::PipelineContext`. Each
stage-populated field is written by a specific pipeline stage:

- `queries` — written by `MqeStage`
- `search_results` — written by `SearchStage`
- `merged` — written by `FusionStage`
- `reranked` — written by `RerankStage`
- `augment_result` — written by `AugmentStage`
- `stage_results` — appended by `RagPipeline.run()`
- `search_diagnostics` — replaced by `SearchStage` with a new `SearchDiagnostics`
  object containing populated `embed_ok`/`embed_failed`/`fts_errors` during search.

### 4.2 SearchDiagnostics (`scripts/rag/models_result.py`)

Field definitions: `SearchDiagnostics` in `scripts/rag/models_result.py` (summary in [rag_04_dto-models-types.md](rag_04_dto-models-types.md)). Its fields are the local-execution counters (`embed_ok`, `embed_failed`, `fts_errors`, `degraded`).

### 4.3 get_diagnostics() Return Value (`RagPipeline.get_diagnostics()`)

`RagPipeline.get_diagnostics()` returns a dict that groups: per-stage results and timings (`stage_results`, `timings`), the fetch result (`fetch_result`), the fusion mode (`fusion_mode`: `"rrf"` or `"dedup_only"`), fallback counters (`fallback_count`, `fallback_reasons`), refiner counters (see [rag_03_05_query_pipeline-augment-stages.md](rag_03_05_query_pipeline-augment-stages.md)), and the `search_diagnostics` summary including `degraded`. The authoritative key set is the method itself.

> **Note:** `fetch_result` is populated by `RagPipeline.run()` only. The `POST /v1/call_tool` result of the rag-pipeline MCP server has only `result` and `is_error`; the structured `selected_hits` field exists only on the direct `POST /rag_run_pipeline` response (see `mcp_04_03_rag-pipeline-and-cicd.md`).

**Safe to call before `run()` / `augment()`** — returns empty/zero values. Callers should serialize using `orjson.dumps(pipeline.get_diagnostics())`.

`RagPipeline.run()` records a `StageResult` (`stage_name`, `status`, `elapsed_seconds`, `fallback_reason`) for each stage; `status` is `"success"`, `"fallback"`, or `"failure"`, and `fallback_reason` is set only for the latter two. The full list is available as `pipeline.last_stage_results` and is also stored in `PipelineContext.stage_results` for debugging and inspection.

## Keywords

- pipeline-context
- search-diagnostics
- rag
