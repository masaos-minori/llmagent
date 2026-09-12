## Goal

Rewrite in-place-model assertions in `tests/eventbus/test_eventbus_dlq.py` to match the lineage model (REQ-002).

## Scope

- **In-Scope**: Modifying `tests/eventbus/test_eventbus_dlq.py` to update assertions for the lineage model
- **Out-of-Scope**: Changes to other files (handled in separate procedure documents)

## Assumptions

- The lineage model is chosen as the single truth for `/dlq/{event_id}/requeue`
- Each DLQ requeue creates a new event row with `redelivered_from` pointing to the original
- The original row's `dlq_at` is intentionally left set so only one redeliver succeeds per original event
- The response shape includes `new_event_id` and `new_seq` fields

## Design decisions

- Update `test_dlq_requeue` to verify the lineage model response shape
- Update `test_requeue_increments_dlq_requeue_count` to verify the lineage model behavior
- Preserve existing test structure and setup logic

## Alternatives considered

- Keeping the in-place model: would leave `redeliver_event()` and the `redelivered_from`/`cycle_failure_count` schema columns unused, representing wasted engineering effort
- Adding a config flag to switch between models: adds complexity without clear benefit; the design decision should be made once and committed

## Implementation

### Target file

`tests/eventbus/test_eventbus_dlq.py`

### Procedure

1. Update `test_dlq_requeue` to verify lineage model response shape
2. Update `test_requeue_increments_dlq_requeue_count` to verify lineage model behavior
3. Preserve existing test structure and setup logic

### Method

For each test function:
- Update assertions to check for `new_event_id` and `new_seq` fields in the response
- Verify that the original event remains in DLQ (dlq_at IS NOT NULL)
- Verify that a new event row was created with `redelivered_from` pointing to the original

### Details

#### Step 1: Update test_dlq_requeue

```python
# Before:
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
    assert r.json()["requeued"] is True

    r2 = client.get("/dlq")
    body2 = r2.json()
    ids = [e["event_id"] for e in body2["items"]]
    assert ev["event_id"] not in ids

# After:
def test_dlq_requeue(client: TestClient, tmp_path: Path) -> None:
    """Verify lineage model: requeue returns new_event_id and new_seq."""
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
    assert "new_seq" in body
    uuid.UUID(body["new_event_id"], version=4)
    assert isinstance(body["new_seq"], int)

    # Original event should still be in DLQ (dlq_at IS NOT NULL)
    row = db.execute(
        "SELECT dlq_at FROM events WHERE event_id = ?",
        (ev["event_id"],),
    ).fetchone()
    assert row["dlq_at"] is not None

    # New event should exist with redelivered_from pointing to original
    new_row = db.execute(
        "SELECT redelivered_from FROM events WHERE event_id = ?",
        (body["new_event_id"],),
    ).fetchone()
    assert new_row["redelivered_from"] == ev["event_id"]

    # Original event should NOT appear in /dlq list (still has dlq_at)
    r2 = client.get("/dlq")
    body2 = r2.json()
    ids = [e["event_id"] for e in body2["items"]]
    assert ev["event_id"] not in ids
```

#### Step 2: Update test_requeue_increments_dlq_requeue_count

