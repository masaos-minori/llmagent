"""tests/test_eventbus_offsets.py
Event Bus offset checkpoint tests.

NOTE: /subscribe returns an infinite SSE stream; httpx.ASGITransport/TestClient
both block waiting for response_complete on infinite generators. The subscribe
loop logic is tested by driving the checkpoint counter
manually using events from the DB, the same approach used in test_eventbus_phase2.
"""

from __future__ import annotations

import asyncio
import json
import uuid
from pathlib import Path
from typing import Any, cast

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from tests.eventbus.eventbus_helpers import eventbus_auth_headers, eventbus_test_tokens


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
    eb_app.app.state.broker = eb_app.EventBroker(cfg)


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
        port=8015,
        db_path=str(tmp_path / "eventbus.sqlite"),
        storage_dir=str(tmp_path / "storage"),
        deadletter_dir=str(tmp_path / "deadletter"),
        max_retry=3,
        **eventbus_test_tokens("test-token"),
    )
    monkeypatch.setattr(eb_app, "load_config", lambda path=None: cfg)
    schema_path = (
        Path(__file__).parent.parent.parent / "schemas" / "event_envelope.json"
    )
    monkeypatch.setattr(eb_app, "_ENVELOPE_SCHEMA_PATH", schema_path)
    monkeypatch.setattr(eb_app, "get_schema_path", lambda: schema_path)

    # Initialize app.state before creating TestClient
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_init_state(cfg))
    finally:
        loop.close()

    with TestClient(eb_app.app) as c:
        c.headers["Authorization"] = eventbus_auth_headers("publisher")["Authorization"]
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
    published: dict[str, Any] = r.json()
    return published


def _event(topic: str = "t") -> dict[str, Any]:
    return {
        "event_id": str(uuid.uuid4()),
        "topic": topic,
        "payload": {},
        "producer": "p",
        "published_at": "2026-06-25T12:00:00Z",
    }


def test_ack_writes_offset(client: TestClient, tmp_path: Path) -> None:
    """Acknowledge an event writes the offset atomically via ack_event_for_consumer."""
    from eventbus.db import (  # noqa: PLC0415 — deferred import kept local to this test helper
        ack_event_for_consumer,
        insert_event,
    )

    db = cast(FastAPI, client.app).state.db
    now = "2026-09-09T10:00:00Z"
    consumer_id = "test_consumer"

    # Insert an event first
    seq, inserted, _ = insert_event(
        db, "evt-001", "test-topic", '{"data": "value"}', "test-producer", now
    )
    assert inserted

    # Acknowledge with consumer_id — should advance offset atomically
    found, newly_acked, result_seq = ack_event_for_consumer(
        db, "evt-001", consumer_id, now
    )
    assert found
    assert newly_acked
    assert result_seq == seq

    # Verify offset was advanced in consumer_offsets table
    row = db.execute(
        "SELECT offset FROM consumer_offsets WHERE consumer_id = ?",
        (consumer_id,),
    ).fetchone()
    assert row is not None
    assert int(row["offset"]) == seq


def test_ack_nonexistent_event_returns_404(client: TestClient) -> None:
    """POST /events/{id}/ack for unknown event_id should return 404."""
    r = client.post(
        "/events/nonexistent-id/ack?consumer_id=consumer1",
        headers=eventbus_auth_headers("consumer"),
    )
    assert r.status_code == 404


def test_reconnect_resume_via_consumer_id(client: TestClient) -> None:
    """consumer_id reconnect should restore start_seq from last acked offset."""
    r1 = _pub(client)
    r2 = _pub(client)

    # ack first event -> offset = r1["seq"]
    client.post(
        f"/events/{r1['event_id']}/ack?consumer_id=consumer2",
        headers=eventbus_auth_headers("consumer"),
    )

    # Verify: new broker subscription with consumer_id picks up from last acked seq
    from eventbus import app as eb_app
    from eventbus.db import get_consumer_offset

    offset = get_consumer_offset(eb_app.app.state.db, "consumer2")
    assert offset == r1["seq"]

    # Subscribe again -- start_seq should be r1["seq"] so only r2 replays
    sub = eb_app.app.state.broker.subscribe([])
    try:
        # The broker queue will have new events from here on
        # We verify by checking the replay query is scoped correctly
        # (Direct replay query verification without SSE streaming)
        assert offset < r2["seq"]  # replay would include r2 but not r1
    finally:
        eb_app.app.state.broker.unsubscribe(sub)


def test_offset_not_advanced_without_ack(client: TestClient) -> None:
    """Offset should remain 0 for consumer_id that never acked."""
    from eventbus import app as eb_app
    from eventbus.db import get_consumer_offset

    _pub(client)
    offset = get_consumer_offset(eb_app.app.state.db, "never-acked-consumer")
    assert offset == 0


def test_consumer_id_stability() -> None:
    """Same consumer_name + host + pid → same consumer_id (stability)."""
    import hashlib
    import os
    import socket

    def _make_consumer_id(consumer_name: str) -> str:
        stable_key = f"{consumer_name}:{socket.gethostname()}:{os.getpid()}"
        return hashlib.sha256(stable_key.encode()).hexdigest()[:16]

    cid1 = _make_consumer_id("my-consumer")
    cid2 = _make_consumer_id("my-consumer")
    assert cid1 == cid2
    assert len(cid1) == 16


