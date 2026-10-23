# Implement end-to-end NACK idempotency for client and proxy retries

## Priority
High

## Summary
Define one NACK idempotency key contract from the caller through the HTTP route to durable delivery state, so a retry of the same delivery attempt does not increment the failure counter again.

## Background
Confirmed against HEAD (adversarial re-verification):
- `scripts/eventbus/ack_route.py` generates `attempt_id = str(uuid.uuid4())` inside `_nack_and_promote` on every request and passes it as `last_nack_attempt`; `scripts/eventbus/delivery_repo.py` suppresses a repeat only when the stored `consumer_last_nack_attempt` equals the new key. A UUID per request never matches, so the repository guard is dead for retries.
- The repository stores one key per `(consumer_id, event_id)` row (single column `consumer_last_nack_attempt`). Even with a caller-supplied key, only a repeat of the most recent attempt is deduplicated: the sequence NACK(A), NACK(B), NACK(A retry) increments the count a second time for A. The memo's "retention and replay-window semantics" therefore has a concrete current limit of one remembered key.
- No NACK client exists under `scripts/` (grep for NACK outside `scripts/eventbus/` finds nothing), and the SSE events delivered by `subscribe_route.py` carry no delivery-attempt identifier. "Delivery attempt" is not defined anywhere a client could read it, so a client cannot currently generate a stable key for a retry.
- `nack_event()` still accepts `consumer_id=None`; the route always requires `consumer_id`, so that path is internal-only today.

## Problem
A retry of the same NACK is indistinguishable from a new delivery attempt and increments the failure counter again, moving the event to `max_retry` and the DLQ earlier than intended.

## Reason for Change
Network and proxy retries are normal in an at-least-once system; double counting violates the documented duplicate-NACK behavior.

## Implementation Intent
The same delivery attempt reuses the same caller-supplied key; a genuinely new attempt uses a new key. The key is scoped by consumer ID, event ID and delivery attempt, passed unchanged to the repository, and its retention and replay-window semantics are defined.

## Target Files or Areas
`scripts/eventbus/ack_route.py`, `scripts/eventbus/delivery_repo.py`, `scripts/eventbus/subscribe_route.py` (event stream fields), `scripts/eventbus/schema.sql` (only if the storage changes), the request-ID middleware in `scripts/eventbus/auth.py`, tests `tests/eventbus/test_eventbus_ack_nack.py`, `test_eventbus_ack_endpoint.py`, `docs/24_eventbus/` (ACK/NACK documents) and `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`.

## Required Changes
- Define the delivery-attempt identity: either the server issues an attempt identifier with each delivered event (SSE field), or the NACK carries a client-generated idempotency key that is stable across retries of one NACK call.
- Add the key to the NACK API; remove per-request UUID generation as the idempotency source and pass the key unchanged to the repository.
- Decide the retention and replay window; if more than the latest key must be deduplicated, change the storage (for example a small per-consumer-event key set) instead of the single column. A schema change requires bumping `PRAGMA user_version` (database is recreated, never migrated).
- Remove or explicitly internalize the `consumer_id=None` repository path.
- Update the endpoint contract, the ACK/NACK documentation and any client implementation (none exists in this repository; the contract is for external subscribers).

## Constraints
Schema changes are not migrated (the database is recreated), so a storage change must account for the schema version stamp. Behavior for NACK requests without a key must be decided explicitly (reject, or server-derived key); the current behavior counts every request as a new attempt.

## Acceptance Criteria
- Retrying the same delivery attempt does not increment the counter and a distinct attempt increments it exactly once.
- Duplicate retries cannot accelerate DLQ promotion.
- API, client, route, repository, documentation and tests use the same contract.
- The documented retention window is tested at its boundary (for example NACK(A), NACK(B), NACK(A retry) behaves exactly as the contract states).

## Testing Expectations
Same key repeated sequentially; same key repeated concurrently; retry after a simulated timeout; different keys; duplicate at `max_retry - 1`. Then ruff and mypy.

## Documentation Impact
Yes: the NACK endpoint contract, the idempotency key scope and retention, and the delivery-attempt definition.

## Out of Scope
DLQ requeue (H-01); ACK semantics.

## Dependencies
No open issue under `issues/` overlaps. Related memo task H-01 (DLQ promotion) and L-01 (stale ACK/NACK comments).

## Unresolved Questions
- What happens to a NACK request without a key: reject with 400, or fall back to a server-derived key? Owner decision.
- Where does the client obtain the attempt identity (SSE event field versus client-generated key)? Needs design decision.
- Must retries of an older attempt (A, B, A-retry) be deduplicated, or only the latest? Decides whether the schema changes.

## AI Implementation Instruction
- Read the listed implementation, tests, and design documents before editing; keep changes minimal and do not rewrite unrelated files.
- Preserve the existing public contract unless this issue explicitly names a contract change; an unresolved owner decision is reported, not guessed.
- Do not resolve an implementation defect by changing documentation alone.
- Keep transaction, locking, authorization, durability and fail-closed boundaries explicit.
- Add or update automated tests for every acceptance criterion; do not implement out-of-scope items.

## Traceability
- **Workflow phase**: `issue-creator` (converted from `memo-issue.md`, task `H-05`)
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261023-154326
- **Related target files**: `scripts/eventbus/ack_route.py`, `scripts/eventbus/delivery_repo.py`
