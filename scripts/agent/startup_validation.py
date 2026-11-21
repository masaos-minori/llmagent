"""scripts/agent/startup_validation.py

Startup validation pipeline: LLM/Embed health, MCP readiness and Security
Posture validation, tool definitions, routing drift/safety tiers, and RAG
consistency.

Security input is the posture each MCP server publishes, validated in
``agent.services.mcp_health.check_readiness()``. This module assembles
the pipeline; it validates no configuration of another module.
"""

from __future__ import annotations

import asyncio
import sqlite3
import threading
from typing import TYPE_CHECKING

from db.models import FindingSeverity
from shared.component_mandatoriness import (
    ComponentMandatorinessError,
    load_component_mandatoriness,
)

from agent.context import AgentContext
from agent.production_config_validator import ProductionConfigValidator
from agent.services.mcp_health import check_readiness, collect_server_postures
from agent.services.mcp_tool_discovery import McpToolDiscoveryService
from agent.services.models import RagConsistencyResult
from agent.services.rag_maintenance_service import RagMaintenanceService
from agent.services.routing_drift import check_routing_safety_tiers
from agent.shared.health_models import StartupCheckStatus, StartupValidationResult

if TYPE_CHECKING:
    from agent.cli_view import CLIView


RAG_CONSISTENCY_TIMEOUT_SEC: float = 30.0


def _classify_rag_failure(exc: Exception) -> str:
    """Classify a RAG consistency failure by root cause.

    Mirrors ``PromptSetup._classify_memory_failure()`` in startup_prompt_setup.py;
    re-declared here so this module does not depend on that module's private
    exception tuple. ``ConnectionError`` is an ``OSError``, so it is tested first.
    """
    if isinstance(exc, (ConnectionError, TimeoutError)):
        return "NETWORK_TRANSIENT"
    if isinstance(exc, (sqlite3.Error, OSError)):
        return "DATABASE_OR_IO"
    if isinstance(
        exc, (AttributeError, NameError, TypeError, LookupError, AssertionError)
    ):
        return "PROGRAMMING_ERROR"
    return "UNKNOWN"


def _record_drift_check_failure(
    pipeline: StartupValidationResult, exc: Exception
) -> None:
    """Record an unexpected failure of the routing-drift check itself.

    An unknown result is not a clean result: the failure is always FATAL.
    """
    message = f"Routing drift check failed: {exc}"
    pipeline.add_fatal("routing_drift", message)


def _record_rag_findings(
    pipeline: StartupValidationResult, rag_check: RagConsistencyResult
) -> None:
    """Record every finding of an inconsistent RAG result by its severity.

    Findings carry severity structurally (docs 05/03/04); route by it. No config
    path may downgrade a fatal finding (AC-4). An inconsistent result without any
    finding is itself FATAL: a result that cannot be explained is not trusted.
    """
    if not rag_check.findings:
        pipeline.add_fatal(
            "rag_consistency",
            "RAG consistency result is inconsistent but carries no finding; "
            "the result cannot be trusted.",
        )
        return
    for finding in rag_check.findings:
        message = f"{finding.message} Repair action: {finding.repair_action}"
        if finding.severity == FindingSeverity.FATAL:
            pipeline.add_fatal("rag_consistency", message)
        else:
            pipeline.add_warning("rag_consistency", message)


def _check_component_mandatoriness(
    ctx: AgentContext, pipeline: StartupValidationResult
) -> None:
    """Abort startup on a mandatoriness registry conflict or unknown server.

    Loads the component-mandatoriness registry once and cross-checks each
    configured MCP server's ``required`` value against the approved
    classification via ``ProductionConfigValidator.validate_against_registry``.
    A conflicting or unknown server yields exactly one fatal per message under
    the ``component_mandatoriness`` source label. A missing or unparsable
    registry is also fatal (ADR-004 Fail-Fast). Synchronous; reads no network
    state. Callers must run this before MCP tool discovery so ``runtime_tools``
    is never published when the gate fails (AC-3).
    """
    try:
        registry = load_component_mandatoriness()
    except (ComponentMandatorinessError, FileNotFoundError, OSError) as exc:
        pipeline.add_fatal(
            "component_mandatoriness",
            f"Undeterminable component mandatoriness: {exc}",
            remediation=(
                "Ensure registry/component_mandatoriness.yaml exists and is "
                "valid (ADR-004 Fail-Fast)."
            ),
        )
        return

    required_map = {key: srv.required for key, srv in ctx.cfg.mcp.mcp_servers.items()}
    for message in ProductionConfigValidator().validate_against_registry(
        registry, required_map
    ):
        pipeline.add_fatal(
            "component_mandatoriness",
            message,
            remediation=(
                "Correct the server's 'required' value in config/agent.toml or "
                "reclassify via agent_08_04 "
                "(registry: registry/component_mandatoriness.yaml)"
            ),
        )


