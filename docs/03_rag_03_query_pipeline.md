---
title: "RAG Query Pipeline"
category: rag
tags:
  - pipeline-overview
  - pipeline-stage
related:
  - 03_rag_00_document-guide.md
  - 03_rag_01_system_overview.md
  - 03_rag_03_query_pipeline-rag-pipeline-class.md
  - 03_rag_03_query_pipeline-context-and-diagnostics.md
  - 03_rag_03_query_pipeline-search-stages.md
  - 03_rag_03_query_pipeline-augment-stages.md
  - 03_rag_03_query_pipeline-helpers-and-cache.md
  - 03_rag_03_query_pipeline-tests.md
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

## 1. Pipeline Overview

`RagPipeline` orchestrates 6 sequential stages (5 fixed + PluginHooks). Each stage implements
`PipelineStage` Protocol and mutates a shared `PipelineContext` dataclass in-place.

```
RagPipeline.augment(query)
  → use_search=False? → return ""
  → rag_service_url set? → call_rag_service() → fallback to in-process on failure
  → run(query, db, history_context, hook_strict=False)
      [1] MqeStage    — expand query into N variants
      [2] SearchStage — KNN + BM25 per variant
      [3] FusionStage — RRF merge (Σ 1/(rrf_k+rank); rrf_k configurable via config, default: 60)
      [4] RerankStage — cross-encoder scoring; filter by rag_min_score; post-rerank dedup by URL
      [5] PluginHooks — registered post-rerank hooks (error-isolated; strict mode re-raises); runs between RerankStage and AugmentStage (not a PipelineStage)
      [6] AugmentStage — format [RAG_CONTEXT_START]...[RAG_CONTEXT_END]
  → use_refiner=True? → refine_context() (compress chunks; fallback to raw on error)
  → return context block string
```

**Caller:** `scripts/mcp/rag_pipeline/service.py` (`RagPipelineMCPService`). Agent REPL does not
call `RagPipeline` directly.

### MCP サーバー呼び出しパス

```
MCP クライアント
  → scripts/mcp/rag_pipeline/server.py (HTTP ルート)
    → RagPipelineMCPService.run_pipeline() (service.py)
      → RagPipeline.run() (scripts/rag/pipeline.py)
```

For RagPipeline class details → [03_rag_03_query_pipeline-rag-pipeline-class.md](03_rag_03_query_pipeline-rag-pipeline-class.md)

---

## 2. PipelineStage Protocol (`scripts/rag/stage.py`)

```python
from rag.stage import PipelineStage, PipelineContext

class MyStage(PipelineStage):
    async def run(self, ctx: PipelineContext, **kwargs: object) -> None:
        ...
```

`kwargs` receives `db: SQLiteHelper` and other stage-specific args.
The stage mutates `ctx` in-place; it does not return a value.

---

## Related Documents

- `03_rag_00_document-guide.md`
- `03_rag_01_system_overview.md`
- `03_rag_03_query_pipeline-rag-pipeline-class.md`
- `03_rag_03_query_pipeline-context-and-diagnostics.md`
- `03_rag_03_query_pipeline-search-stages.md`
- `03_rag_03_query_pipeline-augment-stages.md`
- `03_rag_03_query_pipeline-helpers-and-cache.md`
- `03_rag_03_query_pipeline-tests.md`
- `03_rag_04_data_model_and_interfaces.md`
- `03_rag_05_configuration_and_operations.md`

## Keywords

pipeline-overview
pipeline-stage
rag
