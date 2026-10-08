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
    async def test_startup_poll_succeeds_with_correct_token(
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
