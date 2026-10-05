# EventBus: NACK is accepted (HTTP 200) after the same consumer has ACKed the event

## Priority
High

## Summary
After a consumer ACKs an event through `POST /events/{event_id}/ack`, a later `POST /nack` for the same event and consumer still succeeds with HTTP 200 and increments the failure counters. The documentation states that an ACKed event cannot be NACKed (HTTP 409). Decide the intended behavior and align code, tests and documentation.

## Background
- The consumer ACK path (`ack_route.py`, `_do_ack`) calls `ack_event_for_consumer()` in `scripts/eventbus/delivery_repo.py`. That function writes only `consumer_delivery` and `consumer_offsets`; it never sets `events.acked_at`.
- The consumer-less `ack_event()` in `delivery_repo.py`, which does set `events.acked_at`, is re-exported by `eventbus.db` but is not called by any route (the route module comments that the consumer-less path was removed).
- `nack_event()` in `delivery_repo.py` only rejects (returns the invalid-transition sentinel that `ack_route.py` maps to HTTP 409) when `events.acked_at` or `events.dlq_at` is set.
- Documentation describing the 409 on NACK after ACK: `docs/24_eventbus/eventbus_03_dlq_operations.md` (response description and ACK/NACK state transition table), `docs/24_eventbus/eventbus_06_dlq_offsets_and_delivery_semantics.md` (prohibited transitions), `docs/24_eventbus/eventbus_15_ack_nack_endpoints.md` (conflict responses), and `docs/10_adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md` (invalid transitions already ACKed or DLQ'd map to HTTP 409).
- `tests/eventbus/test_eventbus_ack_nack.py` covers ACK, repeated ACK and NACK separately; no test performs ACK followed by NACK through the route or through the per-consumer ACK function (Evidence label: confirmed by code reading and test file search).

## Problem
Evidence (confirmed by code reading, not by execution):
- Because the per-consumer ACK leaves `events.acked_at` NULL and `dlq_at` NULL, the `WHERE acked_at IS NULL AND dlq_at IS NULL` guard in `nack_event()` matches, so the NACK is applied: `delivery_failure_count`, `cycle_failure_count` and the consumer-specific failure counter increase and the route returns HTTP 200 with `delivery_failure_count`.
- Repeated NACKs after an ACK can reach `max_retry` and promote an already-ACKed event to the DLQ, which contradicts the documented state machine (ACKed is terminal for NACK).
- The 409 branch for "event already acknowledged" in `ack_route.py` is effectively reachable only for events whose `events.acked_at` was set by some path other than the routes (for example legacy data), so the documented 409 is not produced by the normal ACK flow.
- Ambiguity: the event is shared by multiple consumers while ACK state is per consumer. Whether "ACKed" means "ACKed by this consumer" or "ACKed by any consumer" is not stated in the documents.

## Reason for Change
Documented API contract and implemented behavior disagree on a state transition that affects delivery correctness (spurious failure counts and possible DLQ promotion of processed events).

## Implementation Intent
Recommended: reject NACK with HTTP 409 (`event already acknowledged`) when the same consumer has already ACKed the event, because the docs and ADR-006 define ACKed as non-NACKable. The check should use the per-consumer delivery state (`consumer_delivery.acked_at` for the given `consumer_id`), consistent with the per-consumer ACK model, and must not mutate any counter when rejecting. Alternative: keep current behavior and change the documents (and ADR-006) to state that NACK after a per-consumer ACK is allowed and what it does to counters; this is not recommended because it permits DLQ promotion of processed events.

## Target Files or Areas
- scripts/eventbus/delivery_repo.py (`nack_event`)
- scripts/eventbus/ack_route.py (`nack`, 409 mapping)
- tests/eventbus/test_eventbus_ack_nack.py
- docs/24_eventbus/eventbus_03_dlq_operations.md
- docs/24_eventbus/eventbus_06_dlq_offsets_and_delivery_semantics.md
- docs/24_eventbus/eventbus_15_ack_nack_endpoints.md
- docs/10_adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md (only if the alternative option is chosen)

## Required Changes
- Decide between the two options in Implementation Intent and record the decision in this issue.
- If rejecting: make NACK return HTTP 409 when the requesting consumer has already ACKed the event, without changing failure counters; keep existing 404/403/409 (DLQ) behavior.
- Add regression tests for ACK then NACK (see Testing Expectations).
- Update the three EventBus documents so they describe the final behavior and remove the pointer to this issue once resolved.

## Constraints
- Preserve idempotent duplicate-ACK behavior (HTTP 200 with `already_acked`).
- Preserve NACK-then-ACK behavior (ACK succeeds, counters not readjusted).
- NACK by a different consumer that has not ACKed must keep its current behavior unless the decision on "ACKed by any consumer" says otherwise.
- Authorization (403) must still be evaluated before the state check.

## Acceptance Criteria
- ACK by consumer A followed by NACK by consumer A returns HTTP 409 with `event already acknowledged` (if the reject option is chosen), and `delivery_failure_count`, `cycle_failure_count` and the consumer failure counter are unchanged.
- The event is not promoted to the DLQ by NACKs sent after the ACK.
- Duplicate ACK still returns HTTP 200 with `already_acked: true`; NACK then ACK still succeeds.
- The documented behavior of the three EventBus documents matches the code and the pointer to this issue is removed.

## Testing Expectations
- Unit test on `nack_event()` / `ack_event_for_consumer()`: ACK then NACK for the same consumer returns the invalid-transition result and leaves counters unchanged.
- Route-level test: POST ack then POST nack returns 409 with the documented detail; counters verified via the database.
- Regression test: repeated NACK after ACK never reaches DLQ promotion.
- Test for a second consumer that has not ACKed (documents the decided semantics).
- Run `uv run pytest tests/eventbus`, ruff and mypy; run the docs checkers for the changed documents.

## Documentation Impact
Yes. `eventbus_03`, `eventbus_06` and `eventbus_15` describe the transition and currently carry a pointer to this issue; after resolution they must state the final behavior (failure behavior, state transitions). ADR-006 changes only if the alternative option is chosen.

## Out of Scope
- Redesigning the per-consumer delivery model or offsets.
- Idempotency guard for duplicate NACK (separately documented as a known issue).
- The deleted-event race on the 409 path noted in ADR-006.

## Dependencies
N/A: none

## Unresolved Questions
- Should "already ACKed" mean ACKed by the same consumer only, or by any consumer, given that `events.acked_at` is not set by the per-consumer path?
- Should `events.acked_at` ever be set by the per-consumer ACK path (for example when all consumers have ACKed)? Unknown; not covered by the documents.

## AI Implementation Instruction
Keep the change minimal and limited to the NACK state check and its tests. Do not change ACK semantics or offsets. Do not silently patch documents to match current behavior; follow the decision recorded here. Stop and report if the decision on per-consumer versus global ACK state is not made.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261005-102244
- **Related target files**: scripts/eventbus/delivery_repo.py, scripts/eventbus/ack_route.py, tests/eventbus/test_eventbus_ack_nack.py, docs/24_eventbus/eventbus_03_dlq_operations.md, docs/24_eventbus/eventbus_06_dlq_offsets_and_delivery_semantics.md, docs/24_eventbus/eventbus_15_ack_nack_endpoints.md
