## Goal
Make the two repair tests that patch `SQLiteHelper` honor the `row_factory` flag as the real helper does, and update them to the canonical repair contracts (REQ-006).

## Scope
**Release unit**: rag-repair-persistence
- The tests of `rebuild_vec` and `reconcile_url` in this file only; its other tests are unchanged.
- Release unit: the failing-first tests stay red until the fix of procedure 05 lands, so the full suite and diff-cover run once at the end of the unit.

## Assumptions
- The repair contracts are the Source plan defaults (UNK-01, UNK-02, UNK-05).
- The fake `_FakeSQLiteHelper.open` already sets `row_factory` from its flag; the two tests bypass it by setting the context manager result of a mock, which is why they pass while the real helper returns tuples.

## Design decisions
- Route the mocked `open` to the fake's own `open` so the flag decides the row type, as in production.

## Alternatives considered
Deleting the two tests was rejected: they cover the service through the shared fixtures.

## Implementation
### Target file
`tests/agent/services/test_rag_index_integrity.py`
### Procedure
1. In the existing `test_reconcile_url_fts_deletion` and `test_rebuild_vec_removes_orphaned_chunks_vec_rows`, replace the lines that set `open.return_value.__enter__.return_value` and `__exit__` with `mock_helper_cls.return_value.open.side_effect = db.open`.
2. `test_reconcile_url_fts_deletion`: keep the seeded synced index, the `{"found": True, "chunks": 1}` result, and the search assertion; reword the docstring to say `reconcile_url()` must not raise on a consistent index (the gap repair is covered by the new persistence tests).
3. `test_rebuild_vec_removes_orphaned_chunks_vec_rows`: seed the valid vector row for the chunk and the orphan row directly in `chunks_vec`; drop the `UPDATE chunks SET embedding` step and the first populate call; assert the orphan is removed, the valid row is kept, and the returned count equals the rows left.
### Method
Use the existing helpers `_insert_doc` and `_insert_chunk`; keep the `mock_patch` import style of the file. Do not change `_SCHEMA_SQL` or any other test.
### Details
- The stand-in `chunks` table keeps its `embedding` column because other tests insert through it; only these two tests stop using it.

## Compatibility considerations
N/A: test-only change; no public contract.

## Security considerations
N/A: in-memory database only.

## Rollback considerations
Revert only this procedure's own changes with `git checkout -- <path>` on each changed path (single-path revert; no bulk form).

## Validation plan
- `uv run pytest tests/agent/services/test_rag_index_integrity.py` (the `rebuild_vec` test passes only after procedure 05)
- `uv run ruff format <changed files>`, `uv run ruff check <changed files>`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`
- `uv run python tools/check_mock_patch_targets.py`

## Completion criteria
- The two tests use the fake's `open` and encode the canonical contracts.
- Every other test of the file still passes.

## Out of Scope
- Editing `scripts/` files.
- Changing `rebuild_fts` tests.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Route the mocked `open` to the fake and update the two tests | Completed | 20261118-123047 | 20261118-123111 | Both repair tests now route the mocked open to the fake (side_effect = db.open); rebuild_vec test rewritten to the orphan-removal contract; changed: tests/agent/services/test_rag_index_integrity.py Correction during procedure 05: the fake gained executemany (the helper API the new rebuild_vec uses); same file |
| 2 | Run the file and record which tests are red until procedure 05 | Completed | 20261118-123111 | 20261118-123111 | Red until procedure 05: reconcile test TypeError (tuple indices), rebuild_vec test assert 0 == 1 (the old code wipes the valid row); the other 7 tests pass |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261118-123617 | 20261118-123617 | End-of-unit run passed: full suite 12734 passed, 7 skipped; diff-cover 100% (10 changed lines in rag_maintenance_service.py); ruff, project mypy (569 files), bandit -ll (0 medium/high), lint-imports (6 kept), validation gates: pass |
| 4 | Update documentation, if in scope | Completed | 20261118-123111 | 20261118-123111 | N/A: test-only change |

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
- **Requirement ID**: `REQ-006`: tests that reopen real databases and a fake that honors `row_factory`
- **Source issue**: issues/20261117-123007_adrchk007_rag-repair-persistence.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261118-112342_adrchk007_rag-repair-persistence.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-121341
- **Related target files**: `tests/agent/services/test_rag_index_integrity.py`
