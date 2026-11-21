"""scripts/agent/services/tool_validation.py

Tool-definition runtime validation.
"""

from __future__ import annotations

from http import HTTPStatus

import httpx
from shared.logger import Logger
from shared.mcp_config import TransportType
from shared.tool_routing_validation import validate_routing_against_live

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


async def _collect_server_tool_names(
    ctx: AgentContext,
) -> tuple[dict[str, list[str]], list[str]]:
    """Probe all configured MCP servers and return ({server_key: tool_names}, unreachable_keys).

    HTTP servers: probed via GET /v1/tools.
    Returns a tuple of {server_key: [tool names]} and the list of server keys that were unreachable.

    Scenarios and expected log output:
      - One HTTP server unreachable:
          WARNING "{key} unreachable at {url}/v1/tools: ..."
          returns ({remaining_servers: [...]}, [key])
      - All HTTP servers unreachable:
          WARNING per server (as above)
          returns ({}, [key1, key2, ...])
      - All servers reachable:
          returns ({server_key: [...], ...}, [])
    """
    if ctx.services_required.http is None:
        raise RuntimeError("http service not initialized")
    per_server: dict[str, list[str]] = {}
    unreachable: list[str] = []
    for key, srv_cfg in ctx.cfg.mcp.mcp_servers.items():
        if srv_cfg.transport == TransportType.HTTP and not srv_cfg.is_disabled:
            if not srv_cfg.url:
                continue
            try:
                resp = await ctx.services_required.http.get(
                    f"{srv_cfg.url}/v1/tools",
                    timeout=5.0,
                    headers=srv_cfg.auth_headers(),
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
                        per_server[key] = names
                else:
                    msg = f"{key} /v1/tools returned HTTP {resp.status_code}"
                    logger.warning(msg)
                    unreachable.append(key)
            except (httpx.HTTPError, OSError) as e:
                msg = f"{key} unreachable at {srv_cfg.url}/v1/tools: {e}"
                logger.warning(msg)
                unreachable.append(key)
    return per_server, unreachable


async def _check_tool_definitions(
    ctx: AgentContext, strict: bool = False
) -> HealthCheckResult:
    """Compare live /v1/tools against the static ownership/capability registry.

    Delegates the live-vs-registry comparison to
    ``shared.tool_routing_validation.validate_routing_against_live`` so the
    startup health path and discovery share one drift definition. A server whose
    live tools do not match its declared ownership in the registry is reported as
    an ownership/routing drift finding; under ``strict=True`` that drift is fatal.

    Distinguishes failure cases:
      - server unreachable (logged as warning, included in unreachable list)
      - /v1/tools fetch failed (HTTP non-200 / malformed)
      - routing/ownership drift (live tools diverge from the registry)
      - all servers unreachable -> skip validation with info log

    Scenarios and expected log output:
      - Partial unreachable (some servers respond) with drift:
          WARNING per unreachable server (from _collect_server_tool_names)
          WARNING per drift message (per server, from validate_routing_against_live)
          returns HealthCheckResult(warnings=[...])
      - All servers unreachable, strict=True:
          ERROR "Strict mode: all MCP servers unreachable — cannot validate tool ownership. Unreachable servers: [...]."
          raises RuntimeError
      - All servers unreachable, strict=False:
          INFO "All MCP servers unreachable; skipping tool ownership check. Unreachable: [...]"
          returns HealthCheckResult() — no warnings
      - No reachable servers at all:
          INFO "No reachable servers; skipping tool ownership check"
          returns HealthCheckResult()
      - Drift, strict=True:
          ERROR "Strict mode: tool ownership/routing drift detected. Mismatches: .... Unreachable servers: ...."
          raises RuntimeError
    """
    per_server, unreachable = await _collect_server_tool_names(ctx)
    if not per_server:
        if unreachable:
            if strict:
                msg = (
                    f"Strict mode: all MCP servers unreachable — cannot validate tool ownership. "
                    f"Unreachable servers: {sorted(set(unreachable))}."
                )
                logger.error(msg)
                raise RuntimeError(msg)
            msg = (
                f"All MCP servers unreachable; skipping tool ownership check. "
                f"Unreachable: {sorted(set(unreachable))}"
            )
            logger.info(msg)
        else:
            msg = "No reachable servers; skipping tool ownership check"
            logger.info(msg)
        return HealthCheckResult()
    drift = validate_routing_against_live(live_tool_lists=per_server)
    warnings: list[ServiceWarning] = []
    if drift:
        for server_key in sorted(drift):
            for message in drift[server_key]:
                logger.warning(message)
                warnings.append(
                    ServiceWarning(label="tool_ownership", url="", message=message)
                )
        if strict:
            mismatch_str = "; ".join(
                f"{server_key}={messages}"
                for server_key, messages in sorted(drift.items())
            )
            unreachable_str = sorted(set(unreachable)) if unreachable else []
            msg = (
                f"Strict mode: tool ownership/routing drift detected. "
                f"Mismatches: {mismatch_str}. "
                f"Unreachable servers: {unreachable_str}."
            )
            logger.error(msg)
            raise RuntimeError(msg)
    return HealthCheckResult(warnings=warnings)


async def check_tool_definitions_runtime(ctx: AgentContext) -> HealthCheckResult:
    """Runtime validation: no raise, warnings only."""
    return await _check_tool_definitions(ctx, strict=False)
