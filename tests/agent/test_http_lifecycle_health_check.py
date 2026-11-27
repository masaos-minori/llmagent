"""Regression tests for HTTP health-poll client lifecycle.

Covers the documented intentional behavior of the readiness poll loop
``HealthChecker.poll_until_ready()`` in ``scripts/agent/http_lifecycle_health_checker.py``,
reached through ``HttpServerLifecycleManager._health_poll_until_ready()`` in
``scripts/agent/http_lifecycle.py``:

- REQ-002: the ``httpx.AsyncClient`` context is always exited, so no connection
  leaks remain on the failure / timeout path. Each request timeout is also capped
  by the time left to the deadline, and no request starts once it has passed.
- REQ-001: the request timeout is the server's effective ``health_timeout``, not a
  global constant.
- REQ-003 (corrected): each health-poll session instantiates a fresh
  ``AsyncClient`` rather than reusing one. This matches the selected Option B
  (document-as-intentional) trade-off in plan
  ``plans/done/20261004-182819_plan.md``, which prioritizes correctness (no
  leaked connections) over connection pooling. Note the plan's literal
  "connection reuse across retries" wording contradicts Option B, so the
  verifiable intent here is *new client per session*, i.e. the documented
  behavior.
- REQ-005: readiness is proven by the parsed report through the shared contract;
  `liveness` alone is not proof and a legacy body falls back to `ready`. The
  `required_capability` is resolved by the caller from the tool catalog.

These tests live in a dedicated file (not ``tests/agent/test_http_lifecycle.py``)
because that filename is already owned by an unrelated getpgid-failure test suite.
"""

from __future__ import annotations

from types import SimpleNamespace, TracebackType
from unittest.mock import AsyncMock, Mock, patch

import agent.http_lifecycle as hl_module
import agent.http_lifecycle_health_checker as hc_module
import httpx
import pytest
from agent.http_lifecycle import HttpServerLifecycleManager, HttpStartupError
from agent.http_lifecycle_errors import TerminationOutcome
from agent.http_lifecycle_health_checker import HealthChecker
from shared.mcp_config import McpServerConfig, StartupMode, TransportType
from shared.mcp_health_contract import (
    HEALTH_SCHEMA_VERSION,
    LEGACY_HEALTH_SCHEMA_VERSION,
)
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


def _assert_no_shutdown_budget(terminator: AsyncMock) -> None:
    """State that every terminate call in this case carried no shutdown budget.

    The readiness poll is not part of a shutdown sequence: it owns its own window and
    must not be coupled to a deadline it does not hold (REQ-010).
    """
    assert terminator.await_count >= 1, "expected a terminate_with_timeout() call"
    for call in terminator.await_args_list:
        assert call.kwargs.get("budget") is None


class _RecordingAsyncClient:
    """Minimal stand-in for ``httpx.AsyncClient`` recording context-manager exit."""

    def __init__(self, **kwargs: object) -> None:
        self.kwargs = kwargs
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


class _FakeClock:
    """Deterministic stand-in for ``time.monotonic`` (T-02)."""

    def __init__(self, start: float = 0.0) -> None:
        self.now = start

    def monotonic(self) -> float:
        return self.now

    def advance(self, delta: float) -> None:
        self.now += delta


class _RecordingTimeoutClient(_RecordingAsyncClient):
    """AsyncClient stand-in recording the client default and each request timeout."""

    def __init__(
        self,
        recorded: list[object],
        responses: list[httpx.Response],
        **kwargs: object,
    ) -> None:
        super().__init__(**kwargs)
        self.recorded = recorded
        self.responses = responses

    async def get(self, url: str, *, timeout: object = None) -> httpx.Response:
        self.recorded.append(timeout)
        if self.responses:
            return self.responses.pop(0)
        # A live but unproven server: the poll keeps running until the deadline.
        return _json_response(503, {"liveness": True})


