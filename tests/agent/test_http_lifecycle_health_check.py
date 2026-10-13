"""Regression tests for HTTP health-poll client lifecycle.

Covers the documented intentional behavior of
``HttpServerLifecycleManager._health_poll_until_ready()`` in
``scripts/agent/http_lifecycle.py``:

- REQ-002: the ``httpx.AsyncClient`` context is always exited, so no connection
  leaks remain on the failure / timeout path.
- REQ-003 (corrected): each health-poll session instantiates a fresh
  ``AsyncClient`` rather than reusing one. This matches the selected Option B
  (document-as-intentional) trade-off in plan
  ``plans/done/20261004-182819_plan.md``, which prioritizes correctness (no
  leaked connections) over connection pooling. Note the plan's literal
  "connection reuse across retries" wording contradicts Option B, so the
  verifiable intent here is *new client per session*, i.e. the documented
  behavior.

These tests live in a dedicated file (not ``tests/agent/test_http_lifecycle.py``)
because that filename is already owned by an unrelated getpgid-failure test suite.
"""

from __future__ import annotations

from types import TracebackType
from unittest.mock import AsyncMock, Mock, patch

import agent.http_lifecycle as hl_module
import pytest
from agent.http_lifecycle import HttpServerLifecycleManager, HttpStartupError
from shared.mcp_config import McpServerConfig, StartupMode, TransportType
from starlette.requests import Request


def _make_cfg(**overrides: object) -> McpServerConfig:
    defaults = dict(
        transport=TransportType.HTTP,
        url="http://localhost:8080",
        startup_mode=StartupMode.SUBPROCESS,
        startup_timeout_sec=30,
        cmd=["node", "/fake/server.js"],
        auth_token="test-token",
    )
    defaults.update(overrides)
    return McpServerConfig(**defaults)  # type: ignore[arg-type] — test helper merges arbitrary override kwargs into a typed dict; mypy cannot narrow the value types


@pytest.fixture
def mgr() -> HttpServerLifecycleManager:
    return HttpServerLifecycleManager()


class _RecordingAsyncClient:
    """Minimal stand-in for ``httpx.AsyncClient`` recording context-manager exit."""

    def __init__(self, **kwargs: object) -> None:
        self.exited = False

    async def __aenter__(self) -> _RecordingAsyncClient:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool:
        self.exited = True
        return False


class TestHealthPollClientLifecycle:
    """REQ-002 / REQ-003: AsyncClient lifecycle during health polling."""

    @pytest.mark.asyncio
    async def test_closes_client_on_timeout_no_leak(
        self, mgr: HttpServerLifecycleManager
    ) -> None:
        """REQ-002: AsyncClient context is exited even on the timeout failure path."""
        cfg = _make_cfg()
        proc = Mock(pid=1234, poll=Mock(return_value=None))
        instantiated: list[_RecordingAsyncClient] = []

        def _factory(*args: object, **kwargs: object) -> _RecordingAsyncClient:
            client = _RecordingAsyncClient(**kwargs)
            instantiated.append(client)
            return client

        with (
            patch.object(hl_module.httpx, "AsyncClient", side_effect=_factory),
            patch.object(mgr, "_cleanup_server_resources", return_value=""),
            patch.object(
                mgr._process_terminator,
                "terminate_with_timeout",
                AsyncMock(return_value=True),
            ),
            pytest.raises(HttpStartupError),
        ):
            await mgr._health_poll_until_ready(
                "test-server", cfg, proc, deadline=0.0, shutdown_event=None
            )

        assert instantiated, "AsyncClient was never instantiated"
        for client in instantiated:
            assert client.exited, (
                "AsyncClient context not exited — possible connection leak"
            )

    @pytest.mark.asyncio
    async def test_instantiates_new_client_per_call(
        self, mgr: HttpServerLifecycleManager
    ) -> None:
        """Documented behavior (REQ-003): each call creates a fresh AsyncClient."""
        cfg = _make_cfg()
        proc = Mock(pid=1234, poll=Mock(return_value=None))
        instantiated: list[_RecordingAsyncClient] = []

        def _factory(*args: object, **kwargs: object) -> _RecordingAsyncClient:
            client = _RecordingAsyncClient(**kwargs)
            instantiated.append(client)
            return client

        with patch.object(hl_module.httpx, "AsyncClient", side_effect=_factory):
            with (
                patch.object(mgr, "_cleanup_server_resources", return_value=""),
                patch.object(
                    mgr._process_terminator,
                    "terminate_with_timeout",
                    AsyncMock(return_value=True),
                ),
            ):
                for server_key in ("test-server", "test-server-2"):
                    with pytest.raises(HttpStartupError):
                        await mgr._health_poll_until_ready(
                            server_key,
                            cfg,
                            proc,
                            deadline=0.0,
                            shutdown_event=None,
                        )

        assert len(instantiated) == 2


def _auth_required_route(token: str):
    """respx side effect: 200 only when the Bearer token matches, else 401."""
    import httpx

    def _handler(request: httpx.Request) -> httpx.Response:
        if request.headers.get("Authorization") == f"Bearer {token}":
            return httpx.Response(200, json={"status": "ok"})
        return httpx.Response(401, json={"error": "Unauthorized"})

    return _handler


