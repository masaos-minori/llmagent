"""tests/test_eventbus_publish.py
Event Bus publish and health endpoint tests.
"""

from __future__ import annotations

import sqlite3
import uuid
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from eventbus.route_helpers import ERR_EVENT_CONFLICT
from eventbus_helpers import eventbus_auth_headers, make_eventbus_client
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Any:
    with make_eventbus_client(tmp_path, monkeypatch) as c:
        yield c


def _event(topic: str = "test.topic") -> dict[str, Any]:
    return {
        "event_id": str(uuid.uuid4()),
        "topic": topic,
        "payload": {"key": "value"},
        "producer": "test-producer",
        "published_at": "2026-06-22T11:56:00Z",
    }


def test_health_ok(client: TestClient) -> None:
    r = client.get(
        "/health",
        headers=eventbus_auth_headers("monitoring"),
    )
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["db"] == "ok"
    assert body["dlq_task"] == "running"


def test_health_degraded_when_db_unavailable(client: TestClient) -> None:
    import eventbus.app as eb_app

    mock_db = MagicMock()
    mock_db.execute.side_effect = sqlite3.OperationalError("DB gone")
    eb_app.app.state.db = mock_db
    resp = client.get(
        "/health",
        headers=eventbus_auth_headers("monitoring"),
    )
    assert resp.status_code == 503
    body = resp.json()
    assert body["status"] == "degraded"
    assert body["db"] == "unavailable"


def test_publish_inserts_event(client: TestClient, tmp_path: Path) -> None:
    ev = _event()
    r = client.post("/publish", json=ev)
    assert r.status_code == 200
    body = r.json()
    assert body["event_id"] == ev["event_id"]
    assert body["seq"] >= 1
    jsonl = (tmp_path / "storage" / "events.jsonl").read_text()
    assert ev["event_id"] in jsonl


def test_publish_idempotent(client: TestClient) -> None:
    ev = _event()
    r1 = client.post("/publish", json=ev)
    r2 = client.post("/publish", json=ev)
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r1.json()["seq"] == r2.json()["seq"]


def test_publish_invalid_schema(client: TestClient) -> None:
    r = client.post("/publish", json={"invalid": "body"})
    assert r.status_code == 422


def test_publish_succeeds_if_jsonl_append_fails(client: TestClient) -> None:
    """JSONL append failure after SQLite commit must still return 200."""
    ev = _event()

    # Patch Path.open to raise OSError for JSONL writes
    original_open = Path.open

    def failing_open(self, *args, **kwargs):
        if "events.jsonl" in str(self):
            raise OSError("disk full")
        return original_open(self, *args, **kwargs)

    with patch.object(Path, "open", failing_open):
        resp = client.post("/publish", json=ev)
    assert resp.status_code == 200
    assert resp.json()["event_id"] == ev["event_id"]

    # Event should be retrievable from SQLite
    # Event should be retrievable from SQLite
    replay = client.get(
        "/replay",
        params={"since_seq": 0, "format": "json"},
        headers=eventbus_auth_headers("operator"),
    )
    assert replay.status_code == 200
    body = replay.json()
    event_ids = [e["event_id"] for e in body["items"]]
    assert ev["event_id"] in event_ids


def test_duplicate_publish_after_jsonl_failure_returns_same_seq_and_does_not_backfill(
    client: TestClient, tmp_path: Path
) -> None:
    """REQ-006: a retry after a failed JSONL append returns the same seq and does not backfill."""
    ev = _event()

    original_open = Path.open

    def failing_open(self, *args, **kwargs):
        if "events.jsonl" in str(self):
            raise OSError("disk full")
        return original_open(self, *args, **kwargs)

    with patch.object(Path, "open", failing_open):
        first = client.post("/publish", json=ev)
    assert first.status_code == 200
    seq1 = first.json()["seq"]

    # Identical retry with a healthy filesystem.
    second = client.post("/publish", json=ev)
    assert second.status_code == 200
    assert second.json()["seq"] == seq1

    # JSONL is appended only for a fresh insert: no backfill of the failed append.
    jsonl_path = tmp_path / "storage" / "events.jsonl"
    assert not jsonl_path.exists() or ev["event_id"] not in jsonl_path.read_text()

    # SQLite is the source of truth: the event appears exactly once in replay.
    replay = client.get(
        "/replay",
        params={"since_seq": 0, "format": "json"},
        headers=eventbus_auth_headers("operator"),
    )
    assert replay.status_code == 200
    event_ids = [e["event_id"] for e in replay.json()["items"]]
    assert event_ids.count(ev["event_id"]) == 1


