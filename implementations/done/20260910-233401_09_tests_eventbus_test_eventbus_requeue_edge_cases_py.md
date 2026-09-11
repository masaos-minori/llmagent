# Update requeue edge-case tests for actual redelivery reachability and DLQ-file archival

## Goal

Update `tests/eventbus/test_eventbus_requeue_edge_cases.py` to assert actual redelivery reachability (new `seq`, new UUID `event_id`, `redelivered_from` set) and DLQ-file archival, not only `dlq_requeue_count`.

## Scope

- Modify `test_repeated_requeue_increments_dlq_requeue_count`: update to assert new-row properties after redelivery.
- Modify `test_requeue_event_at_max_retry_then_re_promoted`: update to account for the cycle-count-based retry budget.

## Assumptions

- `test_repeated_requeue_increments_dlq_requeue_count`/`test_requeue_event_at_max_retry_then_re_promoted` currently assert only the DB flag/count change (confirmed by direct read).
- The new `redeliver_event()` function inserts a new row with fresh UUID v4 `event_id`.

## Design decisions

- After calling `redeliver_event()`, query the database directly to verify:
  1. A new row exists with a different `event_id` from the original.
  2. `redelivered_from` points to the original `event_id`.
  3. `cycle_failure_count` is 0 on the new row.
  4. `delivery_failure_count` on the new row equals the original row's value.
  5. The original row's `dlq_requeue_count` incremented.
  6. The original DLQ JSON file was moved to `requeued/` subdirectory.
- For the max-retry test: after redelivery, the event should NOT be immediately re-promoted because `cycle_failure_count` resets to 0.

## Alternatives considered

- Adding new test functions instead of modifying existing ones: rejected because the existing tests already exercise the right scenarios, just with outdated assertions.
- Using mock objects for DLQ file verification: rejected because direct filesystem inspection is more reliable for this check.

## Compatibility considerations

- These are unit tests — no external API contract impact.
- The tests must be updated simultaneously with the implementation changes.

## Security considerations

- No security surface change.

## Rollback considerations

- Reverting means restoring the old flag-only assertions.

## Validation plan

- Run `uv run pytest tests/eventbus/test_eventbus_requeue_edge_cases.py -v` to confirm:
  - Redelivery produces a new `seq`/UUID `event_id`/`redelivered_from`.
  - DLQ JSON file is archived.
  - Cycle count resets on redelivery.

## Completion criteria

- Tests assert new-row existence with correct lineage fields.
- Tests assert DLQ JSON file archival to `requeued/` subdirectory.
- Tests assert cycle count reset on redelivery.
- Tests pass.

## Out of scope

- Changes to `redeliver_event()` itself (handled separately in REQ-005).
- Changes to `dlq_route.py` call site (handled separately in REQ-006).
- Promotion predicate switch (handled separately in REQ-008).

## execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update test_repeated_requeue_increments_dlq_requeue_count | Pending | — | — | |
| 2 | Update test_requeue_event_at_max_retry_then_re_promoted | Pending | — | — | |

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
- **Requirement ID**: REQ-005, REQ-006, REQ-007
- **Source issue**: issues/20260907-125042_eb_h03_dlq_requeue_real_redelivery.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260909-100315_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260910-233401
- **Related target files**: tests/eventbus/test_eventbus_requeue_edge_cases.py
