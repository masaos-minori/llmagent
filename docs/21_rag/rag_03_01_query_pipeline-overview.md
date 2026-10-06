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
  - rag_05_1-configuration-reference.md
---


# RAG Query Pipeline

- System Overview → [rag_01_system_overview.md](rag_01_system_overview.md)
- Configuration → [rag_05_1-configuration-reference.md](rag_05_1-configuration-reference.md)
- Type Definitions → [rag_04_dto-models-types.md](rag_04_dto-models-types.md)

---

## 1. Pipeline Overview

`RagPipeline` executes five stages in order. Each stage implements the `PipelineStage` Protocol and modifies a shared `PipelineContext` dataclass in-place.

``` text
RagPipeline.augment(query)
  → use_search=False? → returns ""
  → rag_service_url is configured? → call_rag_service() → fallback to in-process execution on failure
  → run(query, db, history_context)
      [1] MqeStage         — Expands query into N variants
      [2] SearchStage      — Executes KNN + BM25 per variant
      [3] FusionStage      — Merges via RRF (Σ 1/(rrf_k+rank); rrf_k is configurable)
      [4] RerankStage      — Scoring via Cross-Encoder; filtered by rag_min_score; limits chunks per document URL (`deduplicate_chunks`) after reranking
      [5] AugmentStage     — Formats as [RAG_CONTEXT_START]...[RAG_CONTEXT_END]
  → use_refiner=True? → refine_context() (compresses chunks; falls back to raw chunks on error)
  → Returns context block string
```

**Caller:** `scripts/mcp_servers/rag_pipeline/rag_pipeline_service.py` (`RagPipelineMCPService`). The Agent REPL does not call `RagPipeline` directly.

### augment() Fallback Chain (`scripts/rag/pipeline.py`)

`augment()` determines the final result through the following sequence. Each step only falls back to the next if it returns `None` (Explicit in code).

| Step | Produces | Fallback Trigger | Final Result | Diagnostics |
|---|---|---|---|---|
| 1. HTTP Mode | `str` (including empty string) or `None` | Returns `None` | HTTP response body or empty string | `last_stage_results` (via `_augment_refiner.last_stage_results`, `pipeline.py`), `last_search_diagnostics` (`SearchDiagnostics`, `pipeline.py`) |
| 2. Search Pipeline | `ctx.reranked` (list of ranked chunks) | Not a fallback/final step — produces input for subsequent steps | N/A (intermediate) | `last_search_diagnostics` (`SearchDiagnostics`, populated via `RagPipelineStageLifecycle`, `pipeline.py`) |
| 3. Refiner | Compressed text (`str`) or `None` | Returns `None` | Compressed/refined context text | `last_stage_results` (`StageResult(stage_name="Refiner")`, appended in `augment.py`; `status="success"` or `"fallback"`) |
| 4. Raw Chunks | Formatted text (`str`) | Reached if Step 1 or Step 3 returned `None`, or if `use_refiner=False` | Chunk-formatted context text | Not directly tracked — inferable from absence of a "success"/"fallback" `StageResult` for Refiner combined with `use_refiner=False`, or from `Refiner`'s `StageResult` showing `status="fallback"` |

**Identity vs Truthiness (Explicit in code):** Results for HTTP mode and the refiner are determined using identity checks (`is not None`), not truthiness checks. Therefore, an empty string `""` returned by HTTP mode is treated as a valid result, and fallback only occurs when `None` is explicitly returned. This allows distinguishing between "searched but found 0 results" and "not yet searched."

**On DB Connection Failure (Explicit in code):** If opening the DB from `self._rag_db_path` raises `sqlite3.OperationalError` or `sqlite3.DatabaseError`, the DB connection layer wraps it in `RuntimeError` and `augment()` raises a `RagPipelineError` (it catches and falls back, it doesn't just swallow the error).

### MCP Server Call Path

``` text
MCP Client
  → scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py (HTTP route)
    → RagPipelineMCPService.run_pipeline() (rag_pipeline_service.py)
      → RagPipeline.run() (scripts/rag/pipeline.py)
```

Detailed `RagPipeline` class info $\rightarrow$ [rag_03_02_query_pipeline-rag-pipeline-class.md](rag_03_02_query_pipeline-rag-pipeline-class.md)

---

## 2. PipelineStage Protocol (`scripts/rag/stage.py`)

```python
from rag.stage import PipelineStage, PipelineContext

class MyStage(PipelineStage):
    async def run(self, ctx: PipelineContext, **kwargs: Any) -> None:
        ...
```

`kwargs` can include stage-specific arguments such as `db: SQLiteHelper`.
Stages modify `ctx` in-place and do not return values.

---

## Keywords

pipeline-overview
pipeline-stage
rag
