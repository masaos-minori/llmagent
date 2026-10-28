---
title: "Error Handling Reference"
area: rag
tags:
  - rag
  - configuration
related:
  - rag_00_document-guide.md
  - rag_05_01-configuration-reference.md
  - rag_02_01_ingestion_pipeline-overview.md
  - rag_03_01_query_pipeline-overview.md
  - rag_02_03_ingestion_pipeline-chunksplitter.md
  - rag_02_06_ingestion_pipeline-supporting-components.md
---

# Error Handling Reference

## Crawler

All Crawler-level failures are non-fatal at URL granularity. An HTTP failure is
retried with backoff before falling through to the same per-URL exception handling
that an unhandled exception or an unsupported `lang` value also hits, each of which
skips just that URL without stopping the overall crawl — see
`scripts/rag/ingestion/crawler.py` for the exact retry count/backoff formula.

## ChunkSplitter

| Error | Action |
|---|---|
| Sudachi tokenization error | `TokenizationError` propagates to `process_all()`; the entire file is aborted; `ERROR` (with traceback); continue to next file |
| Failure at file level | `ERROR` (with traceback); continue to next file |
| Existing chunks | Skip unless `--force` is specified |

## Pipeline Utils — Artifact Validation (`read_crawl_json()` / `read_chunk_json()`)

Both canonical artifact readers (`scripts/rag/ingestion/pipeline_utils.py`) raise
`ChunkFormatError` (`scripts/rag/exceptions.py`, a `RagLayerError` and `ValueError`
subclass) on any validation failure — there is no silent-default fallback path in
either reader.

| Error | Action |
|---|---|
| File read failure (`OSError`) | `ChunkFormatError` |
| JSON parse failure | `ChunkFormatError` |
| Parsed JSON is not an object | `ChunkFormatError` |
| Missing one or more required keys (exact-key-set check; separate key sets for crawl and chunk artifacts) | `ChunkFormatError` |
| Unknown key present beyond the required key set (chunk artifacts only; `schema_version`/`artifact_type`/`created_by` are exempted) | `ChunkFormatError` |
| Required-classified field is missing, `null`, or the wrong type (`_validate_str`) | `ChunkFormatError` |
| Conditional-classified field has the wrong type (`_validate_str_or_empty`) | `ChunkFormatError` |
| Nullable-classified field is present but neither `str` nor `null` (`_validate_nullable_str`) | `ChunkFormatError` |
| `chunk_index` is `bool`, non-`int`, or negative (`_validate_int_non_negative`; `bool` explicitly rejected before the `int` check) | `ChunkFormatError` |
| Crawl artifact only: `content` is empty and `code_blocks` is also empty (cross-field rule) | `ChunkFormatError` |

**Catch guidance**: Callers should catch `ChunkFormatError` specifically, not the broader `RagLayerError` base class (see Catch-site pattern below).

For the full per-field Required/Nullable/Conditional classification referenced above,
see the canonical table in
[rag_02_03_ingestion_pipeline-chunksplitter.md](rag_02_03_ingestion_pipeline-chunksplitter.md).

### ChunkFormatError Classification Guidance

#### Hierarchy position

`ChunkFormatError` is defined in `scripts/rag/exceptions.py` as a subclass of both
`RagLayerError` (the rag-layer base class) and `ValueError`. Its sibling classes under
`RagLayerError` (`EmbeddingSchemaError`, `PipelineValidationError`, `SearchQueryError`,
`TokenizationError`, `UnknownMetadataError`) each cover a distinct condition described in
their docstrings. Raise each class only when its docstring condition applies — e.g., use
`SearchQueryError` for an unexecutable search query, not a malformed chunk document.

#### Catch-site pattern

Every current caller (the chunk splitter, file routing, ingester, and chunk grouping
modules under `scripts/rag/ingestion/`) catches `ChunkFormatError` specifically rather
than `RagLayerError` or `ValueError`. New code should follow the same pattern: catch
`ChunkFormatError` specifically, not its base classes.

#### Exception hierarchy

The RAG-layer error classes, including `RagRerankError` and `RagPipelineError`, are defined in `scripts/rag/exceptions.py` and derive from `RagLayerError`; some also derive from `ValueError` or `RuntimeError`, but `RagRerankError` and `RagExpansionError` derive from `RagLayerError` only. `MqeParseError` (a `ValueError`) is defined in `scripts/rag/llm_prompts.py`.

## RagIngester

| Error | Action |
|---|---|
| Embedding API failure | Retry with exponential backoff up to `embed_retry` |
| Retry limit reached (single chunk) | `WARNING`; skip chunk; continue |
| Invalid `lang` value | `ValueError`; skip URL group; `ERROR` (with traceback) |
| Invalid `fetched_at` (incoming or stored) | `ETagManager._is_stale_update()` raises `InvalidIncomingTimestampError` (invalid incoming `fetched_at`) or `InvalidStoredTimestampError` (invalid stored `fetched_at`) — both subclass `ValueError`; the message text (`Invalid incoming timestamp: {value}` vs `Invalid stored timestamp: {value}`) distinguishes the two at the call site. Uncaught at the call site (`RagIngester.ingest_url_group()`), it propagates to the same catch-all as "Invalid `lang` value" above: skip URL group; `ERROR` (with traceback). See [rag_02_06_ingestion_pipeline-supporting-components.md section 4.9.1](rag_02_06_ingestion_pipeline-supporting-components.md#491-freshness-comparison-edge-cases-and-error-handling). |
| `sqlite3.Error` during URL group processing (caught by `_process_url_groups()`) | Skip URL group; `ERROR` (with traceback); continue with remaining groups; `check_consistency` still runs after the batch |

## RagPipeline

| Error | Action |
|---|---|
| DB open error | Raises `RagPipelineError` (does not return `""`) |
| `use_search=False` | Immediately returns `""` |
| Failure when setting `rag_query_service_url` | Fallback to in-process pipeline |
| Cross-encoder failure | `RerankStage.run()` catches `RagRerankError` and falls back to the RRF-ranked results (sliced and deduplicated), recording the fallback reason `rerank_exception`. Other exceptions from the stage propagate to `RagPipeline`, which records `StageResult.status="failure"` for `RuntimeError`, `sqlite3.OperationalError`, `httpx` errors, and `TimeoutError`, logs a warning, and continues with `ctx.reranked=[]`. If `use_rerank=False`, RRF ordering and deduplication are used instead. |
| Startup config validation failure | `RagPipeline.__init__()` runs `RagConfigValidator().validate()`; a failing result raises `ValueError` and aborts construction. Warnings-only results are logged and allow continuation. |

---


## Keywords

- configuration
- exception-hierarchy
