## Goal
Remove the tests that depend on the removed migration symbols and add tests for the version record and the refuse-to-stamp guard (REQ-004: remove or rewrite migration tests; REQ-005: guard tests).

## Scope
- Workflow-related parts of the file only; the EventBus migration tests (`TestEventbusAckedAtMigration`) belong to a separate Plan.

## Assumptions
- The base-DDL tests `test_migration_workflow_id_column_exists` and `..._idempotent` pass without migrations because the base DDL already holds the column (verified in the base DDL).
- `_OLD_APPROVALS_DDL` and `_make_old_schema_db` are used only by the approvals-migration tests (verified by search), so they become unused.
- `_migrate(db_file)` is a thin helper around `create_workflow_schema()`; it is renamed because its name no longer describes it.

## Design decisions
- Keep one helper that creates a workflow database from `_WORKFLOW_SCHEMA_NO_VEC0` through `create_workflow_schema()`.
- New guard tests build the "older version" case by creating a current database and rewriting its recorded version, instead of seeding old table shapes.

## Alternatives considered
N/A: removal and replacement are fixed by the Plan.

## Implementation
### Target file
`tests/db/test_create_schema.py`

### Procedure
1. Delete `test_non_duplicate_column_error_propagates` (it patches `_WORKFLOW_MIGRATIONS`).
2. Rename `test_migration_workflow_id_column_exists` and `test_migration_workflow_id_column_idempotent` to names that describe base-DDL creation and idempotent re-run, and fix their docstrings (remove "applies migration" and "_migrate_workflow_schema").
3. Delete `_OLD_APPROVALS_DDL` and `_make_old_schema_db`; rename `_migrate` to `_create_workflow_db`.
4. Replace class `TestApprovalsMigration`: delete the two migration tests; keep `test_new_database_has_no_approvals_table`; rename the class to describe the version record.
5. Add tests: first run records exactly one version row equal to `WORKFLOW_SCHEMA_VERSION`; re-run at the current version keeps one row; when the recorded version is rewritten to a different value, `create_workflow_schema()` raises `RuntimeError` and the version log is unchanged.

### Method
- Reuse the existing patch pattern (`db.helper.build_db_config`, `db.create_schema.build_workflow_schema_sql`) via the helper.
- Read the log with a plain `sqlite3.connect` after the call; assert row count and latest version.

### Details
- Update the stale `_migrate` name uses; after the change `rg "_migrate\b" tests/db/test_create_schema.py` must show only EventBus-related names (none expected).
- Do not touch `TestEventbusAckedAtMigration`; apply sequentially with that Plan's procedure for the same file.

## Compatibility considerations
N/A: test-only; follows the library changes of the sibling procedures.

## Security considerations
N/A: temporary files only.

## Rollback considerations
N/A: revert the commit with the library change.

## Validation plan
- `uv run pytest tests/db/test_create_schema.py -q`, then the full suite once.
- `uv run ruff format`/`check`; `uv run mypy` on the file if covered by pre-commit.

## Completion criteria
- No test references `apply_workflow_migrations`, `_WORKFLOW_MIGRATIONS`, `_make_old_schema_db`, or `_OLD_APPROVALS_DDL`.
- The version-record and guard tests pass and fail without the guard.

## Out of Scope
- EventBus tests, RAG/session tests, and the removal of base-DDL tests.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the migration-dependent tests, helpers, and names | Completed | 20261022-105307 | 20261022-105307 | Changed: tests/db/test_create_schema.py |
| 2 | Add the version-record and guard tests | Completed | 20261022-105307 | 20261022-105307 | validated; full suite 9690 passed, 14 skipped with coverage run; ruff, mypy, lint-imports, check_module_size, check_db_separation pass; diff-cover: no measurable lines |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261022-105307 | 20261022-105307 | validated; full suite 9690 passed, 14 skipped with coverage run; ruff, mypy, lint-imports, check_module_size, check_db_separation pass; diff-cover: no measurable lines |

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
- **Requirement ID**: `REQ-004` (remove or rewrite migration tests), `REQ-005` (guard tests)
- **Source issue**: `issues/20261021-102049_rmwfmig_remove-the-workflow.sqlite-incremental-migrations.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261022-093726_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-100642
- **Related target files**: tests/db/test_create_schema.py