---
title: "6.3 types.py (`scripts/rag/types.py`)"
area: rag
tags:
  - rag
  - dto
  - data-model
related:
  - 03_rag_00_document-guide.md
  - 03_rag_04_05_dto-types.md
source:
  - 03_rag_04_05_dto-types.md
---


# 6.3 types.py (`scripts/rag/types.py`)

**RagQuery** — A query with optional context.

| Field | Type | Default | Description |
|---|---|---|---|
| `query` | `str` | (required) | Query string |
| `context` | `str` | `""` | Optional context |

**PipelineRunResult** — Pipeline execution result.

| Field | Type | Description |
|---|---|---|
| `queries` | `list[str]` | Set of queries expanded by MQE |
| `search_results` | `list[list[RawHit]]` | Search results per query |
| `merged` | `list[RagHit]` | Hit results integrated by RRF |
| `reranked` | `list[RagHit]` | Hit results after reranking |
| `stage_results` | `list[StageResult]` | Execution results for each stage |
| `diagnostics` | `SearchDiagnostics` | Search diagnostic information |

## Implementation Notes

- The origin of the result ("remote/local/fallback") is maintained in `rag/models_result.py` within `SearchDiagnostics.result_source` (`ResultSource` enum), which is set inside `RagPipeline.augment()` depending on the success or failure of the HTTP mode.
  [Explicit in code]

## Related Documents

- [03_rag_04_05_dto-types.md](03_rag_04_05_dto-types.md)
- [03_rag_04_04_dto-models_config.md](03_rag_04_04_dto-models_config.md)

## Keywords

dto
data-model
pipeline-result
