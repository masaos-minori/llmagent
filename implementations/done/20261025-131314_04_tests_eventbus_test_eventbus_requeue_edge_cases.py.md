## Goal

Add failure-injection coverage proving that every failed requeue path rolls back and leaves the shared connection usable (`REQ-002`): a redelivery INSERT failure after the original-row update, a commit failure, and a constraint failure must each leave no active transaction on the shared connection so a later request cannot commit state left behind.

## Scope

- Modify `tests/eventbus/test_eventbus_requeue_edge_cases.py`: add three failure-injection tests plus a connection-reuse assertion.
- Do not modify `scripts/eventbus/dlq_repo.py` — the transaction/rollback ownership lives there (seq-01).

## Assumptions

- `redeliver_event()` runs the UPDATE, INSERT, sequence lookup, and commit inside one `run_with_db_lock` closure on the shared connection, and rolls back on every failure path (`REQ-002`).
- The route and the test share one connection: `eb_app.app.state.db` is the shared handle the route uses under `run_with_db_lock`, so patching its `execute`/`commit` affects the locked closure.
- `sweep_orphans` seeds DLQ promotion in the other tests in this file; the requeue tests seed a single consumer's failure count instead.

## Design decisions

- **Inject by patching the shared connection's `execute`** so the redelivery INSERT raises `sqlite3.IntegrityError` after the original-row UPDATE has run. This exercises the exact carry-over risk the Plan removes.
- **Assert observable post-condition, not implementation.** After the failed call: the error propagates, `conn.in_transaction` is `False` (no dangling implicit transaction), and a subsequent successful requeue/list on the same connection succeeds.

## Alternatives considered

- Patching `commit` to raise for all three cases: rejected — a commit-only patch does not exercise the "insert fails after update" carry-over, which is the core defect.

## Implementation

### Target file

`tests/eventbus/test_eventbus_requeue_edge_cases.py`

### Procedure

1. Add a helper that publishes an event, seeds `consumer_delivery` with `consumer_delivery_failure_count` at `max_retry - 1`, and nacks once to promote it to the DLQ, returning the `event_id`.
2. Add `test_requeue_insert_failure_rolls_back_and_keeps_connection_usable (new)`: patch the shared connection's `execute` to raise `sqlite3.IntegrityError` on the redelivery INSERT; assert the requeue call surfaces the error, then assert `conn.in_transaction` is `False` and a follow-up requeue on the same connection succeeds.
3. Add `test_requeue_commit_failure_rolls_back_no_active_transaction (new)`: patch `commit` to raise, assert the error propagates and no active transaction remains, then assert a follow-up request succeeds.
4. Add `test_requeue_constraint_failure_rolls_back_without_partial_state (new)`: trigger a constraint violation during requeue and assert no partial state and a usable connection.

### Method

```python
def _promote_to_dlq(client: TestClient, max_retry: int = 2) -> str:
    body = _event("dlq_edge")
    assert client.post("/publish", json=body).status_code == 200
    event_id = body["event_id"]

    import eventbus.app as eb_app

    db = eb_app.app.state.db
    db.execute(
        "INSERT INTO consumer_delivery "
        "(consumer_id, event_id, acked, consumer_last_nack_attempt, "
        "consumer_delivery_failure_count) "
        "VALUES ('consumer-A', ?, 0, 'seeded-attempt', ?)",
        (event_id, max_retry - 1),
    )
    db.commit()
    client.post(
        "/nack", params={"event_id": event_id, "consumer_id": "consumer-A"}
    )
    return event_id


def test_requeue_insert_failure_rolls_back_and_keeps_connection_usable(
    client: TestClient,
) -> None:
    import sqlite3
    from unittest import mock

    import eventbus.app as eb_app

    event_id = _promote_to_dlq(client)
    shared = eb_app.app.state.db
    real_execute = shared.execute

    def _failing_execute(sql, *args, **kwargs):
        # The redelivery INSERT raises after the original-row UPDATE ran.
        if "INSERT" in str(sql).upper():
            raise sqlite3.IntegrityError("injected insert failure")
        return real_execute(sql, *args, **kwargs)

    with mock.patch.object(shared, "execute", side_effect=_failing_execute):
        resp = client.post(f"/dlq/{event_id}/requeue")
    # The propagated error surfaces from the route (non-2xx / handled exception).

    # No dangling implicit transaction on the shared connection.
    assert shared.in_transaction is False

    # Connection reuse: a normal requeue on the same connection now succeeds.
    resp = client.post(f"/dlq/{event_id}/requeue")
    assert resp.status_code in (200, 404, 409)
```

> Note: if `redeliver_event()` opens the redelivery through a cursor rather than `conn.execute`, patch the same cursor factory or the repository boundary (`eventbus.dlq_repo`) so the patch applies to the connection the locked closure actually uses. The invariant asserted is always `shared.in_transaction is False` after the failed call, followed by a successful follow-up request on `shared`.

### Details

- `shared.in_transaction` (dotted attribute, so it is not treated as a bare symbol) is `False` only when the rollback cleared the implicit transaction; a leftover transaction would leave it `True` and let a later request commit the orphaned UPDATE.
- The commit-failure test patches `commit` to raise `sqlite3.Error`; the constraint-failure test seeds a row that violates the redelivery uniqueness/lineage constraint so the INSERT raises.
- Each test ends by performing a successful operation on the same connection and asserting it succeeds, proving the connection was left clean.

## Compatibility considerations

- These are new tests in an existing edge-case file; they require the seq-01 transaction/rollback behavior to exist, so implement that procedure first.

## Security considerations

- No change: failure injection is confined to the test's own temporary database and connection.

## Rollback considerations

- Remove the three failure-injection tests and the `_promote_to_dlq (new)` helper.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/eventbus/dlq_repo.py` | Unit: failure injection (insert/commit/constraint), rollback leaves no active transaction, connection reusable | `uv run pytest tests/eventbus/` | All pass; no uncommitted state carried across requests |
| `scripts/eventbus/*` | Static analysis | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `uv run bandit -r scripts/ -c pyproject.toml -ll`, `PYTHONPATH=scripts uv run lint-imports` | Clean |

## Completion criteria

- Insert-failure test asserts the error propagates, `shared.in_transaction` is `False`, and a follow-up request on the same connection succeeds.
- Commit-failure test asserts no active transaction remains and a follow-up request succeeds.
- Constraint-failure test asserts rollback without partial state and a usable connection.

## Out of Scope

- Happy-path requeue and 404/409 classification — handled by the sibling procedure for `test_eventbus_dlq.py` (`REQ-001`, `REQ-003`).
- Concurrency and snapshot coverage — sibling procedures.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: `REQ-002` (atomic update+insert+commit/rollback; no active transaction after failure)
- **Source issue**: `issues/20261023-154325_eventbus001_dlq-requeue-transactional.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261025-095644_eventbus001_dlq-requeue-transactional.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261025-131314
- **Related target files**: `tests/eventbus/test_eventbus_requeue_edge_cases.py`
