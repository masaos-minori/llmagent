# Enforce consumer and topic authorization across subscribe, ACK, and NACK

## Priority
High

## Summary
Consumer identity, topic permissions, ACK ownership, and NACK ownership currently lack one fail-closed authorization model across the subscribe/ACK/NACK paths, creating a risk that a consumer could act on another consumer's events or an unauthorized topic could be subscribed to.

## Background
Depends on `eventbus02`'s principal model — this issue applies that principal to the consumer-scoped state transitions (subscribe, ACK, NACK) specifically.

## Problem
The consumer ACK endpoint currently has (or is at risk of having) a consumer-less fallback path, and neither the ACK nor NACK endpoint mandatorily validates that the requesting principal owns the `consumer_id` it is acting as, nor that the event was actually delivered to that consumer before accepting the ACK/NACK. Topic authorization for subscriptions is similarly not guaranteed to fail closed when identity resolution is missing, and there is no single canonical topic list/parameter name shared between the endpoint and its authorization dependency.

## Reason for Change
Consumer identity, topic permissions, ACK ownership, and NACK ownership are interdependent. Separate changes could leave bypass paths or contradictory state transitions.

## Implementation Intent
Apply one fail-closed consumer authorization model to subscription and all consumer-scoped state changes, built on the principal introduced in `eventbus02`.

## Target Files or Areas
- `scripts/eventbus/app.py`
- `scripts/eventbus/ack_route.py`
- `scripts/eventbus/db.py`
- `tests/eventbus/test_eventbus_ack_endpoint.py`, `tests/eventbus/test_eventbus_ack_nack.py`, `tests/eventbus/test_eventbus_crash_ack.py`
- `scripts/eventbus/auth.py`
- `scripts/eventbus/config.py`
- `tests/eventbus/test_eventbus_auth.py`
- `scripts/eventbus/subscribe_route.py`
- `tests/eventbus/test_eventbus_subscribe.py`

## Required Changes
- Pass the authenticated principal or equivalent authorization context through all ACK layers.
- Validate that the requested consumer ID belongs to the principal.
- Verify that the event was delivered to the consumer before accepting the ACK.
- Make `consumer_id` mandatory for the consumer ACK endpoint.
- Remove the consumer-less fallback from the consumer API.
- If forced administrative ACK is required, expose it as a separate operator-only endpoint.
- Add a required `consumer_id` to the NACK API.
- Validate that the principal is allowed to use the consumer ID.
- Verify that the event was delivered to that consumer.
- Define the relationship between consumer-specific failures and the event-level retry counter.
- Represent unrestricted, deny-all, and explicit allowlist states with distinct values.
- Fail closed when a token has no authorization entry.
- Define whether an empty consumer ID is permitted.
- Use one parameter name and one canonical topic list across the endpoint and authorization dependency.
- Fail closed when identity resolution is missing or invalid.
- Pass only authorized topics to the subscription handler.
- Define whether an empty topic list means all topics and who may request it.

## Constraints
N/A: none stated in source review.

## Acceptance Criteria
- Authorization context is available in the transactional ACK operation.
- A consumer cannot ACK an event on behalf of another consumer.
- Tests cover authorized ACK, consumer mismatch, and undelivered-event ACK.
- A missing or empty consumer ID is rejected with HTTP 400 or 422.
- Consumer ACK updates delivery state and consumer offset atomically.
- Administrative override, if implemented, requires an operator principal and is audited.
- A NACK is accepted only from the consumer that received the event.
- A consumer mismatch receives HTTP 403 or 409 according to the documented contract.
- Retry and DLQ promotion behavior remains deterministic.
- Tests cover authorized, unauthorized, missing-consumer, ACKed, and already-DLQ states.
- Unrestricted, deny-all, and explicit allowlist configurations behave differently and predictably.
- An unregistered token cannot use any consumer ID.
- Tests cover empty ID, allowed ID, denied ID, empty set, unrestricted state, and missing mapping.
- Unauthorized topics are rejected before broker subscription or database replay.
- A mixed list containing any unauthorized topic is rejected as a whole.
- Missing identity never bypasses authorization.
- Tests cover one topic, multiple topics, duplicates, no topic, and mixed authorization.

## Testing Expectations
Add or update unit, integration, and regression tests for all affected boundaries (see Acceptance Criteria). Run the relevant test suites, static analysis, and type checks.

## Documentation Impact
Update active design documents and the known-issue inventory only after implementation evidence is available.

## Out of Scope
- Unrelated refactoring outside the identified behavioral boundary.

## Dependencies
Depends on `eventbus02` (principal-based authentication) being implemented first, since this issue passes that principal through the ACK/NACK/subscribe layers. `eventbus10` (ADR/known-issue reconciliation) depends on this issue's outcome.

## Unresolved Questions
Same ACK test file ambiguity as `eventbus02` — confirm which existing test file(s) under `tests/eventbus/` correspond to the source review's cited `test_eventbus_ack.py` before adding tests. Non-blocking.

## AI Implementation Instruction
Implement only after `eventbus02`'s principal model is available; do not duplicate principal-resolution logic here. Keep changes scoped to consumer/topic authorization in the ACK, NACK, and subscribe paths; do not rewrite unrelated DB or broker logic beyond what fail-closed authorization requires. Confirm that failure paths do not expose credentials, tokens, payloads, or sensitive configuration. Stop and report if the retry-counter/consumer-failure relationship is ambiguous in the current code rather than inventing a policy.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260914-102317
- **Related target files**: scripts/eventbus/app.py, scripts/eventbus/ack_route.py, scripts/eventbus/db.py, tests/eventbus/test_eventbus_ack_endpoint.py, tests/eventbus/test_eventbus_ack_nack.py, tests/eventbus/test_eventbus_crash_ack.py, scripts/eventbus/auth.py, scripts/eventbus/config.py, tests/eventbus/test_eventbus_auth.py, scripts/eventbus/subscribe_route.py, tests/eventbus/test_eventbus_subscribe.py
