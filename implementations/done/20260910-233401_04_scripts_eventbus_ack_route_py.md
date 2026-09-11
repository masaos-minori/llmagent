# Update `nack()`/`_nack_and_promote()` to consume `nack_event()`'s two-value return

## Goal

Update `scripts/eventbus/ack_route.py`'s `nack()` and `_nack_and_promote()` to handle `nack_event()`'s new two-value return `(delivery_failure_count, cycle_failure_count)`. Use the cycle count (`cycle_failure_count`) for the DLQ-promotion threshold decision (`>= cfg.max_retry`) while preserving `delivery_failure_count` (the lifetime count) as the `"delivery_failure_count"` field in the `/nack` response body.

## Scope

- Modify `_nack_and_promote()`: unpack the two-value return from `nack_event()`, use `cycle_failure_count` for the promotion threshold check.
- Modify `nack()`: preserve `delivery_failure_count` in the response body (no change to the API contract for callers).

## Assumptions

- `_nack_and_promote()` currently treats `nack_event()`'s return as a single `int` used both for the threshold check and the response's `"delivery_failure_count"` field (confirmed by direct read).
- The API response contract must remain unchanged for external callers: `"delivery_failure_count"` still refers to the lifetime count.

## Design decisions

- Unpack as `failure_count, cycle_count = _nack_event(db, event_id)` in `_nack_and_promote()`.
- Use `cycle_count >= cfg.max_retry` for the DLQ promotion threshold.
- Keep `failure_count` as the `"delivery_failure_count"` value in the response body.
- Preserve the `-1` sentinel for not-found events.

## Alternatives considered

- Renaming the response field to `"cycle_failure_count"`: rejected because the Plan scope explicitly states the existing API response contract's meaning must not change for callers.
- Adding a new response field alongside `"delivery_failure_count"`: rejected because the Plan scope limits changes to consuming the two-value return without adding new API surface.

## Compatibility considerations

- The API response body retains the same `"delivery_failure_count"` field name and semantics (lifetime count).
- The DLQ promotion threshold now uses `cycle_failure_count` instead of `delivery_failure_count`, which is an internal behavioral change only.
- Pre-existing callers relying on `"delivery_failure_count"` in the response body see no change.

## Security considerations

- No new security surface. Both counts are integer values derived from SQLite queries.

## Rollback considerations

- Reverting means restoring the single-int return consumption and the original threshold check against `delivery_failure_count`.

## Validation plan

- Run `uv run pytest tests/eventbus/test_eventbus_dlq.py tests/eventbus/test_eventbus_dlq_promotion.py -v` to confirm:
  - `/nack` responses include correct `"delivery_failure_count"` (lifetime count).
  - DLQ promotion threshold uses `cycle_failure_count`.
  - `test_dlq_requeue_increments_dlq_requeue_count_not_delivery_failure_count` passes with updated assertions.

## Completion criteria

- `_nack_and_promote()` unpacks `nack_event()`'s two-value return.
- DLQ promotion threshold checks `cycle_count >= cfg.max_retry`.
- Response body includes `"delivery_failure_count"` with the lifetime count value.
- Tests pass confirming the updated behavior.

## Out of scope

- Changes to `nack_event()` itself (handled separately in REQ-003).
- Changes to `dlq_route.py`'s requeue handler (handled separately in REQ-006).
- DLQ JSON file archival (handled separately in REQ-007).
- Promotion predicate switch in `dlq.py` (handled separately in REQ-008).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update _nack_and_promote() to consume two-value return | Completed | — | — | |
| 2 | Preserve delivery_failure_count in /nack response body | Completed | — | — | No change needed |

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
- **Requirement ID**: REQ-004
- **Source issue**: issues/20260907-125042_eb_h03_dlq_requeue_real_redelivery.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260909-100315_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260910-233401
- **Related target files**: scripts/eventbus/ack_route.py
