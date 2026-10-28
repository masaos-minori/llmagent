"""scripts/agent/startup_validation.py

Startup validation pipeline: LLM/Embed health, MCP readiness and Security
Posture validation, tool definitions, routing drift/safety tiers, and RAG
consistency.

Security input is the posture each MCP server publishes, validated in
``agent.services.mcp_health.check_readiness()`` (REQ-017). This module assembles
the pipeline; it validates no configuration of another module.

Extracted from scripts/agent/startup.py (REQ-003).
"""

from __future__ import annotations

import asyncio
import sqlite3
from typing import TYPE_CHECKING

from agent.context import AgentContext
from agent.services.mcp_health import check_readiness, collect_server_postures
from agent.services.mcp_tool_discovery import McpToolDiscoveryService
from agent.services.rag_maintenance_service import RagMaintenanceService
from agent.services.routing_drift import check_routing_drift, check_routing_safety_tiers
from agent.shared.health_models import StartupCheckStatus, StartupValidationResult

if TYPE_CHECKING:
    from agent.cli_view import CLIView


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
    pipeline: StartupValidationResult, exc: Exception, *, strict: bool
) -> None:
    """Record an unexpected failure of the routing-drift check itself.

    An unknown result is not a clean result: the failure follows
    routing_drift_strict, FATAL when strict and a recorded WARNING otherwise.
    """
    message = f"Routing drift check failed: {exc}"
    if strict:
        pipeline.add_fatal("routing_drift", message)
    else:
        pipeline.add_warning("routing_drift", message)


class StartupValidationPipeline:
    """Owns the full service-validation pipeline."""

    def __init__(self, ctx: AgentContext, view: CLIView) -> None:
        self._ctx = ctx
        self._view = view

    async def check_services(self) -> StartupValidationResult:
        """Probe LLM/Embed health, validate MCP readiness and Security Posture, validate tool definitions."""
        from shared.logger import Logger

        logger = Logger(__name__, "/opt/llm/logs/agent.log")

        ctx = self._ctx
        pipeline = StartupValidationResult()

        # 1b. MCP authentication check
        missing_auth = [
            key for key, srv in ctx.cfg.mcp.mcp_servers.items() if not srv.auth_token
        ]
        if missing_auth:
            pipeline.add_fatal(
                "mcp_auth",
                f"MCP server(s) missing auth_token: {', '.join(sorted(missing_auth))}",
                remediation="Set a non-empty auth_token (via environment variable) for every MCP server before startup.",
            )
        else:
            pipeline.add_ok("mcp_auth")

        # 2. Service readiness
        try:
            result = await check_readiness(ctx)
            for msg in result.warning_messages():
                pipeline.add_warning("readiness", msg)
            for msg in result.error_messages():
                pipeline.add_fatal("readiness", msg)
            if not result.has_issues:
                pipeline.add_ok("readiness")
        except Exception as exc:  # noqa: BLE001 — an unexpected readiness-probe failure must be captured and reported as a pipeline fatal rather than crashing startup outright
            pipeline.add_fatal("readiness", f"Readiness check failed: {exc}")

        # 4. MCP tool discovery and validation (consolidated)
        # ADR-004 Decision #14: a FATAL discovery finding always routes through
        # pipeline.add_fatal() unconditionally — this safety/integrity Fail-Fast
        # path is not weakened by any environment/profile distinction.
        # The Security Posture gate is collected here rather than read from the
        # readiness step: check_readiness() raises when a posture error exists, and
        # this step still runs after that except, so the gate must be available on
        # exactly that failure path (REQ-014).
        try:
            posture_gates = await collect_server_postures(ctx)
            discovery = await McpToolDiscoveryService(
                ctx, posture_gates=posture_gates
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

        # 5. Routing drift (static)
        # Strictness starts as strict so that a failure while reading the setting
        # fails closed.
        drift_strict = True
        try:
            drift_strict = ctx.cfg.tool.routing_drift_strict
            for msg in check_routing_drift(ctx, strict=drift_strict):
                pipeline.add_warning("routing_drift", msg)
        except RuntimeError as exc:
            pipeline.add_fatal("routing_drift", str(exc))
        except Exception as exc:  # noqa: BLE001 — an unexpected failure of the drift check follows routing_drift_strict (an unknown result is not a clean result), so it must be captured and classified rather than crash startup
            _record_drift_check_failure(pipeline, exc, strict=drift_strict)

        # 5b. Routing safety tiers
        try:
            for msg in check_routing_safety_tiers(ctx):
                pipeline.add_warning("routing_safety_tiers", msg)
        except Exception as exc:  # noqa: BLE001 — Safety Tier failures are Fail-Closed per INV-07; broad catch handles RuntimeError from check_tool_safety_tiers
            pipeline.add_fatal(
                "routing_safety_tiers", f"Routing safety tier check failed: {exc}"
            )

        # 6. RAG consistency
        try:
            loop = asyncio.get_running_loop()
            rag_check = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: RagMaintenanceService().consistency(),
                ),
                timeout=30.0,
            )
            if rag_check.is_consistent:
                pipeline.add_ok("rag_consistency")
            else:
                for issue in rag_check.issues:
                    pipeline.add_warning(
                        "rag_consistency", f"[RAG] Consistency issue: {issue}"
                    )
        except TimeoutError:
            logger.warning("RAG consistency check timed out after 30s")
            pipeline.add_skipped(
                "rag_consistency", "RAG consistency check skipped: timeout after 30s"
            )
        except Exception as exc:  # noqa: BLE001 — non-critical maintenance check must not abort startup
            category = _classify_rag_failure(exc)
            logger.warning("RAG consistency check failed: %s", exc)
            pipeline.add_skipped(
                "rag_consistency",
                f"RAG consistency check skipped: {category} ({type(exc).__name__}): {exc}",
            )

        return pipeline
