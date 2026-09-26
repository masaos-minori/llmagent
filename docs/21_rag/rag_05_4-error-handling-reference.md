---
title: "4. Error Handling Reference"
area: rag
tags:
  - rag
  - configuration
related:
  - rag_00_document-guide.md
  - rag_05_1-configuration-reference.md
source:
  - rag_05_1-configuration-reference.md
---

# 4. Error Handling Reference

## Crawler

All Crawler-level failures are non-fatal at URL granularity. An HTTP failure is
retried with backoff before falling through to the same per-URL exception handling
that an unhandled exception or an unsupported `lang` value also hits, each of which
skips just that URL without stopping the overall crawl — see
`scripts/rag/ingestion/crawler.py` for the exact retry count/backoff formula.

## ChunkSplitter

| Error | Action |
|---|---|
| Sudachi tokenization error | Return `""`; skip chunk; `WARNING` |
| Failure at file level | `ERROR` (with traceback); continue to next file |
| Existing chunks | Skip unless `--force` is specified |

## Pipeline Utils — Artifact Validation (`read_crawl_json()` / `read_chunk_json()`)

Both canonical artifact readers (`scripts/rag/ingestion/pipeline_utils.py`) raise
`ChunkFormatError` (`scripts/rag/exceptions.py:27`, a `RagLayerError` and `ValueError`
subclass) on any validation failure — there is no silent-default fallback path in
either reader (contrast with the legacy `read_json_file()`, documented as historical
in [rag_02_08_ingestion_pipeline-shared.md](rag_02_08_ingestion_pipeline-shared.md)).

| Error | Action |
|---|---|
| File read failure (`OSError`) | `ChunkFormatError` |
| JSON parse failure | `ChunkFormatError` |
| Parsed JSON is not an object | `ChunkFormatError` |
| Missing one or more required keys (exact-key-set check; 8 keys for crawl, 13 for chunk) | `ChunkFormatError` |
| Unknown key present beyond the required 13 (chunk artifacts only; `schema_version`/`artifact_type`/`created_by` are exempted) | `ChunkFormatError` |
| Required-classified field is missing, `null`, or the wrong type (`_validate_str`) | `ChunkFormatError` |
| Conditional-classified field has the wrong type (`_validate_str_or_empty`) | `ChunkFormatError` |
| Nullable-classified field is present but neither `str` nor `null` (`_validate_nullable_str`) | `ChunkFormatError` |
| `chunk_index` is `bool`, non-`int`, or negative (`_validate_int_non_negative`; `bool` explicitly rejected before the `int` check) | `ChunkFormatError` |
| Crawl artifact only: `content` is empty and `code_blocks` is also empty (cross-field rule) | `ChunkFormatError` |

**Catch guidance**: Callers should catch `ChunkFormatError` specifically, not the broader `RagLayerError` base class. This matches every actual catch site in the codebase — `chunk_grouping.py:30`, `chunk_splitter.py:197` (as part of `(FileNotFoundError, ChunkFormatError)`), `file_routing.py:52,101`, and `ingester.py:217,235,348`. No catch site was found using the wrong exception type as of this cycle's search.

For the full per-field Required/Nullable/Conditional classification referenced above,
see the canonical table in
[rag_02_03_ingestion_pipeline-chunksplitter.md](rag_02_03_ingestion_pipeline-chunksplitter.md).

### ChunkFormatError Classification Guidance

#### Hierarchy position

`ChunkFormatError` is defined in `scripts/rag/exceptions.py` as a subclass of both
`RagLayerError` (the rag-layer base class) and `ValueError`. Its five sibling classes
under `RagLayerError` are:

| Class | Docstring-derived purpose |
|---|---|
| `EmbeddingSchemaError` | Raised when an embedding service response does not match expected schema |
| `PipelineValidationError` | Raised when a pipeline stage receives invalid configuration or input |
| `SearchQueryError` | Raised when a search query cannot be executed |
| `TokenizationError` | Raised when a tokenization step fails |
| `UnknownMetadataError` | Raised when metadata field has an unexpected value |

Each class should be raised when its docstring condition applies — e.g., use
`SearchQueryError` for an unexecutable search query, not a malformed chunk document.

#### Catch-site pattern

Every current caller in the repository catches `ChunkFormatError` specifically rather
than `RagLayerError` or `ValueError`:

- `scripts/rag/ingestion/chunk_splitter.py:197` — `except (FileNotFoundError, ChunkFormatError)`
- `scripts/rag/ingestion/file_routing.py:52,101` — `except ChunkFormatError`
- `scripts/rag/ingestion/ingester.py:217,235,348` — `except ChunkFormatError`
- `scripts/rag/ingestion/chunk_grouping.py:30` — `except ChunkFormatError`

New code should follow the same pattern: catch `ChunkFormatError` specifically, not its
base classes.

#### Known hierarchy deviation

Tracked as Known Issue CI-018 in
`docs/governance_03_issue-and-uncertainty-management.md`. `RagRerankError`
and `RagPipelineError` are defined outside `scripts/rag/exceptions.py` (in
`llm_prompts.py` and `pipeline.py` respectively), inheriting from `RuntimeError` rather
than `RagLayerError`. This fragmentation arose from three independent refactoring efforts
at different times, each introducing its own exception class without referencing the others.
No ADR or design document records a rationale for keeping them separate.

## RagIngester

| Error | Action |
|---|---|
| Embedding API failure | Retry with exponential backoff up to `embed_retry` |
| Retry limit reached (single chunk) | `WARNING`; skip chunk; continue |
| Invalid `lang` value | `ValueError`; skip URL group; `ERROR` (with traceback) |
| Invalid `fetched_at` (incoming or stored) | `ETagManager._is_stale_update()` raises `ValueError` — `Invalid incoming timestamp: {value}` or `Invalid stored timestamp: {value}` (message text is the only current distinction; no separate exception classes). Uncaught at the call site (`RagIngester.ingest_url_group()`), it propagates to the same catch-all as "Invalid `lang` value" above: skip URL group; `ERROR` (with traceback). See [rag_02_06_ingestion_pipeline-supporting-components.md section 4.8.1](rag_02_06_ingestion_pipeline-supporting-components.md#481-freshness-comparison-edge-cases-and-error-handling). |

## RagPipeline

| Error | Action |
|---|---|
| DB open error | Raises `RagPipelineError` (does not return `""`) |
| `use_search=False` | Immediately returns `""` |
| Failure when setting `rag_service_url` | Fallback to in-process pipeline |
| Cross-encoder failure | `RagRerankError` is caught as a `RuntimeError`, and `StageResult.status="failure"` is recorded, with a warning logged. The pipeline continues with `ctx.reranked=[]` (no fallback to RRF). If `use_rerank=False`, RRF ordering and deduplication are used instead. |
| Startup config validation failure | `RagPipeline.__init__()` runs `RagConfigValidator().validate()`; a failing result raises `ValueError` and aborts construction. Warnings-only results are logged and allow continuation. |

---


## Related Documents

- [rag_05_1-configuration-reference.md](rag_05_1-configuration-reference.md)
- [rag_04_04_dto-models_config.md](rag_04_04_dto-models_config.md)

## Keywords

configuration
exception-hierarchy
