"""tests/test_eventbus_health.py

Event Bus health endpoint tests.
"""

from __future__ import annotations

import asyncio
import sqlite3
import types
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from tests.eventbus.eventbus_helpers import (
    eventbus_auth_headers,
    make_eventbus_client,
)


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from eventbus import app as eb_app
    from eventbus.config import EventBusConfig

    cfg = EventBusConfig(
        port=8015,
        db_path=str(tmp_path / "eventbus.sqlite"),
        storage_dir=str(tmp_path / "storage"),
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

    # The production lifespan starts the app and its shutdown sequence stops it.
    with TestClient(eb_app.app) as c:
        c.headers["Authorization"] = "Bearer test-token"
        yield c


@pytest.fixture
def real_dlq_loop() -> Any:
    """Return the production ``_dlq_loop`` before any test replaces it."""
    from eventbus import app as eb_app

    return eb_app._dlq_loop


@pytest.fixture
def monitoring_client(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, real_dlq_loop: Any
):
    """Monitoring-role client whose background DLQ loop is replaced by an idle task.

    The real loop records a cycle result shortly after startup; replacing it keeps
    ``app.state.last_dlq_cycle_*`` under the test's control (``dlq_task`` still runs,
    so liveness stays true).
    """
    from eventbus import app as eb_app

    async def _idle_dlq_loop(app: Any) -> None:
        await asyncio.sleep(3600)

    monkeypatch.setattr(eb_app, "_dlq_loop", _idle_dlq_loop)
    with make_eventbus_client(tmp_path, monkeypatch, default_role="monitoring") as c:
        yield c


def _insert_failed_outbox(db: Any) -> None:
    """Insert one event and a terminal 'failed' dlq_outbox row (under the DB lock)."""
    from eventbus.db_conn import get_db_lock
    from eventbus.json_utils import now_iso

    with get_db_lock():
        db.execute(
            "INSERT INTO events (event_id, topic, payload, producer, published_at) "
            "VALUES ('evt-health-failed', 't', '{}', 'test', ?)",
            (now_iso(),),
        )
        db.execute(
            "INSERT INTO dlq_outbox (event_id, requested_at, status, attempts) "
            "VALUES ('evt-health-failed', ?, 'failed', 3)",
            (now_iso(),),
        )
        db.commit()


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
        # Tiered health fields (liveness, readiness)
        assert "liveness" in body
        assert "readiness" in body
        assert "integrity" not in body
        assert body["liveness"] is True
        assert body["readiness"] is True

    def test_health_degraded_when_db_unavailable(self, client: TestClient) -> None:
        from unittest.mock import MagicMock

        import eventbus.app as eb_app

        mock_db = MagicMock()
        mock_db.execute.side_effect = sqlite3.OperationalError("DB gone")
        eb_app.app.state.db = mock_db
        resp = client.get("/health")
        assert resp.status_code == 503
        body = resp.json()
        assert body["status"] == "degraded"
        assert body["db"] == "unavailable"

    def test_gate_predicate_is_true_for_healthy_and_capacity_only_payloads(
        self, client: TestClient
    ) -> None:
        """The deployment gate predicate holds for a healthy payload and for a
        capacity-only 503, which still reports liveness and readiness."""
        from eventbus import app as eb_app
        from eventbus.health_route import is_ready

        healthy = client.get("/health")
        assert healthy.status_code == 200
        body = healthy.json()
        assert is_ready(body["liveness"], body["readiness"]) is True

        # Shrink the subscriber capacity so one subscriber reaches it.
        object.__setattr__(eb_app.app.state.config, "subscriber_count", 1)
        sub = eb_app.app.state.broker.subscribe([])
        try:
            capacity = client.get("/health")
        finally:
            eb_app.app.state.broker.unsubscribe(sub)
        assert capacity.status_code == 503
        body = capacity.json()
        assert body["degraded_reasons"] == ["subscribers_at_capacity"]
        assert is_ready(body["liveness"], body["readiness"]) is True

    def test_gate_predicate_is_false_when_db_unavailable_or_dlq_task_stopped(
        self, client: TestClient
    ) -> None:
        from unittest.mock import MagicMock

        from eventbus import app as eb_app
        from eventbus.health_route import is_ready

        real_db = eb_app.app.state.db
        broken_db = MagicMock()
        broken_db.execute.side_effect = sqlite3.OperationalError("DB gone")
        eb_app.app.state.db = broken_db
        try:
            body = client.get("/health").json()
        finally:
            eb_app.app.state.db = real_db
        assert body["readiness"] is False
        assert is_ready(body["liveness"], body["readiness"]) is False

        eb_app.app.state.dlq_task.cancel()
        eb_app.app.state.dlq_task = None
        body = client.get("/health").json()
        assert body["liveness"] is False
        assert is_ready(body["liveness"], body["readiness"]) is False

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

    def test_health_reports_no_failures_before_first_sweep(
        self, monitoring_client: TestClient
    ) -> None:
        resp = monitoring_client.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["terminal_failed_outbox"] == 0
        assert body["last_dlq_sweep"] == {"result": "not_run", "time": None}
        assert body["degraded_reasons"] == []

    def test_health_reports_terminal_failed_outbox(
        self, monitoring_client: TestClient
    ) -> None:
        from eventbus import app as eb_app

        _insert_failed_outbox(eb_app.app.state.db)
        resp = monitoring_client.get("/health")
        assert resp.status_code == 503
        body = resp.json()
        assert body["terminal_failed_outbox"] >= 1
        assert "dlq_outbox_failed" in body["degraded_reasons"]
        # A terminal outbox failure is a real failure, not a gate change.
        assert body["liveness"] is True
        assert body["readiness"] is True

    def test_health_reports_failing_sweep(self, monitoring_client: TestClient) -> None:
        from eventbus import app as eb_app
        from eventbus.json_utils import now_iso

        eb_app.app.state.last_dlq_cycle_result = "failed"
        eb_app.app.state.last_dlq_cycle_time = now_iso()
        try:
            resp = monitoring_client.get("/health")
        finally:
            eb_app.app.state.last_dlq_cycle_result = "not_run"
            eb_app.app.state.last_dlq_cycle_time = None
        assert resp.status_code == 503
        body = resp.json()
        assert body["last_dlq_sweep"]["result"] == "failed"
        assert body["last_dlq_sweep"]["time"] is not None
        assert "dlq_sweep_failing" in body["degraded_reasons"]

    def test_new_degraded_reasons_do_not_change_liveness_or_readiness(
        self, monitoring_client: TestClient
    ) -> None:
        from eventbus import app as eb_app
        from eventbus.health_route import is_ready

        _insert_failed_outbox(eb_app.app.state.db)
        eb_app.app.state.last_dlq_cycle_result = "failed"
        try:
            body = monitoring_client.get("/health").json()
        finally:
            eb_app.app.state.last_dlq_cycle_result = "not_run"
        assert "dlq_outbox_failed" in body["degraded_reasons"]
        assert "dlq_sweep_failing" in body["degraded_reasons"]
        assert body["liveness"] is True
        assert body["readiness"] is True
        assert is_ready(body["liveness"], body["readiness"]) is True

    def test_health_leaves_count_null_when_count_query_fails(
        self, monitoring_client: TestClient
    ) -> None:
        from unittest.mock import patch

        with patch(
            "eventbus.health_route.count_failed_outbox",
            side_effect=sqlite3.OperationalError("count failed"),
        ):
            resp = monitoring_client.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["terminal_failed_outbox"] is None
        assert "dlq_outbox_failed" not in body["degraded_reasons"]

    def test_health_rejects_non_monitoring_role(
        self, monitoring_client: TestClient
    ) -> None:
        resp = monitoring_client.get(
            "/health", headers=eventbus_auth_headers("operator")
        )
        assert resp.status_code == 403


class TestDlqLoopRecording:
    """The loop records the result and time of each cycle on app.state."""

    @staticmethod
    def _run_one_cycle(
        eb_app: Any, real_dlq_loop: Any, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        class _StopLoop(Exception):
            pass

        async def _stop(_seconds: float) -> None:
            raise _StopLoop

        # Replace only this module's asyncio, and only for the one cycle, so the
        # loop's sleep ends the run and the app's shutdown sees the real module.
        with monkeypatch.context() as patch:
            patch.setattr(eb_app, "asyncio", types.SimpleNamespace(sleep=_stop))
            with pytest.raises(_StopLoop):
                asyncio.run(real_dlq_loop(eb_app.app))

    def test_clean_cycle_records_ok_and_time(
        self,
        monitoring_client: TestClient,
        real_dlq_loop: Any,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from eventbus import app as eb_app

        self._run_one_cycle(eb_app, real_dlq_loop, monkeypatch)
        assert eb_app.app.state.last_dlq_cycle_result == "ok"
        assert eb_app.app.state.last_dlq_cycle_time.endswith("Z")

    def test_failing_cycle_records_failed_and_time(
        self,
        monitoring_client: TestClient,
        real_dlq_loop: Any,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from eventbus import app as eb_app

        def _boom(*_args: Any, **_kwargs: Any) -> int:
            raise sqlite3.OperationalError("sweep failed")

        monkeypatch.setattr(eb_app, "sweep_orphans", _boom)
        self._run_one_cycle(eb_app, real_dlq_loop, monkeypatch)
        assert eb_app.app.state.last_dlq_cycle_result == "failed"
        assert eb_app.app.state.last_dlq_cycle_time.endswith("Z")
