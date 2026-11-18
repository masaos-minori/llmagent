## Goal
Write, before the fix, tests that run `RagMaintenanceService` against a real temporary database file, reopen it with a new connection, and map `recover()` results (REQ-001 to REQ-004, REQ-006).

## Scope
**Release unit**: rag-repair-persistence
- One new test file; no production file changes.
- Release unit: the failing-first tests stay red until the fix of procedure 05 lands, so the full suite and diff-cover run once at the end of the unit.

## Assumptions
- The repair contracts follow the Source plan defaults: `rebuild_vec` removes orphan `chunks_vec` rows and returns the rows left (UNK-01, UNK-02); `reconcile_url` inserts only the missing `chunks_fts` entries (UNK-05). The owner confirms them before procedure 05; a different decision changes these tests.
- The sqlite-vec package is not installed in the dev environment, so `chunks_vec` is a plain table stand-in, as in the existing tests; commit behavior does not depend on the table type.
- Production is untouched: the tests replace the `SQLiteHelper` name in `agent.services.rag_maintenance_service` with a factory that opens a file under `tmp_path`.
- Expected pre-fix result: the `rebuild_vec` tests fail with `OperationalError` (no such column), the `reconcile_url` tests fail with `TypeError`, and the `vacuum_failed` mapping case fails on `integrity_ok`; the other mapping cases pass and guard existing behavior. Record the failing output in the Execution Status Notes (REQ-006).

## Design decisions
- Real file plus a fresh `sqlite3.connect` for every assertion, so a discarded transaction is visible.
- A helper subclass whose `commit` raises proves the rollback on failure: the repair's writes must be absent for a new connection.

## Alternatives considered
The in-memory fake of `test_rag_index_integrity.py` was rejected for these tests: it shares one connection, so a missing commit is invisible.

## Implementation
### Target file
`tests/agent/services/test_rag_maintenance_persistence.py` (new)
### Procedure
1. Create the file with a module docstring that names the contracts under test.
2. Add fixture `rag_db_path` (new): creates `rag.sqlite` under `tmp_path` with the canonical table shapes (`documents`, `chunks` without an embedding column, a plain `chunks_vec`, the external-content `chunks_fts`, and the insert trigger that indexes new chunks).
3. Add fixture `use_file_db` (new): replaces the `SQLiteHelper` name in the service module with a factory returning `SQLiteHelper(db_path=<file>)`; add class `_FailingCommitHelper` (new), a `SQLiteHelper` subclass whose `commit` raises `RuntimeError`, selectable by the same fixture.
4. Add the `rebuild_vec` tests: orphan rows removed and persisted with the rows-left return; valid rows kept when there is no orphan; a failing commit leaves the orphan in place.
5. Add the `reconcile_url` tests: a missing FTS entry (created with an FTS5 delete of an indexed row) is inserted and visible to a new connection without an error; `chunks_vec` rows and indexed entries are unchanged; an unknown URL returns `{"found": False}`; a consistent index returns `{"found": True, "chunks": n}` without error; a failing commit leaves the gap.
6. Add the `recover` mapping test: patch `recover_corruption` in the service module to return each `RecoveryResult` of the table in Details and assert `integrity_ok` and `recovered`.
7. Run the file and record the failures; do not change production code in this procedure.
### Method
Seed one document per URL, chunk rows with ids 1 and 2 for the first URL and 3 for the second, vector rows for 1, 2, 3 and an orphan 99. Query with `sqlite3.connect` after each call. The FTS gap is made with `INSERT INTO chunks_fts(chunks_fts, rowid, content) VALUES('delete', <id>, <indexed text>)` for a row that is indexed, which is a valid use of the command.
### Details
- `recover` mapping table (success, action, expected integrity_ok, expected recovered): (True, vacuum, True, False); (False, vacuum_failed, True, False); (True, restored, True, True); (False, restore_verify_failed, False, False); (False, no_backup, False, False); (False, rollback_failed, False, False).
- Do not import fixtures or helpers from another test module.

## Compatibility considerations
N/A: test-only change.

## Security considerations
N/A: the tests write only under `tmp_path` and never reach a production path.

## Rollback considerations
N/A: delete the new file (a single file this procedure created).

## Validation plan
- `uv run pytest tests/agent/services/test_rag_maintenance_persistence.py` (expected red before procedure 05, green after)
- `uv run ruff format <changed files>`, `uv run ruff check <changed files>`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`
- `uv run python tools/check_mock_patch_targets.py`

## Completion criteria
- The tests exist, reopen the database with a new connection, and fail before the fix for the stated reasons.
- After procedure 05 they pass, and no production path is touched.

## Out of Scope
- Editing `scripts/` files.
- Changing the existing fake-helper tests (procedure 03).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Write the persistence and `integrity_ok` tests | Completed | 20261118-123012 | 20261118-123025 | New test file written; changed: tests/agent/services/test_rag_maintenance_persistence.py |
| 2 | Run the file and record the expected failures | Completed | 20261118-123025 | 20261118-123025 | Pre-fix run: 8 failed, 6 passed. rebuild_vec x3: sqlite3.OperationalError no such column: embedding; reconcile_url x4: TypeError tuple indices must be integers; recover vacuum_failed mapping x1: integrity_ok mismatch. The unknown-URL case and five mapping cases pass and guard existing behavior |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261118-123617 | 20261118-123617 | End-of-unit run passed: full suite 12734 passed, 7 skipped; diff-cover 100% (10 changed lines in rag_maintenance_service.py); ruff, project mypy (569 files), bandit -ll (0 medium/high), lint-imports (6 kept), validation gates: pass |
| 4 | Update documentation, if in scope | Completed | 20261118-123025 | 20261118-123025 | N/A: test-only change |

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
- **Requirement ID**: `REQ-001`, `REQ-002`, `REQ-003`, `REQ-004`, `REQ-006`: persistence, repair contracts, `integrity_ok`, failing-first tests
- **Source issue**: issues/20261117-123007_adrchk007_rag-repair-persistence.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261118-112342_adrchk007_rag-repair-persistence.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-121341
- **Related target files**: `tests/agent/services/test_rag_maintenance_persistence.py`
