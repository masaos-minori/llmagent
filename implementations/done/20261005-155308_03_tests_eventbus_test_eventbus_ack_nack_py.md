# Implementation Procedure: Add regression tests for ACK-then-NACK

## Goal

Add unit and route-level regression tests covering ACK-then-NACK, no-DLQ-promotion, and second-consumer semantics. REQ-006, REQ-004, REQ-005.

## Scope

Add tests to `tests/eventbus/test_eventbus_ack_nack.py`.

## Assumptions

- Fixtures `db` and `client` exist in the test file (confirmed).
- The `_simulate_delivery_http` helper exists for simulating event delivery (confirmed).
- The `NackResult` class is imported from `eventbus.db` (confirmed).

## Design decisions

- Add both unit-level tests (using the `db` fixture) and route-level tests (using the `client` fixture).
- Use the existing `_simulate_delivery_http` helper to simulate event delivery before ACK/NACK.
- Verify counter values via direct database queries after each test scenario.

## Alternatives considered

- Using only route-level tests: would miss the unit-level verification of counter values.
- Using only unit-level tests: would miss the HTTP response status code verification.

## Implementation

### Target file

`tests/eventbus/test_eventbus_ack_nack.py`

### Procedure

1. Add an ACK-then-NACK unit test under `TestNackEvent`.
2. Add an ACK-then-NACK route-level test under `TestNackEvent`.
3. Add a no-DLQ-promotion test under `TestNackEvent`.
4. Add a second-consumer semantics test under `TestNackEvent`.
5. Verify that duplicate ACK and NACK-then-ACK tests remain unchanged.

### Method

Add the following test methods to the `TestNackEvent` class:

#### Test 1: ACK-then-NACK by same consumer (unit)

```python
def test_ack_then_nack_same_consumer(self, db: sqlite3.Connection) -> None:
    """ACK by consumer A followed by NACK by consumer A returns invalid transition."""
    from eventbus.db import ack_event_for_consumer, nack_event

    ev = _event()
    db.execute(
        "INSERT INTO events (event_id, topic, payload, producer, published_at) VALUES (?, ?, ?, ?, ?)",
        (ev["event_id"], ev["topic"], json.dumps(ev["payload"]), ev["producer"], ev["published_at"]),
    )
    db.commit()

    now = "2026-06-22T13:00:00Z"
    found, newly_acked, seq = ack_event_for_consumer(db, ev["event_id"], "consumer-A", now)
    assert found is True
    assert newly_acked is True

    result = nack_event(db, ev["event_id"], "consumer-A")
    assert result == NackResult(delivery_failure_count=-2, cycle_failure_count=-2)

    # Counters unchanged
    row = db.execute(
        "SELECT delivery_failure_count, cycle_failure_count, consumer_delivery_failure_count FROM events WHERE event_id = ?",
        (ev["event_id"],),
    ).fetchone()
    assert row["delivery_failure_count"] == 0
    assert row["cycle_failure_count"] == 0
    assert row["consumer_delivery_failure_count"] == 0
```

#### Test 2: ACK-then-NACK by same consumer (route)

```python
def test_ack_then_nack_same_consumer_route(self, client: Any) -> None:
    """POST ack then POST nack returns 409 with event already acknowledged."""
    body = _event()
    resp = client.post("/publish", json=body)
    assert resp.status_code == 200

    _simulate_delivery_http(client, body["event_id"], "consumer-A")

    resp = client.post(
        f"/events/{body['event_id']}/ack", params={"consumer_id": "consumer-A"}
    )
    assert resp.status_code == 200

    resp = client.post(
        "/nack", params={"event_id": body["event_id"], "consumer_id": "consumer-A"}
    )
    assert resp.status_code == 409
    assert resp.json()["detail"] == "event already acknowledged"

    # Counters unchanged
    dfc = _get_field(client, body["event_id"], "delivery_failure_count")
    assert dfc == 0
```

#### Test 3: No DLQ promotion after ACK

