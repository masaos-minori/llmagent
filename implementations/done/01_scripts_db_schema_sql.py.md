## Goal
Delete the EventBus bootstrap migration list and its apply function (REQ-001: remove `_EVENTBUS_MIGRATIONS` and `apply_eventbus_migrations()`).

## Scope
- Remove both symbols, fix any text citing them, and drop `import sqlite3` if nothing else in the module uses it.
- No change to `EVENTBUS_SCHEMA_SQL_PATH`, `build_eventbus_schema_sql()`, or the other schema builders.

## Assumptions
- `apply_eventbus_migrations()` is called only from `create_schema.py` and patched only in `tests/db/test_create_schema.py` (verified by search).
- `sqlite3` is used in this module only by the two apply functions (verified); the workflow function is removed by a sibling Plan, so whichever of the two Plans lands last removes the import.

## Design decisions
- Delete by symbol; do not leave a tombstone comment (Current-Specification-Only policy).

## Alternatives considered
N/A: deletion required by the Plan.

## Implementation
### Target file
`scripts/db/schema_sql.py`

### Procedure
1. Delete the `_EVENTBUS_MIGRATIONS` list and the comment block explaining the `acked_at` conversion that sits inside it.
2. Delete `apply_eventbus_migrations()`.
3. Remove `import sqlite3` if no other use remains (ruff F401); keep `logging` and the `logger` declaration (the accepted unused-logger boilerplate).
4. Check the module docstring for any mention and remove it.

### Method
- Re-read the file before editing: the workflow-migration procedure edits adjacent regions; apply sequentially.
- Confirm with `rg "apply_eventbus_migrations|_EVENTBUS_MIGRATIONS" scripts tests tools docs` afterwards (remaining hits belong to sibling procedures).

### Details
- Module size only shrinks (16384-byte gate).

## Compatibility considerations
No behavior change for a database at the current schema. The only callers are covered by the `create_schema.py` and test procedures.

## Security considerations
N/A: removes code that ran DDL/DML on an existing database at each bootstrap.

## Rollback considerations
Revert the commit; no data is changed by this edit.

## Validation plan
- `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `uv run python tools/check_module_size.py`, `uv run pytest tests/db -q`.

## Completion criteria
- Neither symbol exists; no unused import remains; DDL builders unchanged.

## Out of Scope
- The workflow migration symbols (separate Plan) and any DDL change.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Delete the list and function; drop the unused import | Done | 20261022-101015 | 20261022-101015 | Removed `_EVENTBUS_MIGRATIONS` and `apply_eventbus_migrations()`; kept `import sqlite3` (still used by `apply_workflow_migrations`). |
| 2 | Tests are covered by the test-file procedures | Done | 20261022-101015 | 20261022-101015 | Migration tests removed by proc 05; create_schema EventBus tests removed by proc 07. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Done | 20261022-101015 | 20261022-101015 | ruff + mypy clean; full db/eventbus suite green (669 passed, 1 skipped). |

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
- **Requirement ID**: `REQ-001` (remove the EventBus bootstrap migration path)
- **Source issue**: `issues/20261021-102130_rmebmig_remove-the-eventbus.sqlite-schema-migrations.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261022-093935_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-101015
- **Related target files**: scripts/db/schema_sql.py
