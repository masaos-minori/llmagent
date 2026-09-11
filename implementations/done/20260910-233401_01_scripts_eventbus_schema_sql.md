# Add `cycle_failure_count` and `redelivered_from` columns to the `events` table in both DDL sources

## Goal

Add two new columns (`cycle_failure_count INTEGER NOT NULL DEFAULT 0`, `redelivered_from TEXT`) to the `events` table definition in both DDL sources: `scripts/eventbus/schema.sql` (live-service bootstrap via `_init_schema()`) and `scripts/db/schema_sql.py` (`_EVENTBUS_SCHEMA` used by `create_eventbus_schema()`). Both currently define an identical `events` table with `delivery_failure_count`, `dlq_requeue_count`, `dlq_at` only — no lineage column exists today.

## Scope

- Modify `scripts/eventbus/schema.sql`: add `cycle_failure_count` and `redelivered_from` columns to the `CREATE TABLE IF NOT EXISTS events (...)` statement.
- Modify `scripts/db/schema_sql.py`: add matching columns to the `_EVENTBUS_SCHEMA` string literal.
- Both changes must be additive and consistent — the two DDL sources must remain identical after this change.

## Assumptions

- The new columns follow the existing naming convention (snake_case, uppercase SQL types).
- `cycle_failure_count` uses `INTEGER NOT NULL DEFAULT 0` per REQ-001 specification.
- `redelivered_from` uses `TEXT` type (nullable, as it will be NULL for original rows).
- No new indexes are needed on these columns at this time.

## Design decisions

- Both columns are added to the `events` table definition in both DDL sources simultaneously to maintain consistency between the two bootstrap paths.
- `cycle_failure_count` defaults to `0` because a redelivered event starts with a fresh retry budget.
- `redelivered_from` is nullable because original (non-redelivered) events do not have a parent event.

## Alternatives considered

- Adding `redelivered_from` as a foreign key constraint: rejected because SQLite does not enforce foreign keys by default and the column is used for audit lineage, not referential integrity.
- Using a separate `redelivery_history` table: rejected because the Plan scope limits changes to the `events` table; a separate table would require additional DDL and migration logic outside this row's scope.

## Compatibility considerations

- Pre-existing databases that already have the `events` table but lack these columns will receive them via the migration path (`_migrate()`), which catches duplicate-column errors.
- New databases bootstrapped from either DDL source will include the columns from creation.
- The `fetch_dlq()` query in `db.py` selects specific columns and does not use `SELECT *`, so adding columns does not affect its output shape.

## Security considerations

- No new security surface introduced. `redelivered_from` stores a UUID string, not user input.
- `cycle_failure_count` is an integer counter, not influenced by external data.

## Rollback considerations

- Removing the columns requires dropping them via `ALTER TABLE DROP COLUMN`, which SQLite supports only if no other constraints depend on them.
- If the migration fails, the existing DLQ promotion logic continues to operate on the lifetime count only (the pre-change behavior).

## Validation plan

- Run `uv run pytest tests/db/test_create_schema.py -v` to confirm `create_eventbus_schema()` includes both new columns.
- Verify both DDL sources produce identical schema output by comparing their `CREATE TABLE events` statements.

## Completion criteria

- `scripts/eventbus/schema.sql` contains `cycle_failure_count INTEGER NOT NULL DEFAULT 0` and `redelivered_from TEXT` in the `events` table definition.
- `scripts/db/schema_sql.py`'s `_EVENTBUS_SCHEMA` contains matching column definitions.
- Both DDL sources remain identical after the change.
- Tests pass confirming both bootstrap paths include the new columns.

## Out of scope

- Migration logic for the new columns (handled separately in REQ-002).
- Indexes on the new columns (deferred to future work).
- Changes to `DlqEventRecord` dataclass fields (handled separately in REQ-007).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add cycle_failure_count/redelivered_from columns to schema.sql | Completed | — | — | |
| 2 | Add matching columns to _EVENTBUS_SCHEMA in schema_sql.py | Completed | — | — | |

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
- **Related target files**: scripts/eventbus/schema.sql
