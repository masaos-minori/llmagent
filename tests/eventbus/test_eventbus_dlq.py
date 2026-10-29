from __future__ import annotations

import asyncio
import uuid
from pathlib import Path
from typing import Any

import orjson
import pytest
from fastapi.testclient import TestClient

from tests.eventbus.eventbus_helpers import eventbus_auth_headers, eventbus_test_tokens


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Any:
    from eventbus import app as eb_app
    from eventbus.config import EventBusConfig

    cfg = EventBusConfig(
        port=8015,
        db_path=str(tmp_path / "eventbus.sqlite"),
        storage_dir=str(tmp_path / "storage"),
        deadletter_dir=str(tmp_path / "deadletter"),
        max_retry=2,
        **eventbus_test_tokens("test-token"),
    )
    monkeypatch.setattr(eb_app, "load_config", lambda path=None: cfg)
    schema_path = (
        Path(__file__).parent.parent.parent / "schemas" / "event_envelope.json"
    )
    monkeypatch.setattr(eb_app, "get_schema_path", lambda: schema_path)

    with TestClient(eb_app.app) as c:
        c.headers["Authorization"] = eventbus_auth_headers("publisher")["Authorization"]
        yield c


def _event(topic: str = "t") -> dict[str, Any]:
    return {
        "event_id": str(uuid.uuid4()),
        "topic": topic,
        "payload": {},
        "producer": "p",
        "published_at": "2026-06-22T12:00:00Z",
    }


def _dlq_failure_counter() -> float:
    """Current DLQ file-write failure counter, registering it if needed."""
    from eventbus import dlq
    from prometheus_client import REGISTRY

    # Ensure the counter is registered (may have been unregistered by a prior test's cleanup)
    if dlq._dlq_file_write_failure_counter not in REGISTRY._collector_to_names:
        try:
            REGISTRY.register(dlq._dlq_file_write_failure_counter)
        except ValueError:
            pass
    return REGISTRY.get_sample_value("eventbus_dlq_file_write_failure_total") or 0.0


def _make_promotable(db: Any, event_id: str) -> None:
    """Insert a consumer_delivery record at the retry limit so the event is promotable."""
    db.execute(
        "INSERT INTO consumer_delivery (consumer_id, event_id, acked, consumer_delivery_failure_count) VALUES (?, ?, 0, 2)",
        ("consumer-A", event_id),
    )
    db.commit()


def test_dlq_promotion_when_retry_exhausted(client: TestClient, tmp_path: Path) -> None:
    from eventbus.db import open_db
    from eventbus.dlq import sweep_orphans

    db = open_db(str(tmp_path / "eventbus.sqlite"))
    ev = _event()
    client.post("/publish", json=ev)
    # Create consumer_delivery record required for REQ-002 per-consumer DLQ promotion
    db.execute(
        "INSERT INTO consumer_delivery (consumer_id, event_id, acked, consumer_delivery_failure_count) VALUES (?, ?, 0, 2)",
        ("consumer-A", ev["event_id"]),
    )
    db.commit()

    n = sweep_orphans(db, str(tmp_path / "deadletter"), max_retry=2)
    assert n == 1
    dlq_file = tmp_path / "deadletter" / f"{ev['event_id']}.json"
    assert dlq_file.exists()
    record = orjson.loads(dlq_file.read_bytes())
    assert record["event_id"] == ev["event_id"]
    assert record["dlq_at"] is not None


def test_dlq_list(client: TestClient, tmp_path: Path) -> None:
    from eventbus.db import open_db
    from eventbus.dlq import sweep_orphans

    db = open_db(str(tmp_path / "eventbus.sqlite"))
    ev = _event()
    client.post("/publish", json=ev)
    # Create consumer_delivery record required for REQ-002 per-consumer DLQ promotion
    db.execute(
        "INSERT INTO consumer_delivery (consumer_id, event_id, acked, consumer_delivery_failure_count) VALUES (?, ?, 0, 2)",
        ("consumer-A", ev["event_id"]),
    )
    db.commit()

    sweep_orphans(db, str(tmp_path / "deadletter"), max_retry=2)

    r = client.get("/dlq", headers=eventbus_auth_headers("operator"))
    assert r.status_code == 200
    body = r.json()
    ids = [e["event_id"] for e in body["items"]]
    assert ev["event_id"] in ids
    for item in body["items"]:
        assert "delivery_failure_count" not in item
        assert "cycle_failure_count" not in item


