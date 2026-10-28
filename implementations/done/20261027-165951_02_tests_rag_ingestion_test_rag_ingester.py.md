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
1. Add `test_sqlite_error_first_group_continues` (new): build an ingester with `_make_ingester`. Inject a side-effect wrapper onto the instance attribute `ingester.ingest_url_group` (an instance attribute shadows the class method, and `_process_url_groups` calls `self.ingest_url_group(...)` unbound, so no implicit `self` is passed): the first call raises `sqlite3.OperationalError("database is locked")`, subsequent calls return a success `IngestUrlResult(url=url, n_success=1, ...)`. Call `_process_url_groups` directly with a two-entry URL-group dict `{"http://a.com": [], "http://b.com": []}` (dict order is insertion order, so `results[0]`/`results[1]` are deterministic).
2. Assert: exactly two results returned; `results[0]` (group A) is `unexpected_failure` (`failure_reason == IngestionFailureReason.UNEXPECTED_FAILURE`, `n_success == 0`); `results[1]` (group B) succeeded (`n_success == 1`); no exception escapes.
3. Capture the `ERROR` log with traceback emitted for the failed group via a temporary `_ListHandler` attached to the module logger. The module `logger` sets `propagate=False`, so pytest's `caplog` cannot capture these records — a temporary handler is required (see Deviations).
4. Add `test_sqlite_error_hierarchy_boundary` (new, module-level): assert `issubclass(sqlite3.OperationalError, sqlite3.Error)` and `not issubclass(sqlite3.Error, (OSError, RuntimeError, ValueError))` — guards the Issue's hierarchy claim inside the suite (Plan Tests).
### Method
Two new tests in the existing file style: `test_sqlite_error_first_group_continues` inside a new `TestBatchContinuation` class; `test_sqlite_error_hierarchy_boundary` at module level. Reuse existing fixtures `mock_db`/`mock_doc_mgr` where needed.
### Details
- Added imports: `import logging` (for `_ListHandler`/`logging.ERROR`), `from rag.exceptions import IngestionFailureReason` (assert on `failure_reason`), `from rag.ingestion import ingester as ingester_module` (reach the module logger, whose underlying stdlib logger the handler attaches to via `Logger.__getattr__` delegation). `sqlite3` was already imported.
- `_ListHandler` (module-level helper) captures `LogRecord`s without relying on propagation.
- The new continuation test depends on procedure _01 landing first; it belongs to Plan Phase 3 after Phase 2.

### Deviations from procedure intent
- **Direct `_process_url_groups` instead of `ingest_all`.** The original procedure step 3 instructed running `ingest_all` and asserting `check_consistency` was invoked. `ingest_all` opens a real `SQLiteHelper` connection (L159-164), which is impractical to mock cleanly and diverges from this suite's established pattern of mocking at the `ingest_url_group` boundary. We therefore drive `_process_url_groups` directly with an injected `ingest_url_group` side effect. Consequently `check_consistency` is **not** asserted — it lives in `ingest_all`, outside the method under test; the batch-continuation contract being pinned is precisely `_process_url_groups` catching the error and continuing.
- **Log capture via temporary handler, not `caplog`.** The module `logger` (`rag.ingestion.ingester`) sets `propagate=False`, so `caplog` (root-level) never sees its records. A temporary handler attached to the underlying stdlib logger is used instead.

## Compatibility considerations
- Existing tests keep passing unmodified (AC-3, AC-5); the propagation contract is not relaxed.

## Security considerations
- Test-only change; no production surface.

## Rollback considerations
- Single commit adding the import, the widened tuple, tests, and the doc row; rollback is `git revert`. No config, schema, or deployed-state change.

## Validation plan
- `uv run ruff format tests/rag/ingestion/test_rag_ingester.py` + `uv run ruff check tests/rag/ingestion/test_rag_ingester.py` — clean.
- `uv run mypy --no-namespace-packages tests/rag/ingestion/test_rag_ingester.py` — clean.
- `uv run pytest tests/rag/ingestion/test_rag_ingester.py` — the two new tests pass against the widened catch (procedure _01); the continuation test fails against pre-change code (red-before-green confirmed).
- `uv run pytest tests/rag/ingestion/` green.

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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261028-071800 | 20261028-072000 | Direct `_process_url_groups` test; see Deviations |
| 2 | Add or update tests per Validation plan | Completed | 20261028-071800 | 20261028-072000 | Two new tests; red-before-green confirmed |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261028-072000 | 20261028-072129 | ruff+mypy clean on test file; 179 package tests green |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261028-072129 | 20261028-072129 | Procedure body corrected to match implementation; deviations documented |

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
