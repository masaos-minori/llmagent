"""Tests for MCP server startup health verification."""

from unittest.mock import MagicMock, patch

import httpx
import pytest
from shared.tool_registry import _reset_registry_for_testing


def setup_function():
    _reset_registry_for_testing()


# --- post-startup health verification sends the Bearer token ---


def _auth_handler(token: str):
    import httpx

    def _handler(request: httpx.Request) -> httpx.Response:
        if request.headers.get("Authorization") == f"Bearer {token}":
            # Readiness is the parsed report, not the status code (REQ-005), so the
            # accepted body must prove it through the legacy `ready` fallback (D-6).
            return httpx.Response(200, json={"status": "ok", "ready": True})
        return httpx.Response(401, json={"error": "Unauthorized"})

    return _handler


class _RecordingClient:
    """A health-check client that records the client-level timeout it was constructed with."""

    def __init__(self, kwargs: dict, response: object) -> None:
        self.kwargs = kwargs
        self.response = response

    async def __aenter__(self) -> "_RecordingClient":
        return self

    async def __aexit__(self, *exc: object) -> bool:
        return False

    async def get(self, url: str) -> object:
        return self.response


def _starter_ctx(token: str):
    from shared.mcp_config import McpServerConfig, StartupMode, TransportType

    ctx = MagicMock()
    cfg = McpServerConfig(
        transport=TransportType.HTTP,
        url="http://localhost:9999",
        startup_mode=StartupMode.SUBPROCESS,
        cmd=["python", "server.py"],
        auth_token=token,
    )
    ctx.cfg.mcp.mcp_servers = {"srv": cfg}
    ctx.services_required.tools = MagicMock()
    ctx.services_required.lifecycle = MagicMock()
    return ctx, cfg


@pytest.mark.asyncio
async def test_verify_health_passes_with_correct_token():
    import respx
    from agent.startup_mcp_starter import McpServerStarter

    ctx, _ = _starter_ctx("s3cret")
    starter = McpServerStarter(ctx, MagicMock())
    with respx.mock as router:
        route = router.get("http://localhost:9999/health").mock(
            side_effect=_auth_handler("s3cret")
        )
        await starter.verify_health()
    assert route.call_count == 1


@pytest.mark.asyncio
async def test_verify_single_health_fails_with_wrong_token():
    import respx
    from agent.startup_mcp_starter import McpServerStarter

    ctx, cfg = _starter_ctx("wrong")
    starter = McpServerStarter(ctx, MagicMock())
    with respx.mock as router:
        router.get("http://localhost:9999/health").mock(
            side_effect=_auth_handler("s3cret")
        )
        with pytest.raises(RuntimeError, match="HTTP 401"):
            await starter._verify_single_health("srv", cfg)


@pytest.mark.asyncio
async def test_verify_single_health_liveness_only_503_raises() -> None:
    """REQ-005: `liveness` alone is not proof, so a live but unproven server fails here."""
    import respx
    from agent.startup_mcp_starter import McpServerStarter

    ctx, cfg = _starter_ctx("s3cret")
    starter = McpServerStarter(ctx, MagicMock())
    with respx.mock as router:
        router.get("http://localhost:9999/health").mock(
            return_value=httpx.Response(503, json={"liveness": True})
        )
        with pytest.raises(RuntimeError, match="HTTP 503"):
            await starter._verify_single_health("srv", cfg)


@pytest.mark.asyncio
async def test_verify_single_health_required_capability_ok_503_does_not_raise() -> None:
    """The same live body with the required capability `ok` is proof (AC-05)."""
    import agent.startup_mcp_starter as starter_module
    import respx
    from agent.startup_mcp_starter import McpServerStarter

    ctx, cfg = _starter_ctx("s3cret")
    starter = McpServerStarter(ctx, MagicMock())
    with (
        respx.mock as router,
        patch.object(
            starter_module,
            "load_tool_catalog",
            return_value={"server": {"srv": {"required_capability": "github.api"}}},
        ),
    ):
        router.get("http://localhost:9999/health").mock(
            return_value=httpx.Response(
                503, json={"liveness": True, "capabilities": {"github.api": "ok"}}
            )
        )
        # Must not raise: the catalog capability is proven `ok`.
        await starter._verify_single_health("srv", cfg)


@pytest.mark.asyncio
async def test_verify_single_health_legacy_body_falls_back_to_ready() -> None:
    """A body with no capability block is read through `ready` (D-6)."""
    import respx
    from agent.startup_mcp_starter import McpServerStarter

    ctx, cfg = _starter_ctx("s3cret")
    starter = McpServerStarter(ctx, MagicMock())
    with respx.mock as router:
        router.get("http://localhost:9999/health").mock(
            return_value=httpx.Response(503, json={"ready": True})
        )
        await starter._verify_single_health("srv", cfg)


