## Goal
Make `create_eventbus_schema()` run the DDL only (REQ-002: DDL only; the schema is created on an empty path and left unchanged on a database at the current schema).

## Scope
- Remove the migration import, call, its error label, the explanatory comment, and the connection assertion in `create_eventbus_schema()`.
- Keep the inline DDL try/except and its `Failed to execute Event Bus schema DDL` log label.

## Assumptions
- `schema.sql` statements are all `IF NOT EXISTS`, so running the DDL on a database at the current schema changes nothing (verified: all DDL statements are guarded).
- The assertion existed only to guard the migration call (its message says "when applying migrations").

## Design decisions
- Keep the inline try/except instead of switching to `_execute_schema_ddl`, preserving the existing log text and keeping the diff minimal.

## Alternatives considered
- Reusing `_execute_schema_ddl(db, sql, "Event Bus")`: equivalent log text, but it changes more lines and an existing note in the tests (DDL path intentionally uses its own inline handling); not needed for this Plan.

## Implementation
### Target file
`scripts/db/create_schema.py`

### Procedure
1. Remove `apply_eventbus_migrations` from the `from db.schema_sql import (...)` block.
2. In `create_eventbus_schema()` delete the `assert db.conn is not None, ...`, the comment about migrations running before the DDL, and the `try: apply_eventbus_migrations(db.conn) ... raise` block.
3. Keep `db.executescript(build_eventbus_schema_sql())` in its existing try/except, then `db.commit()` and the success log.

### Method
- Re-read the function before editing: the workflow procedure edits the neighbouring function and the import block; apply sequentially.

### Details
- Docstring wording ("Create eventbus.sqlite tables ...") stays valid.

## Compatibility considerations
Output schema is identical for an empty path and for a database at the current schema; an older database is no longer converted before the DDL (recreate instead, per the baseline).

## Security considerations
N/A: no new input.

## Rollback considerations
Revert the commit; no persisted state changes.

## Validation plan
- `uv run pytest tests/db/test_create_schema.py tests/db/test_eventbus_schema_equivalence.py -q`.
- `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `uv run bandit scripts/db/create_schema.py`.

## Completion criteria
- `create_eventbus_schema()` has no reference to migrations and creates the three tables on an empty path with an unchanged schema on re-run.

## Out of Scope
- The workflow function and the other create functions.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the import, assertion, comment, and migration block | Done | 20261022-101015 | 20261022-101015 | `create_eventbus_schema()` is now DDL-only; removed `apply_eventbus_migrations` import and its try/except block. |
| 2 | Tests are covered by the test-file procedures | Done | 20261022-101015 | 20261022-101015 | `TestEventbusAckedAtMigration` removed by proc 07. |
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
- **Requirement ID**: `REQ-002` (DDL-only EventBus bootstrap)
- **Source issue**: `issues/20261021-102130_rmebmig_remove-the-eventbus.sqlite-schema-migrations.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261022-093935_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-101015
- **Related target files**: scripts/db/create_schema.py
