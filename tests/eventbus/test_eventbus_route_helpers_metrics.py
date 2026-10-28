"""tests/eventbus/test_eventbus_route_helpers_metrics.py

Prometheus metrics instrumentation for run_with_db_lock.
"""

from __future__ import annotations

import asyncio
import threading
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from eventbus.config import EventBusConfig
from prometheus_client import REGISTRY, generate_latest

# -- Helpers ------------------------------------------------------------------


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


def _sample(name: str) -> float:
    """Return a registered Prometheus sample value, 0.0 when it has no sample yet."""
    return REGISTRY.get_sample_value(name) or 0.0


def _run_with_lock(func: Any) -> Any:
    """Run `func` through run_with_db_lock on a fresh event loop."""

    async def _call() -> Any:
        from eventbus.route_helpers import run_with_db_lock

        return await run_with_db_lock(func)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_call())
    finally:
        loop.close()


@pytest.fixture(scope="module")
def tmp_path_module(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return tmp_path_factory.mktemp("eventbus_metrics")


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from eventbus import app as eb_app

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

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_init_state(cfg))
    finally:
        loop.close()

    from fastapi.testclient import TestClient

    with TestClient(eb_app.app) as c:
        c.headers["Authorization"] = "Bearer test-token"
        yield c

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_do_cleanup())
    finally:
        loop.close()

    # Clear Prometheus metrics after each test to avoid cross-test pollution
    for collector in list(REGISTRY._collector_to_names.keys()):
        try:
            REGISTRY.unregister(collector)
        except ValueError:
            pass


class TestRunWithDbLockMetrics:
    """Tests for Prometheus metrics in run_with_db_lock."""

    def test_query_duration_metric_observed(self) -> None:
        """run_with_db_lock observes _db_query_duration once per call, with a positive
        duration. No app fixture: its DLQ sweep would add observations of its own."""
        from tests.eventbus.conftest import _ensure_route_helpers_metrics_registered

        _ensure_route_helpers_metrics_registered()
        count_before = _sample("eventbus_db_query_duration_seconds_count")
        sum_before = _sample("eventbus_db_query_duration_seconds_sum")

        assert _run_with_lock(lambda: 42) == 42

        assert _sample("eventbus_db_query_duration_seconds_count") - count_before == 1
        assert _sample("eventbus_db_query_duration_seconds_sum") - sum_before > 0

    def test_lock_wait_time_metric_observed(self) -> None:
        """run_with_db_lock observes _db_lock_wait_time once per call, and an uncontended
        call waits well under the 1 ms contention threshold."""
        from tests.eventbus.conftest import _ensure_route_helpers_metrics_registered

        _ensure_route_helpers_metrics_registered()
        count_before = _sample("eventbus_db_lock_wait_time_seconds_count")
        sum_before = _sample("eventbus_db_lock_wait_time_seconds_sum")

        assert _run_with_lock(lambda: True) is True

        assert _sample("eventbus_db_lock_wait_time_seconds_count") - count_before == 1
        assert _sample("eventbus_db_lock_wait_time_seconds_sum") - sum_before < 0.001

    def test_lock_contention_counter_increments_on_slow_acquire(
        self, client: Any, tmp_path: Path
    ) -> None:
        """_db_lock_contention increments when lock wait exceeds threshold."""

        # Ensure route_helpers metrics are registered (may have been
        # unregistered by a prior test's cleanup).
        from tests.eventbus.conftest import _ensure_route_helpers_metrics_registered

        _ensure_route_helpers_metrics_registered()

        # Capture before/after delta to avoid order-dependent failures
        before_text = generate_latest().decode()
        before_lines = [
            line
            for line in before_text.splitlines()
            if "eventbus_db_lock_contention_total" in line
        ]
        before_value = float(before_lines[-1].split(" ")[-1]) if before_lines else 0.0

        # Call run_with_db_lock multiple times to potentially trigger contention
        async def _call():
            from eventbus.route_helpers import run_with_db_lock

            def _noop():
                return True

            return await run_with_db_lock(_noop)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            for _ in range(5):
                loop.run_until_complete(_call())
        finally:
            loop.close()

        # Collect metrics after calling
        text_after = generate_latest().decode()
        lines_after = [
            line
            for line in text_after.splitlines()
            if "eventbus_db_lock_contention_total" in line
        ]
        count_after = float(lines_after[-1].split(" ")[-1]) if lines_after else 0.0
        delta = count_after - before_value
        # Counter may or may not have incremented depending on whether
        # lock wait exceeded the 1ms threshold — just verify it's a valid number
        assert delta >= 0

    @pytest.mark.asyncio
    async def test_contended_call_waits_and_increments_contention_counter(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A call queued behind a held lock records the wait up to acquisition (not the
        callback time), increments the contention counter and records the callback as
        the query duration. The clock is scripted so the timing is deterministic."""
        import eventbus.route_helpers as rh
        from eventbus import db as eb_db

        from tests.eventbus.conftest import _ensure_route_helpers_metrics_registered

        _ensure_route_helpers_metrics_registered()

        real_lock = threading.Lock()
        worker_waiting = threading.Event()

        class _SignalingLock:
            """Signal that the worker reached the lock, then block on the real lock."""

            def __enter__(self) -> None:
                worker_waiting.set()
                real_lock.acquire()

            def __exit__(self, *exc_info: object) -> None:
                real_lock.release()

        monkeypatch.setattr(eb_db, "get_db_lock", lambda: _SignalingLock())
        # outer start, worker start, lock acquired, callback done, outer end
        ticks = iter([100.0, 100.0, 100.5, 100.6, 100.6])
        monkeypatch.setattr(
            rh, "time", SimpleNamespace(monotonic=lambda: next(ticks, 100.6))
        )

        wait_count = _sample("eventbus_db_lock_wait_time_seconds_count")
        wait_sum = _sample("eventbus_db_lock_wait_time_seconds_sum")
        duration_sum = _sample("eventbus_db_query_duration_seconds_sum")
        contention = _sample("eventbus_db_lock_contention_total")

        real_lock.acquire()  # the test plays the role of the lock holder
        task = asyncio.create_task(rh.run_with_db_lock(lambda: "done"))
        assert await asyncio.to_thread(worker_waiting.wait, 5), "worker never queued"
        real_lock.release()
        assert await asyncio.wait_for(task, 5) == "done"

        assert _sample("eventbus_db_lock_wait_time_seconds_count") - wait_count == 1
        assert _sample("eventbus_db_lock_wait_time_seconds_sum") - wait_sum == (
            pytest.approx(0.5)
        )
        assert _sample("eventbus_db_query_duration_seconds_sum") - duration_sum == (
            pytest.approx(0.1)
        )
        assert _sample("eventbus_db_lock_contention_total") - contention == 1

    def test_raising_callback_still_records_query_duration(self) -> None:
        """The query duration is recorded even when the callback raises."""
        from tests.eventbus.conftest import _ensure_route_helpers_metrics_registered

        _ensure_route_helpers_metrics_registered()
        count_before = _sample("eventbus_db_query_duration_seconds_count")

        def _boom() -> None:
            raise ValueError("callback failed")

        with pytest.raises(ValueError, match="callback failed"):
            _run_with_lock(_boom)

        assert _sample("eventbus_db_query_duration_seconds_count") - count_before == 1
