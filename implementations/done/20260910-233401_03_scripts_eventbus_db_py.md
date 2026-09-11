# Extend `_migrate()`, update `nack_event()`, and add `redeliver_event()` in `scripts/eventbus/db.py`

## Goal

Three changes to `scripts/eventbus/db.py`:
1. Extend `_migrate()` to add `cycle_failure_count` and `redelivered_from` columns using the existing ALTER-TABLE/catch-duplicate-column-error pattern.
2. Change `nack_event()` to increment both `delivery_failure_count` (lifetime) and `cycle_failure_count` (cycle-scoped), and return both values (breaking its current `-> int` single-value return).
3. Add `redeliver_event()` function that performs conditional-update guard + new-row insert with lineage and a fresh UUID v4 `event_id`.

## Scope

- Modify `_migrate()`: add two new column migrations following the existing pattern.
- Modify `nack_event()`: update SQL to increment both counters, return tuple `(delivery_failure_count, cycle_failure_count)` instead of single `int`.
- Add `redeliver_event()`: new function implementing REQ-005.

## Assumptions

- `_migrate()`'s existing pattern of catching `sqlite3.OperationalError` with "duplicate column name" applies to the new columns.
- `nack_event()`'s callers are limited to `ack_route.py`'s `_nack_and_promote()` and unit tests (confirmed by `rg "nack_event"` across `scripts/` and `tests/`).
- `redeliver_event()` follows the same conditional-update guard pattern as `requeue_event()`: `WHERE event_id = ? AND dlq_at IS NOT NULL`.

## Design decisions

- `nack_event()` returns `tuple[int, int]` (lifetime count, cycle count) or `-1` for not-found. The `-1` sentinel is preserved for backward compatibility with callers checking for errors.
- `redeliver_event()` generates a UUID v4 `event_id` using `uuid.uuid4().hex` to satisfy `schemas/event_envelope.json`'s strict UUID v4 pattern constraint.
- `redeliver_event()` copies the original row's `delivery_failure_count` forward for lifetime continuity.
- `redeliver_event()` sets `cycle_failure_count = 0` on the new row (fresh retry budget).
- `redeliver_event()` sets `redelivered_from` to the original `event_id`.
- `redeliver_event()` increments `dlq_requeue_count` on the original row as audit trail.

## Alternatives considered

- Returning a named tuple from `nack_event()`: rejected because the breaking change already requires updating all callers; a simple positional tuple is sufficient and avoids import changes.
- Using `INSERT OR REPLACE` for redelivery: rejected because it would delete the original row, losing audit history. A new row preserves lineage.

## Compatibility considerations

- `nack_event()`'s signature change breaks all callers — `ack_route.py`'s `_nack_and_promote()` and unit tests must be updated simultaneously.
- `fetch_dlq()` does not select the new columns, so DLQ list output shape is unaffected.
- `requeue_event()` remains unchanged; `redeliver_event()` is a new function that replaces it in the requeue flow.

## Security considerations

- `uuid.uuid4().hex` produces cryptographically random UUIDs suitable for `event_id`.
- No user input flows into the new `redelivered_from` column value.

## Rollback considerations

- Reverting `nack_event()` means restoring the single-return `int` and the original SQL.
- Removing `redeliver_event()` leaves the old flag-only requeue behavior intact.

## Validation plan

- Run `uv run pytest tests/eventbus/test_eventbus_ack_nack.py tests/eventbus/test_eventbus_requeue_edge_cases.py tests/eventbus/test_eventbus_db_migration.py -v` to confirm:
  - `nack_event()` returns both counts correctly.
  - `redeliver_event()` inserts a new row with lineage.
  - `_migrate()` adds both new columns to a pre-migration schema.

## Completion criteria

- `_migrate()` adds `cycle_failure_count` and `redelivered_from` columns via ALTER TABLE.
- `nack_event()` increments and returns both `(delivery_failure_count, cycle_failure_count)`.
- `redeliver_event()` exists and performs conditional-update guard + new-row insert with fresh UUID v4 `event_id`, `redelivered_from`, `cycle_failure_count=0`, and copied `delivery_failure_count`.
- All affected tests pass.

## Out of scope

- Changes to `ack_route.py`'s consumer of `nack_event()`'s return (handled separately in REQ-004).
- Changes to `dlq_route.py`'s call site (handled separately in REQ-006).
- DLQ JSON file archival (handled separately in REQ-007).
- Promotion predicate switch (handled separately in REQ-008).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Extend _migrate() for new columns | Completed | — | — | |
| 2 | Update nack_event() to increment and return both counts | Completed | — | — | |
| 3 | Add redeliver_event() function | Completed | — | — | |

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
- **Requirement ID**: REQ-002, REQ-003, REQ-005
- **Source issue**: issues/20260907-125042_eb_h03_dlq_requeue_real_redelivery.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260909-100315_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260910-233401
- **Related target files**: scripts/eventbus/db.py
