---
title: "RAG Query Pipeline"
area: rag
tags:
  - pipeline-overview
  - pipeline-stage
related:
  - rag_00_document-guide.md
  - rag_01_system_overview.md
  - rag_03_02_query_pipeline-rag-pipeline-class.md
  - rag_03_03_query_pipeline-context-and-diagnostics.md
  - rag_03_04_query_pipeline-search-stages.md
  - rag_03_05_query_pipeline-augment-stages.md
  - rag_03_06_query_pipeline-helpers-and-cache.md
  - rag_03_07_query_pipeline-tests.md
  - rag_04_dto-models-types.md
  - rag_05_01-configuration-reference.md
---


# RAG Query Pipeline

- System Overview → [rag_01_system_overview.md](rag_01_system_overview.md)
- Configuration → [rag_05_01-configuration-reference.md](rag_05_01-configuration-reference.md)
- Type Definitions → [rag_04_dto-models-types.md](rag_04_dto-models-types.md)

---

## 1. Pipeline Overview

`RagPipeline` executes its stages in order. Each stage implements the `PipelineStage` Protocol and modifies a shared `PipelineContext` dataclass in-place.

``` text
RagPipeline.augment(query)
  → use_search=False? → returns ""
  → run(query, db, history_context)
      [1] MqeStage         — Expands query into N variants
      [2] SearchStage      — Executes KNN + BM25 per variant
      [3] FusionStage      — Merges via RRF (Σ 1/(rrf_k+rank); rrf_k is configurable), or deduplication only when use_rrf=False
      [4] RerankStage      — Scoring via Cross-Encoder; filtered by rag_min_score; limits chunks per document URL (`deduplicate_chunks`) after reranking
      [5] AugmentStage     — Formats as [RAG_CONTEXT_START]...[RAG_CONTEXT_END]
  → use_refiner=True? → refine_context() (compresses chunks; falls back to raw chunks on error)
  → Returns context block string
```

**Caller:** `RagPipelineMCPService` (`scripts/mcp_servers/rag_pipeline/rag_pipeline_service.py`). The Agent REPL does not call `RagPipeline` directly; it calls the `rag_run_pipeline` MCP tool.

### augment() Result Chain

`augment()` determines the final result through the following sequence. The refiner is the only step that can hand over to the next step by returning `None` (Explicit in code).

| Step | Produces | Fallback Trigger | Final Result | Diagnostics |
|---|---|---|---|---|
| 1. Search Pipeline | `ctx.reranked` (list of ranked chunks) | Not a fallback/final step — produces input for subsequent steps | N/A (intermediate) | `last_search_diagnostics` (`SearchDiagnostics`) |
| 2. Refiner | Compressed text (`str`) or `None` | Returns `None` | Compressed/refined context text | `last_stage_results` (`StageResult(stage_name="Refiner")`; `status="success"` or `"fallback"`) |
| 3. Raw Chunks | Formatted text (`str`) | Reached if Step 2 returned `None`, or if `use_refiner=False` | Chunk-formatted context text | Not directly tracked — inferable from absence of a "success"/"fallback" `StageResult` for Refiner combined with `use_refiner=False`, or from `Refiner`'s `StageResult` showing `status="fallback"` |

**Identity vs Truthiness (Explicit in code):** The refiner result is determined using an identity check (`is not None`), not a truthiness check, so only an explicit `None` hands over to the raw chunks.

**On DB Connection Failure (Explicit in code):** If opening the DB from `self._rag_db_path` raises `sqlite3.OperationalError` or `sqlite3.DatabaseError`, the DB connection layer wraps it in `RuntimeError` and `augment()` raises a `RagPipelineError` (the error is surfaced to the caller, not swallowed and not followed by a fallback).

### MCP Server Call Path

``` text
MCP Client
  → scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py (HTTP route)
    → RagPipelineMCPService.run_pipeline() (rag_pipeline_service.py)
      → RagPipeline.augment() (scripts/rag/pipeline.py), which runs the in-process stages through RagPipeline.run()
```

Detailed `RagPipeline` class info → [rag_03_02_query_pipeline-rag-pipeline-class.md](rag_03_02_query_pipeline-rag-pipeline-class.md)

---

## 2. PipelineStage Protocol (`scripts/rag/stage.py`)

Each stage implements `async run(ctx, **kwargs)` (`scripts/rag/stage.py`).

`kwargs` can include stage-specific arguments such as `db: SQLiteHelper`.
Stages modify `ctx` in-place and do not return values.

---

## Keywords

- pipeline-overview
- pipeline-stage
- rag
