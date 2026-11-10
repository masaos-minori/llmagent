"""tests/eventbus/test_eventbus_route_registry.py

Registered-route and negative-authorization tests through the production app.

The registry tests lock one registered handler per (method, path) and one
definition per registered route function name. The authorization tests cover the
role-gated routes that had no production-app 401/403 test. Cases already locked
elsewhere are not repeated:

- /health and /publish: ``test_eventbus_auth.py::TestProductionRouteWiring``
- subscribe, ack, nack grants (403 without a grant for the consumer_id or topic):
  ``test_eventbus_consumer_authorization.py``
- /admin/topics/authorization 401/403: ``test_admin_topics_authorization.py``
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

import pytest
from eventbus_helpers import eventbus_auth_headers, make_eventbus_client
from fastapi.routing import APIRoute

EXPECTED_ROUTES = {
    ("GET", "/health"),
    ("POST", "/publish"),
    ("GET", "/replay"),
    ("GET", "/subscribe"),
    ("GET", "/dlq"),
    ("POST", "/dlq/{event_id}/requeue"),
    ("POST", "/events/{event_id}/ack"),
    ("POST", "/nack"),
    ("POST", "/admin/topics/authorization"),
}

_EVENTBUS_DIR = Path(__file__).resolve().parents[2] / "scripts" / "eventbus"


def _api_routes() -> list[APIRoute]:
    from eventbus import app as eb_app

    return [r for r in eb_app.app.routes if isinstance(r, APIRoute)]


def test_every_method_path_has_one_registered_handler() -> None:
    pairs = [(m, r.path) for r in _api_routes() for m in sorted(r.methods or ())]
    duplicated = sorted({p for p in pairs if pairs.count(p) > 1})
    assert duplicated == []
    assert set(pairs) == EXPECTED_ROUTES


def test_registered_route_function_names_are_unique_in_package() -> None:
    definitions: dict[str, list[str]] = {}
    for path in sorted(_EVENTBUS_DIR.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                definitions.setdefault(node.name, []).append(path.name)
    shared = {
        r.endpoint.__name__: definitions.get(r.endpoint.__name__, [])
        for r in _api_routes()
        if len(definitions.get(r.endpoint.__name__, [])) != 1
    }
    assert shared == {}


OPERATOR_ROUTES = [
    ("GET", "/replay"),
    ("GET", "/dlq"),
    ("POST", "/dlq/missing-id/requeue"),
]

CONSUMER_ROUTES = [
    ("POST", "/events/e1/ack?consumer_id=c1"),
    ("POST", "/nack?event_id=e1&consumer_id=c1&idempotency_key=k"),
]


def _call(client: Any, method: str, url: str, headers: dict[str, str] | None) -> Any:
    client.headers.pop("Authorization", None)
    return client.request(method, url, headers=headers or {})


@pytest.mark.parametrize(("method", "url"), OPERATOR_ROUTES)
def test_operator_route_rejects_missing_unknown_and_wrong_role(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, method: str, url: str
) -> None:
    with make_eventbus_client(tmp_path, monkeypatch) as c:
        assert _call(c, method, url, None).status_code == 401
        unknown = {"Authorization": "Bearer unknown"}
        assert _call(c, method, url, unknown).status_code == 401
        publisher = eventbus_auth_headers("publisher")
        assert _call(c, method, url, publisher).status_code == 403
        # The right role passes the gate (the route's own outcome may differ).
        operator = eventbus_auth_headers("operator")
        assert _call(c, method, url, operator).status_code not in (401, 403)


@pytest.mark.parametrize(("method", "url"), CONSUMER_ROUTES)
def test_consumer_route_rejects_missing_token_and_wrong_role(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, method: str, url: str
) -> None:
    with make_eventbus_client(tmp_path, monkeypatch) as c:
        assert _call(c, method, url, None).status_code == 401
        unknown = {"Authorization": "Bearer unknown"}
        assert _call(c, method, url, unknown).status_code == 401
        publisher = eventbus_auth_headers("publisher")
        assert _call(c, method, url, publisher).status_code == 403
