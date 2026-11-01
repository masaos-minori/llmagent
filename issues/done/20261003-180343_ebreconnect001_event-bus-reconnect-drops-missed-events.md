# Event bus reconnect drops missed events

## Priority
Low

## Summary
`EventBusSubscriber` does not track the last-seen `seq` and never sends `since_seq` (or `Last-Event-ID`) when it reconnects, and it uses a fresh random `consumer_id` per attempt. The event bus server already supports resume (`since_seq`, a persisted per-consumer offset and `Last-Event-ID`, replayed from the SQLite `events` table), so the gap is client-side: events published during a disconnect window are missed on reconnect although the server could replay them. A random `consumer_id` also cannot hold a pairwise authorization grant, so a real broker would reject the subscriber as written. The subscriber is not wired into production today, so operational impact is nil; fix it before it is wired in.

## Background
Found during an adversarial code review (`python-code-review` skill) of the REPL's session/lifecycle subsystem and corrected after a second verification against the current code. `EventBusClient`, `EventBusSubscriber` and `EventBusTopicAdminClient` are instantiated only in tests. Server side (`Explicit in code`): `GET /subscribe` in `scripts/eventbus/app.py` and `subscribe_route.py` accepts `since_seq`, resumes from a persisted per-consumer offset (`delivery_repo.get_resume_position`) and from `Last-Event-ID` (precedence: `since_seq`, then resume position, then `Last-Event-ID`), replays from the `events` table in batches and then switches to live delivery with de-duplication by seq. Only `EventBroker.subscribe` is a queue-only live layer. Authorization (`authorize_consumer_access` in `scripts/eventbus/auth.py`) requires an explicit `(consumer_id, topic)` grant and denies everything when no grant exists; the broker raises `ConsumerAlreadyConnectedError` (HTTP 409) for a `consumer_id` that is still registered. The recent authz-generation change does not alter these points.

## Problem
`scripts/agent/eventbus_subscriber.py::EventBusSubscriber.subscribe()` generates `consumer_id = uuid.uuid4().hex` per attempt. `_stream_once` sends only `consumer_id` and `topic`; it parses `seq` from the SSE `id:` line but never stores it and never passes `since_seq` or `Last-Event-ID`. A reconnect therefore starts a new subscription at the live edge, and events published during the gap are not delivered, with no error surfaced. The random `consumer_id` can never hold an authorization grant, so against a broker with authorization enabled the subscriber would receive 403. The bounded 5-attempt/1-second-delay retry budget is fine; the gap is the loss of events across a successful reconnect.

## Reason for Change
If/when this subscriber is wired into the live agent, a transient network blip (well within the bounded retry budget) would cause silent, permanent loss of every event published during the outage. This matters for event types the agent relies on for correctness (e.g. approval/workflow-state notifications), not just best-effort telemetry.

## Implementation Intent
Make the subscriber resume from the last processed `seq` and use a configured, stable `consumer_id`. No broker change is needed: the server-side resume already exists. The stable `consumer_id` must be paired with handling for HTTP 409 while the previous connection is still registered (retry with the same id after the old connection is released, or surface the conflict).

## Target Files or Areas
- `scripts/agent/eventbus_subscriber.py` (`EventBusSubscriber.subscribe()`, `_stream_once`)
- `EventBusSubscriberConfig` (new configured `consumer_id`)
- `scripts/eventbus/` and `registry/manifests/eventbus_api.yaml` are read-only references (the server resume API is unchanged)

## Required Changes
- Track the last successfully processed `seq` in `EventBusSubscriber` across reconnects and pass it as `since_seq` on reconnect.
- Use a configured stable `consumer_id` instead of a random one per attempt, and handle HTTP 409 (`ConsumerAlreadyConnectedError`) while the old connection is still registered.
- Add a test simulating a disconnect and reconnect with an event published during the gap, asserting the reconnected subscriber receives it exactly once.

## Constraints
- Do not change the existing bounded 5-attempt/1-second-delay retry budget.
- Do not change the server or broker API in this issue.
- Pre-production-wiring fix only: do not wire `EventBusSubscriber` into `factory.py` or `startup*.py`.

## Acceptance Criteria
- A reconnecting subscriber receives events published during the disconnect window (replayed by the server from the last processed `seq`), without duplicates.
- The subscriber uses a configured, stable `consumer_id` that an authorization grant can name.
- The existing reconnect retry behavior (attempt count, delay) is unchanged.

## Testing Expectations
Unit test simulating a disconnect/reconnect cycle with an event published mid-gap, asserting no event loss. Run `tests/agent/test_eventbus_subscriber.py` and relevant `scripts/eventbus` broker tests after the change.

## Documentation Impact
N/A: no broker API or manifest change. State in `docs/` that the subscriber resumes via `since_seq` once implemented, not before.

## Out of Scope
- Wiring `EventBusSubscriber` into production REPL startup (separate future task).
- Any change to the broker, the server resume logic or the authorization layer.
- `EventBusTopicAdminClient`'s own behavior.

## Dependencies
N/A: none.

## Unresolved Questions
- Where the stable `consumer_id` comes from (configuration key and how a grant is provisioned for it): a decision for the owner.
- How to handle a 409 on reconnect while the old connection is still registered (wait and retry, or fail): a design choice during implementation.

## AI Implementation Instruction
Implement last-`seq` tracking, `since_seq` on reconnect and a configured stable `consumer_id` in the subscriber only; do not change the server or wire the subscriber into production. Add the disconnect/reconnect regression test described above before considering this done.

## Traceability
- **Workflow phase**: python-code-review -> issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261003-180343
- **Related target files**: scripts/agent/eventbus_subscriber.py, scripts/eventbus/broker.py
