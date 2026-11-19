# Crawl payloads are read into the chunk DTO and the crawl DTO is unused

## Priority
Medium

## Summary
`read_crawl_json` returns a `ChunkDocument` populated with placeholder chunk fields, while the dedicated
`CrawlDocument` in `scripts/rag/models_data.py` is referenced nowhere. The chunk metadata TypedDict is also
declared with all fields optional although the producer always sets every field.

## Background
- `pipeline_utils.read_crawl_json` builds a `ChunkDocument` with `chunking_strategy="text"`,
  `chunk_index=0`, `source_file=""`, `chunk_type=""` for a payload that has no chunk at all;
  `ChunkSplitter._extract_chunk_metadata` then overwrites those fields.
- `models_data.CrawlDocument` exists and is not imported by any file under `scripts/` or `tests/`.
- `ChunkSplitter.ChunkMetadata` is a `TypedDict` with `total=False`, documented as required for `**`
  spreading, yet `_extract_chunk_metadata` always returns all eight keys and `_build_chunk_payload` relies
  on the spread to produce the payload key set asserted by `TestChunkPayloadKeyContract`.
- Related closed issues: `issues/done/20260913-183029_missing_chunksplitter_typedict_usage_mismatch.md`
  and `issues/done/20260926-072314_rewrite_dto_models_config_to_document_RagConfigImpl.md`.

## Problem
Two different documents share one class, so the type no longer says which fields are real: four chunk
fields are always fake values on the crawl side. The unused `CrawlDocument` makes the intended boundary
invisible, and the optional metadata TypedDict hides a missing key instead of failing at construction.

## Reason for Change
`read_chunk_json` and `read_crawl_json` are the strict validators of the artifact contract; their return
types should describe the artifact they validated.

## Implementation Intent
Give each payload direction the DTO that matches its fields, and make the chunk metadata contract total
so a missing key fails where it is built rather than producing a payload with a missing key later.

## Target Files or Areas
- `scripts/rag/models_data.py`
- `scripts/rag/ingestion/pipeline_utils.py` (`read_crawl_json`)
- `scripts/rag/ingestion/chunk_splitter.py` (`ChunkMetadata`, `_extract_chunk_metadata`, `_build_chunk_payload`)
- `tests/rag/ingestion/test_pipeline_utils_strict.py`, `tests/rag/ingestion/test_chunk_splitter.py`

## Required Changes
- Read crawl payloads into `CrawlDocument` (extending it with the fields `ChunkSplitter` actually needs) and
  stop manufacturing chunk fields for crawl input.
- Make `ChunkMetadata` total (all keys required) or replace it with a frozen dataclass, keeping the payload
  key contract test green.
- Confirm no other consumer depends on `read_crawl_json` returning a `ChunkDocument`.

## Constraints
- The chunk JSON payload key set is a published artifact contract validated by `read_chunk_json` and by
  `TestChunkPayloadKeyContract`; it must not change.
- `ChunkFormatError` remains the validation failure type.
- `ChunkGroupingStrategy` and `ChunkGeneration` read chunk payloads only and must keep working.

## Acceptance Criteria
- `read_crawl_json` returns the crawl DTO and constructs no chunk-only fields.
- `CrawlDocument` is used or removed, with the reason recorded.
- `ChunkMetadata` no longer declares a key optional that the producer always sets.

## Testing Expectations
- Unit: crawl reader validation tests assert the returned DTO type and fields.
- Unit: metadata construction rejects a missing key.
- Regression: `test_pipeline_utils_strict.py`, `TestChunkPayloadKeyContract`, `test_chunk_grouping.py` stay green.

## Documentation Impact
- `docs/21_rag/rag_02_07_ingestion_pipeline-utils.md`: record which DTO each reader returns.
- `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md`: record the metadata contract.

## Out of Scope
- Changing the chunk JSON payload fields or their order.
- Crawler-side config work.

## Dependencies
- N/A: none

## Unresolved Questions
- Whether `CrawlDocument` was created for a crawler-side refactor that never landed — `Needs confirmation`
  from git history before it is deleted.

## AI Implementation Instruction
Do not delete `CrawlDocument` without checking its history. Do not weaken any validator to make a DTO
change easier.

## Traceability
- **Workflow phase**: `python-code-review` (finding `F-008`)
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261119-112020
- **Related target files**: `scripts/rag/models_data.py`, `scripts/rag/ingestion/pipeline_utils.py`, `scripts/rag/ingestion/chunk_splitter.py`, `tests/rag/ingestion/test_pipeline_utils_strict.py`
