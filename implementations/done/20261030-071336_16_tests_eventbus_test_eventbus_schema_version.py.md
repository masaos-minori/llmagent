# Implementation Procedure: `tests/eventbus/test_eventbus_schema_version.py` (startup contract extension)

## Goal
Extend the startup schema-version contract tests so registered migration paths succeed at startup while unknown/downgrade still refuse, and update the hard-coded stamp contract from 3 to 4 (Plan row 16; REQ-003, REQ-005, REQ-009).

## Scope
- In scope: modification of the existing module `tests/eventbus/test_eventbus_schema_version.py`.
- Out of scope: registry/CLI behavior (row 15), schema.sql content (row 04).

## Assumptions
- Current module pins `PRAGMA user_version = 3` as a contract lock (`tests/eventbus/test_eventbus_schema_version.py:74-81` area: "schema.sql must stamp PRAGMA user_version = 3") and refuses foreign versions (`user_version = 99` case ~:47, `user_version = 0` stamp case ~:57). Anchors re-verified against the current tree 2026-10-30.
- The lock flips to 4 only in the same release train as rows 04/02 (stamp and registry baseline land together); a test-only flip before row 04 lands must not be shipped.

## Design decisions
- Keep every existing refusal test intact (fail-closed startup, REQ-005/AC-3); add, don't replace.
- Registered-path success test drives startup through the row-03 lookup path with a pre-seeded backup fixture so the gate is satisfiable in-process.

## Alternatives considered
- New separate module for migrated-startup cases — rejected: the contract lock and refusal suite belong in one file the Plan row explicitly says "Extend".

## Implementation
### Target file
- `tests/eventbus/test_eventbus_schema_version.py` (modify)

### Procedure
1. Update the stamp contract lock from `= 3` to `= 4` and its docstring/comment to reference row 04's stamp change.
2. Add: fixture DB at `user_version=3` with required tables + valid ledger backup → `_init_schema` migrates via the registered 3→4 path (row 03 wiring), then startup succeeds and version reads 4.
3. Add: `user_version=5` (future/unknown) refused with "recreate" guidance preserved; downgrade-shaped fixtures (ledger ahead of schema.sql expected version) refused.
4. Keep the `user_version=0` fresh-DB stamping test; assert it stamps 4 after row 04 lands.

### Method
Existing module style (raw `sqlite3` connections on tmp files, no service involvement).

### Details
- The stamp-lock flip (3 to 4) ships in the same changeset as rows 02/04; never a test-only early flip.

## Compatibility considerations
- Until rows 02–04 land, the updated stamp lock fails by design (test-first contract). No other module depends on the literal 3 after row 04 (`tests/eventbus/test_eventbus_db_migration.py` covers pragmas only — re-verify no other literal `user_version = 3` asserts outside row 19's fingerprint tests, which row 15/19 handle).

## Security considerations
- No production DB access.

## Rollback considerations
- `git checkout` the single file.

## Validation plan
- Automated: `uv run pytest tests/eventbus/test_eventbus_schema_version.py`; included in `uv run pytest tests/eventbus` from the Plan's test matrix.
- Manual: none.

## Completion criteria
- Registered path migrates at startup (AC-1/AC-3 pair); unknown/downgrade refusals unchanged; stamp contract reads 4 and matches `schema.sql`.

## Out of Scope
- CLI behaviors (row 15). Fingerprint internals (row 18/19 test cross-refs).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | Tests implemented in dbmig001 feature commit 319691d15; verified against current tree 2026-10-30. Stamp contract lock flipped 3->4, registered 3->4 path migrates at startup, unknown(5)/downgrade refusals preserved, fresh-DB stamps 4. |
| 2 | Add or update tests per Validation plan | Completed | — | — | Module tests/eventbus/test_eventbus_schema_version.py: 10 tests pass. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | ruff format OK; ruff check OK; mypy clean; pytest 10 passed. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | — | Out of scope: registry/CLI behavior (row 15), schema.sql (row 04). |

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
- **Requirement ID**: `REQ-003`, `REQ-005`, `REQ-009`
- **Source issue**: `issues/20261029-104500_dbmig001_forward-only-db-migrations.md`
- **Source requirement**: N/A: no standalone requirement document exists
- **Source plan**: `plans/20261029-214108_dbmig001_forward-only-db-migrations.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Related target files**: `tests/eventbus/test_eventbus_schema_version.py`
- **Generated at**: 20261030-071336