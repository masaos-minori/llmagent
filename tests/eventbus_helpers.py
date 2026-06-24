"""Shared helpers for Event Bus tests."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient


def make_eventbus_client(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, max_retry: int = 3
) -> Any:
    from eventbus import app as eb_app
    from eventbus.config import EventBusConfig

    cfg = EventBusConfig(
        port=8015,
        db_path=str(tmp_path / "eventbus.sqlite"),
        storage_dir=str(tmp_path / "storage"),
        offsets_dir=str(tmp_path / "offsets"),
        deadletter_dir=str(tmp_path / "deadletter"),
        max_retry=max_retry,
    )
    monkeypatch.setattr(eb_app, "load_config", lambda path=None: cfg)
    schema_path = Path(__file__).parent.parent / "schemas" / "event_envelope.json"
    monkeypatch.setattr(eb_app, "_ENVELOPE_SCHEMA_PATH", schema_path)
    return TestClient(eb_app.app)
