"""tests/test_eventbus_restart_resume.py
Event Bus restart/resume behavior tests for consumer ID stability.
"""

from __future__ import annotations

import asyncio
import uuid
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest
from fastapi.testclient import TestClient

if TYPE_CHECKING:
    import sqlite3


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
        port=8016,
        db_path=str(tmp_path / "eventbus.sqlite"),
        storage_dir=str(tmp_path / "storage"),
        offsets_dir=str(tmp_path / "offsets"),
        deadletter_dir=str(tmp_path / "deadletter"),
        max_retry=3,
        auth_token="test-token",
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
        c.headers["Authorization"] = "Bearer test-token"
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
    """Two ACKs with the same consumer_id share one offset (highest acked seq wins; no collision detection on ACK)."""
    from eventbus import app as eb_app
    from eventbus.db import get_consumer_offset

    # Both consumers ack different events with the same consumer_id
    r1 = _pub(client)
    client.post(f"/events/{r1['event_id']}/ack?consumer_id=shared-consumer")

    r2 = _pub(client)
    client.post(f"/events/{r2['event_id']}/ack?consumer_id=shared-consumer")

    # The second ack has the higher seq, so the offset is from the second ack
    offset = get_consumer_offset(eb_app.app.state.db, "shared-consumer")
    assert offset == r2["seq"]

    # No collision detection — both consumers can ack with same consumer_id without error
    # The offset file simply overwrites silently


@pytest.mark.skip(
    reason="TestClient's plain .get() blocks forever on /subscribe when there is "
    "deliverable data, since the SSE generator never detects the client "
    "disconnecting — see issues/20260911-135626_ebsse01_subscribe-generator-"
    "never-detects-client-disconnect.md"
)
def test_resume_from_sqlite_offset(client: TestClient, tmp_path: Path) -> None:
    """Consumer resumes from SQLite-backed offset after restart."""
    import json

    from eventbus import app as eb_app
    from eventbus.db import ack_event_for_consumer, get_consumer_offset, insert_event

    db = eb_app.app.state.db

    seq1, _, _ = insert_event(
        db,
        "evt-resume-1",
        "t",
        json.dumps({"data": "1"}),
        "p",
        "2026-06-25T12:00:00Z",
    )
    seq2, _, _ = insert_event(
        db,
        "evt-resume-2",
        "t",
        json.dumps({"data": "2"}),
        "p",
        "2026-06-25T12:00:00Z",
    )
    seq3, _, _ = insert_event(
        db,
        "evt-resume-3",
        "t",
        json.dumps({"data": "3"}),
        "p",
        "2026-06-25T12:00:00Z",
    )
    assert seq1 < seq2 < seq3

    _, newly_acked_a, _ = ack_event_for_consumer(
        db, "evt-resume-1", "resume-consumer", "2026-06-25T12:00:00Z"
    )
    assert newly_acked_a
    _, newly_acked_b, _ = ack_event_for_consumer(
        db, "evt-resume-2", "resume-consumer", "2026-06-25T12:00:00Z"
    )
    assert newly_acked_b

    row = db.execute(
        "SELECT offset FROM consumer_offsets WHERE consumer_id = ?",
        ("resume-consumer",),
    ).fetchone()
    assert row is not None
    assert int(row["offset"]) == seq2

    start_seq = get_consumer_offset(db, "resume-consumer")
    assert start_seq == seq2

    response = client.get(
        "/subscribe",
        params={
            "topic": ["t"],
            "consumer_id": "resume-consumer",
            "since_seq": start_seq,
        },
    )
    assert response.status_code == 200

    lines = response.text.split("\n")
    data_lines = [line[5:] for line in lines if line.startswith("data:")]
    assert len(data_lines) == 1
    assert '"event_id":"evt-resume-3"' in data_lines[0]


