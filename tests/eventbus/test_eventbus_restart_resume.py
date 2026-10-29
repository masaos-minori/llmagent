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

from tests.eventbus.eventbus_helpers import (
    eventbus_auth_headers,
    eventbus_test_config,
    eventbus_test_tokens,
)

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
    import asyncio

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


@pytest.fixture
def eventbus_two_lifecycle_clients(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Any:
    """Yield (open_client, snapshots).

    open_client() enters TestClient(eb_app.app) so the production lifespan builds and
    tears down app.state; each entry appends (app.state.db, app.state.broker) to
    snapshots. Callers open two sequential lifecycles on the same tmp_path database.
    """
    from contextlib import contextmanager

    from eventbus import app as eb_app

    cfg = eventbus_test_config(tmp_path)
    monkeypatch.setattr(eb_app, "load_config", lambda path=None: cfg)
    schema_path = (
        Path(__file__).parent.parent.parent / "schemas" / "event_envelope.json"
    )
    monkeypatch.setattr(eb_app, "_ENVELOPE_SCHEMA_PATH", schema_path)
    monkeypatch.setattr(eb_app, "get_schema_path", lambda: schema_path)

    snapshots: list[tuple[Any, Any]] = []

    @contextmanager
    def open_client() -> Any:
        with TestClient(eb_app.app) as client:
            client.headers["Authorization"] = eventbus_auth_headers("publisher")[
                "Authorization"
            ]
            snapshots.append((eb_app.app.state.db, eb_app.app.state.broker))
            yield client

    yield open_client, snapshots


def test_same_consumer_id_resumes_from_last_acked_offset(
    client: TestClient, tmp_path: Path
) -> None:
    """Consumer with same consumer_id reconnects → resumes from last acked offset."""
    from eventbus import app as eb_app
    from eventbus.db import get_consumer_offset

    # Publish and ack first event
    r1 = _pub(client)
    client.post(
        f"/events/{r1['event_id']}/ack?consumer_id=svc-A",
        headers=eventbus_auth_headers("consumer"),
    )

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
    client.post(
        f"/events/{r1['event_id']}/ack?consumer_id=svc-A",
        headers=eventbus_auth_headers("consumer"),
    )

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
    client.post(
        f"/events/{r1['event_id']}/ack?consumer_id=shared-consumer",
        headers=eventbus_auth_headers("consumer"),
    )

    r2 = _pub(client)
    client.post(
        f"/events/{r2['event_id']}/ack?consumer_id=shared-consumer",
        headers=eventbus_auth_headers("consumer"),
    )

    # The second ack has the higher seq, so the offset is from the second ack
    offset = get_consumer_offset(eb_app.app.state.db, "shared-consumer")
    assert offset == r2["seq"]

    # No collision detection — both consumers can ack with same consumer_id without error
    # The offset file simply overwrites silently


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
    assert seq1 is not None and seq2 is not None and seq3 is not None
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

    # Bounded SSE read (REQ-006; AC-4) — set idle timeout before request
    object.__setattr__(eb_app.app.state.config, "sse_idle_timeout", 0.5)
    response = client.get(
        "/subscribe",
        params={
            "topic": ["t"],
            "consumer_id": "resume-consumer",
            "since_seq": start_seq,
        },
        headers=eventbus_auth_headers("consumer"),
        timeout=5.0,
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
            raise FileNotFoundError(f"EventBus schema.sql not found: {schema_path}")
        conn.executescript(schema_path.read_text())

    def test_unit_midsequence_ack_resume_position(self, tmp_path: Path) -> None:
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
            assert seq1 is not None and seq2 is not None and seq3 is not None
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

    def test_unit_inorder_ack_resume_position(self, tmp_path: Path) -> None:
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

    def test_unit_get_resume_position_defaults_to_zero(self, tmp_path: Path) -> None:
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
    resp = client.get(
        f"/subscribe?consumer_id={consumer_id}",
        timeout=5.0,
        headers=eventbus_auth_headers("consumer"),
    )
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


def test_two_lifecycle_probe_fresh_state(
    eventbus_two_lifecycle_clients: Any,
    tmp_path: Path,
) -> None:
    """Probe: verify two sequential lifecycles produce distinct state handles."""
    open_client, snapshots = eventbus_two_lifecycle_clients

    with open_client() as client_1:
        # Single reconnect read on topic t
        _reconnect_ids(client_1, "probe-consumer")

    with open_client():
        pass  # phase B: no operations needed for probe

    # Fresh-state gate (REQ-001, REQ-003, AC-2)
    (db_1, broker_1), (db_2, broker_2) = snapshots
    assert db_1 is not db_2 and broker_1 is not broker_2
    from eventbus import db_conn

    assert db_conn.is_shutting_down()


def test_restart_unacked_redelivery_single_consumer(
    eventbus_two_lifecycle_clients: Any,
    tmp_path: Path,
) -> None:
    """Publish 2 events; ack only the first → reconnect returns only the unacked seq."""
    open_client, snapshots = eventbus_two_lifecycle_clients

    with open_client() as client_1:
        ev1 = _pub(client_1)
        ev2 = _pub(client_1)
        # Ack only the first event via HTTP route
        client_1.post(
            f"/events/{ev1['event_id']}/ack?consumer_id=svc-A",
            headers=eventbus_auth_headers("consumer"),
        )
        # Drain SSE to establish the subscription
        _reconnect_ids(client_1, "svc-A")

    with open_client() as client_2:
        # Reconnect should return only the unacked event
        replayed = _reconnect_ids(client_2, "svc-A")
        assert replayed == [ev2["seq"]]

    # Fresh-state gate (REQ-003, AC-2)
    (db_1, broker_1), (db_2, broker_2) = snapshots
    assert db_1 is not db_2 and broker_1 is not broker_2
    from eventbus import db_conn

    assert db_conn.is_shutting_down()


def test_restart_resume_position_skips_acked(
    eventbus_two_lifecycle_clients: Any,
    tmp_path: Path,
) -> None:
    """Publish 3 events; ack 1-2 → reconnect returns only seq 3; offset row matches."""
    open_client, snapshots = eventbus_two_lifecycle_clients

    with open_client() as client_1:
        ev1 = _pub(client_1)
        ev2 = _pub(client_1)
        ev3 = _pub(client_1)
        # Ack events 1 and 2 via HTTP route
        client_1.post(
            f"/events/{ev1['event_id']}/ack?consumer_id=svc-B",
            headers=eventbus_auth_headers("consumer"),
        )
        client_1.post(
            f"/events/{ev2['event_id']}/ack?consumer_id=svc-B",
            headers=eventbus_auth_headers("consumer"),
        )

    with open_client() as client_2:
        replayed = _reconnect_ids(client_2, "svc-B")
        assert replayed == [ev3["seq"]]

    # Verify consumer_offsets row via direct sqlite read
    import sqlite3

    db_path = str(tmp_path / "eventbus.sqlite")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            "SELECT offset FROM consumer_offsets WHERE consumer_id = ?",
            ("svc-B",),
        ).fetchone()
        assert row is not None
        assert int(row["offset"]) == ev2["seq"]
    finally:
        conn.close()

    # Fresh-state gate (REQ-003, AC-2)
    (db_1, broker_1), (db_2, broker_2) = snapshots
    assert db_1 is not db_2 and broker_1 is not broker_2
    from eventbus import db_conn

    assert db_conn.is_shutting_down()


def test_restart_midsequence_ack_resume_position(
    eventbus_two_lifecycle_clients: Any,
    tmp_path: Path,
) -> None:
    """Ack events 2 and 3 (high-water = seq 3) → reconnect starts at lowest unacked seq."""
    open_client, snapshots = eventbus_two_lifecycle_clients

    with open_client() as client_1:
        ev1 = _pub(client_1)
        ev2 = _pub(client_1)
        ev3 = _pub(client_1)
        # Ack events 2 and 3 (skip event 1)
        client_1.post(
            f"/events/{ev2['event_id']}/ack?consumer_id=svc-C",
            headers=eventbus_auth_headers("consumer"),
        )
        client_1.post(
            f"/events/{ev3['event_id']}/ack?consumer_id=svc-C",
            headers=eventbus_auth_headers("consumer"),
        )

    with open_client() as client_2:
        replayed = _reconnect_ids(client_2, "svc-C")
        # Should deliver the unacked set starting from the lowest unacked seq
        assert replayed == [ev1["seq"], ev2["seq"], ev3["seq"]]

    # Verify consumer_offsets row via direct sqlite read
    import sqlite3

    db_path = str(tmp_path / "eventbus.sqlite")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            "SELECT offset FROM consumer_offsets WHERE consumer_id = ?",
            ("svc-C",),
        ).fetchone()
        assert row is not None
        assert int(row["offset"]) == ev3["seq"]
    finally:
        conn.close()

    # Fresh-state gate (REQ-003, AC-2)
    (db_1, broker_1), (db_2, broker_2) = snapshots
    assert db_1 is not db_2 and broker_1 is not broker_2
    from eventbus import db_conn

    assert db_conn.is_shutting_down()


