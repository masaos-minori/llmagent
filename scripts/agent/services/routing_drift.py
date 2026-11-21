"""scripts/agent/services/routing_drift.py

Routing-drift validation."""

from __future__ import annotations

from shared.logger import Logger

from agent.context import AgentContext

logger = Logger(__name__, "/opt/llm/logs/agent.log")


def check_routing_safety_tiers(ctx: AgentContext) -> list[str]:
    """Return tier-drift findings comparing the seed registry with live declarations.

    Agentcfg003 REQ-007 (AC-10): the shared check compares the reference seed
    registry against the live ``RuntimeToolRegistry`` — every live entry carries
    the ``agent_safety_tier`` its producer declared (the strict builder rejects an
    undeclared tier), so a seed tool with no live entry is the drift finding.
    The removed ``tool_safety_tiers`` configuration map no longer feeds the check.
    The findings are a drift report only: no caller may use them to classify a
    tool. An empty live registry (config-build / pre-discovery startup point) has
    nothing to compare and returns no findings.
    """
    from shared.tool_routing_validation import check_tool_safety_tiers

    services = ctx.services
    runtime_registry = getattr(services, "runtime_tools", None) if services else None
    warnings: list[str] = check_tool_safety_tiers(runtime_registry=runtime_registry)
    return warnings
