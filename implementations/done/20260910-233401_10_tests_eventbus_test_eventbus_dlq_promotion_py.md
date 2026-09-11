# Update DLQ promotion tests for cycle-count reset and promotion predicate switch

## Goal

Update `tests/eventbus/test_eventbus_dlq_promotion.py` to:
1. Add an assertion that `promote_single()`'s predicate now keys on `cycle_failure_count`.
2. Update `test_dlq_requeue_increments_dlq_requeue_count_not_delivery_failure_count` for the cycle-count reset behavior.

## Scope

- Modify `test_dlq_requeue_increments_dlq_requeue_count_not_delivery_failure_count`: add assertion that `cycle_failure_count` resets to 0 on redelivery.
- Add/update tests confirming `promote_single()` uses `cycle_failure_count >= ?` predicate.

## Assumptions

- This test currently asserts requeue leaves `delivery_failure_count` untouched — still true under the new design, but does not yet assert `cycle_failure_count`'s reset or the promotion predicate switch (confirmed by reading test body).

## Design decisions

- In `test_dlq_requeue_increments_dlq_requeue_count_not_delivery_failure_count`:
  - After redelivery, assert `cycle_failure_count = 0` on the new row.
  - Preserve the existing assertion that `delivery_failure_count` carries forward.
- Add a test case: after redelivery, the event should NOT be promoted to DLQ even if `delivery_failure_count >= cfg.max_retry`, because `cycle_failure_count` is 0.
- Verify `promote_single()` queries `cycle_failure_count >= ?` by checking that events with high `delivery_failure_count` but zero `cycle_failure_count` are not promoted.

## Alternatives considered

- Modifying the existing promotion tests directly: rejected because the Plan scope requires adding new assertions rather than replacing existing ones.

## Compatibility considerations

- These are unit tests — no external API contract impact.
- The tests must be updated simultaneously with the implementation changes.

## Security considerations

- No security surface change.

## Rollback considerations

- Reverting means restoring the old assertions without cycle-count checks.

## Validation plan

- Run `uv run pytest tests/eventbus/test_eventbus_dlq_promotion.py -v` to confirm:
  - Cycle count resets on redelivery.
  - Promotion predicate keys on `cycle_failure_count`.
  - Events with high lifetime count but zero cycle count are not promoted.

## Completion criteria

- `test_dlq_requeue_increments_dlq_requeue_count_not_delivery_failure_count` asserts `cycle_failure_count = 0` after redelivery.
- New/updated test confirms `promote_single()` uses `cycle_failure_count` predicate.
- Tests pass.

## Out of scope

- Changes to `nack_event()` return type (handled separately in REQ-003).
- Changes to `ack_route.py` consumer (handled separately in REQ-004).
- Changes to `redeliver_event()` itself (handled separately in REQ-005).

## execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update test_dlq_requeue_increments_dlq_requeue_count_not_delivery_failure_count | Pending | — | — | |
| 2 | Add promotion predicate assertion for cycle_failure_count | Pending | — | — | |

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
- **Requirement ID**: REQ-004, REQ-008
- **Source issue**: issues/20260907-125042_eb_h03_dlq_requeue_real_redelivery.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260909-100315_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260910-233401
- **Related target files**: tests/eventbus/test_eventbus_dlq_promotion.py
