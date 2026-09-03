"""scripts/agent/startup_validation.py

Startup validation pipeline: LLM/Embed health, tool definitions, security audit,
routing drift/safety tiers, and RAG consistency.

Extracted from scripts/agent/startup.py (REQ-003).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agent.context import AgentContext
from agent.services.mcp_health import check_readiness
from agent.services.mcp_tool_discovery import McpToolDiscoveryService
from agent.services.rag_maintenance_service import RagMaintenanceService
from agent.services.routing_drift import check_routing_drift, check_routing_safety_tiers
from agent.services.security_audit import audit_security_defaults
from agent.shared.health_models import StartupCheckStatus, StartupValidationResult

if TYPE_CHECKING:
    from agent.cli_view import CLIView


class StartupValidationPipeline:
    """Owns the full service-validation pipeline."""

    def __init__(self, ctx: AgentContext, view: CLIView) -> None:
        self._ctx = ctx
        self._view = view

    async def check_services(self) -> StartupValidationResult:
        """Probe LLM/Embed health, validate tool definitions, and audit security defaults."""
        from shared.logger import Logger

        logger = Logger(__name__, "/opt/llm/logs/agent.log")
        from shared.mcp_config import SecurityProfile

        ctx = self._ctx
        production_mode = ctx.cfg.mcp.security_profile == SecurityProfile.PRODUCTION
        pipeline = StartupValidationResult()

        # 1. Security audit
        try:
            warnings = audit_security_defaults(ctx, production_mode=production_mode)
            for msg in warnings:
                pipeline.add_warning("security_audit", msg)
            pipeline.add_ok("security_audit")
        except RuntimeError as exc:
            pipeline.add_fatal(
                "security_audit",
                str(exc),
                remediation="Fix MCP server auth_token or sandbox config.",
            )

        # 2. Service readiness
        try:
            result = await check_readiness(ctx, production_mode=production_mode)
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
        # pipeline.add_fatal() unconditionally, regardless of production_mode —
        # environment name must not weaken this safety/integrity Fail-Fast path.
        try:
            discovery = await McpToolDiscoveryService(ctx).discover_all()
            ctx.services_required.runtime_tools = discovery.registry
            # Wire RuntimeToolRegistry into ToolExecutor routing resolver.
            if discovery.registry is not None:
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
        try:
            for msg in check_routing_drift(
                ctx, strict=ctx.cfg.tool.routing_drift_strict
            ):
                pipeline.add_warning("routing_drift", msg)
        except RuntimeError as exc:
            pipeline.add_fatal("routing_drift", str(exc))
        except Exception as exc:  # noqa: BLE001 — unexpected routing-drift check failures are downgraded to a warning rather than allowed to abort startup
            pipeline.add_warning("routing_drift", f"Routing drift check failed: {exc}")

        # 5b. Routing safety tiers
        try:
            for msg in check_routing_safety_tiers(ctx):
                pipeline.add_warning("routing_safety_tiers", msg)
        except Exception as exc:  # noqa: BLE001 — unexpected routing-safety-tier check failures are downgraded to a warning rather than allowed to abort startup
            pipeline.add_warning(
                "routing_safety_tiers", f"Routing safety tier check failed: {exc}"
            )

        # 6. RAG consistency
        try:
            rag_check = RagMaintenanceService().consistency()
            if rag_check.is_consistent:
                pipeline.add_ok("rag_consistency")
            else:
                for issue in rag_check.issues:
                    pipeline.add_warning(
                        "rag_consistency", f"[RAG] Consistency issue: {issue}"
                    )
        except Exception as exc:  # noqa: BLE001 — non-critical maintenance check must not abort startup
            logger.warning("RAG consistency check failed: %s", exc)
            pipeline.add_skipped(
                "rag_consistency", f"RAG consistency check skipped: {exc}"
            )

        return pipeline
