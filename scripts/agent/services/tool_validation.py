"""Tool-definition runtime validation.

Extracted from scripts/agent/repl_health.py to isolate tool-definition
validation concerns from MCP health monitoring.
"""

from __future__ import annotations

from http import HTTPStatus

import httpx
from shared.logger import Logger
from shared.mcp_config import TransportType

from agent.context import AgentContext
from agent.shared.health_models import HealthCheckResult, ServiceWarning

logger = Logger(__name__, "/opt/llm/logs/agent.log")


def _validate_tools_response(
    server_key: str, body: object
) -> tuple[list[str], str | None]:
    """Validate /v1/tools response body. Returns (tool_names, error_msg).

    error_msg is None on success; a descriptive string if the response is malformed.
    """
    if not isinstance(body, dict):
        return (
            [],
            f"{server_key}: /v1/tools response is not a JSON object (got {type(body).__name__})",
        )
    tools = body.get("tools")
    if tools is None:
        return [], f"{server_key}: /v1/tools response missing 'tools' field"
    if not isinstance(tools, list):
        return (
            [],
            f"{server_key}: /v1/tools 'tools' must be a list (got {type(tools).__name__})",
        )
    names: list[str] = []
    for i, entry in enumerate(tools):
        if not isinstance(entry, dict):
            return [], f"{server_key}: /v1/tools tools[{i}] is not an object"
        name = entry.get("name")
        if not isinstance(name, str) or not name.strip():
            return [], f"{server_key}: /v1/tools tools[{i}] has invalid name {name!r}"
        names.append(name)
    return names, None


async def _collect_server_tool_names(ctx: AgentContext) -> tuple[set[str], list[str]]:
    """Probe all configured MCP servers and return (tool_names, unreachable_keys).

    HTTP servers: probed via GET /v1/tools.
    Returns a tuple of (union of tool names, list of server keys that were unreachable).

    Scenarios and expected log output:
      - One HTTP server unreachable:
          WARNING "{key} unreachable at {url}/v1/tools: ..."
          returns (names_from_remaining_servers, [key])
      - All HTTP servers unreachable:
          WARNING per server (as above)
          returns (set(), [key1, key2, ...])
      - All servers reachable:
          returns (union_of_all_tool_names, [])
    """
    if ctx.services_required.http is None:
        raise RuntimeError("http service not initialized")
    server_names: set[str] = set()
    unreachable: list[str] = []
    for key, srv_cfg in ctx.cfg.mcp.mcp_servers.items():
        if srv_cfg.transport == TransportType.HTTP:
            if not srv_cfg.url:
                continue
            try:
                resp = await ctx.services_required.http.get(
                    f"{srv_cfg.url}/v1/tools",
                    timeout=5.0,
                )
                if resp.status_code == HTTPStatus.OK:
                    try:
                        body_data: object = resp.json()
                    except ValueError as e:
                        msg = f"{key}: /v1/tools response is not valid JSON: {e}"
                        logger.warning("Malformed /v1/tools: %s", msg)
                        unreachable.append(key)
                        continue
                    names, err_msg = _validate_tools_response(key, body_data)
                    if err_msg:
                        logger.warning("Malformed /v1/tools: %s", err_msg)
                        unreachable.append(key)
                    else:
                        server_names.update(names)
                else:
                    msg = f"{key} /v1/tools returned HTTP {resp.status_code}"
                    logger.warning(msg)
                    unreachable.append(key)
            except (httpx.HTTPError, OSError) as e:
                msg = f"{key} unreachable at {srv_cfg.url}/v1/tools: {e}"
                logger.warning(msg)
                unreachable.append(key)
    return server_names, unreachable


async def _check_tool_definitions(
    ctx: AgentContext, strict: bool = False
) -> HealthCheckResult:
    """Compare tool_definitions against live server tool lists.

    Distinguishes failure cases:
      - server unreachable (logged as warning, included in unreachable list)
      - /v1/tools fetch failed (HTTP non-200)
      - tool mismatch (missing_in_server or missing_in_cfg)
      - all servers unreachable -> skip validation with info log

    Scenarios and expected log output:
      - Partial unreachable (some servers respond):
          WARNING per unreachable server (from _collect_server_tool_names)
          WARNING "Tools in tools_definitions.toml but not on any server: [...]" (if mismatch)
          returns HealthCheckResult(warnings=[...]) or HealthCheckResult()
      - All servers unreachable, strict=True:
          ERROR "Strict mode: all MCP servers unreachable — cannot validate tool definitions. Unreachable servers: [...]."
          raises RuntimeError
      - All servers unreachable, strict=False:
          INFO "All MCP servers unreachable; skipping tool definition check. Unreachable: [...]"
          returns HealthCheckResult() — no warnings
      - Tool mismatch, strict=False:
          WARNING "Tools in tools_definitions.toml but not on any server: [...]"
          returns HealthCheckResult(warnings=[ServiceWarning(...)])
      - Tool mismatch, strict=True:
          ERROR "Strict mode: tool definition mismatch detected. Mismatches: .... Unreachable servers: ...."
          raises RuntimeError
    """
    cfg_names = {
        td["function"]["name"]
        for td in ctx.cfg.tool.tool_definitions
        if "function" in td
    }
    server_names, unreachable = await _collect_server_tool_names(ctx)
    if not server_names:
        if unreachable:
            if strict:
                msg = (
                    f"Strict mode: all MCP servers unreachable — cannot validate tool definitions. "
                    f"Unreachable servers: {sorted(set(unreachable))}."
                )
                logger.error(msg)
                raise RuntimeError(msg)
            msg = f"All MCP servers unreachable; skipping tool definition check. Unreachable: {sorted(set(unreachable))}"
            logger.info(msg)
        else:
            msg = "No tool definitions in config and no servers reachable; skipping validation"
            logger.info(msg)
        return HealthCheckResult()
    missing_in_server = cfg_names - server_names
    missing_in_cfg = server_names - cfg_names
    warnings: list[ServiceWarning] = []
    if missing_in_server:
        msg = f"Tools in tools_definitions.toml but not on any server: {sorted(missing_in_server)}"
        logger.warning(msg)
        warnings.append(ServiceWarning(label="tool_definitions", url="", message=msg))
    if missing_in_cfg:
        msg = f"Tools on servers but not in tools_definitions.toml: {sorted(missing_in_cfg)}"
        logger.warning(msg)
    if (missing_in_server or missing_in_cfg) and strict:
        mismatch_parts: list[str] = []
        if missing_in_server:
            mismatch_parts.append(f"missing_in_server={sorted(missing_in_server)}")
        if missing_in_cfg:
            mismatch_parts.append(f"extra_on_servers={sorted(missing_in_cfg)}")
        mismatch_str = ", ".join(mismatch_parts) if mismatch_parts else "none"
        unreachable_str = sorted(set(unreachable)) if unreachable else []
        msg = (
            f"Strict mode: tool definition mismatch detected. "
            f"Mismatches: {mismatch_str}. "
            f"Unreachable servers: {unreachable_str}."
        )
        logger.error(msg)
        raise RuntimeError(msg)
    return HealthCheckResult(warnings=warnings)


async def check_tool_definitions_runtime(ctx: AgentContext) -> HealthCheckResult:
    """Runtime validation: no raise, warnings only."""
    return await _check_tool_definitions(ctx, strict=False)
