---
title: "6.2 models_result.py (`scripts/rag/models_result.py`)"
category: rag
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

| Field | Type | Default | Description |
|---|---|---|---|
| `success` | `bool` | (required) | Whether execution succeeded |
| `processed` | `int` | (required) | Number of processed chunks |
| `failed` | `int` | (required) | Number of failures |
| `errors` | `list[str]` | `[]` | Error messages |

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
| Field | Type | Default | Description |
|---|---|---|---|
| `embed_ok` | `int` | `0` | Count of successful embedding calls |
| `embed_failed` | `int` | `0` | Count of failed embedding calls |
| `fts_errors` | `int` | `0` | Count of FTS5 query errors |

#### Fields Added After HTTP Introduction (Meaningful only in Remote mode)
These fields are only meaningful when the search is delegated to a remote HTTP RAG service; they remain at their default values during pure local execution.

| Field | Type | Default | Description |
|---|---|---|---|
| `result_source` | `ResultSource` | `LOCAL` | Source of result (in `remote` mode) |
| `http_result_kind` | `HttpResultKind` | `NOT_USED` | Classification of HTTP result (in `remote` mode) |
| `remote_status_code` | `int \| None` | `None` | HTTP status code from the remote RAG service |
| `remote_latency_ms` | `float \| None` | `None` | Latency of remote call (ms) |
| `fallback_reason` | `str \| None` | `None` | Reason for in-process fallback (if applicable) |

## Implementation Notes

- `ResultSource` and `HttpResultKind` are defined as `StrEnum`. All other DTOs (`ExpandedQuerySet` and below) are defined as `@dataclass(frozen=True)`. This follows the design policy of ensuring immutability across the entire DTO layer, similar to `03_rag_04_01_dto-models_data.md` (Explicit in code).
- The fields `result_source`, `http_result_kind`, `remote_status_code`, `remote_latency_ms`, and `fallback_reason` in `SearchDiagnostics` are categorized as "Remote mode fields (new)" in the code comments (Explicit in code, `scripts/rag/models_result.py`). While `embed_ok`, `embed_failed`, and `fts_errors` are existing counters from local execution, the remote fields were added after the introduction of the HTTP RAG service.
- `fallback_reason` is set in `scripts/rag/pipeline.py` and `scripts/rag/http_augment.py` to record the reason for in-process fallback when an HTTP call fails (Explicit in code).

## Related Documents

- [03_rag_04_01_dto-models_data.md](03_rag_04_01_dto-models_data.md)
- [03_rag_00_document-guide.md](03_rag_00_document-guide.md)
- `00_security_01_architecture-and-trust-boundaries.md` — システムセキュリティアーキテクチャ / 信頼境界 / 脅威モデル / 認証認可 / 監査 / ローカルvs本番 / Fail-open/Fail-closed / プロンプトインジェクション責任境界

## Keywords

dto
data-model
frozen-dataclass
SearchDiagnostics
