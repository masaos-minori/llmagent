# Redesign DLQ retry state and make requeue perform real redelivery

## Priority
High

## Summary
`scripts/eventbus/db.py`'s `requeue_event()` only clears `dlq_at` and increments
`dlq_requeue_count` in SQLite — confirmed by direct read, it never publishes to
`EventBroker`, never resets `delivery_failure_count`, and never touches the DLQ JSON file
that `scripts/eventbus/dlq.py`'s `_atomic_write()` created when the event was promoted. A
requeued event is therefore invisible to any active or reconnecting subscriber, can be
immediately re-promoted to the DLQ on the next NACK, and leaves a stale `<event_id>.json`
file in `deadletter_dir` that no longer reflects the event's live state.

## Background
Confirmed by direct read of `scripts/eventbus/db.py` lines 246-259 (`requeue_event`): the
function's only side effects are `dlq_requeue_count = dlq_requeue_count + 1, dlq_at = NULL`.
`scripts/eventbus/dlq_route.py` lines 49-78 (`dlq_requeue`) calls only `requeue_event()` and
returns; it never calls into `scripts/eventbus/broker.py`'s `EventBroker.publish()`, and never
deletes/archives the DLQ JSON file written by `dlq.py`'s `_atomic_write()` (lines 150-165).
`tests/eventbus/test_eventbus_requeue_edge_cases.py` (confirmed by direct read of its fixture
and helpers) tests the DB-flag-only behavior currently implemented; it does not assert that a
requeued event reaches an active subscriber or that the DLQ JSON file is reconciled.

## Problem
- A successful requeue clears `dlq_at` in SQLite, but the event's original `seq` may already
  be behind every currently-subscribed consumer's replay/live-delivery cursor (the SSE
  generator in `subscribe_route.py` only ever delivers rows fetched with `seq > since_seq` at
  connection time, or new events pushed live via `broker.publish()` — a requeued event with an
  old `seq` matches neither).
- `delivery_failure_count` is never reset by `requeue_event()`, so the very next `NACK` against
  the requeued event (`nack_event()` in `db.py`, which unconditionally increments the count) can
  push it back over `cfg.max_retry` and re-promote it to the DLQ almost immediately.
- The JSON file written to `deadletter_dir` by `_atomic_write()` when the event was originally
  promoted is never removed, archived, or updated on requeue — SQLite says the event is no
  longer in the DLQ (`dlq_at IS NULL`) while the filesystem still holds a DLQ record for it,
  producing exactly the SQLite/filesystem divergence memo4.md describes.

## Reason for Change
Make requeue an actual, traceable retry operation rather than a database flag change. A
successfully requeued event must enter a reachable delivery path, receive a well-defined retry
budget, preserve lineage and audit history, and leave all persistence representations in a
consistent documented state.

## Implementation Intent
Define whether requeue creates a new sequence/event row (preferred, per memo4.md, unless a
consumer-specific redelivery ledger is implemented) or otherwise makes the event genuinely
reachable via `EventBroker.publish()`/replay. Preserve lineage to the original event and record
the requeue attempt. Separate a lifetime failure count from the current delivery-cycle failure
count so `requeue_event()` can reset only the cycle-specific count. Reconcile the DLQ JSON file
(archive, move, or explicitly mark superseded) as part of the same requeue operation, using
SQLite as the canonical DLQ state.

## Target Files or Areas
- `scripts/eventbus/schema.sql`
- `scripts/eventbus/db.py`
- `scripts/eventbus/ack_route.py`
- `scripts/eventbus/dlq.py`
- `scripts/eventbus/dlq_route.py`
- `scripts/eventbus/broker.py`
- `scripts/eventbus/subscribe_route.py`
- `docs/06_eventbus_04_dlq_offsets_and_delivery_semantics.md`

## Required Changes
- Define whether requeue creates a new sequence or uses a dedicated redelivery queue. Prefer a
  new sequence unless a consumer-specific redelivery ledger is implemented.
- Preserve lineage to the original event and record the requeue attempt.
- Separate lifetime failure count from the current delivery-cycle failure count.
- Reset only the cycle-specific retry count during requeue.
- Ensure active subscribers and reconnecting consumers can receive the requeued event (call
  into `EventBroker.publish()` or an equivalent reachable path).
- Define SQLite as the canonical DLQ state and archive, move, or explicitly classify the
  corresponding JSON file after requeue.
- Make requeue idempotent and safe under concurrent requests.
- Keep inline promotion (`promote_single`) and background sweep (`sweep_orphans`) consistent
  with the redesigned state model.

## Constraints
- Keep unrelated behavior unchanged.
- Do not weaken fail-closed behavior, validation, or auditability.
- Use additive and idempotent database migrations for persisted data.
- Update the canonical ADR or EventBus specification when the delivery contract changes.
- Do not mark this issue complete with documentation-only changes when runtime behavior is
  defective.
- Do not invent configuration values, migration history, or approval evidence.

## Acceptance Criteria
- [ ] A successful requeue creates an observable delivery path — a test subscriber
      (active or reconnecting) actually receives the requeued event, not merely a cleared
      `dlq_at` flag.
- [ ] A requeued event is not hidden behind an already advanced offset.
- [ ] The event receives the configured retry opportunity after requeue (cycle-specific
      failure count is reset; lifetime count is preserved).
- [ ] Lifetime failure and requeue history remain auditable.
- [ ] Repeated or concurrent requeue requests do not produce uncontrolled duplicates.
- [ ] SQLite and filesystem DLQ representations remain consistent according to the documented
      policy — the stale JSON file left by today's implementation is reconciled.

## Testing Expectations
Update `tests/eventbus/test_eventbus_requeue_edge_cases.py` and
`tests/eventbus/test_eventbus_dlq_promotion.py` to assert actual redelivery reachability and
DLQ-file reconciliation, not only the DB flag change. Run the complete EventBus test suite and
the repository's linting, type checking, and documentation consistency checks.

## Documentation Impact
Update `docs/06_eventbus_04_dlq_offsets_and_delivery_semantics.md` to describe the redesigned
requeue/redelivery model, lifetime-vs-cycle failure counts, and the SQLite-vs-JSONL DLQ state
policy as the canonical specification.

## Out of Scope
- Transactional ACK/offset redesign (tracked separately in this batch, though the failure-count
  schema change here should stay compatible with it).
- Backpressure/duplicate-consumer-connection handling (tracked separately in this batch).
- Consolidating `promote_to_dlq()`/`promote_single()`/`sweep_orphans()` (tracked separately in
  this batch — do not merge that cleanup into this issue's scope).

## Dependencies
N/A: none, though this issue's schema changes (lifetime vs. cycle failure count) should be
coordinated with the DLQ-promotion-path-consolidation issue in this batch to avoid duplicated
schema churn.

## Unresolved Questions
Whether requeue should create a new `seq`/row (simplest, matches memo4.md's stated preference)
or route through a dedicated redelivery ledger — default to a new sequence unless a concrete
need for a separate ledger is identified during implementation.

## AI Implementation Instruction
Confirm current callers/tests of `requeue_event()` and `dlq_requeue()` before changing their
return shape — `tests/eventbus/test_eventbus_requeue_edge_cases.py` and
`tests/eventbus/test_eventbus_dlq_pagination.py` reference this path. Do not implement DLQ
JSON-file reconciliation by simply deleting the file without an explicit archive/classification
decision, per Constraints.