def test_dlq_requeue(client: TestClient, tmp_path: Path) -> None:
    from eventbus.db import open_db
    from eventbus.dlq import sweep_orphans

    db = open_db(str(tmp_path / "eventbus.sqlite"))
    ev = _event()
    pub = client.post("/publish", json=ev)
    assert pub.status_code == 200
    original_seq = pub.json()["seq"]
    # Create consumer_delivery record required for REQ-002 per-consumer DLQ promotion
    db.execute(
        "INSERT INTO consumer_delivery (consumer_id, event_id, acked, consumer_delivery_failure_count) VALUES (?, ?, 0, 2)",
        ("consumer-A", ev["event_id"]),
    )
    db.commit()

    sweep_orphans(db, str(tmp_path / "deadletter"), max_retry=2)

    r = client.post(
        f"/dlq/{ev['event_id']}/requeue", headers=eventbus_auth_headers("operator")
    )
    assert r.status_code == 200
    body = r.json()
    assert body["requeued"] is True
    assert "new_event_id" in body
    assert body["new_event_id"] != ev["event_id"]
    uuid.UUID(body["new_event_id"], version=4)
    # new_event_id and new_seq come from the same atomic result (REQ-001,
    # REQ-003): the descendant row insert and the seq assignment happen in one
    # transaction, so new_seq is strictly greater than the original seq.
    assert "new_seq" in body
    assert isinstance(body["new_seq"], int)
    assert body["new_seq"] > original_seq

    # Original event remains in DLQ (lineage model: original row's dlq_at IS NOT NULL)
    r2 = client.get("/dlq", headers=eventbus_auth_headers("operator"))
    body2 = r2.json()
    ids = [e["event_id"] for e in body2["items"]]
    assert ev["event_id"] in ids

    # New event exists with redelivered_from set
    new_row = db.execute(
        "SELECT event_id, redelivered_from FROM events WHERE event_id = ?",
        (body["new_event_id"],),
    ).fetchone()
    assert new_row is not None
    assert new_row["redelivered_from"] == ev["event_id"]


def test_requeue_increments_dlq_requeue_count(
    client: TestClient, tmp_path: Path
) -> None:
    from eventbus.db import open_db
    from eventbus.dlq import sweep_orphans

    db = open_db(str(tmp_path / "eventbus.sqlite"))
    ev = _event()
    client.post("/publish", json=ev)
    # Create consumer_delivery record required for REQ-002 per-consumer DLQ promotion
    db.execute(
        "INSERT INTO consumer_delivery (consumer_id, event_id, acked, consumer_delivery_failure_count) VALUES (?, ?, 0, 2)",
        ("consumer-A", ev["event_id"]),
    )
    db.commit()

    sweep_orphans(db, str(tmp_path / "deadletter"), max_retry=2)

    # Requeue once — new row inserted with redelivered_from
    r = client.post(
        f"/dlq/{ev['event_id']}/requeue", headers=eventbus_auth_headers("operator")
    )
    assert r.status_code == 200
    body = r.json()
    assert body["requeued"] is True
    new_event_id = body["new_event_id"]

    # Original row's dlq_requeue_count incremented
    orig_row = db.execute(
        "SELECT dlq_requeue_count, dlq_at FROM events WHERE event_id = ?",
        (ev["event_id"],),
    ).fetchone()
    assert orig_row["dlq_requeue_count"] == 1
    assert orig_row["dlq_at"] is not None

    # New row has redelivered_from set
    new_row = db.execute(
        "SELECT redelivered_from FROM events WHERE event_id = ?",
        (new_event_id,),
    ).fetchone()
    assert new_row["redelivered_from"] == ev["event_id"]
    assert orig_row["dlq_at"] is not None

    # Exhaust retries again — should promote to DLQ
    # Need to create a consumer_delivery record for the new descendant event
    db.execute(
        "INSERT INTO consumer_delivery (consumer_id, event_id, acked, consumer_delivery_failure_count) VALUES (?, ?, 0, 2)",
        ("consumer-A", new_event_id),
    )
    db.commit()

    n = sweep_orphans(db, str(tmp_path / "deadletter"), max_retry=2)
    assert n == 1
    dlq_file = tmp_path / "deadletter" / f"{new_event_id}.json"
    assert dlq_file.exists()


