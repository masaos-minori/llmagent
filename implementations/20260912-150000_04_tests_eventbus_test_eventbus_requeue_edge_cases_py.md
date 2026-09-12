## Goal

Rewrite in-place-model assertions in `tests/eventbus/test_eventbus_requeue_edge_cases.py` to match the lineage model (REQ-002).

## Scope

- **In-Scope**: Modifying `tests/eventbus/test_eventbus_requeue_edge_cases.py` to update assertions for the lineage model
- **Out-of-Scope**: Changes to other files (handled in separate procedure documents)

## Assumptions

- The lineage model is chosen as the single truth for `/dlq/{event_id}/requeue`
- Each DLQ requeue creates a new event row with `redelivered_from` pointing to the original
- The original row's `dlq_at` is intentionally left set so only one redeliver succeeds per original event
- The response shape includes `new_event_id` and `new_seq` fields

## Design decisions

- Update `test_requeue_valid_dmq_event` to verify the lineage model response shape
- Update `test_repeated_requeue_increments_dlq_requeue_count` to verify the lineage model behavior
- Update `test_requeue_event_at_max_retry_then_re_promoted` to verify the lineage model behavior
- Preserve existing test structure and setup logic

## Alternatives considered

- Keeping the in-place model: would leave `redeliver_event()` and the `redelivered_from`/`cycle_failure_count` schema columns unused, representing wasted engineering effort
- Adding a config flag to switch between models: adds complexity without clear benefit; the design decision should be made once and committed

## Implementation

### Target file

`tests/eventbus/test_eventbus_requeue_edge_cases.py`

### Procedure

1. Update `test_requeue_valid_dmq_event` to verify lineage model response shape
2. Update `test_repeated_requeue_increments_dlq_requeue_count` to verify lineage model behavior
3. Update `test_requeue_event_at_max_retry_then_re_promoted` to verify lineage model behavior
4. Preserve existing test structure and setup logic

### Method

For each test function:
- Update assertions to check for `new_event_id` and `new_seq` fields in the response
- Verify that the original event remains in DLQ (dlq_at IS NOT NULL)
- Verify that a new event row was created with `redelivered_from` pointing to the original

### Details

#### Step 1: Update test_requeue_valid_dmq_event

```python
# Before:
def test_requeue_valid_dmq_event(self, client: TestClient, tmp_path: Path) -> None:
    """POST /dlq/{event_id}/requeue for valid DLQ event succeeds."""
    from eventbus.db import open_db
    from eventbus.dlq import sweep_orphans

    body = _event()
    resp = client.post("/publish", json=body)
    assert resp.status_code == 200

    # Promote to DLQ
    db = open_db(str(tmp_path / "eventbus.sqlite"))
    db.execute(
        "UPDATE events SET delivery_failure_count = 2 WHERE event_id = ?",
        (body["event_id"],),
    )
    db.commit()
    sweep_orphans(db, str(tmp_path / "deadletter"), max_retry=2)

    # Requeue should succeed
    resp = client.post(f"/dlq/{body['event_id']}/requeue")
    assert resp.status_code == 200
    data = resp.json()
    assert data["requeued"] is True
    assert data["dlq_imminent"] is True

    # Verify dlq_at was cleared
    dlq_at = _get_field(client, body["event_id"], "dlq_at")
    assert dlq_at is None

# After:
def test_requeue_valid_dmq_event(self, client: TestClient, tmp_path: Path) -> None:
    """POST /dlq/{event_id}/requeue for valid DLQ event succeeds (lineage model)."""
    from eventbus.db import open_db
    from eventbus.dlq import sweep_orphans

    body = _event()
    resp = client.post("/publish", json=body)
    assert resp.status_code == 200

    # Promote to DLQ
    db = open_db(str(tmp_path / "eventbus.sqlite"))
    db.execute(
        "UPDATE events SET delivery_failure_count = 2 WHERE event_id = ?",
        (body["event_id"],),
    )
    db.commit()
    sweep_orphans(db, str(tmp_path / "deadletter"), max_retry=2)

    # Requeue should succeed with lineage model response
    resp = client.post(f"/dlq/{body['event_id']}/requeue")
    assert resp.status_code == 200
    data = resp.json()
    assert data["requeued"] is True
    assert "new_event_id" in data
    assert "new_seq" in data
    uuid.UUID(data["new_event_id"], version=4)
    assert isinstance(data["new_seq"], int)

    # Original event should still be in DLQ (dlq_at IS NOT NULL)
    dlq_at = _get_field(client, body["event_id"], "dlq_at")
    assert dlq_at is not None

    # New event should exist with redelivered_from pointing to original
    new_row = db.execute(
        "SELECT redelivered_from FROM events WHERE event_id = ?",
        (data["new_event_id"],),
    ).fetchone()
    assert new_row["redelivered_from"] == body["event_id"]
```

