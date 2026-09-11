# Add `archive_dlq_record()`; switch promotion predicates to `cycle_failure_count`

## Goal

Two changes to `scripts/eventbus/dlq.py`:
1. Add `archive_dlq_record()` function that moves `{deadletter_dir}/{event_id}.json` to `{deadletter_dir}/requeued/{event_id}_{timestamp}.json` (an additive subdirectory of the existing `deadletter_dir` config value).
2. Switch `promote_single()`, `sweep_orphans()`, and `promote_to_dlq()`'s SQL predicate from `delivery_failure_count >= ?` to `cycle_failure_count >= ?`.

## Scope

- Add `archive_dlq_record(deadletter_dir, event_id)`: move DLQ JSON file to `requeued/` subdirectory.
- Modify `promote_to_dlq()`: change SQL predicate to `cycle_failure_count >= ?`.
- Modify `sweep_orphans()`: change SQL predicate to `cycle_failure_count >= ?`.
- Modify `promote_single()`: change SQL predicate to `cycle_failure_count >= ?`.

## Assumptions

- `_atomic_write()` writes `{deadletter_dir}/{event_id}.json` with no corresponding archive/reconcile function (confirmed by direct read).
- All three promotion functions query `delivery_failure_count >= ?` today (confirmed by direct read).
- No new configuration key is introduced — `requeued/` is a subdirectory of the existing `deadletter_dir` value.

## Design decisions

- `archive_dlq_record()`: create `requeued/` subdirectory if not exists, use `os.replace()` for atomic move, append timestamp suffix to avoid collisions.
- The `DlqEventRecord` dataclass does not need modification — the archived file represents the DLQ state at promotion time, not the redelivered state.
- The three promotion functions' SQL predicates are changed uniformly: `delivery_failure_count >= ?` → `cycle_failure_count >= ?`.
- The parameter name in the function signatures remains `max_retry` (it now gates on cycle count, not lifetime count).

## Alternatives considered

- Deleting the DLQ JSON file instead of archiving: rejected because the Plan requires preserving the audit trail of "this event was once in the DLQ."
- Adding a new `requeued_deadletter_dir` config key: rejected because the Plan scope limits to the existing `deadletter_dir` value.

## Compatibility considerations

- Pre-existing DLQ events in the JSON file remain until they are explicitly redelivered (the old flag-only requeue did not remove them either).
- After redelivery, the original `{event_id}.json` is moved to `requeued/{event_id}_{timestamp}.json` — the DLQ JSON file no longer exists at its original path.
- The promotion predicate change means events promoted to DLQ under the old lifetime-count threshold will NOT be re-promoted after redelivery (correct behavior — the retry budget resets).

## Security considerations

- `os.replace()` is used for atomic file operations, preventing partial writes.
- Timestamp suffix prevents filename collisions when multiple events are redelivered.

## Rollback considerations

- Reverting the predicate change restores the lifetime-count-based DLQ promotion.
- Removing `archive_dlq_record()` leaves DLQ JSON files orphaned after redelivery.

## Validation plan

- Run `uv run pytest tests/eventbus/test_eventbus_requeue_edge_cases.py tests/eventbus/test_eventbus_dlq_promotion.py -v` to confirm:
  - DLQ JSON file is archived to `requeued/` subdirectory.
  - Promotion keys on `cycle_failure_count`.
  - `test_dlq_requeue_increments_dlq_requeue_count_not_delivery_failure_count` passes with updated assertions.

## Completion criteria

- `archive_dlq_record()` exists and moves `{event_id}.json` to `requeued/{event_id}_{timestamp}.json`.
- All three promotion functions use `cycle_failure_count >= ?` predicate.
- Tests pass confirming the new behavior.

## Out of scope

- Changes to `nack_event()` return type (handled separately in REQ-003).
- Changes to `ack_route.py` consumer (handled separately in REQ-004).
- Changes to `dlq_route.py` call site (handled separately in REQ-006).
- Documentation update (handled separately in REQ-009).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add archive_dlq_record() function | Completed | — | — | |
| 2 | Switch promote_to_dlq() predicate to cycle_failure_count | Completed | — | — | |
| 3 | Switch sweep_orphans() predicate to cycle_failure_count | Completed | — | — | |
| 4 | Switch promote_single() predicate to cycle_failure_count | Completed | — | — | |

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
- **Requirement ID**: REQ-007, REQ-008
- **Source issue**: issues/20260907-125042_eb_h03_dlq_requeue_real_redelivery.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260909-100315_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260910-233401
- **Related target files**: scripts/eventbus/dlq.py
