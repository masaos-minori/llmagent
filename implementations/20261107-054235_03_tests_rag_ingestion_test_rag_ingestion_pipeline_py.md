## Goal

- Prove the producer→validator boundary end-to-end: real `ChunkSplitter` output is grouped and ingested
  without rejection, and a `code_blocks`-removed chunk file is still rejected and routed to failed/
  (REQ-003: end-to-end regression + negative control).

## Scope
**Release unit**: chunk-payload contract closure

- Two new tests in the existing pipeline test file. Both are Phase 1 tests (RED until the seq01 producer fix
  lands for the positive test; the negative control is green before and after, proving the validator is not
  weakened).

## Assumptions

- `RagIngester.ingest_all()` returns a `RagConsistencyReport | None`; acceptance is asserted via DB row
  counts and directory state, not per-run counters (Plan AC-002, corrected 2026-11-07: the names
  processed_docs, failed_docs and rag_web from the original wording do not exist in current code).
- Rejected files are moved to rag-src/failed/ (sibling of chunk/) with a sibling `.error.json`
  (`file_routing.py` `ArtifactFileRouter.route`, verified 2026-11-07).
- Existing mock scaffolding (`_make_rag_db`, `_make_fake_sqlite_helper`, patched `SQLiteHelper` /
  `check_rag_consistency` / `EmbeddingService.get_embedding`) is sufficient for a real-writer variant; only
  the chunk-file provenance changes from hand-written fixture to ChunkSplitter output.

## Design decisions

- Drive the full `RagIngester.ingest_all()` path (not `ChunkGroupingStrategy` alone): AC-002/AC-004 assert
  persistence and failed/ routing, which only the full path produces.
- Build the source file with the crawler-format fixture pattern already in this file (`_make_chunk_json`
  shape) written under rag-src/, then run `ChunkSplitter.process_file(..., force=True)` — the chunk output
  is real writer bytes, not a fixture.

## Alternatives considered

- Group-only assertion via `ChunkGroupingStrategy.group()`: rejected — would not cover failed/ routing or
  persistence (AC-002/AC-004).
- Switching the existing `_make_chunk_output_json` fixtures to real writer output globally: out of scope for
  this Plan (recorded in the Plan's Scope as the 003 Plan's optional follow-up).

## Implementation
### Target file
`tests/rag/ingestion/test_rag_ingestion_pipeline.py`

### Procedure
1. Add class `TestChunkSplitterOutputEndToEnd` (new) with two tests, per Plan Phase 1.
2. `test_real_chunk_splitter_output_is_ingested` (new):
   - Write a crawler-format source JSON under tmp_path/rag-src/ using the `_make_chunk_json` payload
     shape (content long enough to produce ≥1 chunk, e.g. repeated sentences, `min_chunk` 10 / `max_chunk`
     1000 like `test_chunk_splitter_processes_json`).
   - Run `ChunkSplitter(config=...).process_file(source, force=True)`; assert ≥1 chunk file appears in
     tmp_path/rag-src/chunk/ (naming pattern `{stem}-0000.json`).
   - Build `RagIngester` with the existing cfg pattern (`rag_src_dir`, `embed_url`, `embed_retry`,
     `embed_workers`) and the existing patch trio; run `ingest_all()`.
   - Assert: `SELECT COUNT(*) FROM documents` ≥ 1 with the source url, `chunks` ≥ 1, and
     tmp_path/rag-src/failed contains no `.json` entry for the chunk stem. Before the seq01 fix this
     test is RED (`PARSE_FAILED` rejection, file routed to failed/).
3. `test_chunk_file_without_code_blocks_routed_to_failed` (new) — the negative control:
   - Take `_make_chunk_output_json(...)`, `del payload["code_blocks"]`, write it into
     tmp_path/rag-src/chunk/.
   - Run the same patched `ingest_all()`; assert: no row in `documents`, the chunk file is no longer in
     chunk/, and tmp_path/rag-src/failed contains the file plus a `{stem}.error.json`.
   - This test must pass both before and after the seq01 fix (validator strictness unchanged).

### Method
- Pure test addition; no production code in this file's scope. Import `ChunkSplitter` (already imported in
  this file) and reuse existing module-level helpers; no helper signatures change.

### Details
- Keep tests deterministic: fixed `fetched_at` values, no network (embedding patched), no reliance on
  production paths or the sqlite-vec extension (fixture DB mocks vec0 tables already).
- Name assertions clearly so a failure message names `code_blocks`/`PARSE_FAILED` (matches Plan Phase 1
  expectation).

## Compatibility considerations

- Existing tests in this file keep their hand-written fixtures and must stay green unchanged; the new class is
  additive.

## Security considerations

- N/A: test-only change; no trust-boundary change.

## Rollback considerations

- N/A: revert the commit (test-only addition).

## Validation plan

- `uv run pytest tests/rag/ingestion/test_rag_ingestion_pipeline.py -v` — after seq01's fix: all green incl.
  the new class; before it: exactly the positive test RED with a `PARSE_FAILED`/`code_blocks` failure name,
  negative control green.
- `uv run pytest tests/rag/ingestion` then full `uv run pytest` — no regressions.
- Coverage gates (`rules/toolchain.md`) run once for the whole Plan (documented in the seq01 document).

## Completion criteria

- AC-002: real ChunkSplitter chunk output → ≥1 `documents`/`chunks` rows, nothing in failed/.
- AC-004: `code_blocks`-removed chunk file → rejected, moved to failed/ with `.error.json`, not persisted.
- All pre-existing tests in the file unchanged and green.

## Out of Scope

- The producer fix itself (`scripts/rag/ingestion/chunk_splitter.py`, seq01 document).
- Migrating existing hand-written fixtures (`_make_chunk_json`/`_make_chunk_output_json`) to real writer
  output.
- Any change to `pipeline_utils.py`, `ingester.py`, `chunk_grouping.py`, `file_routing.py` (Reference Files).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `TestChunkSplitterOutputEndToEnd` (new) with the positive e2e test (Plan Phase 1, REQ-003) | Pending | — | — | Release unit "chunk-payload contract closure": RED until seq01 step 2 lands |
| 2 | Add the `code_blocks`-removed negative control test (Plan Phase 1, REQ-003 / AC-004) | Pending | — | — | Must be green before and after the producer fix |
| 3 | Re-run this file + `tests/rag/ingestion` after the seq01 fix: all green | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-003 (end-to-end ingestion regression test with negative control)
- **Source issue**: issues/done/20261106-110845_ragfix001_chunk-payload-code-blocks.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261107-050704_ragfix001_chunk-payload-code-blocks.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261107-054235
- **Related target files**: tests/rag/ingestion/test_rag_ingestion_pipeline.py
