---
title: "6.2 models_result.py (`scripts/rag/models_result.py`)"
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


# 6.2 models_result.py (`scripts/rag/models_result.py`)

**ResultSource** — Origin of the RAG result.

| Value | Description |
|---|---|
| `"remote"` | HTTP RAG service |
| `"local"` | In-process pipeline |
| `"fallback"` | In-process fallback on HTTP failure |

**HttpResultKind** — Classification of HTTP RAG results.

| Value | Description |
|---|---|
| `"success"` | Non-empty context returned |
| `"empty"` | Empty context (valid empty result) |
| `"error"` | HTTP error path |
| `"not_used"` | HTTP mode is inactive |

`ResultSource`/`HttpResultKind` are `StrEnum`; every other DTO in this module is
`@dataclass(frozen=True)`, following the DTO-layer immutability policy shared with
[03_rag_04_01_dto-models_data.md](03_rag_04_01_dto-models_data.md).

**ExpandedQuerySet** — MQE expansion results.

| Field | Type | Description |
|---|---|---|
| `status` | `MqeStatus` | Expansion status |
| `queries` | `list[str]` | Set of queries after expansion |

**SkipInfo** — Record of skipped chunk processing.

| Field | Type | Description |
|---|---|---|
| `path` | `str` | Path of the skipped file |
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
| `hits` | `list[Any]` | Ranked hit results (becomes `list[RankedHit]` from Phase 3-1 onwards) |
| `context_str` | `str` | Context string |

**PipelineExecutionResult** — Pipeline execution result.

Fields and defaults are defined in `scripts/rag/models_result.py::PipelineExecutionResult`.

**SearchDocsResult** — Document search result.

| Field | Type | Description |
|---|---|---|
| `query` | `str` | Original query |
| `results` | `list[str]` | Result strings |
| `total` | `int` | Total number of results |

**SanitizeResult** — Sanitization result for prompt injection.

| Field | Type | Description |
|---|---|---|
| `text` | `str` | Text after sanitization |
| `was_sanitized` | `bool` | Whether the text was modified |
| `patterns_detected` | `list[str]` | Detected injection patterns |

**SearchDiagnostics** — Diagnostic counters for a single search call.

The following table groups fields that are active depending on the execution mode (Local or Remote).

#### Local Execution Counters (Always aggregated)
Fields and defaults are defined in `scripts/rag/models_result.py::SearchDiagnostics`:
`embed_ok`, `embed_failed`, `fts_errors`.

#### Fields Added After HTTP Introduction (Meaningful only in Remote mode)
These fields are only meaningful when the search is delegated to a remote HTTP RAG service; they remain at their default values during pure local execution: `result_source`, `http_result_kind`, `remote_status_code`, `remote_latency_ms`, `fallback_reason`.

## Related Documents

- [03_rag_04_01_dto-models_data.md](03_rag_04_01_dto-models_data.md)
- [03_rag_00_document-guide.md](03_rag_00_document-guide.md)
- `security_01_architecture-and-trust-boundaries.md` — System security architecture / Trust boundaries / Threat modeling / AuthN/AuthZ / Auditing / Local vs Production / Fail-open/Fail-closed / Prompt injection responsibility boundaries

## Keywords

dto
data-model
frozen-dataclass
SearchDiagnostics
