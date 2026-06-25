# Implementation: tests/test_eventbus_delivery.py — E2E delivery lifecycle tests (req #27)

## Goal

Create a new test file covering the full consumer delivery lifecycle: nack, failure count increment, DLQ promotion at threshold, ack, and requeue after DLQ.

## Scope

- New file `tests/test_eventbus_delivery.py`
- 5 test scenarios covering req #24–#26 behavior
- Uses `TestClient` fixture pattern from existing `tests/test_eventbus_dlq.py`
- `max_retry = 2` for brevity

## Assumptions

- req #24, #25, #26, #28 are all implemented before this test is run
- `POST /events/{id}/nack` and `POST /events/{id}/ack` endpoints exist
- TestClient runs FastAPI lifespan (startup/shutdown), giving access to a real SQLite DB in `tmp_path`
- Background DLQ loop interval is 60s, far longer than any test runtime — no timing races

## Implementation

### Target file

`tests/test_eventbus_delivery.py` (new file)

### Procedure

1. Create the file with the shared `client` fixture (same pattern as `test_eventbus_dlq.py`)
2. Add `_event()` helper
3. Implement 5 test functions

### Method

Create new test file. Copy fixture pattern from existing tests.

### Details

**File skeleton:**
```python
from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Any:
    from eventbus import app as eb_app
    from eventbus.config import EventBusConfig

    cfg = EventBusConfig(
        port=8015,
        db_path=str(tmp_path / "eventbus.sqlite"),
        storage_dir=str(tmp_path / "storage"),
        offsets_dir=str(tmp_path / "offsets"),
        deadletter_dir=str(tmp_path / "deadletter"),
        max_retry=2,
    )
    monkeypatch.setattr(eb_app, "load_config", lambda path=None: cfg)
    schema_path = Path(__file__).parent.parent / "schemas" / "event_envelope.json"
    monkeypatch.setattr(eb_app, "get_schema_path", lambda: schema_path)

    with TestClient(eb_app.app) as c:
        yield c


def _event(topic: str = "t") -> dict[str, Any]:
    return {
        "event_id": str(uuid.uuid4()),
        "topic": topic,
        "payload": {},
        "producer": "p",
        "published_at": "2026-06-25T12:00:00Z",
    }
```

**Test 1 — nack increments failure count:**
```python
def test_nack_increments_failure_count(client: TestClient) -> None:
    ev = _event()
    client.post("/publish", json=ev)
    r = client.post(f"/events/{ev['event_id']}/nack")
    assert r.status_code == 200
    assert r.json()["failure_count"] == 1
    # nack again
    r2 = client.post(f"/events/{ev['event_id']}/nack")
    assert r2.json()["failure_count"] == 2
```

**Test 2 — nack at max_retry promotes to DLQ:**
```python
def test_nack_at_max_retry_promotes_to_dlq(client: TestClient, tmp_path: Path) -> None:
    ev = _event()
    client.post("/publish", json=ev)
    # nack max_retry times (= 2)
    for _ in range(2):
        client.post(f"/events/{ev['event_id']}/nack")
    # last nack should return promoted=True
    r = client.post(f"/events/{ev['event_id']}/nack")
    # (actually the 2nd nack hits the threshold since max_retry=2 and count becomes 2)
    # Verify DLQ via GET /dlq
    r_dlq = client.get("/dlq")
    ids = [e["event_id"] for e in r_dlq.json()]
    assert ev["event_id"] in ids
    # DLQ file exists
    dlq_file = tmp_path / "deadletter" / f"{ev['event_id']}.json"
    assert dlq_file.exists()
```

Note: with `max_retry=2`, the event is promoted when `delivery_failure_count` reaches 2 (i.e., on the 2nd nack).

**Test 3 — ack sets acked_at:**
```python
def test_ack_sets_acked_at(client: TestClient, tmp_path: Path) -> None:
    from eventbus.db import open_db

    ev = _event()
    client.post("/publish", json=ev)
    r = client.post(f"/events/{ev['event_id']}/ack")
    assert r.status_code == 200
    assert r.json()["acked"] is True

    db = open_db(str(tmp_path / "eventbus.sqlite"))
    row = db.execute(
        "SELECT acked_at FROM events WHERE event_id = ?", (ev["event_id"],)
    ).fetchone()
    assert row["acked_at"] is not None
```

**Test 4 — requeue returns event to live state:**
```python
def test_requeue_after_dlq(client: TestClient) -> None:
    ev = _event()
    client.post("/publish", json=ev)
    # nack to DLQ (max_retry=2)
    client.post(f"/events/{ev['event_id']}/nack")
    client.post(f"/events/{ev['event_id']}/nack")
    # confirm in DLQ
    ids_before = [e["event_id"] for e in client.get("/dlq").json()]
    assert ev["event_id"] in ids_before
    # requeue
    r = client.post(f"/dlq/{ev['event_id']}/requeue")
    assert r.status_code == 200
    # confirm removed from DLQ
    ids_after = [e["event_id"] for e in client.get("/dlq").json()]
    assert ev["event_id"] not in ids_after
```

**Test 5 — background loop does not double-promote:**
```python
def test_no_double_promote_after_inline(client: TestClient, tmp_path: Path) -> None:
    from eventbus.dlq import promote_to_dlq

    ev = _event()
    client.post("/publish", json=ev)
    # inline promote via nack
    client.post(f"/events/{ev['event_id']}/nack")
    client.post(f"/events/{ev['event_id']}/nack")
    # simulate background loop sweep
    from eventbus import app as eb_app
    n = promote_to_dlq(eb_app._db, str(tmp_path / "deadletter"), max_retry=2)  # noqa: SLF001
    assert n == 0  # already promoted inline; sweep finds nothing
```

## Validation plan

| Check | Command | Target |
|---|---|---|
| Test collection | `uv run pytest tests/test_eventbus_delivery.py --collect-only` | 5 tests |
| All pass | `uv run pytest tests/test_eventbus_delivery.py -v` | all pass |
| No regression | `uv run pytest tests/test_eventbus_*.py` | all pass |
| Lint | `ruff check tests/test_eventbus_delivery.py` | 0 errors |
| Type check | `mypy tests/test_eventbus_delivery.py` | no errors |
