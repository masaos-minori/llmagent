"""tests/test_eventbus_publish_contract.py
Event Bus publish persistence contract tests.
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Any:
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
    monkeypatch.setattr(eb_app, "_ENVELOPE_SCHEMA_PATH", schema_path)

    with TestClient(eb_app.app) as c:
        yield c


def _event(topic: str = "t") -> dict[str, Any]:
    return {
        "event_id": str(uuid.uuid4()),
        "topic": topic,
        "payload": {},
        "producer": "p",
        "published_at": "2026-06-22T12:00:00Z",
    }


def test_publish_succeeds_if_jsonl_append_fails(client: TestClient) -> None:
    """JSONL append failure after SQLite commit must still return 200."""
    ev = _event()
    with patch("eventbus.app._append_jsonl", side_effect=OSError("disk full")):
        resp = client.post("/publish", json=ev)
    assert resp.status_code == 200
    assert resp.json()["event_id"] == ev["event_id"]

    # Event should be retrievable from SQLite via replay
    replay = client.get("/replay", params={"since_seq": 0, "format": "json"})
    assert replay.status_code == 200
    event_ids = [e["event_id"] for e in replay.json()]
    assert ev["event_id"] in event_ids
