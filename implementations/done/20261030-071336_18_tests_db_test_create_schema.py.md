# Implementation Procedure: `tests/db/test_create_schema.py` (create-path ledger coverage)

## Goal
Extend the create-path test module so new databases are asserted ledger-compatible, and fingerprint/equivalence expectations cover the migrated (post-row-04) schema shape (Plan row 18; REQ-001, REQ-006).

## Scope
- In scope: modification of the existing module `tests/db/test_create_schema.py`.
- Out of scope: migration runner tests (rows 14, 17), schema.sql contents (row 04), ledger DDL in Python DDL (row 09).

## Current shape (facts)
- `tests/db/test_create_schema.py` exists and covers schema creation/version-refusal behavior of `scripts/db/create_schema.py` (`create_workflow_schema` :97-103, `create_eventbus_schema` :106-132, `_record_workflow_schema_version` :53-78 — re-verified 2026-10-30).
- `tests/db/test_eventbus_schema_equivalence.py` exists and is the fingerprint-shape guard named by Plan row 4's Related Tests.

## Assumptions
- After rows 04/09 land, new `workflow.sqlite` and `eventbus.sqlite` carry `schema_migrations`; `rag.sqlite`/`session.sqlite` intentionally do not (recreate-only domains, Plan Out-of-Scope).
- The eventbus fingerprint (`scripts/shared/eventbus_schema_fingerprint.py`) canonical shape must include the ledger table after row 04; the equivalence test is the place that catches drift.

## Design decisions
- Assert ledger presence AND baseline row content (id + from/to versions) rather than mere table existence — matches AC-1 wording "ledger created at bootstrap".
- For rag/session, assert the ledger table is absent, locking the recreate-only contract against accidental scope creep.

## Alternatives considered
- A new test module for create-path ledger checks — rejected: the Plan row says "Extend" the existing file; keeping creation assertions together with existing refusal tests preserves one regression surface.

## Implementation
### Target file
- `tests/db/test_create_schema.py` (modify)

### Procedure
1. Add tests: `create_workflow_schema()` on a fresh tmp DB → `schema_migrations` exists with the baseline row written by the row-08 bootstrap, and `workflow_schema_version` marker row unchanged alongside it.
2. Add tests: `create_eventbus_schema()` on a fresh tmp DB → `schema_migrations` exists with baseline row and `PRAGMA user_version` equals the stamped version (4 after row 04).
3. Add refusal-regression: creating over a DB with a mismatched version string still raises (existing behavior preserved, REQ-003 pair).
4. rag/session fresh creation: assert no `schema_migrations` table.
5. Coordinate with `tests/db/test_eventbus_schema_equivalence.py`: its canonical shape expectation is updated in the same landing as row 04 (ledger table added); state the cross-file dependency in the test docstring.

### Method
Extend the module's existing tmp-DB fixture helpers; no new fixtures needed.

### Details
- Version-literal assertions (3 vs 4) must read from `schema.sql` parsing helpers (`_expected_schema_version`) rather than hard-coded numbers where the module already does so, to avoid a second stale-lock surface like row 16's.

## Compatibility considerations
- Tests fail before rows 04/08/09 land (test-first contract, intended).
- No production DB access; existing green tests in this module must stay green.

## Security considerations
- None beyond existing fixture hygiene.

## Rollback considerations
- `git checkout` the single file (and revert the equivalence-test shape change together with row 04).

## Validation plan
- Automated: `uv run pytest tests/db/test_create_schema.py tests/db/test_eventbus_schema_equivalence.py`; full `uv run pytest tests/db` green after code rows land.
- Manual: none.

## Completion criteria
- Ledger + baseline-row assertions pass for workflow/eventbus creation; rag/session absence asserted; refusal tests unchanged.

## Out of Scope
- Migration execution tests (rows 14–17). Deploy init gates (row 13).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | Extended tests/db/test_create_schema.py with TestCreatePathLedgerCoverage: workflow fresh creation carries schema_migrations baseline ('workflow_ledger_baseline',0,1)+user_version=1+version marker; eventbus fresh creation carries baseline ('eventbus_ledger_baseline',4,4)+user_version=4; rag/session assert no schema_migrations. Refusal tests left unchanged. |
| 2 | Add or update tests per Validation plan | Completed | — | — | This row is itself a test module Added the test module itself. 4 new tests pass; full module 72 pass; tests/db 372 pass; test_eventbus_schema_equivalence green. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | ruff format OK; ruff check OK; mypy clean. Coordinated with test_eventbus_schema_equivalence.py (fingerprint shape unchanged by row 04). |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | — | Out of scope: migration runner tests (rows 14,17), schema.sql (row 04), ledger DDL in Python (row 09). |

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
- **Requirement ID**: `REQ-001`, `REQ-006`
- **Source issue**: `issues/20261029-104500_dbmig001_forward-only-db-migrations.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261029-214108_dbmig001_forward-only-db-migrations.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-071336
- **Related target files**: `tests/db/test_create_schema.py`