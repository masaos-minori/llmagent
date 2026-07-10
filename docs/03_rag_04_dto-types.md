---
title: "6.3 types.py (`scripts/rag/types.py`)"
category: rag
tags:
  - rag
  - dto
  - data-model
related:
  - 03_rag_00_document-guide.md
  - 03_rag_04_data_model_and_interfaces.md
source:
  - 03_rag_04_data_model_and_interfaces.md
---

# 6.3 types.py (`scripts/rag/types.py`)

### 6.3 types.py (`scripts/rag/types.py`)

**RagQuery** — Query with optional context.

| Field | Type | Default | Description |
|---|---|---|---|
| `query` | `str` | (required) | Query string |
| `context` | `str` | `""` | Optional context |

**PipelineRunResult** — Pipeline run outcome.

| Field | Type | Description |
|---|---|---|
| `queries` | `list[str]` | MQE-expanded queries |
| `search_results` | `list[list[RawHit]]` | Per-query search results |
| `merged` | `list[RagHit]` | RRF-merged hits |
| `reranked` | `list[RagHit]` | Post-rerank hits |
| `stage_results` | `list[StageResult]` | Per-stage outcomes |
| `diagnostics` | `SearchDiagnostics` | Search diagnostics |
| `result_source` | `str \| None` | Result source (remote/local/fallback) |


## Related Documents

- [03_rag_04_data_model_and_interfaces.md](03_rag_04_dto-models_data.md)

## Keywords

dto
data-model