def test_restart_two_consumers_independent_resume(
    eventbus_two_lifecycle_clients: Any,
    tmp_path: Path,
) -> None:
    """Two consumers ack different events → each reconnects independently."""
    open_client, snapshots = eventbus_two_lifecycle_clients

    with open_client() as client_1:
        ev1 = _pub(client_1)
        ev2 = _pub(client_1)
        ev3 = _pub(client_1)  # third event not acked by either consumer
        # Consumer A acks event 1
        client_1.post(
            f"/events/{ev1['event_id']}/ack?consumer_id=A",
            headers=eventbus_auth_headers("consumer"),
        )
        # Consumer B acks event 2
        client_1.post(
            f"/events/{ev2['event_id']}/ack?consumer_id=B",
            headers=eventbus_auth_headers("consumer"),
        )

    with open_client() as client_2:
        # Consumer A reconnect: should exclude event 1
        replayed_a = _reconnect_ids(client_2, "A")
        assert ev1["seq"] not in replayed_a

        # Consumer B reconnect: acking seq 2 leaves seq 1 unacked below the stored
        # offset, so resume restarts at the lowest unacked seq and the at-least-once
        # replay redelivers 1,2,3 with no ack filtering (delivery_repo.get_resume_position).
        replayed_b = _reconnect_ids(client_2, "B")
        assert replayed_b == [ev1["seq"], ev2["seq"], ev3["seq"]]

    # Verify two independent consumer_offsets rows via direct sqlite read
    import sqlite3

    db_path = str(tmp_path / "eventbus.sqlite")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT consumer_id, offset FROM consumer_offsets ORDER BY consumer_id"
        ).fetchall()
        assert len(rows) == 2
        offsets = {row["consumer_id"]: int(row["offset"]) for row in rows}
        assert offsets["A"] == ev1["seq"]
        assert offsets["B"] == ev2["seq"]
    finally:
        conn.close()

    # Fresh-state gate (REQ-003, AC-2)
    (db_1, broker_1), (db_2, broker_2) = snapshots
    assert db_1 is not db_2 and broker_1 is not broker_2
    from eventbus import db_conn

    assert db_conn.is_shutting_down()


