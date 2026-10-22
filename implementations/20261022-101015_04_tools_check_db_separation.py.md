## Goal
Make `_schema_ddl()` return the base EventBus DDL only, because the EventBus migration list no longer exists (REQ-004).

## Scope
- Remove the EventBus migration text from the EventBus entry of `_schema_ddl()`; the workflow entry is changed by a sibling procedure.

## Assumptions
- The EventBus migrations only add columns already in `schema.sql` or drop columns not in it, so auditing the base DDL covers the same table ownership.
- `tests/tools/test_check_db_separation.py` consumes only the returned dict.

## Design decisions
- Return `schema_sql.build_eventbus_schema_sql()` directly for `eventbus`; drop the `migrations_eventbus` variable and concatenation.

## Alternatives considered
N/A: single-expression change.

## Implementation
### Target file
`tools/check_db_separation.py`

### Procedure
1. Delete `migrations_eventbus = ...` in `_schema_ddl()`.
2. Change the `"eventbus"` value to `schema_sql.build_eventbus_schema_sql()`.
3. Update the docstring so it no longer says "migrations included" (after both removal Plans, no migrations exist).

### Method
- Re-read the function before editing: the workflow procedure edits the same function; apply sequentially.
- Follow `routing.md` "Adding a new tool" validation.

### Details
- If both removal Plans have landed, the `import db.schema_sql as schema_sql` remains in use through the builders.

## Compatibility considerations
The checker's verdicts on the live repository must not change.

## Security considerations
N/A: read-only checker.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_db_separation.py`, `uv run pytest tests/tools/test_check_db_separation.py -q`.
- `uv run ruff format`/`check`, `uv run mypy tools/check_db_separation.py`, `uv run bandit tools/check_db_separation.py`, `uv run python tools/check_tool_descriptions_sync.py`.

## Completion criteria
- The tool does not reference `_EVENTBUS_MIGRATIONS` and passes on the live repository.

## Out of Scope
- The workflow entry and the checks themselves.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the EventBus migration text from `_schema_ddl()` | Pending | — | — | |
| 2 | Run the tool's tests | Pending | — | — | |
| 3 | Run the tool validation sequence per `routing.md` | Pending | — | — | |

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
- **Requirement ID**: `REQ-004` (audit the base EventBus DDL only)
- **Source issue**: `issues/20261021-102130_rmebmig_remove-the-eventbus.sqlite-schema-migrations.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261022-093935_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-101015
- **Related target files**: tools/check_db_separation.py
