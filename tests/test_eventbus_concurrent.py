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
        assert len(seqs) == n_events, f"Expected {n_events} unique seq values, got {len(seqs)}"


class TestConcurrentAck:
    """Verify concurrent ack requests on the same event_id are idempotent."""

    def test_concurrent_ack_same_event(self, client: TestClient) -> None:
        body = {**_event("ack"), "event_id": str(uuid.uuid4())}
        resp = client.post("/publish", json=body)
        assert resp.status_code == 200

        event_id = body["event_id"]
        results: list[dict[str, Any]] = []

        async def _ack_one() -> None:
            resp = client.post("/ack", params={"event_id": event_id, "consumer_id": "consumer-1"})
            results.append(resp.json())

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(
                asyncio.gather(*(_ack_one() for _ in range(10)))
            )
        finally:
            loop.close()

        # First ack should succeed, subsequent ones should return 404 (already acked)
        acked_count = sum(1 for r in results if r.get("acked") is True)
        assert acked_count == 1, f"Expected exactly 1 successful ack, got {acked_count}"


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
            loop.run_until_complete(
                asyncio.gather(*(_replay() for _ in range(5)))
            )
        finally:
            loop.close()

        # All replay requests should return the same events
        first_items = results[0]
        for items in results[1:]:
            assert len(items) == len(first_items), "Replay returned different number of events"
            event_ids = {r["event_id"] for r in first_items}
            assert all(r["event_id"] in event_ids for r in items), "Replay returned different events"


class TestConcurrentDlqRequeue:
    """Verify concurrent DLQ requeue operations do not cause data corruption."""

    def test_concurrent_dlq_requeue(self, client: TestClient) -> None:
        body = {**_event("dlq"), "event_id": str(uuid.uuid4())}
        resp = client.post("/publish", json=body)
        assert resp.status_code == 200

        event_id = body["event_id"]
        # Nack 3 times to promote to DLQ
        for _ in range(3):
            resp = client.post("/nack", params={"event_id": event_id})
            assert resp.status_code == 200

        results: list[dict[str, Any]] = []

        async def _requeue() -> None:
            resp = client.post(f"/dlq/{event_id}/requeue")
            results.append(resp.json())

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(
                asyncio.gather(*(_requeue() for _ in range(5)))
            )
        finally:
            loop.close()

        # Only one requeue should succeed (event is no longer in DLQ after first requeue)
        requeued = [r for r in results if r.get("requeued") is True]
        assert len(requeued) == 1, f"Expected exactly 1 requeue success, got {len(requeued)}"

        # The other concurrent requests should fail with 409 Conflict (event no longer in DLQ)
        conflicts = [r for r in results if r.get("detail") == "event is not in DLQ"]
        assert len(conflicts) == 4, f"Expected 4 conflicts, got {len(conflicts)}"

