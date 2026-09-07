# Redesign consumer delivery state and make ACK and offset updates transactional

## Priority
High

## Summary
`scripts/eventbus/db.py`'s `events` table still stores `acked_at`/`delivery_failure_count`/
`dlq_at` as single global columns on the event row, and `scripts/eventbus/offsets.py` still
persists consumer offsets as separate files, not SQLite rows. `ack_route.py`'s `_ack_and_offset()`
calls `_ack_event()` (which commits to SQLite) and then `write_offset()` (a separate file write)
as two independent operations — confirmed by direct read, there is no shared transaction or
rollback between them.

## Background
Confirmed by direct read of `scripts/eventbus/db.py` lines 118-141 (`ack_event`) and
`scripts/eventbus/offsets.py` lines 21-60 (`write_offset`): `ack_event()` issues its own
`conn.commit()` before `ack_route.py`'s `_ack_and_offset()` (lines 34-46) proceeds to call
`write_offset()`, which performs a separate, unguarded filesystem write. `schema.sql` (lines
3-14) defines one `events` table with no separate consumer/offset table.

## Problem
- `acked_at`/`delivery_failure_count`/`dlq_at` are event-row columns, not
  per-consumer records — a second independent consumer cannot ACK the same event without
  colliding on the first consumer's `acked_at`/failure-count state (confirmed: `ack_event()`'s
  `UPDATE ... WHERE event_id = ? AND acked_at IS NULL` is a single global flag, not keyed by
  consumer).
- If `write_offset()` raises (e.g. `ValueError` on a consumer-ID collision, per
  `offsets.py` lines 44-53) after `ack_event()`'s `conn.commit()` has already succeeded, the
  exception propagates out of `_ack_and_offset()` uncaught (confirmed: no try/except around the
  `write_offset()` call in `ack_route.py` lines 34-46) — the caller receives an error even though
  the ACK is already durably committed in SQLite, exactly the partial-success scenario this
  issue describes.
- `tests/eventbus/test_eventbus_offsets.py` exercises `write_offset()`/`read_offset()` in
  isolation and confirms today's (file-based, non-transactional) behavior — it does not test
  the ACK+offset combination failing atomically, so this gap is not caught by the existing
  suite.

## Reason for Change
Separate immutable event data from consumer-specific delivery state. Store consumer progress
in SQLite and update the delivery record and offset in one transaction. The resulting model
must support independent consumers, monotonic offsets, deterministic concurrent ACK behavior,
and a safe migration from existing offset files.

## Implementation Intent
Add normalized consumer-delivery and consumer-offset tables (or an equivalent schema) that key
delivery/ack/offset state by `(consumer_id, event_id)` or `(consumer_id, seq)` rather than by
event row alone. Move `write_offset()`'s responsibility into the same SQLite connection/
transaction that `ack_event()` already uses, so both commit or roll back together. Provide an
additive, idempotent migration path from the existing `offsets_dir` files, and retain the
legacy files until migration completes and is verified.

## Target Files or Areas
- `scripts/eventbus/schema.sql`
- `scripts/eventbus/db.py`
- `scripts/eventbus/ack_route.py`
- `scripts/eventbus/offsets.py`
- `scripts/eventbus/subscribe_route.py`
- `docs/adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md`
- `docs/06_eventbus_04_dlq_offsets_and_delivery_semantics.md`

## Required Changes
- Define the canonical multi-consumer delivery-state model before changing runtime behavior.
- Add normalized consumer delivery and consumer offset tables, or an equivalent schema that
  preserves independent consumer state.
- Move offset persistence from files into SQLite.
- Update ACK processing so delivery state and consumer offset either commit together or roll
  back together (single transaction, not two independent writes).
- Enforce monotonic offset advancement atomically in SQL (not via a read-then-compare
  file-based check, per the current `write_offset()` pattern).
- Provide an additive, idempotent migration from existing `offsets_dir` and `.map` files.
- Retain legacy files until migration completes and verification succeeds.
- Update `docs/adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md` and
  `docs/06_eventbus_04_dlq_offsets_and_delivery_semantics.md` in the same change.

## Constraints
- Keep unrelated behavior unchanged (publish, replay, DLQ paths not in scope beyond their
  interaction with ACK/offset).
- Do not weaken fail-closed behavior, validation, or auditability.
- Use additive and idempotent database migrations for persisted data.
- Do not mark this issue complete with documentation-only changes when runtime behavior is
  defective.
- Do not invent configuration values, migration history, or approval evidence.

## Acceptance Criteria
- [ ] Two consumers can ACK the same event independently.
- [ ] ACK by one consumer does not mark another consumer's delivery as complete.
- [ ] ACK and offset advancement cannot diverge after a crash or file-system failure —
      confirmed by a test that forces the offset-write step to fail after the SQLite commit and
      asserts the two remain consistent (either both applied via retry/replay, or the ACK
      itself is rolled back).
- [ ] Concurrent ACK requests cannot move an offset backward.
- [ ] The migration is repeatable and does not destroy legacy state on failure.
- [ ] Focused unit, migration, restart, and concurrency tests pass.

## Testing Expectations
Add/update `tests/eventbus/test_eventbus_offsets.py`, `tests/eventbus/test_eventbus_ack_nack.py`,
`tests/eventbus/test_eventbus_crash_ack.py`, and `tests/eventbus/test_eventbus_restart_resume.py`
to cover multi-consumer independent ACK, transactional failure injection between the ACK commit
and offset write, and migration from legacy offset files. Run the complete EventBus test suite
and the repository's linting, type checking, and documentation consistency checks.

## Documentation Impact
Update `docs/adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md` and
`docs/06_eventbus_04_dlq_offsets_and_delivery_semantics.md` to describe the new per-consumer
delivery-state model as the canonical specification, replacing the current file-based-offset
description.

## Out of Scope
- Backpressure/duplicate-consumer-connection handling (tracked separately in this batch).
- DLQ requeue redelivery redesign (tracked separately in this batch).
- Authentication/authorization (tracked separately in this batch).

## Dependencies
N/A: none — this is a foundational schema change that later issues in this batch (notably the
DLQ retry-state redesign) may build on, but it does not itself depend on them.

## Unresolved Questions
N/A: none

## AI Implementation Instruction
This is a schema and persistence-model change, not a bug patch — confirm the migration path
preserves every currently-readable offset file before removing any legacy read path. Do not
delete `scripts/eventbus/offsets.py`'s file-based functions until the SQLite-backed replacement
is verified end-to-end and legacy-file migration is confirmed idempotent.
