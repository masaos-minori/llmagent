## Goal

Promote `POST /events/{event_id}/ack?consumer_id=...` to a fully documented and tested first-class API — define the ack endpoint contract, document error cases, and add tests for ack behavior.

## Scope

**In-Scope**:
- Define the ack endpoint: path, query parameters, response body, error cases
- Ack must update the consumer offset to the event's `seq`
- Return a clear error when `consumer_id` is missing, `event_id` does not exist, or `consumer_id` is invalid
- Document whether acking an older event may move offsets backwards; prefer monotonic offset advancement
- Add ack endpoint tests

**Out-of-Scope**:
- Batch ack
- Negative ack / nack (already exists as POST /nack)
- Exactly-once delivery guarantees

## Assumptions

1. Both `POST /ack` and `POST /events/{event_id}/ack` have the same behavior — the latter is the preferred canonical path
2. `consumer_id` is optional — if missing, ack succeeds but offset is not updated
3. Acker of an older event may move offsets backwards — need to decide if this should be prevented

## Implementation

### Target file: docs/06_eventbus_02_http_api_and_runtime.md

**Procedure**: Define and document the ack endpoint contract.

**Method**: Add POST /events/{event_id}/ack documentation to HTTP API docs.

**Details**:
1. Add POST /events/{event_id}/ack to HTTP API docs
2. Document path, query parameters, response body, error cases:
   - 400 for missing event_id
   - 404 for unknown event_id

### Target file: scripts/eventbus/offsets.py

**Procedure**: Clarify monotonic offset advancement.

**Method**: Decide whether acking an older event should be allowed or prevented.

**Details**:
1. Decide whether acking an older event should be allowed or prevented
2. If preventing: add monotonic check in write_offset or at the ack endpoint level
3. If allowing: document this behavior and its implications

### Target file: docs/06_eventbus_04_dlq_offsets_and_delivery_semantics.md

**Procedure**: Document consumer_id validation.

**Method**: Clarify that consumer_id is optional — ack succeeds even without it (offset not updated).

**Details**:
1. Document the offset update behavior when consumer_id is present
2. Clarify that consumer_id is optional — ack succeeds even without it

### Target file: tests/test_eventbus_ack_nack.py or new test file

**Procedure**: Add ack endpoint HTTP tests.

**Method**: Add new test cases for ack endpoint behavior.

**Details**:
1. Test: POST /events/{id}/ack with valid event_id and consumer_id → 200, offset written
2. Test: POST /events/{id}/ack without consumer_id → 200, ack succeeds but no offset update
3. Test: POST /events/{id}/ack for unknown event_id → 404
4. Test: POST /events/{id}/ack for already-acked event → 404

### Target file: docs/06_eventbus_06_reference_api.md

**Procedure**: Update reference API docs with HTTP endpoint documentation.

**Method**: Add HTTP endpoint documentation to reference API docs.

**Details**:
1. Add POST /events/{event_id}/ack endpoint documentation

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| 06_eventbus_02_http_api_and_runtime.md | Verify ack endpoint fully documented | Check for path, query params, response, errors | Complete ack endpoint documentation present |
| tests/test_eventbus_ack_nack.py or new file | Verify HTTP-level ack tests pass | Run pytest | All ack HTTP tests pass |
| scripts/eventbus/offsets.py | Verify monotonic offset enforcement (if added) | Check write_offset logic | Offsets never move backwards |

## Risks

- **Risk**: Adding monotonic offset enforcement may break existing consumers that ack out-of-order | **Likelihood**: Low-Medium | **Mitigation**: If monotonic enforcement is needed, make it configurable; document the behavior change clearly | False
- **Risk**: HTTP-level SSE streaming tests are hard to write due to blocking behavior | **Likelihood**: Medium | **Mitigation**: Use TestClient with direct HTTP calls (not SSE streaming) — ack endpoint is a simple POST, no streaming involved | False