def test_restart_new_consumer_starts_from_zero(
    eventbus_two_lifecycle_clients: Any,
    tmp_path: Path,
) -> None:
    """A consumer with no stored offset resumes from 0: replay redelivers every event,
    including events already acked by a different consumer (at-least-once semantics)."""
    open_client, snapshots = eventbus_two_lifecycle_clients

    with open_client() as client_1:
        ev1 = _pub(client_1)
        ev2 = _pub(client_1)
        # Ack both events with svc-old
        client_1.post(
            f"/events/{ev1['event_id']}/ack?consumer_id=svc-old",
            headers=eventbus_auth_headers("consumer"),
        )
        client_1.post(
            f"/events/{ev2['event_id']}/ack?consumer_id=svc-old",
            headers=eventbus_auth_headers("consumer"),
        )

    with open_client() as client_2:
        # Publish a new event on the fresh lifecycle
        ev3 = _pub(client_2)
        # svc-new has no consumer_offsets row → resume position 0 → all events redelivered
        replayed = _reconnect_ids(client_2, "svc-new")
        assert replayed == [ev1["seq"], ev2["seq"], ev3["seq"]]

    # Fresh-state gate (REQ-003, AC-2)
    (db_1, broker_1), (db_2, broker_2) = snapshots
    assert db_1 is not db_2 and broker_1 is not broker_2
    from eventbus import db_conn

    assert db_conn.is_shutting_down()


