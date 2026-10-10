## Goal

Implement `REQ-001` (NACK idempotency keyed on the delivery attempt) and `REQ-005`
(correct `ack_event_for_consumer()` ACK decisions) in
`scripts/eventbus/delivery_repo.py`, so that a repeated NACK for the same delivery
attempt is counted once and ACKs record the first acknowledgement time without
creating orphan `consumer_delivery` rows or ACKing events already in the DLQ.

## Scope

Modifies `scripts/eventbus/delivery_repo.py` only. References
`scripts/eventbus/_constants.py` (new `_COL_LAST_NACK_ATTEMPT`),
`scripts/eventbus/schema.sql` and `scripts/db/schema_sql.py` (new-column DDL), and
`tests/eventbus/test_eventbus_ack_nack.py` (existing `ack_event` cases). See
Design decisions for cross-row coordination with the `ack_route.py`, `schema.sql`,
`schema_sql.py`, and `_constants.py` rows.

## Assumptions

- Delivery is at-least-once; duplicate NACK/ACK re-sends are routine and must stay safe.
- `consumer_delivery` is the single per-consumer delivery-state model; there is no
  event-level ACK state.
- The last-NACK-attempt identity can be derived from a monotonic per-delivery value
  (e.g. `consumer_offsets.offset` or a generation number). The source issue leaves
  this open ("last NACKed delivery-attempt ID (or generation number)") — resolve it
  and, if it changes the data model, treat it as a Plan revision.
- Removing `ack_event()` removes its only remaining callers in
  `tests/eventbus/test_eventbus_ack_nack.py` (lines 49-130).

## Design decisions

- NACK idempotency keys on `consumer_delivery.last_nack_attempt`: a NACK whose
  attempt identity equals the stored value skips the failure-count increment
  (count once) while still returning a valid result. The exact attempt identity is
  an open point in the source issue — confirm it before coding.
- `ack_event_for_consumer()` verifies event existence BEFORE upserting
  `consumer_delivery` (no orphan rows on miss), preserves the first `acked_at` via
  COALESCE semantics (do not overwrite via `ON CONFLICT DO UPDATE`), and rejects
  ACKs for events already in the DLQ (409 via `events.dlq_at`).
- `ack_event()` (the `events.acked_at` writer) is removed per `REQ-004`; its test
  callers are updated/removed accordingly.

## Alternatives considered

- Counting every NACK (current behavior) — rejected: double-counts re-sends and lets
  one consumer exhaust the shared DLQ budget (`EVENTBUS-012`).
- Keeping `ack_event()` — rejected: it writes the `events.acked_at` column that
  `REQ-004` removes.

## Implementation

### Target file

`scripts/eventbus/delivery_repo.py`

### Procedure

1. `REQ-001` — In `nack_event()`, when `consumer_id` is provided, track the current
   delivery-attempt identity in `consumer_delivery.last_nack_attempt` and skip the
   failure-count increment when a NACK repeats the stored attempt (idempotent).
   Preserve the existing `NOT EXISTS` per-consumer ACK guard added by commit
   `3ba1dd495`.
2. `REQ-005` — In `ack_event_for_consumer()`: (a) verify the event exists in
   `events` BEFORE upserting `consumer_delivery` and return `(False, False, None)`
   with no write on miss; (b) keep the first `acked_at` by setting it only when
   currently NULL (COALESCE, not `DO UPDATE` overwrite); (c) return 409 for events
   already in the DLQ (check `events.dlq_at`).
3. `REQ-004` — Remove `ack_event()` (the `events.acked_at` writer, lines 35-65) and
   its `eventbus.db` export. Update `tests/eventbus/test_eventbus_ack_nack.py`
   import/usage of `ack_event` (lines 49-130) to remove or replace those cases.

### Method

- Locate functions: `rg -n 'def ack_event|def nack_event|def ack_event_for_consumer' scripts/eventbus/delivery_repo.py`. Current bodies: `ack_event` 35-65, `nack_event` 68-133, `ack_event_for_consumer` 136-217.
- Verify `ack_event()` callers before removal: `rg -n '\back_event\b' scripts/ tests/`. Current callers are the `eventbus.db` export and `tests/eventbus/test_eventbus_ack_nack.py:49-130`. No production caller remains — `ack_route.ack_event` (line 105) and `app.ack_event` (app.py:251) are the route handler, a distinct function that MUST NOT be removed.
- Add the idempotency skip inside the existing `consumer_id` branch of `nack_event()` (lines 96-108).
- Rework `ack_event_for_consumer()` ordering: existence check → conditional `acked_at` write → DLQ check → offset advance.
- Lint and test: `ruff`, `mypy --no-namespace-packages`, `bandit`, `lint-imports`, then targeted `pytest tests/eventbus/test_eventbus_ack_nack.py`.

