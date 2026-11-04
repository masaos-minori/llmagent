"""tests/agent/test_startup_validation.py

Regression tests for REQ-002, REQ-003: Verify the RAG consistency check inside
StartupValidationPipeline.check_services() enforces its timeout and reports a
normal pass, by driving the real check_services() body.
"""

from __future__ import annotations

import sqlite3
from contextlib import ExitStack
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from agent.shared.health_models import (
    HealthCheckResult,
    StartupCheckStatus,
    StartupValidationResult,
)
from agent.startup_validation import StartupValidationPipeline
from shared.mcp_config import (
    McpServerConfig,
    SecurityProfile,
    StartupMode,
    TransportType,
)


def _make_ctx() -> MagicMock:
    ctx = MagicMock()
    ctx.cfg.mcp.security_profile = SecurityProfile.PRODUCTION
    ctx.cfg.memory.memory_embed_dim = 768
    ctx.cfg.tool.tool_definitions_strict = False
    return ctx


async def _run_check_services(
    rag_service: MagicMock,
    *,
    wait_for_side_effect: BaseException | None = None,
    mcp_servers: dict[str, object] | None = None,
) -> StartupValidationResult:
    """Run the real check_services() with every other check mocked to a clean pass."""
    ctx = _make_ctx()
    if mcp_servers is not None:
        ctx.cfg.mcp.mcp_servers = mcp_servers
    discovery = MagicMock(
        return_value=MagicMock(
            discover_all=AsyncMock(
                return_value=MagicMock(registry=None, findings=[], unreachable=[])
            )
        )
    )
    mocks: dict[str, object] = {
        "check_readiness": AsyncMock(return_value=HealthCheckResult()),
        "McpToolDiscoveryService": discovery,
        "check_routing_drift": MagicMock(return_value=[]),
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
        "check_routing_drift": MagicMock(return_value=[]),
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
    async def test_strict_drift_is_fatal(self) -> None:
        """A strict-mode routing drift raises RuntimeError inside check_config and is
        recorded as a FATAL routing_drift outcome."""
        ctx = _make_ctx()
        ctx.cfg.tool.routing_drift_strict = True
        result = _run_check_config(
            ctx,
            check_routing_drift=MagicMock(
                side_effect=RuntimeError("Strict mode: routing drift detected")
            ),
        )

        outcomes = [o for o in result.outcomes if o.source == "routing_drift"]
        assert any(o.status == StartupCheckStatus.FATAL for o in outcomes)

    @pytest.mark.asyncio
    async def test_safety_tier_failure_is_fatal(self) -> None:
        """A safety-tier failure is always FATAL (fail-closed), regardless of drift policy."""
        ctx = _make_ctx()
        result = _run_check_config(
            ctx,
            check_routing_safety_tiers=MagicMock(
                side_effect=RuntimeError("tier missing")
            ),
        )

        outcomes = [o for o in result.outcomes if o.source == "routing_safety_tiers"]
        assert any(o.status == StartupCheckStatus.FATAL for o in outcomes)

    @pytest.mark.asyncio
    async def test_non_strict_drift_is_warning(self) -> None:
        """A non-strict routing drift reports its messages as a WARNING, not a FATAL."""
        ctx = _make_ctx()
        ctx.cfg.tool.routing_drift_strict = False
        result = _run_check_config(
            ctx,
            check_routing_drift=MagicMock(
                return_value=["Routing drift [web]: extra tool 'foo'"]
            ),
        )

        outcomes = [o for o in result.outcomes if o.source == "routing_drift"]
        assert len(outcomes) == 1
        assert outcomes[0].status == StartupCheckStatus.WARNING
        assert not result.has_fatal

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
    async def test_config_checks_report_together_without_short_circuit(self) -> None:
        """The four config checks all run and report together: an enabled token-less
        server (FATAL mcp_auth) and a failing drift check (FATAL routing_drift) are both
        present, proving no short-circuit among them."""
        ctx = _make_ctx()
        ctx.cfg.mcp.mcp_servers = {"web": MagicMock(auth_token="", is_disabled=False)}
        result = _run_check_config(
            ctx,
            check_routing_drift=MagicMock(side_effect=RuntimeError("drift detected")),
        )

        fatal_sources = {
            o.source for o in result.outcomes if o.status == StartupCheckStatus.FATAL
        }
        assert "mcp_auth" in fatal_sources
        assert "routing_drift" in fatal_sources

    @pytest.mark.asyncio
    async def test_runtime_stage_no_longer_runs_config_checks(self) -> None:
        """REQ-006: the runtime stage (check_services) no longer runs the config-only
        checks: check_routing_drift is never called and neither mcp_auth nor
        routing_drift appears among the runtime outcomes."""
        recording = MagicMock()
        ctx = _make_ctx()
        ctx.cfg.mcp.mcp_servers = {"web": MagicMock(auth_token="valid-token")}
        discovery = MagicMock(
            return_value=MagicMock(
                discover_all=AsyncMock(
                    return_value=MagicMock(registry=None, findings=[], unreachable=[])
                )
            )
        )
        mocks: dict[str, object] = {
            "check_readiness": AsyncMock(return_value=HealthCheckResult()),
            "McpToolDiscoveryService": discovery,
            "check_routing_safety_tiers": MagicMock(return_value=[]),
            "RagMaintenanceService": MagicMock(
                return_value=MagicMock(is_consistent=True, issues=[])
            ),
            "_check_component_mandatoriness": MagicMock(),
        }
        with ExitStack() as stack:
            for name, mock_obj in mocks.items():
                stack.enter_context(patch(f"agent.startup_validation.{name}", mock_obj))
            # Patch check_routing_drift last so it is the active reference during the
            # call, letting this test observe whether the runtime stage touches it.
            stack.enter_context(
                patch("agent.startup_validation.check_routing_drift", recording)
            )
            stack.enter_context(
                patch(
                    "db.config.build_db_config",
                    return_value=MagicMock(embedding_dims=768),
                )
            )
            stack.enter_context(patch("shared.logger.Logger", MagicMock()))
            result = await StartupValidationPipeline(ctx, MagicMock()).check_services()

        recording.assert_not_called()
        assert not any(
            o.source in ("mcp_auth", "routing_drift") for o in result.outcomes
        )


class TestRagConsistencyTimeout:
    """Tests for REQ-002, REQ-003: RAG check timeout enforcement."""

    @pytest.mark.asyncio
    async def test_rag_check_timeout_enforced(self) -> None:
        """REQ-002: a timed-out RAG consistency check warns identity-unverified, not fatal."""
        rag_service = MagicMock()
        result = await _run_check_services(
            rag_service,
            wait_for_side_effect=TimeoutError("timed out"),
        )

        assert _rag_outcomes(result) == [StartupCheckStatus.WARNING]
        warned = [o for o in result.outcomes if o.source == "rag_consistency"]
        assert "timed out" in warned[0].message
        assert "identity-unverified" in warned[0].message
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
    async def test_rag_check_programming_error_classified(self) -> None:
        """REQ-004: a programming-error exception is recorded as a classified WARNING."""
        rag_service = MagicMock()
        rag_service.consistency.side_effect = KeyError("missing key")

        result = await _run_check_services(rag_service)

        assert _rag_outcomes(result) == [StartupCheckStatus.WARNING]
        warned = [o for o in result.outcomes if o.source == "rag_consistency"]
        assert "PROGRAMMING_ERROR" in warned[0].message
        assert "KeyError" in warned[0].message
        assert "identity-unverified" in warned[0].message
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
        "check_routing_drift": MagicMock(return_value=[]),
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
