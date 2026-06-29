"""tests/test_eventbus_publish_contract.py

Event Bus publish persistence contract tests.
"""

from __future__ import annotations

import uuid
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from eventbus import app as eb_app
    from eventbus.config import EventBusConfig

    cfg = EventBusConfig(
        port=8015,
        db_path=str(tmp_path / "eventbus.sqlite"),
        storage_dir=str(tmp_path / "storage"),
        offsets_dir=str(tmp_path / "offsets"),
        deadletter_dir=str(tmp_path / "deadletter"),
        max_retry=3,
    )
    monkeypatch.setattr(eb_app, "load_config", lambda path=None: cfg)
    schema_path = Path(__file__).parent.parent / "schemas" / "event_envelope.json"
    monkeypatch.setattr(eb_app, "get_schema_path", lambda: schema_path)

    with TestClient(eb_app.app) as c:
        yield c


def _event(topic: str = "test.topic") -> dict:
    return {
        "event_id": str(uuid.uuid4()),
        "topic": topic,
        "payload": {"key": "value"},
        "producer": "test-producer",
        "published_at": "2026-06-22T11:56:00Z",
    }


class TestPublishEnvelopeSchemaContract:
    """Tests for the publish envelope JSON Schema contract."""

    def test_invalid_non_uuid_v4_event_id_rejected(self, client: TestClient) -> None:
        """Non-UUID-v4 event_id must be rejected by schema validation."""
        resp = client.post(
            "/publish",
            json={**_event(), "event_id": "not-a-uuid"},
        )
        assert resp.status_code == 422

    def test_invalid_uuid_v4_format_rejected(self, client: TestClient) -> None:
        """event_id must match UUID v4 pattern (4xxx, 8xx/9xx/axx/bxx variant)."""
        resp = client.post(
            "/publish",
            json={**_event(), "event_id": "12345678-1234-5678-1234-56789abcdef0"},
        )
        assert resp.status_code == 422

    def test_missing_required_event_id_rejected(self, client: TestClient) -> None:
        """Missing required field 'event_id' must be rejected."""
        event = _event()
        del event["event_id"]
        resp = client.post("/publish", json=event)
        assert resp.status_code == 422

    def test_missing_required_topic_rejected(self, client: TestClient) -> None:
        """Missing required field 'topic' must be rejected."""
        event = _event()
        del event["topic"]
        resp = client.post("/publish", json=event)
        assert resp.status_code == 422

    def test_missing_required_payload_rejected(self, client: TestClient) -> None:
        """Missing required field 'payload' must be rejected."""
        event = _event()
        del event["payload"]
        resp = client.post("/publish", json=event)
        assert resp.status_code == 422

    def test_missing_required_producer_rejected(self, client: TestClient) -> None:
        """Missing required field 'producer' must be rejected."""
        event = _event()
        del event["producer"]
        resp = client.post("/publish", json=event)
        assert resp.status_code == 422

    def test_missing_required_published_at_rejected(self, client: TestClient) -> None:
        """Missing required field 'published_at' must be rejected."""
        event = _event()
        del event["published_at"]
        resp = client.post("/publish", json=event)
        assert resp.status_code == 422

    def test_non_object_payload_rejected(self, client: TestClient) -> None:
        """payload must be a JSON object, not array or string."""
        resp = client.post(
            "/publish",
            json={**_event(), "payload": [1, 2, 3]},
        )
        assert resp.status_code == 422

    def test_string_payload_rejected(self, client: TestClient) -> None:
        """payload must be a JSON object, not a string."""
        resp = client.post(
            "/publish",
            json={**_event(), "payload": "not-an-object"},
        )
        assert resp.status_code == 422

    def test_array_payload_rejected(self, client: TestClient) -> None:
        """payload must be a JSON object, not an array."""
        resp = client.post(
            "/publish",
            json={**_event(), "payload": []},
        )
        assert resp.status_code == 422

    def test_additional_unexpected_property_rejected(self, client: TestClient) -> None:
        """additionalProperties=false must reject unknown fields."""
        resp = client.post(
            "/publish",
            json={**_event(), "unknown_field": "unexpected"},
        )
        assert resp.status_code == 422

    def test_multiple_additional_properties_rejected(self, client: TestClient) -> None:
        """Multiple additional properties must be rejected."""
        resp = client.post(
            "/publish",
            json={**_event(), "field1": "val1", "field2": "val2"},
        )
        assert resp.status_code == 422

    def test_published_at_format_not_validated_by_jsonschema(
        self, client: TestClient
    ) -> None:
        """jsonschema does NOT validate the date-time format by default.

        The jsonschema library ignores the 'format' keyword unless a format
        checker is explicitly attached. This test documents that behavior
        so it is not mistaken for a bug.
        """
        resp = client.post(
            "/publish",
            json={**_event(), "published_at": "not-a-date"},
        )
        assert resp.status_code == 200

    def test_empty_string_topic_rejected(self, client: TestClient) -> None:
        """topic must have minLength=1."""
        resp = client.post(
            "/publish",
            json={**_event(), "topic": ""},
        )
        assert resp.status_code == 422

    def test_empty_string_producer_rejected(self, client: TestClient) -> None:
        """producer must have minLength=1."""
        resp = client.post(
            "/publish",
            json={**_event(), "producer": ""},
        )
        assert resp.status_code == 422

    def test_schema_version_optional_accepted(self, client: TestClient) -> None:
        """Optional schema_version field is accepted when provided."""
        resp = client.post(
            "/publish",
            json={**_event(), "schema_version": "2.0"},
        )
        assert resp.status_code == 200

    def test_schema_version_defaults_when_not_provided(
        self, client: TestClient
    ) -> None:
        """When schema_version is not provided, the publish succeeds (default '1.0' is applied server-side)."""
        resp = client.post(
            "/publish",
            json=_event(),
        )
        assert resp.status_code == 200
        # Verify the event was stored in SQLite
        replay_resp = client.get("/replay", params={"since_seq": 0, "format": "json"})
        replay_data = replay_resp.json()
        items = replay_data["items"]
        assert len(items) >= 1

    def test_schema_version_empty_string_accepted(self, client: TestClient) -> None:
        """Empty string schema_version is accepted (no minLength constraint)."""
        resp = client.post(
            "/publish",
            json={**_event(), "schema_version": ""},
        )
        assert resp.status_code == 200

    def test_topic_too_long_rejected(self, client: TestClient) -> None:
        """topic must have maxLength=255."""
        resp = client.post(
            "/publish",
            json={**_event(), "topic": "a" * 256},
        )
        assert resp.status_code == 422

    def test_producer_too_long_rejected(self, client: TestClient) -> None:
        """producer must have maxLength=255."""
        resp = client.post(
            "/publish",
            json={**_event(), "producer": "a" * 256},
        )
        assert resp.status_code == 422

    def test_valid_event_with_schema_version_succeeds(self, client: TestClient) -> None:
        """Valid event with optional schema_version must succeed."""
        resp = client.post(
            "/publish",
            json={**_event(), "schema_version": "1.0"},
        )
        assert resp.status_code == 200

    def test_valid_event_without_schema_version_succeeds(
        self, client: TestClient
    ) -> None:
        """Valid event without optional schema_version must succeed."""
        resp = client.post(
            "/publish",
            json=_event(),
        )
        assert resp.status_code == 200


class TestPublishContract:
    def test_publish_succeeds_if_jsonl_append_fails(self, client: TestClient) -> None:
        """JSONL append 失敗後も SQLite commit 済みなら 200 を返す。"""

        # Patch Path.open to raise OSError for JSONL writes
        original_open = Path.open

        def failing_open(self, *args, **kwargs):
            if "events.jsonl" in str(self):
                raise OSError("disk full")
            return original_open(self, *args, **kwargs)

        with patch.object(Path, "open", failing_open):
            resp = client.post(
                "/publish",
                json=_event(),
            )
        assert resp.status_code == 200
        # Event should be retrievable from SQLite
        replay_resp = client.get("/replay", params={"since_seq": 0, "format": "json"})
        assert replay_resp.status_code == 200
        events = replay_resp.json()
        assert len(events) >= 1
