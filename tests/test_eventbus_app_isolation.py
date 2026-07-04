"""tests/test_eventbus_app_isolation.py
Event Bus app state isolation tests.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient


async def _init_state(cfg: Any) -> None:
    import pathlib

    from eventbus import app as eb_app

    eb_app.app.state.config = cfg
    pathlib.Path(cfg.db_path).parent.mkdir(parents=True, exist_ok=True)
    eb_app.app.state.db = eb_app.open_db(cfg.db_path)
    schema_path = Path(__file__).parent.parent / "schemas" / "event_envelope.json"
    eb_app.app.state.envelope_schema = eb_app.orjson.loads(schema_path.read_bytes())
    pathlib.Path(cfg.storage_dir).mkdir(parents=True, exist_ok=True)
    eb_app.app.state.broker = eb_app.EventBroker()


async def _do_cleanup() -> None:
    from eventbus import app as eb_app

    if eb_app.app.state.dlq_task:
        eb_app.app.state.dlq_task.cancel()
        try:
            await eb_app.app.state.dlq_task
        except asyncio.CancelledError:
            pass
    if eb_app.app.state.broker:
        eb_app.app.state.broker.shutdown()
    if eb_app.app.state.db:
        eb_app.app.state.db.close()


def _make_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
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

    # Monkeypatch load_config to prevent app from trying to load from default path
    monkeypatch.setattr(eb_app, "load_config", lambda path=None: cfg)
    schema_path = Path(__file__).parent.parent / "schemas" / "event_envelope.json"
    monkeypatch.setattr(eb_app, "_ENVELOPE_SCHEMA_PATH", schema_path)
    monkeypatch.setattr(eb_app, "get_schema_path", lambda: schema_path)

    # Prevent segfault: _dlq_loop uses asyncio.to_thread() whose thread continues
    # running even after task cancellation. If db.close() races with the thread
    # accessing the SQLite connection, the C library crashes. Replace with a
    # no-op coroutine that is safely cancellable.
    async def _noop_dlq_loop(app: Any) -> None:
        await asyncio.sleep(9999)

    monkeypatch.setattr(eb_app, "_dlq_loop", _noop_dlq_loop)

    # Initialize app.state before creating TestClient
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_init_state(cfg))
    finally:
        loop.close()

    return TestClient(eb_app.app)


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
