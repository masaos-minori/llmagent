# Event bus reconnect drops missed events

## Priority
Low

## Summary
`EventBusSubscriber.subscribe()` generates a fresh `consumer_id` on every initial connection and every reconnect attempt, with no tracking of the last-seen sequence number. The broker creates a brand-new, empty in-memory queue per `consumer_id` with no persisted offset or replay, so any event published during a disconnect window is permanently lost on reconnect. This code is not currently wired into production REPL operation, so operational impact today is nil, but it should be fixed before it is wired in.

## Background
Found during an adversarial code review (`python-code-review` skill) of the REPL's session/lifecycle subsystem (`scripts/agent/eventbus_subscriber.py`, `scripts/eventbus/broker.py`) and re-verified against the current code. `EventBusClient`, `EventBusSubscriber` and `EventBusTopicAdminClient` are instantiated only in tests today. A fresh `consumer_id` per attempt is deliberate (the module docstring documents it): the broker raises `ConsumerAlreadyConnectedError` for a duplicate `consumer_id` (pairwise-consumer authorization, archived ebauth001), so a resume feature must not reuse a `consumer_id` while the old connection is still registered. The fix is a design change on the broker (a durable or ring buffer), not a small subscriber change; consider treating it as a feature request. `origin/master` adds eventbus manifests and an API reference doc kept in sync by drift gates, so a broker API change must update them.

## Problem
`scripts/agent/eventbus_subscriber.py::EventBusSubscriber.subscribe()` generates `consumer_id = uuid.uuid4().hex` on every initial connection and every reconnect attempt, with no tracking of the last-seen `seq`/resume parameter passed to the new connection. `scripts/eventbus/broker.py::EventBroker.subscribe()` creates a brand-new, empty `asyncio.Queue` per `consumer_id` with no persisted offset or replay of missed events — it is a pure in-memory pub/sub. Any event published between a disconnect and the next successful reconnect is therefore never delivered to that fresh subscription; a clean reconnect looks identical to a gap-free one, with no error surfaced to the consumer. The subscriber's bounded 5-attempt/1-second-delay reconnect retry budget is itself fine (not unbounded) — the gap is specifically the loss of in-flight events across a successful reconnect.

## Reason for Change
If/when this subscriber is wired into the live agent, a transient network blip (well within the bounded retry budget) would cause silent, permanent loss of every event published during the outage. This matters for event types the agent relies on for correctness (e.g. approval/workflow-state notifications), not just best-effort telemetry.

## Implementation Intent
Before wiring this subscriber into production, add seq-based resume — either a durable per-consumer offset in the broker, or client-side buffering/replay via a `Last-Event-ID`-style resume parameter — so a reconnect continues from the last successfully processed `seq` rather than starting a brand-new, empty subscription.

## Target Files or Areas
- `scripts/agent/eventbus_subscriber.py` (`EventBusSubscriber.subscribe()`)
- `scripts/eventbus/broker.py` (`EventBroker.subscribe()`)

## Required Changes
- Track the last successfully processed `seq` in `EventBusSubscriber` across reconnects.
- Add a resume parameter to `EventBroker.subscribe()` (or an equivalent durable-offset mechanism) so a reconnect can request events since the last-seen `seq`, without reusing a `consumer_id` that is still registered.
- Add a test simulating a disconnect-then-reconnect with an event published during the gap, asserting the reconnected subscriber receives it.

## Constraints
- Do not change the existing bounded 5-attempt/1-second-delay retry budget.
- This is a pre-production-wiring fix — do not wire `EventBusSubscriber` into `factory.py`/`startup*.py` as part of this issue; that is a separate, future task.

## Acceptance Criteria
- A reconnecting subscriber receives events published during the disconnect window, up to whatever durability/buffering bound is chosen.
- The existing reconnect retry behavior (attempt count, delay) is unchanged.

## Testing Expectations
Unit test simulating a disconnect/reconnect cycle with an event published mid-gap, asserting no event loss. Run `tests/agent/test_eventbus_subscriber.py` and relevant `scripts/eventbus` broker tests after the change.

## Documentation Impact
A broker API change must update `registry/manifests/eventbus_api.yaml` and the eventbus API reference doc (present on `origin/master`) to keep the manifest and doc drift gates green. State in `docs/` that reconnect preserves delivery via seq-based resume only once implemented.

## Out of Scope
- Actually wiring `EventBusSubscriber` into production REPL startup (separate future task, not part of this fix).
- `EventBusTopicAdminClient`'s own behavior (not reviewed as part of this finding).

## Dependencies
N/A: none.

## Unresolved Questions
N/A: none for the mechanism itself — confirmed by reading `subscribe()` in both `eventbus_subscriber.py` and `broker.py`, and by confirming via `grep` that no production call site currently wires this subscriber in.

## AI Implementation Instruction
Implement seq-based resume at the broker and/or subscriber level; do not attempt to wire the subscriber into production as part of this fix. Add the disconnect/reconnect regression test described above before considering this done.

## Traceability
- **Workflow phase**: python-code-review -> issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261003-180343
- **Related target files**: scripts/agent/eventbus_subscriber.py, scripts/eventbus/broker.py
