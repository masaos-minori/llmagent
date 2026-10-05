## Goal

Add a per-consumer "already ACKed" guard to `nack_event()` so that a NACK from consumer C for event E, when C has already ACKed E, returns the invalid-transition sentinel (`NackResult(-2, -2)`) without incrementing any failure counters (`REQ-001`, `REQ-002`). Leave the `consumer_id is None` path unchanged.

## Scope

**In**:
- Modify `scripts/eventbus/delivery_repo.py` only — add a `NOT EXISTS` subquery on `consumer_delivery` bound to `consumer_id` to the UPDATE's WHERE clause when `consumer_id` is provided; keep the existing not-found/invalid-state result handling.

**Out**:
- No changes to the `consumer_id is None` path of `nack_event()`.
- No schema change — `consumer_delivery` already holds the per-consumer ACK state with a primary key on `(consumer_id, event_id)`.
- No changes to call sites (`ack_route.py`, `eventbus.db` facade).
- No test authoring here — tests owned by the paired doc `20261005-151801_03_tests_eventbus_test_eventbus_ack_nack_py.md`.

## Assumptions

1. "Already ACKed" means ACKed by the requesting consumer (per-consumer semantics), not by any consumer. This follows the Issue's recommendation and the Plan's decision gate (UNK-01).
2. The `consumer_delivery` table already has `acked_at` and a primary key on `(consumer_id, event_id)` — confirmed by `schema.sql` lines 26–31.
3. The existing `NackResult(-2, -2)` sentinel for invalid transitions is retained; the route maps it to HTTP 409.
4. Retaining the existing follow-up SELECT (lines 104–110) to distinguish not-found (-1) from invalid transition (-2) is required.

## Design decisions

- Add a `NOT EXISTS` subquery on `consumer_delivery` bound to `consumer_id` inside the UPDATE's WHERE clause when `consumer_id` is provided. This makes the check atomic with the counter update — no counter can change on rejection.
- When the UPDATE matches no row and the follow-up SELECT finds the event exists, return `NackResult(-2, -2)` (invalid transition).
- The `consumer_id is None` path keeps its current events-level-only behavior (no `consumer_delivery` check).

## Alternatives considered

- **Separate SELECT before UPDATE**: Rejected — introduces a TOCTOU race between the check and the counter update.
- **UPDATE with a CASE expression returning a flag**: Rejected — SQLite does not support returning a value from UPDATE; the existing pattern of checking `rowcount` + follow-up SELECT is the correct approach.
- **Global "already ACKed" (any consumer)**: Rejected — the Issue recommends per-consumer semantics; global semantics would require additional design work.

## Implementation

### Target file

`scripts/eventbus/delivery_repo.py`

### Procedure

Add a `NOT EXISTS` subquery on `consumer_delivery` bound to `consumer_id` to the UPDATE's WHERE clause when `consumer_id` is provided; keep the existing not-found/invalid-state result handling. Do not change the `consumer_id is None` path.

### Method

Modify the `where_clause` construction in `nack_event()` to include a `NOT EXISTS` condition when `consumer_id` is provided.

### Details

Before (lines 91–93):
```python
where_clause = (
    f"{_COL_EVENT_ID} = ? AND {_COL_ACKED_AT} IS NULL AND {_COL_DLQ_AT} IS NULL"
)
```

After (when `consumer_id is not None`):
```python
where_clause = (
    f"{_COL_EVENT_ID} = ? AND {_COL_ACKED_AT} IS NULL AND {_COL_DLQ_AT} IS NULL "
    f"AND NOT EXISTS ("
    f"  SELECT 1 FROM consumer_delivery "
    f"  WHERE consumer_delivery.consumer_id = ? "
    f"  AND consumer_delivery.event_id = ? "
    f"  AND consumer_delivery.acked_at IS NOT NULL"
    f")"
)
params = [event_id, consumer_id, event_id]
```

When `consumer_id is None`, the original `where_clause` and `params` are unchanged.

