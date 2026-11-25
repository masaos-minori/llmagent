# Make crawl and chunk artifacts versioned, generation-consistent, and atomically replaceable

## Priority
High

## Summary
Give crawl and chunk artifacts one validated envelope with a generation id, group all chunks of a document generation together regardless of type, and activate a new generation atomically so a failed forced rebuild keeps the previous one.

## Background
Verified against master on 2026-11-25 (source: `memo-issue.md` H-06):
- Confirmed: chunk files carry `schema_version`, `artifact_type`, and `created_by` (`scripts/rag/ingestion/chunk_splitter.py:596-597`), but the reader only allows them as extra keys without validating values (`scripts/rag/ingestion/pipeline_utils.py:180`), and no `generation_id` exists anywhere under `scripts/rag/ingestion`. The crawl persister writes no envelope.
- Confirmed: `chunk_type` is part of the generation key `ChunkGeneration` (`scripts/rag/ingestion/chunk_grouping.py:44,58`), so text and code chunks of one document can fall into different groups.
- Confirmed: a forced rebuild prunes the previous chunk files before writing the new ones (`chunk_splitter.py:293-295` calls `_prune_stale_chunk_files` before `_write_chunk_files`), and a prune failure per file is only logged.
- Not verified: whether chunk indices are one sequence across types (the note says so; `chunk_splitter.py:532` enumerates a single list, which supports it), and the error-sidecar `chunk_index` type.

## Problem
Valid code chunks can be rejected by grouping, incompatible artifact versions are accepted, generations of one URL can mix, and the last good generation is destroyed before the replacement is complete.

## Reason for Change
Ingestion correctness and recoverability depend on consumers seeing either the previous or the new complete generation.

## Implementation Intent
Define a common envelope (`schema_version`, `artifact_type`, `created_by`, `generation_id`) validated on read, drop `chunk_type` from the grouping key while keeping it per chunk, write each generation to a generation-specific location with a manifest (generation id, expected count, file names, hashes), validate, then switch an active pointer atomically and delete the old generation afterwards.

## Target Files or Areas
- `scripts/rag/ingestion/crawl_persister.py`, `chunk_splitter.py`, `chunk_grouping.py`, `pipeline_utils.py`, `ingester.py`, `file_routing.py`
- `tests/rag/ingestion/`

## Required Changes
- Envelope definition and strict validation (presence, type, allowed values); reject unknown future versions; add a migration reader only if legacy artifacts must stay readable.
- Remove `chunk_type` from the grouping key; validate chunk-index continuity across text and code together.
- Manifest, temporary generation location, pre-activation validation, atomic activation, post-activation cleanup.
- Keep error-sidecar `chunk_index` values as integers.

## Constraints
- Existing artifacts on disk must remain processable or fail with a clear message; no silent re-chunking.
- Atomicity must rely on filesystem rename semantics within one directory.

## Acceptance Criteria
- A document with text and several code blocks stores every chunk with contiguous indices; generations of one URL never mix.
- A chunk reader rejects a crawl artifact and an unsupported schema version.
- A failed forced rebuild leaves the previous generation usable; missing, corrupted, or hash-mismatched files invalidate the new generation before activation; consumers never see a partial generation.

## Testing Expectations
Unit and failure-injection tests for each acceptance item; ingestion regression tests; whole-suite run and changed-path gates.

## Documentation Impact
Document the artifact envelope and generation lifecycle in the ingestion pipeline documents.

## Out of Scope
- Ingestion exit codes and routing recovery (issues/20261125-093152_ragrem007_rag-ingest-exit-routing.md); embedding validation (issues/20261125-093154_ragrem009_rag-embedding-validation.md).

## Dependencies
- Blocks issues/20261125-093152_ragrem007_rag-ingest-exit-routing.md and issues/20261125-093154_ragrem009_rag-embedding-validation.md.

## Unresolved Questions
- `不明`: whether legacy artifacts exist in production that need a migration reader.
- `不明`: the on-disk layout preferred for the active-generation pointer.

## AI Implementation Instruction
Do not delete existing generations before activation succeeds; keep the change within the listed modules.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261125-093151
- **Related target files**: `scripts/rag/ingestion/chunk_splitter.py`, `scripts/rag/ingestion/chunk_grouping.py`, `scripts/rag/ingestion/pipeline_utils.py`, `scripts/rag/ingestion/crawl_persister.py`
