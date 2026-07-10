---
title: "6.2 models_result.py (`scripts/rag/models_result.py`)"
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

# 6.2 models_result.py (`scripts/rag/models_result.py`)

### 6.2 models_result.py (`scripts/rag/models_result.py`)

**ResultSource** — Source of the RAG result.

| Value | Description |
|---|---|
| `"remote"` | HTTP RAG service |
| `"local"` | In-process pipeline |
| `"fallback"` | In-process fallback from HTTP failure |

**HttpResultKind** — Classification of HTTP RAG result.

| Value | Description |
|---|---|
| `"success"` | Non-empty context returned |
| `"empty"` | Empty context (valid empty result) |
| `"error"` | HTTP error path |
| `"not_used"` | HTTP mode not active |

**ExpandedQuerySet** — MQE expansion result.

| Field | Type | Description |
|---|---|---|
| `status` | `MqeStatus` | Expansion status |
| `queries` | `list[str]` | Expanded queries |

**SkipInfo** — Chunk processing skip record.

| Field | Type | Description |
|---|---|---|
| `path` | `str` | File path that was skipped |
| `reason` | `str` | Reason for skipping |

**RagSearchRequest** — Search request DTO.

| Field | Type | Default | Description |
|---|---|---|---|
| `query` | `str` | (required) | Search query |
| `top_k` | `int` | `5` | Number of results to return |

**RagSearchResult** — Search result DTO.

| Field | Type | Description |
|---|---|---|
| `query` | `str` | Original query |
| `hits` | `list[Any]` | Ranked hits (typed as `list[RankedHit]` after Phase 3-1) |
| `context_str` | `str` | Context string |

**PipelineExecutionResult** — Pipeline execution outcome.

| Field | Type | Default | Description |
|---|---|---|---|
| `success` | `bool` | (required) | Whether execution succeeded |
| `processed` | `int` | (required) | Number of chunks processed |
| `failed` | `int` | (required) | Number of failures |
| `errors` | `list[str]` | `[]` | Error messages |

**SearchDocsResult** — Search documents result.

| Field | Type | Description |
|---|---|---|
| `query` | `str` | Original query |
| `results` | `list[str]` | Result strings |
| `total` | `int` | Total result count |

**SanitizeResult** — Prompt injection sanitization result.

| Field | Type | Description |
|---|---|---|
| `text` | `str` | Sanitized text |
| `was_sanitized` | `bool` | Whether text was modified |
| `patterns_detected` | `list[str]` | Detected injection patterns |


## Related Documents

- [03_rag_04_data_model_and_interfaces.md](03_rag_04_dto-models_data.md)

## Keywords

dto
data-model
