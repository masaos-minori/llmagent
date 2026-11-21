"""tests/agent/test_startup_validation.py

Regression tests for REQ-002, REQ-003: Verify the RAG consistency check inside
StartupValidationPipeline.check_services() enforces its timeout and reports a
normal pass, by driving the real check_services() body.
"""

from __future__ import annotations

import asyncio
import sqlite3
import threading
import time
from contextlib import ExitStack
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import agent.startup_validation as startup_validation
import pytest
import yaml
from agent.shared.health_models import (
    HealthCheckResult,
    StartupCheckStatus,
    StartupValidationResult,
)
from agent.startup_validation import (
    StartupValidationPipeline,
    _check_component_mandatoriness,
)
from db.models import ConsistencyFinding, FindingSeverity
from shared.component_mandatoriness import (
    ComponentMandatorinessError,
    load_component_mandatoriness,
)
from shared.mcp_config import (
    McpServerConfig,
    StartupMode,
    TransportType,
)
from shared.runtime_tool_registry import RuntimeToolRegistry
from shared.tool_registry import get_registry

from tests.shared.runtime_tool_factory import build_fixture_runtime_tool


def _make_ctx() -> MagicMock:
    ctx = MagicMock()
    ctx.cfg.memory.memory_embed_dim = 768
    return ctx


async def _run_check_services(
    rag_service: MagicMock,
    *,
    wait_for_side_effect: BaseException | None = None,
    mcp_servers: dict[str, object] | None = None,
    discovery_findings: list[Any] | None = None,
) -> StartupValidationResult:
    """Run the real check_services() with every other check mocked to a clean pass."""
    ctx = _make_ctx()
    if mcp_servers is not None:
        ctx.cfg.mcp.mcp_servers = mcp_servers
    findings = [] if discovery_findings is None else discovery_findings
    discovery = MagicMock(
        return_value=MagicMock(
            discover_all=AsyncMock(
                return_value=MagicMock(registry=None, findings=findings, unreachable=[])
            )
        )
    )
    mocks: dict[str, object] = {
        "check_readiness": AsyncMock(return_value=HealthCheckResult()),
        "McpToolDiscoveryService": discovery,
        "check_routing_safety_tiers": MagicMock(return_value=[]),
        "RagMaintenanceService": MagicMock(return_value=rag_service),
    }
    if mcp_servers is not None:
        # A real server dict makes the mandatoriness cross-check read the on-disk
        # registry; neutralise it so only the mcp_auth outcome is under test.
        mocks["_check_component_mandatoriness"] = MagicMock()
    with ExitStack() as stack:
        for name, mock_obj in mocks.items():
            stack.enter_context(patch(f"agent.startup_validation.{name}", mock_obj))
        stack.enter_context(
            patch(
                "db.config.build_db_config",
                return_value=MagicMock(embedding_dims=768),
            )
        )
        # check_services() builds its own Logger; keep it from touching log files.
        stack.enter_context(patch("shared.logger.Logger", MagicMock()))
        if wait_for_side_effect is not None:
            stack.enter_context(
                patch(
                    "agent.startup_validation.asyncio.wait_for",
                    side_effect=wait_for_side_effect,
                )
            )
        return await StartupValidationPipeline(ctx, MagicMock()).check_services()


def _rag_outcomes(result: StartupValidationResult) -> list[StartupCheckStatus]:
    return [o.status for o in result.outcomes if o.source == "rag_consistency"]


def _run_check_config(
    ctx: MagicMock,
    *,
    mcp_servers: dict[str, object] | None = None,
    **overrides: object,
) -> StartupValidationResult:
    """Run the real check_config() config-only stage with the three module-level
    config checks mocked to clean passes, overridden per-test via kwargs (named after
    the agent.startup_validation import site), and return the captured result.

    check_config() is synchronous, so this helper is synchronous too.
    """
    if mcp_servers is not None:
        ctx.cfg.mcp.mcp_servers = mcp_servers
    mocks: dict[str, object] = {
        "check_routing_safety_tiers": MagicMock(return_value=[]),
        "_check_component_mandatoriness": MagicMock(),
    }
    mocks.update(overrides)
    with ExitStack() as stack:
        for name, mock_obj in mocks.items():
            stack.enter_context(patch(f"agent.startup_validation.{name}", mock_obj))
        return StartupValidationPipeline(ctx, MagicMock()).check_config()


