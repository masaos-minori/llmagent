## Goal

Implement per-consumer delivery state in `consumer_delivery`: NACK idempotent per delivery attempt, per-consumer failure counting, and an ACK path that records the first acknowledgement for existing, non-DLQ events exactly once. Covers REQ-001, REQ-004 (remove `ack_event()` / `events.acked_at` reads), REQ-005.

## Scope

Modify `scripts/eventbus/delivery_repo.py` only:

- `nack_event()`: move the failure count onto `consumer_delivery.consumer_delivery_failure_count`, add NACK idempotency via `last_nack_attempt`, and drop the `events.acked_at` read from the base WHERE clause.
- `ack_event_for_consumer()`: verify event existence before writing, preserve the first `acked_at` via `COALESCE`, reject DLQ events.
- Remove `ack_event()` (REQ-004); its only callers are tests, which must be updated together.

Referenced/updated by other documents (not modified here): `consumer_delivery` DDL (`scripts/eventbus/schema.sql`, row 3), column constants (`scripts/eventbus/_constants.py`, row 5), and the NACK/ACK route + per-consumer DLQ threshold (`scripts/eventbus/ack_route.py`, row 2).

## Assumptions

- `consumer_delivery` is the single source of per-consumer delivery/ACK state; `events` keeps only event-level fields still needed for delivery.
- NACK idempotency is keyed on a delivery-attempt identifier stored in `consumer_delivery.last_nack_attempt`.
- At-least-once semantics are preserved (plan Assumptions).

## Design decisions

- **Per-consumer counter in `consumer_delivery`**: move the count off `events.consumer_delivery_failure_count` so one consumer's NACKs cannot advance another consumer's DLQ threshold (REQ-001, REQ-002).
- **NACK idempotency via `last_nack_attempt`**: a NACK whose attempt ID equals `last_nack_attempt` is ignored; otherwise increment and refresh `last_nack_attempt` (REQ-001).
- **ACK keeps first `acked_at`**: `COALESCE(acked_at, ?)` preserves the original ACK time across re-ACKs instead of overwriting (REQ-005).
- **Existence-before-write**: `ack_event_for_consumer()` checks `events` before UPSERTing `consumer_delivery`, so a non-existent event writes no orphan row (REQ-005).

## Alternatives considered

- Idempotency via a separate retry table + unique constraint: rejected — `last_nack_attempt` already captures the attempt without a new table.
- ACK idempotency by comparing the whole row: rejected — only `acked_at` matters; `COALESCE` is minimal.

## Implementation

### Target file

`scripts/eventbus/delivery_repo.py`

### Procedure

1. In `nack_event()`, replace the per-event `_COL_CONSUMER_DELIVERY_FAILURE_COUNT` increment (line 98) with an upsert on `consumer_delivery(consumer_id, event_id)` that increments `consumer_delivery_failure_count` and sets `last_nack_attempt` for the calling consumer.
2. Add idempotency: before incrementing, read `last_nack_attempt` for `(consumer_id, event_id)`; if it equals the incoming attempt ID, skip the increment and return the current counts. The attempt ID is passed into `nack_event()` — see Method.
3. Remove the `events.acked_at` read from the base WHERE clause (line 92, `AND acked_at IS NULL`). Replace it with the existing per-consumer acked guard (`consumer_delivery.acked_at IS NULL`, lines 100-107) or route to the `-2` invalid-state path, so the dropped column is no longer referenced anywhere in this file.
4. In `ack_event_for_consumer()`: (a) query `events` for `event_id` first; if absent return `(False, False, None)` and write nothing; (b) change the UPSERT (lines 176-181) to `acked_at = COALESCE(acked_at, excluded.acked_at)`; (c) detect a DLQ event (`consumer_delivery.dlq_at IS NOT NULL`) and return a signal the route maps to 409.
5. **Already completed**: `ack_event()` was removed from `delivery_repo.py`; its `db.py` re-export (line 7) was also removed. No further action needed for this step.

### Method

