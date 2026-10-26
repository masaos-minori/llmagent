"""tests/test_eventbus_concurrent.py
Concurrent stress tests for Event Bus DB lock serialization.
"""

from __future__ import annotations

import asyncio
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


def _event(topic: str = "test") -> dict[str, Any]:
    return {
        "event_id": str(uuid.uuid4()),
        "topic": topic,
        "payload": {"key": "value"},
        "producer": "test-producer",
        "published_at": "2026-01-01T00:00:00Z",
    }


class TestConcurrentPublish:
    """Verify concurrent publish requests do not cause SQLite lock errors."""

    def test_concurrent_publish_no_errors(self, client: TestClient) -> None:
        n_events = 20
        results: list[dict[str, Any]] = []

        async def _publish_one(i: int) -> None:
            body = {**_event("concurrent"), "event_id": str(uuid.uuid4())}
            resp = client.post("/publish", json=body)
            results.append(resp.json())

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(
                asyncio.gather(*(_publish_one(i) for i in range(n_events)))
            )
        finally:
            loop.close()

        assert len(results) == n_events
        seqs = {r["seq"] for r in results}
        assert len(seqs) == n_events, (
            f"Expected {n_events} unique seq values, got {len(seqs)}"
        )


class TestConcurrentAck:
    """Verify concurrent ack requests on the same event_id are idempotent."""

    def test_concurrent_ack_same_event(
        self, client: TestClient, tmp_path: Path
    ) -> None:
        body = {**_event("ack"), "event_id": str(uuid.uuid4())}
        resp = client.post("/publish", json=body)
        assert resp.status_code == 200

        event_id = body["event_id"]

        # Mark the event as delivered but not yet acked so the first ack succeeds
        from eventbus.db import open_db

        db = open_db(str(tmp_path / "eventbus.sqlite"))
        try:
            db.execute(
                "INSERT OR IGNORE INTO consumer_delivery(consumer_id, event_id) VALUES (?, ?)",
                ("consumer-A", event_id),
            )
            db.commit()
        finally:
            db.close()

        results: list[dict[str, Any]] = []

        async def _ack_one() -> None:
            resp = client.post(
                f"/events/{event_id}/ack", params={"consumer_id": "consumer-A"}
            )
            results.append({"status_code": resp.status_code, **resp.json()})

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(asyncio.gather(*(_ack_one() for _ in range(10))))
        finally:
            loop.close()

        # First ack should succeed with 200 (acked=True), subsequent ones return 200 (already_acked=True)
        all_success = sum(1 for r in results if r.get("status_code") == 200)
        assert all_success == 10, (
            f"Expected all 10 acks to return 200, got {all_success}"
        )
        newly_acked_count = sum(
            1 for r in results if r.get("already_acked") is not True
        )
        already_acked_count = sum(1 for r in results if r.get("already_acked") is True)
        assert newly_acked_count == 1, (
            f"Expected exactly 1 newly acked, got {newly_acked_count}"
        )
        assert already_acked_count == 9, (
            f"Expected exactly 9 already_acked, got {already_acked_count}"
        )


class TestConcurrentReplay:
    """Verify concurrent replay requests with overlapping time ranges do not cause duplicates."""

    def test_concurrent_replay_no_duplicates(self, client: TestClient) -> None:
        for i in range(5):
            body = {**_event("replay"), "event_id": str(uuid.uuid4())}
            resp = client.post("/publish", json=body)
            assert resp.status_code == 200

        results: list[list] = []

        async def _replay() -> None:
            resp = client.get("/replay?since_seq=0&format=json")
            assert resp.status_code == 200
            results.append(resp.json()["items"])

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(asyncio.gather(*(_replay() for _ in range(5))))
        finally:
            loop.close()

        # All replay requests should return the same events
        first_items = results[0]
        for items in results[1:]:
            assert len(items) == len(first_items), (
                "Replay returned different number of events"
            )
            event_ids = {r["event_id"] for r in first_items}
            assert all(r["event_id"] in event_ids for r in items), (
                "Replay returned different events"
            )