class StartupValidationPipeline:
    """Owns the full service-validation pipeline."""

    def __init__(self, ctx: AgentContext, view: CLIView) -> None:
        self._ctx = ctx
        self._view = view

    def check_config(self) -> StartupValidationResult:
        """Run the configuration-only checks; none needs a running MCP server."""
        ctx = self._ctx
        pipeline = StartupValidationResult()

        # 1b. MCP authentication check
        missing_auth = [
            key
            for key, srv in ctx.cfg.mcp.mcp_servers.items()
            if not srv.is_disabled and not srv.auth_token
        ]
        if missing_auth:
            pipeline.add_fatal(
                "mcp_auth",
                f"MCP server(s) missing auth_token: {', '.join(sorted(missing_auth))}",
                remediation="Set a non-empty auth_token (via environment variable) for every MCP server before startup.",
            )
        else:
            pipeline.add_ok("mcp_auth")

        # 3. Component mandatoriness cross-check
        # Runs before discovery publication: a registry conflict or an unknown
        # server aborts startup so runtime_tools is never published (AC-3).
        # Synchronous; reads no network state, so it costs nothing here.
        _check_component_mandatoriness(ctx, pipeline)

        # 5b. Routing tier drift
        # Drift report comparing the reference seed registry with the live
        # declared tools (agentcfg003 AC-10): findings are reported, never
        # consulted for a tool decision. At this pre-discovery point the live
        # registry is empty, so the stage reports nothing until tools exist.
        try:
            for msg in check_routing_safety_tiers(ctx):
                pipeline.add_fatal(
                    "routing_drift",
                    msg,
                    remediation=(
                        "Register the tool through its producer with a declared "
                        "agent_safety_tier; declared metadata is the only tier "
                        "source (ADR-004 INV-07)."
                    ),
                )
        except Exception as exc:  # noqa: BLE001 — Safety Tier failures are Fail-Closed per INV-07; broad catch keeps a report-path failure from changing startup behaviour
            pipeline.add_fatal(
                "routing_drift", f"Routing tier drift check failed: {exc}"
            )

        return pipeline

    async def check_services(self) -> StartupValidationResult:
        """Probe LLM/Embed health, validate MCP readiness and Security Posture, discover tools, and check RAG consistency."""
        from shared.logger import Logger

        logger = Logger(__name__, "/opt/llm/logs/agent.log")

        ctx = self._ctx
        pipeline = StartupValidationResult()

        # 2. Service readiness
        # One observation rule: probe each server's posture once here, then pass
        # the same gates to readiness (which classifies them) and to discovery
        # below, so discovery never applies a gate readiness did not see.
        try:
            gates = await collect_server_postures(ctx)
            result = await check_readiness(ctx, gates=gates)
            for msg in result.warning_messages():
                pipeline.add_warning("readiness", msg)
            for msg in result.error_messages():
                pipeline.add_fatal("readiness", msg)
            if not result.has_issues:
                pipeline.add_ok("readiness")
        except Exception as exc:  # noqa: BLE001 — an unexpected readiness-probe failure must be captured and reported as a pipeline fatal rather than crashing startup outright
            pipeline.add_fatal("readiness", f"Readiness check failed: {exc}")

        # A readiness FATAL skips tool discovery and the RAG check.
        if pipeline.has_fatal:
            return pipeline

        # 4. MCP tool discovery and validation (consolidated)
        # ADR-004 Decision #14: a FATAL discovery finding always routes through
        # pipeline.add_fatal() unconditionally — this safety/integrity Fail-Fast
        # path is not weakened by any environment/profile distinction.
        # One observation rule: the gates were probed once for readiness above and
        # are reused here unchanged. Discovery fails closed — it never falls back
        # to an unprobed default, so an unavailable gate means no server allowed.
        try:
            discovery = await McpToolDiscoveryService(
                ctx, posture_gates=gates
            ).discover_all()
            ctx.services_required.runtime_tools = discovery.registry
            # Wire RuntimeToolRegistry into ToolExecutor routing resolver.
            ctx.services_required.tools.set_runtime_registry(discovery.registry)

            if not discovery.findings and not discovery.unreachable:
                pipeline.add_ok("mcp_tool_discovery")
            else:
                for outcome in discovery.findings:
                    if outcome.status == StartupCheckStatus.FATAL:
                        pipeline.add_fatal("mcp_tool_discovery", outcome.message)
                    elif outcome.status == StartupCheckStatus.WARNING:
                        pipeline.add_warning("mcp_tool_discovery", outcome.message)
        except Exception as exc:  # noqa: BLE001 — a broad catch prevents one failing MCP server discovery from aborting the whole startup sequence
            msg = f"MCP tool discovery failed: {exc}. No MCP tools will be available this session."
            pipeline.add_fatal(
                "mcp_tool_discovery",
                msg,
                remediation="Check MCP server connectivity and configuration.",
            )

        # A tool-discovery FATAL skips the RAG check too.
        if pipeline.has_fatal:
            return pipeline

        # 6. RAG consistency
        stop = threading.Event()
        try:
            loop = asyncio.get_running_loop()
            rag_check = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: RagMaintenanceService().consistency(stop=stop),
                ),
                timeout=RAG_CONSISTENCY_TIMEOUT_SEC,
            )
            if rag_check.is_consistent:
                pipeline.add_ok("rag_consistency")
            else:
                _record_rag_findings(pipeline, rag_check)
        except asyncio.CancelledError:
            # The awaiting stage was cancelled (shutdown request): the executor
            # future is cancelled but the worker thread keeps running, so set the
            # run's stop event before propagating the cancellation.
            stop.set()
            raise
        except TimeoutError:
            stop.set()
            logger.warning(
                "RAG consistency check timed out after %ss",
                RAG_CONSISTENCY_TIMEOUT_SEC,
            )
            pipeline.add_warning(
                "rag_consistency",
                f"RAG consistency check timed out after "
                f"{RAG_CONSISTENCY_TIMEOUT_SEC:g}s; startup continues "
                "with RAG consistency unverified.",
            )
        except Exception as exc:  # noqa: BLE001 — a failed RAG consistency check is an availability failure (ADR-004);
            # it is reported as a warning and startup continues with RAG consistency unverified.
            category = _classify_rag_failure(exc)
            logger.warning("RAG consistency check failed: %s", exc)
            pipeline.add_warning(
                "rag_consistency",
                "RAG consistency check failed: "
                f"{category} ({type(exc).__name__}): {exc}; startup continues "
                "with RAG consistency unverified.",
            )

        return pipeline
