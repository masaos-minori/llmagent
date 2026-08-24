## Goal
Determine whether `tests/rag/ingestion/test_rag_ingester_callback.py`'s single test needs any
edit to accommodate this plan's `fetched_at`-mandatory changes, and document the (negative)
finding so a future reader does not re-investigate the same question.

## Scope
- In scope: `tests/rag/ingestion/test_rag_ingester_callback.py` only (94 lines, 1 test
  function: `test_ingest_all_calls_on_ingest_complete`).
- Out of scope: `ingester.py`'s own migration (own implementation document) — this document
  only verifies whether that migration has any observable effect on this file's test.

## Assumptions
- Confirmed by reading the file: there is no literal chunk/crawl JSON dict and no
  `ChunkDocument(...)` construction anywhere in this file. The only "fixture" standing in for a
  chunk file is a bare `MagicMock()` (`mock_chunk_dir.glob.return_value = [MagicMock()]`), with
  `_process_url_groups` patched to return `[]` directly on `type(ingester)`.
- Confirmed by reading `ingester.py`: `ingest_all()` calls `self._group_chunks_by_url(chunk_files)`
  before `_process_url_groups` — the one method this test mocks. `_group_chunks_by_url()` calls
  `self._read_chunk_json(path)` for each glob result (including the `MagicMock()` stand-in),
  which delegates to `pipeline_utils._read_chunk_json_raw()`. That function's `orjson.loads()`
  call on a `MagicMock()`'s default `read_bytes()` return value raises `orjson.JSONDecodeError`,
  which `_read_chunk_json_raw()` catches internally and returns `None` for; `_group_chunks_by_url()`
  silently skips a `None` result. This behavior is unrelated to `fetched_at` and is not touched
  by this plan.
- This plan's scope (per its Design and Implementation steps sections) only widens
  `ChunkJsonRaw.fetched_at` to required and changes `pipeline_utils.read_json_file()` to read
  and raise on a missing/invalid `fetched_at`. It does not change `_read_chunk_json_raw()`'s own
  validation logic (which still checks only `url`/`content` and is the function this file's test
  path actually exercises). `read_json_file()` itself is not on this test's call path at all —
  confirmed by tracing `ingest_all()` -> `_group_chunks_by_url()` -> `_read_chunk_json()` ->
  `_read_chunk_json_raw()`, none of which call `read_json_file()`.
- Because `_process_url_groups` is patched directly on `type(ingester)` before
  `ingest_all(force=False, on_ingest_complete=callback)` runs, `ingest_url_group()`'s body
  (where this plan's `first_data["fetched_at"]` mandatory-key change lands, per `ingester.py`'s
  own implementation document) is never invoked for this test. The `fetched_at` field never
  enters this test's execution path in any form.
- Conclusion: this file contains no fixture that constructs chunk JSON or a `ChunkDocument`
  without `fetched_at` — the pattern this plan's Phase 5 asks to update. The plan's Affected
  areas table lists this file with "0 existing fetched_at references," consistent with this
  finding.

## Design decisions
- No fixture change is made in this file under this plan — the file has no chunk-JSON/
  `ChunkDocument` fixture pattern that omits `fetched_at`, only an opaque `MagicMock()` that
  never reaches `fetched_at`-dependent code.
- This finding is distinct from the *other*, unrelated question already on record for this file
  (see `implementations/20260821-124913_test_rag_ingester_callback.py.md`, sourced from the
  sibling plan `plans/20260820-094150_plan.md`): whether `read_json_file()`'s `ChunkFormatError`
  propagation changes this test's pass/fail outcome. That question concerns a *different* plan's
  *different* change (`read_json_file()`'s error-handling contract) and does not overlap with
  this plan's `fetched_at`-mandatory scope, since this test's path never calls `read_json_file()`
  either before or after either plan lands.

## Alternatives considered
- Preemptively rewriting the `MagicMock()` fixture to produce a fully valid chunk JSON payload
  (including `fetched_at`) regardless of the analysis above — rejected: there is no code path in
  this test that reads `fetched_at`, so such a change would be speculative churn with no
  regression it guards against, and would obscure the fact that this file is genuinely
  unaffected by this plan.
- Adding a new test to this file specifically covering `fetched_at` propagation through
  `ingest_all()` — rejected: out of scope for a migration-safety document; the plan's Phase 5
  already assigns `fetched_at`-propagation coverage to `test_ingester.py` and
  `test_rag_ingester.py` (see the plan's Validation plan table row for `ingester.py`).

## Implementation
### Target file
`tests/rag/ingestion/test_rag_ingester_callback.py`

### Procedure
1. No source edit is required in this file for this plan.
2. After all of this plan's Phase 1-4 source changes land, run this file's test unedited (see
   Validation plan) to confirm the analysis above holds in practice, not just by static tracing.
3. If the test unexpectedly fails post-migration, treat that as a signal that some other,
   undocumented call path now reaches `fetched_at`-dependent code from this test — re-open this
   document's Assumptions section rather than patching the symptom blindly.

### Method
- Verification-only: no code change, confirmed by tracing the exact call sequence
  `ingest_all()` -> `_group_chunks_by_url()` -> `_read_chunk_json()` -> `_read_chunk_json_raw()`
  against this plan's Design section.

### Details
- This document intentionally records a "no change needed" outcome rather than silently
  omitting the file, so a future reader (or a re-run of this same planning workflow) does not
  re-derive the same trace from scratch.

## Compatibility considerations
- N/A: no edit is made to this file under this plan; production behavior is unaffected by
  definition.

## Security considerations
N/A: test-only file, no external input surface.

## Rollback considerations
- N/A: no change is made, so there is nothing to roll back.

## Validation plan
- `uv run pytest tests/rag/ingestion/test_rag_ingester_callback.py -v` — run once after all of
  this plan's Phase 1-4 source changes land, to confirm the single test
  (`test_ingest_all_calls_on_ingest_complete`) still passes unedited, corroborating this
  document's "no fixture change needed" conclusion.
- If it fails, capture the traceback and compare it against this document's Assumptions section
  before making any edit, to identify which assumption about the call path was wrong.

## Out of scope
- `ingester.py`'s own `fetched_at`-mandatory signature changes — own implementation document.
- The unrelated `ChunkFormatError`-propagation question already tracked in
  `implementations/20260821-124913_test_rag_ingester_callback.py.md` under
  `plans/20260820-094150_plan.md` — a different plan's different change, not re-litigated here.

## Execution Status

##### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| — | — | Pending | — | — | |

##### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

##### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A: not applicable in this phase
- Source requirement: N/A: not applicable in this phase
- Source plan: plans/20260820-095054_plan.md
- Source implementation procedure: N/A: not applicable in this phase
- Generated at: 20260823-200056
- Related target files: tests/rag/ingestion/test_rag_ingester_callback.py
