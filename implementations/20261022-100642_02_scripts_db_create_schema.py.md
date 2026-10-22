## Goal
Make `create_workflow_schema()` create-only plus version recording, and make it refuse to record the current version over a database whose latest recorded version differs (REQ-002: remove the migration call; REQ-005: refuse-to-stamp guard).

## Scope
- Remove the migration import and call (and the assertion that exists only for it) from `create_workflow_schema()`.
- Change `_record_workflow_schema_version()` so a differing latest version raises instead of being overwritten.
- No change to the other `create_*_schema()` functions (the EventBus function belongs to a separate Plan).

## Assumptions
- Today `_record_workflow_schema_version()` inserts the current version whenever the latest recorded version differs, so after the migrations are removed an older database would be stamped as current while its columns stay old (verified; `REQUIRED_WORKFLOW_TABLES` omits the migration-added columns).
- The guard is a refusal, not a replacement migration or a fallback (Plan UNK-01: owner confirms at review).
- `deploy/init_db.sh` runs `create_schema()`; a raised error there stops the deploy before services start.

## Design decisions
- Behavior of the record step: no row in `workflow_schema_version` records the current version; a latest version equal to the current version does nothing; any other latest version logs an error and raises `RuntimeError` naming both versions and telling the operator to recreate the database.
- Raise before inserting, so nothing is written on refusal.

## Alternatives considered
- Keep stamping and rely on the startup check: rejected, the startup check does not verify the migration-added columns, so an old database could pass.
- Add the missing columns to `REQUIRED_WORKFLOW_TABLES`: rejected, it changes the startup check that the Issue says must stay unchanged.

## Implementation
### Target file
`scripts/db/create_schema.py`

### Procedure
1. Remove `apply_workflow_migrations` from the `from db.schema_sql import (...)` block.
2. In `create_workflow_schema()` remove the `assert db.conn is not None, ...` statement and the `apply_workflow_migrations(db.conn)` call; keep DDL execution, `_record_workflow_schema_version(db)`, and `db.commit()`.
3. In `_record_workflow_schema_version()` replace the unconditional insert-on-difference with the behavior described under Design decisions; update its docstring.

### Method
- Keep the `db.execute(...)` read of the latest row as is; branch on `current is None` / `current != WORKFLOW_SCHEMA_VERSION`.
- Log with `logger.error("...")` using the module's existing pattern before raising, as `_execute_schema_ddl` does.
- Do not catch the error inside `create_workflow_schema()`; let it propagate to the caller (`create_schema()` / `init_db.sh`).

### Details
- The error message names `workflow_schema_version`, the recorded version, and `WORKFLOW_SCHEMA_VERSION`; it contains no paths or secrets.
- A database file created from the current DDL on an empty path ends with exactly one version row.

## Compatibility considerations
First run and same-version re-run behave as before. Running against a database at a different version changes from "stamp" to "raise"; the only deployment is at the current version (read-only check before deploy).

## Security considerations
N/A: no new input; the message exposes only version strings.

## Rollback considerations
Revert the commit; no schema or data change. If the guard was already triggered, nothing was written.

## Validation plan
- `uv run pytest tests/db/test_create_schema.py tests/conftest.py -q` via the test procedure; `uv run pytest tests/agent/workflow -q` (fixtures call `create_workflow_schema()`).
- `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit scripts/db/create_schema.py`.

## Completion criteria
- Creating the schema on an empty path and re-running at the current version both succeed with one recorded version.
- A differing latest recorded version raises `RuntimeError` and writes nothing.
- No reference to the removed function remains in the file.

## Out of Scope
- `create_eventbus_schema()`, the startup schema check, and the version value.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the import, assertion, and call; add the refuse-to-stamp guard | Pending | — | — | |
| 2 | Tests are covered by the procedure for `tests/db/test_create_schema.py` | Pending | — | — | |
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
- **Requirement ID**: `REQ-002` (remove the migration call), `REQ-005` (refuse to stamp a differing version)
- **Source issue**: `issues/20261021-102049_rmwfmig_remove-the-workflow.sqlite-incremental-migrations.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261022-093726_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-100642
- **Related target files**: scripts/db/create_schema.py
