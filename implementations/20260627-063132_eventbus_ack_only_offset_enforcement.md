## Goal

Enforce ack-only consumer offset advancement by removing any automatic offset write on disconnect — correct documentation that says `/subscribe` writes the current sequence to the offset file on disconnect, since runtime behavior already does not do this.

## Scope

**In-Scope**:
- Inspect `/subscribe` disconnect handling (already verified: no automatic offset write)
- Remove any automatic offset write on disconnect from docs (06_eventbus_02_http_api_and_runtime.md line 61)
- Ensure offsets are updated only by `POST /events/{event_id}/ack?consumer_id=...`
- Update HTTP API docs to remove "write offset on disconnect" behavior
- Add tests for reconnect behavior with and without ack

**Out-of-Scope**:
- Implementing exactly-once delivery
- Adding consumer-side deduplication beyond event_id semantics

## Assumptions

1. Runtime behavior already does NOT write offsets on disconnect — confirmed by app.py:305 (CancelledError handler only logs, no offset write)
2. Existing tests are correct — confirmed by test_eventbus_offsets.py (offsets written only via ack)
3. Only documentation needs correction for the disconnect offset claim

## Implementation

### Target file: docs/06_eventbus_02_http_api_and_runtime.md

**Procedure**: Remove automatic offset write on disconnect from docs, update reconnect semantics.

**Method**: Modify the HTTP API and runtime documentation.

**Details**:
1. Remove line 61 "On disconnect, the current `seq` is written to the offset file via `write_offset()`"
2. Update reconnect semantics section to clarify that offsets advance only via ack, not on disconnect
3. Add note about crash-before-ack causing replay of unacked event

### Target file: docs/06_eventbus_04_dlq_offsets_and_delivery_semantics.md

**Procedure**: Verify consistency with ack-only offset model.

**Method**: Cross-check all three Event Bus docs for disconnect offset claims.

**Details**:
1. Line 28: Already correct ("Offsets are never advanced automatically during streaming")
2. No changes needed if already consistent

### Target file: docs/06_eventbus_05_configuration_deploy_and_operations.md

**Procedure**: Verify consistency with ack-only offset model.

**Method**: Cross-check all three Event Bus docs for disconnect offset claims.

**Details**:
1. Line 25: Already notes offset_checkpoint_interval is deprecated/removed
2. No changes needed if already consistent

### Target file: tests/test_eventbus_offsets.py

**Procedure**: Add reconnect behavior tests.

**Method**: Add new test cases for reconnect with and without ack.

**Details**:
1. Test: receive event without ack, disconnect, reconnect → event is replayed
2. Test: ack event, disconnect, reconnect → replay starts after acked seq
3. Test: since_seq override behavior remains explicit and documented

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| 06_eventbus_02_http_api_and_runtime.md | Verify no disconnect offset write claim remains | Check subscribe section | Zero "write offset on disconnect" claims |
| All Event Bus docs | Verify no contradictory claims remain | Search for "disconnect.*offset" across docs | Zero contradictory claims |
| tests/test_eventbus_offsets.py | Verify new reconnect behavior tests pass | Run pytest | Tests pass, proving ack-only model |

## Risks

- **Risk**: Existing consumers may rely on disconnect checkpointing behavior documented in the wrong doc | **Likelihood**: Low (runtime doesn't do this) | **Mitigation**: If any consumer relies on this, document as Needs confirmation and assess migration path | False
- **Risk**: SSE streaming tests are hard to write due to blocking behavior | **Likelihood**: Medium | **Mitigation**: Use the same approach as test_eventbus_phase2 — patch write_offset and drive checkpoint counter manually using DB events | False
