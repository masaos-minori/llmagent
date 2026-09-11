# Update `test_requeue_increments_dlq_requeue_count` and its direct-SQL column assertions for the new row/lineage model

## Goal

Update `tests/eventbus/test_eventbus_dlq.py` to reflect the new row/lineage model: the requeue operation no longer modifies the original row's `dlq_at` flag — it inserts a new row with fresh UUID v4 `event_id`.

## Scope

- Modify `test_requeue_increments_dlq_requeue_count`: update direct-SQL column assertions for the new row/lineage model.
- Update raw SQL queries to verify the new row's properties instead of the original row's.

## Assumptions

- This test directly queries `dlq_requeue_count`/`delivery_failure_count`/`dlq_at` via raw SQL against the original `event_id`, which will no longer represent the live/redelivered row after this change (confirmed by reading test body).

## Design decisions

- After calling `redeliver_event()`:
  1. Query for the new row using `redelivered_from = <original_event_id>` instead of querying by the original `event_id`.
  2. Assert the new row has `cycle_failure_count = 0`.
  3. Assert the new row's `delivery_failure_count` equals the original row's value.
  4. Assert the original row's `dlq_requeue_count` incremented.
  5. Assert the original row's `dlq_at` remains set (it was not cleared — the flag-only behavior is gone).

## Alternatives considered

- Rewriting the test entirely: rejected because the existing test structure is valid; only the assertions need updating.

## Compatibility considerations

- These are unit tests — no external API contract impact.
- The tests must be updated simultaneously with the implementation changes.

## Security considerations

- No security surface change.

## Rollback considerations

- Reverting means restoring the old flag-based assertions.

## Validation plan

- Run `uv run pytest tests/eventbus/test_eventbus_dlq.py -v` to confirm:
  - Direct-SQL assertions match the new row/lineage model.
  - Original row's `dlq_at` is preserved.
  - New row has correct lineage fields.

## Completion criteria

- Test queries the new row via `redelivered_from` instead of the original `event_id`.
- Assertions confirm `cycle_failure_count = 0` on the new row.
- Assertions confirm `delivery_failure_count` carries forward from the original row.
- Tests pass.

## Out of scope

- Changes to `redeliver_event()` itself (handled separately in REQ-005).
- Changes to `dlq_route.py` call site (handled separately in REQ-006).

## execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update test_requeue_increments_dlq_requeue_count for new row model | Pending | — | — | |

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
- **Requirement ID**: REQ-004, REQ-005
- **Source issue**: issues/20260907-125042_eb_h03_dlq_requeue_real_redelivery.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260909-100315_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260910-233401
- **Related target files**: tests/eventbus/test_eventbus_dlq.py
