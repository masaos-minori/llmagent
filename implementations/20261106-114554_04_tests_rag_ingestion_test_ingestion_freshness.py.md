## Goal

Add the failed-re-ingestion, transaction-abort, fresh/stale insert-semantics, and `resolve_incoming` unit tests to the freshness suite, RED against current code, so the commit-boundary fix is pinned by regression coverage (REQ-004).

## Scope
**Release unit**: etag-atomic-fix

## Assumptions

- `resolve_incoming` is created by sibling procedure 02 (`implementations/20261106-114554_02_scripts_rag_ingestion_etag_manager.py.md`); the unit tests for it (e) are written against that contract and fail until 02 lands.
- The real in-memory SQLite pattern `_FakeSQLiteHelper(conn)` (test_ingester.py:116) is reusable here; `TestGetOrCreateDocumentFreshness` (test_ingestion_freshness.py:149-254) already mixes real-`DocumentManager` and mock-based cases.

## Design decisions

- Integration coverage on a real in-memory SQLite `documents`/`chunks` schema instead of mocks — mock-based ingestion tests stub `handle_existing_document` and cannot detect this behavior change (Plan Risks).

## Alternatives considered

- Extending `test_ingester_etag_guard.py` for the new behavior: rejected — that file stays unchanged as characterization coverage of `ETagManager.update`.

## Implementation
### Target file
`tests/rag/ingestion/test_ingestion_freshness.py`
### Procedure

- (a) Failed re-ingestion test: existing HTTP document with a stored etag, payload with a changed etag, embedding forced to fail → stored `etag`/`last_modified`/`fetched_at` unchanged; a second run with the same payload reaches the replace/commit path again (not freshness-skipped).
- (b) Transaction-abort test: raise inside the commit's chunk-insert loop → `documents` and `chunks` rows equal pre-run values.
- (c)/(d) Insert-semantics tests: fresh payload → row carries payload freshness; stale payload (older `fetched_at`) → row carries stored freshness.
- (e) `resolve_incoming` unit tests mirroring `test_ingester_etag_guard.py` guard cases: stale skip, both-`None` keep-stored, invalid timestamps raise (`InvalidIncomingTimestampError` / `InvalidStoredTimestampError`), empty `new_fetched_at` raises `ValueError`, no-stored-row keeps incoming.

### Method

- Phase order (Plan Phase 1): (a)-(d) must fail against current code before the fix and pass after; (e) fails until `resolve_incoming` exists.

### Details

- Use the `_FakeSQLiteHelper(conn)` harness pattern from `tests/rag/ingestion/test_ingester.py` with the real schema so transaction rollback is genuinely exercised.

## Compatibility considerations

- `tests/rag/ingestion/test_ingester_etag_guard.py` must stay unchanged and green; `test_rag_ingester.py` / `test_ingester.py` mock tests must stay green (Plan Reference Files).

## Security considerations

N/A: test-only change.

## Rollback considerations

N/A: revert the single commit (revert together with sibling procedures 01-03).

## Validation plan

| Check | Command | Expected |
|---|---|---|
| RED phase | `uv run pytest tests/rag/ingestion/test_ingestion_freshness.py -v` before the fix | New (a)-(e) tests fail against current code |
| GREEN phase | `uv run pytest tests/rag/ingestion/test_ingestion_freshness.py -v` after siblings 01-03 | All pass |
| Suite | `uv run pytest tests/rag/ingestion` | All green |

## Completion criteria

- AC-1: failed re-ingestion leaves stored freshness unchanged and a subsequent run re-processes the URL (test (a)).
- AC-2: success path writes freshness in the same transaction as chunks (tests (c)/(d)).
- AC-3: abort leaves `documents` and `chunks` at pre-run values (test (b)).
- AC-4: `resolve_incoming` guard rules verified (test (e)).

## Out of Scope

- Changes to `test_ingester_etag_guard.py` (must stay unchanged) and the mock-based ingestion tests.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the (a)-(e) tests per Procedure (RED first, Plan Phase 1) | Pending | — | — | Must fail before sibling procedures 01-03 land |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Includes diff-cover ≥ 90% |

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
- **Requirement ID**: `REQ-004` (regression and atomicity tests for the commit-boundary fix)
- **Source issue**: `issues/20261106-073538_raging002_etag-updated-before-reingestion.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261106-094942_raging002_etag-updated-before-reingestion.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261106-114554
- **Related target files**: `tests/rag/ingestion/test_ingestion_freshness.py`