@pytest.mark.asyncio
async def test_verify_single_health_unproven_body_raises():
    import httpx
    import respx
    from agent.startup_mcp_starter import McpServerStarter

    ctx, cfg = _starter_ctx("s3cret")
    starter = McpServerStarter(ctx, MagicMock())
    with respx.mock as router:
        router.get("http://localhost:9999/health").mock(
            return_value=httpx.Response(
                503,
                json={"liveness": False},
                headers={"content-type": "application/json"},
            )
        )
        with pytest.raises(RuntimeError, match="HTTP 503"):
            await starter._verify_single_health("srv", cfg)


@pytest.mark.asyncio
async def test_verify_single_health_non_503_non_200_raises():
    import httpx
    import respx
    from agent.startup_mcp_starter import McpServerStarter

    ctx, cfg = _starter_ctx("s3cret")
    starter = McpServerStarter(ctx, MagicMock())
    with respx.mock as router:
        router.get("http://localhost:9999/health").mock(
            return_value=httpx.Response(401, json={"error": "Unauthorized"})
        )
        with pytest.raises(RuntimeError, match="HTTP 401"):
            await starter._verify_single_health("srv", cfg)


# --- verify_health report-based readiness (httpx-level, REQ-005) ---


def _verify_ctx():
    """Build the ctx/cfg pair used by the verify_health httpx-level tests."""
    from shared.mcp_config import McpServerConfig, StartupMode, TransportType

    cfg = McpServerConfig(
        transport=TransportType.HTTP,
        url="http://localhost:9999",
        startup_mode=StartupMode.SUBPROCESS,
        cmd=["python", "server.py"],
        auth_token="s3cret",
    )
    ctx = MagicMock()
    ctx.cfg.mcp.mcp_servers = {"srv": cfg}
    ctx.services_required.tools = MagicMock()
    ctx.services_required.lifecycle = MagicMock()
    return ctx, cfg


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "body",
    [
        {"ready": True},
        {"liveness": True, "ready": True, "capabilities": {"github.api": "ok"}},
    ],
)
async def test_verify_health_proven_readiness_503_object_not_retried(
    monkeypatch: pytest.MonkeyPatch, body: dict
) -> None:
    """A 503 body that proves readiness is accepted with one probe (AC-05)."""
    import respx
    from agent.startup_mcp_starter import McpServerStarter

    monkeypatch.setattr("agent.startup_mcp_starter.RETRY_DELAY_SEC", 0.01)
    ctx, _ = _verify_ctx()
    starter = McpServerStarter(ctx, MagicMock())
    with respx.mock as router:
        route = router.get("http://localhost:9999/health").mock(
            return_value=httpx.Response(503, json=body)
        )
        # Must not raise or retry: the body is readiness proof.
        await starter.verify_health()
    assert route.call_count == 1


@pytest.mark.asyncio
async def test_verify_health_liveness_only_503_retries_then_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """REQ-005: `liveness` true alone is not proof, so the object body now takes the retry path."""
    import respx
    from agent.startup_mcp_starter import McpServerStarter

    monkeypatch.setattr("agent.startup_mcp_starter.RETRY_DELAY_SEC", 0.01)
    ctx, _ = _verify_ctx()
    starter = McpServerStarter(ctx, MagicMock())
    with respx.mock as router:
        route = router.get("http://localhost:9999/health").mock(
            return_value=httpx.Response(503, json={"liveness": True})
        )
        with pytest.raises(RuntimeError, match=r"\[fatal\]"):
            await starter.verify_health()
    # main probe + the retry helper's single post-startup probe
    assert route.call_count == 2


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(503, json=[1, 2]),
        httpx.Response(503, json="unavailable"),
        httpx.Response(
            503,
            content=b"degraded but not json",
            headers={"content-type": "application/json"},
        ),
    ],
)
async def test_verify_health_non_object_503_body_retries_then_fails(
    monkeypatch: pytest.MonkeyPatch, response: httpx.Response
) -> None:
    """A non-object or malformed 503 body enters the retry path and ends in the [fatal] error."""
    import respx
    from agent.startup_mcp_starter import McpServerStarter

    monkeypatch.setattr("agent.startup_mcp_starter.RETRY_DELAY_SEC", 0.01)
    ctx, _ = _verify_ctx()
    starter = McpServerStarter(ctx, MagicMock())
    with respx.mock as router:
        route = router.get("http://localhost:9999/health").mock(return_value=response)
        with pytest.raises(RuntimeError, match=r"\[fatal\]"):
            await starter.verify_health()
    # main probe + the retry helper's single post-startup _verify_single_health
    # probe (startrev002: skip_first_attempt, so a failing server is probed twice)
    assert route.call_count == 2


