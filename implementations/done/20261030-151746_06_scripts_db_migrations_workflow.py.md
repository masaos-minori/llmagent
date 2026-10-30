## Goal

Create the `workflow.sqlite` migration registry in `scripts/db/migrations_workflow.py` (`REQ-001`, domain registry; `REQ-009`, rows survive registered upgrades).

## Scope

- Create only `scripts/db/migrations_workflow.py`.
- This is the registry that unblocks the schema rows of `plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md` and `plans/20261030-113553_wftaskapi001_consolidate-task-persistence.md`: they register their specs here in their own rows.

## Assumptions

- Step 3a (Plan correction): `workflow.sqlite` has no `PRAGMA user_version`; its version is the latest `workflow_schema_version` row (`version`, `applied_at`) written by `_record_workflow_schema_version` in `scripts/db/create_schema.py`. The domain accessors therefore read and write that table, and a version bump inserts a new row.
- No workflow fingerprint helper exists: `verify_shape` builds an in-memory database from `build_workflow_schema_sql()` (`scripts/db/schema_sql.py`) and compares `build_fingerprint` of both connections, reusing `scripts/shared/eventbus_schema_fingerprint.py`.
- Depends on rows 01 and 09 (`schema_migrations` DDL). Execution order follows the Plan's `Implementation steps` phases (this row is in Phase 3), not necessarily the table `seq`.
- Names that `tools/stale_detector.py` flags in this document are created by other rows of this Plan (the framework row 01 and the domain, drill, and schema rows it names) and exist when `code-implementation` executes the rows in Plan phase order.

## Design decisions

- Export `WORKFLOW_DOMAIN` (new) and an empty `MIGRATIONS` (new) tuple; the baseline for the ledger is a `ledger-baseline` spec (new) from the current `WORKFLOW_SCHEMA_VERSION` that only creates `schema_migrations`... unless row 09 adds the ledger without bumping the version; in that case `ensure_ledger` is called by the runner and no spec is needed.
- Decision: do not bump `WORKFLOW_SCHEMA_VERSION` for the ledger; `ensure_ledger` creates the table idempotently, so existing databases gain it on the first `migrate_db.py` run. Later schema rows bump the version and register specs.

- Correction (Step 3b): `WORKFLOW_DOMAIN` must pass a `connect` callable (opening the path through `SQLiteHelper` or `sqlite3` with the workflow pragmas) to `MigrationDomain`; see the row 01 document.

## Alternatives considered

- Bump the version for the ledger: rejected, it would force a migration of every existing database just to add an empty bookkeeping table.

## Implementation

### Target file

`scripts/db/migrations_workflow.py` (new)

### Procedure

1. Create the module with `WORKFLOW_DOMAIN` (new) and `MIGRATIONS` (new); `read_version` selects the latest `workflow_schema_version` row, `write_version` inserts one, and `verify_shape` compares fingerprints against `build_workflow_schema_sql()`.

### Method

- Open no connection at import time; accessors take the connection the runner passes.

### Details

- `workflow_schema_version.applied_at` orders rows; two versions written in the same second tie, so `read_version` orders by `applied_at DESC, rowid DESC`.

## Compatibility considerations

- New module; an empty registry changes no behavior. `scripts/agent/services/workflow_schema.py` keeps validating the latest version row, so a migrated database passes it.

## Security considerations

- N/A: no input boundary; parameterized SQL.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/db/test_migrations_workflow.py -v` (row 17 document)
- `uv run ruff format scripts/db/migrations_workflow.py`, `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml -ll`, `uv run python tools/check_module_size.py`
- `uv run python tools/check_db_separation.py`

## Completion criteria

- `WORKFLOW_DOMAIN` (new) reads and writes the version through `workflow_schema_version`, `verify_shape` detects a shape drift, and the registry is empty.

## Out of Scope

- Registering the attempt, task-key, or tool-snapshot specs (their own Plans' rows).
- `scripts/agent/services/workflow_schema.py` (reference file, not a target).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create the registry per Procedure | Completed | 20261030-165727 | 20261030-165727 | Plan Phase 3; after rows 01 and 09 migrations_workflow.py created (connect injected, Step 3b) |
| 2 | Add or update tests per Validation plan | Completed | 20261030-165727 | 20261030-165727 | Covered by the row 17 document covered by row 17 tests |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261030-165727 | 20261030-165727 | validators passed; full suite 10485 passed (batched Phase 3 run); coverage 100% |

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
- **Requirement ID**: REQ-001, REQ-009
- **Source issue**: issues/20261029-104500_dbmig001_forward-only-db-migrations.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261029-214108_dbmig001_forward-only-db-migrations.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-151746
- **Related target files**: scripts/db/migrations_workflow.py