class TestConcurrentDlqRequeue:
    """Verify concurrent DLQ requeue operations do not cause data corruption."""

    def test_concurrent_dlq_requeue(self, client: TestClient) -> None:
        body = {**_event("dlq"), "event_id": str(uuid.uuid4())}
        resp = client.post("/publish", json=body)
        assert resp.status_code == 200

        event_id = body["event_id"]
        original_seq = resp.json()["seq"]

        # Simulate one prior failure for consumer-A so a single NACK reaches
        # max_retry. Under per-consumer gating (REQ-002) one consumer reaching
        # its own budget promotes; only the per-consumer failure count gates.
        from eventbus import app as eb_app

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            db = eb_app.app.state.db
            cfg = eb_app.app.state.config
            db.execute(
                "DELETE FROM consumer_delivery WHERE consumer_id = ? AND event_id = ?",
                ("consumer-A", event_id),
            )
            db.execute(
                "INSERT INTO consumer_delivery "
                "(consumer_id, event_id, acked, consumer_last_nack_attempt, consumer_delivery_failure_count) "
                "VALUES ('consumer-A', ?, 0, 'seeded-attempt', ?)",
                (event_id, cfg.max_retry - 1),
            )
            db.commit()
        finally:
            loop.close()

        # Nack consumer-A once to reach max_retry and promote to DLQ.
        resp = client.post(
            "/nack",
            params={"event_id": event_id, "consumer_id": "consumer-A"},
        )
        assert resp.status_code == 200

        results: list[dict[str, Any]] = []

        async def _requeue() -> None:
            resp = client.post(f"/dlq/{event_id}/requeue")
            results.append(resp.json())

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(asyncio.gather(*(_requeue() for _ in range(5))))
        finally:
            loop.close()

        # Only one requeue should succeed (event is no longer in DLQ after first requeue)
        requeued = [r for r in results if r.get("requeued") is True]
        assert len(requeued) == 1, (
            f"Expected exactly 1 requeue success, got {len(requeued)}"
        )

        # Successful response includes new_event_id and new_seq
        success_resp = requeued[0]
        assert "new_event_id" in success_resp, (
            "successful response should include new_event_id"
        )
        assert "new_seq" in success_resp, "successful response should include new_seq"
        # Validate new_event_id is a valid UUID v4 string
        uuid.UUID(success_resp["new_event_id"], version=4)
        # Validate new_seq is an integer greater than the original event's seq
        assert isinstance(success_resp["new_seq"], int), "new_seq should be an integer"
        assert success_resp["new_seq"] > original_seq, (
            f"new_seq ({success_resp['new_seq']}) should be greater than original seq ({original_seq})"
        )

        # The other concurrent requests should fail with 409 Conflict (event no longer in DLQ)
        conflicts = [r for r in results if r.get("detail") == "event is not in DLQ"]
        assert len(conflicts) == 4, f"Expected 4 conflicts, got {len(conflicts)}"

    def test_concurrent_dlq_requeue_no_failed_transaction_carryover(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """One of five requeues fails on the redelivery INSERT; the rollback must
        leave no failed transaction on the shared connection and exactly one of
        the remaining requeues must succeed."""
        import sqlite3

        import eventbus.app as eb_app
        import eventbus.dlq_repo as dlq_repo
        import eventbus.dlq_route as dlq_route

        body = {**_event("dlq"), "event_id": str(uuid.uuid4())}
        resp = client.post("/publish", json=body)
        assert resp.status_code == 200
        event_id = body["event_id"]
        original_seq = resp.json()["seq"]

        # Same seed-and-nack promotion pattern as test_concurrent_dlq_requeue.
        db = eb_app.app.state.db
        cfg = eb_app.app.state.config
        db.execute(
            "DELETE FROM consumer_delivery WHERE consumer_id = ? AND event_id = ?",
            ("consumer-A", event_id),
        )
        db.execute(
            "INSERT INTO consumer_delivery "
            "(consumer_id, event_id, acked, consumer_last_nack_attempt, "
            "consumer_delivery_failure_count) VALUES ('consumer-A', ?, 0, 'seeded-attempt', ?)",
            (event_id, cfg.max_retry - 1),
        )
        db.commit()
        nresp = client.post(
            "/nack", params={"event_id": event_id, "consumer_id": "consumer-A"}
        )
        assert nresp.status_code == 200

        class _FailOnceInsertConn:
            """Delegate connection whose first INSERT raises IntegrityError."""

            def __init__(self, real: Any) -> None:
                self._real = real
                self._failed = False

            def execute(self, sql: Any, *args: Any, **kwargs: Any) -> Any:
                if not self._failed and "INSERT" in str(sql).upper():
                    self._failed = True
                    raise sqlite3.IntegrityError("injected insert failure")
                return self._real.execute(sql, *args, **kwargs)

            def commit(self) -> None:
                self._real.commit()

            def rollback(self) -> None:
                self._real.rollback()

        # Route-level seam: only the first requeue runs against the failing
        # wrapper connection (TestClient calls are serialized by run_with_db_lock);
        # app.state.db itself is never replaced.
        injected = {"done": False}
        real_redeliver = dlq_route.redeliver_event

        def _redeliver_with_one_failure(conn: Any, target_id: str) -> Any:
            if not injected["done"]:
                injected["done"] = True
                wrapper: Any = _FailOnceInsertConn(conn)
                return dlq_repo.redeliver_event(wrapper, target_id)
            return real_redeliver(conn, target_id)

        monkeypatch.setattr(dlq_route, "redeliver_event", _redeliver_with_one_failure)

        results: list[dict[str, Any]] = []
        raised = 0

        async def _requeue() -> None:
            nonlocal raised
            try:
                r = client.post(f"/dlq/{event_id}/requeue")
                results.append(r.json())
            except sqlite3.IntegrityError:
                raised += 1

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(asyncio.gather(*(_requeue() for _ in range(5))))
        finally:
            loop.close()
        monkeypatch.undo()

        # The injected request surfaced the error, exactly one requeue succeeded.
        assert raised == 1, f"Expected 1 injected failure, got {raised}"
        requeued = [r for r in results if r.get("requeued") is True]
        assert len(requeued) == 1, f"Expected 1 success, got {len(requeued)}"
        conflicts = [r for r in results if r.get("detail") == "event is not in DLQ"]
        assert len(conflicts) == 3, f"Expected 3 conflicts, got {len(conflicts)}"

        success_resp = requeued[0]
        uuid.UUID(success_resp["new_event_id"], version=4)
        assert isinstance(success_resp["new_seq"], int)
        assert success_resp["new_seq"] > original_seq

        # No failed transaction lingered on the shared connection.
        assert db.in_transaction is False

        # The shared connection stays usable for follow-up requests.
        follow = client.get("/dlq")
        assert follow.status_code == 200
