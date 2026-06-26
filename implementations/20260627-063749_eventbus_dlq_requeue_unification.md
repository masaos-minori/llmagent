## Goal

Unify the DLQ requeue endpoint path and fix documentation inconsistencies between the HTTP API doc and the DLQ semantics doc regarding `retry_count` vs `delivery_failure_count`.

## Scope

**In-Scope**:
- Confirm `POST /dlq/{event_id}/requeue` is the canonical requeue endpoint (already done in app.py line 334)
- Fix docs that incorrectly reference `retry_count` — code actually uses `delivery_failure_count` for DLQ promotion and `dlq_requeue_count` for requeue tracking
- Document edge cases: unknown event_id, event not in DLQ, event already at/above max_retry, repeated requeue
- Add tests for requeue path and retry_count/delivery_failure_count behavior

**Out-of-Scope**:
- Redesigning DLQ promotion criteria
- Adding automatic consumer failure tracking

## Assumptions

1. `retry_count` is deprecated (per schema.sql line 11) — all DLQ promotion uses `delivery_failure_count >= max_retry`
2. `dlq_requeue_count` tracks how many times an event has been requeued (incremented on each requeue, never reset)
3. The canonical endpoint is `POST /dlq/{event_id}/requeue` — no legacy alias exists in app.py

## Implementation

### Target file: docs/06_eventbus_02_http_api_and_runtime.md

**Procedure**: Fix HTTP API doc to reference correct field names.

**Method**: Modify the HTTP API and runtime documentation.

**Details**:
1. Update line 87: change "Increments `retry_count` by 1" to "Increments `dlq_requeue_count` by 1"
2. Add edge case documentation: event not currently in DLQ (404), repeated requeue (increments dlq_requeue_count each time)

### Target file: docs/06_eventbus_04_dlq_offsets_and_delivery_semantics.md

**Procedure**: Fix DLQ semantics doc to reference correct field names.

**Method**: Modify the DLQ semantics documentation.

**Details**:
1. Update line 16: change "increments `retry_count` by 1" to "increments `dlq_requeue_count` by 1"
2. Update line 7: change "retry_count >= max_retry" to "delivery_failure_count >= max_retry"

### Target file: tests/test_eventbus_requeue.py (new)

**Procedure**: Add requeue tests for edge cases.

**Method**: Create new test file with DLQ requeue edge case tests.

**Details**:
1. Test: POST /dlq/{event_id}/requeue for unknown event_id → 404
2. Test: POST /dlq/{event_id}/requeue for event not in DLQ → 404 (dlq_at IS NULL)
3. Test: POST /dlq/{event_id}/requeue for valid DLQ event → 200, dlq_requeue_count incremented, dlq_at cleared
4. Test: Repeated requeue of same event → dlq_requeue_count increments each time
5. Test: Requeue of event at delivery_failure_count >= max_retry → requeue succeeds but next DLQ loop tick will re-promote

### Target file: docs/06_eventbus_06_reference_api.md

**Procedure**: Update reference API docs with HTTP endpoint documentation.

**Method**: Add HTTP endpoint documentation for POST /dlq/{event_id}/requeue.

**Details**:
1. Add POST /dlq/{event_id}/requeue endpoint documentation

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| 06_eventbus_02_http_api_and_runtime.md | Verify DLQ requeue doc references correct fields | Check for dlq_requeue_count, delivery_failure_count terminology | Documentation matches runtime behavior |
| 06_eventbus_04_dlq_offsets_and_delivery_semantics.md | Verify DLQ promotion criteria uses correct field | Check for delivery_failure_count >= max_retry | Documentation matches schema.sql |
| tests/test_eventbus_requeue.py (new) | Verify requeue edge cases pass | Run pytest | All requeue tests pass |

## Risks

- **Risk**: Changing docs to reference `delivery_failure_count` instead of `retry_count` may break existing documentation that operators rely on | **Likelihood**: Low | **Mitigation**: Add a note about the deprecation in the HTTP API doc, referencing schema.sql line 11. This is a bug fix, not a breaking change — docs should match runtime behavior. | False
- **Risk**: Requeue of event not in DLQ should return 404 but current code doesn't check dlq_at status | **Likelihood**: Medium | **Mitigation**: Verify the current requeue_event() implementation in db.py (line 199-205) — it only checks if event exists, not if it's in DLQ. May need to add a check for dlq_at IS NOT NULL. | False
