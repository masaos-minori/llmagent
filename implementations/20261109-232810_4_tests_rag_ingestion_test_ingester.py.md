## Goal

- Add and update `tests/rag/ingestion/test_ingester.py` coverage for the wrong-size embedding rejection, the `IntegrityError` quarantine, and transient-error retention, including the fixture alignment and the two existing tests whose asserted behavior changes (`REQ-001` / `REQ-003` / `REQ-004` tests; plan AC-5 correction).

## Scope
**Release unit**: N/A: not part of a release unit

- Test file only: `tests/rag/ingestion/test_ingester.py`. No production-code changes in this document (they are the seq-1 and seq-3 documents).

## Assumptions

- Implementation order per the Plan is tests first (Phase 1): the new tests are expected to fail on HEAD and pass after the seq-1/seq-3 changes.
- Overlap judgment: this file is also a target of `plans/20261108-170725_ragrev016_stale-recrawl-replaces-content.md` (a later stale-skip routing test); judged compatible — new test classes/methods in different areas, and this document's changes land first per the plan order.

## Design decisions

- Fixture alignment: derive the fake embedding length from the same constant production code validates against — module-level `_DIM = get_embedding_dims()` (import from `db.store_protocols`) replacing the fixed `_DIM = 384`, so `_FAKE_EMBEDDING` passes `validate_embedding_blob` once seq-1 lands and the whole existing suite stays green (plan AC-5 correction).
- Keep `TestIntegrityErrorPropagation`'s TransactionManager-level test (`test_insert_chunks_batch_propagates_integrity_error`, L1266) unmodified — propagation from `TransactionManager` is still the contract; only the ingester-level behavior changes.

## Alternatives considered

- Monkeypatching `db.store_protocols.QWEN3_EMBEDDING_DIMS` per test: rejected in favor of deriving `_DIM` once — fewer patch sites and the suite tracks the constant.

## Implementation
### Target file
- `tests/rag/ingestion/test_ingester.py`

### Procedure
- Align fake-embedding fixtures with `get_embedding_dims()`.
- Update the two tests whose asserted behavior changes (plan AC-5 correction).
- Add the three new regression tests from the Plan's Tests section.

### Method
- Fixtures: `_DIM = get_embedding_dims()`, `_FAKE_EMBEDDING = [0.1] * _DIM`; `_fake_embed_resp` unchanged otherwise.
- Update `test_dimension_mismatch_on_retry` (L433): the 8-dim first response now yields `IngestionFailureReason.VALIDATION_FAILED` from `factory._embed_and_store` (assert the reason, not `PreparedChunk` success); `rag.ingestion.embedding.time.sleep` patch no longer applies since no retry occurs.
- Update `test_integrity_error_routes_to_failed_via_ingest_url_group` (L1289): replace `pytest.raises(sqlite3.IntegrityError)` with assertions that every group file lands in `failed/` with a `.error.json` naming `STORAGE_FAILED`, `result.failure_reason == IngestionFailureReason.STORAGE_FAILED`, and `SELECT COUNT(*) FROM chunks` is 0 (rollback via `begin_immediate` unchanged).
- Add `test_wrong_size_embedding_routes_group_to_failed` (new) in `TestIngestUrlGroup`: stub `post` returning a `[0.1] * 8` vector; assert no `commit` call (patch `TransactionManager.commit` and assert not called — `len(failed_paths) == 0` gate fails first), every file routed to `failed/` with `VALIDATION_FAILED`, and nothing left in `chunk/` (AC-1).
- Add `test_transient_operational_error_keeps_group_retryable` (new) in `TestIntegrityErrorPropagation`: patch `TransactionManager._insert_chunks_batch` with `side_effect=sqlite3.OperationalError("database is locked")`; assert `ingest_url_group` still raises `sqlite3.OperationalError` (propagation to `_process_url_groups` unchanged) and no file moved from `chunk/` (AC-4).

### Details
- Reuse existing helpers unchanged: `_make_db`, `_make_ingester`, `_write_chunk`, `_fake_embed_resp`, `_FakeSQLiteHelper`.
- The `TestIntegrityErrorPropagation` class docstring ("propagation from `_insert_chunks_batch`") should be extended to note the new split: propagation from `TransactionManager`, quarantine in the ingester.
- A real-schema variant (with the `chunks.chunk_type` CHECK) is a feasible optional addition for the integrity test per the Plan's Tests section; the in-memory minimal schema stays the default.

## Compatibility considerations

- No production behavior is tested by this document alone; the new tests define the seq-1/seq-3 targets and fail on HEAD by design.

## Security considerations
N/A: test-only change.

## Rollback considerations
N/A: revert the single commit.

## Validation plan

- `uv run pytest tests/rag/ingestion/test_ingester.py -q` — new/updated tests fail on HEAD, pass after seq-1 and seq-3 land.
- `uv run pytest tests/rag/ingestion -q` regression (AC-5).
- Coverage: changed lines covered >= 90 percent (`diff-cover` gate in `rules/toolchain.md`).

## Completion criteria

- AC-1 (wrong-size group in `failed/`, no commit), AC-3 (IntegrityError quarantine asserted), and AC-4 (OperationalError keeps files retryable) are each asserted by a green test; the previously conflicting tests updated per the plan AC-5 correction.

## Out of Scope

- `read_chunk_json` `chunk_type` cases (companion of the seq-2 document), production-code changes, ragrev016's stale-skip test.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Apply fixture alignment and update the two conflicting tests | Pending | — | — | |
| 2 | Add the new regression tests per Implementation > Method | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` (wrong-size embedding test), `REQ-003` (integrity-error quarantine test), `REQ-004` (transient-error retention test)
- **Source issue**: issues/20261108-131234_ragrev015_poison-chunk-groups-retried.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261108-170534_ragrev015_poison-chunk-groups-retried.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261109-232810
- **Related target files**: `tests/rag/ingestion/test_ingester.py`