```python
def test_no_dlq_promotion_after_ack(self, client: Any, tmp_path: Path) -> None:
    """Repeated NACKs sent after the same consumer's ACK do not promote to DLQ."""
    from eventbus.db import open_db

    body = _event("dlq_promo")
    resp = client.post("/publish", json=body)
    assert resp.status_code == 200

    # Set delivery_failure_count to max_retry to trigger inline promotion
    db = open_db(str(tmp_path / "eventbus.sqlite"))
    db.execute(
        "UPDATE events SET delivery_failure_count = 2 WHERE event_id = ?",
        (body["event_id"],),
    )
    db.commit()

    # Simulate delivery and ACK
    _simulate_delivery_http(client, body["event_id"], "consumer-A")

    resp = client.post(
        f"/events/{body['event_id']}/ack", params={"consumer_id": "consumer-A"}
    )
    assert resp.status_code == 200

    # NACK should be rejected, not promoted
    resp = client.post(
        "/nack", params={"event_id": body["event_id"], "consumer_id": "consumer-A"}
    )
    assert resp.status_code == 409
    assert resp.json()["detail"] == "event already acknowledged"

    dlq_file = tmp_path / "deadletter" / f"{body['event_id']}.json"
    assert not dlq_file.exists()
```

#### Test 4: Second consumer can still NACK

```python
def test_second_consumer_can_nack(self, client: Any) -> None:
    """Consumer B can NACK an event that consumer A has ACKed."""
    body = _event()
    resp = client.post("/publish", json=body)
    assert resp.status_code == 200

    _simulate_delivery_http(client, body["event_id"], "consumer-A")

    resp = client.post(
        f"/events/{body['event_id']}/ack", params={"consumer_id": "consumer-A"}
    )
    assert resp.status_code == 200

    # Consumer B NACKs — should succeed (per-consumer semantics)
    resp = client.post(
        "/nack", params={"event_id": body["event_id"], "consumer_id": "consumer-B"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["delivery_failure_count"] == 1
```

### Details

- Current test file covers ACK, repeated ACK and NACK separately but no test performs ACK followed by NACK.
- The `_simulate_delivery_http` helper inserts a `consumer_delivery` record to simulate event delivery.
- The `client` fixture provides a TestClient with `max_retry=2` configured.
- The `db` fixture provides a SQLite connection for unit-level testing.
- Counter verification uses direct database queries after each test scenario.

## Compatibility considerations

- Existing tests (`TestAckHttpBehavior`, `test_nack_event_*`) are unchanged.
- The new tests use the same fixtures and helpers as existing tests.

## Security considerations

- Tests use temporary directories (`tmp_path`) — no production data affected.
- No new credential or secret exposure.

## Rollback considerations

- Remove the added test methods to restore the original test file.
- No schema changes, so no data migration rollback needed.

## Validation plan

- New tests pass against the implemented behavior.
- Existing tests pass unchanged: `uv run pytest tests/eventbus/test_eventbus_ack_nack.py -v`.
- Full suite passes: `uv run pytest tests/eventbus -v`.

## Completion criteria

- All four new tests pass.
- All existing tests continue to pass.
- Coverage on changed lines meets the threshold in `rules/toolchain.md`.

## Out of scope

- Modifying `nack_event()` in delivery_repo.py (handled in a separate procedure document).
- Modifying the `nack` route in ack_route.py (handled in a separate procedure document).
- Updating documentation (handled in a separate procedure document).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261005-164838 | 20261005-164838 |  |
| 2 | Add or update tests per Validation plan | Completed | 20261005-164838 | 20261005-164838 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261005-164838 | 20261005-164838 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261005-164838 | 20261005-164838 |  |

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
- **Requirement ID**: REQ-006, REQ-004, REQ-005
- **Source issue**: issues/20261005-102244_eb002_eventbus-nack-accepted-after-per-consumer-ack.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261005-103619_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261005-155308
- **Related target files**: tests/eventbus/test_eventbus_ack_nack.py