def _json_response(status: int, body: object) -> httpx.Response:
    return httpx.Response(
        status, headers={"content-type": "application/json"}, json=body
    )


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
            patch.object(hc_module.httpx, "AsyncClient", side_effect=_factory),
            patch.object(mgr, "_cleanup_server_resources", return_value=""),
            patch.object(
                mgr._process_terminator,
                "terminate_with_timeout",
                AsyncMock(return_value=TerminationOutcome.EXITED),
            ) as term,
            pytest.raises(HttpStartupError),
        ):
            await mgr._health_poll_until_ready(
                "test-server", cfg, proc, deadline=0.0, shutdown_event=None
            )

        _assert_no_shutdown_budget(term)
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

        with patch.object(hc_module.httpx, "AsyncClient", side_effect=_factory):
            with (
                patch.object(mgr, "_cleanup_server_resources", return_value=""),
                patch.object(
                    mgr._process_terminator,
                    "terminate_with_timeout",
                    AsyncMock(return_value=TerminationOutcome.EXITED),
                ) as term,
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
        _assert_no_shutdown_budget(term)


def _auth_required_route(token: str):
    """respx side effect: 200 only when the Bearer token matches, else 401."""
    import httpx

    def _handler(request: httpx.Request) -> httpx.Response:
        if request.headers.get("Authorization") == f"Bearer {token}":
            # A legacy body: readiness proof is the `ready` flag (D-6).
            return httpx.Response(200, json={"status": "ok", "ready": True})
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


def _loopback_health_app(server_token: str) -> tuple[object, list[str]]:
    """Minimal app guarded by the real auth middleware, recording the header it sees."""
    from fastapi import FastAPI
    from mcp_servers.server import attach_auth_middleware

    seen: list[str] = []
    app = FastAPI()
    attach_auth_middleware(app, server_token)

    @app.get("/health")
    async def _health(request: Request) -> dict[str, object]:
        seen.append(request.headers.get("Authorization", ""))
        # A legacy body: readiness proof is the `ready` flag (D-6).
        return {"status": "ok", "ready": True}

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
    async def test_poll_fails_when_token_differs(
        self, mgr: HttpServerLifecycleManager
    ) -> None:
        import time

        app, seen = _loopback_health_app("browser-secret")
        cfg = _make_cfg(auth_token="main-secret")
        proc = Mock(pid=1234, poll=Mock(return_value=None))
        with (
            patch.object(hc_module.httpx, "AsyncClient", _asgi_client_factory(app)),
            patch.object(hl_module, "HEALTH_POLL_INTERVAL_SEC", 0.01),
            patch.object(mgr, "_cleanup_server_resources", return_value=""),
            patch.object(
                mgr._process_terminator,
                "terminate_with_timeout",
                AsyncMock(return_value=TerminationOutcome.EXITED),
            ) as term,
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
        _assert_no_shutdown_budget(term)

    @pytest.mark.asyncio
    async def test_poll_succeeds_when_tokens_match(
        self, mgr: HttpServerLifecycleManager
    ) -> None:
        import time

        app, seen = _loopback_health_app("main-secret")
        cfg = _make_cfg(auth_token="main-secret")
        proc = Mock(pid=1234, poll=Mock(return_value=None))
        with (
            patch.object(hc_module.httpx, "AsyncClient", _asgi_client_factory(app)),
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


class TestReportBasedReadiness:
    """REQ-005: readiness is proven by the parsed report, not by the status code.

    The replaced `is_degraded_but_live` predicate accepted `liveness` alone, which
    started a server that could not prove its required capability. Readiness now
    requires the catalog `required_capability` to be `ok`; a body with no capability
    block falls back to its `ready` flag (D-6). An unparseable body is not proof and
    keeps the poll running rather than raising.
    """

    def test_parse_report_returns_none_for_unparseable_bodies(self) -> None:
        """Non-JSON, non-object, and empty bodies are not proof and do not raise."""
        bodies = [
            httpx.Response(
                503, headers={"content-type": "text/plain"}, text="unavailable"
            ),
            _json_response(503, [1, 2]),
            _json_response(503, "unavailable"),
            _json_response(503, 42),
            httpx.Response(
                503, headers={"content-type": "application/json"}, content=b"null"
            ),
            httpx.Response(503, headers={"content-type": "application/json"}),
            httpx.Response(
                503, headers={"content-type": "application/json"}, content=b"{nope"
            ),
        ]
        for resp in bodies:
            assert HealthChecker.parse_report(resp) is None

    def test_parse_report_rejects_contract_violations(self) -> None:
        """A wrong-typed field or an unknown capability state is not proof."""
        assert (
            HealthChecker.parse_report(_json_response(503, {"liveness": "true"}))
            is None
        )
        assert (
            HealthChecker.parse_report(
                _json_response(503, {"capabilities": {"github.api": "broken"}})
            )
            is None
        )

    def test_liveness_only_body_is_not_readiness_proof(self) -> None:
        """A live server with no capability block does not prove the required capability."""
        report = HealthChecker.parse_report(_json_response(503, {"liveness": True}))
        assert report is not None
        assert report.is_legacy
        assert HealthChecker.is_ready(report, "github.api") is False

    def test_required_capability_ok_proves_readiness(self) -> None:
        """The same live body with the required capability `ok` is proof (AC-05)."""
        report = HealthChecker.parse_report(
            _json_response(
                503,
                {
                    "health_schema_version": HEALTH_SCHEMA_VERSION,
                    "liveness": True,
                    "capabilities": {"github.api": "ok"},
                },
            )
        )
        assert report is not None
        assert report.health_schema_version == HEALTH_SCHEMA_VERSION
        assert not report.is_legacy
        assert HealthChecker.is_ready(report, "github.api") is True

    def test_legacy_body_falls_back_to_ready(self) -> None:
        """A body with no capability block is read through `ready` (D-6)."""
        report = HealthChecker.parse_report(_json_response(200, {"ready": True}))
        assert report is not None
        assert report.is_legacy
        assert report.health_schema_version == LEGACY_HEALTH_SCHEMA_VERSION
        assert HealthChecker.is_ready(report, None) is True
        # A legacy body has no capability proof, so `ready` is the only proof it can give.
        assert HealthChecker.is_ready(report, "github.api") is True
        unproven = HealthChecker.parse_report(_json_response(503, {"liveness": True}))
        assert unproven is not None
        assert HealthChecker.is_ready(unproven, "github.api") is False

    @pytest.mark.asyncio
    async def test_liveness_only_503_does_not_end_the_poll(self, mgr) -> None:
        """A live but unproven server ends the poll in failure, not readiness."""
        import time

        import respx

        cfg = _make_cfg()
        proc = Mock(pid=1234, poll=Mock(return_value=None))
        with (
            respx.mock as router,
            patch.object(hl_module, "HEALTH_POLL_INTERVAL_SEC", 0.01),
            patch.object(mgr, "_cleanup_server_resources", return_value=""),
            patch.object(
                mgr._process_terminator,
                "terminate_with_timeout",
                AsyncMock(return_value=TerminationOutcome.EXITED),
            ) as term,
            pytest.raises(HttpStartupError),
        ):
            router.get("http://localhost:8080/health").mock(
                return_value=_json_response(503, {"liveness": True})
            )
            await mgr._health_poll_until_ready(
                "srv", cfg, proc, deadline=time.monotonic() + 0.05, shutdown_event=None
            )

        _assert_no_shutdown_budget(term)

    @pytest.mark.asyncio
    async def test_required_capability_ok_503_ends_the_poll(self, mgr) -> None:
        """The proven capability ends the poll ready and keeps the process alive."""
        import time

        import respx

        cfg = _make_cfg()
        proc = Mock(pid=1234, poll=Mock(return_value=None))
        with (
            respx.mock as router,
            patch.object(
                mgr, "_resolve_required_capability", return_value="github.api"
            ),
            patch.object(mgr, "_cleanup_server_resources", return_value=""),
            patch.object(
                mgr._process_terminator,
                "terminate_with_timeout",
                AsyncMock(return_value=TerminationOutcome.EXITED),
            ),
        ):
            router.get("http://localhost:8080/health").mock(
                return_value=_json_response(
                    503, {"liveness": True, "capabilities": {"github.api": "ok"}}
                )
            )
            await mgr._health_poll_until_ready(
                "srv", cfg, proc, deadline=time.monotonic() + 5, shutdown_event=None
            )
            mgr._process_terminator.terminate_with_timeout.assert_not_called()

    @pytest.mark.asyncio
    async def test_non_object_503_then_ready_body_ends_the_poll(self, mgr) -> None:
        """An unparseable body keeps the poll alive; a later proof ends it ready."""
        import time

        import respx

        cfg = _make_cfg()
        proc = Mock(pid=1234, poll=Mock(return_value=None))
        with (
            respx.mock as router,
            patch.object(hl_module, "HEALTH_POLL_INTERVAL_SEC", 0.01),
            patch.object(mgr, "_cleanup_server_resources", return_value=""),
            patch.object(
                mgr._process_terminator,
                "terminate_with_timeout",
                AsyncMock(return_value=TerminationOutcome.EXITED),
            ),
        ):
            router.get("http://localhost:8080/health").mock(
                side_effect=[
                    _json_response(503, ["degraded"]),
                    _json_response(200, {"status": "ok", "ready": True}),
                ]
            )
            await mgr._health_poll_until_ready(
                "srv", cfg, proc, deadline=time.monotonic() + 5, shutdown_event=None
            )
            mgr._process_terminator.terminate_with_timeout.assert_not_called()

    @pytest.mark.asyncio
    async def test_permanent_non_object_503_ends_in_timeout(self, mgr) -> None:
        """A permanent non-object body ends in HttpStartupError, not AttributeError."""
        import time

        import respx

        cfg = _make_cfg()
        proc = Mock(pid=1234, poll=Mock(return_value=None))
        with (
            respx.mock as router,
            patch.object(hl_module, "HEALTH_POLL_INTERVAL_SEC", 0.01),
            patch.object(mgr, "_cleanup_server_resources", return_value=""),
            patch.object(
                mgr._process_terminator,
                "terminate_with_timeout",
                AsyncMock(return_value=TerminationOutcome.EXITED),
            ) as term,
            pytest.raises(HttpStartupError),
        ):
            router.get("http://localhost:8080/health").mock(
                return_value=_json_response(503, ["degraded"])
            )
            await mgr._health_poll_until_ready(
                "srv", cfg, proc, deadline=time.monotonic() + 0.05, shutdown_event=None
            )

        _assert_no_shutdown_budget(term)


class TestCallerResolvesRequiredCapability:
    """REQ-005: the caller resolves the catalog capability; the checker does not read it."""

    def test_catalog_entry_reaches_the_poll(self, mgr) -> None:
        catalog = {"server": {"github": {"required_capability": "github.operations"}}}
        with patch.object(hl_module, "load_tool_catalog", return_value=catalog):
            assert mgr._resolve_required_capability("github") == "github.operations"

    def test_server_without_an_entry_resolves_to_none(self, mgr) -> None:
        with patch.object(hl_module, "load_tool_catalog", return_value={"server": {}}):
            assert mgr._resolve_required_capability("srv") is None

    def test_missing_catalog_resolves_to_none_with_a_warning(self, mgr, caplog) -> None:
        """The fail-closed FATAL stays at discovery; here the poll keeps the legacy fallback."""
        with patch.object(
            hl_module, "load_tool_catalog", side_effect=FileNotFoundError("no catalog")
        ):
            assert mgr._resolve_required_capability("srv") is None
        assert "tool catalog unavailable" in caplog.text


class TestPerServerTimeoutAndDeadlineCap:
    """REQ-001 / REQ-002: the effective per-server timeout and the remaining-deadline cap."""

    @pytest.mark.asyncio
    async def test_poll_uses_the_servers_effective_timeout(self, mgr) -> None:
        """T-01: a distinct non-default value reaches the startup poll."""
        import time

        import httpx

        cfg = _make_cfg(health_timeout=7.5)
        proc = Mock(pid=1234, poll=Mock(return_value=None))
        recorded: list[object] = []
        clients: list[_RecordingTimeoutClient] = []

        def _factory(*args: object, **kwargs: object) -> _RecordingTimeoutClient:
            client = _RecordingTimeoutClient(
                recorded, [_json_response(200, {"ready": True})], **kwargs
            )
            clients.append(client)
            return client

        with (
            patch.object(hc_module.httpx, "AsyncClient", side_effect=_factory),
            patch.object(mgr, "_cleanup_server_resources", return_value=""),
        ):
            await mgr._health_poll_until_ready(
                "srv", cfg, proc, deadline=time.monotonic() + 100, shutdown_event=None
            )

        assert clients[0].kwargs["timeout"] == httpx.Timeout(timeout=7.5)
        # Plenty of time remains, so the cap does not shrink the effective timeout.
        assert recorded == [httpx.Timeout(timeout=7.5)]
        assert clients[0].exited

    @pytest.mark.asyncio
    async def test_periodic_check_uses_the_effective_timeout(
        self, mgr: HttpServerLifecycleManager
    ) -> None:
        """T-01: the periodic check no longer relies on the checker default."""

        cfg = _make_cfg(health_timeout=12.0)
        clients: list[_RecordingAsyncClient] = []

        def _factory(*args: object, **kwargs: object) -> _RecordingAsyncClient:
            client = _RecordingAsyncClient(**kwargs)
            clients.append(client)
            return client

        with (
            patch.object(hc_module.httpx, "AsyncClient", side_effect=_factory),
            patch.object(mgr, "verify_running", return_value=True),
        ):
            await mgr.verify_running_async("srv", cfg)

        assert clients[0].kwargs["timeout"] == 12.0
        # REQ-003: the header comes from auth_headers(), not from a second path.
        assert clients[0].kwargs["headers"] == cfg.auth_headers()

    @pytest.mark.asyncio
    async def test_request_timeout_is_capped_by_the_remaining_deadline(
        self, mgr: HttpServerLifecycleManager
    ) -> None:
        """T-02: each request timeout is min(effective, remaining); none starts past the deadline."""

        clock = _FakeClock(0.0)
        cfg = _make_cfg(health_timeout=7.5)
        proc = Mock(pid=1234, poll=Mock(return_value=None))
        recorded: list[object] = []
        client = _RecordingTimeoutClient(recorded, [])

        async def _advance(delay: float, shutdown_event: object) -> bool:
            clock.advance(delay)
            return False

        with (
            patch.object(hc_module, "time", SimpleNamespace(monotonic=clock.monotonic)),
            patch.object(hc_module, "_interruptible_poll_sleep", _advance),
            patch.object(hc_module.httpx, "AsyncClient", lambda *a, **k: client),
            patch.object(hl_module, "HEALTH_POLL_INTERVAL_SEC", 0.01),
            patch.object(mgr, "_cleanup_server_resources", return_value=""),
            patch.object(
                mgr._process_terminator,
                "terminate_with_timeout",
                AsyncMock(return_value=TerminationOutcome.EXITED),
            ) as term,
            pytest.raises(HttpStartupError),
        ):
            await mgr._health_poll_until_ready(
                "srv", cfg, proc, deadline=clock.now + 0.02, shutdown_event=None
            )

        assert [t.read for t in recorded] == [
            pytest.approx(0.02),
            pytest.approx(0.01),
        ]
        # The poll stopped at the deadline: no request was issued after it.
        assert clock.now == pytest.approx(0.02)
        assert client.exited
        call = term.await_args
        assert call is not None
        assert call.kwargs["timeout"] == hl_module.TERMINATE_TIMEOUT_SEC


class TestSingleAuthPath:
    """REQ-003: `auth_headers()` is the only header path and the token is never logged."""

    @pytest.mark.asyncio
    async def test_no_header_without_a_token(
        self, mgr: HttpServerLifecycleManager
    ) -> None:
        # A server with no token is a disabled one (startup_mode=NONE): validation
        # requires a token for any server that actually starts.
        cfg = _make_cfg(
            health_timeout=6.0, auth_token="", startup_mode=StartupMode.NONE
        )
        clients: list[_RecordingAsyncClient] = []

        def _factory(*args: object, **kwargs: object) -> _RecordingAsyncClient:
            client = _RecordingAsyncClient(**kwargs)
            clients.append(client)
            return client

        with (
            patch.object(hc_module.httpx, "AsyncClient", side_effect=_factory),
            patch.object(mgr, "verify_running", return_value=True),
        ):
            await mgr.verify_running_async("srv", cfg)

        assert clients[0].kwargs["headers"] == {}
        assert clients[0].kwargs["timeout"] == 6.0

    @pytest.mark.asyncio
    async def test_header_comes_from_auth_headers(
        self, mgr: HttpServerLifecycleManager
    ) -> None:
        """The checker owns the header; the periodic call site no longer passes one."""

        cfg = _make_cfg(auth_token="s3cret")
        clients: list[_RecordingAsyncClient] = []

        def _factory(*args: object, **kwargs: object) -> _RecordingAsyncClient:
            client = _RecordingAsyncClient(**kwargs)
            clients.append(client)
            return client

        with (
            patch.object(hc_module.httpx, "AsyncClient", side_effect=_factory),
            patch.object(mgr, "verify_running", return_value=True),
        ):
            await mgr.verify_running_async("srv", cfg)

        assert clients[0].kwargs["headers"] == {"Authorization": "Bearer s3cret"}

    @pytest.mark.asyncio
    async def test_failing_probe_logs_no_token(
        self, mgr: HttpServerLifecycleManager, caplog
    ) -> None:
        """T-03: a failing health probe logs the URL and the error, never the token."""
        import logging

        caplog.set_level(logging.DEBUG)
        cfg = _make_cfg(auth_token="s3cret-do-not-log")

        class _FailingClient(_RecordingAsyncClient):
            async def get(self, url: str, *, timeout: object = None) -> httpx.Response:
                raise httpx.ConnectError("connection refused")

        with (
            patch.object(
                hc_module.httpx, "AsyncClient", lambda *a, **k: _FailingClient(**k)
            ),
            patch.object(mgr, "verify_running", return_value=True),
        ):
            assert await mgr.verify_running_async("srv", cfg) is False

        assert "s3cret-do-not-log" not in caplog.text
        assert "http://localhost:8080/health" in caplog.text

    @pytest.mark.asyncio
    async def test_failing_probe_logs_redacted_url(
        self, mgr: HttpServerLifecycleManager, caplog
    ) -> None:
        """REQ-003 (AC-2): the logged URL carries no userinfo, query, or fragment,
        while the request itself still uses the configured endpoint."""
        import logging

        caplog.set_level(logging.DEBUG)
        cfg = _make_cfg(auth_token="s3cret-do-not-log")
        raw_url = "https://admin:s3cr3tpw@db.example.com:8080/health?token=abc#frag"
        requested: list[str] = []

        class _FailingClient(_RecordingAsyncClient):
            async def get(self, url: str, *, timeout: object = None) -> httpx.Response:
                requested.append(url)
                raise httpx.ConnectError("connection refused")

        with patch.object(
            hc_module.httpx, "AsyncClient", lambda *a, **k: _FailingClient(**k)
        ):
            assert (
                await HealthChecker.verify_running_async("srv", cfg, url=raw_url)
                is False
            )

        assert requested == [raw_url]
        assert "s3cr3tpw" not in caplog.text
        assert "token=abc" not in caplog.text
        assert "#frag" not in caplog.text
        assert "https://db.example.com:8080/health" in caplog.text

    @pytest.mark.asyncio
    async def test_passing_probe_logs_redacted_url(
        self, mgr: HttpServerLifecycleManager, caplog
    ) -> None:
        """REQ-003 (AC-2): the pass and status log lines use the same redacted form."""
        import logging

        caplog.set_level(logging.DEBUG)
        cfg = _make_cfg(auth_token="s3cret-do-not-log")
        raw_url = "https://admin:s3cr3tpw@db.example.com:8080/health?token=abc#frag"

        class _OkClient(_RecordingAsyncClient):
            async def get(self, url: str, *, timeout: object = None) -> httpx.Response:
                return httpx.Response(503, request=httpx.Request("GET", url))

        with patch.object(
            hc_module.httpx, "AsyncClient", lambda *a, **k: _OkClient(**k)
        ):
            assert (
                await HealthChecker.verify_running_async("srv", cfg, url=raw_url)
                is False
            )

        assert "s3cr3tpw" not in caplog.text
        assert "token=abc" not in caplog.text
        assert (
            "Health check returned status 503 at https://db.example.com:8080/health"
            in caplog.text
        )


class TestRedactBeforeTruncate:
    """REQ-003 (AC-2): the exited-early log masks before truncating, so a secret that
    crosses the truncation boundary is never cut open."""

    @pytest.mark.asyncio
    async def test_secret_spanning_truncation_boundary_is_fully_masked(
        self, mgr: HttpServerLifecycleManager, caplog
    ) -> None:
        import logging

        caplog.set_level(logging.DEBUG)
        cfg = _make_cfg()
        # "token=" ends at char 496, so the value crosses the 500-char truncation point.
        stderr_full = "x" * 496 + "token=" + "SECRETVALUE" + "y" * 100
        proc = Mock(pid=1234, poll=Mock(return_value=1))
        clock = _FakeClock(0.0)

        with (
            patch.object(hc_module, "time", SimpleNamespace(monotonic=clock.monotonic)),
            patch.object(
                hc_module.httpx,
                "AsyncClient",
                lambda *a, **k: _RecordingAsyncClient(**k),
            ),
            patch.object(mgr, "_cleanup_server_resources", return_value=stderr_full),
            patch.object(
                mgr._process_terminator,
                "terminate_with_timeout",
                AsyncMock(return_value=TerminationOutcome.EXITED),
            ),
            pytest.raises(HttpStartupError),
        ):
            await mgr._health_poll_until_ready(
                "test-server", cfg, proc, deadline=1.0, shutdown_event=None
            )

        # Masking runs before truncation, so the 500-char cut lands on the masked
        # marker, not on the secret value itself.
        assert "SECRETVALUE" not in caplog.text
        assert "SECR" not in caplog.text


class TestHealthPathTerminationWindow:
    """REQ-010: the readiness poll keeps its own window when no budget is supplied.

    This is the fallback pinned where it matters: the health path is the caller that
    never holds a shutdown budget, so a change to the shutdown windows must not move
    this one.
    """

    @pytest.mark.asyncio
    async def test_default_window_is_used_when_the_call_carries_no_budget(
        self, mgr: HttpServerLifecycleManager
    ) -> None:
        """The terminate call states the module constant, not a clamped value."""
        import time

        cfg = _make_cfg()
        proc = Mock(pid=1234, poll=Mock(return_value=None))
        term = AsyncMock(return_value=TerminationOutcome.EXITED)

        with (
            patch.object(hl_module, "HEALTH_POLL_INTERVAL_SEC", 0.01),
            patch.object(mgr, "_cleanup_server_resources", return_value=""),
            patch.object(mgr._process_terminator, "terminate_with_timeout", term),
            pytest.raises(HttpStartupError),
        ):
            await mgr._health_poll_until_ready(
                "srv", cfg, proc, deadline=time.monotonic() + 0.05, shutdown_event=None
            )

        call = term.await_args
        assert call is not None
        assert call.kwargs["timeout"] == hl_module.TERMINATE_TIMEOUT_SEC
        assert call.kwargs.get("budget") is None
