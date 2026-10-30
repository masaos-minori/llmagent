# Implementation Procedure: `tests/shared/test_db_migrations.py` (framework regression tests)

## Goal
Create regression coverage for the shared migration framework: success, failure, interruption, refusal classes, dry-run purity, and gate semantics (Plan row 14; issue Testing Expectations; REQ-001–REQ-004).

## Scope
- In scope: one new pytest module exercising `scripts/shared/db_migrations.py` (row 01) directly with a toy domain registry and file-based SQLite fixtures.
- Out of scope: domain wiring tests (rows 15, 17), CLI tests (rows 15, 17).

## Assumptions
- Test-first ordering: this module is written against the row-01 contract and must fail (import error) until row 01 lands — that failing state is the contract lock, per the Plan's test matrix.
- Fixtures use temporary directories only; no production DB paths (`rules/env.md` paths never opened by tests).
- Injected `verify_backup` callables are stubbed per test; the framework's generic `PRAGMA integrity_check` runs on real temp files.

## Design decisions
- One toy domain registry ("toydb") with a 1→2→3 step chain plus a deliberately cyclic pair, so framework semantics are tested without importing `db`/`eventbus` (mirrors the import contract the framework must keep).
- Refusal assertions match on exception type + message fragment, not exit codes (CLIs map codes in rows 15/17).

## Alternatives considered
- Testing via the domain CLIs only — rejected: framework edge cases (cycle detection, mid-step rollback) need direct runner access.

## Implementation
### Target file
- `tests/shared/test_db_migrations.py` (new)

### Procedure
1. Fixtures: temp `toydb.sqlite` builder at version 1, backup helper producing `integrity_check ok` copies, checkpoint helper.
2. Tests:
   - Happy path: 1→3 migrates, preserves inserted rows, writes one ledger row per step with `applied_at` ISO-8601 UTC.
   - Mid-migration failure: step 2 mutation raises; ledger has step-1 row only; DB byte-state equals post-step-1 (rollback per step).
   - Interrupted migration: process-level simulation (connection closed mid-step) leaves DB at a consistent ledger-verified version; resume re-resolves from ledger.
   - Downgrade request (3→1) refused before any mutation (DB mtime/hash unchanged).
   - Unknown target (3→9) refused; cycle in registry detected at resolution time.
   - Dry-run: full gate on throwaway copy; original file hash identical byte-for-byte (REQ-004/AC-5).
   - Backup gate: missing backup → refusal; corrupted backup (integrity_check fails) → refusal before opening the live DB for write (REQ-002/AC-4).
   - Missing checkpoint record for the step → refusal.
3. Deterministic time: freeze/compare via relative assertions, no wall-clock sleeps.

### Method
Plain pytest + stdlib `sqlite3` on tmp_path files; no monkeypatching of framework internals — failures injected through registry-registered step functions that raise.

### Details
- Toy registry steps are plain callables registered only in-test; the real registries are never mutated.

## Compatibility considerations
- New file only. Must not import `db` or `eventbus` layers (keeps `lint-imports` clean for tests/shared).

## Security considerations
- Test fixtures contain no secrets; temp DBs under tmp_path. Subprocess use (if any) per `rules/coding.md` subprocess rule with argv lists.

## Rollback considerations
- Delete the file; no production impact.

## Validation plan
- Automated: `uv run pytest tests/shared/test_db_migrations.py` — fails before row 01 lands, passes after; `uv run mypy --no-namespace-packages tests/` clean.
- Manual: none.

## Completion criteria
- All nine test groups pass post-row-01; dry-run byte-identity asserted by hash; refusals asserted pre-mutation.

## Out of Scope
- Domain registry/CLI tests (rows 15, 17). Deploy gates (row 13).

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
- **Requirement ID**: `REQ-001`–`REQ-004`
- **Source issue**: `issues/20261029-104500_dbmig001_forward-only-db-migrations.md`
- **Source requirement**: N/A: no standalone requirement document exists
- **Source plan**: `plans/20261029-214108_dbmig001_forward-only-db-migrations.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Related target files**: `tests/shared/test_db_migrations.py`
- **Generated at**: 20261030-071336