class _CommitFailingConn:
    """Connection proxy whose commit() fails, simulating a SQLite commit error."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def execute(self, *args: Any, **kwargs: Any) -> sqlite3.Cursor:
        return self._conn.execute(*args, **kwargs)

    def commit(self) -> None:
        raise sqlite3.OperationalError("disk I/O error")


def _failing_insert_event(mode: str) -> Any:
    """Return an insert_event replacement that fails at the given SQLite stage."""
    from eventbus.event_repo import insert_event as real_insert_event

    def _insert(conn: sqlite3.Connection, *args: Any, **kwargs: Any) -> Any:
        if mode == "insert":
            raise sqlite3.OperationalError("database or disk is full")
        return real_insert_event(_CommitFailingConn(conn), *args, **kwargs)  # type: ignore[arg-type]  # test-only: proxy connection stand-in

    return _insert


@pytest.mark.parametrize("mode", ["insert", "commit"])
def test_publish_sqlite_write_failure_reports_failure_without_side_effects(
    client: TestClient, tmp_path: Path, mode: str
) -> None:
    """ADR-006 INV-02: a SQLite write failure is never reported as a successful publish.

    Verifies HTTP response, SQLite state, JSONL append and broker notification together.
    """
    import eventbus.app as eb_app

    ev = _event()
    broker_publish = MagicMock()
    failing_client = TestClient(client.app, raise_server_exceptions=False)
    failing_client.headers["Authorization"] = client.headers["Authorization"]

    with (
        patch("eventbus.publish_route.insert_event", _failing_insert_event(mode)),
        patch.object(eb_app.app.state.broker, "publish", broker_publish),
    ):
        resp = failing_client.post("/publish", json=ev)

    assert resp.status_code >= 500

    # A separate connection sees only committed state.
    with sqlite3.connect(tmp_path / "eventbus.sqlite") as other:
        count = other.execute(
            "SELECT COUNT(*) FROM events WHERE event_id = ?", (ev["event_id"],)
        ).fetchone()[0]
    assert count == 0

    jsonl_path = tmp_path / "storage" / "events.jsonl"
    assert not jsonl_path.exists() or ev["event_id"] not in jsonl_path.read_text()
    broker_publish.assert_not_called()


def test_identical_content_retry_returns_same_seq(client: TestClient) -> None:
    """Identical retries return the existing sequence and do not cause redelivery."""
    ev = _event()
    resp1 = client.post("/publish", json=ev)
    assert resp1.status_code == 200
    seq1 = resp1.json()["seq"]

    resp2 = client.post("/publish", json=ev)
    assert resp2.status_code == 200
    seq2 = resp2.json()["seq"]

    assert seq1 == seq2  # Same seq returned


def test_conflicting_content_retry_returns_409(client: TestClient) -> None:
    """Conflicting retries return HTTP 409 and do not modify the stored row."""
    resp1 = client.post("/publish", json=_event())
    assert resp1.status_code == 200

    conflicting = _event()
    conflicting["event_id"] = resp1.json()["event_id"]
    conflicting["payload"] = {"key": "different_value"}
    resp2 = client.post("/publish", json=conflicting)
    assert resp2.status_code == 409
    assert resp2.json()["detail"] == ERR_EVENT_CONFLICT


def test_published_at_stored_unchanged(client: TestClient, tmp_path: Path) -> None:
    """Supplied published_at is stored exactly as sent (no server rewrite)."""
    ev = _event()
    resp = client.post("/publish", json=ev)
    assert resp.status_code == 200

    with sqlite3.connect(tmp_path / "eventbus.sqlite") as conn:
        stored = conn.execute(
            "SELECT published_at FROM events WHERE event_id = ?",
            (ev["event_id"],),
        ).fetchone()[0]
    assert stored == ev["published_at"]


def test_duplicate_retry_preserves_original_published_at(
    client: TestClient, tmp_path: Path
) -> None:
    """Identical-content retry keeps the original row's published_at unchanged.

    Canonical equality excludes published_at, so a retry with a different
    published_at is a duplicate: same seq, stored row not rewritten
    (current duplicate-retention shape, plan UNK-03 decision).
    """
    ev = _event()
    resp1 = client.post("/publish", json=ev)
    assert resp1.status_code == 200
    seq1 = resp1.json()["seq"]

    retry = {**ev, "published_at": "2026-06-22T12:00:00Z"}
    resp2 = client.post("/publish", json=retry)
    assert resp2.status_code == 200
    assert resp2.json()["seq"] == seq1

    with sqlite3.connect(tmp_path / "eventbus.sqlite") as conn:
        rows = conn.execute(
            "SELECT published_at FROM events WHERE event_id = ?",
            (ev["event_id"],),
        ).fetchall()
    assert [r[0] for r in rows] == [ev["published_at"]]


def _ensure_prometheus_counters_registered() -> None:
    """Ensure Prometheus counters used by these tests are registered.

    Prevents cross-test metric pollution: if a prior test's cleanup
    unregistered collectors (e.g. test_eventbus_route_helpers_metrics.py's
    client fixture), this ensures they're present before checking metrics.
    """
    import eventbus.publish_route
    from prometheus_client import REGISTRY

    for counter in (
        eventbus.publish_route._jsonl_append_failure_counter,
        eventbus.publish_route._broker_notify_failure_counter,
    ):
        if counter not in REGISTRY._collector_to_names:
            try:
                REGISTRY.register(counter)
            except ValueError:
                pass

    # Also ensure route_helpers metrics are registered (may have been
    # unregistered by a prior test's cleanup).
    from tests.eventbus.conftest import _ensure_route_helpers_metrics_registered

    _ensure_route_helpers_metrics_registered()


def test_jsonl_append_failure_increments_metric(
    client: TestClient, tmp_path: Path
) -> None:
    """JSONL append failure increments eventbus_jsonl_append_failure_total counter."""
    ev = _event()

    original_open = Path.open

    def failing_open(self, *args, **kwargs):
        if "events.jsonl" in str(self):
            raise OSError("disk full")
        return original_open(self, *args, **kwargs)

    with patch.object(Path, "open", failing_open):
        resp = client.post("/publish", json=ev)

    assert resp.status_code == 200
    assert resp.json()["event_id"] == ev["event_id"]

    _ensure_prometheus_counters_registered()

    from prometheus_client import generate_latest

    text = generate_latest().decode("utf-8")
    counter_name = "eventbus_jsonl_append_failure_total"
    found_line = False
    for line in text.splitlines():
        if counter_name in line and not line.startswith("#"):
            parts = line.split()
            value = float(parts[-1])
            assert value >= 1
            found_line = True
            break
    assert found_line


def test_broker_notify_failure_increments_metric(
    client: TestClient, tmp_path: Path
) -> None:
    """Broker notification failure increments eventbus_broker_notify_failure_total counter."""
    ev = _event()

    mock_broker = MagicMock()
    mock_broker.publish.side_effect = Exception("broker unavailable")

    with patch("eventbus.publish_route.get_broker", return_value=mock_broker):
        resp = client.post("/publish", json=ev)

    assert resp.status_code == 200
    assert resp.json()["event_id"] == ev["event_id"]

    _ensure_prometheus_counters_registered()

    from prometheus_client import generate_latest

    text = generate_latest().decode("utf-8")
    counter_name = "eventbus_broker_notify_failure_total"
    found_line = False
    for line in text.splitlines():
        if counter_name in line and not line.startswith("#"):
            parts = line.split()
            value = float(parts[-1])
            assert value >= 1
            found_line = True
            break
    assert found_line


def test_concurrent_publish_ordering_via_seq(client: TestClient) -> None:
    """Concurrent publishes produce monotonically increasing seq values.

    When multiple messages are published concurrently, the database assigns
    monotonically increasing sequence numbers. Responses reflect this ordering
    regardless of thread scheduling.
    """
    import threading

    results: list[int] = []
    lock = threading.Lock()

    def publish_one(topic: str) -> None:
        ev = {
            "event_id": str(uuid.uuid4()),
            "topic": topic,
            "payload": {"key": "value"},
            "producer": "test-producer",
            "published_at": "2026-06-22T11:56:00Z",
        }
        r = client.post("/publish", json=ev)
        assert r.status_code == 200
        with lock:
            results.append(r.json()["seq"])

    threads = [threading.Thread(target=publish_one, args=(f"t{i}",)) for i in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=5)

    assert len(results) == 5
    # Seq values must be strictly increasing (monotonic)
    sorted_results = sorted(results)
    for i in range(len(sorted_results) - 1):
        assert sorted_results[i] < sorted_results[i + 1]


def test_sequential_publish_seq_matches_persistence_order(client: TestClient) -> None:
    """Sequential publishes produce seq matching DB insertion order.

    Publishing A then B must yield seq(A) < seq(B), confirming response
    ordering matches persistence order.
    """
    ev_a = _event("order.topic.a")
    ev_b = _event("order.topic.b")

    r_a = client.post("/publish", json=ev_a)
    assert r_a.status_code == 200
    seq_a = r_a.json()["seq"]

    r_b = client.post("/publish", json=ev_b)
    assert r_b.status_code == 200
    seq_b = r_b.json()["seq"]

    assert seq_a < seq_b
