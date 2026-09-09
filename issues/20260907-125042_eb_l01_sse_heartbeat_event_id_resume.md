# Add SSE heartbeat, event IDs, and standard resume behavior

## Priority
Low

## Summary
`scripts/eventbus/subscribe_route.py`'s SSE generator (`_sse_gen()`, lines 36-87) yields only
`f"data: {data}\n\n"` frames for both replayed and live events — confirmed by direct read,
there is no `id:` field, no comment-based heartbeat, and no read of the standard
`Last-Event-ID` header anywhere in the module. An idle subscription (no new events after replay
completes) sits on `await sub.queue.get()` (line 72) indefinitely with no periodic output.

## Background
Confirmed by direct read of `scripts/eventbus/subscribe_route.py`: the only client-facing
resume mechanism is the custom `since_seq`/`consumer_id` query-parameter pair (lines 20-34),
not the SSE-standard `Last-Event-ID` request header. `scripts/eventbus/replay_route.py`'s SSE
path (lines 57-63) has the same `data:`-only frame shape with no `id:` field.

## Problem
- After replay completes, an idle subscription can wait indefinitely without sending any data;
  intermediaries (proxies, load balancers) may time out and close such connections, and the
  client has no way to detect this short of its own transport-level timeout.
- SSE frames carry no `id:` field, so clients cannot rely on the standard `EventSource`
  auto-reconnect-with-`Last-Event-ID` behavior — they must implement custom reconnect logic
  around `since_seq`/`consumer_id` instead.

## Reason for Change
Improve interoperability and reconnect behavior without changing the event ordering contract.
Heartbeats should keep idle connections observable, and standard SSE event IDs should provide a
clear resume signal while preserving the existing consumer-offset mechanism.

## Implementation Intent
Add configurable SSE comment heartbeats (e.g. `: heartbeat\n\n` on an interval) emitted from the
same generator loop. Emit each event's `seq` as the SSE `id:` field alongside the existing
`data:` line. Read the `Last-Event-ID` request header as an additional resume-position input,
used only when neither an explicit `since_seq` nor a persisted consumer offset takes precedence
— define and document this precedence order explicitly rather than leaving it implicit.

## Target Files or Areas
- `scripts/eventbus/subscribe_route.py`
- `scripts/eventbus/replay_route.py`
- `scripts/eventbus/config.py`
- `docs/06_eventbus_06_reference-api.md`

## Required Changes
- Add configurable SSE comment heartbeats.
- Emit each event sequence as the SSE `id` field.
- Read `Last-Event-ID` when explicit `since_seq` and persisted consumer offset do not take
  precedence.
- Define and document precedence among `since_seq`, consumer offset, and `Last-Event-ID`.
- Ensure heartbeat tasks terminate on disconnect and shutdown (reuse the existing
  `finally: broker.unsubscribe(sub)` pattern in `subscribe_route.py` as the model for cleanup).

## Constraints
- Keep unrelated behavior unchanged.
- Do not weaken fail-closed behavior, validation, or auditability.
- Update the canonical ADR or EventBus specification when the delivery contract changes.
- Do not mark this issue complete with documentation-only changes when runtime behavior is
  defective.
- Do not invent configuration values, migration history, or approval evidence.

## Acceptance Criteria
- [ ] Idle subscriptions emit heartbeats at the configured interval.
- [ ] Heartbeat frames do not alter offsets or delivery state.
- [ ] Reconnect with `Last-Event-ID` resumes after that sequence according to the documented
      precedence.
- [ ] No task or subscriber registration leaks after disconnect.

## Testing Expectations
Add tests for heartbeat emission on an idle subscription, `id:` field presence on delivered
events, and precedence among `since_seq`/consumer offset/`Last-Event-ID`. Run the complete
EventBus test suite and the repository's linting, type checking, and documentation consistency
checks.

## Documentation Impact
Update `docs/06_eventbus_06_reference-api.md` to document heartbeat behavior, the `id:` field,
`Last-Event-ID` support, and the resume-precedence order as the canonical specification.

## Out of Scope
- Changing the underlying event ordering or offset-persistence mechanism (tracked separately
  in this batch as EB-H01).
- Backpressure/duplicate-connection handling (tracked separately in this batch as EB-H02).

## Dependencies
N/A: none

## Unresolved Questions
N/A: none

## AI Implementation Instruction
Keep the heartbeat as an SSE comment line (`:`-prefixed), not a `data:` event, so it does not
appear as a delivered event to `EventSource`-based clients. Do not change `replay_ceil`-based
duplicate-discard logic in `subscribe_route.py` when adding the `id:` field.

## Traceability
- **Workflow phase**: N/A: manually filed
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260907-125042
- **Related target files**: see Target Files or Areas above
