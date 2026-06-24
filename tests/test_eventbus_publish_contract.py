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


class TestPublishContract:
    def test_publish_succeeds_if_jsonl_append_fails(self, client: TestClient) -> None:
        """JSONL append 失敗後も SQLite commit 済みなら 200 を返す。"""
        with patch("eventbus.app._append_jsonl", side_effect=OSError("disk full")):
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
