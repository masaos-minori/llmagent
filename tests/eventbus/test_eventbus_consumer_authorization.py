"""tests/eventbus/test_eventbus_consumer_authorization.py

ADR-013 INV-02 / INV-07: Consumer routes admit only Consumer-scoped principals bound
to explicit consumer_id and topic authorizations. The shared auth_token and the
admin_token hold no Consumer role and have no bypass; a rejected request changes no
delivery state.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

_AUTH = {
    "shared": "control-token",
    "admin": "admin-token",
    "publisher": "publisher-token",
    "consumer": "consumer-token",
}


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _build_client(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    consumer_authorization: dict[str, list[str]],
) -> Iterator[TestClient]:
    from eventbus import app as eb_app
    from eventbus.config import EventBusConfig

    cfg = EventBusConfig(
        port=8015,
        db_path=str(tmp_path / "eventbus.sqlite"),
        storage_dir=str(tmp_path / "storage"),
        offsets_dir=str(tmp_path / "offsets"),
        deadletter_dir=str(tmp_path / "deadletter"),
        max_retry=3,
        auth_token=_AUTH["shared"],
        admin_token=_AUTH["admin"],
        publisher_token=_AUTH["publisher"],
        consumer_token=_AUTH["consumer"],
        consumer_authorization=consumer_authorization,
    )
    monkeypatch.setattr(eb_app, "load_config", lambda path=None: cfg)
    schema_path = (
        Path(__file__).parent.parent.parent / "schemas" / "event_envelope.json"
    )
    monkeypatch.setattr(eb_app, "get_schema_path", lambda: schema_path)
    with TestClient(eb_app.app) as client:
        yield client


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    yield from _build_client(tmp_path, monkeypatch, {"consumer-A": ["t"]})


@pytest.fixture
def deny_all_client(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Iterator[TestClient]:
    yield from _build_client(tmp_path, monkeypatch, {})


def _publish(client: TestClient, topic: str = "t") -> str:
    body: dict[str, Any] = {
        "event_id": str(uuid.uuid4()),
        "topic": topic,
        "payload": {},
        "producer": "p",
        "published_at": "2026-10-15T00:00:00Z",
    }
    resp = client.post("/publish", json=body, headers=_bearer(_AUTH["publisher"]))
    assert resp.status_code == 200
    return str(body["event_id"])


def _delivery_state(event_id: str, consumer_id: str) -> tuple[Any, Any, Any]:
    """Return (consumer_delivery row, consumer_offsets row, events.dlq_at)."""
    import eventbus.app as eb_app

    db = eb_app.app.state.db
    delivery = db.execute(
        "SELECT acked, consumer_delivery_failure_count FROM consumer_delivery "
        "WHERE consumer_id = ? AND event_id = ?",
        (consumer_id, event_id),
    ).fetchone()
    offset = db.execute(
        "SELECT offset FROM consumer_offsets WHERE consumer_id = ?", (consumer_id,)
    ).fetchone()
    dlq = db.execute(
        "SELECT dlq_at FROM events WHERE event_id = ?", (event_id,)
    ).fetchone()
    return (
        tuple(delivery) if delivery else None,
        tuple(offset) if offset else None,
        dlq[0] if dlq else None,
    )


class TestSharedAndAdminTokensHaveNoConsumerBypass:
    @pytest.mark.parametrize("token_key", ["shared", "admin"])
    def test_subscribe_ack_and_nack_return_403(
        self, client: TestClient, token_key: str
    ) -> None:
        event_id = _publish(client)
        headers = _bearer(_AUTH[token_key])
        assert (
            client.get(
                "/subscribe?consumer_id=consumer-A&topic=t", headers=headers
            ).status_code
            == 403
        )
        assert (
            client.post(
                f"/events/{event_id}/ack",
                params={"consumer_id": "consumer-A"},
                headers=headers,
            ).status_code
            == 403
        )
        assert (
            client.post(
                "/nack",
                params={"event_id": event_id, "consumer_id": "consumer-A"},
                headers=headers,
            ).status_code
            == 403
        )

    @pytest.mark.parametrize("token_key", ["shared", "admin"])
    def test_rejected_ack_and_nack_change_no_delivery_state(
        self, client: TestClient, token_key: str
    ) -> None:
        event_id = _publish(client)
        before = _delivery_state(event_id, "consumer-A")
        headers = _bearer(_AUTH[token_key])
        client.post(
            f"/events/{event_id}/ack",
            params={"consumer_id": "consumer-A"},
            headers=headers,
        )
        client.post(
            "/nack",
            params={"event_id": event_id, "consumer_id": "consumer-A"},
            headers=headers,
        )
        assert _delivery_state(event_id, "consumer-A") == before == (None, None, None)

    def test_unknown_token_is_401_not_403(self, client: TestClient) -> None:
        resp = client.post(
            "/events/x/ack",
            params={"consumer_id": "consumer-A"},
            headers=_bearer("unknown-token"),
        )
        assert resp.status_code == 401


class TestConsumerPrincipalBinding:
    def test_authorized_consumer_id_and_topic_succeed(self, client: TestClient) -> None:
        event_id = _publish(client)
        resp = client.post(
            f"/events/{event_id}/ack",
            params={"consumer_id": "consumer-A"},
            headers=_bearer(_AUTH["consumer"]),
        )
        assert resp.status_code == 200

    def test_unauthorized_consumer_id_returns_403(self, client: TestClient) -> None:
        event_id = _publish(client)
        headers = _bearer(_AUTH["consumer"])
        assert (
            client.post(
                f"/events/{event_id}/ack",
                params={"consumer_id": "consumer-B"},
                headers=headers,
            ).status_code
            == 403
        )
        assert (
            client.post(
                "/nack",
                params={"event_id": event_id, "consumer_id": "consumer-B"},
                headers=headers,
            ).status_code
            == 403
        )
        assert _delivery_state(event_id, "consumer-B") == (None, None, None)

    def test_unauthorized_topic_returns_403(self, client: TestClient) -> None:
        resp = client.get(
            "/subscribe?consumer_id=consumer-A&topic=other",
            headers=_bearer(_AUTH["consumer"]),
        )
        assert resp.status_code == 403

    def test_empty_consumer_mapping_denies_every_consumer_id(
        self, deny_all_client: TestClient
    ) -> None:
        event_id = _publish(deny_all_client)
        resp = deny_all_client.post(
            f"/events/{event_id}/ack",
            params={"consumer_id": "consumer-A"},
            headers=_bearer(_AUTH["consumer"]),
        )
        assert resp.status_code == 403
        assert (
            deny_all_client.get(
                "/subscribe?consumer_id=consumer-A&topic=t",
                headers=_bearer(_AUTH["consumer"]),
            ).status_code
            == 403
        )
        assert _delivery_state(event_id, "consumer-A") == (None, None, None)
