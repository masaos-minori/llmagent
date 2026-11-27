"""tests/mcp_servers/cicd/test_cicd_lifecycle.py

Lifecycle contract tests for scripts/mcp_servers/cicd/cicd_service_init.py and the
scripts/mcp_servers/cicd/cicd_server.py lifespan (REQ-008, REQ-003, AC-6).

`build_service()` receives the HTTP client from its caller and never creates one, so the
lifespan is the single owner. These pin test injection through the same parameter, that
repeated construction does not leak a client, that the lifespan creates the client on
startup and closes it on shutdown, and that the probe outcome it stores reaches health.
"""

from __future__ import annotations

import asyncio
import gc
import weakref
from collections.abc import Callable, Generator

import httpx
import pytest
from fastapi.testclient import TestClient
from mcp_servers.cicd import cicd_server
from mcp_servers.cicd.cicd_models import CicdConfig
from mcp_servers.cicd.cicd_service_github_actions_composite import (
    GitHubActionsCompositeBackend,
)
from mcp_servers.cicd.cicd_service_guards import ProbeOutcome
from mcp_servers.cicd.cicd_service_init import build_service
from shared.security.result_dto import (
    REASON_AUTH_TOKEN_MISSING,
    REASON_DEPENDENCY_UNREACHABLE,
    REASON_NOT_APPLICABLE,
    REASON_OK,
)

from tests.mcp_servers._auth_headers import MCP_TEST_AUTH_HEADERS

pytestmark = pytest.mark.contract

_ENV_VAR = "GITHUB_TOKEN"
_CREDENTIAL = "ghp_test_token"
_OK_OUTCOME = ProbeOutcome(REASON_OK, REASON_OK, REASON_OK)


def _cfg(github_token: str = "") -> CicdConfig:
    return CicdConfig(
        repo_allowlist=["acme/widgets"],
        workflow_allowlist=["ci.yml"],
        github_token=github_token,
    )


@pytest.fixture
def client() -> Generator[httpx.AsyncClient]:
    """A client owned by the test, so the injected object is identifiable."""
    http = httpx.AsyncClient(timeout=30.0)
    try:
        yield http
    finally:
        asyncio.run(http.aclose())


@pytest.fixture
def lifespan_state() -> Generator[None]:
    """Restore the module-level state the lifespan assigns (REQ-008)."""
    saved = (cicd_server._http_client, cicd_server._service, cicd_server._probe_outcome)
    try:
        yield
    finally:
        cicd_server._http_client = saved[0]
        cicd_server._service = saved[1]
        cicd_server._probe_outcome = saved[2]


def _stub_probe(outcome: ProbeOutcome) -> Callable[..., object]:
    """A probe stand-in for the lifespan, so no case reaches the network."""

    async def _probe(
        cfg: CicdConfig, http: httpx.AsyncClient, effective_credential: str
    ) -> ProbeOutcome:
        return outcome

    return _probe


def _probe_client(
    handler: Callable[[httpx.Request], httpx.Response],
) -> httpx.AsyncClient:
    """A client whose transport is the recorded handler, so the probe stays offline."""
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


def test_injected_client_reaches_the_backends_unchanged(
    client: httpx.AsyncClient,
) -> None:
    """The same client object is handed to the composite and its sub-backends (AC-6)."""
    service = build_service(_cfg(_CREDENTIAL), client)
    backend = service._backend
    assert isinstance(backend, GitHubActionsCompositeBackend)
    assert backend._workflow._http is client
    assert backend._job._http is client