Behavior after the change:
- Consumer C ACKs event E → `consumer_delivery.acked_at` is set for `(C, E)`.
- Consumer C sends NACK for event E → UPDATE matches no row (the `NOT EXISTS` subquery fails), `rowcount == 0`, follow-up SELECT finds the event exists → `NackResult(-2, -2)` returned.
- Consumer D (different consumer) sends NACK for event E → `NOT EXISTS` subquery succeeds (D has not ACKed), UPDATE proceeds normally, counters incremented.
- `consumer_id is None` → original behavior unchanged.

## Compatibility considerations

- No public-API change: `nack_event()` signature and return type (`NackResult`) are unchanged.
- The `NackResult(-2, -2)` sentinel is retained; the route maps it to HTTP 409.
- Callers that rely on the existing `delivery_failure_count` / `cycle_failure_count` values on success are unaffected (they only see the new behavior when the UPDATE matches no row).
- `eventbus.db` facade re-exports `nack_event`; its callers inherit the fix transitively.

## Security considerations

- This change directly addresses a security concern: spurious failure counts and possible DLQ promotion of events that consumers have already processed. The fix ensures that a consumer cannot drive DLQ promotion of an event it has already ACKed.
- No new attack surface introduced — the check is a simple `NOT EXISTS` subquery on an existing table.
- The fix does not introduce any new dependencies or external calls.

## Rollback considerations

- If the change causes unexpected issues, reverting the WHERE clause modification restores the original behavior. The patterns themselves are unchanged, so the rollback is a targeted revert of the WHERE clause change.
- Downstream consumers that rely on the old behavior (e.g., accepting NACKs after ACK) may need adjustment if they expect the old behavior.

## Validation plan

- Run the validation sequence on `scripts/eventbus/delivery_repo.py`: `ruff format/check`, `mypy`, `bandit`.
- Run the new test module: `uv run pytest tests/eventbus/test_eventbus_ack_nack.py -v`.
- Confirm existing tests still pass: `uv run pytest tests/eventbus -v`.

## Completion criteria

- A NACK from consumer C for event E, when C has already ACKed E, returns `NackResult(-2, -2)` (invalid transition).
- `delivery_failure_count`, `cycle_failure_count` and `consumer_delivery_failure_count` are unchanged after the rejected NACK.
- Consumer D (different consumer) can still NACK event E (counters incremented).
- `consumer_id is None` path keeps its current behavior.
- Existing tests pass unchanged.
- `ruff format/check`, `mypy`, `bandit` clean on `scripts/eventbus/delivery_repo.py`.

## Out of scope

- Adding patterns for non-`key=value` credential forms (`Authorization: Bearer ...`, `Cookie`, etc.).
- Introducing a general log-redaction framework.
- Changes to call sites (`http_lifecycle.py`, `http_lifecycle_errors.py`, `startup_mcp_starter.py`, `retry_helper.py`).
- Test authoring — covered by the paired doc `20261005-151801_03_tests_eventbus_test_eventbus_ack_nack_py.md`.

## Execution Status

### Execution Status

| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261005-163034 | 20261005-163034 | REQ-001, REQ-002 |
| 2 | Add or update tests per Validation plan | Completed | 20261005-163040 | 20261005-163040 | Tests owned by paired doc |
| 3 | Run the validation sequence (`rules/toolchain.md`) incl. `TestStartupOrchestratorRecoverPendingApprovals` | Completed | 20261005-163040 | 20261005-163040 | Cross-row dependency: implement paired test doc first so assertions reflect gated behavior |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261005-163040 | 20261005-163040 | N/A: doc update covered by paired doc `20261005-151801_04_docs_24_eventbus_eventbus_03_dlq_operations_md.md` |

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
- **Requirement ID**: `REQ-001` — reject NACK when same consumer ACKed; `REQ-002` — per-consumer check atomic with counter update
- **Source issue**: issues/20261005-102244_eb002_eventbus-nack-accepted-after-per-consumer-ack.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261005-103619_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261005-151801
- **Related target files**: scripts/eventbus/delivery_repo.py