## Goal
Make `_schema_ddl()` return the base workflow DDL only, because the workflow migration list no longer exists (REQ-003: read only the base DDL).

## Scope
- Remove the workflow migration text from the workflow entry of `_schema_ddl()`.
- The EventBus entry (which still reads its own migration list) is changed by a separate Plan.

## Assumptions
- The migrations only add columns already present in the base workflow DDL and drop a table that is not in it, so auditing the base DDL covers the same table ownership (verified against the base DDL).
- `tests/tools/test_check_db_separation.py` consumes the dict returned by `_schema_ddl()` and does not reference the migration variable.

## Design decisions
- Return `schema_sql.build_workflow_schema_sql()` directly for `workflow`.

## Alternatives considered
N/A: single-expression change.

## Implementation
### Target file
`tools/check_db_separation.py`

### Procedure
1. In `_schema_ddl()` delete the `migrations_workflow = ...` assignment.
2. Change the `"workflow"` value to `schema_sql.build_workflow_schema_sql()` (no `+ ";\n" + migrations_workflow`).
3. Adjust the function docstring if it says "migrations included" only for the workflow part.

### Method
- Minimal edit; keep the EventBus lines untouched.
- Apply sequentially with the EventBus removal procedure for the same function; re-read the function before editing.

### Details
- Follow `routing.md` "Adding a new tool": ruff format/check, `uv run mypy tools/check_db_separation.py`, `uv run bandit tools/check_db_separation.py`, and a smoke run on live data.

## Compatibility considerations
The checker's table-ownership verdicts must be unchanged on the live repository.

## Security considerations
N/A: read-only checker.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_db_separation.py` (same verdict as before) and `uv run pytest tests/tools/test_check_db_separation.py -q`.
- `uv run ruff format`/`check`, `uv run mypy tools/check_db_separation.py`, `uv run bandit tools/check_db_separation.py`, `uv run python tools/check_tool_descriptions_sync.py`.

## Completion criteria
- The tool no longer references `_WORKFLOW_MIGRATIONS` and passes on the live repository.

## Out of Scope
- The EventBus entry of `_schema_ddl()` and any change to the checks themselves.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the workflow migration text from `_schema_ddl()` | Completed | 20261022-105304 | 20261022-105304 | Changed: tools/check_db_separation.py |
| 2 | Run the tool's tests | Completed | 20261022-105304 | 20261022-105304 | validated; full suite 9690 passed, 14 skipped with coverage run; ruff, mypy, lint-imports, check_module_size, check_db_separation pass; diff-cover: no measurable lines |
| 3 | Run the tool validation sequence per `routing.md` | Completed | 20261022-105304 | 20261022-105304 | validated; full suite 9690 passed, 14 skipped with coverage run; ruff, mypy, lint-imports, check_module_size, check_db_separation pass; diff-cover: no measurable lines |

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
- **Requirement ID**: `REQ-003` (audit the base workflow DDL only)
- **Source issue**: `issues/20261021-102049_rmwfmig_remove-the-workflow.sqlite-incremental-migrations.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261022-093726_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-100642
- **Related target files**: tools/check_db_separation.py