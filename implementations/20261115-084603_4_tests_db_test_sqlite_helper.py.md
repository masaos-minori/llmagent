## Goal
- Unit-cover the Helper `read_only` open mode.

## Scope
**Release unit**: N/A: not part of a release unit (plan Phase 1 tests, land with `20261115-084603_1`)

- In scope: `tests/db/test_sqlite_helper.py` — read-only open unit tests and the local fake's signature extension (REQ-001, REQ-006).

## Assumptions
- The local fake `_InMemoryHelper` (`:16`) mirrors `SQLiteHelper.open` kwargs at `:23-25` (`write_mode`, `row_factory`); fake-based tests break with `TypeError` unless it gains the `read_only` kwarg (plan Correction 3).
- Tests use the existing style: real `tmp_path` databases through `SQLiteHelper(db_path=...)` (e.g. `TestReuseConnection` at `:256-274`).

## Design decisions
- New class `TestReadOnlyOpen` (new) instead of adding cases to `TestSQLiteHelperVecDefault` — the vec tests are cited as the guard for vec defaults in ADR-008; keeping them untouched avoids churn in a doc-cited test id.

## Alternatives considered
- Asserting pragma skipping via mock_connect patching only: rejected — the Issue's AC-1 is about observable bytes/files (journal mode stays `delete`, no sidecars), so real-file assertions are the primary test; pragma query reads verify the mode directly.

## Implementation
### Target file
`tests/db/test_sqlite_helper.py`

### Procedure
1. Extend `_InMemoryHelper.open` (`:23-25`) with the `read_only` keyword (accepted, stored on the instance for assertion, connection unchanged) (plan Correction 3).
2. Add class `TestReadOnlyOpen` (new) with:
   - `test_read_only_open_skips_write_pragmas` (new): create a rollback-journal database (plain `sqlite3.connect`, one table, `journal_mode=delete`); `SQLiteHelper(...).open(read_only=True)`; `PRAGMA journal_mode` reports `delete` during and after the open; the directory listing shows no `-wal`/`-shm` files; `PRAGMA busy_timeout` reports the configured non-zero timeout (REQ-001/AC-1).
   - `test_read_only_open_missing_path_raises` (new): `open(read_only=True)` on a non-existent `tmp_path` file raises `sqlite3.OperationalError` and the file still does not exist afterwards (REQ-001/AC-2 mechanism).
   - `test_default_open_unchanged` (new): default `open()` on the same fixture still yields `journal_mode` = `wal` (REQ-001 default-invariance regression).
   - `test_read_only_open_loads_vec_when_requested` (new): with `sqlite_vec_so` pointing at the repo's `vec0.so` (skip with explicit reason if absent, mirroring Plan 001's test convention), `open(read_only=True, load_vec=True)` succeeds and `load_vec` behavior is unchanged (Plan Design assumption).

### Method
- Additive tests; no existing test edits beyond the fake signature extension.

### Details
- No new fixtures; reuse `tmp_path`.
- Overlap: Plan 005's teardown tests land in this file after 004 and are disjoint from `TestReadOnlyOpen` (new) (plan overlap record).

## Compatibility considerations
- Test-only file; no production code touched here (Helper change is companion `20261115-084603_1`).

## Security considerations
- N/A: test-only.

## Rollback considerations
- Revert with companion `20261115-084603_1` (tests assert its behavior); checkout revert.

## Validation plan
- `uv run pytest tests/db/test_sqlite_helper.py -v` → new cases green, existing cases green (AC-1).
- `uv run ruff check tests/db/test_sqlite_helper.py` → clean.

## Completion criteria
- The three behaviors (pragma skipping + no sidecars, missing-path raise, default unchanged) are asserted; the fake accepts `read_only`.

## Out of Scope
- Helper implementation (companion `20261115-084603_1`).
- Recovery-level invariance tests (companion `20261115-084603_5`).

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
- **Requirement ID**: REQ-001, REQ-006
- **Source issue**: issues/20261114-092852_dbreview004_integrity-probe-side-effects.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261115-041859_dbreview004_integrity-probe-side-effects.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261115-084603
- **Related target files**: tests/db/test_sqlite_helper.py