class TestCheckConfigStage:
    """REQ-005, REQ-006: the config-only stage reports its four checks together and
    without a short-circuit among them, driven directly through the real check_config()."""

    @pytest.mark.asyncio
    async def test_safety_tier_failure_is_fatal(self) -> None:
        """A tier-drift report failure is always FATAL (fail-closed), regardless of drift policy."""
        ctx = _make_ctx()
        result = _run_check_config(
            ctx,
            check_routing_safety_tiers=MagicMock(
                side_effect=RuntimeError("tier missing")
            ),
        )

        outcomes = [o for o in result.outcomes if o.source == "routing_drift"]
        assert any(o.status == StartupCheckStatus.FATAL for o in outcomes)

    @pytest.mark.asyncio
    async def test_valid_config_passes_cleanly(self) -> None:
        """A valid configuration runs all four config checks cleanly: no FATAL, no
        WARNING, and an OK mcp_auth outcome."""
        ctx = _make_ctx()
        ctx.cfg.mcp.mcp_servers = {"web": MagicMock(auth_token="valid-token")}
        result = _run_check_config(ctx)

        assert not result.has_fatal
        assert not any(o.status == StartupCheckStatus.WARNING for o in result.outcomes)
        auth_outcomes = [o for o in result.outcomes if o.source == "mcp_auth"]
        assert any(o.status == StartupCheckStatus.OK for o in auth_outcomes)

    @pytest.mark.asyncio
    async def test_tool_missing_from_safety_tiers_is_fatal(self) -> None:
        """Agentcfg003 drift shape: a seed-registered tool with no live declared
        entry is FATAL, never a warning (REQ-007 / AC-10)."""
        ctx = _make_ctx()
        names = sorted(get_registry().get_all_tool_names())
        ctx.services = MagicMock()
        ctx.services.runtime_tools = RuntimeToolRegistry(
            tools={name: build_fixture_runtime_tool(name, "git") for name in names[1:]},
            allowed_servers=frozenset({"git"}),
        )
        result = _run_check_config(
            ctx,
            check_routing_safety_tiers=startup_validation.check_routing_safety_tiers,
        )

        outcomes = [o for o in result.outcomes if o.source == "routing_drift"]
        assert [o.status for o in outcomes] == [StartupCheckStatus.FATAL]
        assert names[0] in outcomes[0].message
        assert not any(o.status == StartupCheckStatus.WARNING for o in outcomes)


