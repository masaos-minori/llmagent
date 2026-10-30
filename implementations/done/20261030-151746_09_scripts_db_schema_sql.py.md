## Goal

Add the `schema_migrations` (new) ledger DDL to the workflow DDL set in `scripts/db/schema_sql.py` (`REQ-001`, registry state; `REQ-006`, applied-state ledger).

## Scope

- Modify only `scripts/db/schema_sql.py`.

## Assumptions

- Verified (Step 3a): the workflow DDL (`_WORKFLOW_SCHEMA`, ending with `workflow_schema_version` at `:214`) is returned by `build_workflow_schema_sql()`; `WORKFLOW_SCHEMA_VERSION = "1.1.0"` at `:25`. Six Frozen Plans target this file (`check_plan_target_overlaps.py`): toolexec001, ragcorpus001, wftaskapi001, wfrecovery001, wflease001, and this one; each edits a different table or constant, so the edits are compatible and sequenced by rebasing.
- Decision (row 06): the ledger table is added without bumping `WORKFLOW_SCHEMA_VERSION`; the DDL is `IF NOT EXISTS`, so existing databases gain it through `ensure_ledger`. Execution order follows the Plan's `Implementation steps` phases (this row is in Phase 3, first), not necessarily the table `seq`.
- Names that `tools/stale_detector.py` flags in this document are created by other rows of this Plan (the framework row 01 and the domain, drill, and schema rows it names) and exist when `code-implementation` executes the rows in Plan phase order.

## Design decisions

- Add the `CREATE TABLE IF NOT EXISTS schema_migrations (...)` statement with the same columns as `LEDGER_DDL` in `scripts/shared/db_migrations.py`; a test (row 18 document) asserts the two are identical so there is one definition in effect.

## Alternatives considered

- Import `LEDGER_DDL` from `shared.db_migrations` and splice it in: rejected for the ordinary DDL set, `schema_sql.py` holds literal DDL; the equality test is the guard.

## Implementation

### Target file

`scripts/db/schema_sql.py`

### Procedure

1. Append the ledger statement to the workflow DDL template after `workflow_schema_version`.

### Method

- Match the existing DDL style; no change to the other templates.

### Details

- N/A: no further details beyond the other sections.

## Compatibility considerations

- Additive table; `IF NOT EXISTS` keeps existing databases valid and the existing `REQUIRED_WORKFLOW_TABLES` check unaffected.

## Security considerations

- N/A: DDL only.

## Rollback considerations

- Revert the commit; an extra empty table is harmless.

## Validation plan

- `uv run pytest tests/db/test_create_schema.py -v`
- `uv run ruff format scripts/db/schema_sql.py`, `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml -ll`, `uv run python tools/check_module_size.py`
- `uv run python tools/check_db_separation.py` (table ownership inventory)

## Completion criteria

- `build_workflow_schema_sql()` creates `schema_migrations` (new) with the framework's columns; the table-ownership check still passes.

## Out of Scope

- Version bump and any other table (other Plans' rows).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the ledger DDL | Completed | 20261030-165727 | 20261030-165727 | Plan Phase 3 ledger DDL added to _WORKFLOW_SCHEMA |
| 2 | Add or update tests per Validation plan | Completed | 20261030-165727 | 20261030-165727 | Covered by the row 18 document covered by row 18 tests |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261030-165727 | 20261030-165727 | validators passed; full suite 10485 passed (batched Phase 3 run) |

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
- **Source issue**: issues/20261029-104500_dbmig001_forward-only-db-migrations.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261029-214108_dbmig001_forward-only-db-migrations.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-151746
- **Related target files**: scripts/db/schema_sql.py