def test_inline_dlq_promotion_on_nack(client: TestClient, tmp_path: Path) -> None:
    from eventbus.db import open_db

    db = open_db(str(tmp_path / "eventbus.sqlite"))
    ev = _event()
    client.post("/publish", json=ev)

    # First nack — consumer_delivery_failure_count becomes 1, below threshold of 2
    r = client.post(
        f"/nack?event_id={ev['event_id']}&consumer_id=test-consumer"
        "&idempotency_key=inline-nack-key-1",
        headers=eventbus_auth_headers("consumer"),
    )
    assert r.status_code == 200
    assert r.json()["consumer_delivery_failure_count"] == 1
    assert "dlq_promoted" not in r.json()

    # Second nack — consumer_delivery_failure_count becomes 2, hits threshold, inline promote
    # A distinct idempotency key is required: the same key would be skipped
    # as a duplicate NACK attempt (REQ-002 idempotency guard).
    r = client.post(
        f"/nack?event_id={ev['event_id']}&consumer_id=test-consumer"
        "&idempotency_key=inline-nack-key-2",
        headers=eventbus_auth_headers("consumer"),
    )
    assert r.status_code == 200
    assert r.json()["consumer_delivery_failure_count"] == 2
    assert r.json().get("dlq_promoted") is True

    dlq_file = tmp_path / "deadletter" / f"{ev['event_id']}.json"
    assert dlq_file.exists()
    record = orjson.loads(dlq_file.read_bytes())
    assert record["event_id"] == ev["event_id"]
    assert record["dlq_at"] is not None

    row = db.execute(
        "SELECT dlq_at FROM events WHERE event_id = ?",
        (ev["event_id"],),
    ).fetchone()
    assert row["dlq_at"] is not None


def test_inline_dlq_promotion_skipped_below_threshold(
    client: TestClient, tmp_path: Path
) -> None:
    from eventbus.db import open_db

    db = open_db(str(tmp_path / "eventbus.sqlite"))
    ev = _event()
    client.post("/publish", json=ev)

    # Nack once — below threshold of 2, no DLQ promotion
    r = client.post(
        f"/nack?event_id={ev['event_id']}&consumer_id=test-consumer"
        "&idempotency_key=below-threshold-nack-key",
        headers=eventbus_auth_headers("consumer"),
    )
    assert r.status_code == 200
    assert r.json()["consumer_delivery_failure_count"] == 1
    assert "dlq_promoted" not in r.json()

    dlq_file = tmp_path / "deadletter" / f"{ev['event_id']}.json"
    assert not dlq_file.exists()

    row = db.execute(
        "SELECT dlq_at FROM events WHERE event_id = ?",
        (ev["event_id"],),
    ).fetchone()
    assert row["dlq_at"] is None


def test_inline_dlq_promotion_not_found(client: TestClient) -> None:
    r = client.post(
        "/nack?event_id=nonexistent&consumer_id=test-consumer"
        "&idempotency_key=not-found-nack-key",
        headers=eventbus_auth_headers("consumer"),
    )
    assert r.status_code == 404
    assert r.json()["detail"] == "event not found"


def test_nack_on_already_dlq_event_does_not_repromote(
    client: TestClient, tmp_path: Path
) -> None:
    from eventbus.db import open_db
    from eventbus.dlq import sweep_orphans

    db = open_db(str(tmp_path / "eventbus.sqlite"))
    ev = _event()
    client.post("/publish", json=ev)
    # Create consumer_delivery record required for REQ-002 per-consumer DLQ promotion
    db.execute(
        "INSERT INTO consumer_delivery (consumer_id, event_id, acked, consumer_delivery_failure_count) VALUES (?, ?, 0, 2)",
        ("consumer-A", ev["event_id"]),
    )
    db.commit()

    sweep_orphans(db, str(tmp_path / "deadletter"), max_retry=2)

    # Nack an already-DLQ'd event — should return 409 Conflict, not increment count
    r = client.post(
        f"/nack?event_id={ev['event_id']}&consumer_id=test-consumer"
        "&idempotency_key=already-dlq-nack-key",
        headers=eventbus_auth_headers("consumer"),
    )
    assert r.status_code == 409
    assert "event already in dead letter queue" in r.json()["detail"]

    dlq_files = list((tmp_path / "deadletter").glob("*.json"))
    assert len(dlq_files) == 1


def test_requeue_non_dlq_event_fails(client: TestClient, tmp_path: Path) -> None:
    """Requeue should fail with 409 for events not currently in DLQ."""
    from eventbus.db import open_db

    db = open_db(str(tmp_path / "eventbus.sqlite"))
    ev = _event()
    client.post("/publish", json=ev)

    # Requeue an event that is NOT in DLQ — should return 409 Conflict
    r = client.post(
        f"/dlq/{ev['event_id']}/requeue", headers=eventbus_auth_headers("operator")
    )
    assert r.status_code == 409, f"Expected 409, got {r.status_code}: {r.text}"

    # Verify dlq_requeue_count is NOT incremented
    row = db.execute(
        "SELECT dlq_requeue_count FROM events WHERE event_id = ?",
        (ev["event_id"],),
    ).fetchone()
    assert row["dlq_requeue_count"] == 0