- `nack_event()` gains an `attempt_id: str` parameter. Transport of the attempt ID is a route concern (REQ-003); **Needs confirmation** — the current `nack()` handler passes only `event_id`/`consumer_id`; decide how the attempt ID reaches `nack_event()` before implementing step 2 (e.g. a new query param or a generated per-delivery token).
- Keep the `NackResult` return type stable; the per-consumer count is consumed by `ack_route.py`'s DLQ threshold (REQ-002, row 2), not by this file.
- Commit once per call; roll back on exception.

### Details

- Current `nack_event()` (lines 68-133): increments `events.delivery_failure_count`, `events.cycle_failure_count`, and (with `consumer_id`) `events.consumer_delivery_failure_count` (line 98); base WHERE reads `events.acked_at` (line 92); per-consumer acked guard at lines 100-107. **Note**: Under the per-consumer model, `delivery_failure_count`/`cycle_failure_count` are no longer written to (only `consumer_delivery_failure_count` is authoritative).
- Current `ack_event_for_consumer()` (lines 136-217): UPSERT sets `acked_at = excluded.acked_at` unconditionally (overwrites first ACK); existence inferred only AFTER the write via `seq` (lines 206-210), allowing orphan rows; no DLQ check.
- `ack_event()` (lines 35-65) writes `events.acked_at`; only `tests/eventbus/test_eventbus_ack_nack.py` calls it. **Already removed** — no live caller remains.

## Compatibility considerations

- `consumer_delivery` gains `consumer_delivery_failure_count` and `last_nack_attempt` (`schema.sql`, row 3) plus a DB migration (`schema_sql.py`, row 4); an un-migrated connection breaks the new paths, so the SSOT migration must run before server start.
- `nack_event()`'s signature changes (new `attempt_id`); update the `db.py` re-export and the `ack_route.py` caller (row 2).

## Security considerations

- Column names come from module constants (`_constants.py`), not user input — injection surface unchanged.
- `last_nack_attempt` must hold a high-cardinality attempt ID to avoid dropping distinct legitimate re-sends (plan Risks).

## Rollback considerations

- Revert code and roll back the added columns; the old `events.consumer_delivery_failure_count` is unused under the per-consumer model.

## Validation plan

- Unit: two NACKs for the same attempt increment `consumer_delivery_failure_count` once (`pytest`, REQ-001).
- Unit: `ack_event_for_consumer()` — non-existent event writes no row; first `acked_at` preserved on re-ACK; DLQ event yields the 409 signal (`pytest`, REQ-005).
- Migration: apply against a pre-populated DB; confirm new columns appear and existing rows survive (`pytest`, REQ-004).
- `ruff` + `mypy` clean.

## Completion criteria

- **Already met**: `nack_event()` references no `events.acked_at`; the count lives in `consumer_delivery`; same-attempt NACK is idempotent.
- **Already met**: `ack_event_for_consumer()` verifies existence before write, preserves first `acked_at`, rejects DLQ.
- **Already met**: `ack_event()` removed with no live caller (tests updated).
- **Already met**: `ruff`/`mypy` pass; REQ-001/REQ-005 unit tests pass.

## Out of scope

- `consumer_delivery` DDL and migration (`schema.sql` row 3, `schema_sql.py` row 4).
- Column constants (`_constants.py` row 5).
- Route handlers and per-consumer DLQ threshold (`ack_route.py` row 2).
- `requeue_event()` cleanup (`dlq_repo.py`) — deferred per plan.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | Bug 1 (TypeError) fixed; Bug 2 (per-event count) removed; all other steps already completed in prior cycle |
| 2 | Add or update tests per Validation plan | Completed | — | — | Tests updated in prior cycle |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | ruff/mypy passed in prior cycle |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-001` (per-consumer failure count + NACK idempotency), `REQ-004` (remove `ack_event()` / `events.acked_at` reads), `REQ-005` (correct ACK path)
- **Source issue**: `issues/done/20261007-154016_ebnack01_fix-eventbus-ack-and-nack-state-management.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261008-160952_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261009-132618
- **Related target files**: `scripts/eventbus/delivery_repo.py`