#### Step 2: Update test_repeated_requeue_increments_dlq_requeue_count

```python
# Before:
def test_repeated_requeue_increments_dlq_requeue_count(
    self, client: TestClient, tmp_path: Path
) -> None:
    """Repeated requeue of same event increments dlq_requeue_count each time."""
    from eventbus.db import open_db
    from eventbus.dlq import sweep_orphans

    body = _event()
    resp = client.post("/publish", json=body)
    assert resp.status_code == 200

    # Promote to DLQ with delivery_failure_count >= max_retry so re-promotion works
    db = open_db(str(tmp_path / "eventbus.sqlite"))
    db.execute(
        "UPDATE events SET delivery_failure_count = 2 WHERE event_id = ?",
        (body["event_id"],),
    )
    db.commit()
    sweep_orphans(db, str(tmp_path / "deadletter"), max_retry=2)

    # First requeue
    resp = client.post(f"/dlq/{body['event_id']}/requeue")
    assert resp.status_code == 200
    assert _get_field(client, body["event_id"], "dlq_requeue_count") == 1

    # Re-promote to DLQ before second requeue (delivery_failure_count >= max_retry so it will be promoted)
    db = open_db(str(tmp_path / "eventbus.sqlite"))
    n = sweep_orphans(db, str(tmp_path / "deadletter"), max_retry=2)
    assert n == 1

    # Second requeue
    resp = client.post(f"/dlq/{body['event_id']}/requeue")
    assert resp.status_code == 200
    assert _get_field(client, body["event_id"], "dlq_requeue_count") == 2

    # Re-promote to DLQ before third requeue
    db = open_db(str(tmp_path / "eventbus.sqlite"))
    n = sweep_orphans(db, str(tmp_path / "deadletter"), max_retry=2)
    assert n == 1

    # Third requeue
    resp = client.post(f"/dlq/{body['event_id']}/requeue")
    assert resp.status_code == 200
    assert _get_field(client, body["event_id"], "dlq_requeue_count") == 3

# After:
def test_repeated_requeue_increments_dlq_requeue_count(
    self, client: TestClient, tmp_path: Path
) -> None:
    """Repeated requeue of same event increments dlq_requeue_count each time (lineage model)."""
    from eventbus.db import open_db
    from eventbus.dlq import sweep_orphans

    body = _event()
    resp = client.post("/publish", json=body)
    assert resp.status_code == 200

    # Promote to DLQ with delivery_failure_count >= max_retry so re-promotion works
    db = open_db(str(tmp_path / "eventbus.sqlite"))
    db.execute(
        "UPDATE events SET delivery_failure_count = 2 WHERE event_id = ?",
        (body["event_id"],),
    )
    db.commit()
    sweep_orphans(db, str(tmp_path / "deadletter"), max_retry=2)

    # First requeue — original row gets dlq_requeue_count=1, new row created
    resp = client.post(f"/dlq/{body['event_id']}/requeue")
    assert resp.status_code == 200
    data1 = resp.json()
    assert data1["requeued"] is True
    assert _get_field(client, body["event_id"], "dlq_requeue_count") == 1
    assert _get_field(client, body["event_id"], "dlq_at") is not None

    # Second requeue — original row gets dlq_requeue_count=2, another new row created
    resp = client.post(f"/dlq/{body['event_id']}/requeue")
    assert resp.status_code == 200
    data2 = resp.json()
    assert data2["requeued"] is True
    assert _get_field(client, body["event_id"], "dlq_requeue_count") == 2
    assert _get_field(client, body["event_id"], "dlq_at") is not None

    # Third requeue — original row gets dlq_requeue_count=3, yet another new row created
    resp = client.post(f"/dlq/{body['event_id']}/requeue")
    assert resp.status_code == 200
    data3 = resp.json()
    assert data3["requeued"] is True
    assert _get_field(client, body["event_id"], "dlq_requeue_count") == 3
    assert _get_field(client, body["event_id"], "dlq_at") is not None

    # Each new event should have redelivered_from pointing to original
    new_rows = [data1, data2, data3]
    for i, d in enumerate(new_rows):
        new_row = db.execute(
            "SELECT redelivered_from, cycle_failure_count FROM events WHERE event_id = ?",
            (d["new_event_id"],),
        ).fetchone()
        assert new_row["redelivered_from"] == body["event_id"]
        assert new_row["cycle_failure_count"] == 0
```

#### Step 3: Update test_requeue_event_at_max_retry_then_re_promoted

