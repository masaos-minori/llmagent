---
title: "6.3 types.py (`scripts/rag/types.py`)"
area: rag
tags:
  - rag
  - dto
  - data-model
related:
  - rag_00_document-guide.md
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

## Keywords

dto
data-model
pipeline-result
