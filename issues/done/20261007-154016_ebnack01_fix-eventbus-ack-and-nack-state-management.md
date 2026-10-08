# Fix EventBus ACK and NACK state management

## Priority
Medium

## Summary
Manage delivery state per consumer only, make NACK idempotent per delivery attempt, and make ACK record the first acknowledgement time for existing events exactly once.

## Background
Source: local investigation notes (memo1.md, ISSUE-08), consolidating EVENTBUS-012, EVENTBUS-011, EVENTBUS-014 and three earlier findings. Delivery is at-least-once, so client re-sends are routine.

## Problem
- `nack_event()` increments the failure count on every call, so a re-sent NACK for the same delivery double-counts (EVENTBUS-012).
- `delivery_failure_count` is one value per event row shared by all consumers, so one consumer's repeated NACKs can send the event to the DLQ before other consumers process it.
- The NACK rejection state check (-2) runs under a separate lock acquisition from the NACK itself; if the event is deleted in between, 409 is returned instead of 404 (EVENTBUS-011).
- `events.acked_at` is never written but is read in the NACK WHERE clause and the 409 branch; an unreferenced `ack_event()` remains (EVENTBUS-014).
- ACK for a non-existent event_id commits an orphan `consumer_delivery` row (no foreign key).
- Re-ACK overwrites `acked_at` through `ON CONFLICT DO UPDATE`, losing the first ACK time; events already in the DLQ can still be ACKed.

## Reason for Change
- Non-idempotent NACK moves events to the DLQ earlier than intended under routine retries.
- Shared failure counts defeat the multi-consumer design: one faulty consumer blocks others.
- Reading a never-written column leaves misleading state-transition documentation.
- Orphan rows, overwritten ACK times, and ACKs on DLQ events harm audit and data integrity and violate state-transition rules.

## Implementation Intent
- Per-consumer state in `consumer_delivery` as the single model; no event-level ACK state.
- NACK idempotent per delivery attempt; ACK recorded once, for existing, non-DLQ events.

## Target Files or Areas
- `scripts/eventbus/delivery_repo.py`, `ack_route.py`, `schema.sql` / `scripts/db/schema_sql.py`, `_constants.py`, `dlq.py` (to be read)
- ADR-006, eventbus and db documentation (db_03 / eventbus series)

## Required Changes
- Add a per-consumer failure count and the last NACKed delivery-attempt ID (or generation number) to `consumer_delivery`; ignore a NACK for the same attempt.
- Decide DLQ promotion from the per-consumer failure count; decide in ADR-006 whether the DLQ unit is per event or per consumer.
- Perform NACK handling and state determination in one lock acquisition and one transaction.
- Drop the `events.acked_at` column (using the existing `_migrate` approach), `ack_event()`, the 409 branch reading the column, and the unused `requeue_event()`.
- `ack_event_for_consumer()`: verify the event exists first (return not found, write nothing); keep the first `acked_at` via `COALESCE`; return 409 for events in the DLQ.

## Constraints
- Schema migration must be safe for existing databases.
- At-least-once semantics must be preserved.

## Acceptance Criteria
- The same NACK sent twice increments the failure count once (test).
- Consumer A's NACKs do not affect consumer B's DLQ decision (test).
- ACK for a non-existent event adds no row (test).
- No events query reads `acked_at`.

## Testing Expectations
- Repository-level tests for ACK/NACK and migration; DLQ tests; ruff, mypy, targeted pytest.

## Documentation Impact
Update ADR-006, state-transition and 409/404 descriptions in the eventbus docs, and the db schema docs; remove EVENTBUS-011/012/014 from the ledger when done.

## Out of Scope
- Authorization model changes (separate issue).

## Dependencies
- Can proceed in parallel with the EventBus authorization issue; includes a schema change, so documentation updates must be coordinated with the Known Issue ledger issue.

## Unresolved Questions
- Where the failure-count column lives today and whether DLQ promotion (`promote_single`) is per event (requires `schema.sql` / `schema_sql.py`, `_constants.py`, `dlq.py`).

## AI Implementation Instruction
Read the schema and DLQ code first and report if the assumptions differ. Provide a migration for existing databases. Keep authorization logic untouched.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261007-154016
- **Related target files**: `scripts/eventbus/delivery_repo.py`, `scripts/eventbus/ack_route.py`, `scripts/eventbus/schema.sql`, `scripts/db/schema_sql.py`, `scripts/eventbus/_constants.py`
