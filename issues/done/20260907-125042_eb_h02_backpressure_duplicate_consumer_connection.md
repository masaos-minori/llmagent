# Prevent delivery gaps caused by slow consumers and duplicate consumer connections

## Priority
High

## Summary
`scripts/eventbus/broker.py`'s `publish()` silently drops an event and logs a warning when a
subscriber's bounded queue is full, while leaving the SSE connection open — confirmed by direct
read, `EventBroker.publish()` has no path that disconnects or invalidates an overflowing
subscription. `EventBroker.subscribe()` also has no `consumer_id` parameter or tracking at all,
so nothing prevents two concurrent connections from sharing one `consumer_id` and racing on the
same offset/progress state.

## Background
Confirmed by direct read of `scripts/eventbus/broker.py` lines 43-61 (`publish`): on
`asyncio.QueueFull`, the code only calls `logger.warning(...)` and continues the loop — the
subscriber is never removed or notified, and the SSE generator in `subscribe_route.py` keeps
streaming from the same (now gapped) queue. `broker.py`'s `subscribe(self, topics: list[str])`
(line 30) and the `_Subscriber` dataclass (lines 15-20) carry no `consumer_id` field, so
`EventBroker` cannot detect or reject a duplicate active connection for the same consumer.

## Problem
- A consumer whose queue overflows continues receiving events after the gap with no signal
  that an event was dropped — its offset can later advance past the dropped event via a normal
  ACK, permanently losing it from that consumer's perspective, exactly as memo4.md describes.
- `tests/eventbus/test_eventbus_slow_consumer.py` (confirmed by direct read) only verifies that
  the queue has `maxsize=1000` and that the health endpoint's `slow_consumers` counter/503
  status reflects queue depth — it does not test that an overflowing subscription is
  disconnected, nor that a dropped event is ever surfaced to the consumer. The current tests
  pass under today's drop-and-continue behavior, so they do not catch this gap.
- No test or code path in `scripts/eventbus/subscribe_route.py`/`broker.py` tracks active
  `consumer_id`s across concurrent SSE connections — two processes could subscribe with the
  same `consumer_id` simultaneously with no rejection.

## Reason for Change
Make backpressure fail safely. A slow or duplicate consumer must never create an undetected
permanent gap. The server must either preserve ordered delivery or terminate the affected
subscription so the client can resume from its last committed position. Consumer identity must
have one explicit concurrency policy.

## Implementation Intent
Define the supported backpressure and consumer-connection policy first. On queue overflow,
disconnect or otherwise invalidate the affected subscription (e.g. close the SSE stream via the
sentinel-then-unsubscribe pattern `broker.py` already uses for shutdown) instead of silently
dropping an event and continuing. Track active consumer IDs in `EventBroker`/`subscribe_route.py`
and reject a second concurrent connection for the same non-empty `consumer_id` with HTTP 409,
unless a consumer-group model is deliberately chosen instead. Release registration on
cancellation, disconnect, generator failure, and shutdown — `subscribe_route.py`'s existing
`finally: broker.unsubscribe(sub)` (line 87) is the pattern to extend for consumer-ID release.

## Target Files or Areas
- `scripts/eventbus/broker.py`
- `scripts/eventbus/subscribe_route.py`
- `scripts/eventbus/ack_route.py`
- `scripts/eventbus/health_route.py`

## Required Changes
- Define the supported backpressure and consumer-connection policy.
- On queue overflow, disconnect or otherwise invalidate the affected subscription instead of
  silently dropping an event.
- Ensure reconnect resumes after the last committed consumer offset.
- Track active consumer IDs and reject a second active connection with HTTP 409 unless a
  consumer-group model is deliberately implemented.
- Release consumer registration on cancellation, network disconnect, generator failure, and
  server shutdown.
- Add observable overflow, disconnect, and duplicate-connection metrics and structured logs.
- If ACKs must be contiguous, reject an ACK that skips an undispatched or unacknowledged
  sequence.

## Constraints
- Keep unrelated behavior unchanged.
- Do not weaken fail-closed behavior, validation, or auditability.
- Do not mark this issue complete with documentation-only changes when runtime behavior is
  defective.
- Do not invent configuration values, migration history, or approval evidence.

## Acceptance Criteria
- [ ] Queue overflow cannot cause permanent event loss — the affected subscription is
      disconnected/invalidated instead of silently continuing.
- [ ] A slow consumer can reconnect and receive every event after its committed offset.
- [ ] Only one active connection is allowed per non-empty consumer ID under the selected
      policy.
- [ ] Cancellation and shutdown do not leak subscriber registrations.
- [ ] Tests cover queue overflow with an assertion that the subscription is actually
      terminated (not merely that `slow_consumers` is reported), reconnect, concurrent
      subscription attempts with the same `consumer_id`, and ACK after an induced gap.

## Testing Expectations
Update `tests/eventbus/test_eventbus_slow_consumer.py` to assert the overflowing subscription
is disconnected (not just that the queue/health metrics reflect depth); add a duplicate-
`consumer_id`-connection test. Run the complete EventBus test suite and the repository's
linting, type checking, and documentation consistency checks.

## Documentation Impact
Update the EventBus operations/delivery-semantics documentation to describe the chosen
backpressure and consumer-connection policy as the canonical specification.

## Out of Scope
- Transactional ACK/offset redesign (tracked separately in this batch).
- DLQ retry/requeue redesign (tracked separately in this batch).
- Capacity-limit/threshold configuration (tracked separately in this batch).

## Dependencies
N/A: none

## Unresolved Questions
Whether a consumer-group model (multiple concurrent connections sharing progress) should be
supported instead of the simpler one-connection-per-consumer-ID policy — default to rejecting
duplicates with 409 unless the implementer identifies a concrete need for consumer groups.

## AI Implementation Instruction
Confirm the chosen backpressure policy (disconnect-on-overflow vs. some other fail-safe) before
implementing — do not silently keep the current drop-and-continue behavior while only adding
metrics. `tests/eventbus/test_eventbus_slow_consumer.py`'s existing assertions about
`maxsize=1000` and `slow_consumer_count()` should continue to pass; extend rather than replace
them.
