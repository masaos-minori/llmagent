## Goal

Implement `REQ-003` (atomic NACK handling + state determination) and `REQ-004`
(remove the `events.acked_at` reference in the NACK rejection path) in
`scripts/eventbus/ack_route.py`, so that a NACK and its invalid-transition state
determination happen in one lock acquisition/transaction, and the rejection path no
longer reads the `events.acked_at` column that `REQ-004` removes.

## Scope

Modifies `scripts/eventbus/ack_route.py` only. References
`scripts/eventbus/delivery_repo.py` (`nack_event`, `ack_event_for_consumer`) and
`scripts/eventbus/dlq.py` (`promote_single`) as call-path dependencies. See Design
decisions for coordination with the `delivery_repo.py` and `dlq.py` rows.

## Assumptions

- `ack_route.ack_event` (line 105) and `app.ack_event` (app.py:251) are the ACK route
  handler and MUST NOT be removed — only `delivery_repo.ack_event` (the
  `acked_at` writer) is removed by `REQ-004`.
- Per-consumer ACK state now lives in `consumer_delivery.acked_at`; the old
  `events.acked_at` read in the `-2` branch is obsolete.
- `nack()` remains the single NACK entry point; `_nack_and_promote()` performs the
  increment under the DB lock.

## Design decisions

- Fold the `-2` invalid-transition state determination into the same lock
  acquisition/transaction as the NACK increment so the state snapshot is atomic with
  the increment (eliminates the delete-in-between race, `EVENTBUS-011`).
- In the `-2` branch, determine "already acknowledged" solely from
  `consumer_delivery.acked_at` (per-consumer) and "in DLQ" from `events.dlq_at`;
  drop the `events.acked_at` read entirely.
- Keep the 404 (not found, `-1`) vs 409 (invalid transition) distinction.

## Alternatives considered

- Leaving the `-2` check in separate `run_with_db_lock` calls — rejected: the state
  is read after the NACK returns, so a concurrent delete/ack between the two lock
  acquisitions yields a wrong status (`EVENTBUS-011`).
- Reading `events.acked_at` in the `-2` branch — rejected: the column is removed by
  `REQ-004`.

## Implementation

### Target file

`scripts/eventbus/ack_route.py`

### Procedure

1. `REQ-003` — Rework `nack()` so the `-2` state determination runs inside the same
   lock acquisition/transaction as the `nack_event()` increment in
   `_nack_and_promote()`. Instead of returning `-2` and re-reading state in separate
   `run_with_db_lock` calls (lines 178-192), resolve the transition within the
   locked NACK operation and return the concrete status (not-found / already-acked /
   in-DLQ / promoted).
2. `REQ-004` — Remove the `SELECT acked_at, dlq_at FROM events` read and the
   `row["acked_at"] is not None` 409 branch (lines 187-194). Determine
   "already acknowledged" from `consumer_delivery.acked_at` and "in DLQ" from
   `events.dlq_at` only.
3. Preserve the authorization guard (lines 133-146) and the `promote_single` call
   (lines 165-168) unchanged except for the failure-count source if the `dlq.py` row
   changes promotion to per-consumer (`REQ-002`).

### Method

- Locate: `rg -n 'async def nack|def _nack_and_promote|async def ack_event|def _do_ack' scripts/eventbus/ack_route.py`. Current: `_do_ack` 30, `ack_event` 105, `nack` 118, `_nack_and_promote` 151.
- Read the `nack()` body (118-200) to map the current `-1`/`-2` control flow and the two separate `run_with_db_lock` calls in the `-2` branch.
- Confirm `delivery_repo.nack_event` returns the counts used for promotion gating before changing the failure-count source.
- Lint and test: `ruff`, `mypy --no-namespace-packages`, `bandit`, `lint-imports`, then `pytest tests/eventbus/test_eventbus_ack_nack.py`.

### Details

- The combined locked operation must return enough signal for `nack()` to pick 404 vs 409 and to detect DLQ membership. Consider returning a small result tuple/enum from the locked closure rather than sentinel counts.
- If `REQ-002` makes promotion per-consumer, `_nack_and_promote()` must pass `consumer_id` to the promotion decision; coordinate with the `dlq.py` row's `promote_single` signature change.

## Compatibility considerations

- The `-2` branch behavior changes from "read `events.acked_at` then `dlq_at`" to
  "read `consumer_delivery.acked_at` then `events.dlq_at`". Ensure callers/tests that
  assert 409 semantics are updated.
- No change to the ACK route handler or authorization guards.

## Security considerations

- The atomic combined operation closes the race window an attacker could otherwise
  exploit to force a misleading 409/404; keep it under the single DB lock.
- Parameterized SQL; column names from `_constants.py`.

## Rollback considerations

- Revert the `nack()` control flow to the pre-change two-lock structure and restore
  the `events.acked_at` read (which coexists with the column until the `schema.sql`
  row drops it).

## Validation plan

- Integration: a NACK on an already-acked event returns 409 deterministically even
  under a concurrent delete/ack (`REQ-003`); a NACK on a non-existent event returns
  404; a NACK on a DLQ'd event returns 409 (`REQ-004`).
- `tests/eventbus/test_eventbus_ack_nack.py` and any NACK-transition tests.
- `ruff`, `mypy --no-namespace-packages`, `bandit`, `lint-imports`.

## Completion criteria

- No code path in `ack_route.py` reads `events.acked_at`.
- The `-2` state determination executes within the same lock/transaction as the
  NACK increment.
- 404/409 responses remain correct for not-found / already-acked / in-DLQ cases.

## Out of scope

- Removing `delivery_repo.ack_event()` and its test callers (`delivery_repo.py` row).
- `events.acked_at` DDL drop (`schema.sql` / `schema_sql.py` rows).
- DLQ promotion source change (`dlq.py` row) — coordinate only.

## Execution Status

| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement REQ-003/REQ-004 changes in ack_route.py | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation | N/A | — | — | Docs handled by REQ-006 rows |

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
- **Requirement ID**: `REQ-003`, `REQ-004`
- **Source issue**: `issues/done/20261007-154016_ebnack01_fix-eventbus-ack-and-nack-state-management.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261008-160952_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261009-071937
- **Related target files**: `scripts/eventbus/ack_route.py`
