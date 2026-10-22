## Goal
Remove the tests that call `_migrate()` and the fixtures only they use, keeping the pragma test (REQ-005).

## Scope
- Delete `TestMigrateAddsNewColumns`, `TestMigrateConvertsLegacyAckedAt`, the `pre_migration_conn` and `legacy_ack_conn` fixtures, and the `_migrate` import.
- Keep `tmp_conn` and `TestApplyEventbusPragmas`; fix the module docstring.

## Assumptions
- `TestApplyEventbusPragmas` uses only `tmp_conn` (verified); the legacy fixtures are used only by the deleted classes.
- Renaming the file would be a file move, which is out of scope for this workflow; the file keeps its name.

## Design decisions
- Keep the file in place with the one remaining test class; correct the docstring so it describes pragma tests, not migration.

## Alternatives considered
- Moving the pragma test to another file and deleting this one: rejected, it is a rename/move outside the allowed operations.

## Implementation
### Target file
`tests/eventbus/test_eventbus_db_migration.py`

### Procedure
1. Delete the two migration test classes and the two legacy fixtures.
2. Remove `from eventbus.schema import _migrate` and any import left unused (`Generator` remains used by `tmp_conn`).
3. Rewrite the module docstring to describe the pragma tests; drop the SQLite DROP COLUMN note if no remaining test needs it.

### Method
- Delete by symbol; run `ruff` to catch unused imports.

### Details
- Keep `tmp_conn` as is (file-based connection fixture).

## Compatibility considerations
N/A: test-only.

## Security considerations
N/A: test-only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/eventbus/test_eventbus_db_migration.py -q`; `uv run ruff check tests/eventbus/test_eventbus_db_migration.py`.

## Completion criteria
- The file contains only the pragma test class, no reference to `_migrate`, and passes.

## Out of Scope
- Other EventBus tests and file renaming.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Delete the migration classes, legacy fixtures, and the import | Pending | — | — | |
| 2 | Run the file's tests | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-005` (remove migration tests, keep the pragma test)
- **Source issue**: `issues/20261021-102130_rmebmig_remove-the-eventbus.sqlite-schema-migrations.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261022-093935_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-101015
- **Related target files**: tests/eventbus/test_eventbus_db_migration.py