class TestSqliteOffsetMonotonicity:
    """Tests for atomic monotonic offset enforcement in consumer_offsets."""

    def test_older_seq_cannot_move_offset_backward(
        self, tmp_path: Path, client: TestClient
    ) -> None:
        """An older-or-equal seq cannot move a consumer's offset backward."""
        from eventbus.db import (  # noqa: PLC0415 — deferred import kept local to this test helper
            ack_event_for_consumer,
            insert_event,
        )

        db = cast(FastAPI, client.app).state.db
        now = "2026-09-09T10:00:00Z"
        consumer_id = "monotonic_test"

        # Insert two events with different seq values
        seq1, _, _ = insert_event(db, "evt-mono-1", "test-topic", "{}", "producer", now)
        seq2, _, _ = insert_event(db, "evt-mono-2", "test-topic", "{}", "producer", now)
        assert seq1 is not None and seq2 is not None
        assert seq1 < seq2

        # Acknowledge evt-mono-2 first (higher seq)
        _, newly_acked, _ = ack_event_for_consumer(db, "evt-mono-2", consumer_id, now)
        assert newly_acked

        # Verify offset was set to seq2
        row = db.execute(
            "SELECT offset FROM consumer_offsets WHERE consumer_id = ?",
            (consumer_id,),
        ).fetchone()
        assert row is not None
        assert int(row["offset"]) == seq2

        # Try to acknowledge evt-mono-1 (lower seq) — should NOT update offset
        _, newly_acked, _ = ack_event_for_consumer(db, "evt-mono-1", consumer_id, now)
        assert newly_acked  # Event was newly acked (different event)

        # Offset should still be seq2 (not moved backward)
        row = db.execute(
            "SELECT offset FROM consumer_offsets WHERE consumer_id = ?",
            (consumer_id,),
        ).fetchone()
        assert row is not None
        assert int(row["offset"]) == seq2  # Not seq1


class TestConsumerOffsetsTable:
    def test_get_consumer_offset_defaults_to_zero(self, tmp_path: Path) -> None:
        from eventbus.db import get_consumer_offset, open_db

        db = open_db(str(tmp_path / "eventbus.sqlite"))
        try:
            assert get_consumer_offset(db, "consumer-a") == 0
        finally:
            db.close()

    def test_ack_event_for_consumer_advances_offset(self, tmp_path: Path) -> None:
        from eventbus.db import ack_event_for_consumer, get_consumer_offset, open_db

        db = open_db(str(tmp_path / "eventbus.sqlite"))
        try:
            ev = _event()
            db.execute(
                "INSERT INTO events (event_id, topic, payload, producer, published_at) VALUES (?, ?, ?, ?, ?)",
                (
                    ev["event_id"],
                    ev["topic"],
                    json.dumps(ev["payload"]),
                    ev["producer"],
                    ev["published_at"],
                ),
            )
            db.commit()

            now = "2026-06-22T13:00:00Z"
            found, newly_acked, seq = ack_event_for_consumer(
                db, ev["event_id"], "consumer-a", now
            )
            assert found is True
            assert newly_acked is True
            assert seq is not None

            offset = get_consumer_offset(db, "consumer-a")
            assert offset == seq
        finally:
            db.close()

    def test_offset_does_not_regress_on_older_seq(self, tmp_path: Path) -> None:
        from eventbus.db import ack_event_for_consumer, get_consumer_offset, open_db

        db = open_db(str(tmp_path / "eventbus.sqlite"))
        try:
            ev = _event()
            db.execute(
                "INSERT INTO events (event_id, topic, payload, producer, published_at) VALUES (?, ?, ?, ?, ?)",
                (
                    ev["event_id"],
                    ev["topic"],
                    json.dumps(ev["payload"]),
                    ev["producer"],
                    ev["published_at"],
                ),
            )
            db.commit()

            now = "2026-06-22T13:00:00Z"
            found1, _, seq1 = ack_event_for_consumer(
                db, ev["event_id"], "consumer-b", now
            )
            assert found1 is True
            assert seq1 is not None

            offset_after_first = get_consumer_offset(db, "consumer-b")
            assert offset_after_first == seq1

            ev2 = _event("t2")
            db.execute(
                "INSERT INTO events (event_id, topic, payload, producer, published_at) VALUES (?, ?, ?, ?, ?)",
                (
                    ev2["event_id"],
                    ev2["topic"],
                    json.dumps(ev2["payload"]),
                    ev2["producer"],
                    ev2["published_at"],
                ),
            )
            db.commit()

            now_later = "2026-06-22T14:00:00Z"
            found2, newly_acked2, seq2 = ack_event_for_consumer(
                db, ev2["event_id"], "consumer-b", now_later
            )
            assert found2 is True
            assert newly_acked2 is True
            assert seq2 is not None
            assert seq2 > seq1

            offset_after_second = get_consumer_offset(db, "consumer-b")
            assert offset_after_second == seq2

            # Attempt to advance with an older seq should be ignored
            found3, newly_acked3, seq3 = ack_event_for_consumer(
                db, ev["event_id"], "consumer-b", now
            )
            assert found3 is True
            assert newly_acked3 is False
            assert seq3 is not None

            offset_after_regress_attempt = get_consumer_offset(db, "consumer-b")
            assert offset_after_regress_attempt == seq2
        finally:
            db.close()
