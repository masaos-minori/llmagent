## Goal

Register the task-key rename migration in `scripts/db/migrations_workflow.py` (`REQ-003`, rename; `REQ-004`, delivered as a registered step that preserves rows).

## Scope

- Modify only `scripts/db/migrations_workflow.py`.
- Plan amendment (user-approved 2026-10-30): this row was appended after the last row once the registry landed.

## Assumptions

- Registry contract (verified in `scripts/shared/db_migrations.py`): `MigrationSpec(migration_id, from_version, to_version, apply, precondition, postcondition)`; `apply` must use `conn.execute` only, never `executescript`; the runner writes the new `workflow_schema_version` row and the `schema_migrations` row in the same transaction and verifies the fingerprint against `build_workflow_schema_sql()` when `to_version` equals `WORKFLOW_SCHEMA_VERSION`.
- Version chain: default `from_version` `"1.1.0"`, `to_version` `"1.2.0"`; if the wfrecovery001 spec already exists in `MIGRATIONS`, chain after its `to_version` instead (see the row 04 document).
- `tests/db/test_migrations_workflow.py` asserts the registry is one linear chain ending at `WORKFLOW_SCHEMA_VERSION`, so it needs no change.
- Names that `tools/stale_detector.py` flags in this document are created by other rows of the same Plan or by an earlier row of it, and exist when `code-implementation` executes the rows in order.

## Design decisions

- `ALTER TABLE tasks RENAME COLUMN idempotency_key TO task_nonce` keeps the column-level `UNIQUE` and the data; no backfill.

## Alternatives considered

- Rebuild the table: rejected, not needed for a rename.

## Implementation

### Target file

`scripts/db/migrations_workflow.py`

### Procedure

1. Add `_rename_task_key` (new)(conn) running the `ALTER TABLE ... RENAME COLUMN` statement, a precondition that raises when `tasks` has no `idempotency_key` column or already has `task_nonce`, and register one spec `rename-task-nonce` in `MIGRATIONS`.

### Method

- Read the column list with `PRAGMA table_info(tasks)` in the precondition; the postcondition checks `task_nonce` exists and `idempotency_key` does not.

### Details

- The migration is invoked by `scripts/db/migrate_db.py --apply` and is backup-gated by the runner.

## Compatibility considerations

- Registers the first workflow spec; databases at the old version are migrated, others are refused as before.

## Security considerations

- N/A: static SQL, no input.

## Rollback considerations

- Forward-only; restore from the pre-migration backup the runner takes.

## Validation plan

- `uv run pytest tests/db/test_create_schema.py tests/db/test_migrations_workflow.py -v`
- `uv run ruff format scripts/db/migrations_workflow.py`, `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml -ll`, `uv run python tools/check_module_size.py`

## Completion criteria

- `MIGRATIONS` holds the rename spec chained after the current version, and the end-to-end migration test (row 09 document) passes.

## Out of Scope

- The DDL and version constant (row 04), code rename, tests, and docs.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Register the rename spec | Completed | 20261030-173958 | 20261030-173958 | Plan Phase 3; with rows 04 and 09 rename-task-nonce spec registered |
| 2 | Add or update tests per Validation plan | Completed | 20261030-173958 | 20261030-173958 | Covered by the row 09 document covered by row 09 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261030-173958 | 20261030-173958 | validators passed; full suite 10487 passed (wftaskapi001 release unit run); production workflow.sqlite mtime unchanged |

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
- **Requirement ID**: REQ-003, REQ-004
- **Source issue**: issues/20261030-105723_wftaskapi001_consolidate-task-persistence.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-113553_wftaskapi001_consolidate-task-persistence.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-125133
- **Related target files**: scripts/db/migrations_workflow.py