@pytest.mark.asyncio
async def test_verify_health_non_boolean_liveness_retries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A 503 object body with liveness "false" (string) must retry, not be accepted."""
    import respx
    from agent.startup_mcp_starter import McpServerStarter

    monkeypatch.setattr("agent.startup_mcp_starter.RETRY_DELAY_SEC", 0.01)
    ctx, _ = _verify_ctx()
    starter = McpServerStarter(ctx, MagicMock())
    with respx.mock as router:
        route = router.get("http://localhost:9999/health").mock(
            return_value=httpx.Response(503, json={"liveness": "false"})
        )
        with pytest.raises(RuntimeError, match=r"\[fatal\]"):
            await starter.verify_health()
    # main probe + the retry helper's single post-startup _verify_single_health
    # probe (startrev002: skip_first_attempt, so a failing server is probed twice)
    assert route.call_count == 2


@pytest.mark.asyncio
async def test_verify_health_readiness_decision_delegates_to_the_shared_helper(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The accept decision must be the shared helper's: patching `is_ready` true accepts a
    legacy body whose own `ready` flag is false, directly in verify_health with a single probe."""
    import respx
    from agent.http_lifecycle_health_checker import HealthChecker
    from agent.startup_mcp_starter import McpServerStarter

    monkeypatch.setattr("agent.startup_mcp_starter.RETRY_DELAY_SEC", 0.01)
    ctx, _ = _verify_ctx()
    starter = McpServerStarter(ctx, MagicMock())
    with respx.mock as router:
        route = router.get("http://localhost:9999/health").mock(
            return_value=httpx.Response(503, json={"liveness": True})
        )
        with patch.object(HealthChecker, "is_ready", return_value=True):
            await starter.verify_health()
    assert route.call_count == 1


@pytest.mark.asyncio
async def test_effective_timeout_reaches_both_probes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """T-01 (REQ-001): the post-startup probe and the retry probe use the server's value, not 5.0."""
    import agent.startup_mcp_starter as starter_module
    from agent.startup_mcp_starter import McpServerStarter
    from shared.mcp_config import McpServerConfig, StartupMode, TransportType

    monkeypatch.setattr("agent.startup_mcp_starter.RETRY_DELAY_SEC", 0.01)
    cfg = McpServerConfig(
        transport=TransportType.HTTP,
        url="http://localhost:9999",
        startup_mode=StartupMode.SUBPROCESS,
        cmd=["python", "server.py"],
        auth_token="s3cret",
        health_timeout=7.5,
    )
    ctx = MagicMock()
    ctx.cfg.mcp.mcp_servers = {"srv": cfg}
    ctx.services_required.tools = MagicMock()
    ctx.services_required.lifecycle = MagicMock()
    starter = McpServerStarter(ctx, MagicMock())

    clients: list[_RecordingClient] = []

    def _factory(*args: object, **kwargs: object) -> _RecordingClient:
        # A live but unproven body keeps the server on the retry path, so both probes run.
        client = _RecordingClient(kwargs, httpx.Response(503, json={"liveness": True}))
        clients.append(client)
        return client

    with patch.object(starter_module.httpx, "AsyncClient", side_effect=_factory):
        with pytest.raises(RuntimeError, match=r"\[fatal\]"):
            await starter.verify_health()

    assert [c.kwargs["timeout"] for c in clients] == [7.5, 7.5]
    # REQ-003: the header comes from auth_headers(), the only health-auth path.
    assert clients[0].kwargs["headers"] == cfg.auth_headers()


# --- startup retry reaches the subprocess layer a second time (real router) ---


def _real_router_ctx(failures):
    """Build a real ``McpServerStarter`` around a real router with only the subprocess layer faked.

    *failures* is a list of exceptions; the fake HTTP manager's ``start`` raises them in order
    for the first ``len(failures)`` calls and records a single fake ``Popen`` afterwards.
    Returns ``(ctx, router, fake_http_mgr, proc)``.
    """
    import subprocess
    from unittest.mock import AsyncMock, MagicMock

    from agent.http_lifecycle_process_record import ManagedProcessRecord
    from agent.lifecycle import LifecycleState
    from agent.lifecycle_router import _ServerLifecycleRouter
    from shared.mcp_config import McpServerConfig, StartupMode, TransportType

    cfg = McpServerConfig(
        transport=TransportType.HTTP,
        url="http://localhost:9999",
        auth_token="test-token",
        startup_mode=StartupMode.SUBPROCESS,
        cmd=["python", "server.py"],
    )
    router = _ServerLifecycleRouter({"srv": cfg}, MagicMock())
    fake_http_mgr = AsyncMock()
    fake_http_mgr._records = {}
    proc = MagicMock(spec=subprocess.Popen)
    record = ManagedProcessRecord(
        process=proc,
        pid=12345,
        pgid=12345,
        stderr_log=None,
        state=LifecycleState.RUNNING,
    )
    fake_http_mgr._records["srv"] = record
    router._subprocess_mgr._http_mgr = fake_http_mgr

    state = {"n": 0}

    async def _start(server_key, config, shutdown_event=None):
        state["n"] += 1
        if state["n"] <= len(failures):
            raise failures[state["n"] - 1]
        fake_http_mgr._records[server_key] = record
        return None

    fake_http_mgr.start = AsyncMock(side_effect=_start)

    ctx = MagicMock()
    ctx.services_required.tools = MagicMock()
    ctx.services_required.lifecycle = router
    ctx.cfg.mcp.mcp_servers = {"srv": cfg}
    return ctx, router, fake_http_mgr, proc