def test_requeue_unknown_event_returns_404(client: TestClient) -> None:
    """Requeue should return 404 for unknown events."""
    r = client.post(
        "/dlq/nonexistent-event-id/requeue", headers=eventbus_auth_headers("operator")
    )
    assert r.status_code == 404, f"Expected 404, got {r.status_code}: {r.text}"


def test_dlq_requeue_not_found_returns_404(client: TestClient) -> None:
    """Never published, so no events row exists -> repository status not_found -> 404."""
    missing_id = str(uuid.uuid4())
    resp = client.post(
        f"/dlq/{missing_id}/requeue", headers=eventbus_auth_headers("operator")
    )
    assert resp.status_code == 404
    assert resp.json()["detail"] == "event not found"


def test_dlq_requeue_existing_not_in_dlq_returns_409(
    client: TestClient,
) -> None:
    """Published but never nacked: the events row exists but dlq_at is NULL ->
    repository status not_in_dlq -> 409."""
    body = _event("dlq")
    resp = client.post("/publish", json=body)
    assert resp.status_code == 200

    resp = client.post(
        f"/dlq/{body['event_id']}/requeue", headers=eventbus_auth_headers("operator")
    )
    assert resp.status_code == 409
    assert resp.json()["detail"] == "event is not in DLQ"


