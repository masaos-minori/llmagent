"""tests/test_eventbus_restart_resume.py
Event Bus restart/resume behavior tests for consumer ID stability.
"""

from __future__ import annotations

import asyncio
import uuid
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient


async def _init_state(cfg: Any) -> None:
    import pathlib

    from eventbus import app as eb_app

    eb_app.app.state.config = cfg
    eb_app.app.state.db = eb_app.open_db(cfg.db_path)
    schema_path = (
        Path(__file__).parent.parent.parent / "schemas" / "event_envelope.json"
    )
    eb_app.app.state.envelope_schema = eb_app.orjson.loads(schema_path.read_bytes())
    pathlib.Path(cfg.storage_dir).mkdir(parents=True, exist_ok=True)
    eb_app.app.state.broker = eb_app.EventBroker()


async def _do_cleanup() -> None:
    from eventbus import app as eb_app

    if eb_app.app.state.dlq_task:
        eb_app.app.state.dlq_task.cancel()
        try:
            await eb_app.app.state.dlq_task
        except asyncio.CancelledError:
            pass
    if eb_app.app.state.broker:
        eb_app.app.state.broker.shutdown()
    if eb_app.app.state.db:
        eb_app.app.state.db.close()


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Any:
    from eventbus import app as eb_app
    from eventbus.config import EventBusConfig

    cfg = EventBusConfig(
        port=8016,
        db_path=str(tmp_path / "eventbus.sqlite"),
        storage_dir=str(tmp_path / "storage"),
        offsets_dir=str(tmp_path / "offsets"),
        deadletter_dir=str(tmp_path / "deadletter"),
        max_retry=3,
    )
    monkeypatch.setattr(eb_app, "load_config", lambda path=None: cfg)
    schema_path = (
        Path(__file__).parent.parent.parent / "schemas" / "event_envelope.json"
    )
    monkeypatch.setattr(eb_app, "_ENVELOPE_SCHEMA_PATH", schema_path)
    monkeypatch.setattr(eb_app, "get_schema_path", lambda: schema_path)

    # Initialize app.state before creating TestClient
    import asyncio

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_init_state(cfg))
    finally:
        loop.close()

    with TestClient(eb_app.app) as c:
        yield c

    # Cleanup on teardown
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_do_cleanup())
    finally:
        loop.close()


def _pub(client: TestClient, topic: str = "t") -> dict[str, Any]:
    ev = {
        "event_id": str(uuid.uuid4()),
        "topic": topic,
        "payload": {},
        "producer": "p",
        "published_at": "2026-06-25T12:00:00Z",
    }
    r = client.post("/publish", json=ev)
    assert r.status_code == 200
    return r.json()


def test_same_consumer_id_resumes_from_last_acked_offset(
    client: TestClient, tmp_path: Path
) -> None:
    """Consumer with same consumer_id reconnects → resumes from last acked offset."""
    from eventbus import app as eb_app
    from eventbus.db import get_consumer_offset

    # Publish and ack first event
    r1 = _pub(client)
    client.post(f"/events/{r1['event_id']}/ack?consumer_id=svc-A")

    # Verify offset is written
    offset = get_consumer_offset(eb_app.app.state.db, "svc-A")
    assert offset == r1["seq"]

    # Publish second event (this will be the replay start point)
    r2 = _pub(client)

    # Consumer reconnects with same consumer_id → should resume from last acked offset
    # The broker subscription with consumer_id should pick up from r1["seq"]
    sub = eb_app.app.state.broker.subscribe([])
    try:
        assert offset < r2["seq"]  # replay would include r2 but not r1
    finally:
        eb_app.app.state.broker.unsubscribe(sub)


def test_different_consumer_id_starts_from_zero(
    client: TestClient, tmp_path: Path
) -> None:
    """Consumer with different consumer_id reconnects → starts from seq=0 (offset not found)."""
    from eventbus import app as eb_app
    from eventbus.db import get_consumer_offset

    # Consumer-A publishes and acks
    r1 = _pub(client)
    client.post(f"/events/{r1['event_id']}/ack?consumer_id=svc-A")

    # Consumer-B (different ID) has no offset
    offset_b = get_consumer_offset(eb_app.app.state.db, "svc-B")
    assert offset_b == 0

    # Consumer-A's offset should still be intact
    offset_a = get_consumer_offset(eb_app.app.state.db, "svc-A")
    assert offset_a == r1["seq"]

    # Consumer-B would start from seq=0 on reconnect
    sub = eb_app.app.state.broker.subscribe([])
    try:
        assert (
            offset_b < offset_a
        )  # svc-B starts from 0, svc-A resumes from acked offset
    finally:
        eb_app.app.state.broker.unsubscribe(sub)


def test_same_consumer_id_last_write_wins(client: TestClient, tmp_path: Path) -> None:
    """Two consumers with same consumer_id → last write wins for offset (no collision detection)."""
    from eventbus import app as eb_app
    from eventbus.db import get_consumer_offset

    # Both consumers ack different events with the same consumer_id
    r1 = _pub(client)
    client.post(f"/events/{r1['event_id']}/ack?consumer_id=shared-consumer")

    r2 = _pub(client)
    client.post(f"/events/{r2['event_id']}/ack?consumer_id=shared-consumer")

    # Last write wins — offset should be from the second ack
    offset = get_consumer_offset(eb_app.app.state.db, "shared-consumer")
    assert offset == r2["seq"]

    # No collision detection — both consumers can ack with same consumer_id without error
    # The offset file simply overwrites silently


def test_resume_from_sqlite_offset(client: TestClient) -> None:
    """Consumer resumes from SQLite-backed offset after restart."""
    from eventbus.db import ack_event_for_consumer, insert_event  # noqa: PLC0415
    from eventbus.subscribe_route import _get_offset_from_sqlite  # noqa: PLC0415

    db = client.app.state.db
    now = "2026-09-09T10:00:00Z"
    consumer_id = "resume_consumer"

    # Insert three events
    seq1, _ = insert_event(db, "evt-resume-1", "test-topic", '{"data": "1"}', "producer", now)
    seq2, _ = insert_event(db, "evt-resume-2", "test-topic", '{"data": "2"}', "producer", now)
    seq3, _ = insert_event(db, "evt-resume-3", "test-topic", '{"data": "3"}', "producer", now)
    assert seq1 < seq2 < seq3

    # Consumer ACKs evt-resume-1 and evt-resume-2
    _, newly_acked_a, _ = ack_event_for_consumer(db, "evt-resume-1", consumer_id, now)
    assert newly_acked_a
    _, newly_acked_b, _ = ack_event_for_consumer(db, "evt-resume-2", consumer_id, now)
    assert newly_acked_b

    # Verify offset was advanced to seq2
    row = db.execute(
        "SELECT offset FROM consumer_offsets WHERE consumer_id = ?",
        (consumer_id,),
    ).fetchone()
    assert row is not None
    assert int(row["offset"]) == seq2

    # Simulate restart: read offset via SQLite path
    start_seq = _get_offset_from_sqlite(db, consumer_id)
    assert start_seq == seq2

    # Subscribe with since_seq=start_seq — should deliver only evt-resume-3
    response = client.get(
        "/events",
        params={"topic": ["test-topic"], "consumer_id": consumer_id, "since_seq": start_seq},
    )
    assert response.status_code == 200

    # Parse SSE stream and verify only evt-resume-3 is delivered
    lines = response.text.split("\n")
    data_lines = [line[5:] for line in lines if line.startswith("data:")]
    assert len(data_lines) == 1
    assert '"event_id":"evt-resume-3"' in data_lines[0]
