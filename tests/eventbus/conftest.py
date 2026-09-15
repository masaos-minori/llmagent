"""tests/eventbus/conftest.py — Shared fixtures for Event Bus tests."""

from __future__ import annotations

import pytest

# Precedent: tests/mcp_servers/mdq/conftest.py::_reset_mdq_state_for_testing()
# Precedent: tests/conftest.py::_reset_tool_registry() — session-scoped reset pattern


@pytest.fixture(autouse=True)
def _reset_auth_state(monkeypatch: pytest.MonkeyPatch) -> None:
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
