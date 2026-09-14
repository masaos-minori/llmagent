# Implementation Procedure: Add concurrent requeue tests; verify atomic behavior under contention

## Goal

Add concurrent requeue tests to `tests/eventbus/test_eventbus_dlq.py` to verify deterministic DLQ transitions under concurrent execution, covering REQ-003 acceptance criteria.

## Scope

- Add test for concurrent requeue of the same event producing exactly one successful redelivery (REQ-003).
- Add test for concurrent requeue of different events both succeeding independently (REQ-003).
- Verify existing single-threaded requeue test returns correct `new_event_id` and `new_seq` (REQ-002).
- Verify existing HTTP 409/404 tests still pass after the shared-lock fix (REQ-001).

## Assumptions

- A: The `redelivered_from` existence check in `redeliver_event()` provides a concurrency guard against duplicate redeliveries — confirmed by `db.py:516-521`.
- B: `run_with_db_lock()` acquires and releases a shared SQLite lock around the callback — confirmed by `route_helpers.py` usage pattern.
- C: The current `dlq_requeue()` function fetches `new_seq` outside the lock (lines 78-83) — confirmed by `dlq_route.py:78-83`.
- D: The `redeliver_event()` function returns `(success, new_event_id)` but NOT `new_seq` — confirmed by `db.py:510-512`.
- E: `EVENTBUS-002` concerns `/replay?format=json` pagination format documentation — confirmed by `docs/00_governance_03_issue-and-uncertainty-management.md:185-202`.
- F: The `docs/eventbus/` directory does not exist yet — confirmed by filesystem check.

## Design decisions

- **Concurrent test via asyncio**: Use `asyncio.gather()` to simulate concurrent requests since the test client runs synchronously and FastAPI routes are async.
- **Deterministic assertion**: Assert exactly one success among concurrent attempts rather than checking for "at least one" — this validates the atomicity guarantee.
- **Separate fixtures per scenario**: Each concurrent test uses its own fixture to avoid cross-test interference.

## Alternatives considered

- **Threading-based concurrency**: Use Python threading instead of asyncio. Rejected because the EventBus app uses async handlers and `asyncio.gather()` better reflects real concurrent request patterns.
- **Mocking the database lock**: Mock `run_with_db_lock` to simulate contention. Rejected because it would not validate the actual SQLite locking behavior.

## Compatibility considerations

- Tests must work with the updated `redeliver_event()` signature returning `(success, new_event_id, new_seq)` — the existing single-threaded requeue test (`test_dlq_requeue`) will need to assert on `body["new_seq"]` after the db.py change.
- The existing `test_requeue_non_dlq_event_fails` and `test_requeue_unknown_event_returns_404` tests must continue to pass after the failure-state inspection move under the lock.

## Security considerations

- No security-sensitive data is introduced by these tests. Test tokens and paths are ephemeral.

## Rollback considerations

- Removing the concurrent tests is mechanical — they do not affect production code.
- If the shared-lock fix introduces regressions, reverting the concurrent tests alone does not restore correctness; the source changes must also be reverted.

## Implementation

### Target file

`tests/eventbus/test_eventbus_dlq.py`

### Procedure

#### Step 1: Update existing single-threaded requeue test to assert new_seq (REQ-002)

In `test_dlq_requeue` (line 90), add an assertion for `new_seq`:

```python
def test_dlq_requeue(client: TestClient, tmp_path: Path) -> None:
    from eventbus.db import open_db
    from eventbus.dlq import sweep_orphans

    db = open_db(str(tmp_path / "eventbus.sqlite"))
    ev = _event()
    client.post("/publish", json=ev)
    db.execute(
        "UPDATE events SET delivery_failure_count = 2 WHERE event_id = ?",
        (ev["event_id"],),
    )
    db.commit()
    sweep_orphans(db, str(tmp_path / "deadletter"), max_retry=2)

    r = client.post(f"/dlq/{ev['event_id']}/requeue")
    assert r.status_code == 200
    body = r.json()
    assert body["requeued"] is True
    assert "new_event_id" in body
    assert body["new_event_id"] != ev["event_id"]
    # NEW: Assert new_seq is present and is a positive integer
    assert "new_seq" in body
    assert isinstance(body["new_seq"], int)
    assert body["new_seq"] > 0

    # Original event remains in DLQ (lineage model: original row's dlq_at IS NOT NULL)
    r2 = client.get("/dlq")
    body2 = r2.json()
    ids = [e["event_id"] for e in body2["items"]]
    assert ev["event_id"] in ids

    # New event exists with redelivered_from set
    new_row = db.execute(
        "SELECT event_id, redelivered_from FROM events WHERE event_id = ?",
        (body["new_event_id"],),
    ).fetchone()
    assert new_row is not None
    assert new_row["redelivered_from"] == ev["event_id"]
```

Key addition: `assert "new_seq" in body` and `assert isinstance(body["new_seq"], int)` and `assert body["new_seq"] > 0`.

#### Step 2: Add concurrent requeue same-event test (REQ-003)

Append the following test:

```python
@pytest.mark.asyncio
async def test_concurrent_requeue_same_event(client: TestClient, tmp_path: Path) -> None:
    """Concurrent requeue attempts on the same event must produce exactly one successful redelivery."""
    from eventbus.db import open_db
    from eventbus.dlq import sweep_orphans

    db = open_db(str(tmp_path / "eventbus.sqlite"))
    ev = _event()
    client.post("/publish", json=ev)
    db.execute(
        "UPDATE events SET delivery_failure_count = 2 WHERE event_id = ?",
        (ev["event_id"],),
    )
    db.commit()
    sweep_orphans(db, str(tmp_path / "deadletter"), max_retry=2)

    # Concurrent requeues via asyncio.gather
    async def requeue(event_id: str) -> dict:
        r = await client.post_async(f"/dlq/{event_id}/requeue")
        return r.json()

    results = await asyncio.gather(
        requeue(ev["event_id"]),
        requeue(ev["event_id"]),
        requeue(ev["event_id"]),
    )

    successes = [r for r in results if r.get("requeued")]
    failures = [r for r in results if not r.get("requeued")]

    # Exactly one success
    assert len(successes) == 1
    assert len(failures) == 2

    # The successful result has new_event_id and new_seq
    success_body = successes[0]
    assert "new_event_id" in success_body
    assert "new_seq" in success_body
    assert isinstance(success_body["new_seq"], int)
    assert success_body["new_seq"] > 0

    # The failed results have error details
    for fail_body in failures:
        assert "error" in fail_body or "detail" in fail_body

    # Only one new row was inserted
    new_rows = db.execute(
        "SELECT COUNT(*) FROM events WHERE redelivered_from = ?",
        (ev["event_id"],),
    ).fetchone()[0]
    assert new_rows == 1
```

#### Step 3: Add concurrent requeue different-events test (REQ-003)

Append the following test:

```python
@pytest.mark.asyncio
async def test_concurrent_requeue_different_events(client: TestClient, tmp_path: Path) -> None:
    """Concurrent requeue attempts on different events must both succeed independently."""
    from eventbus.db import open_db
    from eventbus.dlq import sweep_orphans

    db = open_db(str(tmp_path / "eventbus.sqlite"))
    ev1 = _event(topic="t1")
    ev2 = _event(topic="t2")
    client.post("/publish", json=ev1)
    client.post("/publish", json=ev2)
    db.execute(
        "UPDATE events SET delivery_failure_count = 2 WHERE event_id IN (?, ?)",
        (ev1["event_id"], ev2["event_id"]),
    )
    db.commit()
    sweep_orphans(db, str(tmp_path / "deadletter"), max_retry=2)

    async def requeue(event_id: str) -> dict:
        r = await client.post_async(f"/dlq/{event_id}/requeue")
        return r.json()

    results = await asyncio.gather(
        requeue(ev1["event_id"]),
        requeue(ev2["event_id"]),
    )

    # Both should succeed
    assert all(r.get("requeued") for r in results)

    # Distinct new_event_ids
    new_ids = {r["new_event_id"] for r in results}
    assert len(new_ids) == 2

    # Distinct new_seqs
    new_seqs = {r["new_seq"] for r in results}
    assert len(new_seqs) == 2

    # Two new rows were inserted
    new_rows = db.execute(
        "SELECT COUNT(*) FROM events WHERE redelivered_from IN (?, ?)",
        (ev1["event_id"], ev2["event_id"]),
    ).fetchone()[0]
    assert new_rows == 2
```

#### Step 4: Verify existing HTTP 409/404 tests still pass

No code changes needed. After the shared-lock fix, verify that:
- `test_requeue_non_dlq_event_fails` still returns HTTP 409
- `test_requeue_unknown_event_returns_404` still returns HTTP 404

These tests already cover REQ-001 acceptance criteria for error cases.

### Details

- REQ-003: Concurrent requeue tests added using `asyncio.gather()` to verify deterministic outcomes under contention.
- REQ-002: Existing single-threaded test updated to assert `new_seq` presence.
- REQ-001: Existing HTTP 409/404 tests verified unchanged after failure-state inspection moved under lock.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| tests/eventbus/test_eventbus_dlq.py | Unit: concurrent requeue behavior | uv run pytest tests/eventbus/test_eventbus_dlq.py -v | All DLQ tests pass including new concurrent tests |
| tests/eventbus/test_eventbus_dlq.py | Static analysis: no credential exposure in logs | uv run bandit -r scripts/eventbus/ -c pyproject.toml | No high/medium findings |
| tests/eventbus/test_eventbus_dlq.py | Type checking | uv run mypy scripts/eventbus/db.py | No new type errors |

## Completion criteria

- [ ] `test_concurrent_requeue_same_event` passes — exactly one successful redelivery among concurrent attempts.
- [ ] `test_concurrent_requeue_different_events` passes — both concurrent attempts succeed independently.
- [ ] `test_dlq_requeue` asserts `new_seq` is present and valid.
- [ ] `test_requeue_non_dlq_event_fails` still returns HTTP 409.
- [ ] `test_requeue_unknown_event_returns_404` still returns HTTP 404.
- [ ] No new static analysis or type-checking errors are introduced.

## Out of scope

- Background DLQ promotion atomicity (addressed separately per UNK-02).
- Replay endpoint pagination documentation (separate from DLQ docs).
- EVENTBUS-002 governance entry update (handled in separate document).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update existing single-threaded requeue test to assert new_seq | Pending | — | — | |
| 2 | Add concurrent requeue same-event test | Pending | — | — | |
| 3 | Add concurrent requeue different-events test | Pending | — | — | |
| 4 | Verify existing HTTP 409/404 tests still pass | Pending | — | — | |

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
- **Requirement ID**: REQ-002, REQ-003
- **Source issue**: issues/20260914-102435_eventbus06_dlq-promotion-requeue-atomicity.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-173831_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260914-232041
- **Related target files**: tests/eventbus/test_eventbus_dlq.py