### Details

- `nack_event()` returns `NackResult(delivery_failure_count, cycle_failure_count)`. The idempotency skip must not increment counts on a repeated attempt but must still return a result consistent with `ack_route._nack_and_promote`'s handling of `-1`/`-2`.
- `ack_event_for_consumer()` currently returns `(found, newly_acked, seq)`; extend the not-found path to write nothing and the DLQ path to signal 409 to the caller (`ack_route.ack_event`).
- Read `_COL_LAST_NACK_ATTEMPT` from `_constants.py` (added by the `_constants.py` row) — do not hardcode the column string.

## Compatibility considerations

- Dropping `ack_event()` changes the `eventbus.db` public export; update
  `tests/eventbus/test_eventbus_ack_nack.py` imports. No production caller depends on it.
- `consumer_delivery_failure_count` currently lives on the `events` table (added by
  `schema.py::_migrate`), not on `consumer_delivery`. The source issue intends it in
  `consumer_delivery`. Confirm placement with the `REQ-002` / ADR-006 decision before
  relying on it for promotion.

## Security considerations

- Idempotency must not be bypassable by replaying a NACK to inflate another
  consumer's DLQ view; the attempt-keyed skip is scoped to `(consumer_id, event_id)`.
- Keep parameterized SQL; column names come from `_constants.py` constants.

## Rollback considerations

- The `nack_event()` change is additive (idempotency guard) and
  `ack_event_for_consumer()` is reordered; revert by restoring the prior bodies.
- Removing `ack_event()` requires re-adding it plus the `acked_at` test cases if
  rolled back.

## Validation plan

- Unit: same NACK twice increments once (`REQ-001`); ACK for non-existent event
  writes no row (`REQ-005`); first ACK time preserved; DLQ event ACK rejected
  (`REQ-005`).
- Run `tests/eventbus/test_eventbus_ack_nack.py` after removing/replacing the
  `ack_event` cases.
- `ruff`, `mypy --no-namespace-packages`, `bandit`, `lint-imports`.

## Completion criteria

- `nack_event()` ignores a NACK repeating the stored `last_nack_attempt` (count once).
- `ack_event_for_consumer()` writes nothing for a non-existent event, preserves the
  first `acked_at`, and rejects DLQ events.
- No remaining reference to `delivery_repo.ack_event()`; dependent test imports updated.

## Out of scope

- `events.acked_at` DDL drop (`schema.sql` / `schema_sql.py` rows) and the
  `ack_route.py` `-2` branch update (`ack_route.py` row) are separate rows.
- DLQ promotion logic (`dlq.py` row) and documentation (`REQ-006` rows).
- `schema.py::_migrate` migration for dropping `acked_at` from existing databases is
  an additional target file not listed in the Plan's `Implementation Target Files`
  (see Plan Gap in the progress report).

## Execution Status

| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement REQ-001/REQ-005/REQ-004 changes in delivery_repo.py | Completed | 2026-10-09 | 2026-10-09 | `ack_event_for_consumer()` now returns 4-tuple `(found, newly_acked, seq, dlq)`; existence-first (no orphan rows), COALESCE `acked_at`, DLQ→`dlq=True`; `ack_event()` removed; per-consumer NACK idempotency via `_is_repeat_nack`/`_record_consumer_nack`/`_current_failure_counts` |
| 2 | Add or update tests per Validation plan | Completed | 2026-10-09 | 2026-10-09 | Removed 4 `ack_event` tests; updated 5 direct `ack_event_for_consumer` call sites to 4-value unpacking; added REQ-001 repeat-count and REQ-005 (not-found/DLQ/first-acked_at/reset) direct tests |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-10-09 | 2026-10-09 | ruff/mypy/lint-imports/bandit clean on changed files; 13 direct unit tests pass. NOTE: `ack_route.py:74` mypy error + HTTP ack tests fail pending file 02 (see Blocker Log) |
| 4 | Update documentation | N/A | — | — | Docs handled by REQ-006 rows |

### Blocker Log

| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 3 | `ack_route.py` still unpacks the old 3-tuple from `ack_event_for_consumer()` → mypy error at line 74 + HTTP ack tests raise `ValueError: too many values to unpack (expected 3, got 4)`. Coupled change owned by file 02 (`ack_route.py`). Source changes held uncommitted until file 02 completes. | No | — |

### Work Items Created

| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability

- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-001`, `REQ-005`
- **Source issue**: `issues/done/20261007-154016_ebnack01_fix-eventbus-ack-and-nack-state-management.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261008-160952_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261009-071937
- **Related target files**: `scripts/eventbus/delivery_repo.py`