class TestRagConsistencyTimeout:
    """Tests for REQ-002, REQ-003: RAG check timeout enforcement."""

    @pytest.mark.asyncio
    async def test_rag_check_timeout_enforced(self) -> None:
        """REQ-002: a timed-out RAG consistency check warns with a WARNING, not fatal."""
        rag_service = MagicMock()
        result = await _run_check_services(
            rag_service,
            wait_for_side_effect=TimeoutError("timed out"),
        )

        assert _rag_outcomes(result) == [StartupCheckStatus.WARNING]
        warned = [o for o in result.outcomes if o.source == "rag_consistency"]
        assert "timed out" in warned[0].message
        assert not result.has_fatal

    @pytest.mark.asyncio
    async def test_rag_check_succeeds_within_timeout(self) -> None:
        """REQ-003: a normal RAG check reports OK."""
        rag_service = MagicMock()
        rag_service.consistency.return_value = MagicMock(is_consistent=True, issues=[])

        result = await _run_check_services(rag_service)

        assert _rag_outcomes(result) == [StartupCheckStatus.OK]
        rag_service.consistency.assert_called_once()

    @pytest.mark.asyncio
    async def test_inconsistent_rag_result_without_findings_is_fatal(self) -> None:
        """An inconsistent result that carries no finding is never silent."""
        rag_service = MagicMock()
        rag_service.consistency.return_value = MagicMock(
            is_consistent=False, findings=()
        )

        result = await _run_check_services(rag_service)

        assert _rag_outcomes(result) == [StartupCheckStatus.FATAL]
        assert result.has_fatal

    @pytest.mark.asyncio
    async def test_unverified_probe_finding_is_a_warning(self) -> None:
        """An unverifiable-result finding is DEGRADED: a warning, and startup continues."""
        rag_service = MagicMock()
        rag_service.consistency.return_value = MagicMock(
            is_consistent=False,
            findings=(
                ConsistencyFinding(
                    severity=FindingSeverity.DEGRADED,
                    message="[WARNING] FK consistency could not be verified.",
                    repair_action="rerun_check",
                ),
            ),
        )

        result = await _run_check_services(rag_service)

        assert _rag_outcomes(result) == [StartupCheckStatus.WARNING]
        assert not result.has_fatal

    @pytest.mark.asyncio
    async def test_rag_check_programming_error_classified(self) -> None:
        """REQ-004: a programming-error exception is recorded as a classified WARNING."""
        rag_service = MagicMock()
        rag_service.consistency.side_effect = KeyError("missing key")

        result = await _run_check_services(rag_service)

        assert _rag_outcomes(result) == [StartupCheckStatus.WARNING]
        warned = [o for o in result.outcomes if o.source == "rag_consistency"]
        assert "PROGRAMMING_ERROR" in warned[0].message
        assert "KeyError" in warned[0].message
        assert not result.has_fatal

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("exc", "category"),
        [
            (ConnectionRefusedError("refused"), "NETWORK_TRANSIENT"),
            (sqlite3.OperationalError("disk I/O error"), "DATABASE_OR_IO"),
            (PermissionError("denied"), "DATABASE_OR_IO"),
            (ValueError("bad data"), "UNKNOWN"),
        ],
    )
    async def test_rag_check_failure_category(
        self, exc: Exception, category: str
    ) -> None:
        """REQ-002: each root-cause category is carried in the WARNING message."""
        rag_service = MagicMock()
        rag_service.consistency.side_effect = exc

        result = await _run_check_services(rag_service)

        assert _rag_outcomes(result) == [StartupCheckStatus.WARNING]
        warned = [o for o in result.outcomes if o.source == "rag_consistency"]
        assert category in warned[0].message
        assert type(exc).__name__ in warned[0].message
        assert not result.has_fatal


class TestToolDiscoveryFatalSkipsRagCheck:
    """REQ-001/REQ-003: a tool-discovery FATAL returns before the RAG check."""

    @pytest.mark.asyncio
    async def test_tool_discovery_fatal_skips_rag_check(self) -> None:
        """A FATAL discovery finding records an mcp_tool_discovery FATAL, sets
        has_fatal, and skips the RAG check entirely (service not called, no
        rag_consistency outcome)."""
        rag_service = MagicMock()
        fatal = MagicMock(
            status=StartupCheckStatus.FATAL, message="tool discovery failed"
        )
        result = await _run_check_services(rag_service, discovery_findings=[fatal])

        fatals = [o for o in result.outcomes if o.source == "mcp_tool_discovery"]
        assert fatals
        assert result.has_fatal
        assert not [o for o in result.outcomes if o.source == "rag_consistency"]
        rag_service.assert_not_called()

    @pytest.mark.asyncio
    async def test_tool_discovery_warning_only_still_runs_rag_check(self) -> None:
        """A warning-only discovery path records no FATAL and still runs the RAG
        check (the service is called and a rag_consistency outcome is produced)."""
        rag_service = MagicMock()
        rag_service.consistency.return_value = MagicMock(is_consistent=True, issues=[])
        warning = MagicMock(
            status=StartupCheckStatus.WARNING, message="tool discovery warning"
        )
        result = await _run_check_services(rag_service, discovery_findings=[warning])

        assert not result.has_fatal
        warned = [o for o in result.outcomes if o.source == "rag_consistency"]
        assert warned
        rag_service.consistency.assert_called()


