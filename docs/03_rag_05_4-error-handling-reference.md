---
title: "4. Error Handling Reference"
area: rag
tags:
  - rag
  - configuration
related:
  - 03_rag_00_document-guide.md
  - 03_rag_05_1-configuration-reference.md
source:
  - 03_rag_05_1-configuration-reference.md
---

# 4. Error Handling Reference

## Crawler

| Error | Action |
|---|---|
| HTTP failure | Retry with exponential backoff up to `fetch_retry` (`min(2**i, 10)` seconds) |
| Exception at URL level | Output `WARNING` and continue |
| `lang` is not `ja` or `en` | Skip URL |

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
in [03_rag_02_08_ingestion_pipeline-shared.md](03_rag_02_08_ingestion_pipeline-shared.md)).

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

For the full per-field Required/Nullable/Conditional classification referenced above,
see the canonical table in
[03_rag_02_03_ingestion_pipeline-chunksplitter.md](03_rag_02_03_ingestion_pipeline-chunksplitter.md).

## RagIngester

| Error | Action |
|---|---|
| Embedding API failure | Retry with exponential backoff up to `embed_retry` |
| Retry limit reached (single chunk) | `WARNING`; skip chunk; continue |
| Invalid `lang` value | `ValueError`; skip URL group; `ERROR` (with traceback) |

## RagPipeline

| Error | Action |
|---|---|
| DB open error | Raises `RagPipelineError` (does not return `""`) |
| `use_search=False` | Immediately returns `""` |
| Failure when setting `rag_service_url` | Fallback to in-process pipeline |
| Cross-encoder failure | `RagRerankError` is caught as a `RuntimeError`, and `StageResult.status="failure"` is recorded, with a warning logged. The pipeline continues with `ctx.reranked=[]` (no fallback to RRF). If `use_rerank=False`, RRF ordering and deduplication are used instead. |

## Implementation Notes

- `RagRerankError` is defined as `class RagRerankError(RuntimeError)` in `scripts/rag/llm_prompts.py` rather than `scripts/rag/exceptions.py`. Since it is a subclass of `RuntimeError`, it is included in the exception handling tuple in `pipeline.py` (`RuntimeError`, `sqlite3.OperationalError`, `httpx.HTTPStatusError`, `httpx.RequestError`, `TimeoutError`), so the description "caught as `RuntimeError`" is accurate.
  [Explicit in code]
- The actual exception classes defined in `scripts/rag/exceptions.py` are 7 types: `RagLayerError` (base) / `EmbeddingSchemaError` / `PipelineValidationError` / `SearchQueryError` / `ChunkFormatError` / `TokenizationError` / `UnknownMetadataError`. `RagRerankError` and `RagPipelineError` are not included here (both are individually defined in `llm_prompts.py` and `pipeline.py` respectively). The exception hierarchy is not unified under a single base class across the entire rag layer.
  [Explicit in code]
- `RagPipeline.__init__()` executes `RagConfigValidator().validate()` (`shared/config_validator.py`) at startup. If `result.ok` is `False`, it raises a `ValueError` and aborts instance creation. Warnings (`result.warnings`) are only logged, allowing continuation.
  [Explicit in code] — This note is added because this section lacked information about this initialization-time validation.

---


## Related Documents

- [03_rag_05_1-configuration-reference.md](03_rag_05_1-configuration-reference.md)
- [03_rag_04_04_dto-models_config.md](03_rag_04_04_dto-models_config.md)

## Keywords

configuration
exception-hierarchy
