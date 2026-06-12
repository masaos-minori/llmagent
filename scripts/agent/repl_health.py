"""MCP server health monitoring and startup validation for AgentREPL.

Standalone async functions taking AgentContext as first argument.
Extracted from agent/repl.py to allow targeted loading when modifying
health check or watchdog behaviour.
"""

from __future__ import annotations

import asyncio
from http import HTTPStatus
from typing import TYPE_CHECKING
from urllib.parse import urlparse

import httpx
import orjson
from shared.logger import Logger
from shared.tool_executor import StdioTransport

from agent.context import AgentContext

if TYPE_CHECKING:
    from shared.mcp_config import McpServerConfig

logger = Logger(__name__, "/opt/llm/logs/agent.log")


async def probe_mcp_health(http: httpx.AsyncClient, base_url: str) -> bool:
    """Return True if the MCP server at base_url responds to /health with 200."""
    try:
        resp = await http.get(f"{base_url}/health", timeout=5.0)
        ok: bool = resp.status_code == HTTPStatus.OK  # explicit type for older mypy stubs
        return ok
    except (httpx.HTTPError, OSError, TimeoutError):
        return False


async def check_service_health(ctx: AgentContext) -> list[str]:
    """Probe LLM and Embed service health at startup; return warning strings on failure.

    Failure is non-fatal: the REPL continues regardless.
    Derives the /health URL by stripping the path from each endpoint URL.
    """
    if ctx.services.http is None:
        raise RuntimeError("http service not initialized")
    checks = [
        ("llm", ctx.cfg.llm.llm_url),
        ("embed-llm", ctx.cfg.rag.embed_url),
    ]
    warnings: list[str] = []
    for label, url in checks:
        if not url:
            continue
        parsed = urlparse(url)
        health_url = f"{parsed.scheme}://{parsed.netloc}/health"
        try:
            resp = await ctx.services.http.get(health_url, timeout=2.0)
            if resp.status_code != HTTPStatus.OK:
                msg = f"{label} health check returned HTTP {resp.status_code}"
                logger.warning(msg)
                warnings.append(msg)
        except (httpx.HTTPError, OSError) as e:
            msg = f"{label} unreachable at {health_url}: {e}"
            logger.warning(msg)
            warnings.append(msg)
    return warnings


async def _fetch_stdio_tools(transport: object) -> set[str]:
    """Query a running stdio server for its tool list via the __list_tools__ RPC.

    Returns an empty set when the server is unreachable or returns an error.
    """
    if not isinstance(transport, StdioTransport) or not transport.is_alive():
        return set()
    try:
        result = await asyncio.wait_for(
            transport.call("__list_tools__", {}),
            timeout=5.0,
        )
        if result.is_error:
            return set()
        data = orjson.loads(result.output)
        return {str(n) for n in data.get("tools", [])}
    except (TimeoutError, orjson.JSONDecodeError, OSError) as e:
        logger.warning(f"__list_tools__ RPC failed: {e}")
        return set()


async def _collect_server_tool_names(ctx: AgentContext) -> set[str]:
    """Probe all configured MCP servers and return the union of their tool names.

    HTTP servers: probed via GET /v1/tools.
    Stdio servers: probed via the __list_tools__ reserved RPC (only when running).
    """
    if ctx.services.http is None:
        raise RuntimeError("http service not initialized")
    server_names: set[str] = set()
    for key, srv_cfg in ctx.cfg.mcp.mcp_servers.items():
        if srv_cfg.transport == "http":
            if not srv_cfg.url:
                continue
            try:
                resp = await ctx.services.http.get(
                    f"{srv_cfg.url}/v1/tools",
                    timeout=5.0,
                )
                if resp.status_code == HTTPStatus.OK:
                    server_names.update(t["name"] for t in resp.json().get("tools", []))
            except (httpx.HTTPError, OSError) as e:
                logger.warning(f"Cannot reach {srv_cfg.url}/v1/tools: {e}")
        elif srv_cfg.transport == "stdio":
            transport = ctx.services.stdio_procs.get(key)
            if transport is None:
                continue  # not yet started (ondemand or failed persistent)
            names = await _fetch_stdio_tools(transport)
            server_names.update(names)
    return server_names


async def _check_tool_definitions(ctx: AgentContext, strict: bool = False) -> list[str]:
    """Shared logic: compare tool_definitions against live server tool lists."""
    cfg_names = {
        td["function"]["name"]
        for td in ctx.cfg.tool.tool_definitions
        if "function" in td
    }
    server_names = await _collect_server_tool_names(ctx)
    if not server_names:
        return []  # All servers unreachable; skip validation
    missing_in_server = cfg_names - server_names
    missing_in_cfg = server_names - cfg_names
    warnings: list[str] = []
    if missing_in_server:
        msg = f"Tools in agent.toml but not on any server: {sorted(missing_in_server)}"
        logger.warning(msg)
        warnings.append(msg)
    if missing_in_cfg:
        logger.warning(
            f"Tools on servers but not in agent.toml: {sorted(missing_in_cfg)}",
        )
    if (missing_in_server or missing_in_cfg) and strict:
        raise RuntimeError("Strict mode: tool definition mismatch detected")
    return warnings


