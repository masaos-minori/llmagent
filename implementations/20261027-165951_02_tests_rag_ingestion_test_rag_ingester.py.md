# Implementation Procedure: Add the two-group batch-continuation regression test and the sqlite3 hierarchy boundary test

## Goal
Pin the widened batch boundary with a regression test (first group fails with `sqlite3.OperationalError`, second group still ingests, `check_consistency` runs) and a boundary test guarding the error-hierarchy claim inside the suite (REQ-002, REQ-003, AC-2).

## Scope
- Two new test functions. All existing tests, including `TestAtomicity::test_database_failure_during_replacement` (verified at L245, class at L203), stay unmodified.

## Assumptions
- No existing test drives `_process_url_groups`/`ingest_all` with a sqlite3 error: the only DB-error test targets `ingest_url_group` propagation directly (verified L272-274 `pytest.raises`), so it is unaffected by the loop-level widening and must keep passing as-is (AC-3).
- The `_make_ingester` fixture pattern (verified at L61: temp dirs plus mocked config dict) plus the existing `mock_db`/`mock_http_client`/`mock_doc_mgr` fixtures are reused.
- Determinism via patching — no wall-clock or real lock contention (Plan Tests).

## Design decisions
- Fail the first group only by wrapping the instance's `ingest_url_group` with a first-call-raises side effect: `_process_url_groups` calls `self.ingest_url_group`, so the failure injection stays at the group boundary the test targets and the second group exercises the normal success path end to end.
- Keep the propagation test untouched rather than adapting it: it is the contract `ingest_url_group` must preserve (REQ-003).

## Alternatives considered
- Patch `TransactionManager._insert_chunks_batch` with a call-count side effect (pattern precedent verified at L269-274) — viable but couples the test to internal call order across both groups; the instance-level wrapper is simpler and equally deterministic. Either satisfies the Plan; the wrapper is preferred.

## Implementation
### Target file
`tests/rag/ingestion/test_rag_ingester.py`
### Procedure
1. Add `test_sqlite_error_first_group_continues` (new): build an ingester with `_make_ingester` and two chunk files belonging to two distinct URL groups in `chunk_dir` (fixture pattern verified at L61 and L132-166 usage). Patch the group builder or let the two files form two groups naturally.
2. Wrap `ingester.ingest_url_group` (new behavior in the test only) so the first call raises `sqlite3.OperationalError("database is locked")` and later calls delegate to the real method.
3. Run `ingest_all` and assert: two results returned; group 1 is `IngestUrlResult.unexpected_failure`; group 2 succeeded (`n_success == 1`); `no exception escapes`; `check_consistency` invoked (assert on the mocked doc manager).
4. Assert the `ERROR` log with traceback is emitted for the failed group (caplog/fixture already used in this suite).
5. Add `test_sqlite_error_hierarchy_boundary` (new): assert `issubclass(sqlite3.OperationalError, sqlite3.Error)` and `not issubclass(sqlite3.Error, (OSError, RuntimeError, ValueError))` — guards the Issue's hierarchy claim inside the suite (Plan Tests).
### Method
Two new test functions in the existing file style (class-organized or module-level, matching the neighboring test's placement); reuse existing fixtures `mock_db`/`mock_http_client`/`mock_doc_mgr` where needed.
### Details
- `sqlite3` is already imported in the test module (verified at L3); no import change needed.
- The new continuation test depends on procedure _01 landing first; it belongs to Plan Phase 3 after Phase 2.

## Compatibility considerations
- Existing tests keep passing unmodified (AC-3, AC-5); the propagation contract is not relaxed.

## Security considerations
- Test-only change; no production surface.

## Rollback considerations
- Single commit adding the import, the widened tuple, tests, and the doc row; rollback is `git revert`. No config, schema, or deployed-state change.

## Validation plan
- `uv run pytest tests/rag/ingestion/test_rag_ingester.py` — the two new tests pass against the widened catch (procedure _01) and the continuation test fails against pre-change code (red-before-green confirmation of the regression).
- `uv run pytest tests/rag/ingestion/` green.
- `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `uv run bandit -r scripts/ -c pyproject.toml -ll`, `PYTHONPATH=scripts uv run lint-imports` — clean; no blind-except findings (AC-1).
- `uv run pytest tests/` — full suite green (AC-5).

## Completion criteria
- Two new tests present and passing; all pre-existing tests unmodified and passing; new except branch covered by diff-cover.

## Out of Scope
- Broadening the catch to bare `Exception`/`BaseException` (Issue Constraint).
- Changing transaction boundaries or rollback behavior (`SQLiteHelper.begin_immediate` stays as-is).
- Changing `ingest_url_group`'s own exception semantics for direct callers.
- The `int(cfg[...])` coercion style in `crawler.py`, `chunk_splitter.py`, `db/config.py`, `db/maintenance.py`.
- httpx/transport error handling — verified contained inside `ChunkFactory.prepare` and converted to `failed_paths` (Issue Unresolved Question, answered: no change).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-002, REQ-003
- **Source issue**: issues/20261027-074526_rag004_ingester-sqlite3-error-aborts-batch.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/done/20261027-111107_rag004_ingester-sqlite3-error-aborts-batch.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261027-165951
- **Related target files**: tests/rag/ingestion/test_rag_ingester.py
