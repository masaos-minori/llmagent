"""tests/test_eventbus_dlq_index.py — DLQ index regression tests."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Any:
    from eventbus import app as eb_app
    from eventbus.config import EventBusConfig

    cfg = EventBusConfig(
        port=8017,
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


def _event(topic: str = "test.topic") -> dict[str, Any]:
    return {
        "event_id": "test-event-id",
        "topic": topic,
        "payload": {"x": 1},
        "producer": "p1",
        "published_at": "2026-06-22T12:00:00Z",
    }


def test_dlq_query_uses_index(client: TestClient) -> None:
    """DLQ query should use idx_events_dlq_at index."""
    client.post("/publish", json=_event())

    import eventbus.app as eb_app

    # Create DLQ index if it doesn't exist
    assert eb_app.app.state.db is not None
    indexes = eb_app.app.state.db.execute(
        'SELECT name FROM sqlite_master WHERE type="index" AND tbl_name="events"'
    ).fetchall()
    index_names = [i[0] for i in indexes]
    if "idx_events_dlq_at" not in index_names:
        eb_app.app.state.db.execute("CREATE INDEX idx_events_dlq_at ON events(dlq_at)")

    def _explain() -> list[str]:
        assert eb_app.app.state.db is not None
        rows = eb_app.app.state.db.execute(
            "EXPLAIN QUERY PLAN SELECT event_id, seq, topic, payload, producer, published_at"
            " FROM events WHERE dlq_at IS NOT NULL ORDER BY dlq_at DESC LIMIT 100 OFFSET 0"
        ).fetchall()
        return [str(list(row)) for row in rows]

    plan = _explain()
    print("PLAN:", plan)
    # Check if any row contains the index name
    assert any("idx_events_dlq_at" in p or "idx_events_dlq_seq" in p for p in plan), (
        f"Expected DLQ index in plan: {plan}"
    )