def test_atomic_write_failure_leaves_db_row_unchanged(
    client: TestClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from eventbus import dlq
    from eventbus.db import open_db

    ev = _event()
    client.post("/publish", json=ev)
    db = open_db(str(tmp_path / "eventbus.sqlite"))

    def _raise(*_args: object, **_kwargs: object) -> None:
        raise OSError("disk full")

    before = _dlq_failure_counter()

    monkeypatch.setattr(dlq, "_atomic_write", _raise)

    with pytest.raises(OSError):
        dlq.promote_single(db, str(tmp_path / "deadletter"), ev["event_id"])

    # The inline write failure increments the failure counter exactly once.
    assert _dlq_failure_counter() - before == 1


def test_inline_write_failure_increments_counter_and_raises(
    client: TestClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """promote_single meters the file-write failure, re-raises, and leaves the row live."""
    from eventbus import dlq
    from eventbus.db import open_db

    db = open_db(str(tmp_path / "eventbus.sqlite"))
    ev = _event("dlq-inline-io")
    client.post("/publish", json=ev)
    _make_promotable(db, ev["event_id"])

    def _raise(*_args: object, **_kwargs: object) -> None:
        raise OSError("disk full")

    before = _dlq_failure_counter()
    monkeypatch.setattr(dlq, "_atomic_write", _raise)

    with pytest.raises(OSError, match="disk full"):
        dlq.promote_single(db, str(tmp_path / "deadletter"), ev["event_id"])

    assert _dlq_failure_counter() - before == 1
    row = db.execute(
        "SELECT dlq_at FROM events WHERE event_id = ?", (ev["event_id"],)
    ).fetchone()
    assert row["dlq_at"] is None
    # No partial file is left behind by the failed atomic write.
    assert not list((tmp_path / "deadletter").glob("*.json"))


def test_sweep_continues_after_one_event_write_failure(
    client: TestClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A failing file write in the sweep is metered, logged and skipped; the sweep continues."""
    from eventbus import dlq
    from eventbus.db import open_db

    db = open_db(str(tmp_path / "eventbus.sqlite"))
    ev1 = _event("io-a")
    ev2 = _event("io-b")
    client.post("/publish", json=ev1)
    client.post("/publish", json=ev2)
    _make_promotable(db, ev1["event_id"])
    _make_promotable(db, ev2["event_id"])

    original = dlq._atomic_write

    def _flaky(deadletter_dir: str, event_id: str, record: Any) -> None:
        if event_id == ev1["event_id"]:
            raise OSError("transient disk error")
        original(deadletter_dir, event_id, record)

    monkeypatch.setattr(dlq, "_atomic_write", _flaky)

    before = _dlq_failure_counter()
    promoted = dlq.sweep_orphans(db, str(tmp_path / "deadletter"), max_retry=2)
    assert promoted == 1
    assert _dlq_failure_counter() - before == 1

    rows = db.execute(
        "SELECT event_id, dlq_at FROM events WHERE event_id IN (?, ?)",
        (ev1["event_id"], ev2["event_id"]),
    ).fetchall()
    dlq_at = {r["event_id"]: r["dlq_at"] for r in rows}
    assert dlq_at[ev1["event_id"]] is None  # skipped event stays live
    assert dlq_at[ev2["event_id"]] is not None
    assert (tmp_path / "deadletter" / f"{ev2['event_id']}.json").exists()
    assert not (tmp_path / "deadletter" / f"{ev1['event_id']}.json").exists()

    # The next sweep repairs the skipped event.
    monkeypatch.setattr(dlq, "_atomic_write", original)
    promoted2 = dlq.sweep_orphans(db, str(tmp_path / "deadletter"), max_retry=2)
    assert promoted2 == 1
    row = db.execute(
        "SELECT dlq_at FROM events WHERE event_id = ?", (ev1["event_id"],)
    ).fetchone()
    assert row["dlq_at"] is not None


def test_db_failure_after_dlq_file_creation_is_repaired_by_next_sweep(
    client: TestClient, tmp_path: Path
) -> None:
    """A commit failure after the DLQ file write leaves the row live; the next sweep repairs it."""
    import sqlite3

    from eventbus import dlq
    from eventbus.db import open_db

    db = open_db(str(tmp_path / "eventbus.sqlite"))
    ev = _event("dlq-db-fail")
    client.post("/publish", json=ev)
    _make_promotable(db, ev["event_id"])

    class _CommitFailingConn:
        """Proxy connection whose first commit raises, simulating a crash after the file write."""

        def __init__(self, inner: Any) -> None:
            self._inner = inner
            self._failed = False

        def execute(self, sql: str, params: Any = ()) -> Any:
            return self._inner.execute(sql, params)

        def commit(self) -> None:
            if not self._failed:
                self._failed = True
                raise sqlite3.OperationalError("disk I/O error")
            self._inner.commit()

        def rollback(self) -> None:
            self._inner.rollback()

    before = _dlq_failure_counter()
    with pytest.raises(sqlite3.OperationalError, match="disk I/O error"):
        dlq.promote_single(
            _CommitFailingConn(db),  # type: ignore[arg-type]  # — test-only: proxy connection stand-in
            str(tmp_path / "deadletter"),
            ev["event_id"],
        )

    # The file was written before the DB failure; only file-write failures move the counter.
    dlq_file = tmp_path / "deadletter" / f"{ev['event_id']}.json"
    assert dlq_file.exists()
    assert _dlq_failure_counter() - before == 0

    # The proxy shares one underlying connection: roll back the un-committed dlq_at UPDATE
    # so the sweep sees the same state a fresh connection would.
    db.rollback()
    row = db.execute(
        "SELECT dlq_at FROM events WHERE event_id = ?", (ev["event_id"],)
    ).fetchone()
    assert row["dlq_at"] is None

    promoted = dlq.sweep_orphans(db, str(tmp_path / "deadletter"), max_retry=2)
    assert promoted == 1
    row = db.execute(
        "SELECT dlq_at FROM events WHERE event_id = ?", (ev["event_id"],)
    ).fetchone()
    assert row["dlq_at"] is not None

    # Repair is idempotent: exactly one valid JSON record, no extra counter movement.
    assert len(list((tmp_path / "deadletter").glob("*.json"))) == 1
    record = orjson.loads(dlq_file.read_bytes())
    assert record["event_id"] == ev["event_id"]
    assert record["dlq_at"] is not None
    assert _dlq_failure_counter() - before == 0


@pytest.mark.asyncio
async def test_concurrent_requeue_same_event(
    client: TestClient, tmp_path: Path
) -> None:
    """Concurrent requeue attempts on the same event must produce exactly one successful redelivery."""
    from eventbus.db import open_db
    from eventbus.dlq import sweep_orphans

    db = open_db(str(tmp_path / "eventbus.sqlite"))
    ev = _event()
    client.post("/publish", json=ev)
    # Create consumer_delivery record required for REQ-002 per-consumer DLQ promotion
    db.execute(
        "INSERT INTO consumer_delivery (consumer_id, event_id, acked, consumer_delivery_failure_count) VALUES (?, ?, 0, 2)",
        ("consumer-A", ev["event_id"]),
    )
    db.commit()

    sweep_orphans(db, str(tmp_path / "deadletter"), max_retry=2)

    from httpx import ASGITransport, AsyncClient

    async def requeue(event_id: str) -> dict[str, Any]:
        async with AsyncClient(
            transport=ASGITransport(app=client.app), base_url="http://test"
        ) as ac:
            r = await ac.post(
                f"/dlq/{event_id}/requeue",
                headers=eventbus_auth_headers("operator"),
            )
            body: dict[str, Any] = r.json()
            return body

    results = await asyncio.gather(
        requeue(ev["event_id"]),
        requeue(ev["event_id"]),
        requeue(ev["event_id"]),
    )

    successes = [r for r in results if r.get("requeued")]
    failures = [r for r in results if not r.get("requeued")]

    assert len(successes) == 1
    assert len(failures) == 2

    success_body = successes[0]
    assert "new_event_id" in success_body
    assert "new_seq" in success_body
    assert isinstance(success_body["new_seq"], int)
    assert success_body["new_seq"] > 0

    for fail_body in failures:
        assert "error" in fail_body or "detail" in fail_body

    new_rows = db.execute(
        "SELECT COUNT(*) FROM events WHERE redelivered_from = ?",
        (ev["event_id"],),
    ).fetchone()[0]
    assert new_rows == 1


@pytest.mark.asyncio
async def test_concurrent_requeue_different_events(
    client: TestClient, tmp_path: Path
) -> None:
    """Concurrent requeue attempts on different events must both succeed independently."""
    from eventbus.db import open_db
    from eventbus.dlq import sweep_orphans
    from httpx import ASGITransport, AsyncClient

    db = open_db(str(tmp_path / "eventbus.sqlite"))
    ev1 = _event(topic="t1")
    ev2 = _event(topic="t2")
    client.post("/publish", json=ev1)
    client.post("/publish", json=ev2)
    # Create consumer_delivery records required for REQ-002 per-consumer DLQ promotion
    db.execute(
        "INSERT INTO consumer_delivery (consumer_id, event_id, acked, consumer_delivery_failure_count) VALUES (?, ?, 0, 2)",
        ("consumer-A", ev1["event_id"]),
    )
    db.execute(
        "INSERT INTO consumer_delivery (consumer_id, event_id, acked, consumer_delivery_failure_count) VALUES (?, ?, 0, 2)",
        ("consumer-B", ev2["event_id"]),
    )
    db.commit()

    sweep_orphans(db, str(tmp_path / "deadletter"), max_retry=2)

    async def requeue(event_id: str) -> dict[str, Any]:
        async with AsyncClient(
            transport=ASGITransport(app=client.app), base_url="http://test"
        ) as ac:
            r = await ac.post(
                f"/dlq/{event_id}/requeue",
                headers=eventbus_auth_headers("operator"),
            )
            body: dict[str, Any] = r.json()
            return body

    results = await asyncio.gather(
        requeue(ev1["event_id"]),
        requeue(ev2["event_id"]),
    )

    assert all(r.get("requeued") for r in results)

    new_ids = {r["new_event_id"] for r in results}
    assert len(new_ids) == 2

    new_seqs = {r["new_seq"] for r in results}
    assert len(new_seqs) == 2

    new_rows = db.execute(
        "SELECT COUNT(*) FROM events WHERE redelivered_from IN (?, ?)",
        (ev1["event_id"], ev2["event_id"]),
    ).fetchone()[0]
    assert new_rows == 2


def test_reconciliation_orphan_file(client: TestClient, tmp_path: Path) -> None:
    """Orphan DLQ file (dlq_at IS NULL but .json exists) is resolved deterministically."""
    from eventbus.db import open_db
    from eventbus.dlq import sweep_orphans

    db = open_db(str(tmp_path / "eventbus.sqlite"))
    ev = _event()
    client.post("/publish", json=ev)

    # Create consumer_delivery record required for promotion
    db.execute(
        "INSERT INTO consumer_delivery (consumer_id, event_id, acked, consumer_delivery_failure_count) VALUES (?, ?, 0, 2)",
        ("consumer-A", ev["event_id"]),
    )
    db.commit()

    # Create a DLQ file without promoting the DB row (orphan scenario)
    dlq_file = tmp_path / "deadletter" / f"{ev['event_id']}.json"
    dlq_file.parent.mkdir(parents=True, exist_ok=True)
    import orjson

    dlq_file.write_bytes(orjson.dumps(ev))

    # Sweep should promote the event (file exists, so write succeeds)
    promoted = sweep_orphans(db, str(tmp_path / "deadletter"), max_retry=2)
    assert promoted == 1

    # Verify the event was promoted (dlq_at set)
    row = db.execute(
        "SELECT dlq_at FROM events WHERE event_id = ?",
        (ev["event_id"],),
    ).fetchone()
    assert row is not None
    assert row["dlq_at"] is not None


def test_reconciliation_missing_file(client: TestClient, tmp_path: Path) -> None:
    """Missing DLQ file (promoted event without .json) does not cause errors."""
    from eventbus.db import open_db
    from eventbus.dlq import sweep_orphans

    db = open_db(str(tmp_path / "eventbus.sqlite"))
    ev = _event()
    client.post("/publish", json=ev)

    # Promote the event normally
    dlq_file = tmp_path / "deadletter" / f"{ev['event_id']}.json"
    dlq_file.parent.mkdir(parents=True, exist_ok=True)
    import orjson

    dlq_file.write_bytes(orjson.dumps(ev))
    sweep_orphans(db, str(tmp_path / "deadletter"), max_retry=2)

    # Now delete the DLQ file (simulating loss)
    dlq_file.unlink()

    # Create another event that needs promotion
    ev2 = _event()
    client.post("/publish", json=ev2)
    db.execute(
        "INSERT INTO consumer_delivery (consumer_id, event_id, acked, consumer_delivery_failure_count) VALUES (?, ?, 0, 2)",
        ("consumer-A", ev2["event_id"]),
    )
    db.commit()

    # Sweep should not fail even though the first event's file is missing
    promoted = sweep_orphans(db, str(tmp_path / "deadletter"), max_retry=2)
    assert promoted == 1  # Only ev2 should be promoted


# ---------------------------------------------------------------------------
# reconcile_missing_dlq_files (new) — rebuild lost DLQ files for promoted events
# ---------------------------------------------------------------------------


def test_reconcile_rebuilds_full_record_from_db(
    client: TestClient, tmp_path: Path
) -> None:
    """A promoted event whose file was lost is rebuilt byte-for-byte from SQLite."""
    from eventbus.db import open_db
    from eventbus.dlq import reconcile_missing_dlq_files, sweep_orphans

    db = open_db(str(tmp_path / "eventbus.sqlite"))
    ev = _event()
    client.post("/publish", json=ev)

    # Promote via sweep so the event has a DLQ record, then delete the file.
    _make_promotable(db, ev["event_id"])
    sweep_orphans(db, str(tmp_path / "deadletter"), max_retry=2)

    original_bytes = (tmp_path / "deadletter" / f"{ev['event_id']}.json").read_bytes()
    (tmp_path / "deadletter" / f"{ev['event_id']}.json").unlink()

    # Reconcile returns {checked, rebuilt, failed}; the file is absent so it rebuilds.
    reconciled = reconcile_missing_dlq_files(db, str(tmp_path / "deadletter"))
    assert reconciled == {"checked": 1, "rebuilt": 1, "failed": 0}

    rebuilt = (tmp_path / "deadletter" / f"{ev['event_id']}.json").read_bytes()
    assert rebuilt == original_bytes  # byte-for-byte identical to sweep-time record


def test_reconcile_ignores_unpromoted_events(
    client: TestClient, tmp_path: Path
) -> None:
    """Events with dlq_at IS NULL are not touched (only promoted events are reconciled)."""
    from eventbus.db import open_db
    from eventbus.dlq import reconcile_missing_dlq_files

    db = open_db(str(tmp_path / "eventbus.sqlite"))
    ev = _event()
    client.post("/publish", json=ev)
    # Never promoted: dlq_at stays NULL.
    reconciled = reconcile_missing_dlq_files(db, str(tmp_path / "deadletter"))
    assert reconciled == {"checked": 0, "rebuilt": 0, "failed": 0}
    assert not (tmp_path / "deadletter" / f"{ev['event_id']}.json").exists()


def test_reconcile_is_idempotent_and_preserves_existing_file(
    client: TestClient, tmp_path: Path
) -> None:
    """Re-running reconcile on an intact file leaves it untouched (no rewrite, mtime preserved)."""
    from eventbus.db import open_db
    from eventbus.dlq import reconcile_missing_dlq_files, sweep_orphans

    db = open_db(str(tmp_path / "eventbus.sqlite"))
    ev = _event()
    client.post("/publish", json=ev)

    # Promote via sweep; do NOT delete the file, so reconcile must skip it.
    _make_promotable(db, ev["event_id"])
    sweep_orphans(db, str(tmp_path / "deadletter"), max_retry=2)

    target = tmp_path / "deadletter" / f"{ev['event_id']}.json"
    stat_before = target.stat()
    reconciled = reconcile_missing_dlq_files(db, str(tmp_path / "deadletter"))
    # File already present: counted as checked, but never rewritten (rebuilt == 0).
    assert reconciled == {"checked": 1, "rebuilt": 0, "failed": 0}
    stat_after = target.stat()
    assert (
        stat_before.st_mtime_ns == stat_after.st_mtime_ns
    )  # existing file not rewritten


def test_reconcile_isolates_single_event_write_failure(
    client: TestClient, tmp_path: Path, monkeypatch
) -> None:
    """A write failure for one event is skipped without blocking the others."""
    from eventbus import dlq
    from eventbus.db import open_db
    from eventbus.dlq import _atomic_write, reconcile_missing_dlq_files, sweep_orphans

    db = open_db(str(tmp_path / "eventbus.sqlite"))

    ev1 = _event()
    ev2 = _event()
    client.post("/publish", json=ev1)
    client.post("/publish", json=ev2)

    for ev in (ev1, ev2):
        _make_promotable(db, ev["event_id"])
    sweep_orphans(db, str(tmp_path / "deadletter"), max_retry=2)

    # Delete both files; both are now reconcile targets.
    for ev in (ev1, ev2):
        (tmp_path / "deadletter" / f"{ev['event_id']}.json").unlink()

    # _atomic_write is a module-level function: (deadletter_dir, event_id, record).
    # Force the write of ev1 to fail; ev2 writes normally via the real function.
    def flaky_atomic_write(deadletter_dir, event_id, record):
        if event_id == ev1["event_id"]:
            raise OSError("simulated disk failure")
        return _atomic_write(deadletter_dir, event_id, record)

    monkeypatch.setattr(dlq, "_atomic_write", flaky_atomic_write)

    reconciled = reconcile_missing_dlq_files(db, str(tmp_path / "deadletter"))
    # ev1 fails, ev2 succeeds: checked=2, rebuilt=1, failed=1.
    assert reconciled == {"checked": 2, "rebuilt": 1, "failed": 1}

    assert (tmp_path / "deadletter" / f"{ev2['event_id']}.json").exists()
    assert not (tmp_path / "deadletter" / f"{ev1['event_id']}.json").exists()

    # Both events were promoted by sweep (dlq_at set); only the file differs.
    row1 = db.execute(
        "SELECT dlq_at FROM events WHERE event_id = ?", (ev1["event_id"],)
    ).fetchone()
    row2 = db.execute(
        "SELECT dlq_at FROM events WHERE event_id = ?", (ev2["event_id"],)
    ).fetchone()
    assert row1["dlq_at"] is not None
    assert row2["dlq_at"] is not None

    # The single write failure was metered on the failure counter.
    assert _dlq_failure_counter() >= 1.0


def test_reconcile_concurrent_callers_under_db_lock(
    client: TestClient, tmp_path: Path
) -> None:
    """Two callers each holding get_db_lock() reconcile their events without corruption."""
    import threading

    from eventbus.db import get_db_lock, open_db
    from eventbus.dlq import reconcile_missing_dlq_files, sweep_orphans

    db = open_db(str(tmp_path / "eventbus.sqlite"))

    ev_a = _event()
    ev_b = _event()
    client.post("/publish", json=ev_a)
    client.post("/publish", json=ev_b)

    for ev in (ev_a, ev_b):
        _make_promotable(db, ev["event_id"])
    sweep_orphans(db, str(tmp_path / "deadletter"), max_retry=2)

    # Delete both files; both are now reconcile targets.
    for ev in (ev_a, ev_b):
        (tmp_path / "deadletter" / f"{ev['event_id']}.json").unlink()

    # get_db_lock() is a non-reentrant threading.Lock, so two callers that both hold
    # it serialize by design. Each worker mirrors the real caller: hold the lock
    # around the whole reconcile call. No sleeps or barriers.
    def worker() -> None:
        with get_db_lock():
            reconcile_missing_dlq_files(db, str(tmp_path / "deadletter"))

    t_a = threading.Thread(target=worker)
    t_b = threading.Thread(target=worker)
    t_a.start()
    t_b.start()
    t_a.join()
    t_b.join()

    for ev in (ev_a, ev_b):
        assert (tmp_path / "deadletter" / f"{ev['event_id']}.json").exists()
        row = db.execute(
            "SELECT dlq_at FROM events WHERE event_id = ?", (ev["event_id"],)
        ).fetchone()
        assert row["dlq_at"] is not None
