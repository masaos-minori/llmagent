## Goal
Delete the workflow migration list and its apply function and fix every comment that cites them (REQ-001: remove the mechanism).

## Scope
- Remove `_WORKFLOW_MIGRATIONS` and `apply_workflow_migrations()`, and update the module docstring, the version-constant comment, and the session-DDL comment.
- No change to `_WORKFLOW_SCHEMA`, `build_workflow_schema_sql()`, `WORKFLOW_SCHEMA_VERSION`, or the EventBus list and function (separate Plan).

## Assumptions
- All seven migration entries are no-ops on a fresh database because the base workflow DDL already contains the added columns and has no `approvals` table (verified: `error_kind`, `error_detail`, `workflow_id`, `attempt_number` are in the base DDL).
- `import sqlite3` and `logger` stay in use by `apply_eventbus_migrations()`; if the EventBus removal Plan lands first, unused-import cleanup is that Plan's concern, not this one.

## Design decisions
- Keep the constant and reword its comment to describe when to bump it (schema changes that require recreating the database) instead of citing the removed list.
- Do not leave a tombstone comment about the removal (Current-Specification-Only policy).

## Alternatives considered
N/A: deletion required by the Plan; no alternative keeps the mechanism.

## Implementation
### Target file
`scripts/db/schema_sql.py`

### Procedure
1. Delete the `_WORKFLOW_MIGRATIONS` list, including the explanatory comment block above its approval-stage entries.
2. Delete `apply_workflow_migrations()`.
3. Remove the `apply_workflow_migrations(conn)` line from the module docstring's function list.
4. Reword the comment above `WORKFLOW_SCHEMA_VERSION` ("Bump this constant whenever a new entry is added to _WORKFLOW_MIGRATIONS.") to say it is bumped when the workflow schema changes in a way that requires recreating the database.
5. In the comment above `_SESSION_SCHEMA_TEMPLATE`, drop the contrast with "workflow.sqlite's incremental _WORKFLOW_MIGRATIONS / apply_workflow_migrations" and describe session.sqlite as recreate-only DDL like the other create-only databases.

### Method
- Delete by symbol, not by line number; confirm with `rg "apply_workflow_migrations|_WORKFLOW_MIGRATIONS" scripts` afterwards.
- Re-read the file before editing: the EventBus removal Plan edits adjacent regions of the same file; apply sequentially.

### Details
- Keep `WORKFLOW_SCHEMA_VERSION = "1.1.0"` unchanged; the value is not touched by this Plan.
- Module size stays below the 16384-byte gate (the file shrinks).

## Compatibility considerations
No behavior change for a database at the current schema; callers of the removed symbols are only `create_schema.py`, `tools/check_db_separation.py`, and tests, all covered by sibling procedures.

## Security considerations
N/A: removes code that executed an UPDATE on task rows at every bootstrap; no new surface.

## Rollback considerations
Revert the commit; no data is changed by this edit.

## Validation plan
- `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `uv run python tools/check_module_size.py`.
- `rg "apply_workflow_migrations|_WORKFLOW_MIGRATIONS" scripts tests tools docs` shows only the references owned by sibling procedures until they land.
- `uv run pytest tests/db/test_create_schema.py -q` after the sibling test procedure.

## Completion criteria
- Neither symbol exists in the file and no comment refers to them.
- `WORKFLOW_SCHEMA_VERSION` and the DDL builders are unchanged.

## Out of Scope
- The EventBus migration list and function, the schema version value, and any DDL change.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Delete the list and function and fix the citing comments | Completed | 20261022-105300 | 20261022-105300 | Changed: scripts/db/schema_sql.py |
| 2 | Tests are covered by the procedures for the two test files | Completed | 20261022-105300 | 20261022-105300 | validated; full suite 9690 passed, 14 skipped with coverage run; ruff, mypy, lint-imports, check_module_size, check_db_separation pass; diff-cover: no measurable lines |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261022-105300 | 20261022-105300 | validated; full suite 9690 passed, 14 skipped with coverage run; ruff, mypy, lint-imports, check_module_size, check_db_separation pass; diff-cover: no measurable lines |

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
- **Requirement ID**: `REQ-001` (remove the migration mechanism)
- **Source issue**: `issues/20261021-102049_rmwfmig_remove-the-workflow.sqlite-incremental-migrations.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261022-093726_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-100642
- **Related target files**: scripts/db/schema_sql.py