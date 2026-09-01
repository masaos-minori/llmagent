"""Routing-drift validation."""

from __future__ import annotations

from shared.logger import Logger

from agent.context import AgentContext

logger = Logger(__name__, "/opt/llm/logs/agent.log")


def check_routing_drift(ctx: AgentContext, *, strict: bool = False) -> list[str]:
    """Check config tool_names against ToolRegistry at startup. Returns warning messages.

    When strict=True, raises RuntimeError if any drift is detected.
    """
    from shared.tool_routing_validation import (
        validate_routing_against_config,
    )

    try:
        server_configs = ctx.cfg.mcp.mcp_servers
        drift = validate_routing_against_config(server_configs=server_configs)
        warnings: list[str] = []
        for server_key, messages in drift.items():
            for msg in messages:
                full_msg = f"Routing drift [{server_key}]: {msg}"
                logger.warning(full_msg)
                warnings.append(full_msg)
        if drift and strict:
            drift_str = "; ".join(f"{sk}: {msgs}" for sk, msgs in drift.items())
            msg = f"Strict mode: routing drift detected. Drift: {drift_str}."
            logger.error(msg)
            raise RuntimeError(msg)
        return warnings
    except RuntimeError:
        raise
    except Exception as exc:  # noqa: BLE001 — routing drift check must not fail startup on unexpected errors
        logger.warning("Routing drift check failed: %s", exc)
        return []


def check_routing_safety_tiers(ctx: AgentContext) -> list[str]:
    """Check that all registered tools have a declared safety tier. Returns warning messages."""
    from shared.tool_routing_validation import check_tool_safety_tiers

    tool_safety_tiers = getattr(ctx.cfg.approval, "tool_safety_tiers", {})
    warnings: list[str] = check_tool_safety_tiers(tool_safety_tiers=tool_safety_tiers)
    return warnings
