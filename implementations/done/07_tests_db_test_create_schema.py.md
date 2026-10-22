## Goal
Remove the EventBus migration tests that seed legacy databases or patch the removed function, keeping the fresh-database test under a correctly named class (REQ-005).

## Scope
- `TestEventbusAckedAtMigration` and the DDL-error note that points to it; the workflow tests belong to a sibling procedure.

## Assumptions
- `test_bootstrap_creates_current_schema_on_a_fresh_database` asserts the three tables and the `acked` column shape on an empty path; it stays valid after the change (the DDL creates them).
- `_seed_legacy_db`, the legacy conversion tests, and `test_migration_failure_is_logged_with_its_own_label` (which patches `db.create_schema.apply_eventbus_migrations`) cannot pass after the function is removed.

## Design decisions
- Keep the fresh-database test, rename the class to describe EventBus schema creation, and drop its docstring's reference to the migration.
- Update the trailing comment about `create_eventbus_schema`'s DDL-error path: it keeps its own inline handling; remove the sentence pointing to the migration test class.

## Alternatives considered
N/A: removal fixed by the Plan.

## Implementation
### Target file
`tests/db/test_create_schema.py`

### Procedure
1. Delete `_seed_legacy_db`, `test_bootstrap_migrates_acked_at_to_acked`, `test_bootstrap_is_idempotent_after_conversion`, and `test_migration_failure_is_logged_with_its_own_label`.
2. Rename `TestEventbusAckedAtMigration` to an EventBus schema-creation class name; rewrite its docstring and the fresh-database test docstring ("Migrations now run before the DDL" is no longer true).
3. Adjust the comment after the DDL-error test so it no longer refers to the removed class.
4. Remove imports left unused (for example `logging` if no test uses it; check before removing).

### Method
- Re-read the file before editing: the workflow-migration procedure edits other classes in this file; apply sequentially.
- After editing run `rg "apply_eventbus_migrations|AckedAtMigration|acked_at" tests/db/test_create_schema.py` (no match expected except the retained column-shape assertion, which refers to `acked`).

### Details
- Keep `_make_db_config`, `_table_names`, and the shared fixtures untouched.

## Compatibility considerations
N/A: test-only.

## Security considerations
N/A: test-only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/db/test_create_schema.py -q`, then the full suite once; `uv run ruff check` on the file.

## Completion criteria
- No test references `apply_eventbus_migrations` or seeds an `acked_at` database; the fresh-database test passes.

## Out of Scope
- Workflow, RAG, and session tests.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Delete the legacy-seeding and patched-migration tests | Done | 20261022-101015 | 20261022-101015 | Removed `_seed_legacy_db`, `test_bootstrap_migrates_acked_at_to_acked`, `test_bootstrap_is_idempotent_after_conversion`, `test_migration_failure_is_logged_with_its_own_label`. |
| 2 | Rename the class and fix docstrings and the comment | Done | 20261022-101015 | 20261022-101015 | Renamed to `TestEventbusSchemaCreation`; fixed fresh-db docstring and the DDL-error comment. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Done | 20261022-101015 | 20261022-101015 | 51 passed; ruff clean; no leftover refs. |

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
- **Requirement ID**: `REQ-005` (remove migration tests, keep fresh-database coverage)
- **Source issue**: `issues/20261021-102130_rmebmig_remove-the-eventbus.sqlite-schema-migrations.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261022-093935_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-101015
- **Related target files**: tests/db/test_create_schema.py
