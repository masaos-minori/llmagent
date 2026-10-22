## Goal
Remove the two tests that call the removed migration function and the now-unneeded import (REQ-004: remove or rewrite migration tests).

## Scope
- Delete the "Migration scenario" section (two tests) and adjust the import line.
- Keep every other test (error kind/detail, workflow id, attempt number, processed events).

## Assumptions
- The columns the migration tests assert are created by the base workflow DDL, and the retained tests of those columns already use `build_workflow_schema_sql()` through the file's fixture (verified: the fixture executes the base DDL).
- `build_workflow_schema_sql` stays imported because the fixture uses it.

## Design decisions
- Delete rather than rewrite: the base-DDL behavior is already covered by the retained tests, so a rewritten test would duplicate them.

## Alternatives considered
N/A: removal required by the Plan.

## Implementation
### Target file
`tests/agent/workflow/test_workflow_stage_persistence.py`

### Procedure
1. Delete the section comment `# --- Migration scenario ---` and the two tests `test_migration_adds_columns_to_existing_db` and `test_migration_idempotent`.
2. Change the import to `from db.schema_sql import build_workflow_schema_sql`.

### Method
- Delete by symbol; run `rg "apply_workflow_migrations" tests` afterwards (no match expected).

### Details
- The file ends after the deleted section; confirm it still ends with a single trailing newline.

## Compatibility considerations
N/A: test-only.

## Security considerations
N/A: test-only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/workflow/test_workflow_stage_persistence.py -q`; `uv run ruff check tests/agent/workflow/test_workflow_stage_persistence.py`.

## Completion criteria
- The file imports and uses only `build_workflow_schema_sql` from `db.schema_sql`, and the remaining tests pass.

## Out of Scope
- Other workflow tests and the base DDL.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Delete the migration scenario tests and fix the import | Completed | 20261022-105309 | 20261022-105309 | Changed: tests/agent/workflow/test_workflow_stage_persistence.py |
| 2 | Run the file's tests | Completed | 20261022-105309 | 20261022-105309 | validated; full suite 9690 passed, 14 skipped with coverage run; ruff, mypy, lint-imports, check_module_size, check_db_separation pass; diff-cover: no measurable lines |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261022-105309 | 20261022-105309 | validated; full suite 9690 passed, 14 skipped with coverage run; ruff, mypy, lint-imports, check_module_size, check_db_separation pass; diff-cover: no measurable lines |

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
- **Requirement ID**: `REQ-004` (remove or rewrite migration tests)
- **Source issue**: `issues/20261021-102049_rmwfmig_remove-the-workflow.sqlite-incremental-migrations.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261022-093726_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-100642
- **Related target files**: tests/agent/workflow/test_workflow_stage_persistence.py