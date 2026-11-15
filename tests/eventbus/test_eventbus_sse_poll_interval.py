"""Tests for the SSE stream's poll interval (the tick that evaluates idle deadlines)."""

from __future__ import annotations

import ast
import time
from pathlib import Path

import pytest
from eventbus_helpers import eventbus_auth_headers, make_eventbus_client


def test_production_poll_interval_defaults_to_one_second() -> None:
    """The tests shorten the interval; the shipped default must stay 1 s."""
    import eventbus.subscribe_route as subscribe_route

    tree = ast.parse(Path(subscribe_route.__file__).read_text(encoding="utf-8"))
    defaults = [
        node.value.value
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(t, ast.Name) and t.id == "SSE_POLL_INTERVAL_SEC"
            for t in node.targets
        )
        and isinstance(node.value, ast.Constant)
    ]
    assert defaults == [1.0]


def test_idle_disconnect_follows_the_poll_interval(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A quiet stream closes on the first poll tick after the idle timeout.

    With a 1 s tick this would take at least 1 s whatever the idle timeout is.
    """
    import eventbus.subscribe_route as subscribe_route

    monkeypatch.setattr(subscribe_route, "SSE_POLL_INTERVAL_SEC", 0.05)
    with make_eventbus_client(tmp_path, monkeypatch, sse_idle_timeout=0.2) as client:
        start = time.monotonic()
        resp = client.get(
            "/subscribe?consumer_id=test-consumer&topic=test",
            timeout=5.0,
            headers=eventbus_auth_headers("consumer"),
        )
        elapsed = time.monotonic() - start

    assert resp.status_code == 200
    assert 0.15 <= elapsed < 0.9, f"closed after {elapsed:.2f}s"
