"""tests/test_eventbus_requeue_edge_cases.py
Edge case tests for POST /dlq/{event_id}/requeue endpoint.

Tests requeue behavior: unknown event, non-DLQ event, repeated requeue,
and re-promotion after requeue when the per-consumer failure count >= max_retry.
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from tests.eventbus.eventbus_helpers import eventbus_test_tokens


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
        c.headers["Authorization"] = "Bearer test-token"
        yield c


def _event(topic: str = "requeue_test") -> dict[str, Any]:
    return {
        "event_id": str(uuid.uuid4()),
        "topic": topic,
        "payload": {"key": "value"},
        "producer": "test-producer",
        "published_at": "2026-01-01T00:00:00Z",
    }


def _get_field(client: TestClient, event_id: str, field: str) -> Any:
    import eventbus.app as eb_app

    db = eb_app.app.state.db
    assert db is not None
    row = db.execute(
        f"SELECT {field} FROM events WHERE event_id = ?",
        (event_id,),
    ).fetchone()
    return row[0] if row else None


class TestRequeueEdgeCases:
    """Tests for POST /dlq/{event_id}/requeue edge cases."""

    def test_requeue_unknown_event(self, client: TestClient) -> None:
        """POST /dlq/{event_id}/requeue for unknown event returns 404."""
        resp = client.post("/dlq/nonexistent-event/requeue")
        assert resp.status_code == 404

    def test_requeue_non_dmq_event(self, client: TestClient) -> None:
        """POST /dlq/{event_id}/requeue for non-DLQ event returns 409 Conflict."""
        body = _event()
        resp = client.post("/publish", json=body)
        assert resp.status_code == 200

        # Event is not in DLQ (dlq_at IS NULL)
        resp = client.post(f"/dlq/{body['event_id']}/requeue")
        assert resp.status_code == 409

    def test_requeue_valid_dmq_event(self, client: TestClient, tmp_path: Path) -> None:
        """POST /dlq/{event_id}/requeue for valid DLQ event succeeds."""
        from eventbus.db import open_db
        from eventbus.dlq import sweep_orphans

        body = _event()
        resp = client.post("/publish", json=body)
        assert resp.status_code == 200

        # Promote to DLQ
        db = open_db(str(tmp_path / "eventbus.sqlite"))
        # Create consumer_delivery record required for REQ-002 per-consumer DLQ promotion
        db.execute(
            "INSERT INTO consumer_delivery (consumer_id, event_id, acked, consumer_delivery_failure_count) VALUES (?, ?, 0, 2)",
            ("consumer-A", body["event_id"]),
        )
        db.commit()
        # Per-consumer sweep gating (REQ-002): seed a giving-up consumer so the
        # sweep can promote.
        db.execute(
            "INSERT INTO consumer_delivery "
            "(consumer_id, event_id, consumer_delivery_failure_count) VALUES ('sweep-consumer', ?, 2)",
            (body["event_id"],),
        )
        db.commit()
        sweep_orphans(db, str(tmp_path / "deadletter"), max_retry=2)

        # Requeue should succeed
        resp = client.post(f"/dlq/{body['event_id']}/requeue")
        assert resp.status_code == 200
        data = resp.json()
        assert data["requeued"] is True
        assert "new_event_id" in data
        assert data["new_event_id"] != body["event_id"]

        # Original event remains in DLQ (lineage model: original row's dlq_at IS NOT NULL)
        orig_row = db.execute(
            "SELECT dlq_at, dlq_requeue_count FROM events WHERE event_id = ?",
            (body["event_id"],),
        ).fetchone()
        assert orig_row["dlq_at"] is not None
        assert orig_row["dlq_requeue_count"] == 1

        # New event exists with redelivered_from set
        new_row = db.execute(
            "SELECT redelivered_from FROM events WHERE event_id = ?",
            (data["new_event_id"],),
        ).fetchone()
        assert new_row["redelivered_from"] == body["event_id"]

    def test_second_requeue_of_same_event_rejected_after_first_redeliver(
        self, client: TestClient, tmp_path: Path
    ) -> None:
        """Second requeue of the same original event_id is rejected (409).

        The lineage model permits only one redeliver per original event_id, by
        design (see dlq_route.py's dlq_requeue docstring: "the original row's
        dlq_at is intentionally left set so only one redeliver succeeds per
        original event") — this is a permanent, per-original-event rule, not a
        guard scoped only to simultaneous concurrent requests.
        """
        from eventbus.db import open_db
        from eventbus.dlq import sweep_orphans

        body = _event()
        resp = client.post("/publish", json=body)
        assert resp.status_code == 200

        # Promote to DLQ when the per-consumer failure count >= max_retry
        db = open_db(str(tmp_path / "eventbus.sqlite"))
        # Create consumer_delivery record required for REQ-002 per-consumer DLQ promotion
        db.execute(
            "INSERT INTO consumer_delivery (consumer_id, event_id, acked, consumer_delivery_failure_count) VALUES (?, ?, 0, 2)",
            ("consumer-A", body["event_id"]),
        )
        db.commit()
        # Per-consumer sweep gating (REQ-002): seed a giving-up consumer so the
        # sweep can promote.
        db.execute(
            "INSERT INTO consumer_delivery "
            "(consumer_id, event_id, consumer_delivery_failure_count) VALUES ('sweep-consumer', ?, 2)",
            (body["event_id"],),
        )
        db.commit()
        sweep_orphans(db, str(tmp_path / "deadletter"), max_retry=2)

        # First requeue — succeeds: new descendant row inserted, original
        # row's dlq_requeue_count incremented
        resp = client.post(f"/dlq/{body['event_id']}/requeue")
        assert resp.status_code == 200
        data = resp.json()
        assert "new_event_id" in data
        orig_row = db.execute(
            "SELECT dlq_requeue_count FROM events WHERE event_id = ?",
            (body["event_id"],),
        ).fetchone()
        assert orig_row["dlq_requeue_count"] == 1

        # The descendant's own dlq_at starts NULL, so it (not the original)
        # becomes the next sweep's promotion candidate — the original's dlq_at
        # is never cleared by redeliver_event, so it is never re-selected here.
        # Seed a giving-up consumer for the descendant so the per-consumer
        # sweep can promote it again.
        db = open_db(str(tmp_path / "eventbus.sqlite"))
        db.execute(
            "INSERT INTO consumer_delivery "
            "(consumer_id, event_id, consumer_delivery_failure_count) VALUES ('sweep-consumer', ?, 2)",
            (data["new_event_id"],),
        )
        db.commit()
        n = sweep_orphans(db, str(tmp_path / "deadletter"), max_retry=2)
        assert n == 1

        # Second requeue of the SAME original event_id is rejected: a
        # descendant with redelivered_from == this event_id already exists,
        # so the lineage guard treats this original event as already
        # redelivered, permanently.
        resp = client.post(f"/dlq/{body['event_id']}/requeue")
        assert resp.status_code == 409

        # dlq_requeue_count is not incremented further by the rejected attempt
        assert _get_field(client, body["event_id"], "dlq_requeue_count") == 1

    def test_requeue_event_at_max_retry_then_re_promoted(
        self, client: TestClient, tmp_path: Path
    ) -> None:
        """Requeue succeeds; the original event's dlq_at is never cleared (lineage
        model), so the next DLQ tick promotes the new descendant event instead of
        re-promoting the original."""
        from eventbus.db import open_db
        from eventbus.dlq import sweep_orphans

        body = _event()
        resp = client.post("/publish", json=body)
        assert resp.status_code == 200

        # Promote to DLQ
        db = open_db(str(tmp_path / "eventbus.sqlite"))
        # Create a consumer_delivery record (required for REQ-002 per-consumer DLQ promotion)
        db.execute(
            "INSERT INTO consumer_delivery (consumer_id, event_id, acked, consumer_delivery_failure_count) VALUES (?, ?, 0, 2)",
            ("consumer-A", body["event_id"]),
        )
        db.commit()
        # Per-consumer sweep gating (REQ-002): seed a giving-up consumer so the
        # sweep can promote.
        db.execute(
            "INSERT INTO consumer_delivery "
            "(consumer_id, event_id, consumer_delivery_failure_count) VALUES ('sweep-consumer', ?, 2)",
            (body["event_id"],),
        )
        db.commit()
        sweep_orphans(db, str(tmp_path / "deadletter"), max_retry=2)

        dlq_file_1 = tmp_path / "deadletter" / f"{body['event_id']}.json"
        assert dlq_file_1.exists()

        # Requeue — returns new_event_id/new_seq per the lineage model (no
        # dlq_imminent field: that field was removed from the response)
        resp = client.post(f"/dlq/{body['event_id']}/requeue")
        assert resp.status_code == 200
        data = resp.json()
        assert "new_event_id" in data

        # The original row's dlq_at is intentionally left set by the lineage
        # model (see dlq_route.py's dlq_requeue docstring) — it is not cleared
        # on requeue, so only one redeliver ever succeeds per original event.
        dlq_at = _get_field(client, body["event_id"], "dlq_at")
        assert dlq_at is not None

        # Next DLQ loop tick promotes the new descendant (a giving-up
        # consumer is seeded for it, and its own dlq_at starts NULL) — not the
        # original, whose dlq_at was never cleared.
        # Seed a giving-up consumer for the descendant so the per-consumer
        # sweep can promote it again.
        db = open_db(str(tmp_path / "eventbus.sqlite"))
        db.execute(
            "INSERT INTO consumer_delivery "
            "(consumer_id, event_id, consumer_delivery_failure_count) VALUES ('sweep-consumer', ?, 2)",
            (data["new_event_id"],),
        )
        db.commit()
        n = sweep_orphans(db, str(tmp_path / "deadletter"), max_retry=2)
        assert n == 1

        # This path coincides with dlq_file_1 above (same original event_id),
        # which was never removed — it is not itself proof the descendant was
        # promoted; that is what `n == 1` above already confirms.
        dlq_file_2 = tmp_path / "deadletter" / f"{body['event_id']}.json"
        assert dlq_file_2.exists()


def _promote_to_dlq(client: TestClient) -> str:
    """Publish an event, seed consumer_delivery at max_retry - 1, and nack once
    so the inline promotion moves it to the DLQ. Returns the event_id."""
    body = _event("dlq_edge")
    assert client.post("/publish", json=body).status_code == 200
    event_id: str = body["event_id"]

    import eventbus.app as eb_app

    db = eb_app.app.state.db
    cfg = eb_app.app.state.config
    db.execute(
        "INSERT INTO consumer_delivery "
        "(consumer_id, event_id, acked, consumer_last_nack_attempt, "
        "consumer_delivery_failure_count) VALUES ('consumer-A', ?, 0, 'seeded-attempt', ?)",
        (event_id, cfg.max_retry - 1),
    )
    db.commit()
    resp = client.post(
        "/nack", params={"event_id": event_id, "consumer_id": "consumer-A"}
    )
    assert resp.status_code == 200
    assert resp.json().get("dlq_promoted") is True
    return event_id


class _FailingConn:
    """Delegate connection wrapper that injects a failure at one repository call.

    Injected through the `eventbus.dlq_route.redeliver_event` seam so only the
    request under test sees the wrapper; the real shared connection in
    `app.state.db` stays untouched for the background DLQ loop and later
    requests, and every non-failing call is delegated to the real connection.
    """

    def __init__(self, real: Any, *, fail_on: str, error: BaseException) -> None:
        self._real = real
        self._fail_on = fail_on
        self._error = error

    def execute(self, sql: Any, *args: Any, **kwargs: Any) -> Any:
        if self._fail_on == "insert" and "INSERT" in str(sql).upper():
            raise self._error
        return self._real.execute(sql, *args, **kwargs)

    def commit(self) -> None:
        if self._fail_on == "commit":
            raise self._error
        self._real.commit()

    def rollback(self) -> None:
        self._real.rollback()


class TestRequeueFailureInjection:
    """Failure-injection tests proving every failed requeue path rolls back and
    leaves the shared connection usable (REQ-002)."""

    def test_requeue_insert_failure_rolls_back_and_keeps_connection_usable(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Redelivery INSERT fails after the original-row UPDATE ran: the error
        propagates, no transaction stays open, and the connection is reusable."""
        import sqlite3

        import eventbus.app as eb_app
        import eventbus.dlq_repo as dlq_repo
        import eventbus.dlq_route as dlq_route

        event_id = _promote_to_dlq(client)
        shared = eb_app.app.state.db

        def _inject(db: Any, target_id: str) -> dlq_repo.RequeueResult:
            wrapper: Any = _FailingConn(
                shared,
                fail_on="insert",
                error=sqlite3.IntegrityError("injected insert failure"),
            )
            return dlq_repo.redeliver_event(wrapper, target_id)

        monkeypatch.setattr(dlq_route, "redeliver_event", _inject)
        with pytest.raises(sqlite3.IntegrityError):
            client.post(f"/dlq/{event_id}/requeue")
        monkeypatch.undo()

        # No dangling implicit transaction on the shared connection.
        assert shared.in_transaction is False
        # The UPDATE increment was rolled back with the failed INSERT (atomic).
        assert _get_field(client, event_id, "dlq_requeue_count") == 0
        n = shared.execute(
            "SELECT COUNT(*) FROM events WHERE redelivered_from = ?",
            (event_id,),
        ).fetchone()[0]
        assert n == 0

        # Connection reuse: a normal requeue on the same connection succeeds.
        resp = client.post(f"/dlq/{event_id}/requeue")
        assert resp.status_code == 200

    def test_requeue_commit_failure_rolls_back_no_active_transaction(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """commit() fails: the error propagates, no active transaction remains,
        and a follow-up request on the same connection succeeds."""
        import sqlite3

        import eventbus.app as eb_app
        import eventbus.dlq_repo as dlq_repo
        import eventbus.dlq_route as dlq_route

        event_id = _promote_to_dlq(client)
        shared = eb_app.app.state.db

        def _inject(db: Any, target_id: str) -> dlq_repo.RequeueResult:
            wrapper: Any = _FailingConn(
                shared,
                fail_on="commit",
                error=sqlite3.Error("injected commit failure"),
            )
            return dlq_repo.redeliver_event(wrapper, target_id)

        monkeypatch.setattr(dlq_route, "redeliver_event", _inject)
        with pytest.raises(sqlite3.Error):
            client.post(f"/dlq/{event_id}/requeue")
        monkeypatch.undo()

        assert shared.in_transaction is False
        assert _get_field(client, event_id, "dlq_requeue_count") == 0

        resp = client.post(f"/dlq/{event_id}/requeue")
        assert resp.status_code == 200

    def test_requeue_constraint_failure_rolls_back_without_partial_state(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A real UNIQUE violation on events.event_id during the redelivery
        INSERT leaves no partial state and the connection stays usable."""
        import sqlite3
        from types import SimpleNamespace

        import eventbus.app as eb_app
        import eventbus.dlq_repo as dlq_repo

        event_id = _promote_to_dlq(client)
        shared = eb_app.app.state.db
        # Force the descendant's generated event_id to collide with the
        # original row's UNIQUE event_id, so the real INSERT raises
        # IntegrityError (UNIQUE constraint failed) inside the transaction.
        monkeypatch.setattr(
            dlq_repo,
            "uuid",
            SimpleNamespace(uuid4=lambda: SimpleNamespace(hex=event_id)),
        )

        with pytest.raises(sqlite3.IntegrityError):
            client.post(f"/dlq/{event_id}/requeue")
        monkeypatch.undo()

        assert shared.in_transaction is False
        # No partial state: UPDATE increment rolled back, no descendant row.
        assert _get_field(client, event_id, "dlq_requeue_count") == 0
        n = shared.execute(
            "SELECT COUNT(*) FROM events WHERE redelivered_from = ?",
            (event_id,),
        ).fetchone()[0]
        assert n == 0

        # Connection reuse: a normal requeue on the same connection succeeds.
        resp = client.post(f"/dlq/{event_id}/requeue")
        assert resp.status_code == 200