async def check_tool_definitions_runtime(ctx: AgentContext) -> list[str]:
    """Runtime validation: no raise, warnings only."""
    return await _check_tool_definitions(ctx, strict=False)


async def _watchdog_check_http(
    ctx: AgentContext,
    key: str,
    srv_cfg: McpServerConfig,
    restart_counts: dict[str, int],
    max_restarts: int,
) -> None:
    """Probe one HTTP server and restart via lifecycle manager when health check fails.

    For startup_mode="subprocess" servers, restart is delegated to
    ctx.services.lifecycle.restart().  Other modes (externally-managed) only
    log a warning because the agent does not own those processes.
    """
    if ctx.services.http is None:
        raise RuntimeError("http service not initialized")
    if not srv_cfg.url:
        return
    ok = await probe_mcp_health(ctx.services.http, srv_cfg.url)
    if ok:
        restart_counts[key] = 0
        if ctx.services.health_registry:
            ctx.services.health_registry.record_success(key)
        return
    count = restart_counts.get(key, 0)
    if count >= max_restarts:
        logger.warning(
            f"Watchdog: {key!r} unreachable; restart limit reached ({max_restarts})",
        )
        return
    logger.warning(
        f"Watchdog: {key!r} health check failed,"
        f" restarting (attempt {count + 1}/{max_restarts})",
    )
    # Delegate restart to lifecycle manager
    if srv_cfg.startup_mode == "subprocess" and ctx.services.lifecycle is not None:
        try:
            await ctx.services.lifecycle.restart(key)
            restart_counts[key] = count + 1
        except (OSError, RuntimeError) as e:
            logger.error(f"Watchdog: failed to restart {key!r}: {e}")
    else:
        logger.warning(
            f"Watchdog: {key!r} is not a subprocess-mode server;"
            " manual intervention required",
        )
    if ctx.services.health_registry:
        ctx.services.health_registry.record_failure(key)


async def _watchdog_check_stdio(
    ctx: AgentContext,
    key: str,
    srv_cfg: McpServerConfig,
    restart_counts: dict[str, int],
    max_restarts: int,
) -> None:
    """Check liveness of one stdio server and restart it when dead."""
    # Ondemand servers are lifecycle-managed; skip watchdog coverage.
    if srv_cfg.startup_mode == "ondemand":
        return
    transport = ctx.services.stdio_procs.get(key)
    if transport is None:
        return
    alive = transport.is_alive()
    if alive and srv_cfg.healthcheck_mode == "ping_tool":
        # Confirm responsiveness beyond process liveness with a ping.
        names = await _fetch_stdio_tools(transport)
        alive = bool(names)
    if alive:
        restart_counts[key] = 0
        if ctx.services.health_registry:
            ctx.services.health_registry.record_success(key)
        return
    count = restart_counts.get(key, 0)
    if count >= max_restarts:
        logger.warning(
            f"Watchdog: stdio server {key!r} dead;"
            f" restart limit reached ({max_restarts})",
        )
        return
    logger.warning(
        f"Watchdog: stdio server {key!r} died,"
        f" restarting (attempt {count + 1}/{max_restarts})",
    )
    if ctx.services.lifecycle is not None:
        try:
            await ctx.services.lifecycle.restart_stdio(key)
            restart_counts[key] = count + 1
        except (OSError, RuntimeError) as e:
            logger.error(f"Watchdog: failed to restart stdio server {key!r}: {e}")
    if ctx.services.health_registry:
        ctx.services.health_registry.record_failure(key)


async def watchdog_loop(ctx: AgentContext) -> None:
    """Periodically probe MCP server health and restart via lifecycle manager on failure.

    Runs until cancelled (e.g. when the REPL exits).
    Restart attempts per server are capped at mcp_watchdog_max_restarts to
    prevent infinite restart loops.
    """
    interval = ctx.cfg.mcp.mcp_watchdog_interval
    max_restarts = ctx.cfg.mcp.mcp_watchdog_max_restarts
    restart_counts: dict[str, int] = {}
    while True:
        await asyncio.sleep(interval)
        for key, srv_cfg in ctx.cfg.mcp.mcp_servers.items():
            if srv_cfg.transport == "http":
                await _watchdog_check_http(
                    ctx,
                    key,
                    srv_cfg,
                    restart_counts,
                    max_restarts,
                )
            elif srv_cfg.transport == "stdio":
                await _watchdog_check_stdio(
                    ctx,
                    key,
                    srv_cfg,
                    restart_counts,
                    max_restarts,
                )
        if ctx.services.lifecycle is not None:
            await ctx.services.lifecycle.shutdown_idle()
