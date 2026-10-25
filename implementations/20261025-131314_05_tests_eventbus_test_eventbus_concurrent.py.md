## Goal

Prove that concurrent requeue requests against the shared connection do not carry a failed transaction across requests (`REQ-002`), and that exactly one of many concurrent requeues succeeds while the rest get 409.

## Scope

- Modify `tests/eventbus/test_eventbus_concurrent.py`: extend `TestConcurrentDlqRequeue` with a mixed success/failure concurrency test.
- Do not modify `scripts/eventbus/dlq_repo.py` or `scripts/eventbus/dlq_route.py` — the transaction ownership and lock live there (seq-01 / seq-02).

## Assumptions

- The existing `test_concurrent_dlq_requeue` already fires 5 concurrent requeues and asserts exactly one success and four 409s (`REQ-002`).
- The shared connection is reachable via `eb_app.app.state.db`; `run_with_db_lock` serializes access to it.
- Under per-consumer gating, seeding `consumer_delivery_failure_count` at `max_retry - 1` and nacking once promotes the event to the DLQ for a single successful requeue.

## Design decisions

- **Keep the existing single-success concurrency test** and add a variant that interleaves an injected-failure requeue with normal ones, then asserts the connection stays usable and exactly one overall success occurs.
- **Assert `conn.in_transaction` is idle** after the concurrent storm, proving no failed transaction lingers on the shared connection.

## Alternatives considered

- Targeting the lock-serialized update/insert: rejected — that path is already serialized by `run_with_db_lock`; the residual risk is the unlocked transaction carry-over, which this test targets.

## Implementation

### Target file

`tests/eventbus/test_eventbus_concurrent.py`

### Procedure

1. Keep `test_concurrent_dlq_requeue` unchanged (one success, four 409s, `new_seq > original_seq`, valid `new_event_id`).
2. Add `test_concurrent_dlq_requeue_no_failed_transaction_carryover (new)`: seed and promote one event, fire a mix of requeues where one is patched to fail on the redelivery INSERT, assert exactly one overall success, all others 409, and the shared connection is idle afterward.

### Method

```python
class TestConcurrentDlqRequeue:
    def test_concurrent_dlq_requeue_no_failed_transaction_carryover(
        self, client: TestClient, tmp_path: Path
    ) -> None:
        import sqlite3
        from unittest import mock

        import eventbus.app as eb_app

        body = {**_event("dlq"), "event_id": str(uuid.uuid4())}
        resp = client.post("/publish", json=body)
        assert resp.status_code == 200
        event_id = body["event_id"]
        original_seq = resp.json()["seq"]

        db = eb_app.app.state.db
        cfg = eb_app.app.state.config
        db.execute(
            "DELETE FROM consumer_delivery WHERE consumer_id = ? AND event_id = ?",
            ("consumer-A", event_id),
        )
        db.execute(
            "INSERT INTO consumer_delivery "
            "(consumer_id, event_id, acked, consumer_last_nack_attempt, "
            "consumer_delivery_failure_count) VALUES ('consumer-A', ?, 0, 'seeded-attempt', ?)",
            (event_id, cfg.max_retry - 1),
        )
        db.commit()
        client.post("/nack", params={"event_id": event_id, "consumer_id": "consumer-A"})

        real_execute = db.execute

        def _failing_execute(sql, *args, **kwargs):
            if "INSERT" in str(sql).upper():
                raise sqlite3.IntegrityError("injected insert failure")
            return real_execute(sql, *args, **kwargs)

        results: list[dict[str, Any]] = []

        async def _requeue() -> None:
            with mock.patch.object(db, "execute", side_effect=_failing_execute):
                resp = client.post(f"/dlq/{event_id}/requeue")
            results.append(resp.json())

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(asyncio.gather(*(_requeue() for _ in range(5))))
        finally:
            loop.close()

        requeued = [r for r in results if r.get("requeued") is True]
        assert len(requeued) == 1
        assert len([r for r in results if r.get("detail") == "event is not in DLQ"]) == 4

        # No failed transaction lingered on the shared connection.
        assert db.in_transaction is False
```

> Note: the exact promotion seed differs per current test; reuse the pattern already present in `test_concurrent_dlq_requeue` (seed `consumer_delivery_failure_count = max_retry - 1`, nack once). The injected-failure wrapper must patch the shared connection the route uses under `run_with_db_lock`.

### Details

- All 5 concurrent requests share the injected-failure wrapper; only the first to acquire the lock performs the INSERT (which fails), the rest see the event already removed from the DLQ and return 409. The assertion is that the shared connection ends idle (`db.in_transaction is False`) despite the failures.
- The success response still carries a valid `new_event_id` and integer `new_seq` greater than `original_seq`.

## Compatibility considerations

- Adds a new test method to an existing class; existing methods are untouched. Requires the seq-01 transaction behavior to exist.

## Security considerations

- No change: concurrency and injection are confined to the test's own database.

## Rollback considerations

- Remove `test_concurrent_dlq_requeue_no_failed_transaction_carryover (new)`.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/eventbus/test_eventbus_concurrent.py` | Integration: concurrent requeue, no failed-transaction carry-over | `uv run pytest tests/eventbus/` | Exactly one success, rest 409, shared connection idle |
| `scripts/eventbus/*` | Static analysis | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `uv run bandit -r scripts/ -c pyproject.toml -ll`, `PYTHONPATH=scripts uv run lint-imports` | Clean |

## Completion criteria

- `test_concurrent_dlq_requeue` asserts one success, four 409s, valid `new_event_id`, and `new_seq > original_seq`.
- `test_concurrent_dlq_requeue_no_failed_transaction_carryover (new)` asserts one success, an idle shared connection, and a usable follow-up request.

## Out of Scope

- Failure-injection rollback detail — handled by the sibling procedure for `test_eventbus_requeue_edge_cases.py` (`REQ-002`).
- Snapshot and pagination coverage — sibling procedures.

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
- **Requirement ID**: `REQ-002` (no failed-transaction carry-over on the shared connection under concurrency)
- **Source issue**: `issues/20261023-154325_eventbus001_dlq-requeue-transactional.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261025-095644_eventbus001_dlq-requeue-transactional.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261025-131314
- **Related target files**: `tests/eventbus/test_eventbus_concurrent.py`
