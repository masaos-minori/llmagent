# Add assertions that `_migrate()` adds `cycle_failure_count`/`redelivered_from` to a pre-migration schema

## Goal

Add assertions to `tests/eventbus/test_eventbus_db_migration.py` that `_migrate()` adds `cycle_failure_count` and `redelivered_from` columns to a pre-migration schema.

## Scope

- Modify the migration test fixture and/or test function to verify both new columns are present after migration.

## Assumptions

- `pre_migration_conn` fixture and `test_migrate_adds_new_columns` currently check only the existing column set (confirmed by reading fixture and test body).
- The migration follows the existing ALTER-TABLE/catch-duplicate-column-error pattern.

## Design decisions

- Add assertions that after `_migrate(pre_migration_conn)`:
  1. `cycle_failure_count INTEGER NOT NULL DEFAULT 0` column exists.
  2. `redelivered_from TEXT` column exists.
- Use `PRAGMA table_info(events)` or query `sqlite_master` to verify column presence.

## Alternatives considered

- Adding a separate test function: rejected because the existing `test_migrate_adds_new_columns` is the natural place for these assertions.

## Compatibility considerations

- These are unit tests — no external API contract impact.
- The tests must be updated simultaneously with the migration logic changes.

## Security considerations

- No security surface change.

## Rollback considerations

- Reverting means removing the new column assertions.

## Validation plan

- Run `uv run pytest tests/eventbus/test_eventbus_db_migration.py -v` to confirm:
  - Migration adds both new columns to a pre-migration schema.
  - Pre-existing columns remain unchanged.

## Completion criteria

- Test asserts `cycle_failure_count` column exists after migration.
- Test asserts `redelivered_from` column exists after migration.
- Tests pass.

## Out of scope

- DDL source changes (handled separately in REQ-001).
- Changes to `nack_event()` return type (handled separately in REQ-003).
- Changes to `redeliver_event()` itself (handled separately in REQ-005).

## execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add assertion for cycle_failure_count column | Pending | — | — | |
| 2 | Add assertion for redelivered_from column | Pending | — | — | |

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
- **Requirement ID**: REQ-002
- **Source issue**: issues/20260907-125042_eb_h03_dlq_requeue_real_redelivery.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260909-100315_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260910-233401
- **Related target files**: tests/eventbus/test_eventbus_db_migration.py
