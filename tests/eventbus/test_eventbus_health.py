"""tests/test_eventbus_health.py

Event Bus health endpoint tests.
"""

from __future__ import annotations

import asyncio
import sqlite3
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient


async def _init_state(cfg: Any) -> None:
    import pathlib

    from eventbus import app as eb_app

    schema_path = (
        Path(__file__).parent.parent.parent / "schemas" / "event_envelope.json"
    )
    eb_app.app.state.config = cfg
    eb_app.app.state.db = eb_app.open_db(cfg.db_path)
    eb_app.app.state.envelope_schema = eb_app.orjson.loads(schema_path.read_bytes())
    pathlib.Path(cfg.storage_dir).mkdir(parents=True, exist_ok=True)
    eb_app.app.state.broker = eb_app.EventBroker(cfg)


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
        auth_token="test-token",
    )
    monkeypatch.setattr(eb_app, "load_config", lambda path=None: cfg)
    schema_path = (
        Path(__file__).parent.parent.parent / "schemas" / "event_envelope.json"
    )
    monkeypatch.setattr(eb_app, "_ENVELOPE_SCHEMA_PATH", schema_path)
    monkeypatch.setattr(eb_app, "get_schema_path", lambda: schema_path)

    # Initialize app.state before creating TestClient
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_init_state(cfg))
    finally:
        loop.close()

    with TestClient(eb_app.app) as c:
        c.headers["Authorization"] = "Bearer test-token"
        yield c

    # Cleanup on teardown
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_do_cleanup())
    finally:
        loop.close()


class TestHealth:
    def test_health_ok(self, client: TestClient) -> None:
        resp = client.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        assert body["db"] == "ok"
        assert body["dlq_task"] == "running"
        assert body["overflow_disconnects"] == 0
        assert body["duplicate_connection_rejections"] == 0

    def test_health_degraded_when_db_unavailable(self, client: TestClient) -> None:
        from unittest.mock import MagicMock

        import eventbus.app as eb_app

        mock_db = MagicMock()
        mock_db.execute.side_effect = sqlite3.OperationalError("DB gone")
        eb_app.app.state.db = mock_db  # type: ignore[assignment]
        resp = client.get("/health")
        assert resp.status_code == 503
        body = resp.json()
        assert body["status"] == "degraded"
        assert body["db"] == "unavailable"

    def test_health_broker_unavailable(self, client: TestClient) -> None:
        """Test that health endpoint returns degraded status when broker is unavailable."""
        from unittest.mock import patch

        with patch(
            "eventbus.health_route.get_broker", return_value=None
        ) as mock_get_broker:
            resp = client.get("/health")
            assert resp.status_code == 503
            body = resp.json()
            assert body["status"] == "degraded"
            assert "broker_unavailable" in body["degraded_reasons"]
            mock_get_broker.assert_called_once()

    def test_health_503_when_dlq_task_stopped(self, client: TestClient) -> None:
        """Health endpoint returns HTTP 503 when DLQ task is not running."""
        from eventbus import app as eb_app

        assert eb_app.app.state.dlq_task is not None
        eb_app.app.state.dlq_task.cancel()
        try:
            eb_app.app.state.dlq_task = None
        except asyncio.CancelledError:
            pass

        resp = client.get("/health")
        assert resp.status_code == 503
        body = resp.json()
        assert body["status"] == "degraded"
        assert "dlq_task_stopped" in body["degraded_reasons"]

    def test_health_reports_overflow_and_duplicate_counters(
        self, client: TestClient
    ) -> None:
        """Health response reflects incremented overflow/duplicate counters."""
        from eventbus import app as eb_app

        sub1 = eb_app.app.state.broker.subscribe([], consumer_id="dup-health")
        try:
            # Second subscribe with same consumer_id triggers rejection
            with pytest.raises(Exception):
                eb_app.app.state.broker.subscribe([], consumer_id="dup-health")
            resp = client.get("/health")
            assert resp.status_code == 200
            body = resp.json()
            assert body["duplicate_connection_rejections"] >= 1
        finally:
            eb_app.app.state.broker.unsubscribe(sub1)

    def test_health_endpoint_metrics_accessible(self, client: TestClient) -> None:
        """Health endpoint reads metrics via public API without accessing private internals."""
        resp = client.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert "metrics" in body
        assert "lock_wait_avg_seconds" in body["metrics"]
        assert "query_duration_avg_seconds" in body["metrics"]
        assert "lock_contention_total" in body["metrics"]
        assert body["metrics"]["lock_wait_avg_seconds"] >= 0
        assert body["metrics"]["query_duration_avg_seconds"] >= 0
        assert body["metrics"]["lock_contention_total"] >= 0

    def test_health_endpoint_metrics_unavailable_degrades_gracefully(
        self, client: TestClient
    ) -> None:
        """Health endpoint returns stable response when metrics are inaccessible."""
        from unittest.mock import MagicMock, patch

        from eventbus.route_helpers import (
            _db_lock_contention,
            _db_lock_wait_time,
            _db_query_duration,
        )

        mock_fail = MagicMock(side_effect=ValueError("metric read failure"))
        with patch.object(_db_lock_wait_time, "collect", mock_fail):
            with patch.object(_db_query_duration, "collect", mock_fail):
                with patch.object(_db_lock_contention, "collect", mock_fail):
                    resp = client.get("/health")
                    assert resp.status_code == 200
                    body = resp.json()
                    assert body["metrics"]["lock_wait_avg_seconds"] == 0.0
                    assert body["metrics"]["query_duration_avg_seconds"] == 0.0
                    assert body["metrics"]["lock_contention_total"] == 0

    def test_health_broker_backlog_threshold_with_none_broker(
        self, client: TestClient
    ) -> None:
        """Broker backlog threshold check does not raise AttributeError when broker is None."""
        from unittest.mock import patch

        with patch(
            "eventbus.health_route.get_broker", return_value=None
        ) as mock_get_broker:
            resp = client.get("/health")
            assert resp.status_code == 503
            body = resp.json()
            assert body["status"] == "degraded"
            assert "broker_unavailable" in body["degraded_reasons"]
            mock_get_broker.assert_called_once()
