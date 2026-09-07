# Define and enforce valid event delivery state transitions

## Priority
Medium

## Summary
`scripts/eventbus/db.py`'s `nack_event()` (lines 143-158) unconditionally increments
`delivery_failure_count` for any event matching the given `event_id` — confirmed by direct
read, its `UPDATE` statement's `WHERE` clause is `event_id = ?` alone, with no condition
excluding an already-ACKed (`acked_at IS NOT NULL`) or already-DLQ'd (`dlq_at IS NOT NULL`)
event. There is no state-transition contract anywhere in `scripts/eventbus/` that rejects an
invalid ACK/NACK/promote/requeue combination.

## Background
Confirmed by direct read of `scripts/eventbus/db.py`: `ack_event()` (lines 118-141) is
itself idempotent against re-ACK (`WHERE event_id = ? AND acked_at IS NULL`, returning
`(True, False)` for an already-acked event without erroring), but `nack_event()` has no
equivalent guard — it will happily increment `delivery_failure_count` for an event that is
already ACKed or already sitting in the DLQ. By contrast, `scripts/eventbus/dlq_route.py`'s
`dlq_requeue()` (lines 49-78) already returns HTTP 409 (`ERR_EVENT_NOT_IN_DLQ`) for an
event that exists but is not currently in the DLQ — so a 409-on-invalid-transition pattern is
already established elsewhere in this codebase and can be extended to ACK/NACK.

## Problem
- `NACK` on an already-ACKed event silently increments its failure count with no error and no
  defined meaning — the event is "done" from the ACK side but is treated as still failing from
  the NACK side.
- `NACK` on an event already in the DLQ (`dlq_at IS NOT NULL`) also silently increments its
  count, which (combined with this batch's DLQ-requeue-redesign issue's separation of lifetime
  vs. cycle failure counts) could immediately push a freshly-requeued event back toward
  re-promotion.
- No existing test in `tests/eventbus/test_eventbus_ack_nack.py`/
  `test_eventbus_subscribe_transition.py` (confirmed present under `tests/eventbus/`) asserts
  that NACK-after-ACK or NACK-after-DLQ-promotion is rejected — this needs direct confirmation
  of those files' actual assertions, but `nack_event()`'s SQL shows no guard exists to make such
  a test pass today.

## Reason for Change
Turn delivery handling into a deterministic state machine. Every operation must have
documented preconditions, transactional postconditions, and a defined error when the requested
transition is invalid.

## Implementation Intent
Define normal, delivered, ACKed, failed, DLQ, requeued, and archived states as applicable to
the final consumer delivery model (coordinate with this batch's transactional-ACK/offset and
DLQ-redesign issues so the state names stay consistent across all three). Document allowed and
prohibited transitions. Add state predicates to `nack_event()`'s (and any other relevant)
database updates — e.g. `WHERE event_id = ? AND acked_at IS NULL AND dlq_at IS NULL` — and
return HTTP 409 with a safe, actionable reason when the transition is rejected, following the
existing `ERR_EVENT_NOT_IN_DLQ` pattern in `dlq_route.py`.

## Target Files or Areas
- `scripts/eventbus/db.py`
- `scripts/eventbus/ack_route.py`
- `scripts/eventbus/dlq.py`
- `scripts/eventbus/dlq_route.py`
- `docs/06_eventbus_04_dlq_offsets_and_delivery_semantics.md`
- `docs/adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md`

## Required Changes
- Define normal, delivered, ACKed, failed, DLQ, requeued, and archived states as applicable to
  the final consumer model.
- Document allowed and prohibited transitions.
- Add state predicates to database updates (starting with `nack_event()`'s `WHERE` clause).
- Return HTTP 409 for invalid transitions and include a safe, actionable reason.
- Make concurrent ACK, NACK, promotion, and requeue outcomes deterministic.
- Link each invariant to an automated test.

## Constraints
- Keep unrelated behavior unchanged.
- Do not weaken fail-closed behavior, validation, or auditability.
- Update the canonical ADR or EventBus specification when the delivery contract changes.
- Do not mark this issue complete with documentation-only changes when runtime behavior is
  defective.
- Do not invent configuration values, migration history, or approval evidence.

## Acceptance Criteria
- [ ] ACKed events cannot be NACKed (a NACK against an ACKed event returns a defined error,
      not a silently-incremented failure count).
- [ ] DLQ events cannot accumulate normal delivery failures before requeue (a NACK against a
      DLQ'd event returns a defined error, not a silently-incremented failure count).
- [ ] Concurrent conflicting transitions produce one valid winner and a defined response for
      the loser.
- [ ] The specification, API behavior, and tests use the same state names and rules.

## Testing Expectations
Update `tests/eventbus/test_eventbus_ack_nack.py` to add NACK-after-ACK and NACK-after-DLQ
test cases asserting the new rejection behavior; run the complete EventBus test suite and the
repository's linting, type checking, and documentation consistency checks.

## Documentation Impact
Update `docs/06_eventbus_04_dlq_offsets_and_delivery_semantics.md` and
`docs/adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md` to document the
state-transition contract as the canonical specification, using the same state names as the
implementation and tests.

## Out of Scope
- Transactional ACK/offset redesign (tracked separately in this batch) — this issue only adds
  state predicates to the existing single-row model; it does not redesign the underlying
  per-consumer schema.
- DLQ requeue real-redelivery redesign (tracked separately in this batch).

## Dependencies
Coordinate state naming with this batch's transactional-ACK/offset redesign (EB-H01) and DLQ
requeue redesign (EB-H03) issues so all three use consistent state names — implement in
whichever order is convenient, but reconcile naming before finalizing documentation.

## Unresolved Questions
N/A: none

## AI Implementation Instruction
Start with `nack_event()`'s `WHERE` clause — add `AND acked_at IS NULL AND dlq_at IS NULL` (or
equivalent) and return a rowcount-based signal the route layer can turn into HTTP 409,
mirroring `dlq_route.py`'s existing `ERR_EVENT_NOT_IN_DLQ` pattern. Do not redesign the
underlying schema in this issue — that is EB-H01's scope.