@pytest.mark.asyncio
async def test_runtime_registry_published_after_posture_gate() -> None:
    """AC-5: runtime_tools is published only after the posture gate completes.

    Records the call order of the mandatoriness cross-check (config-only stage),
    the posture collection, and the discovery/publication step (runtime stage)
    across both stages and asserts the fail-closed sequence
    mandatoriness -> posture -> publication. The mandatoriness cross-check lives
    in the config-only stage (REQ-001/REQ-003), which runs before the runtime
    stage, so both stages are driven in order.
    """

    order: list[str] = []

    async def _collect_posture(_ctx: object) -> dict:
        order.append("posture")
        return {}

    async def _discover() -> MagicMock:
        order.append("publication")
        return MagicMock(registry=MagicMock(), findings=[], unreachable=[])

    ctx = _make_ctx()
    # The config-only stage reads mcp_servers during mcp_auth; an empty dict keeps
    # that clean so only the mandatoriness ordering is under test.
    ctx.cfg.mcp.mcp_servers = {}
    discovery = MagicMock()
    discovery.discover_all = AsyncMock(side_effect=_discover)

    mocks: dict[str, object] = {
        "check_readiness": AsyncMock(return_value=HealthCheckResult()),
        "McpToolDiscoveryService": MagicMock(return_value=discovery),
        "check_routing_safety_tiers": MagicMock(return_value=[]),
        "RagMaintenanceService": MagicMock(return_value=MagicMock()),
        "_check_component_mandatoriness": MagicMock(
            side_effect=lambda _c, _p: order.append("mandatoriness")
        ),
    }
    with ExitStack() as stack:
        for name, mock_obj in mocks.items():
            stack.enter_context(patch(f"agent.startup_validation.{name}", mock_obj))
        stack.enter_context(
            patch(
                "agent.startup_validation.collect_server_postures",
                side_effect=_collect_posture,
            )
        )
        stack.enter_context(
            patch(
                "db.config.build_db_config",
                return_value=MagicMock(embedding_dims=768),
            )
        )
        # check_services() builds its own Logger; keep it from touching log files.
        stack.enter_context(patch("shared.logger.Logger", MagicMock()))
        # Config-only stage runs the mandatoriness cross-check before the runtime stage.
        StartupValidationPipeline(ctx, MagicMock()).check_config()
        result = await StartupValidationPipeline(ctx, MagicMock()).check_services()

    assert not result.has_fatal
    assert order.index("mandatoriness") < order.index("posture")
    assert order.index("posture") < order.index("publication")


class TestMcpAuthDisabledServers:
    """REQ-001, REQ-002: the mcp_auth step exempts disabled token-less servers."""

    @pytest.mark.asyncio
    async def test_disabled_server_without_token_passes_mcp_auth(self) -> None:
        """REQ-001: a disabled server with an empty token yields an OK mcp_auth outcome."""
        disabled = McpServerConfig(
            transport=TransportType.HTTP,
            url="https://example.local/mcp",
            startup_mode=StartupMode.NONE,
            auth_token="",
        )

        result = _run_check_config(
            MagicMock(),
            mcp_servers={"optional_srv": disabled},
        )

        outcomes = [o for o in result.outcomes if o.source == "mcp_auth"]
        assert len(outcomes) == 1
        assert outcomes[0].status == StartupCheckStatus.OK
        assert not any(o.status == StartupCheckStatus.FATAL for o in outcomes)

    @pytest.mark.asyncio
    async def test_enabled_server_without_token_is_fatal_and_named(self) -> None:
        """REQ-002: an enabled token-less server is fatal and named in the message."""
        result = _run_check_config(
            MagicMock(),
            mcp_servers={"web": MagicMock(auth_token="", is_disabled=False)},
        )

        outcomes = [o for o in result.outcomes if o.source == "mcp_auth"]
        assert len(outcomes) == 1
        assert outcomes[0].status == StartupCheckStatus.FATAL
        assert "web" in outcomes[0].message

    @pytest.mark.asyncio
    async def test_message_lists_only_enabled_offenders(self) -> None:
        """REQ-002: a mix names only the enabled offender, not the disabled server."""
        disabled = McpServerConfig(
            transport=TransportType.HTTP,
            url="https://example.local/mcp",
            startup_mode=StartupMode.NONE,
            auth_token="",
        )

        result = _run_check_config(
            MagicMock(),
            mcp_servers={
                "optional_srv": disabled,
                "web": MagicMock(auth_token="", is_disabled=False),
            },
        )

        outcomes = [o for o in result.outcomes if o.source == "mcp_auth"]
        assert len(outcomes) == 1
        assert outcomes[0].status == StartupCheckStatus.FATAL
        assert "web" in outcomes[0].message
        assert "optional_srv" not in outcomes[0].message