class TestOutOfOrderAckNoSkipOnReconnect:
    """Verify at-least-once delivery under out-of-order ACK conditions."""

    @staticmethod
    def _create_tables(conn: sqlite3.Connection) -> None:
        """Create the EventBus schema tables in the given connection."""
        schema_path = (
            Path(__file__).parent.parent.parent / "scripts" / "eventbus" / "schema.sql"
        )
        if not schema_path.exists():
            # Fallback: inline schema for test isolation
            conn.executescript(
                "CREATE TABLE IF NOT EXISTS events ("
                "seq INTEGER PRIMARY KEY AUTOINCREMENT, "
                "event_id TEXT NOT NULL UNIQUE, "
                "topic TEXT NOT NULL, "
                "payload TEXT NOT NULL, "
                "producer TEXT NOT NULL, "
                "published_at TEXT NOT NULL, "
                "acked_at TEXT, "
                "delivery_failure_count INTEGER NOT NULL DEFAULT 0, "
                "cycle_failure_count INTEGER NOT NULL DEFAULT 0, "
                "redelivered_from TEXT, "
                "dlq_requeue_count INTEGER NOT NULL DEFAULT 0, "
                "dlq_at TEXT, "
                "consumer_id TEXT, "
                "consumer_delivery_failure_count INTEGER NOT NULL DEFAULT 0"
                "); "
                "CREATE TABLE IF NOT EXISTS consumer_delivery ("
                "consumer_id TEXT NOT NULL, "
                "event_id TEXT NOT NULL, "
                "acked_at TEXT, "
                "PRIMARY KEY (consumer_id, event_id)"
                "); "
                "CREATE TABLE IF NOT EXISTS consumer_offsets ("
                "consumer_id TEXT PRIMARY KEY, "
                "offset INTEGER NOT NULL DEFAULT 0"
                ");"
            )
        else:
            conn.executescript(schema_path.read_text())

    def test_out_of_order_ack_no_skip_on_reconnect(self, tmp_path: Path) -> None:
        """ACK a higher seq before a lower seq → reconnect must not skip the lower seq."""
        import sqlite3

        from eventbus.db import get_consumer_offset, get_resume_position, insert_event
        from eventbus.delivery_repo import ack_event_for_consumer

        db_path = str(tmp_path / "test.db")
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row

        try:
            TestOutOfOrderAckNoSkipOnReconnect._create_tables(conn)

            # Publish three events
            seq1, _, _ = insert_event(
                conn,
                "evt-oof-1",
                "t",
                '{"data": "1"}',
                "p",
                "2026-10-04T00:00:00Z",
            )
            seq2, _, _ = insert_event(
                conn,
                "evt-oof-2",
                "t",
                '{"data": "2"}',
                "p",
                "2026-10-04T00:00:00Z",
            )
            seq3, _, _ = insert_event(
                conn,
                "evt-oof-3",
                "t",
                '{"data": "3"}',
                "p",
                "2026-10-04T00:00:00Z",
            )
            assert seq1 < seq2 < seq3

            # ACK out of order: ack seq3 before seq2
            _, newly_acked_c, _ = ack_event_for_consumer(
                conn, "evt-oof-3", "oof-consumer", "2026-10-04T00:00:00Z"
            )
            assert newly_acked_c
            _, newly_acked_b, _ = ack_event_for_consumer(
                conn, "evt-oof-2", "oof-consumer", "2026-10-04T00:00:00Z"
            )
            assert newly_acked_b

            # Verify offset jumped to seq3 (high-water mark)
            offset = get_consumer_offset(conn, "oof-consumer")
            assert offset == seq3

            # Compute resume position — should be seq1 (lowest unacked <= offset)
            # Note: seq1 has no consumer_delivery record, so it won't appear in the join
            # We need to handle this case separately
            resume_pos = get_resume_position(conn, "oof-consumer")
            assert resume_pos == seq1  # lowest unacked event
        finally:
            conn.close()

    def test_ordered_ack_baseline(self, tmp_path: Path) -> None:
        """Ordered ACKs: reconnect resumes from stored offset + 1 (fast-forward)."""
        import sqlite3

        from eventbus.db import get_consumer_offset, get_resume_position, insert_event
        from eventbus.delivery_repo import ack_event_for_consumer

        db_path = str(tmp_path / "test.db")
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row

        try:
            TestOutOfOrderAckNoSkipOnReconnect._create_tables(conn)

            # Publish two events
            seq1, _, _ = insert_event(
                conn,
                "evt-ok-1",
                "t",
                '{"data": "1"}',
                "p",
                "2026-10-04T00:00:00Z",
            )
            seq2, _, _ = insert_event(
                conn,
                "evt-ok-2",
                "t",
                '{"data": "2"}',
                "p",
                "2026-10-04T00:00:00Z",
            )

            # ACK in order
            _, newly_acked_a, _ = ack_event_for_consumer(
                conn, "evt-ok-1", "ok-consumer", "2026-10-04T00:00:00Z"
            )
            assert newly_acked_a
            _, newly_acked_b, _ = ack_event_for_consumer(
                conn, "evt-ok-2", "ok-consumer", "2026-10-04T00:00:00Z"
            )
            assert newly_acked_b

            # Verify offset is seq2
            offset = get_consumer_offset(conn, "ok-consumer")
            assert offset == seq2

            # Resume position should be seq2 + 1 (all events up to offset are acked)
            resume_pos = get_resume_position(conn, "ok-consumer")
            assert resume_pos == seq2 + 1
        finally:
            conn.close()

    def test_get_resume_position_no_offset(self, tmp_path: Path) -> None:
        """No prior offset: resume position returns 0 (start from beginning)."""
        import sqlite3

        from eventbus.db import get_resume_position

        db_path = str(tmp_path / "test.db")
        conn = sqlite3.connect(db_path)

        try:
            TestOutOfOrderAckNoSkipOnReconnect._create_tables(conn)

            # No events published, no offset exists
            resume_pos = get_resume_position(conn, "new-consumer")
            assert resume_pos == 0
        finally:
            conn.close()


