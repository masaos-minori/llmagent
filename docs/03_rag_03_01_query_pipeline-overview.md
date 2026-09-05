---
title: "RAG Query Pipeline"
area: rag
tags:
  - pipeline-overview
  - pipeline-stage
related:
  - 03_rag_00_document-guide.md
  - 03_rag_01_system_overview.md
  - 03_rag_03_02_query_pipeline-rag-pipeline-class.md
  - 03_rag_03_03_query_pipeline-context-and-diagnostics.md
  - 03_rag_03_04_query_pipeline-search-stages.md
  - 03_rag_03_05_query_pipeline-augment-stages.md
  - 03_rag_03_06_query_pipeline-helpers-and-cache.md
  - 03_rag_03_07_query_pipeline-tests.md
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

## 1. Pipeline Overview

`RagPipeline` executes five stages in order. Each stage implements the `PipelineStage` Protocol and modifies a shared `PipelineContext` dataclass in-place.

``` text
RagPipeline.augment(query)
  → use_search=False? → returns ""
  → rag_service_url is configured? → call_rag_service() → fallback to in-process execution on failure
  → run(query, db, history_context)
      [1] MqeStage         — Expands query into N variants
      [2] SearchStage      — Executes KNN + BM25 per variant
      [3] FusionStage      — Merges via RRF (Σ 1/(rrf_k+rank); rrf_k is configurable, default: 60)
      [4] RerankStage      — Scoring via Cross-Encoder; filtered by rag_min_score; de-duplicates by chunk_id after reranking
      [5] AugmentStage     — Formats as [RAG_CONTEXT_START]...[RAG_CONTEXT_END]
  → use_refiner=True? → refine_context() (compresses chunks; falls back to raw chunks on error)
  → Returns context block string
```

**Caller:** `scripts/mcp_servers/rag_pipeline/rag_pipeline_service.py` (`RagPipelineMCPService`). The Agent REPL does not call `RagPipeline` directly.

### augment() Fallback Chain (`scripts/rag/pipeline.py`)

`augment()` determines the final result through the following sequence. Each step only falls back to the next if it returns `None` (Explicit in code).

1. HTTP Mode: HTTP augment $\rightarrow$ `str` (including empty string) or `None` (fallback)
2. Search Pipeline: MQE + KNN/BM25 + RRF merge + Rerank $\rightarrow$ `ctx.reranked`
3. Refiner: `refine_context()` $\rightarrow$ compressed text (final) or `None` (fallback)
4. Raw Chunks: Formatted by chunk formatting function (final)

**Identity vs Truthiness (Explicit in code):** Results for HTTP mode and the refiner are determined using identity checks (`is not None`), not truthiness checks. Therefore, an empty string `""` returned by HTTP mode is treated as a valid result, and fallback only occurs when `None` is explicitly returned. This allows distinguishing between "searched but found 0 results" and "not yet searched."

**On DB Connection Failure (Explicit in code):** If opening the DB from `self._rag_db_path` raises `sqlite3.OperationalError` or `sqlite3.DatabaseError`, `augment()` re-raises a `RagPipelineError` (it catches and falls back, it doesn't just swallow the error).

### MCP Server Call Path

``` text
MCP Client
  → scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py (HTTP route)
    → RagPipelineMCPService.run_pipeline() (service.py)
      → RagPipeline.run() (scripts/rag/pipeline.py)
```

Detailed `RagPipeline` class info $\rightarrow$ [03_rag_03_02_query_pipeline-rag-pipeline-class.md](03_rag_03_02_query_pipeline-rag-pipeline-class.md)

---

## 2. PipelineStage Protocol (`scripts/rag/stage.py`)

```python
from rag.stage import PipelineStage, PipelineContext

class MyStage(PipelineStage):
    async def run(self, ctx: PipelineContext, **kwargs: object) -> None:
        ...
```

`kwargs` can include stage-specific arguments such as `db: SQLiteHelper`.
Stages modify `ctx` in-place and do not return values.

---

## Related Documents

- `03_rag_00_document-guide.md`
- `03_rag_01_system_overview.md`
- `03_rag_03_02_query_pipeline-rag-pipeline-class.md`
- `03_rag_03_03_query_pipeline-context-and-diagnostics.md`
- `03_rag_03_04_query_pipeline-search-stages.md`
- `03_rag_03_05_query_pipeline-augment-stages.md`
- `03_rag_03_06_query_pipeline-helpers-and-cache.md`
- `03_rag_03_07_query_pipeline-tests.md`
- `03_rag_04_05_dto-types.md`
- `03_rag_05_1-configuration-reference.md`

## Keywords

pipeline-overview
pipeline-stage
rag
