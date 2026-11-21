"""scripts/agent/services/routing_drift.py

Routing-drift validation."""

from __future__ import annotations

from shared.logger import Logger

from agent.context import AgentContext

logger = Logger(__name__, "/opt/llm/logs/agent.log")


def check_routing_safety_tiers(ctx: AgentContext) -> list[str]:
    """Check that all registered tools have a declared safety tier.

    Returns one message per registered tool missing from tool_safety_tiers; the
    startup pipeline records each as FATAL (ADR-004 INV-07).
    """
    from shared.tool_routing_validation import check_tool_safety_tiers

    tool_safety_tiers = getattr(ctx.cfg.approval, "tool_safety_tiers", {})
    warnings: list[str] = check_tool_safety_tiers(tool_safety_tiers=tool_safety_tiers)
    return warnings