def _write_registry(tmp_path: Path, *component_ids: str) -> Path:
    """Write a minimal valid registry classifying every id as ``required``."""
    entries = [
        {
            "component_id": cid,
            "classification": "required",
            "failure_category": "safety-integrity",
            "safety_role": "Baseline safety role.",
            "safely_disableable_functions": [],
            "startup_consequence": "abort_startup",
            "observability": ["ServiceWarning"],
            "owner": "agent-architecture-owner",
            "authority_adr": "ADR-004",
            "rationale": "Baseline rationale text.",
        }
        for cid in component_ids
    ]
    path = tmp_path / "component_mandatoriness.yaml"
    path.write_text(
        yaml.safe_dump({"version": 1, "entries": entries}), encoding="utf-8"
    )
    return path


def _server(*, required: bool) -> MagicMock:
    return MagicMock(required=required, auth_token="valid-token", is_disabled=False)


def _run_mandatoriness_check(
    servers: dict[str, object], *, side_effect: Any
) -> StartupValidationResult:
    """Run the real config stage with the real mandatoriness check unmocked.

    Only the registry loader is patched, so the fatal source label and message
    are asserted end to end through ``check_config()``.
    """
    with patch(
        "agent.startup_validation.load_component_mandatoriness", side_effect=side_effect
    ):
        return _run_check_config(
            _make_ctx(),
            mcp_servers=servers,
            _check_component_mandatoriness=_check_component_mandatoriness,
        )


def _mandatoriness_fatals(result: StartupValidationResult) -> list[str]:
    return [
        o.message
        for o in result.outcomes
        if o.source == "component_mandatoriness"
        and o.status == StartupCheckStatus.FATAL
    ]


class TestComponentMandatorinessAbort:
    """ADR-004 INV-14: startup does not continue when a component's mandatoriness
    is undefined. These tests run the real check, not a mock of it."""

    def test_unknown_configured_server_is_fatal(self, tmp_path: Path) -> None:
        registry_path = _write_registry(tmp_path, "shell")
        result = _run_mandatoriness_check(
            {"ghost": _server(required=True)},
            side_effect=lambda: load_component_mandatoriness(registry_path),
        )

        fatals = _mandatoriness_fatals(result)
        assert len(fatals) == 1
        assert "ghost" in fatals[0]
        assert result.has_fatal

    def test_conflicting_required_value_is_fatal(self, tmp_path: Path) -> None:
        registry_path = _write_registry(tmp_path, "shell")
        result = _run_mandatoriness_check(
            {"shell": _server(required=False)},
            side_effect=lambda: load_component_mandatoriness(registry_path),
        )

        fatals = _mandatoriness_fatals(result)
        assert len(fatals) == 1
        assert "shell" in fatals[0]

    @pytest.mark.parametrize(
        "error",
        [
            ComponentMandatorinessError("registry is invalid"),
            FileNotFoundError("registry file missing"),
        ],
    )
    def test_missing_or_invalid_registry_is_fatal(self, error: Exception) -> None:
        result = _run_mandatoriness_check(
            {"shell": _server(required=True)}, side_effect=error
        )

        fatals = _mandatoriness_fatals(result)
        assert len(fatals) == 1
        assert "Undeterminable component mandatoriness" in fatals[0]
        assert result.has_fatal

    def test_consistent_registry_adds_no_fatal(self, tmp_path: Path) -> None:
        registry_path = _write_registry(tmp_path, "shell")
        result = _run_mandatoriness_check(
            {"shell": _server(required=True)},
            side_effect=lambda: load_component_mandatoriness(registry_path),
        )

        assert _mandatoriness_fatals(result) == []
        assert not result.has_fatal


class _FakeRagService:
    """A fake RagMaintenanceService for the stop-hook tests (REQ-003/004/005).

    ``consistency(stop)`` records the event the pipeline passes, then either
    blocks on it (a check that outlives the startup bound) or returns a fixed
    result immediately (an in-time check), depending on ``block``. The recorded
    event lets a test assert whether the pipeline ever set the stop signal.
    """

    def __init__(
        self,
        *,
        block: bool = True,
        block_seconds: float = 30.0,
        result: object | None = None,
    ) -> None:
        self.block = block
        self.block_seconds = block_seconds
        self.result = (
            result
            if result is not None
            else MagicMock(is_consistent=False, findings=[])
        )
        self.event: threading.Event | None = None
        self.called = False

    def consistency(self, stop: threading.Event | None = None) -> object:
        self.called = True
        self.event = stop
        if self.block and stop is not None:
            stop.wait(timeout=self.block_seconds)
        return self.result