class TestHealthProbesSendBearerToken:
    """REQ-002 / REQ-005: startup poll and liveness check authenticate."""

    @pytest.mark.asyncio
    async def test_liveness_check_passes_with_correct_token(
        self, mgr: HttpServerLifecycleManager
    ) -> None:
        import respx

        cfg = _make_cfg(auth_token="s3cret")
        with (
            respx.mock as router,
            patch.object(mgr, "verify_running", return_value=True),
        ):
            router.get("http://localhost:8080/health").mock(
                side_effect=_auth_required_route("s3cret")
            )
            assert await mgr.verify_running_async("srv", cfg) is True

    @pytest.mark.asyncio
    async def test_liveness_check_fails_with_wrong_token(
        self, mgr: HttpServerLifecycleManager
    ) -> None:
        import respx

        cfg = _make_cfg(auth_token="wrong")
        with (
            respx.mock as router,
            patch.object(mgr, "verify_running", return_value=True),
        ):
            router.get("http://localhost:8080/health").mock(
                side_effect=_auth_required_route("s3cret")
            )
            assert await mgr.verify_running_async("srv", cfg) is False

    @pytest.mark.asyncio
    async def test_health_poll_succeeds_with_correct_token(
        self, mgr: HttpServerLifecycleManager
    ) -> None:
        import time

        import respx

        cfg = _make_cfg(auth_token="s3cret")
        proc = Mock(pid=1234, poll=Mock(return_value=None))
        with respx.mock as router:
            route = router.get("http://localhost:8080/health").mock(
                side_effect=_auth_required_route("s3cret")
            )
            await mgr._health_poll_until_ready(
                "srv", cfg, proc, deadline=time.monotonic() + 5, shutdown_event=None
            )
        assert route.called
        assert route.calls[0].request.headers["Authorization"] == "Bearer s3cret"


def _loopback_health_app(
    server_token: str, *, exempt_health_on_loopback: bool
) -> tuple[object, list[str]]:
    """Minimal app guarded by the real auth middleware, recording the header it sees."""
    from fastapi import FastAPI
    from mcp_servers.server import attach_auth_middleware

    seen: list[str] = []
    app = FastAPI()
    # Pass the keyword only when enabling it, so the default (off) cases run the
    # unchanged call shape of every other server.
    extra = {"exempt_health_on_loopback": True} if exempt_health_on_loopback else {}
    attach_auth_middleware(
        app,
        server_token,
        **extra,
    )

    @app.get("/health")
    async def _health(request: Request) -> dict[str, str]:
        seen.append(request.headers.get("Authorization", ""))
        return {"status": "ok"}

    return app, seen


def _asgi_client_factory(app: object):
    """AsyncClient replacement: a real client over an in-process (loopback) ASGI transport."""
    import httpx

    # Captured before the test patches httpx.AsyncClient, which is the same module
    # attribute the factory would otherwise resolve.
    real_client = httpx.AsyncClient

    def _factory(*args: object, **kwargs: object) -> httpx.AsyncClient:
        return real_client(transport=httpx.ASGITransport(app=app), **kwargs)

    return _factory


class TestStartupPollWithDistinctServerToken:
    """REQ-001 / REQ-003: a server whose middleware expects a token other than the
    main auth_token (web-search with a distinct browser token)."""

    @pytest.mark.asyncio
    async def test_poll_succeeds_when_switch_on_and_tokens_differ(
        self, mgr: HttpServerLifecycleManager
    ) -> None:
        import time

        app, seen = _loopback_health_app(
            "browser-secret", exempt_health_on_loopback=True
        )
        cfg = _make_cfg(auth_token="main-secret")
        proc = Mock(pid=1234, poll=Mock(return_value=None))
        with (
            patch.object(hl_module.httpx, "AsyncClient", _asgi_client_factory(app)),
            patch.object(hl_module, "HEALTH_POLL_INTERVAL_SEC", 0.01),
        ):
            await mgr._health_poll_until_ready(
                "web-search",
                cfg,
                proc,
                deadline=time.monotonic() + 5,
                shutdown_event=None,
            )
        assert seen == ["Bearer main-secret"]

    @pytest.mark.asyncio
    async def test_poll_fails_when_switch_off_and_tokens_differ(
        self, mgr: HttpServerLifecycleManager
    ) -> None:
        import time

        app, seen = _loopback_health_app(
            "browser-secret", exempt_health_on_loopback=False
        )
        cfg = _make_cfg(auth_token="main-secret")
        proc = Mock(pid=1234, poll=Mock(return_value=None))
        with (
            patch.object(hl_module.httpx, "AsyncClient", _asgi_client_factory(app)),
            patch.object(hl_module, "HEALTH_POLL_INTERVAL_SEC", 0.01),
            patch.object(mgr, "_cleanup_server_resources", return_value=""),
            patch.object(
                mgr._process_terminator,
                "terminate_with_timeout",
                AsyncMock(return_value=True),
            ),
            pytest.raises(HttpStartupError),
        ):
            await mgr._health_poll_until_ready(
                "web-search",
                cfg,
                proc,
                deadline=time.monotonic() + 0.3,
                shutdown_event=None,
            )
        assert seen == []

    @pytest.mark.asyncio
    async def test_poll_succeeds_when_tokens_match_and_switch_off(
        self, mgr: HttpServerLifecycleManager
    ) -> None:
        import time

        app, seen = _loopback_health_app("main-secret", exempt_health_on_loopback=False)
        cfg = _make_cfg(auth_token="main-secret")
        proc = Mock(pid=1234, poll=Mock(return_value=None))
        with (
            patch.object(hl_module.httpx, "AsyncClient", _asgi_client_factory(app)),
            patch.object(hl_module, "HEALTH_POLL_INTERVAL_SEC", 0.01),
        ):
            await mgr._health_poll_until_ready(
                "other-server",
                cfg,
                proc,
                deadline=time.monotonic() + 5,
                shutdown_event=None,
            )
        assert seen == ["Bearer main-secret"]