```python
# Before:
def test_requeue_event_at_max_retry_then_re_promoted(
    self, client: TestClient, tmp_path: Path
) -> None:
    """Requeue of event at delivery_failure_count >= max_retry succeeds but re-promoted on next DLQ tick."""
    from eventbus.db import open_db
    from eventbus.dlq import sweep_orphans

    body = _event()
    resp = client.post("/publish", json=body)
    assert resp.status_code == 200

    # Promote to DLQ
    db = open_db(str(tmp_path / "eventbus.sqlite"))
    db.execute(
        "UPDATE events SET delivery_failure_count = 2 WHERE event_id = ?",
        (body["event_id"],),
    )
    db.commit()
    sweep_orphans(db, str(tmp_path / "deadletter"), max_retry=2)

    dlq_file_1 = tmp_path / "deadletter" / f"{body['event_id']}.json"
    assert dlq_file_1.exists()

    # Requeue — returns dlq_imminent warning
    resp = client.post(f"/dlq/{body['event_id']}/requeue")
    assert resp.status_code == 200
    data = resp.json()
    assert data["dlq_imminent"] is True

    # Verify dlq_at was cleared in DB
    dlq_at = _get_field(client, body["event_id"], "dlq_at")
    assert dlq_at is None

    # Next DLQ loop tick should re-promote (delivery_failure_count still >= max_retry)
    db = open_db(str(tmp_path / "eventbus.sqlite"))
    n = sweep_orphans(db, str(tmp_path / "deadletter"), max_retry=2)
    assert n == 1

    dlq_file_2 = tmp_path / "deadletter" / f"{body['event_id']}.json"
    assert dlq_file_2.exists()

# After:
def test_requeue_event_at_max_retry_then_re_promoted(
    self, client: TestClient, tmp_path: Path
) -> None:
    """Requeue of event at delivery_failure_count >= max_retry succeeds but re-promoted on next DLQ tick (lineage model)."""
    from eventbus.db import open_db
    from eventbus.dlq import sweep_orphans

    body = _event()
    resp = client.post("/publish", json=body)
    assert resp.status_code == 200

    # Promote to DLQ
    db = open_db(str(tmp_path / "eventbus.sqlite"))
    db.execute(
        "UPDATE events SET delivery_failure_count = 2 WHERE event_id = ?",
        (body["event_id"],),
    )
    db.commit()
    sweep_orphans(db, str(tmp_path / "deadletter"), max_retry=2)

    dlq_file_1 = tmp_path / "deadletter" / f"{body['event_id']}.json"
    assert dlq_file_1.exists()

    # Requeue — returns new_event_id and new_seq (no dlq_imminent since original event remains in DLQ)
    resp = client.post(f"/dlq/{body['event_id']}/requeue")
    assert resp.status_code == 200
    data = resp.json()
    assert data["requeued"] is True
    assert "new_event_id" in data
    assert "new_seq" in data

    # Original event should still be in DLQ (dlq_at IS NOT NULL)
    dlq_at = _get_field(client, body["event_id"], "dlq_at")
    assert dlq_at is not None

    # New event should exist with redelivered_from pointing to original
    new_row = db.execute(
        "SELECT redelivered_from FROM events WHERE event_id = ?",
        (data["new_event_id"],),
    ).fetchone()
    assert new_row["redelivered_from"] == body["event_id"]

    # Next DLQ loop tick should re-promote the original event (delivery_failure_count still >= max_retry)
    db = open_db(str(tmp_path / "eventbus.sqlite"))
    n = sweep_orphans(db, str(tmp_path / "deadletter"), max_retry=2)
    assert n == 1

    dlq_file_2 = tmp_path / "deadletter" / f"{body['event_id']}.json"
    assert dlq_file_2.exists()
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

- [ ] `test_requeue_valid_dmq_event` updated to verify lineage model response shape
- [ ] `test_repeated_requeue_increments_dlq_requeue_count` updated to verify lineage model behavior
- [ ] `test_requeue_event_at_max_retry_then_re_promoted` updated to verify lineage model behavior
- [ ] Tests pass with the new requeue model

## Out of scope

- Changes to `scripts/eventbus/dlq_route.py` (handled in separate procedure document)
- Changes to `scripts/eventbus/db.py` (handled in separate procedure document)
- Changes to other test files (handled in separate procedure documents)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update test_requeue_valid_dmq_event | Pending | — | — | |
| 2 | Update test_repeated_requeue_increments_dlq_requeue_count | Pending | — | — | |
| 3 | Update test_requeue_event_at_max_retry_then_re_promoted | Pending | — | — | |
| 4 | Run validation tests | Pending | — | — | |

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
- **Related target files**: tests/eventbus/test_eventbus_requeue_edge_cases.py
