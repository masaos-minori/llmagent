# Add assertion that `create_eventbus_schema()` includes the two new columns

## Goal

Add an assertion to `tests/db/test_create_schema.py` that `create_eventbus_schema()` includes both `cycle_failure_count` and `redelivered_from` columns in the `events` table.

## Scope

- Extend the existing schema assertion in `test_create_schema.py` to include the two new columns.

## Assumptions

- No existing assertion checks these new columns; file already extended once for `eb_h01`'s new tables, per that Plan (confirmed by reading file).
- The `_table_names()`/column-assertion helper pattern used in this file can accommodate additional column assertions.

## Design decisions

- Add assertions that the `events` table returned by `create_eventbus_schema()` contains:
  1. `cycle_failure_count` column.
  2. `redelivered_from` column.
- Follow the existing pattern of asserting column names/types via the helper function.

## Alternatives considered

- Creating a new test function: rejected because the existing test is the canonical place for schema assertions.

## Compatibility considerations

- These are unit tests — no external API contract impact.
- The tests must be updated simultaneously with the DDL source changes.

## Security considerations

- No security surface change.

## Rollback considerations

- Reverting means removing the new column assertions.

## Validation plan

- Run `uv run pytest tests/db/test_create_schema.py -v` to confirm:
  - `create_eventbus_schema()` includes both new columns.
  - Pre-existing columns remain unchanged.

## Completion criteria

- Test asserts `cycle_failure_count` column exists in the schema.
- Test asserts `redelivered_from` column exists in the schema.
- Tests pass.

## Out of scope

- DDL source changes (handled separately in REQ-001).
- Migration logic (handled separately in REQ-002).
- Changes to `nack_event()` return type (handled separately in REQ-003).

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
- **Requirement ID**: REQ-001
- **Source issue**: issues/20260907-125042_eb_h03_dlq_requeue_real_redelivery.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260909-100315_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260910-233401
- **Related target files**: tests/db/test_create_schema.py