```python
# Before:
def test_requeue_increments_dlq_requeue_count(
    client: TestClient, tmp_path: Path
) -> None:
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

    # Requeue once — dlq_requeue_count should increment to 1
    r = client.post(f"/dlq/{ev['event_id']}/requeue")
    assert r.status_code == 200
    assert r.json()["requeued"] is True

    row = db.execute(
        "SELECT dlq_requeue_count, delivery_failure_count, dlq_at FROM events WHERE event_id = ?",
        (ev["event_id"],),
    ).fetchone()
    assert row["dlq_requeue_count"] == 1
    assert row["delivery_failure_count"] == 2
    assert row["dlq_at"] is None

    # Exhaust retries again — should promote to DLQ
    db.execute(
        "UPDATE events SET delivery_failure_count = 2 WHERE event_id = ?",
        (ev["event_id"],),
    )
    db.commit()
    n = sweep_orphans(db, str(tmp_path / "deadletter"), max_retry=2)
    assert n == 1
    dlq_file = tmp_path / "deadletter" / f"{ev['event_id']}.json"
    assert dlq_file.exists()

# After:
def test_requeue_increments_dlq_requeue_count(
    client: TestClient, tmp_path: Path
) -> None:
    """Verify lineage model: requeue increments dlq_requeue_count on original row."""
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

    # Requeue once — dlq_requeue_count should increment to 1 on original row
    r = client.post(f"/dlq/{ev['event_id']}/requeue")
    assert r.status_code == 200
    body = r.json()
    assert body["requeued"] is True
    assert "new_event_id" in body

    # Original row: dlq_requeue_count incremented, but dlq_at remains set
    row = db.execute(
        "SELECT dlq_requeue_count, delivery_failure_count, dlq_at FROM events WHERE event_id = ?",
        (ev["event_id"],),
    ).fetchone()
    assert row["dlq_requeue_count"] == 1
    assert row["delivery_failure_count"] == 2
    assert row["dlq_at"] is not None

    # New row: redelivered_from points to original
    new_row = db.execute(
        "SELECT redelivered_from, cycle_failure_count FROM events WHERE event_id = ?",
        (body["new_event_id"],),
    ).fetchone()
    assert new_row["redelivered_from"] == ev["event_id"]
    assert new_row["cycle_failure_count"] == 0

    # Exhaust retries again — should promote to DLQ
    db.execute(
        "UPDATE events SET delivery_failure_count = 2 WHERE event_id = ?",
        (ev["event_id"],),
    )
    db.commit()
    n = sweep_orphans(db, str(tmp_path / "deadletter"), max_retry=2)
    assert n == 1
    dlq_file = tmp_path / "deadletter" / f"{ev['event_id']}.json"
    assert dlq_file.exists()
```

## Compatibility considerations

- The response shape changes to include `new_event_id` and `new_seq` fields
- Existing callers expecting the same `event_id` back will need updating
- The `dlq_imminent` field is no longer included since the original event's `delivery_failure_count` is no longer relevant after redelivery

## Security considerations

- The lineage model provides better auditability — each delivery attempt is a distinct row with `redelivered_from` pointing to the original
- This improves security by preventing indefinite resource consumption from abandoned subscriptions

## Rollback considerations

- If the lineage model causes issues in production, roll back to the previous state where `requeue_event()` was used
- Ensure test coverage exists before making changes to verify rollback safety

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/eventbus/dlq_route.py::dlq_requeue | Integration: verify response shape matches lineage model | pytest tests/eventbus/test_eventbus_dlq.py::test_dlq_requeue | Test completes without assertion errors |
| scripts/eventbus/db.py::redeliver_event | Integration: verify concurrent requeue operations don't cause data corruption | pytest tests/eventbus/test_eventbus_concurrent.py::TestConcurrentDlqRequeue::test_concurrent_dlq_requeue | Test completes without assertion errors |

## Completion criteria

- [ ] `test_dlq_requeue` updated to verify lineage model response shape
- [ ] `test_requeue_increments_dlq_requeue_count` updated to verify lineage model behavior
- [ ] Tests pass with the new requeue model

## Out of scope

- Changes to `scripts/eventbus/dlq_route.py` (handled in separate procedure document)
- Changes to `scripts/eventbus/db.py` (handled in separate procedure document)
- Changes to other test files (handled in separate procedure documents)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update test_dlq_requeue | Pending | — | — | |
| 2 | Update test_requeue_increments_dlq_requeue_count | Pending | — | — | |
| 3 | Run validation tests | Pending | — | — | |

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
- **Requirement ID**: REQ-002
- **Source issue**: issues/20260911-142700_ebdlq01_requeue-model-in-place-vs-lineage-conflict.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260912-115455_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260912-150000
- **Related target files**: tests/eventbus/test_eventbus_dlq.py
