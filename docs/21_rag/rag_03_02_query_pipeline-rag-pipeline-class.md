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

Configuration is resolved by `resolve_rag_config` into a fresh mapping that never mutates the caller's config. For a dict or object config the caller's values take precedence, then the explicitly passed `module_cfg`, then the built-in defaults. When no config object is passed, the config loader runs first and `module_cfg` is only a fallback. `rag_db_path` has no default and must be non-empty whenever `use_search` is enabled; construction fails together with any empty `llm_url` or `embed_url` when search is on.

### Implementation Note

- `RagPipeline` has no cache invalidation mechanism because it has no cache; see [rag_03_06_query_pipeline-helpers-and-cache.md](rag_03_06_query_pipeline-helpers-and-cache.md) section 6.

## Keywords

- rag-pipeline-class
- http-mode
- rag
