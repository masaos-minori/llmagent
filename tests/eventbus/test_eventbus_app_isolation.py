"""tests/test_eventbus_app_isolation.py
Event Bus app state isolation tests.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient


def _make_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    from eventbus import app as eb_app
    from eventbus.config import EventBusConfig

    tmp_path.mkdir(
        parents=True, exist_ok=True
    )  # lifespan opens db without mkdir'ing its parent
    cfg = EventBusConfig(
        port=8015,
        db_path=str(tmp_path / "eventbus.sqlite"),
        storage_dir=str(tmp_path / "storage"),
        deadletter_dir=str(tmp_path / "deadletter"),
        max_retry=3,
        auth_token="test-token",
    )

    # Monkeypatch load_config to prevent app from trying to load from default path
    monkeypatch.setattr(eb_app, "load_config", lambda path=None: cfg)
    schema_path = (
        Path(__file__).parent.parent.parent / "schemas" / "event_envelope.json"
    )
    monkeypatch.setattr(eb_app, "_ENVELOPE_SCHEMA_PATH", schema_path)
    monkeypatch.setattr(eb_app, "get_schema_path", lambda: schema_path)

    # TestClient's context manager runs lifespan(), which is the single state
    # initializer (config/db/schema/broker/tasks) and also closes the DB and
    # cancels its tasks on exit. A prior manual pre-initialization here leaked
    # orphan DB connections, broker instances, and a closed event loop per call,
    # which surfaced as order-dependent failures in the full suite.
    client = TestClient(eb_app.app)
    client.headers["Authorization"] = "Bearer test-token"
    return client


class TestAppStateIsolation:
    def test_two_clients_different_db(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Two TestClient instances should use different databases."""
        import eventbus.app as eb_app

        client1 = _make_client(tmp_path / "client1", monkeypatch)
        with client1:
            resp1 = client1.get("/health")
            assert resp1.status_code == 200
            db_path1 = eb_app.app.state.config.db_path
            assert "client1" in db_path1

        client2 = _make_client(tmp_path / "client2", monkeypatch)
        with client2:
            resp2 = client2.get("/health")
            assert resp2.status_code == 200
            db_path2 = eb_app.app.state.config.db_path
            assert "client2" in db_path2

        assert db_path1 != db_path2

    def test_two_clients_different_broker(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Two TestClient instances should have different broker instances."""
        import eventbus.app as eb_app

        client1 = _make_client(tmp_path / "client1", monkeypatch)
        with client1:
            broker1_id = (
                id(eb_app.app.state.broker) if eb_app.app.state.broker else None
            )

        client2 = _make_client(tmp_path / "client2", monkeypatch)
        with client2:
            broker2_id = (
                id(eb_app.app.state.broker) if eb_app.app.state.broker else None
            )

        assert broker1_id is not None
        assert broker2_id is not None
        assert broker1_id != broker2_id

    def test_two_clients_different_config(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Two TestClient instances should have different config instances."""
        import eventbus.app as eb_app

        client1 = _make_client(tmp_path / "client1", monkeypatch)
        with client1:
            config1_id = (
                id(eb_app.app.state.config) if eb_app.app.state.config else None
            )

        client2 = _make_client(tmp_path / "client2", monkeypatch)
        with client2:
            config2_id = (
                id(eb_app.app.state.config) if eb_app.app.state.config else None
            )

        assert config1_id is not None
        assert config2_id is not None
        assert config1_id != config2_id
