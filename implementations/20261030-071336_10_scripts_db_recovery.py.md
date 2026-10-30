## Goal
Expose `scripts/db/recovery.py`'s integrity-check and domain-identity helpers as public functions so the migration gate (rows 01/06), the drill harness (row 11), and rotation verification (row 12) reuse them instead of building parallel checks (REQ-002 backup gate, REQ-007 drill reuse).

## Scope
- In scope: `scripts/db/recovery.py` — public wrappers for `_run_integrity_check` (`recovery.py:90-106`), `_verify_domain_identity` (`:142-162`), and `_backup_is_usable` (`:165-191`).
- Out of scope: any behavior change to the recovery flow (`recover_corruption`, `_restore_from_backup` and friends stay byte-identical), new checks, `_REQUIRED_TABLE_BY_DOMAIN` content changes.

## Assumptions
- The three helpers already behave exactly as rows 01/06/11/12 need: integrity via `PRAGMA integrity_check` with typed `DbCondition`, domain identity via required-table lookup with unknown-target passthrough, and `_backup_is_usable` composing both into `(failed_action, detail)` where `(None, "")` means usable.
- Public exposure is a thin delegation layer (module-level `run_integrity_check`, `verify_domain_identity`, `backup_is_usable` wrappers calling the private implementations) rather than renaming the privates, so every existing internal call site and `tests/db/test_db_recovery.py` keep passing untouched (Plan row: "no behavior change").

## Design decisions
- Wrappers re-export the same signatures and return types (`tuple[DbCondition, str | None]`, `tuple[bool, str | None]`, `tuple[str | None, str]`); no dataclass reshaping.
- `_REQUIRED_TABLE_BY_DOMAIN` (`recovery.py:136-139`) keeps only rag/session entries: the workflow domain check lives in row 06's `verify_backup`, the eventbus domain check in row 02's, per the Plan's domain-registry split.

## Alternatives considered
- Renaming `_run_integrity_check` etc. to public names — rejected: touches every internal caller and the existing recovery tests for no gain; wrappers make the public surface explicit and auditable.

## Implementation
### Target file
- `scripts/db/recovery.py`

### Procedure
1. Add three public wrapper functions delegating to the privates, with docstrings stating they are the cross-module entry points for migration/drill/rotation consumers.
2. No other edits.

### Method
Additive functions only; verify with a diff that no existing body changed.

### Details
- Consumers: row 01 injected verifier (db domain), row 06 `verify_backup`, row 11 drill harness, row 12 post-archive check. Import direction stays inside the `db` layer or `shared`-provided callables (row 01 receives them as callables, never imports them).

## Compatibility considerations
- `tests/db/test_db_recovery.py` must pass unchanged (regression gate named in the Plan row).

## Security considerations
- No new surface; helpers already open candidate files read-only through `SQLiteHelper`.

## Rollback considerations
- Revert the commit; consumers that land later (rows 06/11/12) revert with it in `seq` order.

## Validation plan
- `uv run pytest tests/db/test_db_recovery.py` (unchanged behavior).
- New call-site coverage lives in rows 15/17/19 tests.
- `uv run mypy --no-namespace-packages scripts/`.

## Completion criteria
- Public wrappers exist with identical behavior to the privates; the recovery flow diff is empty; import-linter contracts KEPT.

## Out of Scope
- Drill harness (row 11), rotation change (row 12), registry verifiers (rows 02/06).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | Existing tests unchanged; new coverage from rows 15/17/19 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A for this row |

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
- **Requirement ID**: `REQ-002` (backup gate), `REQ-007` (drill)
- **Source issue**: `issues/20261029-104500_dbmig001_forward-only-db-migrations.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261029-214108_dbmig001_forward-only-db-migrations.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-071336
- **Related target files**: `scripts/db/recovery.py`
