"""scripts/agent/startup_reporter.py

Readiness reporter: pipeline result display and aggregated readiness status.

Extracted from scripts/agent/startup.py (REQ-004).

Replaces five repeated per-source/per-status counting blocks with
one shared _count_by_status() helper.
"""

from __future__ import annotations

from collections import OrderedDict
from typing import TYPE_CHECKING, Any

from shared.logger import Logger

from agent.output_tags import OutputTag

if TYPE_CHECKING:
    from agent.cli_view import CLIView
    from agent.shared.health_models import StartupValidationResult

logger = Logger(__name__, "/opt/llm/logs/agent.log")


def _count_by_status(
    pipeline: StartupValidationResult, source: str
) -> OrderedDict[str, int]:
    """Count OK/FATAL/WARNING/SKIPPED outcomes for a single source.

    Returns an ordered dict: {OK: n, FATAL: n, WARNING: n, SKIPPED: n}.
    """
    counts: OrderedDict[str, int] = OrderedDict(
        [
            ("OK", 0),
            ("FATAL", 0),
            ("WARNING", 0),
            ("SKIPPED", 0),
        ]
    )
    for o in pipeline.outcomes:
        if o.source == source:
            key = o.status.name  # e.g., "OK", "FATAL", "WARNING", "SKIPPED"
            if key in counts:
                counts[key] += 1
    return counts


class ReadinessReporter:
    """Owns pipeline result display and readiness reporting."""

    def __init__(self, ctx: Any, view: CLIView) -> None:
        self._ctx = ctx
        self._view = view

    def display_pipeline_results(self, pipeline: StartupValidationResult) -> None:
        """Display startup validation warnings and fatal errors via the CLI view."""
        from agent.shared.health_models import StartupCheckStatus

        for outcome in pipeline.outcomes:
            if outcome.status == StartupCheckStatus.WARNING:
                self._view.write_warning(f"{OutputTag.NON_FATAL} {outcome.message}")
            elif outcome.status == StartupCheckStatus.FATAL:
                self._view.write_fatal(outcome.message)
                if outcome.remediation:
                    self._view.write_fatal(f"  Remediation: {outcome.remediation}")
            elif outcome.status == StartupCheckStatus.SKIPPED:
                self._view.write_warning(f"{OutputTag.SKIPPED} {outcome.message}")

    def report_readiness(self, pipeline: StartupValidationResult) -> None:
        """Report aggregated readiness status after startup checks complete."""
        from shared.mcp_config import McpServerHealthState

        security_counts = _count_by_status(pipeline, "security_audit")
        mcp_counts = _count_by_status(pipeline, "readiness")
        tool_disc_counts = _count_by_status(pipeline, "mcp_tool_discovery")
        rag_counts = _count_by_status(pipeline, "rag_consistency")

        lines: list[str] = []
        lines.append("Readiness Summary:")
        lines.append(
            f"  Security audit: {'OK' if security_counts['OK'] else 'FAIL'} ({security_counts['FATAL']} fatal, {security_counts['WARNING']} warnings)"
        )
        lines.append(
            f"  Service readiness: {'OK' if mcp_counts['OK'] else 'FAIL'} ({mcp_counts['FATAL']} fatal, {mcp_counts['WARNING']} warnings, {mcp_counts['SKIPPED']} skipped)"
        )
        lines.append(
            f"  Tool discovery: {'OK' if tool_disc_counts['OK'] else 'FAIL'} ({tool_disc_counts['FATAL']} fatal, {tool_disc_counts['WARNING']} warnings, {tool_disc_counts['SKIPPED']} skipped)"
        )
        lines.append(
            f"  RAG consistency: {'OK' if rag_counts['OK'] else 'WARN'} ({rag_counts['FATAL']} fatal, {rag_counts['WARNING']} warnings)"
        )
        unreachable_count = sum(
            1
            for o in pipeline.outcomes
            if o.source == "mcp_tool_discovery" and "unreachable" in o.message.lower()
        )
        if unreachable_count > 0:
            lines.append(f"  Unreachable servers: {unreachable_count}")
        degraded_keys = []
        registry = (
            self._ctx.services_required.health_registry
            if self._ctx.services_required
            else None
        )
        if registry is not None:
            degraded_keys = [
                key
                for key in self._ctx.cfg.mcp.mcp_servers
                if registry.get_state(key) == McpServerHealthState.DEGRADED
            ]
        if degraded_keys:
            lines.append(f"  Degraded servers: {', '.join(degraded_keys)}")
        unavailable_servers: frozenset[str] = frozenset()
        runtime_tools = (
            self._ctx.services_required.runtime_tools
            if self._ctx.services_required
            else None
        )
        if runtime_tools is not None:
            unavailable_servers = runtime_tools.unavailable_servers
        if unavailable_servers:
            parts = []
            for key in sorted(unavailable_servers):
                cfg_entry = self._ctx.cfg.mcp.mcp_servers.get(key)
                policy = getattr(cfg_entry, "failure_policy", None)
                if policy is not None:
                    parts.append(f"{key} ({policy})")
                else:
                    parts.append(key)
            lines.append(f"  Excluded tools (unavailable): {', '.join(parts)}")
        self._view.write_warning("\n".join(lines))
        logger.info("Readiness summary: %s", "; ".join(lines))
