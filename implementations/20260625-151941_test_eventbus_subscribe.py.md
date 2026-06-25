# Implementation: tests/test_eventbus_subscribe.py — subscribe integration tests (req #38)

## Goal

Integration-test the hybrid subscribe model: immediate push delivery, multiple subscribers, topic filtering via broker, and reconnect replay semantics.

## Scope

- New file `tests/test_eventbus_subscribe.py`
- Tests broker queue state directly (avoids async SSE streaming complexity)
- Uses the same TestClient fixture pattern as existing tests
- 5 test cases

## Assumptions

- req #35–37, #39 are implemented (broker wired into publish and subscribe)
- `eb_app._broker` is accessible from tests for direct queue inspection
- TestClient runs lifespan so `_broker` is initialized
- Tests verify broker queue state rather than full SSE byte stream to avoid async complexity

## Implementation

### Target file

`tests/test_eventbus_subscribe.py` (new)

### Procedure

1. Create file with shared `client` fixture
2. Implement 5 test functions using broker queue inspection

### Method

New file. Reuse fixture pattern from `test_eventbus_dlq.py`.

### Details

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
        max_retry=3,
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


def test_publish_notifies_broker(client: TestClient) -> None:
    """publish() should push the event to the broker after SQLite commit."""
    from eventbus import app as eb_app

    sub = eb_app._broker.subscribe([])
    try:
        ev = _event()
        client.post("/publish", json=ev)
        assert sub.queue.qsize() == 1
        item = sub.queue.get_nowait()
        assert item["event_id"] == ev["event_id"]
    finally:
        eb_app._broker.unsubscribe(sub)


def test_duplicate_publish_does_not_notify_twice(client: TestClient) -> None:
    """Duplicate publish (same event_id) should not push a second notification."""
    from eventbus import app as eb_app

    ev = _event()
    sub = eb_app._broker.subscribe([])
    try:
        client.post("/publish", json=ev)
        client.post("/publish", json=ev)  # duplicate
        assert sub.queue.qsize() == 1  # only one notification
    finally:
        eb_app._broker.unsubscribe(sub)


def test_multiple_subscribers_receive_event(client: TestClient) -> None:
    """All active subscribers should receive each published event."""
    from eventbus import app as eb_app

    sub1 = eb_app._broker.subscribe([])
    sub2 = eb_app._broker.subscribe([])
    try:
        client.post("/publish", json=_event())
        assert sub1.queue.qsize() == 1
        assert sub2.queue.qsize() == 1
    finally:
        eb_app._broker.unsubscribe(sub1)
        eb_app._broker.unsubscribe(sub2)


def test_topic_filter_in_broker(client: TestClient) -> None:
    """Topic-filtered subscriber should not receive events for other topics."""
    from eventbus import app as eb_app

    sub_foo = eb_app._broker.subscribe(["foo"])
    sub_all = eb_app._broker.subscribe([])
    try:
        client.post("/publish", json=_event(topic="bar"))
        assert sub_foo.queue.empty()       # "bar" does not match "foo"
        assert sub_all.queue.qsize() == 1  # all-topics subscriber receives it
    finally:
        eb_app._broker.unsubscribe(sub_foo)
        eb_app._broker.unsubscribe(sub_all)


def test_subscriber_count_in_health(client: TestClient) -> None:
    """GET /health should reflect active subscriber count."""
    from eventbus import app as eb_app

    sub = eb_app._broker.subscribe([])
    try:
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert data.get("active_subscribers", 0) >= 1
    finally:
        eb_app._broker.unsubscribe(sub)
```

## Validation plan

| Check | Command | Target |
|---|---|---|
| Test collection | `uv run pytest tests/test_eventbus_subscribe.py --collect-only` | 5 tests |
| All pass | `uv run pytest tests/test_eventbus_subscribe.py -v` | all pass |
| No regression | `uv run pytest tests/test_eventbus_*.py` | all pass |
| Lint | `ruff check tests/test_eventbus_subscribe.py` | 0 errors |
| Type check | `mypy tests/test_eventbus_subscribe.py` | no errors |