def test_repeated_construction_does_not_create_a_client(
    client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No client is created at service-init time, so repeated calls leak nothing (REQ-008)."""
    live: list[weakref.ref[httpx.AsyncClient]] = []
    original = httpx.AsyncClient

    def tracking(*args: object, **kwargs: object) -> httpx.AsyncClient:
        http = original(*args, **kwargs)
        live.append(weakref.ref(http))
        return http

    monkeypatch.setattr(httpx, "AsyncClient", tracking)
    for _ in range(3):
        build_service(_cfg(_CREDENTIAL), client)
    gc.collect()
    alive = [ref() for ref in live]
    assert [http for http in alive if http is not None] == []


def test_effective_credential_is_the_resolution_function_value(
    monkeypatch: pytest.MonkeyPatch,
    client: httpx.AsyncClient,
) -> None:
    """The backend token equals the resolved effective value, not the config alone (AC-1)."""
    monkeypatch.setenv(_ENV_VAR, _CREDENTIAL)
    service = build_service(_cfg("config-token"), client)
    backend = service._backend
    assert isinstance(backend, GitHubActionsCompositeBackend)
    assert backend._workflow._token == _CREDENTIAL


def test_missing_credential_keeps_the_rate_limit_warning(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    client: httpx.AsyncClient,
) -> None:
    """A service built without an effective credential still warns about the rate limit."""
    monkeypatch.delenv(_ENV_VAR, raising=False)
    build_service(_cfg(""), client)
    assert "60 req/hr" in caplog.text


class TestLifespanOwnership:
    """The lifespan is the single owner of the shared client (REQ-008, AC-6)."""

    def test_client_is_created_on_startup_and_closed_on_shutdown(
        self, monkeypatch: pytest.MonkeyPatch, lifespan_state: None
    ) -> None:
        monkeypatch.setattr(
            cicd_server, "run_read_permission_probe", _stub_probe(_OK_OUTCOME)
        )
        with TestClient(cicd_server.app, headers=MCP_TEST_AUTH_HEADERS) as test_client:
            http = cicd_server._http_client
            service = cicd_server._service
            assert http is not None and service is not None
            assert not http.is_closed
            # The service is built from the client the lifespan created, not another one.
            assert isinstance(service._backend, GitHubActionsCompositeBackend)
            assert service._backend._workflow._http is http
            assert test_client.get("/v1/tools").status_code == 200
        assert http.is_closed

    def test_probe_outcome_is_stored_for_health(
        self, monkeypatch: pytest.MonkeyPatch, lifespan_state: None
    ) -> None:
        """The lifespan runs the probe and stores the outcome health reads (REQ-003)."""
        outcome = ProbeOutcome(REASON_AUTH_TOKEN_MISSING, REASON_OK, REASON_OK)
        monkeypatch.setattr(
            cicd_server, "run_read_permission_probe", _stub_probe(outcome)
        )
        with TestClient(cicd_server.app, headers=MCP_TEST_AUTH_HEADERS):
            assert cicd_server._probe_outcome == outcome

    def test_probe_failure_reaches_health_as_a_dependency(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A failed probe makes health degraded through the shared ready rule (AC-1, AC-7)."""
        monkeypatch.setenv(_ENV_VAR, _CREDENTIAL)
        monkeypatch.setattr(
            cicd_server, "_security_posture", cicd_server._build_security_posture()
        )
        monkeypatch.setattr(
            cicd_server,
            "_probe_outcome",
            ProbeOutcome(
                REASON_DEPENDENCY_UNREACHABLE,
                REASON_DEPENDENCY_UNREACHABLE,
                REASON_NOT_APPLICABLE,
            ),
        )
        test_client = TestClient(cicd_server.app, headers=MCP_TEST_AUTH_HEADERS)
        response = test_client.get("/health")

        assert response.status_code == 503
        assert response.json()["dependencies"] == {
            "credential_probe": REASON_DEPENDENCY_UNREACHABLE
        }

    def test_probe_ok_leaves_dependencies_empty(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """An OK probe is not a dependency failure, so health stays 200 (AC-1)."""
        monkeypatch.setenv(_ENV_VAR, _CREDENTIAL)
        monkeypatch.setattr(
            cicd_server, "_security_posture", cicd_server._build_security_posture()
        )
        monkeypatch.setattr(cicd_server, "_probe_outcome", _OK_OUTCOME)
        test_client = TestClient(cicd_server.app, headers=MCP_TEST_AUTH_HEADERS)
        response = test_client.get("/health")

        assert response.status_code == 200
        assert response.json()["dependencies"] == {}


class TestProbePolicy:
    """The lifespan probe is side-effect-free and reports status without the token (AC-7)."""

    async def test_read_permission_ok(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.path == "/repos/acme/widgets/actions/workflows"
            return httpx.Response(200, headers={"x-ratelimit-remaining": "100"})

        outcome = await cicd_server.run_read_permission_probe(
            _cfg(_CREDENTIAL), _probe_client(handler), _CREDENTIAL
        )
        assert outcome == ProbeOutcome(REASON_OK, REASON_OK, REASON_OK)

    async def test_read_permission_denied_reports_the_credential(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(403)

        outcome = await cicd_server.run_read_permission_probe(
            _cfg(_CREDENTIAL), _probe_client(handler), _CREDENTIAL
        )
        assert outcome.read_permission == REASON_AUTH_TOKEN_MISSING
        assert outcome.reachability == REASON_OK

    async def test_unreachable_api_reports_the_dependency(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("unreachable", request=request)

        outcome = await cicd_server.run_read_permission_probe(
            _cfg(_CREDENTIAL), _probe_client(handler), _CREDENTIAL
        )
        assert outcome.read_permission == REASON_DEPENDENCY_UNREACHABLE
        assert outcome.reachability == REASON_DEPENDENCY_UNREACHABLE

    async def test_empty_allowlist_runs_no_probe(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            raise AssertionError("no probe target exists")

        outcome = await cicd_server.run_read_permission_probe(
            CicdConfig(repo_allowlist=[], workflow_allowlist=[]),
            _probe_client(handler),
            _CREDENTIAL,
        )
        assert outcome == ProbeOutcome(
            REASON_NOT_APPLICABLE, REASON_NOT_APPLICABLE, REASON_NOT_APPLICABLE
        )

    async def test_dispatch_permission_is_never_reported_as_granted(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200)

        outcome = await cicd_server.run_read_permission_probe(
            _cfg(_CREDENTIAL), _probe_client(handler), _CREDENTIAL
        )
        assert outcome.dispatch_permission == REASON_NOT_APPLICABLE

    async def test_exhausted_rate_limit_reports_the_dependency(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(403, headers={"x-ratelimit-remaining": "0"})

        outcome = await cicd_server.run_read_permission_probe(
            _cfg(_CREDENTIAL), _probe_client(handler), _CREDENTIAL
        )
        assert outcome.read_permission == REASON_DEPENDENCY_UNREACHABLE
        assert outcome.rate_limit == REASON_DEPENDENCY_UNREACHABLE
