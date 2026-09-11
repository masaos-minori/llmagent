# Add matching columns to `_EVENTBUS_SCHEMA` in `scripts/db/schema_sql.py`

## Goal

Add `cycle_failure_count INTEGER NOT NULL DEFAULT 0` and `redelivered_from TEXT` columns to the `_EVENTBUS_SCHEMA` string literal in `scripts/db/schema_sql.py`. This DDL source is used by `create_eventbus_schema()`'s separate bootstrap path and must mirror `schema.sql`'s `events` definition exactly.

## Scope

- Modify `scripts/db/schema_sql.py`: add the two new columns to the `_EVENTBUS_SCHEMA` string literal's `events` table definition.

## Assumptions

- The two DDL sources (`schema.sql` and `_EVENTBUS_SCHEMA`) must remain identical after this change.
- Column order within the `CREATE TABLE` should match `schema.sql` for readability and diff clarity.

## Design decisions

- Columns are inserted after `dlq_at` to match the column ordering in `schema.sql`.
- `cycle_failure_count` uses `INTEGER NOT NULL DEFAULT 0` per REQ-001.
- `redelivered_from` uses `TEXT` type (nullable).

## Alternatives considered

- None — this is a straightforward mirroring of `schema.sql` changes.

## Compatibility considerations

- Same as REQ-001: pre-existing databases receive columns via `_migrate()`; new databases get them from DDL.
- `create_eventbus_schema()`'s bootstrap path now includes the same columns as `_init_schema()`.

## Security considerations

- No new security surface.

## Rollback considerations

- Reverting means removing the columns from `_EVENTBUS_SCHEMA` only, keeping `schema.sql` unchanged.

## Validation plan

- Run `uv run pytest tests/db/test_create_schema.py -v` to confirm `create_eventbus_schema()` includes both new columns.
- Compare the `events` table definition in `_EVENTBUS_SCHEMA` against `schema.sql` to verify identity.

## Completion criteria

- `_EVENTBUS_SCHEMA` contains `cycle_failure_count INTEGER NOT NULL DEFAULT 0` and `redelivered_from TEXT`.
- Both DDL sources remain identical after the change.
- Tests pass confirming the new columns are present.

## Out of scope

- Migration logic (REQ-002).
- Indexes on the new columns.
- `DlqEventRecord` field updates.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add matching columns to _EVENTBUS_SCHEMA | Completed | — | — | Already implemented in previous cycle |

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
- **Requirement ID**: REQ-001
- **Source issue**: issues/20260907-125042_eb_h03_dlq_requeue_real_redelivery.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260909-100315_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260910-233401
- **Related target files**: scripts/db/schema_sql.py