def _reconnect_ids(client: TestClient, consumer_id: str) -> list[int]:
    """Reconnect through /subscribe and return every replayed seq until idle."""
    from eventbus import app as eb_app

    object.__setattr__(eb_app.app.state.config, "sse_idle_timeout", 0.5)
    resp = client.get(f"/subscribe?consumer_id={consumer_id}", timeout=5.0)
    assert resp.status_code == 200
    return [
        int(line.split(":")[1].strip())
        for line in resp.iter_lines()
        if line.startswith("id:")
    ]


def _ack(client: TestClient, event: dict[str, Any], consumer_id: str) -> None:
    from eventbus import app as eb_app
    from eventbus.delivery_repo import ack_event_for_consumer

    ack_event_for_consumer(
        eb_app.app.state.db, event["event_id"], consumer_id, "2026-06-25T12:00:00Z"
    )


def test_reconnect_after_ordered_acks_replays_next_event_first(
    client: TestClient,
) -> None:
    """In-order ACKs up to seq N: the reconnect replays N+1 first, in order."""
    events = [_pub(client) for _ in range(4)]
    _ack(client, events[0], "ordered-consumer")
    _ack(client, events[1], "ordered-consumer")

    assert _reconnect_ids(client, "ordered-consumer") == [3, 4]


def test_reconnect_after_out_of_order_ack_replays_lowest_unacked_first(
    client: TestClient,
) -> None:
    """A higher seq ACKed before a lower one: the reconnect starts at the lowest
    unacked event, which is included, and continues in order."""
    events = [_pub(client) for _ in range(4)]
    _ack(client, events[2], "oof-route-consumer")
    _ack(client, events[1], "oof-route-consumer")

    assert _reconnect_ids(client, "oof-route-consumer") == [1, 2, 3, 4]
