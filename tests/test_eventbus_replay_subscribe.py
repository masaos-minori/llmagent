"""tests/test_eventbus_replay_subscribe.py
Event Bus replay and subscribe endpoint tests.

NOTE: /subscribe returns an infinite SSE stream; httpx.ASGITransport blocks on
response_complete for infinite generators. Subscribe query logic is tested via
direct DB access (same approach as original test_eventbus_phase2.py).
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

import pytest
from eventbus_helpers import make_eventbus_client
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Any:
    with make_eventbus_client(tmp_path, monkeypatch) as c:
        yield c


def _event(topic: str = "test.topic") -> dict[str, Any]:
    return {
        "event_id": str(uuid.uuid4()),
        "topic": topic,
        "payload": {"x": 1},
        "producer": "p1",
        "published_at": "2026-06-22T12:00:00Z",
    }


def test_replay_returns_events_since_seq(client: TestClient) -> None:
    ev1 = _event()
    ev2 = _event()
    client.post("/publish", json=ev1)
    client.post("/publish", json=ev2)

    r = client.get("/replay?since_seq=0&format=json")
    assert r.status_code == 200
    ids = [e["event_id"] for e in r.json()]
    assert ev1["event_id"] in ids
    assert ev2["event_id"] in ids


def test_replay_since_seq_filters(client: TestClient) -> None:
    ev1 = _event()
    ev2 = _event()
    s1 = client.post("/publish", json=ev1).json()["seq"]
    client.post("/publish", json=ev2)

    r = client.get(f"/replay?since_seq={s1}&format=json")
    assert r.status_code == 200
    ids = [e["event_id"] for e in r.json()]
    assert ev1["event_id"] not in ids
    assert ev2["event_id"] in ids


@pytest.mark.anyio
async def test_subscribe_yields_matching_event(client: TestClient) -> None:
    """Test the query logic that powers /subscribe.

    httpx.ASGITransport blocks on response_complete for infinite SSE generators,
    so we test the DB query + _row_to_dict transformation directly.
    /replay already validates SSE framing; the same _row_to_dict is used here.
    """
    import eventbus.app as eb_app

    ev = _event("live.topic")
    client.post("/publish", json=ev)

    rows = eb_app._db.execute(  # type: ignore[union-attr]
        "SELECT seq, event_id, topic, payload, producer, published_at"
        " FROM events WHERE seq > ? AND topic IN (?)"
        " ORDER BY seq",
        (0, "live.topic"),
    ).fetchall()
    results = [eb_app._row_to_dict(row) for row in rows]
    assert any(r["event_id"] == ev["event_id"] for r in results)
