"""tests/eventbus/conftest.py — Shared fixtures for Event Bus tests."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

# Precedent: tests/mcp_servers/mdq/conftest.py::_reset_mdq_state_for_testing()
# Precedent: tests/conftest.py::_reset_tool_registry() — session-scoped reset pattern


@pytest.fixture(autouse=True)
def _reset_auth_state(monkeypatch: pytest.MonkeyPatch) -> None:
    """Reset auth module-level state before each test.

    _TOKEN_CONSUMER_MAP and _TOKEN_TOPIC_MAP are populated at runtime by
    attach_auth_middleware() or config loading; without resetting them per
    test, a previous test's identity mappings leak into unrelated tests
    depending on collection order, causing false positives/negatives in
    authorization assertions.
    """
    from eventbus import auth

    original_map = getattr(auth, "_TOKEN_CONSUMER_MAP", {})
    original_topic_map = getattr(auth, "_TOKEN_TOPIC_MAP", {})
    monkeypatch.setattr(auth, "_TOKEN_CONSUMER_MAP", {})
    monkeypatch.setattr(auth, "_TOKEN_TOPIC_MAP", {})
    yield
    monkeypatch.setattr(auth, "_TOKEN_CONSUMER_MAP", original_map)
    monkeypatch.setattr(auth, "_TOKEN_TOPIC_MAP", original_topic_map)