class TestStartupRetryWithRealRouter:
    """Integration-style: real router + real starter, only the subprocess layer faked."""

    @pytest.mark.asyncio
    async def test_first_failure_then_success_launches_second_attempt(self) -> None:
        from agent.http_lifecycle_errors import HttpStartupError, StartupFailure
        from agent.lifecycle import LifecycleState
        from agent.startup_mcp_starter import McpServerStarter

        ctx, router, fake_http_mgr, proc = _real_router_ctx(
            [HttpStartupError(StartupFailure("srv", "port busy", ""))]
        )
        with patch("agent.startup_mcp_starter.RETRY_DELAY_SEC", 0.0):
            started = await McpServerStarter(ctx, MagicMock()).start_servers()

        assert started == [proc]
        assert fake_http_mgr.start.await_count == 2
        assert router.get_transport_state("srv") == LifecycleState.RUNNING
        assert "srv" not in router._failed_starts

    @pytest.mark.asyncio
    async def test_two_failures_abort_with_named_error_and_visible_first_failure(
        self,
    ) -> None:
        from agent.http_lifecycle_errors import HttpStartupError, StartupFailure
        from agent.startup_mcp_starter import McpServerStarter

        # Two failures: the start entry makes two subprocess-layer calls
        # (inline initial attempt + the retry helper's single skip-first
        # attempt); the helper aborts on that second call. This is the
        # startrev002 contract: a failing server is attempted exactly twice.
        ctx, router, fake_http_mgr, _proc = _real_router_ctx(
            [
                HttpStartupError(StartupFailure("srv", "first reason", "")),
                HttpStartupError(StartupFailure("srv", "second reason", "")),
            ]
        )
        with (
            patch("agent.startup_mcp_starter.RETRY_DELAY_SEC", 0.0),
            patch("agent.startup_mcp_starter.logger") as patched_logger,
        ):
            with pytest.raises(HttpStartupError) as excinfo:
                await McpServerStarter(ctx, MagicMock()).start_servers()

        text = str(excinfo.value)
        assert "srv" in text
        assert "second reason" in text
        assert fake_http_mgr.start.await_count == 2
        assert isinstance(excinfo.value.__cause__, HttpStartupError)
        warning_calls = [c for c in patched_logger.warning.call_args_list if c.args]
        assert warning_calls, "first failure must be logged at WARNING"
        first_call = warning_calls[0]
        assert "First attempt failed" in first_call.args[0]
        joined = " ".join(str(a) for a in first_call.args)
        assert "srv" in joined
        assert "first reason" in joined

    @pytest.mark.asyncio
    async def test_shutdown_suppressed_start_raises_startup_interrupted(self) -> None:
        from unittest.mock import AsyncMock

        from agent.startup import StartupInterrupted
        from agent.startup_mcp_starter import McpServerStarter

        ctx, router, fake_http_mgr, _proc = _real_router_ctx([])
        fake_http_mgr.shutdown_all = AsyncMock(return_value=[])
        await router.shutdown_all()

        # The no-argument call is today's default path: the surface is reached with no
        # budget, and the lifecycle fills in its own window (REQ-010).
        fake_http_mgr.shutdown_all.assert_awaited_once_with(budget=None)

        with pytest.raises(StartupInterrupted):
            await McpServerStarter(ctx, MagicMock()).start_servers()

        fake_http_mgr.start.assert_not_called()

    @pytest.mark.asyncio
    async def test_shutdown_all_accepts_the_budget_it_is_given(self) -> None:
        """REQ-010: the startup path's lifecycle surface accepts a supplied budget.

        Only the surface is pinned here; the rollback path decides when a budget exists,
        and that is asserted in tests/agent/test_startup_rollback.py.
        """
        from unittest.mock import AsyncMock

        from agent.shutdown_budget import ShutdownBudget

        _ctx, router, fake_http_mgr, _proc = _real_router_ctx([])
        fake_http_mgr.shutdown_all = AsyncMock(return_value=[])
        budget = ShutdownBudget(total_seconds=15.0)
        budget.arm()

        await router.shutdown_all(budget=budget)

        fake_http_mgr.shutdown_all.assert_awaited_once_with(budget=budget)
