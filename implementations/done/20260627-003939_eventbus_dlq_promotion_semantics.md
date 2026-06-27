## Goal

Clarify DLQ promotion semantics and fix documentation inconsistencies regarding `retry_count` vs `delivery_failure_count` ownership and increment rules.

## Scope

**In-Scope**:
- Fix docs that reference `retry_count` for DLQ promotion — code actually uses `delivery_failure_count >= max_retry`
- Clarify what increments `delivery_failure_count`: nack API, not DLQ requeue
- Document the difference between unacked replay and DLQ promotion
- Add warning to requeue response when event will be re-promoted on next DLQ loop tick
- Update known issues if behavior remains surprising

**Out-of-Scope**:
- Implementing full consumer group failure tracking
- Exactly-once delivery

## Assumptions

1. `retry_count` is deprecated (per schema.sql line 11) — all DLQ promotion uses `delivery_failure_count >= max_retry`
2. `delivery_failure_count` is incremented on nack (app.py line 97), not on DLQ requeue
3. `dlq_requeue_count` is the field incremented on DLQ requeue (db.py line 202)

## Implementation

### Target file: docs/06_eventbus_04_dlq_offsets_and_delivery_semantics.md

**Procedure**: Fix DLQ promotion criteria documentation.

**Method**: Update all references to `retry_count` in DLQ context to use the correct field names.

**Details**:
1. Line 7: change "retry_count >= max_retry" to "delivery_failure_count >= max_retry"
2. Line 16: change "increments `retry_count` by 1" to "increments `dlq_requeue_count` by 1"; change "If the event's `retry_count` is already at or above `max_retry`" to "If the event's `delivery_failure_count` is already at or above `max_retry`"
3. Line 55: change "retry_count >= max_retry" to "delivery_failure_count >= max_retry"

### Target file: docs/06_eventbus_03_persistence_schema_and_replay.md

**Procedure**: Fix field semantics documentation for DLQ promotion.

**Method**: Update the `retry_count` row in the field semantics table to clarify its deprecated status and correct the DLQ promotion reference.

**Details**:
1. Line 33: update "retry_count" row description — note it is deprecated per schema.sql line 11; change "threshold `max_retry` triggers DLQ promotion" to reference `delivery_failure_count` instead

### Target file: docs/06_eventbus_02_http_api_and_runtime.md

**Procedure**: Fix HTTP API documentation for DLQ requeue and promotion.

**Method**: Update references to use correct field names in both the DLQ section and the background loop description.

**Details**:
1. Line 81: change "retry_count" in DLQ list response to "delivery_failure_count"
2. Line 87: change "Increments `retry_count` by 1" to "Increments `dlq_requeue_count` by 1"; change "If `retry_count >= max_retry` after re-promotion logic runs" to "If `delivery_failure_count >= max_retry`"
3. Line 96: change "Events with `retry_count >= max_retry AND dlq_at IS NULL`" to "Events with `delivery_failure_count >= max_retry AND dlq_at IS NULL`"

### Target file: docs/06_eventbus_90_inconsistencies_and_known_issues.md

**Procedure**: Update known issues table for correctness.

**Method**: Update the `retry_count` row to reflect its deprecated status and clarify what actually triggers DLQ promotion.

**Details**:
1. Line 8: update "retry_count" row — note it is deprecated per schema.sql line 11; change "Not incremented during normal delivery" to clarify that DLQ promotion uses `delivery_failure_count`, not `retry_count`

### Target file: scripts/eventbus/app.py

**Procedure**: Add warning to DLQ requeue response when event will be re-promoted.

**Method**: Add an optional `"dlq_imminent": true` field in the requeue response when the event's `delivery_failure_count >= max_retry`.

**Details**:
1. In the dlq_requeue handler (around line 334-340), after incrementing `dlq_requeue_count`, check if `delivery_failure_count >= max_retry`
2. If true, add `"dlq_imminent": true` to the response body
3. This is backward-compatible — existing consumers ignore unknown fields

### Target file: tests/test_eventbus_dlq_promotion.py (new)

**Procedure**: Add tests for DLQ promotion edge cases.

**Method**: Create a new test file with specific tests for the DLQ promotion semantics clarified in this design.

**Details**:
1. Test: nack increments `delivery_failure_count` (not `retry_count`)
2. Test: DLQ promotion when `delivery_failure_count >= max_retry`
3. Test: Requeue of event at `delivery_failure_count >= max_retry` returns warning with `"dlq_imminent": true`
4. Test: DLQ requeue increments `dlq_requeue_count` but does NOT modify `delivery_failure_count`

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| 06_eventbus_04_dlq_offsets_and_delivery_semantics.md | Verify DLQ promotion criteria uses delivery_failure_count | Check for delivery_failure_count >= max_retry references | Documentation matches runtime behavior |
| 06_eventbus_03_persistence_schema_and_replay.md | Verify field documentation uses correct names | Check for delivery_failure_count terminology | Documentation matches schema.sql |
| tests/test_eventbus_dlq_promotion.py (new) | Verify DLQ promotion edge cases pass | Run pytest | All DLQ promotion tests pass |

## Risks

- **Risk**: Changing docs to reference `delivery_failure_count` instead of `retry_count` may break existing documentation that operators rely on | **Likelihood**: Low | **Mitigation**: This is a bug fix — docs should match runtime behavior. Add a note about the deprecation in the persistence schema doc, referencing schema.sql line 11. | False
- **Risk**: Adding warning to requeue response may change API contract for existing consumers | **Likelihood**: Medium | **Mitigation**: Add the warning as an optional field in the response (e.g., "dlq_imminent": true) rather than changing the existing response structure. This is backward-compatible. | True