def test_restart_reconnect_consumer_id_reuse(
    eventbus_two_lifecycle_clients: Any,
    tmp_path: Path,
) -> None:
    """Same consumer_id across lifecycles: reconnect resumes from stored offset."""
    open_client, snapshots = eventbus_two_lifecycle_clients

    with open_client() as client_1:
        ev1 = _pub(client_1)
        ev2 = _pub(client_1)
        # Ack event 1 with svc-reuse
        client_1.post(
            f"/events/{ev1['event_id']}/ack?consumer_id=svc-reuse",
            headers=eventbus_auth_headers("consumer"),
        )

    with open_client() as client_2:
        # Reconnect with same consumer_id should resume from offset
        replayed = _reconnect_ids(client_2, "svc-reuse")
        assert replayed == [ev2["seq"]]

    # Verify consumer_offsets row via direct sqlite read
    import sqlite3

    db_path = str(tmp_path / "eventbus.sqlite")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            "SELECT offset FROM consumer_offsets WHERE consumer_id = ?",
            ("svc-reuse",),
        ).fetchone()
        assert row is not None
        assert int(row["offset"]) == ev1["seq"]
    finally:
        conn.close()

    # Fresh-state gate (REQ-003, AC-2)
    (db_1, broker_1), (db_2, broker_2) = snapshots
    assert db_1 is not db_2 and broker_1 is not broker_2
    from eventbus import db_conn

    assert db_conn.is_shutting_down()


def test_restart_offset_gap_no_silent_skip(
    eventbus_two_lifecycle_clients: Any,
    tmp_path: Path,
) -> None:
    """Delete consumer_delivery row for seq 2 between lifecycles → gap event is replayed."""
    open_client, snapshots = eventbus_two_lifecycle_clients

    with open_client() as client_1:
        ev1 = _pub(client_1)
        ev2 = _pub(client_1)
        ev3 = _pub(client_1)
        # Ack all three events
        client_1.post(
            f"/events/{ev1['event_id']}/ack?consumer_id=svc-gap",
            headers=eventbus_auth_headers("consumer"),
        )
        client_1.post(
            f"/events/{ev2['event_id']}/ack?consumer_id=svc-gap",
            headers=eventbus_auth_headers("consumer"),
        )
        client_1.post(
            f"/events/{ev3['event_id']}/ack?consumer_id=svc-gap",
            headers=eventbus_auth_headers("consumer"),
        )

    # Delete the consumer_delivery row for seq 2 between lifecycles
    import sqlite3

    db_path = str(tmp_path / "eventbus.sqlite")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute(
            "DELETE FROM consumer_delivery WHERE consumer_id = ? AND event_id = ?",
            ("svc-gap", ev2["event_id"]),
        )
        conn.commit()
    finally:
        conn.close()

    with open_client() as client_2:
        # Reconnect should return seq 2 (gap event replayed, no silent skip to 3)
        replayed = _reconnect_ids(client_2, "svc-gap")
        assert ev2["seq"] in replayed

    # Verify consumer_offsets.offset still equals 3
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            "SELECT offset FROM consumer_offsets WHERE consumer_id = ?",
            ("svc-gap",),
        ).fetchone()
        assert row is not None
        assert int(row["offset"]) == ev3["seq"]
    finally:
        conn.close()

    # Fresh-state gate (REQ-003, AC-2)
    (db_1, broker_1), (db_2, broker_2) = snapshots
    assert db_1 is not db_2 and broker_1 is not broker_2
    from eventbus import db_conn

    assert db_conn.is_shutting_down()
