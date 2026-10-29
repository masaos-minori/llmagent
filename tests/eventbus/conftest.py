"""tests/eventbus/conftest.py — Shared fixtures for Event Bus tests."""

from __future__ import annotations

from collections.abc import Generator

import pytest

# Register generator fixtures from helpers so pytest discovers them.
from tests.eventbus.eventbus_helpers import (
    eventbus_two_lifecycle_clients,  # noqa: F401 — fixture registration via side-effect import; pytest discovers eventbus_two_lifecycle_clients from helpers
)

# Precedent: tests/mcp_servers/mdq/conftest.py::_reset_mdq_state_for_testing()
# Precedent: tests/conftest.py::_reset_tool_registry() — session-scoped reset pattern


def _ensure_route_helpers_metrics_registered() -> None:
    """Ensure Prometheus metrics used by route_helpers are registered.

    Prevents cross-test metric pollution: if a prior test's cleanup
    unregistered collectors (e.g. test_eventbus_route_helpers_metrics.py's
    client fixture), restoring them ensures subsequent tests see their
    expected counters/histograms.
    """
    import eventbus.route_helpers as rh
    from prometheus_client import REGISTRY

    for obj in (rh._db_lock_wait_time, rh._db_query_duration, rh._db_lock_contention):
        if obj not in REGISTRY._collector_to_names:
            try:
                REGISTRY.register(obj)
            except ValueError:
                pass


@pytest.fixture(autouse=True)
def _reset_db_conn_state() -> Generator[None]:
    """Preserve db_conn module-level shutdown state across tests.

    set_shutdown_flag() is set by lifespan() shutdown and
    run_with_db_lock()'s fail-fast guard reads it; preserving the flag and
    the active-user counter prevents test-to-test leakage that would make
    later tests refuse DB work (scripts/eventbus/db_conn.py).
    """
    from eventbus import db_conn

    original_flag = db_conn._shutting_down
    original_users = db_conn._active_db_users
    yield
    db_conn._shutting_down = original_flag
    db_conn._active_db_users = original_users


@pytest.fixture(autouse=True)
def _reset_auth_state(monkeypatch: pytest.MonkeyPatch) -> Generator[None]:
    """Preserve auth module-level state across tests.

    _TOKEN_PRINCIPAL_MAP is populated at runtime by
    attach_auth_middleware() or config loading; preserving it prevents
    test-to-test leakage while keeping the map intact for the duration
    of each test run.
    """
    from eventbus import auth

    original_map = getattr(auth, "_TOKEN_PRINCIPAL_MAP", {})
    yield
    monkeypatch.setattr(auth, "_TOKEN_PRINCIPAL_MAP", original_map)