class TestRagConsistencyStopHook:
    """REQ-003, REQ-004, REQ-005: the RAG check is stopped by the startup bound.

    These drive the real check_services() with a fake service instead of the
    MagicMock used elsewhere, so the stop event the pipeline passes is observable.
    The bound is shortened by patching the module constant; the tests fail on the
    pre-change code because that constant does not exist yet.
    """

    @pytest.mark.asyncio
    async def test_timeout_sets_event_and_warns(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """REQ-003: a check that outlives the bound is stopped; the event is set
        and the existing rag_consistency warning is reported."""
        monkeypatch.setattr("agent.startup_validation.RAG_CONSISTENCY_TIMEOUT_SEC", 0.1)
        fake = _FakeRagService(block=True, block_seconds=30.0)

        result = await _run_check_services(fake)

        assert _rag_outcomes(result) == [StartupCheckStatus.WARNING]
        warned = [o for o in result.outcomes if o.source == "rag_consistency"]
        assert "unverified" in warned[0].message
        assert fake.called
        assert fake.event is not None
        assert fake.event.is_set()

    def test_loop_close_releases_worker(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """REQ-004: closing the loop after a timed-out check does not wait for
        the worker thread's natural duration."""
        monkeypatch.setattr("agent.startup_validation.RAG_CONSISTENCY_TIMEOUT_SEC", 0.1)
        fake = _FakeRagService(block=True, block_seconds=3.0)

        async def _run() -> StartupValidationResult:
            return await _run_check_services(fake)

        start = time.monotonic()
        asyncio.run(_run())
        elapsed = time.monotonic() - start

        assert elapsed < 1.5

    async def test_in_time_fatal_still_fatal(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """REQ-005: an in-time check that reports a fatal finding still yields a
        pipeline fatal, and the event it receives is never set."""
        monkeypatch.setattr(
            "agent.startup_validation.RAG_CONSISTENCY_TIMEOUT_SEC", 30.0
        )
        fatal_finding = MagicMock(
            severity=FindingSeverity.FATAL, message="boom", repair_action="fix"
        )
        result = MagicMock(is_consistent=False, findings=[fatal_finding])
        fake = _FakeRagService(block=False, result=result)

        outcome = await _run_check_services(fake)

        fatals = [o for o in outcome.outcomes if o.source == "rag_consistency"]
        assert any(o.status == StartupCheckStatus.FATAL for o in fatals)
        assert fake.called
        assert fake.event is not None
        assert not fake.event.is_set()


class _CancelObservingFakeRag(_FakeRagService):
    """`_FakeRagService` plus a `returned` flag so the test can observe the
    worker thread exiting once the stop event is set."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.returned = False

    def consistency(self, stop: threading.Event | None = None) -> object:
        try:
            return super().consistency(stop)
        finally:
            self.returned = True


class TestRagConsistencyCancellation:
    """REQ-003 (Plan startrev004): cancelling the services stage while the RAG
    check runs must set the stop event so the worker thread stops, and the
    cancellation must still propagate."""

    @pytest.mark.asyncio
    async def test_cancelling_check_services_sets_stop_event_and_returns(
        self,
    ) -> None:
        """Cancelling `check_services` mid-RAG sets the stop event passed to the
        fake, the fake returns (worker released), and CancelledError propagates."""
        fake = _CancelObservingFakeRag(block=True, block_seconds=5.0)

        async def _run() -> StartupValidationResult:
            return await _run_check_services(fake)

        task = asyncio.ensure_future(_run())
        for _ in range(200):
            if fake.called:
                break
            await asyncio.sleep(0.01)
        assert fake.called, "fake consistency check never started"

        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

        assert fake.event is not None
        assert fake.event.is_set()
        # The handler must release the worker; bound the wait so a pre-change
        # run fails fast instead of hanging for the fake's full block time.
        for _ in range(300):
            if fake.returned:
                break
            await asyncio.sleep(0.01)
        assert fake.returned, "worker thread was not released by the stop event"
